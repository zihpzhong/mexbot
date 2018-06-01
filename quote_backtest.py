# -*- coding: utf-8 -*-
import pandas as pd
from backtest import Backtest, BacktestReport, BacktestIteration
from hyperopt import hp
from indicator import *
from functools import lru_cache


def shooter_backtest(ohlcv, asklength, bidlength):

    buysize = ohlcv['buy_volume']
    sellsize = ohlcv['sell_volume']

    @lru_cache(maxsize=None)
    def cached_buysize(period):
        return sma(buysize, period)

    @lru_cache(maxsize=None)
    def cached_sellsize(period):
        return sma(sellsize, period)

    # インジケーター作成
    bid = cached_buysize(bidlength)
    ask = cached_sellsize(asklength)

    # エントリー／イグジット
    buy_entry = bid > ask
    sell_entry = ask > bid
    buy_exit = sell_entry
    sell_exit = buy_entry

    ignore = int(max(asklength, bidlength))
    buy_entry[:ignore] = False
    buy_exit[:ignore] = False
    sell_entry[:ignore] = False
    sell_exit[:ignore] = False

    #buy_size = sell_size = 500 / ohlcv.close
    # entry_exit = pd.DataFrame({'close':ohlcv.close, 'ask':ask, 'bid':bid,
    #     'buy_entry_price':buy_entry_price, 'buy_exit_price':buy_exit_price, 'buy_entry':buy_entry, 'buy_exit':buy_exit,
    #     'sell_entry_price':sell_entry_price, 'sell_entry':sell_entry, 'sell_exit_price':sell_exit_price, 'sell_exit':sell_exit})#, index=ohlcv.index)
    # entry_exit.to_csv('entry_exit.csv')

    return Backtest(**locals())


if __name__ == '__main__':

    # テストデータ読み込み
    ohlcv = pd.read_csv('csv/xbtusd_trade-20s.csv', index_col='timestamp', parse_dates=True)

    default_parameters = {
        'ohlcv': ohlcv,
        'asklength':55,
        'bidlength':87,
    }

    hyperopt_parameters = {
        'asklength': hp.quniform('asklength', 1, 100, 1),
        'bidlength': hp.quniform('bidlength', 1, 100, 1),
    }

    best, report = BacktestIteration(shooter_backtest, default_parameters, hyperopt_parameters, 0)
