# -*- coding: utf-8 -*-

def sma(series, window):
    return series.rolling(window).mean()

def ema(series, window):
    return series[-1::-1].ewm(span=window).mean()

def highest(series, window):
    return series[-1::-1].rolling(window).max()

def lowest(series, window):
	return series[-1::-1].rolling(window).min()
