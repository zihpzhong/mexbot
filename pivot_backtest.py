# -*- coding: utf-8 -*-
import pandas as pd
import numpy as np
from backtest import Backtest, BacktestReport, BacktestIteration
from hyperopt import hp
from numba import jit
from indicator import *

# テストデータ読み込み
data = pd.read_csv('csv/bitmex_201804_5m.csv', index_col='timestamp', parse_dates=True)

@jit
def pivot_backtest(ohlc, leftbars, rightbars, trailing_stop=0):

    ignore = leftbars + rightbars

    # ピボットハイ＆ロー
    long_entry_price = pivothigh(ohlc.high, leftbars, rightbars).ffill()
    short_entry_price = pivotlow(ohlc.low, leftbars, rightbars).ffill()
    long_exit_price = short_entry_price
    short_exit_price = long_entry_price

    long_entry_price[:ignore] = 0
    long_exit_price[:ignore] = 0

    short_entry_price[:ignore] = 0
    short_exit_price[:ignore] = 0

    long_entry = ohlc.close > long_entry_price
    short_entry = ohlc.close < short_entry_price

    long_exit = short_entry
    short_exit = long_entry

    long_entry[:ignore] = 0
    long_exit[:ignore] = 0

    short_entry[:ignore] = 0
    short_exit[:ignore] = 0

    # STOP注文
    if 1:
        long_entry = None
        long_exit = None
        short_entry = None
        short_exit = None
    # 成り行き注文
    else:
        long_entry_price = None
        long_exit_price = None
        short_entry_price = None
        short_exit_price = None

    # バックテスト実施
    entry_exit = pd.DataFrame({'close':ohlc.close, 'high':ohlc.high, 'low':ohlc.low,
        'long_entry_price':long_entry_price, 'long_exit_price':long_exit_price, 'long_entry':long_entry, 'long_exit':long_exit,
        'short_entry_price':short_entry_price, 'short_entry':short_entry, 'short_exit_price':short_exit_price, 'short_exit':short_exit})#, index=data.index)
    entry_exit.to_csv('entry_exit.csv')

    return Backtest(data, buy_entry=long_entry, sell_entry=short_entry, buy_exit=long_exit, sell_exit=short_exit,
        stop_buy_entry=long_entry_price, stop_sell_entry=short_entry_price, stop_buy_exit=long_exit_price, stop_sell_exit=short_exit_price,
        lots=1, spread=6, trailing_stop=trailing_stop, slippage=0)

default_parameters = {
    'ohlcv':data,
    'leftbars':14,
    'rightbars':19,
    'trailing_stop':0,
}

hyperopt_parameters = {
    'leftbars': hp.quniform('leftbars', 1, 20, 1),
    'rightbars': hp.quniform('rightbars', 0, 20, 1),
    # 'trailing_stop': hp.quniform('trailing_stop', 0, 100, 1),
}

BacktestIteration(pivot_backtest, default_parameters, hyperopt_parameters, 50)
