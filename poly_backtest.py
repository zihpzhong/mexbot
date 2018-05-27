# -*- coding: utf-8 -*-
import pandas as pd
import numpy as np
from datetime import datetime
from backtest import Backtest, BacktestReport, BacktestIteration
from hyperopt import hp
from indicator import *
from functools import lru_cache

# テストデータ読み込み
ohlcv = pd.read_csv('csv/bitmex_2018_1h.csv', index_col='timestamp', parse_dates=True)
#ohlcv = ohlcv[datetime(2018, 5, 1):]

@lru_cache(maxsize=None)
def cached_polyfline(period):
    return polyfline(ohlcv.close, period)

def poly_cross_backtest(polylength, smalength):

    # インジケーター作成
    vpoly = cached_polyfline(polylength)
    vsig = sma(vpoly, smalength)

    # エントリー／イグジット
    long_entry = crossover(vpoly, vsig)
    short_entry = crossunder(vpoly, vsig)
    long_exit = short_entry
    short_exit = long_entry

    long_entry_price = None
    long_exit_price = None
    short_entry_price = None
    short_exit_price = None

    ignore = int(max(polylength, smalength))
    long_entry[:ignore] = False
    long_exit[:ignore] = False
    short_entry[:ignore] = False
    short_exit[:ignore] = False

    # long_entry_price[:ignore] = 0
    # long_exit_price[:ignore] = 0
    # short_entry_price[:ignore] = 0
    # short_exit_price[:ignore] = 0

    entry_exit = pd.DataFrame({'close':ohlcv.close, 'poly':vpoly, 'sig':vsig,
        'long_entry_price':long_entry_price, 'long_exit_price':long_exit_price, 'long_entry':long_entry, 'long_exit':long_exit,
        'short_entry_price':short_entry_price, 'short_entry':short_entry, 'short_exit_price':short_exit_price, 'short_exit':short_exit})#, index=ohlcv.index)
    entry_exit.to_csv('entry_exit.csv')

    report = Backtest(ohlcv, buy_entry=long_entry, sell_entry=short_entry, buy_exit=long_exit, sell_exit=short_exit,
        stop_buy_entry=long_entry_price, stop_sell_entry=short_entry_price, stop_buy_exit=long_exit_price, stop_sell_exit=short_exit_price,
        lots=1, spread=0, take_profit=0, stop_loss=0, trailing_stop=0, slippage=0)#, percent_of_equity=(1, 1000))
    return report

default_parameters = {
    'polylength':28,
    'smalength':15,
}

hyperopt_parameters = {
    'polylength': hp.quniform('polylength', 5, 50, 1),
    'smalength': hp.quniform('smalength', 1, 20, 1),
}

BacktestIteration(poly_cross_backtest, default_parameters, hyperopt_parameters, 300)
