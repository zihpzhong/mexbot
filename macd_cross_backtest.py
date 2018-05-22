# -*- coding: utf-8 -*-
import argparse
import datetime
import dateutil.parser
import pandas as pd
import numpy as np
from datetime import datetime
from backtest import Backtest, BacktestReport, BacktestIteration
from hyperopt import hp
from numba import jit
from indicator import *
from functools import lru_cache
from functools import wraps
import redis
import pickle

def store_datetime(str):
    return dateutil.parser.parse(str)

parser = argparse.ArgumentParser(description="")
parser.add_argument("--start", type=store_datetime)
parser.add_argument("--end", type=store_datetime)
args = parser.parse_args()

r = redis.StrictRedis(host='localhost', port=6379, db=0)

def redis_cache(r):
    def _redis_cache(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            k = str(func)+str(args)+str(kwargs)
            v = r.get(k)
            if v is None:
                v = func(*args, **kwargs)
                r.set(k, pickle.dumps(v))
            else:
                v = pickle.loads(v)
            return v
        return wrapper
    return _redis_cache

#@redis_cache(r)
def read_ohlc(filename):
    return pd.read_csv(filename, index_col='timestamp', parse_dates=True)

ohlcv = read_ohlc('csv/bitmex_2018_1h.csv')

if args.start is not None and args.end is not None:
    ohlcv = ohlcv[args.start:args.end]
elif args.start is None:
    ohlcv = ohlcv[:args.end]
elif args.end is None:
    ohlcv = ohlcv[args.start:]

@lru_cache(maxsize=None)
#@redis_cache(r)
def cached_sma(period):
    return ohlcv.close.rolling(int(period)).mean()

@lru_cache(maxsize=None)
#@redis_cache(r)
def cached_macd(fastlen, slowlen, siglen):
    macd = cached_sma(fastlen) - cached_sma(slowlen)
    signal = macd.rolling(int(siglen)).mean()
    return (macd, signal, macd-signal)

@jit
def macd_cross_backtest(fastlen, slowlen, siglen, smafastlen, smaslowlen, use_sma):

    # インジケーター作成
    vmacd, vsig, vhist = cached_macd(fastlen, slowlen, siglen)
    if use_sma:
        vfast = cached_sma(smafastlen)
        vslow = cached_sma(smaslowlen)

    # エントリー／イグジット
    if use_sma:
        long_entry = crossover(vmacd, vsig) | crossover(vfast, vslow)
        short_entry = crossunder(vmacd, vsig) | crossunder(vfast, vslow)
    else:
        long_entry = crossover(vmacd, vsig)
        short_entry = crossunder(vmacd, vsig)
    long_exit = short_entry
    short_exit = long_entry

    long_entry_price = None
    long_exit_price = None
    short_entry_price = None
    short_exit_price = None

    ignore = int(max([fastlen, slowlen, smafastlen, smaslowlen]))
    long_entry[:ignore] = False
    long_exit[:ignore] = False
    short_entry[:ignore] = False
    short_exit[:ignore] = False

    lots = (1000 / ohlcv.close)

    entry_exit = pd.DataFrame({'close':ohlcv.close, 'macd':vmacd, 'sig':vsig, #'fast':vfast, 'slow':vslow,
        'long_entry_price':long_entry_price, 'long_exit_price':long_exit_price, 'long_entry':long_entry, 'long_exit':long_exit,
        'short_entry_price':short_entry_price, 'short_entry':short_entry, 'short_exit_price':short_exit_price, 'short_exit':short_exit})#, index=ohlcv.index)
    entry_exit.to_csv('entry_exit.csv')

    report = Backtest(ohlcv, buy_entry=long_entry, sell_entry=short_entry, buy_exit=long_exit, sell_exit=short_exit,
        stop_buy_entry=long_entry_price, stop_sell_entry=short_entry_price, stop_buy_exit=long_exit_price, stop_sell_exit=short_exit_price,
        lots=1, spread=0, take_profit=0, stop_loss=0, trailing_stop=0, slippage=0)#, percent_of_equity=(1, 1000))
    return report

default_parameters = {
    'fastlen':19,
    'slowlen':27,
    'siglen':13,
    'smafastlen':19,
    'smaslowlen':27,
    'use_sma':False,
}

hyperopt_parameters = {
    'fastlen': hp.quniform('fastlen', 5, 50, 1),
    'slowlen': hp.quniform('slowlen', 5, 50, 1),
    'siglen': hp.quniform('siglen', 1, 50, 1),
    # 'smafastlen': hp.quniform('smafastlen', 1, 50, 1),
    # 'smaslowlen': hp.quniform('smaslowlen', 1, 50, 1),
}

BacktestIteration(macd_cross_backtest, default_parameters, hyperopt_parameters, 0)
