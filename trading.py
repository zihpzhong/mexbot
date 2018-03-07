# -*- coding: utf-8 -*-
from strategy import *

def my_logic():
	print("my_logic")	

myst = strategy()
myst.run_loop(my_logic)
