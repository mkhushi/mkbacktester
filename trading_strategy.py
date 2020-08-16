import talib as ta 
import pandas as pd
import numpy as np

# This funciton can be replaced by your trading strategy. 
# The function must one of the following three 
# 	1     - BUY
# 	0     - HOLD
# 	-1    - SELL
def trading_strategy(inputs):
	# This demo trading strategy is build on cross over of moving averages of 5 and 20 periods (data points) .
	df = pd.DataFrame(inputs)
	
	sma5_list = ta.SMA(df['close'] , 5)
	ema20_list = ta.EMA(df['close'] , 20)

	arr = np.array(sma5_list)
	df['sma5'] = arr.tolist()
	arr = np.array(ema20_list)
	df['ema20'] = arr.tolist()
	
	sma5 = df['sma5'].iloc[-1]
	ema20 = df['ema20'].iloc[-1]
	last_sma5 = df['sma5'].iloc[-2]
	last_ema20 = df['ema20'].iloc[-2]
	if ~np.isnan(last_sma5) and ~np.isnan(last_ema20):
		if (last_sma5 < last_ema20 and sma5 >= ema20):
			return 1  # buy
		elif (last_sma5 > last_ema20 and sma5 <= ema20):
			return -1 # sell 
		else:
			return 0 # do nothing


def trading_strategySD(inputs):	
	df = pd.DataFrame(inputs)
	current_std = df['close'][-3:len(df)].std()   # std of last 3 prices
	past_std = df['close'][-15:-3].std()

	if df['close'].iloc[-1] > df['close'][-15:-3].max() and current_std > 1.5 * past_std:
			return 1 # buy
	elif df['close'].iloc[-1] < df['close'][-15:-3].min() and current_std > 1.5 * past_std:
			return 1 # sell
	else:
		return 0