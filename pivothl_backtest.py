# -*- coding: utf-8 -*-
import pandas as pd
from backtest import Backtest, BacktestReport, BacktestIteration
from hyperopt import hp
from indicator import *


def pivot_backtest(ohlcv, leftbars, rightbars):

    ignore = int(leftbars + rightbars)

    # ピボットハイ＆ロー
    stop_buy_entry = pivothigh(ohlcv.high, leftbars, rightbars).ffill()
    stop_sell_entry = pivotlow(ohlcv.low, leftbars, rightbars).ffill()
    stop_buy_exit = stop_sell_entry
    stop_sell_exit = stop_buy_entry

    stop_buy_entry[:ignore] = 0
    stop_buy_exit[:ignore] = 0

    stop_sell_entry[:ignore] = 0
    stop_sell_exit[:ignore] = 0

    # バックテスト実施
    # entry_exit = pd.DataFrame({'close':ohlcv.close, 'high':ohlcv.high, 'low':ohlcv.low,
    #     'stop_sell_entry':stop_sell_entry, 'short_entry':short_entry, 'stop_sell_exit':stop_sell_exit, 'short_exit':short_exit})
    # entry_exit.to_csv('entry_exit.csv')

    return Backtest(**locals())

if __name__ == '__main__':

    # テストデータ読み込み
    ohlcv = pd.read_csv('csv/bitmex_2018_1h.csv', index_col='timestamp', parse_dates=True)

    default_parameters = {
        'ohlcv': ohlcv,
        'leftbars':14,
        'rightbars':19,
    }

    hyperopt_parameters = {
        'leftbars': hp.quniform('leftbars', 1, 300, 1),
        'rightbars': hp.quniform('rightbars', 1, 300, 1),
    }

    best, report = BacktestIteration(pivot_backtest, default_parameters, hyperopt_parameters, 300)
