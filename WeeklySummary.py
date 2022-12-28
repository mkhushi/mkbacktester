import pandas as pd
import datetime
import os

def get_weekly_summary(data, frequency_str):

    #Break down into weeks and set up lists containing start/end date for each week
    n_days = data['time'].iloc[-1] - data['time'].iloc[0]
    start_dates = [data['time'].iloc[0]]

    if frequency_str == "M15":
        end_dates = [data['time'].iloc[0] + datetime.timedelta(days = 6, hours = 23, minutes = 45)]
    elif frequency_str == "M05" or frequency_str == "M5":
        end_dates = [data['time'].iloc[0] + datetime.timedelta(days = 6, hours = 23, minutes = 55)]
    elif frequency_str == "D1":
        end_dates = [data['time'].iloc[0] + datetime.timedelta(days = 7)]
    elif frequency_str == "H1":
        end_dates = [data['time'].iloc[0] + datetime.timedelta(days = 6, hours = 23)]
    elif frequency_str == "M1":
        end_dates = [data['time'].iloc[0] + datetime.timedelta(days = 6, hours = 23, minutes = 59)]

    weeks = [1]
    for i in range(1, (n_days.days // 7) + 1):
        start_dates.append(start_dates[-1] + datetime.timedelta(days = 7))
        end_dates.append(end_dates[-1] + datetime.timedelta(days = 7))
        weeks.append(i+1)
    end_dates[-1] = data['time'].iloc[-1]
    
    #Set up dataframe & lists for data
    weekly_update_df = pd.DataFrame({"Week": weeks, "Start Date": start_dates, "End Date": end_dates})
    
    weekly_trades_total_list = []
    weekly_trades_won_list = []
    weekly_trades_lost_list = []
    weekly_pnl_list = []

    #Iterate through each week
    for i in range(0, len(weekly_update_df)):
        weekly_won = 0
        weekly_lost = 0

        #Calculations
        weekly_vals = data[(data['time'] >= weekly_update_df['Start Date'].iloc[i]) & (data['time'] <= weekly_update_df['End Date'].iloc[i])]
        if weekly_vals.empty:
            weekly_trades = 0
            weekly_pnl = 0
        else:
            weekly_trades = (weekly_vals['action'] == 'close short').sum() + (weekly_vals['action'] == 'close long').sum()
            weekly_pnl = weekly_vals['Total profit'].iloc[-1] - weekly_vals['Total profit'].iloc[0]

            for j in range(1, len(weekly_vals)):
                if weekly_vals['Total profit'].iloc[j] > weekly_vals['Total profit'].iloc[j-1]:
                    weekly_won += 1
                elif weekly_vals['Total profit'].iloc[j] < weekly_vals['Total profit'].iloc[j-1]:
                    weekly_lost += 1

        weekly_trades_total_list.append(weekly_trades)
        weekly_trades_won_list.append(weekly_won)
        weekly_trades_lost_list.append(weekly_lost)
        weekly_pnl_list.append(weekly_pnl)

    #Insert into dataframe
    weekly_update_df['Total Trades'] = weekly_trades_total_list
    weekly_update_df['Trades Won'] = weekly_trades_won_list
    weekly_update_df['Trades Lost'] = weekly_trades_lost_list
    weekly_update_df['Realised PnL'] = weekly_pnl_list
    weekly_update_df['winPercentage'] = round(weekly_update_df['Trades Won'] / weekly_update_df['Total Trades'],2 ) * 100

    return weekly_update_df