# -*- coding: utf-8 -*-
import pandas as pd
import numpy as np
from backtest import Backtest, BacktestReport, BacktestIteration
from hyperopt import hp
from numba import jit
from indicator import *

# テストデータ読み込み
data = pd.read_csv('csv/bitmex_201801_1h.csv', index_col='timestamp', parse_dates=True)
#data = data[data.index.month == 4]

@jit
def sma_cross_backtest(ohlcv, fastlen, slowlen, siglen):

    # インジケーター作成
    vmacd, vsig, vhist = macd(ohlcv.close, fastlen, slowlen, siglen, use_sma=True)

    # エントリー／イグジット
    long_entry = crossover(vmacd, vsig)
    short_entry = crossunder(vmacd, vsig)
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


    entry_exit = pd.DataFrame({'close':ohlcv.close, 'macd':vmacd, 'sig':vsig,
        'long_entry_price':long_entry_price, 'long_exit_price':long_exit_price, 'long_entry':long_entry, 'long_exit':long_exit,
        'short_entry_price':short_entry_price, 'short_entry':short_entry, 'short_exit_price':short_exit_price, 'short_exit':short_exit})#, index=ohlcv.index)
    entry_exit.to_csv('entry_exit.csv')

    report = Backtest(ohlcv, buy_entry=long_entry, sell_entry=short_entry, buy_exit=long_exit, sell_exit=short_exit,
        stop_buy_entry=long_entry_price, stop_sell_entry=short_entry_price, stop_buy_exit=long_exit_price, stop_sell_exit=short_exit_price,
        lots=1, spread=0, take_profit=0, stop_loss=0, trailing_stop=0, slippage=0)
    report.Total.shortProfit = report.Short.Profit
    report.Total.longProfit = report.Long.Profit
    return report

default_parameters = {
    'ohlcv':data,
    'fastlen':9,
    'slowlen':26,
    'siglen':5,
}

hyperopt_parameters = {
    'fastlen': hp.quniform('fastlen', 1, 50, 1),
    'slowlen': hp.quniform('slowlen', 1, 50, 1),
    'siglen': hp.quniform('siglen', 1, 50, 1),
}

BacktestIteration(sma_cross_backtest, default_parameters, hyperopt_parameters, 3000)
