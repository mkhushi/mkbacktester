#Standard library imports
import pandas as pd
import pytz 
import os
import datetime
import sys

#Muting CUDA Warnings 
#os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
#import tensorflow as tf 
#import keras.models

#Import remaining relevant module files
sys.path.append(os.getcwd())
from signalHandler import signalHandler
from WeeklySummary import get_weekly_summary
from TradeSummary import get_trade_summary
from BacktestRunner import BacktestRunner

##IMPORTANT
#If you are feeding the data as a directory and wishing the backtesting system to format/prep for report based on filename, please use .readAndPrepData().
#An example of setting up the data directory with specified dates is below.
#If feeding data directly (ie passing a dataframe), please use inputDataAndInfo and supply currency/frequency info for the reporting.

##Data Read setup - method 1
tz = pytz.utc
startDate = datetime.datetime(2022, 1, 1, tzinfo = tz) #Start Date - adjust as necessary
endDate = datetime.datetime(2022, 11, 30, tzinfo = tz) #End Date - adjust as necessary
use_dates = False #Flag whether to use a date window, or not. Setting to zero makes the above irrelevant.
dataFolder = os.path.join(os.getcwd(), 'ExampleDatasets')
dataFiles = os.listdir(dataFolder) #Set up for iteration
exportFolder = os.path.join(os.getcwd(), 'BacktestResults') #Where reports are saved.

##Trading Strategiies Import
# from TradingStrategies.MACD_Crossover import MACD_Crossover
# from TradingStrategies.pSAR_SO import pSAR_SO
from TradingStrategies.BB_ATR import BB_ATR

##Remaining Static inputs
inputRows = 21 #Dictates how many rows are used in each loop of backtest. Primarily for minimum number of bars required for indicators.
strategy = BB_ATR
hold_direction = True #A flag whether further signals are ignored or not once in a trade. True means only hitting a limit will exit a trade.

#limit_type options are 'Percentage' to use a multiple/percentage of executed price, or flat to use a flat value.
#Also note the factor variable use, just to make things cosmetically simpler in this area.
# limit_type = 'Percentage' 
limit_type = 'Percentage' 
# stop_loss = -1
stop_loss = -2
take_profit = 5
factor = 1/100 #This can be 1/10000 for one pip if using 'Flat' limit, 1/100 for one percent if using 'Percentage' limits, and so on.
broker_cost = 0.2 #this is percertage will be divided by 100; NB this is now applied twice, on the way in and on the way out.
guaranteed_sl = False #Whether limits are firm and cannot be gapped by high/low price or not.
dynamic_limits = False #Whether limits are reset with a stronger signal or not

#Apply factor
stop_loss = stop_loss * factor
take_profit = take_profit * factor
broker_cost = broker_cost * factor

runType = 1 #Pertains to how the objects are called (different for DL strategies) as well as if indicator dataframes are saved in history. 
    #Review BacktestRunner.runBacktest for further context

backtestSummaries = pd.DataFrame()

for file in dataFiles:
    print("Running for file", file)
    fileDir = os.path.join(dataFolder, file)
    Backtest = BacktestRunner(startDate, endDate, inputRows, strategy, exportFolder)
    Backtest.prepData(fileDir, use_dates)
    Backtest.loadBroker(stop_loss, take_profit, guaranteed_sl, broker_cost, limit_type, dynamic_limits, hold_direction)
    Backtest.runBacktest(runType)
    singleSummary = Backtest.runReports()
    backtestSummaries = pd.concat([backtestSummaries, singleSummary])
    print("Total PnL: {}".format(round(Backtest.broker.total_profit, 6)))

if len(dataFiles) > 1:
    saveName = "BacktestSummary_" + datetime.datetime.now().strftime("%d%m%y-%H%M%S") + ".csv"
    saveDir = os.path.join(Backtest.exportSubdir, saveName)
    backtestSummaries.to_csv(saveDir, index = False)

print("Backtests completed")