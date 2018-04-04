# -*- coding: utf-8 -*-
import pandas as pd

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
