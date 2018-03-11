# -*- coding: utf-8 -*-

def sma(series, period):
    return series[0:period].mean()

def ema(series, period):
    return series[period-1::-1].ewm(span=period).mean()[0]

def highest(series, period):
    return series[0:period].max()

def lowest(series, period):
    return series[0:length].min()
