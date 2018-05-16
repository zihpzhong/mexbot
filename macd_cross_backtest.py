# -*- coding: utf-8 -*-
import pandas as pd
import numpy as np
from datetime import datetime
from backtest import Backtest, BacktestReport, BacktestIteration
from hyperopt import hp
from numba import jit
from indicator import *
from functools import lru_cache

# テストデータ読み込み
ohlcv = pd.read_csv('csv/bitmex_2018_1h.csv', index_col='timestamp', parse_dates=True)
#ohlcv = ohlcv[datetime(2018, 2, 1):]

@lru_cache(maxsize=32)
def cached_sma(period):
    return ohlcv.close.rolling(int(period)).mean()

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

    # entry_exit = pd.DataFrame({'close':ohlcv.close, 'macd':vmacd, 'sig':vsig,
    #     'long_entry_price':long_entry_price, 'long_exit_price':long_exit_price, 'long_entry':long_entry, 'long_exit':long_exit,
    #     'short_entry_price':short_entry_price, 'short_entry':short_entry, 'short_exit_price':short_exit_price, 'short_exit':short_exit})#, index=ohlcv.index)
    # entry_exit.to_csv('entry_exit.csv')

    report = Backtest(ohlcv, buy_entry=long_entry, sell_entry=short_entry, buy_exit=long_exit, sell_exit=short_exit,
        stop_buy_entry=long_entry_price, stop_sell_entry=short_entry_price, stop_buy_exit=long_exit_price, stop_sell_exit=short_exit_price,
        lots=1, spread=0, take_profit=0, stop_loss=0, trailing_stop=0, slippage=0)
    return report

default_parameters = {
    'fastlen':19,
    'slowlen':27,
    'siglen':13,
    'smafastlen':22,
    'smaslowlen':26,
    'use_sma':False,
}

hyperopt_parameters = {
    'fastlen': hp.quniform('fastlen', 1, 50, 1),
    'slowlen': hp.quniform('slowlen', 1, 50, 1),
    'siglen': hp.quniform('siglen', 1, 50, 1),
    # 'smafastlen': hp.quniform('smafastlen', 1, 50, 1),
    # 'smaslowlen': hp.quniform('smaslowlen', 1, 50, 1),
}

BacktestIteration(macd_cross_backtest, default_parameters, hyperopt_parameters, 1000)
