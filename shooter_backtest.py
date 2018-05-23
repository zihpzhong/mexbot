# -*- coding: utf-8 -*-
import pandas as pd
import numpy as np
from datetime import datetime
from backtest import Backtest, BacktestReport, BacktestIteration
from hyperopt import hp
from indicator import *

# テストデータ読み込み
ohlcv = pd.read_csv('csv/bitmex_2018_1h.csv', index_col='timestamp', parse_dates=True)

def deviation(source, period):
    base = source.rolling(int(period)).mean()
    return (base, ((source - base) / base) * 100)

def shooter_backtest(smalength, overshoot, undershoot):

    # インジケーター作成
    vsma, vdev = deviation(ohlcv.close, smalength)

    # エントリー／イグジット
    long_entry = None
    short_entry = None
    long_exit = None
    short_exit = None

    long_entry_price = None
    long_exit_price = None
    short_entry_price = None
    short_exit_price = None

    # ignore = int(smalength)
    # long_entry[:ignore] = False
    # long_exit[:ignore] = False
    # short_entry[:ignore] = False
    # short_exit[:ignore] = False

    # long_entry_price[:ignore] = 0
    # long_exit_price[:ignore] = 0
    # short_entry_price[:ignore] = 0
    # short_exit_price[:ignore] = 0

    entry_exit = pd.DataFrame({'close':ohlcv.close, 'deviation':vdev, 'sma':vsma,
        'long_entry_price':long_entry_price, 'long_exit_price':long_exit_price, 'long_entry':long_entry, 'long_exit':long_exit,
        'short_entry_price':short_entry_price, 'short_entry':short_entry, 'short_exit_price':short_exit_price, 'short_exit':short_exit})#, index=ohlcv.index)
    entry_exit.to_csv('entry_exit.csv')

    report = Backtest(ohlcv, buy_entry=long_entry, sell_entry=short_entry, buy_exit=long_exit, sell_exit=short_exit,
        stop_buy_entry=long_entry_price, stop_sell_entry=short_entry_price, stop_buy_exit=long_exit_price, stop_sell_exit=short_exit_price,
        lots=1, spread=0, take_profit=0, stop_loss=0, trailing_stop=20, slippage=0)
    report.Total.shortProfit = report.Short.Profit
    report.Total.longProfit = report.Long.Profit
    return report

default_parameters = {
    'smalength':20,
    'overshoot':0.005,
    'undershoot':0.005,
}

hyperopt_parameters = {
    'smalength': hp.quniform('smalength', 1, 75, 1),
    'overshoot': hp.uniform('overshoot', 0.0001, 0.2),
    'undershoot': hp.uniform('undershoot', 0.0001, 0.2),
}

BacktestIteration(shooter_backtest, default_parameters, hyperopt_parameters, 0)
