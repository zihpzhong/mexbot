# -*- coding: utf-8 -*-
import pandas as pd
from backtest import Backtest, BacktestIteration
from hyperopt import hp
from indicator import *
from functools import lru_cache, wraps

def macd_cross_backtest(ohlcv, fastlen, slowlen, siglen, smafastlen, smaslowlen, use_sma):

    @lru_cache(maxsize=None)
    def cached_sma(period):
        return ohlcv.close.rolling(int(period)).mean()

    @lru_cache(maxsize=None)
    def cached_macd(fastlen, slowlen, siglen):
        macd = cached_sma(fastlen) - cached_sma(slowlen)
        signal = macd.rolling(int(siglen)).mean()
        return (macd, signal, macd-signal)

    # インジケーター作成
    vmacd, vsig, vhist = cached_macd(fastlen, slowlen, siglen)
    if use_sma:
        vfast = cached_sma(smafastlen)
        vslow = cached_sma(smaslowlen)

    # エントリー／イグジット
    if use_sma:
        buy_entry = crossover(vmacd, vsig) | crossover(vfast, vslow)
        sell_entry = crossunder(vmacd, vsig) | crossunder(vfast, vslow)
    else:
        buy_entry = crossover(vmacd, vsig)
        sell_entry = crossunder(vmacd, vsig)
    buy_exit = sell_entry
    sell_exit = buy_entry

    ignore = int(max([fastlen, slowlen, smafastlen, smaslowlen]))
    buy_entry[:ignore] = False
    buy_exit[:ignore] = False
    sell_entry[:ignore] = False
    sell_exit[:ignore] = False

    # entry_exit = pd.DataFrame({'close':ohlcv.close, 'macd':vmacd, 'sig':vsig, #'fast':vfast, 'slow':vslow,
    #     'buy_entry':buy_entry, 'buy_exit':buy_exit, 'sell_entry':sell_entry, 'sell_exit':sell_exit})#, index=ohlcv.index)
    # entry_exit.to_csv('entry_exit.csv')

    lots = 1
    max_size = 1

    return Backtest(**locals())

if __name__ == '__main__':

    import argparse
    import datetime
    import dateutil.parser

    def store_datetime(str):
        return dateutil.parser.parse(str)

    parser = argparse.ArgumentParser(description="")
    parser.add_argument("--start", type=store_datetime)
    parser.add_argument("--end", type=store_datetime)
    args = parser.parse_args()

    ohlcv = pd.read_csv('csv/bitmex_2018_1h.csv', index_col='timestamp', parse_dates=True)
    if args.start is not None and args.end is not None:
        ohlcv = ohlcv[args.start:args.end]
    elif args.start is None:
        ohlcv = ohlcv[:args.end]
    elif args.end is None:
        ohlcv = ohlcv[args.start:]

    default_parameters = {
        'ohlcv': ohlcv,
        'fastlen':19,
        'slowlen':27,
        'siglen':13,
        'smafastlen':19,
        'smaslowlen':27,
        'use_sma':False,
    }

    hyperopt_parameters = {
        'fastlen': hp.quniform('fastlen', 5, 50, 1),
        'slowlen': hp.quniform('slowlen', 5, 50, 1),
        'siglen': hp.quniform('siglen', 1, 50, 1),
        # 'smafastlen': hp.quniform('smafastlen', 1, 50, 1),
        # 'smaslowlen': hp.quniform('smaslowlen', 1, 50, 1),
    }

    best, report = BacktestIteration(macd_cross_backtest, default_parameters, hyperopt_parameters, 0)
