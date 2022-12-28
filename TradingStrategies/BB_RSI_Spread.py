import pandas as pd
import ta

'''
@ Vita
https://www.dailyfx.com/forex/education/trading_tips/daily_trading_lesson/2020/01/09/macd-histogram.html

'''


class BB_RSI_Spread:

    def __init__(self):
        
        self.Name = "BB_RSI_Spread"
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
        self.df['bb_spread_stdev'] = [0] * len(data)
        self.df['bb_spread'] = [0] * len(data)
        
    def add_bollinger_bands(self):
        # Add Bollinger Bands features
        from ta.volatility import BollingerBands
        from ta.momentum import RSIIndicator
        indicator_bb = BollingerBands(close=self.df["close"], window=20, window_dev=2)
        self.df['bb_bbm'] = indicator_bb.bollinger_mavg()
        self.df['bb_bbh'] = indicator_bb.bollinger_hband()
        self.df['bb_bbl'] = indicator_bb.bollinger_lband()        
        self.df['bb_spread'] = self.df['bb_bbh'] - self.df['bb_bbl']
        self.df['bb_spread_stdev'] = self.df['bb_spread'].rolling(window = 14).std()
        
        rsi = RSIIndicator(close=self.df["close"], window=14)
        self.df['rsi'] = rsi.rsi()
        
        
    def determine_signal(self):
        # sell = -1, hold = 0, buy = 1, initialise all as hold first

        action = 0
        df = self.df
        
# self.df.high.iloc[:-1].max(): # max of last n-1 items
        # buy signal
        if  df.close.iloc[-1] > df.high.iloc[-2] and \
            ((df.low.iloc[-2]-df.bb_bbl.iloc[-2])<0.0003 or (df.high.iloc[-2]-df.bb_bbl.iloc[-2])<0.0003 ) and \
            df.bb_spread_stdev.iloc[-1] <=  df.bb_spread.iloc[-1]    :
            # and \ df.rsi.iloc[-1]<40: 
            action = 1
        
        # sell signal
        if  df.close.iloc[-1] < df.low.iloc[-2] and \
            ((df.high.iloc[-2]-df.bb_bbh.iloc[-2])<0.0003 or (df.low.iloc[-2]-df.bb_bbh.iloc[-2])<0.0003 ) and \
            df.bb_spread_stdev.iloc[-1] <=  df.bb_spread.iloc[-1]    :
                # and \            df.rsi.iloc[-1]>70: 
            action = -1
            
        
        # if((dframe['bb_spread'].iloc[-1] > dframe['bb_spread_low_band'].iloc[-1]) 
        #    & (dframe['bb_spread'].iloc[-1] < dframe['bb_spread_high_band'].iloc[-1]) 
        #    & (dframe['rsi'].iloc[-1] <= 50)):
        #     signal = 1
        # # BUY if price breaks bb upper
        # if(dframe['close'].iloc[-1] < dframe['bb_low_band'].iloc[-1]):
        #     signal = 1
        # # BUY if BB spread is large and RSI >= 70
        # if((dframe['bb_spread'].iloc[-1] >= dframe['bb_spread_high_band'].iloc[-1]) 
        #    & (dframe['rsi'].iloc[-1] >= 70)):
        #     signal = 1        
        
            

        return action

    def addIndicatorDf(self):
        # self.indicatorDf = self.df[['time', 'macd_line', 'macd_signal']]
        self.indicatorDf = self.df[['time', 'bb_bbh','bb_bbl', 'rsi']]

    def run(self, data):
        self.addData(data)
        self.add_bollinger_bands()
        self.addIndicatorDf()
        return self.determine_signal() , self.indicatorDf
