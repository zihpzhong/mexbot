# -*- coding: utf-8 -*-
import pandas as pd
from backtest import Backtest, BacktestIteration
from hyperopt import hp
from indicator import *
from functools import lru_cache

def macd_cross_backtest(ohlcv, fastlen, slowlen, siglen, smafastlen, smaslowlen, filter, shrink):

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

    # エントリー／イグジット
    buy_entry = crossover(vmacd, vsig)
    sell_entry = crossunder(vmacd, vsig)
    buy_exit = sell_entry.copy()
    sell_exit = buy_entry.copy()

    ignore = int(max([fastlen, slowlen, smafastlen, smaslowlen]))
    buy_entry[:ignore] = False
    buy_exit[:ignore] = False
    sell_entry[:ignore] = False
    sell_exit[:ignore] = False

    if filter:
        fastsma = sma(ohlcv.close, smafastlen)
        slowsma = sma(ohlcv.close, smaslowlen)
        buy_entry[fastsma < slowsma] = False
        sell_entry[fastsma > slowsma] = False

    # ゼロラインフィルタ
    # buy_entry[vsig>0] = False
    # sell_entry[vsig<0] = False

    # 2つの移動平均線の剥離によるロット制限
    if shrink:
        fastsma = sma(ohlcv.close, smafastlen)
        slowsma = sma(ohlcv.close, smaslowlen)
        upper = 1.00
        lower = 0.01
        sell_size = lower + (slowsma > fastsma) * (upper - lower)
        buy_size = lower + (fastsma > slowsma) * (upper - lower)
        # sell_size = 1 - ((1 - (slowsma / fastsma)) * klot)
        # sell_size.clip(0.01, 1.0, inplace=True)
        # buy_size  = 1 - ((1 - (fastsma / slowsma)) * klot)
        # buy_size.clip(0.01, 1.0, inplace=True)

    # entry_exit = pd.DataFrame({'close':ohlcv.close, 'macd':vmacd, 'sig':vsig, 'fsma':fastsma, 'ssma':slowsma, 'buy_size':buy_size, 'sell_size':sell_size,
    #     'buy_entry':buy_entry, 'buy_exit':buy_exit, 'sell_entry':sell_entry, 'sell_exit':sell_exit})#, index=ohlcv.index)
    # entry_exit.to_csv('entry_exit.csv')

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
        'smafastlen':10,
        'smaslowlen':95,
        'filter':False,
        'shrink':True,
    }

    hyperopt_parameters = {
        'fastlen': hp.quniform('fastlen', 5, 50, 1),
        'slowlen': hp.quniform('slowlen', 5, 50, 1),
        'siglen': hp.quniform('siglen', 1, 50, 1),
        # 'smafastlen': hp.quniform('smafastlen', 1, 100, 1),
        # 'smaslowlen': hp.quniform('smaslowlen', 1, 100, 1),
    }

    best, report = BacktestIteration(macd_cross_backtest, default_parameters, hyperopt_parameters, 0, maximize=lambda r:r.All.ProfitFactor)
    report.DataFrame.to_csv('TradeData.csv')
    report.Equity.to_csv('Equity.csv')
