import os
import pandas as pd
import datetime

def get_trade_summary(data):

    data = data[['time', 'close', 'signal', 'action', 'Executed price', 'position', 'Total profit']]
    #Add Executed Trade Price to history 
    trades_summary_df = pd.DataFrame({"Trade Type": [], "Trade Open Time": [], "Trade Open Price": [], \
        "Trade Close Time": [], "Trade Close Price": [], "Trade P/L": []})
    
    trades_df = data.loc[data['action'] != 'hold'].reset_index(drop = True)

    #Remove the last trade entry if it was not closed - deemed as incomplete trade
    if not 'close' in trades_df.loc[len(trades_df)-1, 'action']:
        trades_df = trades_df[:-1]

    trades_opened = trades_df.loc[(trades_df.loc[:, 'action'] == 'buy') | (trades_df.loc[:, 'action'] == 'short')].reset_index(drop = True)
    trades_closed = trades_df.loc[(trades_df.loc[:, 'action'] == 'close long') | (trades_df.loc[:, 'action'] == 'close short')].reset_index(drop = True)

    trades_opened = trades_opened[['action', 'time', 'Executed price', 'Total profit']]
    trades_opened.rename(columns = {'action': 'Trade Type', 'time': 'Trade Open Time', 'Executed price': 'Trade Open Price', 'Total profit': 'Open PnL'}, inplace = True)

    trades_closed = trades_closed[['time', 'Executed price', 'Total profit']]
    trades_closed.rename(columns = {'time': 'Trade Close Time', 'Executed price': 'Trade Close Price', 'Total profit': 'Close PnL'}, inplace = True)

    trades_summary_df = trades_opened.merge(trades_closed, left_index = True, right_index = True)
    trades_summary_df['Trade P/L'] = trades_summary_df['Close PnL'] - trades_summary_df['Open PnL']

    trades_summary_df.drop(columns = ['Open PnL', 'Close PnL'], inplace = True)

    if len(trades_summary_df.loc[trades_summary_df['Trade Open Time'] > trades_summary_df['Trade Close Time']]):
        raise Exception('Trade summary does not reconcile - Trades are recorded as closing before they have opened.')

    return trades_summary_df