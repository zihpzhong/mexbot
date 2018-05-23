# -*- coding: utf-8 -*-
import pandas as pd
import numpy as np
from backtest import Backtest, BacktestReport, BacktestIteration
from hyperopt import hp
from indicator import *

# テストデータ読み込み
ohlcv = pd.read_csv('csv/bitmex_201804_5m.csv', index_col='timestamp', parse_dates=True)

def bband_backtest(length, multi):
    ignore = int(length)

    # インジケーター作成
    source = ohlcv.close
    upper, lower, basis, sigma = bband(source, length, multi)

    buyEntry = crossover(source, lower)
    sellEntry = crossunder(source, upper)

    # エントリー／イグジット
    long_entry = buyEntry
    long_exit = sellEntry
    short_entry = sellEntry
    short_exit = buyEntry

    long_entry[:ignore] = False
    long_exit[:ignore] = False
    short_entry[:ignore] = False
    short_exit[:ignore] = False

    # long_entry_price = upper
    # long_entry_price[~buyEntry] = 0

    # short_entry_price = lower
    # short_entry_price[~sellEntry] = 0

    # long_exit_price = short_entry_price
    # short_exit_price = long_entry_price

    # long_entry_price[:ignore] = 0
    # long_exit_price[:ignore] = 0
    # short_entry_price[:ignore] = 0
    # short_exit_price[:ignore] = 0

    entry_exit = pd.DataFrame({'close':ohlcv.close, 'upper':upper, 'lower':lower,
    	'long_entry':long_entry, 'long_exit':long_exit, 'short_entry':short_entry, 'short_exit':short_exit,
    	#'long_entry_price':long_entry_price, 'long_exit_price':long_exit_price, 'short_entry_price':short_entry_price, 'short_exit_price':short_exit_price,
    	})
    entry_exit.to_csv('entry_exit.csv')

    return Backtest(ohlcv,
    	buy_entry=long_entry, sell_entry=short_entry, buy_exit=long_exit, sell_exit=short_exit,
        #stop_buy_entry=long_entry_price, stop_sell_entry=short_entry_price, stop_buy_exit=long_exit_price, stop_sell_exit=short_exit_price,
        lots=1, spread=0, take_profit=0, stop_loss=0, trailing_stop=0, slippage=0)

default_parameters = {
    'length':20,
    'multi':2,
}

hyperopt_parameters = {
    'length': hp.quniform('length', 1, 60, 1),
    'multi': hp.quniform('multi', 0.0, 3.0, 0.1),
}

BacktestIteration(bband_backtest, default_parameters, hyperopt_parameters, 1000)
