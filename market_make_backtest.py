# -*- coding: utf-8 -*-
import pandas as pd
from backtest import Backtest, BacktestWithTickData, BacktestReport, BacktestIteration
from hyperopt import hp
from indicator import *
from functools import lru_cache


def market_make_backtest(ohlcv, period, margin):

    range_high = highest(ohlcv.high, period)
    range_low = lowest(ohlcv.low, period)

    middle_price = (range_high + range_low) / 2 
    limit_buy_entry = middle_price - (margin/2)
    limit_buy_exit = middle_price + (margin/2)
    limit_sell_entry = middle_price + (margin/2)
    limit_sell_exit = middle_price - (margin/2)

    # バックテスト実施
    # entry_exit = pd.DataFrame({'close':ticks['close'], 'high':ticks['high'], 'low':ticks['low'],
    #     'limit_buy_entry':limit_buy_entry, 'limit_buy_exit':limit_buy_exit})
    # entry_exit.to_csv('entry_exit.csv')

    buy_size = sell_size = 0.02
    max_buy_size = max_sell_size = 0.02

    return Backtest(**locals())
    # return BacktestWithTickData(**locals())


if __name__ == '__main__':

    # テストデータ読み込み
    ohlcv = pd.read_csv('csv/bffx_2018-6-22_3s.csv', index_col="timestamp", parse_dates=True)
    # ohlcv = ohlcv[:3000]
    # ticks = pd.read_csv('csv/bffx_2018-6-22.csv', names=['id', 'side', 'price', 'size', 'exec_date'], index_col="exec_date", parse_dates=True)
    # ticks = ticks[300000:]

    default_parameters = {
        # 'ticks': ticks,
        'ohlcv': ohlcv,
        'period': 1,
        'margin': 500,
    }

    hyperopt_parameters = {
        'period': hp.quniform('period', 1, 100, 1),
        # 'margin': hp.quniform('margin', 1, 50, 0.5),
        # 'period': hp.quniform('period', 10, 1000, 10),
        'margin': hp.quniform('margin', 100, 5000, 50),
    }

    def maximize(r):
        return ((r.All.WinRatio * r.All.WinPct) + ((1 - r.All.WinRatio) * r.All.LossPct)) * r.All.Trades
        # return r.All.WinPct * r.All.WinRatio * r.All.WinTrades

    best, report = BacktestIteration(market_make_backtest, default_parameters, hyperopt_parameters, 0, maximize=maximize)
    report.DataFrame.to_csv('TradeData.csv')
    report.Equity.to_csv('Equity.csv')
