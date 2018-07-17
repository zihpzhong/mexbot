# -*- coding: utf-8 -*-
import pandas as pd
from backtest import Backtest, BacktestReport, BacktestIteration
from hyperopt import hp
from indicator import *


def bband_backtest(ohlcv, length, multi, sigmath):

    # インジケーター作成
    upper, lower, basis, sigma = bband(ohlcv.close, length, multi)

    # エントリー／イグジット
    buy_entry = (change(upper)<0) & (sigma > sigmath) & (ohlcv.close < basis)
    sell_entry = (change(lower)>0) & (sigma > sigmath) & (ohlcv.close > basis)
    buy_exit = sell_entry
    sell_exit = buy_entry

    ignore = int(length)
    buy_entry[:ignore] = False
    buy_exit[:ignore] = False
    sell_entry[:ignore] = False
    sell_exit[:ignore] = False

    return Backtest(**locals())

if __name__ == '__main__':

    # テストデータ読み込み
    ohlcv = pd.read_csv('csv/bitmex_2018_5m.csv', index_col='timestamp', parse_dates=True)
    ohlcv = ohlcv['2018-6-1':]

    default_parameters = {
        'ohlcv': ohlcv,
        'length':20,
        'multi':3,
        'sigmath':40,
    }

    hyperopt_parameters = {
        'length': hp.quniform('length', 1, 100, 1),
        'multi': hp.uniform('multi', 0.1, 5.0),
        'sigmath': hp.quniform('sigmath', 1, 200, 1),
    }

    best, report = BacktestIteration(bband_backtest, default_parameters, hyperopt_parameters, 0)
