# -*- coding: utf-8 -*-
import pandas as pd
from backtest import Backtest, BacktestReport, BacktestIteration
from hyperopt import hp
from indicator import *
from functools import lru_cache


def quote_backtest(ohlcv, asklength, bidlength):

    @lru_cache(maxsize=None)
    def cached_buysize(period):
        #buysize = change(ohlcv['buy_volume'])
        #return sma(buysize, period)
        buysize = (ohlcv['buy_volume'])
        return rsi(buysize, period)

    @lru_cache(maxsize=None)
    def cached_sellsize(period):
        #sellsize = change(ohlcv['sell_volume'])
        #return sma(sellsize, period)
        sellsize = (ohlcv['sell_volume'])
        return rsi(sellsize, period)

    # インジケーター作成
    bid = cached_buysize(bidlength)
    ask = cached_sellsize(asklength)

    # エントリー／イグジット
    buy_entry = (bid > ask)
    sell_entry = (bid < ask)
    buy_exit = sell_entry
    sell_exit = buy_entry

    ignore = int(max(asklength, bidlength))
    buy_entry[:ignore] = False
    buy_exit[:ignore] = False
    sell_entry[:ignore] = False
    sell_exit[:ignore] = False

    entry_exit = pd.DataFrame({'close':ohlcv.close, 'ask':ask, 'bid':bid,
        'buy_entry':buy_entry, 'buy_exit':buy_exit, 'sell_entry':sell_entry, 'sell_exit':sell_exit})
    entry_exit.to_csv('entry_exit.csv')

    return Backtest(**locals())


if __name__ == '__main__':

    # テストデータ読み込み
    ohlcv = pd.read_csv('csv/xbtusd_trade-20s.csv', index_col='timestamp', parse_dates=True)

    default_parameters = {
        'ohlcv': ohlcv,
        'asklength':26,
        'bidlength':20,
    }

    hyperopt_parameters = {
        'asklength': hp.quniform('asklength', 10, 100, 1),
        'bidlength': hp.quniform('bidlength', 10, 100, 1),
    }

    best, report = BacktestIteration(quote_backtest, default_parameters, hyperopt_parameters, 0, maximize=lambda r:r.All.Profit)
    report.DataFrame.to_csv('TradeData.csv')
    report.Equity.to_csv('Equity.csv')
