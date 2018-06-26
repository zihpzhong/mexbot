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
        return fastrci(ohlcv.close, period)

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

    # entry_exit = pd.DataFrame({'close':ohlcv.close, 'rci':vrci, 'inv-rci':vinvrci,
    # 	'buy_entry':buy_entry, 'buy_exit':buy_exit, 'sell_entry':sell_entry, 'sell_exit':sell_exit})
    # entry_exit.to_csv('entry_exit.csv')

    return Backtest(**locals())

if __name__ == '__main__':

    # テストデータ読み込み
    ohlcv = pd.read_csv('csv/bitmex_2018_1m.csv', index_col='timestamp', parse_dates=True)
    ohlcv = ohlcv['2018-3-22':'2018-3-29']

    default_parameters = {
        'ohlcv': ohlcv,
        'rcilength':68,
        'overBought':69,
        'overSold':-68,
        'invrcilen':90,
    }

    hyperopt_parameters = {
        'rcilength': hp.quniform('rcilength', 2, 90, 1),
        'overBought': hp.quniform('overBought', 0, 100, 1),
        'overSold': hp.quniform('overSold', -100, 0, 1),
        # 'invrcilen': hp.quniform('invrcilen', 2, 90, 1),
    }

    def maximize(r):
        return ((r.All.WinRatio*r.All.WinPct) + ((1-r.All.WinRatio)*r.All.LossPct)) * r.All.Trades

    best, report = BacktestIteration(rci_cross_backtest, default_parameters, hyperopt_parameters, 0, maximize=maximize)
    report.DataFrame.to_csv('TradeData.csv')
    report.Equity.to_csv('Equity.csv')
