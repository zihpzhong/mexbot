# -*- coding: utf-8 -*-
import pandas as pd

# index 0 が最新値、1が1つ前、-1 が最古値であることに注意

def sma(series, window):
    return series.rolling(window).mean()

def ema(series, window):
    return series[-1::-1].ewm(span=window).mean()

def highest(series, window):
    return series[-1::-1].rolling(window).max()

def lowest(series, window):
	return series[-1::-1].rolling(window).min()

def stdev(series, window):
	return series[-1::-1].rolling(window).std()
