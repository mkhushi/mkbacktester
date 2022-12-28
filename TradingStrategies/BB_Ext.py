import pandas as pd
import ta

'''
@ Vita
https://www.dailyfx.com/forex/education/trading_tips/daily_trading_lesson/2020/01/09/macd-histogram.html

'''


class BB_Ext:

    def __init__(self):
        
        self.Name = "BB_Ext"
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
        indicator_bb = BollingerBands(close=self.df["close"], window=20, window_dev=2)
        self.df['bb_bbm'] = indicator_bb.bollinger_mavg()
        self.df['bb_bbh'] = indicator_bb.bollinger_hband()
        self.df['bb_bbl'] = indicator_bb.bollinger_lband()        
        rsi = RSIIndicator(close=self.df["close"], window=14)
        self.df['rsi'] = rsi.rsi()
        
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
        # buy signal
        if  (  df.close.iloc[-1] > df.high.iloc[-2] and \
             (abs(df.low.iloc[-2]-df.bb_bbl.iloc[-2])<0.0003 or abs(df.high.iloc[-2]-df.bb_bbl.iloc[-2])<0.0003 ) ) \
            or ( \
                df.close.iloc[-1] > df.high.iloc[-2] and \
            (df.close.iloc[-1] > df.bb_bbh.iloc[-2] and df.close.iloc[-1] > max(df.close[:-50])) ):
            
            action = 1
            
        # sell signal
        if  ( df.close.iloc[-1] < df.low.iloc[-2] and \
              (abs(df.high.iloc[-2]-df.bb_bbh.iloc[-2])<0.0003 or abs(df.low.iloc[-2]-df.bb_bbh.iloc[-2])<0.0003 ) )\
           or ( \
               df.close.iloc[-1] < df.low.iloc[-2] and \
           (df.close.iloc[-1] < df.bb_bbl.iloc[-2] and df.close.iloc[-1] < min(df.close[:-50])) ):
                
            action = -1
            

        return action

    def addIndicatorDf(self):
        # self.indicatorDf = self.df[['time', 'macd_line', 'macd_signal']]
        self.indicatorDf = self.df[['time', 'bb_bbh','bb_bbl', 'rsi']]

    def run(self, data):
        self.addData(data)
        self.add_bollinger_bands()
        self.addIndicatorDf()
        return self.determine_signal() , self.indicatorDf
