# -*- coding: utf-8 -*-
import pandas as pd
from backtest import Backtest, BacktestReport, BacktestIteration
from hyperopt import hp
from indicator import *


def bband_backtest(ohlcv, length, multi):

    # インジケーター作成
    upper, lower, basis, sigma = bband(ohlcv.close, length, multi)

    # エントリー／イグジット
    limit_buy_entry = lower
    limit_buy_exit = basis
    limit_sell_entry = upper
    limit_sell_exit = basis

    ignore = int(length)
    limit_buy_entry[:ignore] = 0
    limit_buy_exit[:ignore] = 0
    limit_sell_entry[:ignore] = 0
    limit_sell_exit[:ignore] = 0

    # 売り買い優劣でエントリー抑制
    buy_volume = rsi(ohlcv.buy_volume, length)
    sell_volume = rsi(ohlcv.sell_volume, length)
    limit_buy_entry[buy_volume < sell_volume] = -1
    limit_sell_entry[buy_volume > sell_volume] = -1

    return Backtest(**locals())

if __name__ == '__main__':

    # テストデータ読み込み
    ohlcv = pd.read_csv('csv/bffx_20180618_3s.csv', index_col='timestamp', parse_dates=True)

    default_parameters = {
        'ohlcv': ohlcv,
        'length':6,
        'multi':1.6,
    }

    hyperopt_parameters = {
        'length': hp.quniform('length', 1, 60, 1),
        'multi': hp.quniform('multi', 0.0, 3.0, 0.1),
    }

    best, report = BacktestIteration(bband_backtest, default_parameters, hyperopt_parameters, 0)
