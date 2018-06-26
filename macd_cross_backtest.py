# -*- coding: utf-8 -*-
import sys
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

    @lru_cache(maxsize=None)
    def cached_fund():
        fund = pd.read_csv('csv/bitmex_funding.csv', index_col='timestamp', parse_dates=True)
        fund = pd.DataFrame(fund, index=ohlcv.index).interpolate()
        return fund

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

    # 資金調達率によるエントリー制限
    if 0:
        fund = cached_fund()
        buy_entry[fund.fundingRate > 0.000] = False
        sell_entry[fund.fundingRate < 0.000] = False
        buy_exit[fund.fundingRate < 0.000] = False
        sell_exit[fund.fundingRate > 0.000] = False

    # 2つの移動平均線によるエントリー制限
    if filter:
        fastsma = sma(ohlcv.close, smafastlen)
        slowsma = sma(ohlcv.close, smaslowlen)
        buy_entry[slowsma > fastsma] = False
        sell_entry[fastsma > slowsma] = False

    # ゼロラインフィルタ
    if 0:
        buy_entry[vsig>0] = False
        sell_entry[vsig<0] = False

    # 2つの移動平均線によるロット制限
    if shrink:
        fastsma = sma(ohlcv.close, smafastlen)
        slowsma = sma(ohlcv.close, smaslowlen)
        upper = 1.999
        lower = 0.001
        buy_size = upper - ((slowsma > fastsma) * (upper - lower))
        buy_size = buy_size.shift(1)    # フィルターの条件と合わせるためシフトする
        sell_size = upper - ((fastsma > slowsma) * (upper - lower))
        sell_size = sell_size.shift(1)  # 注文は次の足で行われる

    # buy_size = sell_size = 3000 / ohlcv.close
    # initial_capital = 500
    # percent_of_equity = 0.5

    # entry_exit = pd.DataFrame({'close':ohlcv.close, 'macd':vmacd, 'sig':vsig, #'fsma':fastsma, 'ssma':slowsma, 'buy_size':buy_size, 'sell_size':sell_size,
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
    parser.add_argument('csv', nargs='?', type=argparse.FileType('r'), default=sys.stdin)
    parser.add_argument("--start", type=store_datetime)
    parser.add_argument("--end", type=store_datetime)
    parser.add_argument("--max_evals", dest='max_evals', type=int, default=0)
    args = parser.parse_args()

    ohlcv = pd.read_csv(args.csv, index_col='timestamp', parse_dates=True)
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
        'shrink':False,
    }

    hyperopt_parameters = {
        'fastlen': hp.quniform('fastlen', 5, 50, 1),
        'slowlen': hp.quniform('slowlen', 5, 50, 1),
        'siglen': hp.quniform('siglen', 1, 50, 1),
        # 'smafastlen': hp.quniform('smafastlen', 1, 100, 1),
        # 'smaslowlen': hp.quniform('smaslowlen', 1, 100, 1),
    }

    best, report = BacktestIteration(macd_cross_backtest, default_parameters, hyperopt_parameters, args.max_evals)
    report.DataFrame.to_csv('TradeData.csv')
    report.Equity.to_csv('Equity.csv')
