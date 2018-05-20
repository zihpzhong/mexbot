# -*- coding: utf-8 -*-
import pandas as pd
import numpy as np
from backtest import Backtest, BacktestReport, BacktestIteration
from hyperopt import hp
from numba import jit
from indicator import *
from functools import lru_cache

# テストデータ読み込み
ohlcv = pd.read_csv('csv/bitmex_2018_1h.csv', index_col='timestamp', parse_dates=True)

@lru_cache(maxsize=None)
def cached_rci(period):
    return rci(ohlcv.close, period)

@jit
def rci_cross_backtest(fastlen, slowlen):

    # インジケーター作成
    vfastrci = cached_rci(fastlen)
    vslowrci = cached_rci(slowlen)

    # エントリー／イグジット
    long_entry = crossover(vfastrci, vslowrci)
    short_entry = crossunder(vfastrci, vslowrci)
    long_exit = short_entry
    short_exit = long_entry

    long_entry_price = None
    long_exit_price = None
    short_entry_price = None
    short_exit_price = None

    ignore = int(max([fastlen, slowlen]))
    long_entry[:ignore] = False
    long_exit[:ignore] = False
    short_entry[:ignore] = False
    short_exit[:ignore] = False

    entry_exit = pd.DataFrame({'close':ohlcv.close, 'fast':vfastrci, 'slow':vslowrci,
    	'long_entry':long_entry, 'long_exit':long_exit, 'short_entry':short_entry, 'short_exit':short_exit})
    entry_exit.to_csv('entry_exit.csv')

    return Backtest(ohlcv, buy_entry=long_entry, sell_entry=short_entry, buy_exit=long_exit, sell_exit=short_exit,
        stop_buy_entry=long_entry_price, stop_sell_entry=short_entry_price, stop_buy_exit=long_exit_price, stop_sell_exit=short_exit_price,
        lots=1, spread=0, take_profit=0, stop_loss=0, trailing_stop=0, slippage=0)

default_parameters = {
    'fastlen':25,
    'slowlen':35,
}

hyperopt_parameters = {
    'fastlen': hp.quniform('fastlen', 2, 100, 1),
    'slowlen': hp.quniform('slowlen', 2, 100, 1),
}

BacktestIteration(rci_cross_backtest, default_parameters, hyperopt_parameters, 0)
