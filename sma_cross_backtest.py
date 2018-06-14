# -*- coding: utf-8 -*-
import pandas as pd
import numpy as np
from datetime import datetime
from backtest import Backtest, BacktestReport, BacktestIteration
from hyperopt import hp
from indicator import *

def sma_cross_backtest(ohlcv, fastlen, slowlen, filterlen, buyfilterth, sellfilterth, rsiperiod, overBought, overSold):

    # インジケーター作成
    vfast = sma(change(ohlcv.close), fastlen)
    vslow = sma(change(ohlcv.close), slowlen)

    # エントリー／イグジット
    buy_entry = crossover(vfast, vslow)
    sell_entry = crossunder(vfast, vslow)
    buy_exit = sell_entry
    sell_exit = buy_entry

    # フィルター
    # vfilter = sma(ohlcv.close, filterlen)
    # vfilter = vfilter.diff()
    # buy_entry = buy_entry & (vfilter > buyfilterth)
    # sell_entry = sell_entry & (vfilter < -sellfilterth)

    # 利確
    # buy_exit = buy_exit | (ohlcv.close > (slowlen * 1.01))
    # sell_exit = sell_exit | (ohlcv.close < (slowlen * 0.99))

    ignore = int(max(fastlen, slowlen))
    buy_entry[:ignore] = False
    buy_exit[:ignore] = False
    sell_entry[:ignore] = False
    sell_exit[:ignore] = False

    # entry_exit = pd.DataFrame({'close':ohlcv.close, 'fast':vfast, 'slow':vslow,
    #     'buy_entry':buy_entry, 'buy_exit':buy_exit, 'sell_entry':sell_entry, 'sell_exit':sell_exit})#, index=ohlcv.index)
    # entry_exit.to_csv('entry_exit.csv')

    return Backtest(**locals())

if __name__ == '__main__':

    # テストデータ読み込み
    ohlcv = pd.read_csv('csv/bitmex_2018_1h.csv', index_col='timestamp', parse_dates=True)

    default_parameters = {
        'ohlcv': ohlcv,
        'fastlen':24,
        'slowlen':27,
        'filterlen':1,
        'buyfilterth':82,
        'sellfilterth':82,
        'rsiperiod':14,
        'overBought':70.1,
        'overSold':29.9,
    }

    hyperopt_parameters = {
        'fastlen': hp.quniform('fastlen', 1, 100, 1),
        'slowlen': hp.quniform('slowlen', 1, 100, 1),
        # 'filterlen': hp.loguniform('filterlen', 0, 5),
        # 'buyfilterth': hp.loguniform('buyfilterth', 0, 3),
        # 'sellfilterth': hp.loguniform('sellfilterth', 0, 3),
        # 'rsiperiod': hp.quniform('rsiperiod', 1, 30, 1),
        # 'overBought': hp.quniform('overBought', 60, 90, 2),
        # 'overSold': hp.quniform('overSold', 1, 40, 2),
    }

    best, report = BacktestIteration(sma_cross_backtest, default_parameters, hyperopt_parameters, 0, maximize=lambda r:r.All.ProfitFactor)
    report.DataFrame.to_csv('TradeData.csv')
    report.Equity.to_csv('Equity.csv')
