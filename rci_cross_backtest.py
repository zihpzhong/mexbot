# -*- coding: utf-8 -*-
import pandas as pd
from backtest import Backtest, BacktestReport, BacktestIteration
from hyperopt import hp
from indicator import *
from functools import lru_cache
from datetime import datetime


def rci_cross_backtest(ohlcv, rcilength, overBought, overSold, invrcilen):

    @lru_cache(maxsize=None)
    def cached_rci(period):
        return sma(fastrci(ohlcv.close, period), 5)

    if 1:
        vrci = cached_rci(rcilength)
        vinvrci = cached_rci(invrcilen) * -1
        buy_entry = vrci < vinvrci
        sell_entry = vrci > vinvrci
        buy_exit = sell_entry
        sell_exit = buy_entry
    else:
        # インジケーター作成
        vrci = cached_rci(rcilength)

        # エントリー／イグジット
        buy_entry = crossover(vrci, overSold)
        buy_exit = crossover(vrci, overBought)
        sell_entry = crossunder(vrci, overBought)
        sell_exit = crossunder(vrci, overSold)

    ignore = int(max([rcilength]))
    buy_entry[:ignore] = False
    buy_exit[:ignore] = False
    sell_entry[:ignore] = False
    sell_exit[:ignore] = False

    buy_size = sell_size = 1000 / ohlcv.close
    max_buy_size = max_sell_size = 0.1

    entry_exit = pd.DataFrame({'close':ohlcv.close, 'rci':vrci, 'inv-rci':vinvrci,
    	'buy_entry':buy_entry, 'buy_exit':buy_exit, 'sell_entry':sell_entry, 'sell_exit':sell_exit})
    entry_exit.to_csv('entry_exit.csv')

    return Backtest(**locals())

if __name__ == '__main__':

    # テストデータ読み込み
    ohlcv = pd.read_csv('csv/bitmex_2018_1m.csv', index_col='timestamp', parse_dates=True)
    ohlcv = ohlcv['2018-3-1':'2018-3-8']

    default_parameters = {
        'ohlcv': ohlcv,
        'rcilength':6,
        'overBought':40,
        'overSold':-40,
        'invrcilen':90,
    }

    hyperopt_parameters = {
        'rcilength': hp.quniform('rcilength', 2, 90, 1),
        # 'overBought': hp.quniform('overBought', 0, 100, 1),
        # 'overSold': hp.quniform('overSold', -100, 0, 1),
        'invrcilen': hp.quniform('invrcilen', 2, 90, 1),
    }

    best, report = BacktestIteration(rci_cross_backtest, default_parameters, hyperopt_parameters, 0, maximize=lambda r:r.All.Profit)
    report.DataFrame.to_csv('TradeData.csv')
    report.Equity.to_csv('Equity.csv')
