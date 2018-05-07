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
def stoch_backtest(ohlc, length, overBought, overSold):

    # インジケーター作成
    vstoch = stoch(ohlc.close, ohlc.high, ohlc.low, length)
    vstoch_last = vstoch.shift(1)

    # エントリー／イグジット
    long_entry = (vstoch > overSold) & (vstoch_last < overSold)
    long_exit = (vstoch > overBought) & (vstoch_last < overBought)
    short_entry = (vstoch < overBought) & (vstoch_last > overBought)
    short_exit = (vstoch < overSold) & (vstoch_last > overSold)

    long_entry_price = None
    long_exit_price = None
    short_entry_price = None
    short_exit_price = None

    long_entry[:length] = False
    long_exit[:length] = False
    short_entry[:length] = False
    short_exit[:length] = False

    # long_entry_price[:length] = 0
    # long_exit_price[:length] = 0
    # short_entry_price[:length] = 0
    # short_exit_price[:length] = 0

    entry_exit = pd.DataFrame({'close':ohlc.close, 'stoch':vstoch, 'stoch-last':vstoch_last,
        'long_entry_price':long_entry_price, 'long_exit_price':long_exit_price, 'long_entry':long_entry, 'long_exit':long_exit,
        'short_entry_price':short_entry_price, 'short_entry':short_entry, 'short_exit_price':short_exit_price, 'short_exit':short_exit})#, index=data.index)
    entry_exit.to_csv('entry_exit.csv')

    return Backtest(data, buy_entry=long_entry, sell_entry=short_entry, buy_exit=long_exit, sell_exit=short_exit,
        stop_buy_entry=long_entry_price, stop_sell_entry=short_entry_price, stop_buy_exit=long_exit_price, stop_sell_exit=short_exit_price,
        lots=1, spread=0, take_profit=0, stop_loss=0, slippage=0)

default_parameters = {
    'ohlcv':data,
    'length':19,
    'overBought':99,
    'overSold':15,
}

hyperopt_parameters = {
    'length': hp.quniform('length', 1, 30, 1),
    'overBought': hp.quniform('overBought', 1, 99, 3),
    'overSold': hp.quniform('overSold', 1, 99, 3),
}

BacktestIteration(stoch_backtest, default_parameters, hyperopt_parameters, 50)
