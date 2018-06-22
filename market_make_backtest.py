# -*- coding: utf-8 -*-
import pandas as pd
from backtest import Backtest, BacktestReport, BacktestIteration
from hyperopt import hp
from indicator import *
from functools import lru_cache


def market_make_backtest(ohlcv, period, margin):

    middle_price = (highest(ohlcv.high, period) + lowest(ohlcv.low, period)) / 2
    # middle_price = sma(ohlcv.close, period)
    limit_buy_entry = middle_price - (margin/2)
    limit_buy_exit = middle_price + (margin/2)
    limit_sell_entry = middle_price + (margin/2)
    limit_sell_exit = middle_price - (margin/2)

    # バックテスト実施
    # entry_exit = pd.DataFrame({'close':ohlcv['close'], 'high':ohlcv['high'], 'low':ohlcv['low'],
    #     'limit_buy_entry':limit_buy_entry, 'limit_buy_exit':limit_buy_exit})
    # entry_exit.to_csv('entry_exit.csv')

    return Backtest(**locals())


if __name__ == '__main__':

    # テストデータ読み込み
    ohlcv = pd.read_csv('csv/bffx_20180618_3s.csv', index_col="timestamp", parse_dates=True)
    #ohlcv = ohlcv[2000:3000]

    default_parameters = {
        'ohlcv': ohlcv,
        'period': 5,
        'margin': 5000,
    }

    hyperopt_parameters = {
        'period': hp.quniform('period', 1, 100, 1),
        'margin': hp.quniform('margin', 50, 5000, 50),
    }

    best, report = BacktestIteration(market_make_backtest, default_parameters, hyperopt_parameters, 0, maximize=lambda r:r.All.ProfitFactor)
    report.DataFrame.to_csv('TradeData.csv')
    report.Equity.to_csv('Equity.csv')
