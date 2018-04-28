# -*- coding: utf-8 -*-
import pandas as pd
import numpy as np
from backtest import Backtest, BacktestReport
from hyperopt import hp, tpe, Trials, fmin, rand, anneal
from numba import jit
from indicator import *

# テストデータ読み込み
data = pd.read_csv('csv/bitmex_20180421-29_5m.csv', index_col='timestamp', parse_dates=True)
#print(data.head())

@jit
def pivot_backtest(ohlc, leftbars, rightbars, trailing_stop=0):

    ignore = leftbars + rightbars

    # ピボットハイ＆ロー
    long_entry_price = pivothigh(ohlc.high, leftbars, rightbars).ffill()
    short_entry_price = pivotlow(ohlc.low, leftbars, rightbars).ffill()
    long_exit_price = short_entry_price
    short_exit_price = long_entry_price

    long_entry_price[:ignore] = 0
    long_exit_price[:ignore] = 0

    short_entry_price[:ignore] = 0
    short_exit_price[:ignore] = 0

    long_entry = ohlc.close > long_entry_price
    short_entry = ohlc.close < short_entry_price

    long_exit = short_entry
    short_exit = long_entry

    long_entry[:ignore] = 0
    long_exit[:ignore] = 0

    short_entry[:ignore] = 0
    short_exit[:ignore] = 0

    # STOP注文
    if 1:
        long_entry = None
        long_exit = None
        short_entry = None
        short_exit = None
    # 成り行き注文
    else:
        long_entry_price = None
        long_exit_price = None
        short_entry_price = None
        short_exit_price = None

    # バックテスト実施
    entry_exit = pd.DataFrame({'close':ohlc.close, 'high':ohlc.high, 'low':ohlc.low,
        'long_entry_price':long_entry_price, 'long_exit_price':long_exit_price, 'long_entry':long_entry, 'long_exit':long_exit,
        'short_entry_price':short_entry_price, 'short_entry':short_entry, 'short_exit_price':short_exit_price, 'short_exit':short_exit})#, index=data.index)
    entry_exit.to_csv('entry_exit.csv')

    return Backtest(data, buy_entry=long_entry, sell_entry=short_entry, buy_exit=long_exit, sell_exit=short_exit,
        stop_buy_entry=long_entry_price, stop_sell_entry=short_entry_price, stop_buy_exit=long_exit_price, stop_sell_exit=short_exit_price,
        lots=1, spread=6, trailing_stop=trailing_stop, slippage=0)

leftbars = 14
rightbars = 19
trailing_stop = 0

# report = pivot_backtest(data, leftbars, rightbars, trailing_stop)
# report.Raw.Trades.to_csv('trades.csv')
# report.Raw.PL.to_csv('pl.csv')
# report.Equity.to_csv('equity.csv')
# print(report)
# exit()

# 参考
# https://qiita.com/kenchin110100/items/ac3edb480d789481f134

def objective(args):
    leftbars = int(args['leftbars'])
    rightbars = int(args['rightbars'])
    # take_profit = int(args['take_profit'])
    # stop_loss = int(args['stop_loss'])
    # trailing_stop = int(args['trailing_stop'])
    report = pivot_backtest(data, leftbars, rightbars, trailing_stop)
    print(leftbars, ',', rightbars, ',', trailing_stop, ',', report.ProfitFactor, ',', report.Profit, ',', report.GrossProfit, ',', report.GrossLoss, ',', report.Trades, ',', report.WinTrades, ',', report.LossTrades, ',', report.WinRatio)
    return -1 * report.ProfitFactor

# 探索するパラメータ
hyperopt_parameters = {
    'leftbars': hp.quniform('leftbars', 1, 20, 1),
    'rightbars': hp.quniform('rightbars', 0, 20, 1),
    # 'trailing_stop': hp.quniform('trailing_stop', 0, 100, 1),
}

# iterationする回数
max_evals = 1000

# 試行の過程を記録するインスタンス
trials = Trials()

best = fmin(
    # 最小化する値を定義した関数
    objective,
    # 探索するパラメータのdictもしくはlist
    hyperopt_parameters,
    # どのロジックを利用するか、基本的にはtpe.suggestでok
    # rand.suggest ランダム・サーチ？
    # anneal.suggest 焼きなましっぽい
    algo=tpe.suggest,
    #algo=rand.suggest,
    #algo=anneal.suggest,
    max_evals=max_evals,
    trials=trials,
    # 試行の過程を出力
    verbose=0
)

print('best:', best)

leftbars = int(best['leftbars']) if 'leftbars' in best else leftbars
rightbars = int(best['rightbars']) if 'rightbars' in best else rightbars
trailing_stop = int(best['trailing_stop']) if 'trailing_stop' in best else trailing_stop

report = pivot_backtest(data, leftbars, rightbars, trailing_stop)
report.Raw.Trades.to_csv('trades.csv')
report.Raw.PL.to_csv('pl.csv')
report.Equity.to_csv('equity.csv')
print(report)
