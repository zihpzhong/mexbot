# -*- coding: utf-8 -*-
from strategy import *

def my_logic(open, close, high, low, volume, strategy, **env):
	print(strategy)
	print(open)
	print(close)
	print(high)
	print(low)
	print(volume)
	print(env)

myst = Strategy(my_logic)
myst.run_loop()
