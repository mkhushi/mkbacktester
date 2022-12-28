from logging import exception
from unittest import case
import pandas as pd
import pytz 
import os
import datetime
import time

from signalHandler import signalHandler
from WeeklySummary import get_weekly_summary
from TradeSummary import get_trade_summary

#os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3' #Mute cuda warnings
#import tensorflow as tf 
#import keras.models
pd.set_option('mode.chained_assignment', None)

class BacktestRunner:
    """
    Class for handling all aspects of the backtest.    
    """

    def __init__(self, startDate, endDate, inputRowSize, strategy, exportParentFolder, storeIndicators = 1):        
        """        
        Parameters:
        startDate (datetime): Starting date of backtest. Required for trimming dataset as well as report functionality.
        endDate (datetime): Ending date of backtest. Also required for trimming dataset as well as report functionality.
        inputRowSize (int): Minimum number of rows required to compute a signal based on the chosen strategy.
        strategy (object): Trading Strategy object. See TradingStrategies for information on structure, and .runBacktest() for further context.
        exportParentFolder (str): Parent directory of where to export results files.
        storeIndicators(int): Integer used as Boolean flag on whether to store indicators calculated by strategy in the history results.
        """

        #Data Preparation attributes
        self.startDate = startDate
        self.endDate = endDate
        self.inputRowSize = inputRowSize
        self.data = None
        self.inputs = pd.DataFrame()

        #Report formatting        
        self.asset = None
        self.frequencyStr = None
        self.exportParentFolder = exportParentFolder

        #Backtesting functionality
        self.broker = signalHandler
        self.strategy = strategy
        self.storeIndicators = storeIndicators
  
    def prepData(self, dataDir, useDates = 0):
        """
        Function used to read and format data based on an input directory. Useful as automatically formats things within the object.
        This function infers the delimitter to read as well as the assumes the frequency/asset.
            The frequency is inferred by taking the minimum difference of the first five points.
            The asset is inferred by assuming the filename is in the format {AssetName}_{ExtraArgs}.csv. Ie, separates "_" and uses the first result.
        
        Parameters:
        dataDir (str): The directory of the input csv file.
        useDates (int/Bool): A flag whether to trim the data based on the start/end dates input
        """

        #Set up export filename details
        if "/" in dataDir:
            dataFilename = dataDir.split("/")[-1]
        elif "\\" in dataDir:
            dataFilename = dataDir.split("\\")[-1]

        self.asset = dataFilename.split("_")[0]
        
        fullData = pd.read_csv(dataDir, sep = None, engine = 'python')

        #Establish time columns - seen cases where there are multiple (e.g. "Date", "Time").
        timeCols = []
        for colName in fullData.columns:
            if 'date' in colName.lower() or 'time' in colName.lower():
                timeCols.append(colName)

        if len(timeCols) > 1:
            timeCols = [timeCols]

        #Easier to re-read data and parse_dates now.
        #Note that this will combine the date/time columns into one if necessary, but that is significantly more simply to work with.
        fullData = pd.read_csv(dataDir, sep = None, engine = 'python', parse_dates = timeCols)

        #Now handle any extra characters (such as seen in MT5 export.)
        #Easiest to convert all column names to lower case such that is consistent across other parts of the functionality. 
        for oldCol in fullData.columns:
            fullData.rename(columns = {oldCol: oldCol.replace('<', '').replace('>', '').replace('_', '').lower()}, inplace = True) 

        #Also easiest to rename the timecol to 'time' per other uses across backtests/signals
        fullData.rename(columns = {fullData.columns[0]: 'time'}, inplace = True) 

        #Localise as UTC time. Timezone required for any trimming/manipulation, and UTC is standard.
        # fullData['time'] = fullData['time'].dt.tz_localize(tz = pytz.utc)

        #Infer frequency
        frequency = min(fullData['time'].diff(1)[1:6])
        frequencyDict = {pd.Timedelta(1, 'D'): 'D1',\
            pd.Timedelta(1, 'H'): 'H1',\
                pd.Timedelta(15, 'm'): 'M15',\
                    pd.Timedelta(5, 'm'): 'M5',\
                        pd.Timedelta(1, 'm'): 'M1'}

        if frequency in frequencyDict.keys():
            self.frequencyStr = frequencyDict[frequency]
        else:
            raise Exception ("Unrecognised Frequency - please add to dictionary above or review any missing/inconsistent data.")

        if useDates:
            #Flag any errors with date inputs
            if self.startDate >= fullData['time'].iloc[-1] or self.startDate > self.endDate or self.endDate <= fullData['time'].iloc[0]:
                print("Date Input error - data dates vs input dates noted below:")
                print("Input start date: {} | Input end date: {}".format(self.startDate, self.endDate))
                print("Data start date : {} | Data end date:  {}".format(fullData['time'].iloc[0], fullData['time'].iloc[-1]))
                raise Exception ("Input time does not work with data dates - please review input dates or dataset")
            
            #Trim the data to the required window
            startIdx = fullData.index[fullData['time'] >= self.startDate][0]
            startIdxAdj = max((startIdx - self.inputRowSize + 1), 0) #This allows the minimum input leading up to start date
            endIdx =  min((fullData.index[fullData['time'] <= self.endDate][-1] + 1), fullData.index[-1])
            self.data = fullData[startIdxAdj:endIdx].reset_index(drop = True)

            #Flag any errors with input dates vs input row size
            if len(fullData[startIdx:endIdx]) <= self.inputRowSize:
                print("Date vs Input Row Size error - specified dates vs data size noted below:")
                print("Input start date: {} | Input end date: {}".format(self.startDate, self.endDate))
                print("Resulting data size: {}".format(len(fullData[startIdx:endIdx])))
                print("Input row size: {}".format(self.inputRowSize))
                raise Exception ("Input time does not work with input row size - please review input dates, input row size or dataset")

        else:
            self.data = fullData                    

        #Adjust the start/end date accordingly to line up with the actual data used - for result file naming purposes
        self.startDate = self.data['time'].iloc[self.inputRowSize-1]
        self.endDate = self.data['time'].iloc[-2] #-2 used as we clear the end, given using open t+1 prices.

        startDateStr = self.startDate.strftime("%d%m%y")
        endDateStr = self.endDate.strftime("%d%m%y")

        asset = dataFilename.split("_")[0]
        self.subFolderName = "{}_{}_{}".format(asset, startDateStr, endDateStr)

    def loadBroker(self, stopLoss, takeProfit, guaranteedSl, brokerCost, limitType, dynamicLimits, holdDirection):
        """
        Function used to set up the broker/signal handler object based on passed parameters.
        See signalHandler for further information on the broker/signal handler inputs.

        Parameters:
        stopLoss (float): Stop loss level in absolute value, not pips.
        takeProfit (float): Take profit level in absolute value, not pips.
        guaranteedSl (bool): Whether to implement a guaranteed stoploss/takeprofit, or if stop conditions are based on the next available price.
            Worth reading online regarding this point as this is topical with the use of brokers and impacts spreads/costs. 
        brokerCost (float): Flat cost of broker in absolute value, not pips.        
        """

        self.broker = self.broker(stopLoss, takeProfit, guaranteedSl, brokerCost, limitType, dynamicLimits, holdDirection, self.data, self.asset, self.frequencyStr, \
            self.startDate, self.endDate, self.storeIndicators)
    
    def runBacktest(self, runType = 1):
        '''
        The main looping function for running the backtest. Implements interaction between the data, trading strategy and signal handler methods.

        Parameters:
        runType(int): The type of run based on the strategy used. Differentiates between standard indicators, deep learning (which return no indicator df) 
            and charting indicator strategies that require instantiation in a different style:
        
            1 - standard indicator strategy. Can return indicatorDF.
            2 - Deep Learning - requires model/scaler upon instantiation before input into backtest (otherwise timely), and an indicator strategy class as input. 
                Cannot return indicator DF
            3 - Charting - requires preliminary data upon instantiation before input into backtest. Can return indicatorDF. At this stage only set up/useful with ZigZag/ABCD.
        '''
        startTime = time.time()
        #Need to start from negative 1 as we are using rowsize + 1 to capture open t+1
        index = self.inputRowSize - 1
        signal = 0

        if runType == 2 and self.storeIndicators == 1:
            print("Note: Indicators can't be saved with history for runType 2 (DL) - Overriding this setting.")
            self.storeIndicators = 0
            self.broker.storeIndicators = 0

        #Set up Iteration and print commencing statement
        print("Commencing Backtest")
        while index <= len(self.data) - 2:
            
            inputs = self.data[index-self.inputRowSize+1:index+1].copy()
            row = self.data.iloc[index]

            openPriceT1 = self.data['open'].iloc[index+1]            
            lowPrice = row['low']
            highPrice = row['high']
            closePrice = row['close']

            if runType == 1:
                #Vanilla indicator strategies
                strategy = self.strategy()
                signal, indicatorDf = strategy.run(pd.DataFrame(inputs))
                self.broker.storeSignalAndIndicators(signal, indicatorDf, index)          

            elif runType == 2:
                signal = self.strategy.run(pd.DataFrame(inputs))
                self.broker.storeSignalAndIndicators(signal, None, index)          
            
            elif runType == 3:
                signal, indicatorDf = self.strategy.run(pd.DataFrame(inputs))
                self.broker.storeSignalAndIndicators(signal, indicatorDf, index)          

            if signal == 1:
                self.broker.buy(openPriceT1, highPrice, lowPrice, closePrice, index)
            elif signal == -1:
                self.broker.sell(openPriceT1, highPrice, lowPrice, closePrice, index)
            elif signal == 0:
                self.broker.checkStopConditions(closePrice, highPrice, lowPrice, index)
            else:
                raise Exception ("Unknown Signal!")

            index += 1

            #Show progress
            if index % (round(0.01 * len(self.data), 0)) == 0:
                print("----- Backtest Progress: {}% as at date: {} | PnL: {} | Total Trades: {} -----".format(\
                    round(100 * (index/len(self.data))), row['time'].strftime("%Y-%m-%d %H:%M"), round(self.broker.total_profit, 5), self.broker.trades_total), \
                        end = "\r", flush = True)

        endTime = time.time()
        print("\nTimeConsumed: {}".format(datetime.timedelta(seconds = endTime - startTime)))

    def runReports(self, suffix = None):
        """
        Function for running and exporting reports; History, Summary, Trade Summary and Weekly Summary.
        Will create a subdirectory based on the BacktestRunner export folder input and save the 4 files. 
            The subdirectory is named in the following fashion: {Strategy (where available)}_{Time_Date ran}_{Frequency}_{StartDate}_to_{EndDate}_{Suffix (where available)}

        Parameters:
        suffix (str = None): A suffix that can be appended to the export.
        """

        if hasattr(self.strategy(), 'Name'):
            exportStratName = self.strategy().Name
        else:
            try:
                exportStratName = self.strategy.Name
            except:
                print("Unavailable to obtain strategy name. Perhaps review structure of strategy class. \n")
                print("Saving in 'UndefinedStrategies'")
                exportStratName = 'UndefinedStrategies'

        exportSubdir = os.path.join(self.exportParentFolder, exportStratName)

        #Check duplicate/overriding filenames/folders and handle.
        if exportStratName not in os.listdir(self.exportParentFolder):
            os.mkdir(exportSubdir)
        else:
            counter = 0
            newFlag = False
            originalSubfolder = self.subFolderName
            while newFlag == False:
                if self.subFolderName in os.listdir(exportSubdir):             
                    counter += 1
                    self.subFolderName = originalSubfolder + "_" + str(counter)
                else:
                    newFlag = True
                if counter == 0:
                    self.subFolderName = self.subFolderName

        self.exportSubdir = exportSubdir

        subfolderDir = os.path.join(exportSubdir, self.subFolderName)

        os.mkdir(subfolderDir)

        #History
        historyData = self.broker.getHistory()
        historyData = historyData.loc[self.inputRowSize-1:, :].reset_index(drop = True)
        historyFilename = "History.csv"
        historyDir = os.path.join(subfolderDir, historyFilename).replace('\\', '/')

        #Summary
        summaryData = self.broker.getSummary()
        summaryFilename = "Summary.csv"
        summaryDir = os.path.join(subfolderDir, summaryFilename).replace('\\', '/')

        #Weekly summary
        weeklySummaryData = get_weekly_summary(historyData, self.frequencyStr)
        weeklySummaryFilename = "Weekly_Summary.csv"
        weeklySummaryDir = os.path.join(subfolderDir, weeklySummaryFilename).replace('\\', '/')

        #Trade summary
        tradeSummaryData = get_trade_summary(historyData)
        tradeSummaryFilename = "Trade_Summary.csv"
        tradeSummaryDir = os.path.join(subfolderDir, tradeSummaryFilename).replace('\\', '/')

        #Exporting csvs
        historyData.to_csv(historyDir, index = False)
        summaryData.to_csv(summaryDir, index = False)
        weeklySummaryData.to_csv(weeklySummaryDir, index = False)
        tradeSummaryData.to_csv(tradeSummaryDir, index = False)

        print("Exports finalised\n", summaryData)

        return summaryData