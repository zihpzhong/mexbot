# -*- coding: utf-8 -*-
import pandas as pd
from backtest import Backtest, BacktestWithTickData, BacktestReport, BacktestIteration
from hyperopt import hp
from indicator import *
from functools import lru_cache


def market_make_backtest(ohlcv, period, margin):

    buy_entry = None
    sell_entry = None
    buy_exit = None
    sell_exit = None

    limit_buy_entry = None
    limit_sell_entry = None
    limit_buy_exit = None
    limit_sell_exit = None

    # シンプルハイロー
    # range_high = ohlcv.high
    # range_low = ohlcv.low
    # limit_buy_entry = range_low
    # limit_buy_exit = range_high
    # limit_sell_entry = range_high
    # limit_sell_exit = range_low

    # 売り買い優劣でエントリー価格を調整
    # buy_volume = sma(ohlcv.buy_volume, 3)
    # sell_volume = sma(ohlcv.sell_volume, 3)
    # limit_buy_entry = limit_buy_entry - (buy_volume < sell_volume) * 50
    # limit_buy_exit = limit_buy_exit - (buy_volume < sell_volume) * 50
    # limit_sell_entry = limit_sell_entry + (buy_volume > sell_volume) * 50
    # limit_sell_exit = limit_sell_exit + (buy_volume > sell_volume) * 50

    # 売り買い優劣でエントリー1
    # buy_volume = sma(ohlcv.buy_volume, period)
    # sell_volume = sma(ohlcv.sell_volume, period)
    # power = buy_volume - sell_volume
    # buy_entry = power > 0
    # sell_entry = power < 0
    # buy_exit = sell_entry
    # sell_exit = buy_entry

    # 売り買い優劣でエントリー2
    # buy_volume = rci(ohlcv.buy_volume, 20)
    # sell_volume = rci(ohlcv.sell_volume, 20)
    # buy_entry = (buy_volume > 0) & (sell_volume < 0)
    # sell_entry = (buy_volume < 0) & (sell_volume > 0)
    # buy_exit = sell_entry
    # sell_exit = buy_entry

    # 売り買い優劣でエントリー3
    buy_volume = rsi(ohlcv.buy_volume, period)
    sell_volume = rsi(ohlcv.sell_volume, period)
    power = buy_volume - sell_volume
    buy_entry = power > 0
    sell_entry = power < 0
    buy_exit = sell_entry
    sell_exit = buy_entry

    # 売り買い優劣でエントリー価格を調整2
    # buy_volume = rsi(ohlcv.buy_volume, 10)
    # sell_volume = rsi(ohlcv.sell_volume, 10)
    # limit_buy_entry = limit_buy_entry - (buy_volume < sell_volume) * 50
    # limit_buy_exit = limit_buy_exit - (buy_volume < sell_volume) * 50
    # limit_sell_entry = limit_sell_entry + (buy_volume > sell_volume) * 50
    # limit_sell_exit = limit_sell_exit + (buy_volume > sell_volume) * 50

    # ボリュームでエントリー価格を調整
    # buy_volume = sma(ohlcv.buy_volume, 1)
    # sell_volume = sma(ohlcv.sell_volume, 1)
    # restrict_volume = 20
    # limit_buy_entry = limit_buy_entry - (buy_volume > restrict_volume) * 50
    # limit_buy_exit = limit_buy_exit - (buy_volume > restrict_volume) * 50
    # limit_sell_entry = limit_sell_entry + (sell_volume > restrict_volume) * 50
    # limit_sell_exit = limit_sell_exit + (sell_volume > restrict_volume) * 50

    range_high = highest(ohlcv.high, period)
    range_low = lowest(ohlcv.low, period)
    limit_buy_entry = range_low
    limit_buy_exit = range_high
    limit_sell_entry = range_high
    limit_sell_exit = range_low

    # バックテスト実施
    # entry_exit = pd.DataFrame({'close':ohlcv['close'], 'high':ohlcv['high'], 'low':ohlcv['low'],
    #     'limit_buy_entry':limit_buy_entry, 'limit_buy_exit':limit_buy_exit, 'limit_sell_entry':limit_sell_entry, 'limit_sell_exit':limit_sell_exit,
    #     'buy_entry':buy_entry, 'buy_exit':buy_exit, 'sell_entry':sell_entry, 'sell_exit':limit_sell_exit,
    #     })
    # entry_exit.to_csv('entry_exit.csv')

    buy_size = sell_size = 0.01
    max_buy_size = max_sell_size = 0.01

    return Backtest(**locals())
    # return BacktestWithTickData(**locals())


if __name__ == '__main__':

    # テストデータ読み込み
    ohlcv = pd.read_csv('csv/bffx_20180618_3s.csv', index_col="timestamp", parse_dates=True)
    # ohlcv = ohlcv[:3000]
    # ticks = pd.read_csv('csv/bffx_2018-6-22.csv', names=['id', 'side', 'price', 'size', 'exec_date'], index_col="exec_date", parse_dates=True)
    # ticks = ticks[300000:]

    default_parameters = {
        # 'ticks': ticks,
        'ohlcv': ohlcv,
        'period': 5,
        'margin': 2000,
    }

    hyperopt_parameters = {
        # 'period': hp.quniform('period', 1, 100, 1),
        # 'margin': hp.quniform('margin', 1, 50, 0.5),
        # 'period': hp.quniform('period', 10, 1000, 10),
        # 'margin': hp.uniform('margin', 0.0001, 0.01),
    }

    def maximize(r):
        # return ((r.All.WinRatio * r.All.WinPct) + ((1 - r.All.WinRatio) * r.All.LossPct)) * r.All.Trades
        # return r.All.WinPct * r.All.WinRatio * r.All.WinTrades
        return r.All.Profit

    best, report = BacktestIteration(market_make_backtest, default_parameters, hyperopt_parameters, 0, maximize=maximize)
    report.DataFrame.to_csv('TradeData.csv')
    report.Equity.to_csv('Equity.csv')
