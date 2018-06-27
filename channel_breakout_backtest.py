import pandas as pd
import numpy as np
from backtest import Backtest, BacktestReport, BacktestIteration
from hyperopt import hp
from indicator import *

def channel_breakout_backtest(ohlcv, breakout_in, breakout_out):

    # エントリー・エグジット
    stop_buy_entry = highest(ohlcv.high, breakout_in) + 0.5
    stop_buy_exit = lowest(ohlcv.low, breakout_out) - 0.5
    stop_sell_entry = lowest(ohlcv.low, breakout_in) - 0.5
    stop_sell_exit = highest(ohlcv.high, breakout_out) + 0.5

    # 値が確定するまでの間はノーポジ
    ignore = int(max([breakout_in, breakout_out]))
    stop_buy_entry[:ignore] = 0
    stop_buy_exit[:ignore] = 0
    stop_sell_entry[:ignore] = 0
    stop_sell_exit[:ignore] = 0

    # バックテスト実施
    # entry_exit = pd.DataFrame({'close':ohlcv.close, 'open':ohlcv.open,
    #     'stop_buy_entry':stop_buy_entry, 'stop_buy_exit':stop_buy_exit, 'stop_sell_entry':stop_sell_entry, 'stop_sell_exit':stop_sell_exit})
    # entry_exit.to_csv('entry_exit.csv')

    return Backtest(**locals())

if __name__ == '__main__':

    # テストデータ読み込み
    ohlcv = pd.read_csv('csv/bitmex_2018_1h.csv', index_col='timestamp', parse_dates=True)

    default_parameters = {
        'ohlcv':ohlcv,
        'breakout_in':18,
        'breakout_out':18,
        # 'fastperiod':89,
        # 'slowperiod':91,
        # 'filterth':19,
    }

    hyperopt_parameters = {
        'breakout_in': hp.quniform('breakout_in', 1, 100, 1),
        'breakout_out': hp.quniform('breakout_out', 1, 100, 1),
    }

    best, report = BacktestIteration(channel_breakout_backtest, default_parameters, hyperopt_parameters, 300)
    report.DataFrame.to_csv('TradeData.csv')
    report.Equity.to_csv('Equity.csv')
