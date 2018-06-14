# -*- coding: utf-8 -*-
import pandas as pd
from datetime import datetime
from backtest import Backtest, BacktestReport, BacktestIteration
from hyperopt import hp
from indicator import *
from functools import lru_cache

def shooter_backtest(ohlcv, smalength, overshoot, undershoot):

    @lru_cache(maxsize=None)
    def deviation(period):
        base = ohlcv.close.rolling(int(period)).mean()
        return (base, ((ohlcv.close - base) / base) * 100)

    # インジケーター作成
    vsma, vdev = deviation(smalength)

    # エントリー／イグジット
    buy_entry = vdev < -undershoot
    sell_entry = vdev > overshoot
    buy_exit = vdev <= 0
    sell_exit = vdev >= 0

    ignore = int(smalength)
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
    ohlcv = pd.read_csv('csv/bitmex_2018_1h.csv', index_col='timestamp', parse_dates=True)

    default_parameters = {
        'ohlcv':ohlcv,
        'smalength':20,
        'overshoot':0.005,
        'undershoot':0.005,
    }

    hyperopt_parameters = {
        'smalength': hp.quniform('smalength', 1, 100, 1),
        'overshoot': hp.uniform('overshoot', 0.1, 20.0),
        'undershoot': hp.uniform('undershoot', 0.1, 20.0),
    }

    best, report = BacktestIteration(shooter_backtest, default_parameters, hyperopt_parameters, 300, maximize=lambda r:r.All.ProfitFactor)
    report.DataFrame.to_csv('TradeData.csv')
    report.Equity.to_csv('Equity.csv')
