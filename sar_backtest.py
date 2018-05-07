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
def sar_backtest(ohlcv, start, inc, max):

    # インジケーター作成
    vsar = sar(ohlcv.high, ohlcv.low, start, inc, max)

    # エントリー／イグジット
    long_entry_price = None
    long_exit_price = None
    short_entry_price = None
    short_exit_price = None

    long_entry = None
    long_exit = None
    short_entry = None
    short_exit = None

    entry_exit = pd.DataFrame({'close':ohlcv.close, 'sar':vsar,
        'long_entry_price':long_entry_price, 'long_exit_price':long_exit_price, 'long_entry':long_entry, 'long_exit':long_exit,
        'short_entry_price':short_entry_price, 'short_entry':short_entry, 'short_exit_price':short_exit_price, 'short_exit':short_exit})#, index=data.index)
    entry_exit.to_csv('entry_exit.csv')

    return Backtest(data, buy_entry=long_entry, sell_entry=short_entry, buy_exit=long_exit, sell_exit=short_exit,
        stop_buy_entry=long_entry_price, stop_sell_entry=short_entry_price, stop_buy_exit=long_exit_price, stop_sell_exit=short_exit_price,
        lots=1, spread=0, take_profit=0, stop_loss=0, trailing_stop=0, slippage=0)

default_parameters = {
    'ohlcv':data,
    'start':0.02,
    'inc':0.02,
    'max':0.2,
}

hyperopt_parameters = {
    'start': hp.uniform('start', 0.005, 0.1),
    'inc': hp.uniform('inc', 0.005, 0.1),
    'max': hp.uniform('max', 0.05, 0.8),
}

BacktestIteration(sar_backtest, default_parameters, hyperopt_parameters, 50)
