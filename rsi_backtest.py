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
def rsi_backtest(ohlc, length, overBought, overSold, trailing_stop):

    # インジケーター作成
    vrsi = rsi(ohlc.close, length)

    # エントリー／イグジット
    long_entry = crossover(vrsi, overSold)
    long_exit = crossover(vrsi, overBought)
    short_entry = crossunder(vrsi, overBought)
    short_exit = crossunder(vrsi, overSold)

    long_entry_price = None
    long_exit_price = None
    short_entry_price = None
    short_exit_price = None

    long_entry[:length] = False
    long_exit[:length] = False
    short_entry[:length] = False
    short_exit[:length] = False

    entry_exit = pd.DataFrame({'close':ohlc.close, 'rsi':vrsi, 'long_entry':long_entry, 'long_exit':long_exit, 'short_entry':short_entry, 'short_exit':short_exit})
    entry_exit.to_csv('entry_exit.csv')

    return Backtest(data, buy_entry=long_entry, sell_entry=short_entry, buy_exit=long_exit, sell_exit=short_exit,
        stop_buy_entry=long_entry_price, stop_sell_entry=short_entry_price, stop_buy_exit=long_exit_price, stop_sell_exit=short_exit_price,
        lots=1, spread=0, take_profit=0, stop_loss=0, trailing_stop=trailing_stop, slippage=0)

default_parameters = {
    'ohlcv':data,
    'length':14,
    'overBought':78,
    'overSold':30,
    'trailing_stop':0,
}

hyperopt_parameters = {
    'length': hp.quniform('length', 1, 30, 1),
    'overBought': hp.quniform('overBought', 1, 99, 1),
    'overSold': hp.quniform('overSold', 1, 99, 1),
    # 'trailing_stop': hp.quniform('trailing_stop', 0, 99, 1),
}

BacktestIteration(rsi_backtest, default_parameters, hyperopt_parameters, 50)
