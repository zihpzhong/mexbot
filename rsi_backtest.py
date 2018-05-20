# -*- coding: utf-8 -*-
import pandas as pd
import numpy as np
from backtest import Backtest, BacktestReport, BacktestIteration
from hyperopt import hp
from numba import jit
from indicator import *
from functools import lru_cache

# テストデータ読み込み
ohlcv = pd.read_csv('csv/bitmex_201805_1m.csv', index_col='timestamp', parse_dates=True)

@lru_cache(maxsize=None)
def cached_rsi(period):
    return rsi(ohlcv.close, period)

@jit
def rsi_backtest(rsilength, overBought, overSold, take_profit, stop_loss, trailing_stop):

    # インジケーター作成
    vrsi = cached_rsi(rsilength)

    # エントリー／イグジット
    long_entry = crossover(vrsi, overSold)
    short_entry = crossunder(vrsi, overBought)
    long_exit = short_entry
    short_exit = long_entry

    long_entry_price = None
    long_exit_price = None
    short_entry_price = None
    short_exit_price = None

    ignore = int(rsilength)
    long_entry[:ignore] = False
    long_exit[:ignore] = False
    short_entry[:ignore] = False
    short_exit[:ignore] = False

    entry_exit = pd.DataFrame({'close':ohlcv.close, 'rsi':vrsi, 'long_entry':long_entry, 'long_exit':long_exit, 'short_entry':short_entry, 'short_exit':short_exit})
    entry_exit.to_csv('entry_exit.csv')

    return Backtest(ohlcv, buy_entry=long_entry, sell_entry=short_entry, buy_exit=long_exit, sell_exit=short_exit,
        stop_buy_entry=long_entry_price, stop_sell_entry=short_entry_price, stop_buy_exit=long_exit_price, stop_sell_exit=short_exit_price,
        lots=1, spread=0, take_profit=take_profit, stop_loss=stop_loss, trailing_stop=trailing_stop, slippage=0)

default_parameters = {
    'rsilength':14,
    'overBought':78,
    'overSold':30,
    'take_profit':0,
    'stop_loss':0,
    'trailing_stop':0,
}

hyperopt_parameters = {
    'rsilength': hp.quniform('rsilength', 1, 30, 1),
    'overBought': hp.quniform('overBought', 0, 100, 2),
    'overSold': hp.quniform('overSold', 0, 100, 2),
    'take_profit': hp.quniform('take_profit', 10, 100, 5),
    'stop_loss': hp.quniform('stop_loss', 10, 100, 5),
    # 'trailing_stop': hp.quniform('trailing_stop', 10, 200, 5),
}

BacktestIteration(rsi_backtest, default_parameters, hyperopt_parameters, 1000)
