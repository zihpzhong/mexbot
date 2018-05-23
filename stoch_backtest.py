# -*- coding: utf-8 -*-
import pandas as pd
import numpy as np
from backtest import Backtest, BacktestReport, BacktestIteration
from hyperopt import hp
from indicator import *

# テストデータ読み込み
ohlcv = pd.read_csv('csv/bitmex_2018_5m.csv', index_col='timestamp', parse_dates=True)

def stoch_backtest(length, overBought, overSold, exit_length):

    # インジケーター作成
    vstoch = stoch(ohlcv.close, ohlcv.high, ohlcv.low, length)
    long_stop = lowest(ohlcv.close, exit_length)
    short_stop = highest(ohlcv.close, exit_length)

    # エントリー／イグジット
    long_entry = crossover(vstoch, overSold)
    long_exit = crossunder(vstoch, overBought)
    short_entry = crossunder(vstoch, overBought)
    short_exit = crossover(vstoch, overSold)

    long_entry_price = None
    long_exit_price = long_stop
    short_entry_price = None
    short_exit_price = short_stop

    ignore = int(max(length,exit_length))
    long_entry[:ignore] = False
    long_exit[:ignore] = False
    short_entry[:ignore] = False
    short_exit[:ignore] = False

    # long_entry_price[:ignore] = 0
    # long_exit_price[:ignore] = 0
    # short_entry_price[:ignore] = 0
    # short_exit_price[:ignore] = 0

    entry_exit = pd.DataFrame({'close':ohlcv.close, 'stoch':vstoch,
        'long_entry_price':long_entry_price, 'long_exit_price':long_exit_price, 'long_entry':long_entry, 'long_exit':long_exit,
        'short_entry_price':short_entry_price, 'short_entry':short_entry, 'short_exit_price':short_exit_price, 'short_exit':short_exit})#, index=ohlcv.index)
    entry_exit.to_csv('entry_exit.csv')

    return Backtest(ohlcv, buy_entry=long_entry, sell_entry=short_entry, buy_exit=long_exit, sell_exit=short_exit,
        stop_buy_entry=long_entry_price, stop_sell_entry=short_entry_price, stop_buy_exit=long_exit_price, stop_sell_exit=short_exit_price,
        lots=1, spread=0, take_profit=0, stop_loss=0, slippage=0)

default_parameters = {
    'length':19,
    'overBought':99,
    'overSold':15,
    'exit_length':19,
}

hyperopt_parameters = {
    'length': hp.quniform('length', 1, 200, 1),
    'overBought': hp.quniform('overBought', 0, 100, 1),
    'overSold': hp.quniform('overSold', 0, 100, 1),
    'exit_length': hp.quniform('exit_length', 2, 200, 1),
}

BacktestIteration(stoch_backtest, default_parameters, hyperopt_parameters, 3000)
