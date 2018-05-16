# -*- coding: utf-8 -*-
import pandas as pd
import numpy as np
from datetime import datetime
from backtest import Backtest, BacktestReport, BacktestIteration
from hyperopt import hp
from numba import jit
from indicator import *

# テストデータ読み込み
ohlcv = pd.read_csv('csv/bitmex_2018_1h.csv', index_col='timestamp', parse_dates=True)
ohlcv = ohlcv[datetime(2018, 5, 1):]

@jit
def sma_cross_backtest(fastlen, slowlen, filterlen, buyfilterth, sellfilterth, rsiperiod, overBought, overSold):

    # インジケーター作成
    vfast = sma(ohlcv.close, fastlen)
    vslow = sma(ohlcv.close, slowlen)

    # エントリー／イグジット
    long_entry = crossover(vfast, vslow)
    short_entry = crossunder(vfast, vslow)
    long_exit = short_entry
    short_exit = long_entry

    # フィルター
    # vfilter = sma(ohlcv.close, filterlen)
    # vfilter = vfilter.diff()
    # long_entry = long_entry & (vfilter > buyfilterth)
    # short_entry = short_entry & (vfilter < -sellfilterth)

    # 利確
    # long_exit = long_exit | (ohlcv.close > (slowlen * 1.01))
    # short_exit = short_exit | (ohlcv.close < (slowlen * 0.99))

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
        # 'rsi':vrsi,
        # 'filter':vfilter,
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
    'fastlen':20,
    'slowlen':25,
    'filterlen':1,
    'buyfilterth':82,
    'sellfilterth':82,
    'rsiperiod':14,
    'overBought':70.1,
    'overSold':29.9,
}

hyperopt_parameters = {
    'fastlen': hp.quniform('fastlen', 1, 50, 1),
    'slowlen': hp.quniform('slowlen', 1, 75, 1),
    # 'filterlen': hp.loguniform('filterlen', 0, 5),
    # 'buyfilterth': hp.loguniform('buyfilterth', 0, 3),
    # 'sellfilterth': hp.loguniform('sellfilterth', 0, 3),
    # 'rsiperiod': hp.quniform('rsiperiod', 1, 30, 1),
    # 'overBought': hp.quniform('overBought', 60, 90, 2),
    # 'overSold': hp.quniform('overSold', 1, 40, 2),
}

BacktestIteration(sma_cross_backtest, default_parameters, hyperopt_parameters, 0)
