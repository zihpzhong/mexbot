import pandas as pd
import numpy as np
from backtest import Backtest, BacktestReport, BacktestIteration
from hyperopt import hp
from numba import jit
from indicator import *

# テストデータ読み込み
data = pd.read_csv('csv/bitmex_201801_1h.csv', index_col='timestamp', parse_dates=True)

@jit
def channel_breakout_backtest(ohlcv, breakout_in, breakout_out, rsiperiod, overBought, overSold, fastperiod, slowperiod, filterth, take_profit, stop_loss, trailing_stop, klot):
    ignore = int(max(breakout_in, breakout_out))

    # エントリー・エグジット
    long_entry_price = highest(ohlcv.high, breakout_in) + 0.5
    long_exit_price = lowest(ohlcv.low, breakout_out) - 0.5
    short_entry_price = lowest(ohlcv.low, breakout_in) - 0.5
    short_exit_price = highest(ohlcv.high, breakout_out) + 0.5

    # 値が確定するまでの間はノーポジ
    long_entry_price[:ignore] = 0
    long_exit_price[:ignore] = 0
    short_entry_price[:ignore] = 0
    short_exit_price[:ignore] = 0

    # RSIによる利確とエントリー制限
    if rsiperiod:
        vrsi = rsi(ohlcv.close, rsiperiod)
        long_entry_price[vrsi > overBought] = 0
        long_exit_price[vrsi > overBought] = ohlcv.close
        short_entry_price[vrsi < overSold] = 0
        short_exit_price[vrsi < overSold] = ohlcv.close

    # 2つの移動平均線の剥離によるエントリー制限
    fastsma = sma(ohlcv.close, fastperiod)
    slowsma = sma(ohlcv.close, slowperiod)
    # if filterth > 0:
    #     ignoreEntry = (fastsma - slowsma).abs() > filterth
    #     long_entry_price[ignoreEntry] = 0
    #     short_entry_price[ignoreEntry] = 0

    # 2つの移動平均線の剥離によるロット制限
    if klot > 0:
        lots = (1 - (fastsma / slowsma)).abs()
        lots = (1 - lots * klot)
        lots.clip(0.01, 1.0, inplace=True)
        lots = lots
    else:
        lots = 1

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

    # 成り行き売買時の条件設定
    long_entry = ohlcv.close > long_entry_price.shift(1)
    long_exit = ohlcv.close < long_exit_price.shift(1)
    short_entry = ohlcv.close < short_entry_price.shift(1)
    short_exit = ohlcv.close > short_exit_price.shift(1)

    if rsiperiod:
        long_exit[vrsi > overBought] = True
        short_exit[vrsi < overSold] = True

    long_entry[:ignore] = 0
    long_exit[:ignore] = 0
    short_entry[:ignore] = 0
    short_exit[:ignore] = 0

    # STOP注文の場合、1
    if 1:
        long_entry = None
        long_exit = None
        short_entry = None
        short_exit = None
    # 成り行き注文の場合、0
    else:
        long_entry_price = None
        long_exit_price = None
        short_entry_price = None
        short_exit_price = None

    # バックテスト実施
    entry_exit = pd.DataFrame({'close':ohlcv.close, 'open':ohlcv.open, 'lots':lots,
        'long_entry_price':long_entry_price, 'long_exit_price':long_exit_price, 'long_entry':long_entry, 'long_exit':long_exit,
        'short_entry_price':short_entry_price, 'short_entry':short_entry, 'short_exit_price':short_exit_price, 'short_exit':short_exit})#, index=ohlcv.index)
    entry_exit.to_csv('entry_exit.csv')

    return Backtest(ohlcv, buy_entry=long_entry, sell_entry=short_entry, buy_exit=long_exit, sell_exit=short_exit,
        stop_buy_entry=long_entry_price, stop_sell_entry=short_entry_price, stop_buy_exit=long_exit_price, stop_sell_exit=short_exit_price,
        lots=lots, spread=0, take_profit=take_profit, stop_loss=stop_loss, trailing_stop=trailing_stop, slippage=0)

default_parameters = {
    'ohlcv':data,
    'breakout_in':22,
    'breakout_out':22,
    'rsiperiod':0,
    'overBought':79,
    'overSold':29,
    'fastperiod':13,
    'slowperiod':26,
    'filterth':0,
    'take_profit':0,
    'stop_loss':0,
    'trailing_stop':0,
    'klot':0,
}

hyperopt_parameters = {
    'breakout_in': hp.quniform('breakout_in', 1, 30, 1),
    'breakout_out': hp.quniform('breakout_out', 1, 30, 1),
    # 'rsiperiod': hp.quniform('rsiperiod', 1, 50, 1),
    # 'overBought': hp.quniform('overBought', 50, 100, 1),
    # 'overSold': hp.quniform('overSold', 0, 50, 1),
    # 'fastperiod': hp.quniform('fastperiod', 1, 50, 1),
    # 'slowperiod': hp.quniform('slowperiod', 1, 50, 1),
    # 'filterth': hp.quniform('filterth', 1, 100, 1),
    # 'take_profit': hp.quniform('take_profit', 0, 100, 5),
    # 'stop_loss': hp.quniform('stop_loss', 0, 40, 2),
    # 'trailing_stop': hp.quniform('trailing_stop', 0, 100, 1),
    # 'klot': hp.loguniform('klot', 1, 10),
}

BacktestIteration(channel_breakout_backtest, default_parameters, hyperopt_parameters, 500)
