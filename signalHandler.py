import pandas as pd
import numpy as np
import datetime
import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)
pd.set_option('mode.chained_assignment', None)

class signalHandler:
    """
    Class for acting as a broker or handling signals of the backtest process.
    """
    
    def __init__(self, stop_loss, take_profit, guaranteed_sl, broker_cost, limit_type, dynamic_limits,\
        hold_direction, data, asset, frequency, start_date, end_date, storeIndicators = 1):

        """
        Parameters:
        stopLoss (float): Stop loss level in absolute value, not pips.
        takeProfit (float): Take profit level in absolute value, not pips.
        guaranteedSl (bool): Whether to implement a guaranteed stoploss/takeprofit, or if stop conditions are based on the next available price.
            Worth reading online regarding this point as this is topical with the use of brokers and impacts spreads/costs. 
        brokerCost (float): Flat cost of broker in absolute value, not pips.
        data (pd.DataFrame): The data used in the backtest.
        asset (str): String representation of the financial asset/instrument.
        frequency (str): String representation of the data frequency/interval.
        start_date (datetime): Start date of the backtest.
        end_date (datetime): End date of the backtest.
        storeIndicators (int): Integer Boolean representation for whether to store calculated indicator values in the history file.

        Note that these inputs should be handled automatically by the Backtest loadBroker method.
        """
                
        self.original_stop_loss = stop_loss
        self.original_take_profit = take_profit
        self.guaranteed_sl = guaranteed_sl #Boolean
        self.broker_cost = broker_cost
        self.limit_type = limit_type
        self.dynamic_limits = dynamic_limits
        self.hold_direction = hold_direction
        self.data = data
        self.stop_loss = stop_loss
        self.take_profit = take_profit
        self.asset = asset
        self.frequency = frequency
        self.start_date = start_date
        self.end_date = end_date                
        self.storeIndicators = storeIndicators
        if self.storeIndicators == 1:
            self.indicatorDf = pd.DataFrame()        

        self.prev_traded_position = 0
        self.prev_traded_price = None
        self.total_profit = 0

        data['signal'] = ''
        data['action'] = ''
        data['position'] = ''
        data['Trade P/L'] = ''
        data['Brokerage Cost'] = ''
        data['Total profit'] = ''
        data['Executed price'] = ''
        data['Take Profit'] = ''
        data['Stop Loss'] = ''

        n = len(data) - 1
        self.signal_list = [""]*n
        self.action = [""]*n
        self.position = [""]*n
        self.arr_broker_cost = [""]*n 
        self.arr_PL = [""]*n 
        self.arr_total_profit = [""]*n 
        self.executed_price = [""]*n
        self.stop_loss_px_list = [""]*n
        self.take_profit_px_list = [""]*n
        self.current_action = ""
        
        self.trades_total = 0
        self.trades_won = 0
        self.trades_lost = 0
        self.trades_tied = 0       
        self.summary_df = pd.DataFrame()

    def bandPL(self, PL, executed_price):
        """
        A function for finalising the PL level as well as hitting guaranteed stoploss/take profit.

        Parameters:
        PL (float): The pre-fee/cost P&L once a trade is closed.

        Returns:
        PL (float): The net P&L once a trade is closed, accounting for if a guaranteed limit is hit + the flat broker cost/fee.
        """

        if self.limit_type == 'Flat':
            self.curr_broker_cost = self.broker_cost
        elif self.limit_type == 'Percentage':
            self.curr_broker_cost = self.broker_cost * executed_price

        total_brokerage = self.curr_broker_cost + self.prev_brokerage_cost
        
        if self.guaranteed_sl:
            if PL > self.take_profit:
                PL = self.take_profit
            elif PL < self.stop_loss:
                PL = self.stop_loss
        else:
            PL = PL
        PL -= total_brokerage
        return PL

    def closeTrade(self, PL, executed_price, index):
        """
        Function called to handle updating attributes once a trade is closed.
        Parameters:
        PL (float): The P&L after bandPL to be added to the total profit.
        """
        
        #Count in total trades
        self.trades_total += 1

        PL = self.bandPL(PL, executed_price)

        # Reseting Current position,action and other attributes.
        if self.prev_traded_position == -1:
            self.current_action = "close short"
        elif self.prev_traded_position == 1:
            self.current_action = "close long"        
        
        self.store_executed_price(executed_price, index)
        self.total_profit += PL

        self.prev_traded_position = 0
        self.prev_traded_price = None

        self.stop_loss = self.original_stop_loss
        self.take_profit = self.original_take_profit
        self.take_profit_px = 0
        self.stop_loss_px = 0

        #Count if trade is succesful or not
        #NB Rounding to handle Floating Point Error
        if round(PL, 5) > 0:
            self.trades_won += 1
        elif round(PL, 5) < 0:
            self.trades_lost += 1
        elif round(PL, 5) == 0:
            self.trades_tied += 1

        self.prev_brokerage_cost = None
        
    def saveStats(self, PL, index):
        """
        Function used to save stats for the results files.

        Parameters:
        PL (float): The current P&L to save.
        index (int): The input index for where to save the stats in context of the history file.
        """
                
        self.action[index] = self.current_action
        self.arr_PL[index] = PL
        self.arr_total_profit[index] = self.total_profit
        self.position[index] = self.prev_traded_position

    def getHistory(self):        
        """
        Function used to summarise the backtest history once finalised.
        Aggregates everything into a dataframe - appending stats & indicatorDF to the input OHLC (+ bid/ask) data.
        
        Parameters:
        None

        Returns:
        self.data (pd.DataFrame): The finalised history dataframe.
        """        
        
        self.data = self.data.iloc[:-1] #Drop end as we have been executing at OpenT+1

        self.data['signal'] = self.signal_list
        self.data['action'] = self.action
        self.data['position'] = self.position
        self.data['Trade P/L'] = self.arr_PL
        self.data['Brokerage Cost'] = self.arr_broker_cost
        self.data['Total profit'] = self.arr_total_profit
        self.data['Executed price'] = self.executed_price
        self.data['Stop Loss'] = self.stop_loss_px_list
        self.data['Take Profit'] = self.take_profit_px_list

        #Indicator DF
        if self.storeIndicators == 1:
            insertIdx = self.data.columns.get_loc('signal')
            insertDF = self.indicatorDf.drop(columns = 'time')
            for i in range(len(insertDF.columns)):
                self.data.insert(loc = i + insertIdx, column = insertDF.columns.values[i], value = insertDF.iloc[:, i])

        return self.data
    
    def getSummary(self):
        """
        Function used for the summary of the backtest results.
        Summarises basic information of the backtest and total trade statistics.

        Parameters:
        None

        Returns:
        self.summary_df (pd.DataFrame): The resulting summary dataframe.
        """
        self.summary_df['Start'] = [self.start_date.strftime("%Y-%m-%d %H:%S")]
        self.summary_df['End'] = self.end_date.strftime("%Y-%m-%d %H:%S")
        self.summary_df['Asset'] = [self.asset]
        self.summary_df['Frequency'] = [self.frequency]
        self.summary_df['Total Trades'] = [self.trades_total]
        self.summary_df['Total P/L'] = [self.data['Total profit'].iloc[-1]]
        self.summary_df['Trades Won (n)'] = [self.trades_won]
        self.summary_df['Trades Won (%)'] = [(self.trades_won/self.trades_total) * 100 if self.trades_total > 0 else 0]
        self.summary_df['Trades Lost (n)'] = [self.trades_lost]
        self.summary_df['Trades Lost (%)'] = [(self.trades_lost/self.trades_total) * 100 if self.trades_total > 0 else 0]
        self.summary_df['Trades Tied (n)'] = [self.trades_tied]
        self.summary_df['Trades Tied (%)'] = [(self.trades_tied/self.trades_total) * 100 if self.trades_total > 0 else 0]
        return self.summary_df
    
    # Used to store signal for final summary df
    def storeSignalAndIndicators(self, signal, indicatorDf, index):
        """
        A function used to store the signal and indicator details at every iteration.

        Parameters:
        signal (int): The signal output from the trading strategy.
        indicatorDF (pd.DataFrame or None): The dataframe containing indicator values from the trading strategy.
        index (int): The index to store these statistics in reference to the history data.
        """

        if self.storeIndicators == 1 and indicatorDf is not None:
            if self.indicatorDf.empty:
                self.indicatorDf = indicatorDf
            else:
                self.indicatorDf = self.indicatorDf.append(indicatorDf.iloc[-1], ignore_index=True)
        self.signal_list[index] = signal
        
    def store_executed_price(self, executed_price, index):
        """
        A function to store the trade executed price in the history.

        Parameters:
        bid_price (float): The current bid price from the input data.
        ask_price (float): The current ask price from the input data.
            NB these are both substituted as Close price in the backtest if not bid/ask available.
        index (int): The index to store these statistics in reference to the history data.
        """
        self.executed_price[index] = executed_price
        self.arr_broker_cost[index] = self.curr_broker_cost

    ############### Actions ###############
    def buy(self, open_priceT1, high_price, low_price, close_price, index):
        """
        A function used to simulate a buy trade in the backtest.

        Parameters:
        bid_price (float): The current bid price from the input data.
        ask_price (float): The current ask price from the input data.
            NB these are both substituted as Close price in the backtest if not bid/ask available.
        index (int): The index to store this trade in reference to the history data.

        TODO: consider the updateLimits method. This can be enabled to widen limits if a stronger signal is received.        
        """
        
        #First get broker cost as used across all functions
        if self.limit_type == 'Flat':
            self.curr_broker_cost = self.broker_cost
        elif self.limit_type == 'Percentage':
            self.curr_broker_cost = open_priceT1 * self.broker_cost

        PL = 0 #Reset at the trade
        if self.prev_traded_position == 0:
            self.current_action = "buy"
            self.prev_traded_position = 1
            self.prev_traded_price = open_priceT1 #Executed at ask for a buy     

            if self.limit_type == 'Flat':
                self.stop_loss_px = self.prev_traded_price + self.stop_loss
                self.take_profit_px = self.prev_traded_price + self.take_profit
            elif self.limit_type == 'Percentage':
                self.stop_loss_px = self.prev_traded_price * (1 + self.stop_loss)
                self.take_profit_px = self.prev_traded_price * (1 + self.take_profit)

            self.stop_loss_px_list[index] = self.stop_loss_px
            self.take_profit_px_list[index] = self.take_profit_px

            self.saveStats(PL, index)
            self.store_executed_price(open_priceT1, index)
            self.prev_brokerage_cost = self.curr_broker_cost

        elif self.prev_traded_position == 1:
            # Reciving a stroger buy signal
            if self.dynamic_limits:
                self.updateLimits(high_price, low_price, close_price, index)
            else:
                self.checkStopConditions(close_price, high_price, low_price, index)

        elif self.prev_traded_position == -1:
            if self.hold_direction:
                self.checkStopConditions(close_price, high_price, low_price, index)
            else:
                self.current_action = "close short"
                PL = (self.prev_traded_position*(open_priceT1 - self.prev_traded_price)) #Executed at ask for a buy 
                self.closeTrade(PL, open_priceT1, index)
                self.saveStats(PL,index)
                self.store_executed_price(open_priceT1, index)

        else: 
            raise Exception ("Unknown Signal!")
        
        self.curr_broker_cost = ""

    def sell(self, open_priceT1, high_price, low_price, close_price, index):
        """
        A function used to simulate a sell trade in the backtest.

        Parameters:
        bid_price (float): The current bid price from the input data.
        ask_price (float): The current ask price from the input data.
            NB these are both substituted as Close price in the backtest if not bid/ask available.
        index (int): The index to store this trade in reference to the history data.

        TODO: consider the updateLimits method. This can be enabled to widen limits if a stronger signal is received.
        
        """        
        
        #First get broker cost as used across all functions
        if self.limit_type == 'Flat':
            self.curr_broker_cost = self.broker_cost
        elif self.limit_type == 'Percentage':
            self.curr_broker_cost = open_priceT1 * self.broker_cost

        PL = 0 # <----- Default for if currently holding
        if self.prev_traded_position == 0:
            self.current_action = "short"
            self.prev_traded_position = -1
            self.prev_traded_price = open_priceT1 #Executed at bid for a sell

            if self.limit_type == 'Flat':
                self.stop_loss_px = self.prev_traded_price - self.stop_loss
                self.take_profit_px = self.prev_traded_price - self.take_profit
            elif self.limit_type == 'Percentage':
                self.stop_loss_px = self.prev_traded_price * (1 - self.stop_loss)
                self.take_profit_px = self.prev_traded_price * (1 - self.take_profit)

            self.stop_loss_px_list[index] = self.stop_loss_px
            self.take_profit_px_list[index] = self.take_profit_px

            self.saveStats(PL, index)
            self.store_executed_price(open_priceT1, index)
            self.prev_brokerage_cost = self.curr_broker_cost

        elif self.prev_traded_position == -1:
            # Reciving a stronger sell signal,             
            if self.dynamic_limits:
                self.updateLimits(high_price, low_price, close_price, index)
            else:
                self.checkStopConditions(close_price, high_price, low_price, index)
        
        elif self.prev_traded_position == 1:
            if self.hold_direction:
                self.checkStopConditions(close_price, high_price, low_price, index)
            else:
                self.current_action = "close long"
                PL = (self.prev_traded_position*(open_priceT1 - self.prev_traded_price)) #Executed at bid for a sell + flat spread
                self.closeTrade(PL, open_priceT1, index)
                self.saveStats(PL,index)
                self.store_executed_price(open_priceT1, index)
        else: 
            raise Exception ("Unknown Signal!")

        self.curr_broker_cost = ""
    
    def checkStopConditions(self, close_price, high_price, low_price, index):
        """
        Function used to check stop conditions at each iteration and close trade if limits are hit.
        Conditions are evaluated based on high/low price where relevant.
        Running MtM PnL is based off current bar close price 

        Parameters:
        close_price (float): The current close price from the input data.
        high_price (float): The current high price from the input data.
        low_price (float): The current low price from the input data.            
        index (int): The index to store this information in reference to the history data.

        Returns:
        self.total_profit (float): The current total profit at this index.

        """
        PL = 0
        self.current_action = "hold"
        
        #Short
        if self.prev_traded_position == -1:

            PL = self.prev_traded_position * (close_price - self.prev_traded_price)

            #Take Profit
            if low_price <= self.take_profit_px:                
                PL = self.prev_traded_price - low_price
                self.closeTrade(PL, low_price, index)

            #Stop Loss
            elif high_price >= self.stop_loss_px:
                PL = self.prev_traded_price - high_price
                self.closeTrade(PL, high_price, index)

        #Long
        elif self.prev_traded_position == 1:

            PL = self.prev_traded_position * (close_price - self.prev_traded_price)
          
            #Take Profit
            if high_price >= self.take_profit_px:
                PL = high_price - self.prev_traded_price
                self.closeTrade(PL, high_price, index)  

            #Stop Loss
            elif low_price <= self.stop_loss_px:
                PL = low_price - self.prev_traded_price
                self.closeTrade(PL, low_price, index)         

        self.saveStats(PL,index)
        return self.total_profit

    def updateLimits(self, high_price, low_price, close_price, index):
        """
        A function being considered to adjust limits based on a stronger signal received.
            NOTE: This is based off current close price, as opposed to T+1 open.
        Resets the stop_loss_px and take_profit_px that the checkStopConditions checks.

        Parameters:
        high_price (float): The current high price to check stop loss hasn't been hit for shorts.
        low_price (float): The current low price to check stop loss hasn't been hit for longs.
        close_price (float): The current close price to apply the stop_loss/take_profit around.
        index (int): The current index to apply this to.

        """

        #Wish to check stop conditions, without fully closing the trade, then reset limits if also profitable.
        reset_flag = 0

        PL = self.prev_traded_position * (close_price - self.prev_traded_price)

        if self.prev_traded_position == 1:
            if low_price >= self.stop_loss_px and PL > 0:
                reset_flag = 1
                if self.limit_type == 'Flat':
                    self.stop_loss_px = close_price + self.stop_loss
                    self.take_profit_px = close_price + self.take_profit
                elif self.limit_type == 'Percentage':
                    self.stop_loss_px = close_price * (1 + self.stop_loss)
                    self.take_profit_px = close_price * (1 + self.take_profit)

        elif self.prev_traded_position == -1:
            if high_price <= self.stop_loss_px and PL > 0:
                reset_flag = 1
                if self.limit_type == 'Flat':
                    self.stop_loss_px = close_price - self.stop_loss
                    self.take_profit_px = close_price - self.take_profit
                elif self.limit_type == 'Percentage':
                    self.stop_loss_px = close_price * (1 - self.stop_loss)
                    self.take_profit_px = close_price * (1 - self.take_profit)

        if reset_flag:
            self.stop_loss_px_list[index] = self.stop_loss_px
            self.take_profit_px_list[index] = self.take_profit_px

            #Forego checking stop conditions, as we have updated these limits at the "end" of the bar.
            #Flag the action as updating limits, then save stats.
            self.current_action = "update Limits"
            self.saveStats(PL,index)
        else:
            self.checkStopConditions(close_price, high_price, low_price, index)