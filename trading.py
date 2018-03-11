# -*- coding: utf-8 -*-
from indicator import *
from strategy import *

def my_logic(time, open, close, high, low, volume, strategy, **env):
	# print(time[0])
	# print(open[0])
	# print(close[0])
	# print(high[0])
	# print(low[0])
	# print(volume[0])
	d = {
		'close': close[0],
		'sma': sma(close, 10),
		'ema': ema(close, 10),
		'highest': highest(close, 10),
		'lowest': lowest(close, 10),
	}
	print('{close},{sma},{ema},{highest},{lowest},'.format(**d))

myst = Strategy(my_logic)
myst.interval = 5
myst.run_loop()
