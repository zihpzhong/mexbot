# -*- coding: utf-8 -*-
from strategy import *

def my_logic():
	print('test')

strategy.period = 3
strategy.run_loop(my_logic)
