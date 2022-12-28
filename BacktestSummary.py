import pandas as pd


def get_backtest_summary(historyDat, currency, frequency_str):

    summary_df = pd.DataFrame()

    start_date = historyDat.loc[0, 'time']
    end_date = historyDat.loc[len(historyDat)-1, 'time']

    summary_df['Start'] = [start_date.strftime("%Y-%m-%d %H:%S")]
    summary_df['End'] = end_date.strftime("%Y-%m-%d %H:%S")

    trades_total = len(historyDat.loc[(historyDat['action'] == 'close short') | (historyDat['action'] == 'close long')])
    trades_won = len(historyDat.loc[(historyDat['action'] == 'close long') | (historyDat['action'] == 'close short')].loc[historyDat['P/L'] > 0])
    trades_lost = len(historyDat.loc[(historyDat['action'] == 'close long') | (historyDat['action'] == 'close short')].loc[historyDat['P/L'] < 0])
    trades_tied = trades_total - trades_won - trades_lost
    total_pnl = historyDat.loc[len(historyDat)-1, 'Total profit']

    summary_df['Frequency'] = [frequency_str]
    summary_df['Currency Pair'] = [currency]
    summary_df['Total Trades'] = [trades_total]
    summary_df['Total P/L'] = [total_pnl]
    summary_df['Total P/L (pips)'] = [total_pnl * 10000]
    summary_df['Trades Won (n)'] = [trades_won]
    summary_df['Trades Won (%)'] = [(trades_won/trades_total) * 100 if trades_total > 0 else 0]
    summary_df['Trades Lost (n)'] = [trades_lost]
    summary_df['Trades Lost (%)'] = [(trades_lost/trades_total) * 100 if trades_total > 0 else 0]
    summary_df['Trades Tied (n)'] = [trades_tied]
    summary_df['Trades Tied (%)'] = [(trades_tied/trades_total) * 100 if trades_total > 0 else 0]
    return summary_df