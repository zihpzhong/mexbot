# -*- coding: utf-8 -*-
import pandas as pd
from datetime import datetime
from backtest import Backtest, BacktestReport, BacktestIteration
from hyperopt import hp
from indicator import *
from functools import lru_cache

def inago_backtest(ohlcv, buyth, sellth, eventh):

    # エントリー／イグジット
    cond = (ohlcv.buy_volume > buyth) & (ohlcv.sell_volume > sellth) & ((ohlcv.buy_volume - ohlcv.sell_volume).abs() > eventh)
    buy_entry = (ohlcv.buy_volume > ohlcv.sell_volume) & cond & (change(ohlcv.close,3)<2000)
    sell_entry = (ohlcv.buy_volume < ohlcv.sell_volume) & cond & (change(ohlcv.close,3)>-2000)
    buy_exit = sell_entry
    sell_exit = buy_entry

    # entry_exit = pd.DataFrame({'close':ohlcv.close,
    #     'buy_entry':buy_entry, 'buy_exit':buy_exit, 'sell_entry':sell_entry, 'sell_exit':sell_exit})
    # entry_exit.to_csv('entry_exit.csv')

    return Backtest(**locals())


if __name__ == '__main__':

    # テストデータ読み込み
    ohlcv = pd.read_csv('csv/bffx_20180705_10s.csv', index_col='timestamp', parse_dates=True)

    default_parameters = {
        'ohlcv':ohlcv,
        'buyth':20,
        'sellth':20,
        'eventh':40,
    }

    hyperopt_parameters = {
        'buyth': hp.quniform('buyth', 5, 100, 1),
        'sellth': hp.quniform('sellth', 5, 100, 1),
        'eventh': hp.quniform('eventh', 5, 100, 1),
    }

    def maximize(r):
        return ((r.All.WinRatio * r.All.WinPct) + ((1 - r.All.WinRatio) * r.All.LossPct)) * r.All.Trades
        # return r.All.WinPct * r.All.WinRatio * r.All.WinTrades
        # return r.All.Profit

    best, report = BacktestIteration(inago_backtest, default_parameters, hyperopt_parameters, 0, maximize=maximize)
    report.DataFrame.to_csv('TradeData.csv')
    report.Equity.to_csv('Equity.csv')
