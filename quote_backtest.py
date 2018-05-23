# -*- coding: utf-8 -*-
import pandas as pd
import numpy as np
from datetime import datetime
from backtest import Backtest, BacktestReport, BacktestIteration
from hyperopt import hp
from indicator import *
from functools import lru_cache

# テストデータ読み込み
ohlcv = pd.read_csv('csv/xbtusd_trade-20s.csv', index_col='timestamp', parse_dates=True)

buysize =ohlcv['buy_volume']
sellsize =ohlcv['sell_volume']

@lru_cache(maxsize=32)
def cached_buysize(period):
    return sma(buysize, period)

@lru_cache(maxsize=32)
def cached_sellsize(period):
    return sma(sellsize, period)

def shooter_backtest(asklength, bidlength):

    # インジケーター作成
    bid = cached_buysize(bidlength)
    ask = cached_sellsize(asklength)

    # エントリー／イグジット
    long_entry = bid > ask
    short_entry = ask > bid
    long_exit = short_entry
    short_exit = long_entry

    long_entry_price = None
    long_exit_price = None
    short_entry_price = None
    short_exit_price = None

    ignore = int(max(asklength,bidlength))
    long_entry[:ignore] = False
    long_exit[:ignore] = False
    short_entry[:ignore] = False
    short_exit[:ignore] = False

    lots = 500 / ohlcv.close
    # long_entry_price[:ignore] = 0
    # long_exit_price[:ignore] = 0
    # short_entry_price[:ignore] = 0
    # short_exit_price[:ignore] = 0

    entry_exit = pd.DataFrame({'close':ohlcv.close, 'ask':ask, 'bid':bid,
        'long_entry_price':long_entry_price, 'long_exit_price':long_exit_price, 'long_entry':long_entry, 'long_exit':long_exit,
        'short_entry_price':short_entry_price, 'short_entry':short_entry, 'short_exit_price':short_exit_price, 'short_exit':short_exit})#, index=ohlcv.index)
    entry_exit.to_csv('entry_exit.csv')

    report = Backtest(ohlcv, buy_entry=long_entry, sell_entry=short_entry, buy_exit=long_exit, sell_exit=short_exit,
        stop_buy_entry=long_entry_price, stop_sell_entry=short_entry_price, stop_buy_exit=long_exit_price, stop_sell_exit=short_exit_price,
        lots=lots, spread=0, take_profit=0, stop_loss=0, trailing_stop=0, slippage=0, percent_of_equity=(1, 500))
    return report

default_parameters = {
    'asklength':55,
    'bidlength':87,
}

hyperopt_parameters = {
    'asklength': hp.quniform('asklength', 1, 100, 1),
    'bidlength': hp.quniform('bidlength', 1, 100, 1),
}

BacktestIteration(shooter_backtest, default_parameters, hyperopt_parameters, 1000)
