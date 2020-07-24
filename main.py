import os

import pandas as pd
pd.options.mode.chained_assignment = None
import time
from collections import deque
from signalHandler import signalHandler
from visualise import visualise
from trading_strategy import trading_strategy

############# READ FILE #############

data = pd.read_csv('GBPUSD_H1_202001020600_202006010000.csv',sep='\t', skiprows=1, names = ['date', 'time', 'open', 'high', 'low', 'close', 'tickvol','vol','spread' ])
data = data.drop(['tickvol', 'vol','spread'], axis=1)  # we do not need these coloumns

############# Hyperparameters #############
input_row_size = 30         # <----- Minimum number of inputs required by YOUR trading strategy
one_pip = 0.0001            # <----- Indicating the value of 1 pip, i.e. usually 0.0001 for all major fx except for JPY pairs (0.01)
stop_loss = -10*one_pip     # <----- (THIS WILL CHANGE!!, if the code recieves SELL sequentially the stop loss will be reduced)   The max amount of loss
take_profit = 20*one_pip    # <----- (THIS WILL CHANGE!!, if the code recieves BUY sequentially the take profit will be increased)The max amount of profit
broker_cost = 2*one_pip
inputs = deque(maxlen=input_row_size)
############# BACKTESTING #############
# Handels Buy and Sell
broker = signalHandler(stop_loss,take_profit,broker_cost,data)

start_time = time.time() 
index = 0
signal = 0
for _,row in data.iterrows():

    # Loading the inputs array till the 
    # minimum number of inputs are reached
    inputs.append(row)
    
    if len(inputs) == input_row_size:
        signal = trading_strategy(list(inputs)) # <----- USE to call trading strategy

        # Current Price
        current_price = row['close']  
        
        # Checks signal and executes
        if signal == 1:
            broker.buy(current_price,index)
        elif signal == -1:
            broker.sell(current_price,index)
        elif signal == 0:
            # Checking if stop loss or take profit is hit
            broker.checkStopConditions(current_price,index)
        else:
            print("Unknown Signal")
            break
     
    index += 1

end_time = time.time()
print("Time consumed: {}s".format(round(end_time-start_time,2)))

final_data = broker.getData() # <----- Gets Data into a DATAFRAME
final_data.to_csv('backtesting.csv')
# final_data has THREE new coloumns
#   'action'        : The action the code implemented at that timestep.
#   'P/L'           : The profit or loss at the time step, 0 when holding.
#   'Total profit'  : The total profit TILL that time step. 

############# VISUALISEING #############
visualiser = visualise(final_data)
visualiser.plotFig()