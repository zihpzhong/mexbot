# -*- coding: utf-8 -*-
import pandas as pd
import numpy as np
from backtest import Backtest, BacktestReport, BacktestIteration
from hyperopt import hp
from numba import jit
from indicator import *

# テストデータ読み込み
data = pd.read_csv('csv/bitmex_201804_1h.csv', index_col='timestamp', parse_dates=True)

@jit
def sma_cross_backtest(ohlcv, fastlen, slowlen, trailing_stop):

    # インジケーター作成
    vfast = ema(ohlcv.close, fastlen)
    vslow = ema(ohlcv.close, slowlen)

    # エントリー／イグジット
    long_entry = crossover(vfast, vslow)
    short_entry = crossunder(vfast, vslow)
    long_exit = short_entry
    short_exit = long_entry

    long_entry_price = None
    long_exit_price = None
    short_entry_price = None
    short_exit_price = None

    ignore = int(max(fastlen, slowlen))
    long_entry[:ignore] = False
    long_exit[:ignore] = False
    short_entry[:ignore] = False
    short_exit[:ignore] = False

    # long_entry_price[:ignore] = 0
    # long_exit_price[:ignore] = 0
    # short_entry_price[:ignore] = 0
    # short_exit_price[:ignore] = 0

    entry_exit = pd.DataFrame({'close':ohlcv.close, 'fast':vfast, 'slow':vslow,
        'long_entry_price':long_entry_price, 'long_exit_price':long_exit_price, 'long_entry':long_entry, 'long_exit':long_exit,
        'short_entry_price':short_entry_price, 'short_entry':short_entry, 'short_exit_price':short_exit_price, 'short_exit':short_exit})#, index=ohlcv.index)
    entry_exit.to_csv('entry_exit.csv')

    return Backtest(ohlcv, buy_entry=long_entry, sell_entry=short_entry, buy_exit=long_exit, sell_exit=short_exit,
        stop_buy_entry=long_entry_price, stop_sell_entry=short_entry_price, stop_buy_exit=long_exit_price, stop_sell_exit=short_exit_price,
        lots=1, spread=0, take_profit=0, stop_loss=0, trailing_stop=trailing_stop, slippage=0)

default_parameters = {
    'ohlcv':data,
    'fastlen':18,
    'slowlen':32,
    'trailing_stop':0,
}

hyperopt_parameters = {
    'fastlen': hp.quniform('fastlen', 1, 50, 1),
    'slowlen': hp.quniform('slowlen', 1, 50, 1),
    # 'trailing_stop': hp.quniform('trailing_stop', 0, 20, 1),
}

BacktestIteration(sma_cross_backtest, default_parameters, hyperopt_parameters, 1000)
