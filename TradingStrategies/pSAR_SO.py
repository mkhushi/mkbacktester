import pandas as pd
import ta
from .IndicatorFunctions.StochasticOscilator import StochasticOscilator

class pSAR_SO:
    def __init__(self):

        self.indicatorDf = None
        self.Name = "pSAR_SO"

    def addData(self, data):
        self.df = data
        self.open = self.df["open"]
        self.high = self.df["high"]
        self.low = self.df["low"]
        self.close = self.df["close"]
    
    def calculate_pSAR(self):
        self.df["pSAR"] = ta.trend.PSARIndicator(high = self.high, low = self.low, close = self.close, step = 0.02, max_step = 0.2).psar()

    def calculate_SO(self):
        self.df["slow_k"], self.df["slow_d"] = StochasticOscilator(self.df, K = 14, D = 3, slowing = 3)        

    def addIndicatorDf(self):
        self.indicatorDf = self.df[['time', 'pSAR', 'slow_k', 'slow_d']]
    
    def determine_signal(self):
        action = 0

        pSAR = self.df['pSAR']
        close = self.df['close']
        slow_k = self.df['slow_k']
        slow_d = self.df['slow_d']

        #Buy Criteria
        # pSAR flips from below close to above in the past 3 bars, and slowK or slowD below 30
        if (pSAR.iloc[-3] < close.iloc[-3] and pSAR.iloc[-1] > close.iloc[-1]) and (slow_k.iloc[-1] < 30 or slow_d.iloc[-1] < 30):
            
            action = 1

        #Sell Criteria
        # pSAR flips from above close to below in the past 3 bars, and slowK or slowD above 70
        elif (pSAR.iloc[-3] > close.iloc[-3] and pSAR.iloc[-1] < close.iloc[-1]) and (slow_k.iloc[-1] > 70 or slow_d.iloc[-1] > 70):

            action = -1

        return action

    def run(self, data):
        self.addData(data)
        self.calculate_pSAR()
        self.calculate_SO()
        self.addIndicatorDf()
        signal = self.determine_signal()

        return signal, self.indicatorDf
