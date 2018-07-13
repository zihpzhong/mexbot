# -*- coding: utf-8 -*-
import pandas as pd
from datetime import datetime
from backtest import Backtest, BacktestReport, BacktestIteration
from hyperopt import hp
from indicator import *
from functools import lru_cache

def nanpin_backtest(ohlcv, period, overshoot, undershoot):

    # エントリー／イグジット
    buy_entry = change(ohlcv.close, period) < -(ohlcv.close * undershoot)
    sell_entry = change(ohlcv.close, period) > (ohlcv.close * overshoot)
    buy_exit = sell_entry
    sell_exit = buy_entry

    ignore = int(period)
    buy_entry[:ignore] = False
    buy_exit[:ignore] = False
    sell_entry[:ignore] = False
    sell_exit[:ignore] = False

    # entry_exit = pd.DataFrame({'close':ohlcv.close,
    #     'buy_entry':buy_entry, 'buy_exit':buy_exit, 'sell_entry':sell_entry, 'sell_exit':sell_exit})
    # entry_exit.to_csv('entry_exit.csv')

    return Backtest(**locals())


if __name__ == '__main__':

    # テストデータ読み込み
    ohlcv = pd.read_csv('csv/bffx_20180705_10s.csv', index_col='timestamp', parse_dates=True)

    default_parameters = {
        'ohlcv':ohlcv,
        'period':3,
        'overshoot':0.02,
        'undershoot':0.005,
    }

    hyperopt_parameters = {
        # 'period': hp.quniform('period', 1, 100, 1),
        'overshoot': hp.uniform('overshoot', 0.0001, 0.1),
        'undershoot': hp.uniform('undershoot', 0.0001, 0.1),
    }

    best, report = BacktestIteration(nanpin_backtest, default_parameters, hyperopt_parameters, 300, maximize=lambda r:r.All.Profit)
    report.DataFrame.to_csv('TradeData.csv')
    report.Equity.to_csv('Equity.csv')
