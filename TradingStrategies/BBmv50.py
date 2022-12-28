import pandas as pd
import ta
import datetime as dt
from sklearn import linear_model
import numpy as np
'''
@ Vita
https://www.dailyfx.com/forex/education/trading_tips/daily_trading_lesson/2020/01/09/macd-histogram.html

'''


class BBmv50:

    def __init__(self):
        
        self.Name = "BBmv50"
        self.indicatorDf = None

    def addData(self, data):
        
        self.df = data

        self.close = self.df['close']
        self.high = self.df['high']
        self.low = self.df['low']

        self.df['bb_bbh'] = [0] * len(data)
        self.df['bb_bbl'] = [0] * len(data)
        self.df['bb_bbm'] = [0] * len(data)
        self.df['rsi'] = [0] * len(data)
        self.df['mv50'] = [0] * len(data)
        
    def add_bollinger_bands(self):
        # Add Bollinger Bands features
        from ta.volatility import BollingerBands
        from ta.momentum import RSIIndicator
        from ta.trend import sma_indicator
        
        indicator_bb = BollingerBands(close=self.df["close"], window=20, window_dev=2)
        self.df['bb_bbm'] = indicator_bb.bollinger_mavg()
        self.df['bb_bbh'] = indicator_bb.bollinger_hband()
        self.df['bb_bbl'] = indicator_bb.bollinger_lband()        
        
        rsi = RSIIndicator(close=self.df["close"], window=14)
        self.df['rsi'] = rsi.rsi()
        
        
        self.df['mv50'] = sma_indicator(close=self.df["close"], window=50)
        
        # Add Bollinger Band high indicator
        # df['bb_bbhi'] = indicator_bb.bollinger_hband_indicator()
        
        # Add Bollinger Band low indicator
        # df['bb_bbli'] = indicator_bb.bollinger_lband_indicator()
        
        # Add Width Size Bollinger Bands
        # df['bb_bbw'] = indicator_bb.bollinger_wband()
        
        # Add Percentage Bollinger Bands
        # df['bb_bbp'] = indicator_bb.bollinger_pband()    #     self.df['macd_signal'] = ta.trend.MACD(close=self.df['close']).macd_signal()

    def determine_signal(self):
        # sell = -1, hold = 0, buy = 1, initialise all as hold first

        action = 0
        df = self.df
        
# self.df.high.iloc[:-1].max(): # max of last n-1 items


        x = [x for x in range(20)]
        y = df['mv50'][-20:].values
        
        slope = np.polyfit(x,y,1)[0] * 10000
        # buy signal
        if  df.close.iloc[-1] > df.high.iloc[-2] and \
            (abs(df.low.iloc[-2]-df.bb_bbl.iloc[-2])<0.0003 or abs(df.high.iloc[-2]-df.bb_bbl.iloc[-2])<0.0003 ) and \
            (abs(df.low.iloc[-2]-df.mv50.iloc[-2])<0.0003 or abs(df.high.iloc[-2]-df.mv50.iloc[-2])<0.0003 ) and \
            slope > 0.1    :
            # print("slope: ", slope)
            action = 1
        # sell signal
        if  df.close.iloc[-1] < df.low.iloc[-2] and \
            (abs(df.high.iloc[-2]-df.bb_bbh.iloc[-2])<0.0003 or abs(df.low.iloc[-2]-df.bb_bbh.iloc[-2])<0.0003 )  and \
            (abs(df.low.iloc[-2]-df.mv50.iloc[-2])<0.0003 or abs(df.high.iloc[-2]-df.mv50.iloc[-2])<0.0003 ) and \
            slope < 0.1    :
                # and \            df.rsi.iloc[-1]>70: 
            action = -1
            # print("slope: ", slope)

        return action

    def addIndicatorDf(self):
        # self.indicatorDf = self.df[['time', 'macd_line', 'macd_signal']]
        self.indicatorDf = self.df[['time', 'bb_bbh','bb_bbl', 'rsi']]

    def run(self, data):
        self.addData(data)
        self.add_bollinger_bands()
        self.addIndicatorDf()
        return self.determine_signal() , self.indicatorDf
