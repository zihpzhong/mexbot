# -*- coding: utf-8 -*-
import pandas as pd
from backtest import Backtest, BacktestReport, BacktestIteration
from hyperopt import hp
from indicator import *
from functools import lru_cache

def rci_cross_backtest(ohlcv, rcilength, overBought, overSold,):

    @lru_cache(maxsize=None)
    def cached_rci(period):
        return fastrci(ohlcv.close, period)

    # インジケーター作成
    vrci = cached_rci(rcilength)

    # エントリー／イグジット
    buy_entry = crossover(vrci, overBought)
    sell_entry = crossunder(vrci, overSold)
    buy_exit = sell_entry
    sell_exit = buy_entry

    ignore = int(max([rcilength]))
    buy_entry[:ignore] = False
    buy_exit[:ignore] = False
    sell_entry[:ignore] = False
    sell_exit[:ignore] = False

    entry_exit = pd.DataFrame({'close':ohlcv.close, 'rci':vrci,
    	'buy_entry':buy_entry, 'buy_exit':buy_exit, 'sell_entry':sell_entry, 'sell_exit':sell_exit})
    entry_exit.to_csv('entry_exit.csv')

    return Backtest(**locals())

if __name__ == '__main__':

    # テストデータ読み込み
    ohlcv = pd.read_csv('csv/bitmex_2018_1h.csv', index_col='timestamp', parse_dates=True)

    default_parameters = {
        'ohlcv': ohlcv,
        'rcilength':25,
        'overBought':70,
        'overSold':-70,
    }

    hyperopt_parameters = {
        'rcilength': hp.quniform('rcilength', 2, 100, 1),
        'overBought': hp.quniform('overBought', -100, 100, 1),
        'overSold': hp.quniform('overSold', -100, 100, 1),
    }

    best, report = BacktestIteration(rci_cross_backtest, default_parameters, hyperopt_parameters, 0)
