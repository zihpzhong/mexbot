# -*- coding: utf-8 -*-
import pandas as pd
import numpy as np
from backtest import Backtest, BacktestReport, BacktestIteration
from hyperopt import hp
from numba import jit
from indicator import *

# テストデータ読み込み
ohlcv = pd.read_csv('csv/bitmex_201801_1h.csv', index_col='timestamp', parse_dates=True)

@jit
def sar_backtest(start, inc, max):
    # インジケーター作成
    vsar = sar(ohlcv.high, ohlcv.low, start, inc, max)

    # エントリー／イグジット
    long_entry_price = vsar
    long_exit_price = vsar
    short_entry_price = vsar
    short_exit_price = vsar

    long_entry_price[ohlcv.high < vsar] = 0
    short_entry_price[ohlcv.low > vsar] = 0

    long_entry = None
    long_exit = None
    short_entry = None
    short_exit = None

    entry_exit = pd.DataFrame({'close':ohlcv.close, 'sar':vsar,
        'long_entry_price':long_entry_price, 'long_exit_price':long_exit_price, 'long_entry':long_entry, 'long_exit':long_exit,
        'short_entry_price':short_entry_price, 'short_entry':short_entry, 'short_exit_price':short_exit_price, 'short_exit':short_exit})#, index=ohlcv.index)
    entry_exit.to_csv('entry_exit.csv')

    return Backtest(ohlcv, buy_entry=long_entry, sell_entry=short_entry, buy_exit=long_exit, sell_exit=short_exit,
        stop_buy_entry=long_entry_price, stop_sell_entry=short_entry_price, stop_buy_exit=long_exit_price, stop_sell_exit=short_exit_price,
        lots=1, spread=0, take_profit=0, stop_loss=0, trailing_stop=0, slippage=0)

default_parameters = {
    'start':0.15,
    'inc':0.04,
    'max':0.34,
}

hyperopt_parameters = {
    'start': hp.quniform('start', 0.0, 0.1, 0.001),
    'inc': hp.quniform('inc', 0.0, 0.1, 0.001),
    'max': hp.quniform('max', 0.0, 0.3, 0.01),
}

BacktestIteration(sar_backtest, default_parameters, hyperopt_parameters, 1000)
