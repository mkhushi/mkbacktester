import pandas as pd
import datetime
import os
import numpy as np
pd.options.mode.chained_assignment = None #Mute those warnings.

def ratesTicksConcatenator(ratesDat, ticksDat, floorFreq, ticksCleanFlag = 1, replacementSpread = 3):
    """
    A function used to combine MT5 rates data and ticks data in the same dataset, such that it can be fed into the backtest.
    Main focus is to apply the first available tick after a rates data point as the bid/ask price.
        Operates with a bit of estimation or "interpolation" if exact time matches for ticks/rates are not available. 
        Also, extreme bid/ask values have been observed from the ticks which are handled with this estimation too.
    Also important to note this automatically trims the data to the max start date and min end date of the two datasets.

    Parameters:
    ratesDat (pd.DataFrame): The rates data to be used.
    ticksDat (pd.DataFrame): The ticks data to be used.
        Note the column labels used assume a certain type of formatting before input, but this is outlayed in the example.
    floorFreq (str): A string representation of an input to the pandas.Series.dt.floor function.
        This can be set to the frequency of the data by default, or adjust further if there are issues matching the data.
    ticksCleanFlag (int): The replacement policy when there is not an exact time match of ticks and rates:
        1 - Apply a 5 point rolling average of spreads to the current close price.
        2 - Apply a flat spread to close price based on the replacementSpread parameter.
    replacementSpread (int): The flat spread amount (pips) to apply to artifical bid/ask values if not available from tick data.
    
    Returns:
    concatDF (pd.DataFrame): The resulting dataframe with rates & ticks aligned to have OHLC + Bid/Ask Data.
        A "ReplacedBidAsk" column is added for some analytics on how much estimation was used. 
        Note that some results/entries will come back as the same as close price. 
            This does indeed look to be accurate from reviewing the ticks data and examples of 0 spread periods from the broker.
    """
   
    #First, align dates.
    timeCol = ratesDat.columns[0]
    
    firstRatesTime = ratesDat.iloc[0, 0]
    firstTicksTime = ticksDat.iloc[0, 0]
    
    lastRatesTime = ratesDat.iloc[-1, 0]
    lastTicksTime = ticksDat.iloc[-1, 0]

    #Flag any errors with date inputs
    if firstTicksTime >= lastRatesTime or firstRatesTime > lastTicksTime:
        print("Date input error - ticks dates vs rates dates do not align:") 
        print("Rates Start Date: {} | Rates End Date {}".format(firstRatesTime.strftime("%m/%d/%Y %H:%M:%S"), lastRatesTime.strftime("%m/%d/%Y %H:%M:%S")))
        print("Ticks Start Date: {} | Ticks End Date {}".format(firstTicksTime.strftime("%m/%d/%Y %H:%M:%S"), lastTicksTime.strftime("%m/%d/%Y %H:%M:%S")))
        raise Exception ("Review dates of ticks vs rates input - details in print statement")

    if firstRatesTime > firstTicksTime:
        ticksDat = ticksDat[ticksDat[timeCol] >= firstRatesTime].reset_index(drop = True)
    else:
        ratesDat = ratesDat[ratesDat[timeCol] >= firstTicksTime].reset_index(drop = True)

    if lastRatesTime > lastTicksTime:
        ratesDat = ratesDat[ratesDat[timeCol] <= lastTicksTime].reset_index(drop = True)
    else:
        ticksDat = ticksDat[ticksDat[timeCol] <= lastRatesTime].reset_index(drop = True)
        
    #Replacement Policy:
        #1: Replace extreme (spread > 1000pips) & zeroes with spread average of past 5/forward 5 values
        #2: Replace extreme & missing bid/ask with close +- replacementSpread parameter        

    #Get occurences where there is both ASK & BID Data
   
    #Replace extreme values (spread > 1000pips) - have seen this before 
    extremeIdx = ticksDat.loc[abs(ticksDat['ASK'] - ticksDat['BID']) > 0.1].index.values
    ticksDat.loc[extremeIdx, ['BID', 'ASK']] = np.nan
    
    #Clear out the rest of nans
    ticksDat = ticksDat[-(ticksDat['ASK'].isnull() | ticksDat['BID'].isnull())]

    #Floor
    ticksDat.loc[:, timeCol] = ticksDat.loc[:,timeCol].dt.floor(freq = floorFreq)

    #Merge
    concatDF = ratesDat.merge(ticksDat, how = 'left', on = timeCol).groupby(timeCol).first().reset_index()

    #Replace values    
    missingIDX = concatDF[concatDF['BID'].isnull() | concatDF['ASK'].isnull()].index.values

    if ticksCleanFlag == 1:
        #Average spread of 5 behind / 5 forward rounded to nearest pip
        #NB if unavailable for forward 5 (near end of Data), shift this range back as appropriate (and vice versa if at the start)
            # EG if 4 indexes from the end, use 7 behind / 3 forward rather than 5 / 5
        for idx in missingIDX:
            if len(concatDF) - idx <= 5:
                shiftFactor = (len(concatDF) - idx) - 6
            elif idx <= 5:                
                shiftFactor = 1 - idx
            else:
                shiftFactor = 0

            #idxGroup = list(np.arange(idx-5+shiftFactor, idx)) + list(np.arange(idx+1, idx+6+shiftFactor))
            #Update to only capture rolling window where bid/ask is already present from MT5.
            idxGroup = list(concatDF[~concatDF['BID'].isnull() & ~concatDF['ASK'].isnull()].iloc[idx-5+shiftFactor:idx].index.values) \
                + list(concatDF[~concatDF['BID'].isnull() & ~concatDF['ASK'].isnull()].iloc[idx:idx+6+shiftFactor-1].index.values)

            avgBidSpread = round(np.mean(concatDF.loc[idxGroup,'CLOSE'] - concatDF.loc[idxGroup, 'BID']), 5)
            avgAskSpread = round(np.mean(concatDF.loc[idxGroup, 'ASK'] - concatDF.loc[idxGroup, 'CLOSE']), 5)            
            concatDF.loc[idx, 'BID'] = concatDF.loc[idx, 'CLOSE'] - avgBidSpread
            concatDF.loc[idx, 'ASK'] = concatDF.loc[idx, 'CLOSE'] + avgAskSpread

    elif ticksCleanFlag == 2:
        #Flat spread
        for idx in missingIDX:
            concatDF.loc[idx, 'BID'] = concatDF.loc[idx, 'CLOSE'] - (replacementSpread/10000)
            concatDF.loc[idx, 'ASK'] = concatDF.loc[idx, 'CLOSE'] + (replacementSpread/10000)

    #Flag replaced values
    replacedBidAskList = [''] * len(concatDF)
    for idx in missingIDX:
        replacedBidAskList[idx] = 'Replaced'

    concatDF['ReplacedBidAsk'] = replacedBidAskList

    concatDF = concatDF[[timeCol, 'OPEN', 'HIGH', 'LOW', 'CLOSE', 'BID', 'ASK', 'ReplacedBidAsk']]

    return concatDF

##An example of running.

#Set up datafolders - this is just my style of doing things.
ratesDatFolder = os.path.join(os.getcwd(), "ExampleDatasets", "OHLC_Only")
ticksDatFolder = os.path.join(os.getcwd(), "ExampleDatasets", "TicksData")

ratesFileName = "EURUSD.a_M1_202111010000_202204292356.csv"
#Given the size of the ticks data and githubs 100mb limit, a small dataset is used as an example here.
ticksFileName = "EURUSD.a_202201030101_202201312358.csv" 

ratesDir = os.path.join(ratesDatFolder, ratesFileName)
ticksDir = os.path.join(ticksDatFolder, ticksFileName)

ratesDat = pd.read_csv(ratesDir, sep = "\t", parse_dates = [[0, 1]])
ticksDat = pd.read_csv(ticksDir, sep = "\t", parse_dates = [[0, 1]])

#This handles the naming of MT5 Data for input.
for oldCol in ratesDat.columns:
    ratesDat.rename(columns = {oldCol: oldCol.replace('<', '').replace('>', '').replace('_', '')}, inplace = True)

for oldCol in ticksDat.columns:
    ticksDat.rename(columns = {oldCol: oldCol.replace('<', '').replace('>', '').replace('_', '')}, inplace = True)

#Function Call
EURUSDM1_dat = ratesTicksConcatenator(ratesDat, ticksDat, '1T')

#Use dates for file naming
startDate = EURUSDM1_dat.iloc[0, 0]
endDate = EURUSDM1_dat.iloc[-1, 0]

#Set up export
exportFolder = os.path.join(os.getcwd(), "ExampleDatasets", "ConcatExport")
exportName = "EURUSD.a_M1_{}_{}.csv".format(startDate.strftime("%d%m%Y"), endDate.strftime("%d%m%Y")) 
exportDir = os.path.join(exportFolder, exportName)
EURUSDM1_dat.to_csv(exportDir, index = False)