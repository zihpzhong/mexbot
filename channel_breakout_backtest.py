import pandas as pd
import numpy as np
from backtest import Backtest, BacktestReport, BacktestIteration
from hyperopt import hp
from indicator import *

def channel_breakout_backtest(ohlcv, breakout_in, breakout_out, fastperiod, slowperiod, filterth, klot):
    ignore = int(max([breakout_in, breakout_out, fastperiod, slowperiod]))

    # エントリー・エグジット
    stop_buy_entry = highest(ohlcv.high, breakout_in) + 0.5
    stop_buy_exit = lowest(ohlcv.low, breakout_out) - 0.5
    stop_sell_entry = lowest(ohlcv.low, breakout_in) - 0.5
    stop_sell_exit = highest(ohlcv.high, breakout_out) + 0.5

    # 値が確定するまでの間はノーポジ
    stop_buy_entry[:ignore] = 0
    stop_buy_exit[:ignore] = 0
    stop_sell_entry[:ignore] = 0
    stop_sell_exit[:ignore] = 0

    # 2つの移動平均線の剥離によるエントリー制限
    if filterth > 0:
        fastsma = sma(ohlcv.close, fastperiod)
        slowsma = sma(ohlcv.close, slowperiod)
        ignoreEntry = (fastsma - slowsma).abs() > filterth
        stop_buy_entry[ignoreEntry] = 0
        stop_sell_entry[ignoreEntry] = 0

    # 2つの移動平均線の剥離によるロット制限
    if klot > 0:
        fastsma = sma(ohlcv.close, fastperiod)
        slowsma = sma(ohlcv.close, slowperiod)
        lots = (1 - (fastsma / slowsma)).abs()
        lots = (1 - lots * klot)
        lots.clip(0.01, 1.0, inplace=True)
        lots = lots * 10

    # ATRによるロット制限
    # if klot > 0:
    #     lots = atr(ohlcv.close, ohlcv.high, ohlcv.low, 14)
    #     lots = 1 - (lots / klot)
    #     lots.clip(0.001, 1.0, inplace=True)
    #     lots = lots * 10
    # else:
    #     lots = 1

    # 標準偏差によるロット制限
    # if klot > 0:
    #     lots = stdev(ohlcv.close, 20)
    #     lots = 1 - (lots / klot)
    #     lots.clip(0.001, 1.0, inplace=True)
    #     lots = lots
    # else:
    #     lots = 1

    # バックテスト実施
    entry_exit = pd.DataFrame({'close':ohlcv.close, 'open':ohlcv.open, 'lots':lots,
        'stop_buy_entry':stop_buy_entry, 'stop_buy_exit':stop_buy_exit, 'stop_sell_entry':stop_sell_entry, 'stop_sell_exit':stop_sell_exit})#, index=ohlcv.index)
    entry_exit.to_csv('entry_exit.csv')

    return Backtest(**locals())

if __name__ == '__main__':

    # テストデータ読み込み
    ohlcv = pd.read_csv('csv/bitmex_2018_1h.csv', index_col='timestamp', parse_dates=True)

    default_parameters = {
        'ohlcv':ohlcv,
        'breakout_in':18,
        'breakout_out':18,
        'fastperiod':89,
        'slowperiod':91,
        'filterth':19,
        'klot':0,
    }

    hyperopt_parameters = {
        # 'breakout_in': hp.quniform('breakout_in', 1, 30, 1),
        # 'breakout_out': hp.quniform('breakout_out', 1, 30, 1),
        # 'fastperiod': hp.quniform('fastperiod', 1, 300, 10),
        # 'slowperiod': hp.quniform('slowperiod', 1, 300, 10),
        'filterth': hp.quniform('filterth', 1, 300, 1),
        # 'klot': hp.loguniform('klot', 1, 10),
    }

    best, report = BacktestIteration(channel_breakout_backtest, default_parameters, hyperopt_parameters, 0)
