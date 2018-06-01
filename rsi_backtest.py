# -*- coding: utf-8 -*-
import pandas as pd
from backtest import Backtest, BacktestReport, BacktestIteration
from hyperopt import hp
from indicator import *
from functools import lru_cache


def rsi_backtest(ohlcv, rsilength, overBought, overSold, take_profit, stop_loss, trailing_stop):

    @lru_cache(maxsize=None)
    def cached_rsi(period):
        return rsi(ohlcv.close, period)

    # インジケーター作成
    vrsi = cached_rsi(rsilength)

    # エントリー／イグジット
    buy_entry = crossover(vrsi, overSold)
    sell_entry = crossunder(vrsi, overBought)
    buy_exit = sell_entry
    sell_exit = buy_entry

    buy_entry_price = None
    buy_exit_price = None
    sell_entry_price = None
    sell_exit_price = None

    ignore = int(rsilength)
    buy_entry[:ignore] = False
    buy_exit[:ignore] = False
    sell_entry[:ignore] = False
    sell_exit[:ignore] = False

    # entry_exit = pd.DataFrame({'close':ohlcv.close, 'rsi':vrsi, 'buy_entry':buy_entry, 'buy_exit':buy_exit, 'sell_entry':sell_entry, 'sell_exit':sell_exit})
    # entry_exit.to_csv('entry_exit.csv')

    return Backtest(**locals())

if __name__ == '__main__':

    # テストデータ読み込み
    ohlcv = pd.read_csv('csv/bitmex_2018_1h.csv', index_col='timestamp', parse_dates=True)

    default_parameters = {
        'ohlcv': ohlcv,
        'rsilength':14,
        'overBought':78,
        'overSold':30,
        'take_profit':0,
        'stop_loss':0,
        'trailing_stop':0,
    }

    hyperopt_parameters = {
        'rsilength': hp.quniform('rsilength', 1, 30, 1),
        'overBought': hp.quniform('overBought', 0, 100, 2),
        'overSold': hp.quniform('overSold', 0, 100, 2),
        'take_profit': hp.quniform('take_profit', 10, 100, 5),
        'stop_loss': hp.quniform('stop_loss', 10, 100, 5),
        # 'trailing_stop': hp.quniform('trailing_stop', 10, 200, 5),
    }

    best, report = BacktestIteration(rsi_backtest, default_parameters, hyperopt_parameters, 0)
