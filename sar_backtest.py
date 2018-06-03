# -*- coding: utf-8 -*-
import pandas as pd
from backtest import Backtest, BacktestReport, BacktestIteration
from hyperopt import hp
from indicator import *

def sar_backtest(ohlcv, start, inc, max):
    # インジケーター作成
    vsar = fastsar(ohlcv.high, ohlcv.low, start, inc, max)

    # エントリー／イグジット
    buy_entry = crossover(vsar, ohlcv.close)
    buy_exit = crossunder(vsar, ohlcv.close)
    sell_entry = buy_exit
    sell_exit = buy_entry
    # stop_buy_entry = vsar.copy()
    # stop_buy_exit = vsar.copy()
    # stop_sell_entry = vsar.copy()
    # stop_sell_exit = vsar.copy()

    # stop_buy_entry[ohlcv.high < vsar] = 0
    # stop_sell_entry[ohlcv.low > vsar] = 0

    # entry_exit = pd.DataFrame({'close':ohlcv.close, 'high':ohlcv.high, 'low':ohlcv.low, 'sar':vsar,
    #     'stop_buy_entry':stop_buy_entry, 'stop_buy_exit':stop_buy_exit,
    #     'stop_sell_entry':stop_sell_entry, 'stop_sell_exit':stop_sell_exit, })
    # entry_exit.to_csv('entry_exit.csv')

    return Backtest(**locals())

if __name__ == '__main__':

    # テストデータ読み込み
    ohlcv = pd.read_csv('csv/bitmex_2018_5m.csv', index_col='timestamp', parse_dates=True)

    default_parameters = {
        'ohlcv': ohlcv,
        'start':0.012,
        'inc':0.036,
        'max':0.38,
    }

    hyperopt_parameters = {
        'start': hp.quniform('start', 0.0, 0.1, 0.001),
        'inc': hp.quniform('inc', 0.0, 0.1, 0.001),
        'max': hp.quniform('max', 0.2, 0.5, 0.01),
    }

    best, report = BacktestIteration(sar_backtest, default_parameters, hyperopt_parameters, 300)
    report.DataFrame.to_csv('TradeData.csv')
    report.Equity.to_csv('Equity.csv')
