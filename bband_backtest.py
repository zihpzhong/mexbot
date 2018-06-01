# -*- coding: utf-8 -*-
import pandas as pd
from backtest import Backtest, BacktestReport, BacktestIteration
from hyperopt import hp
from indicator import *


def bband_backtest(ohlcv, length, multi):
    ignore = int(length)

    # インジケーター作成
    source = ohlcv.close
    upper, lower, basis, sigma = bband(source, length, multi)

    buyEntry = crossover(source, lower)
    sellEntry = crossunder(source, upper)

    # エントリー／イグジット
    buy_entry = buyEntry
    buy_exit = sellEntry
    sell_entry = sellEntry
    sell_exit = buyEntry

    buy_entry[:ignore] = False
    buy_exit[:ignore] = False
    sell_entry[:ignore] = False
    sell_exit[:ignore] = False

    # buy_entry_price = upper
    # buy_entry_price[~buyEntry] = 0

    # sell_entry_price = lower
    # sell_entry_price[~sellEntry] = 0

    # buy_exit_price = sell_entry_price
    # sell_exit_price = buy_entry_price

    # buy_entry_price[:ignore] = 0
    # buy_exit_price[:ignore] = 0
    # sell_entry_price[:ignore] = 0
    # sell_exit_price[:ignore] = 0

    # entry_exit = pd.DataFrame({'close':ohlcv.close, 'upper':upper, 'lower':lower,
    # 	'buy_entry':buy_entry, 'buy_exit':buy_exit, 'sell_entry':sell_entry, 'sell_exit':sell_exit})
    # entry_exit.to_csv('entry_exit.csv')

    return Backtest(**locals())

if __name__ == '__main__':

    # テストデータ読み込み
    ohlcv = pd.read_csv('csv/bitmex_2018_1h.csv', index_col='timestamp', parse_dates=True)

    default_parameters = {
        'ohlcv': ohlcv,
        'length':20,
        'multi':2,
    }

    hyperopt_parameters = {
        'length': hp.quniform('length', 1, 60, 1),
        'multi': hp.quniform('multi', 0.0, 3.0, 0.1),
    }

    best, report = BacktestIteration(bband_backtest, default_parameters, hyperopt_parameters, 0)
