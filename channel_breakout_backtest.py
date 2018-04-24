# -*- coding: utf-8 -*-
import pandas as pd
import numpy as np
from backtest import Backtest, BacktestReport
from hyperopt import hp, tpe, Trials, fmin, rand, anneal
from numba import jit
from indicator import *

# テストデータ読み込み
data = pd.read_csv('csv/bitmex_20180420_1m.csv', index_col='timestamp', parse_dates=True)
#print(data.head())

@jit
def channel_breakout_backtest(ohlc, breakout_in, breakout_out, take_profit=0, stop_loss=0, trailing_stop=0):

    ignore = max(breakout_in, breakout_out)

    # HLバンド
    long_entry_price = highest(ohlc.high, breakout_in)
    long_exit_price = lowest(ohlc.low, breakout_out)

    short_entry_price = lowest(ohlc.low, breakout_in)
    short_exit_price = highest(ohlc.high, breakout_out)

    long_entry_price[:ignore] = 0
    long_exit_price[:ignore] = 0

    short_entry_price[:ignore] = 0
    short_exit_price[:ignore] = 0

    long_entry = ohlc.close > long_entry_price.shift(1)
    long_exit = ohlc.close < long_exit_price.shift(1)

    short_entry = ohlc.close < short_entry_price.shift(1)
    short_exit = ohlc.close > short_exit_price.shift(1)

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
    entry_exit = pd.DataFrame({'close':ohlc.close, 'open':ohlc.open,
        'long_entry_price':long_entry_price, 'long_exit_price':long_exit_price, 'long_entry':long_entry, 'long_exit':long_exit,
        'short_entry_price':short_entry_price, 'short_entry':short_entry, 'short_exit_price':short_exit_price, 'short_exit':short_exit})#, index=data.index)
    entry_exit.to_csv('entry_exit.csv')

    return Backtest(data, buy_entry=long_entry, sell_entry=short_entry, buy_exit=long_exit, sell_exit=short_exit,
        stop_buy_entry=long_entry_price, stop_sell_entry=short_entry_price, stop_buy_exit=long_exit_price, stop_sell_exit=short_exit_price,
        lots=1, spread=0.5, take_profit=take_profit, stop_loss=stop_loss, trailing_stop=trailing_stop, slippage=0)

breakout_in = 20
breakout_out = 10
take_profit = 0
stop_loss = 0
trailing_stop = 10

# report = channel_breakout_backtest(data, breakout_in, breakout_out, take_profit, stop_loss)
# report.Raw.Trades.to_csv('trades.csv')
# report.Raw.PL.to_csv('pl.csv')
# report.Equity.to_csv('equity.csv')

# long = report.Raw.Trades['Long']
# long = long[long != 0]
# print(long)

# long = report.Raw.PL['Long']
# long = long[long != 0]
# print(long)

# short = report.Raw.Trades['Short']
# short = short[short != 0]
# print(short)

# short = report.Raw.PL['Short']
# short = short[short != 0]
# print(short)

# print(report)
# exit()

# 参考
# https://qiita.com/kenchin110100/items/ac3edb480d789481f134

def objective(args):
    global take_profit, stop_loss, breakout_in, breakout_out
    # breakout_in = int(args['breakout_in'])
    # breakout_out = int(args['breakout_out'])
    # take_profit = int(args['take_profit'])
    # stop_loss = int(args['stop_loss'])
    trailing_stop = int(args['trailing_stop'])

    # if breakout_in < breakout_out:
    #     return 10000

    report = channel_breakout_backtest(data, breakout_in, breakout_out, take_profit, stop_loss, trailing_stop)
    print(breakout_in, ',', breakout_out, ',', take_profit, ',', stop_loss, ',', trailing_stop, ',', report.ProfitFactor, ',', report.Profit, ',', report.GrossProfit, ',', report.GrossLoss, ',', report.Trades, ',', report.WinTrades, ',', report.LossTrades, ',', report.WinRatio)
    return -1 * report.ProfitFactor

# 探索するパラメータ
hyperopt_parameters = {
    # 'breakout_in': hp.quniform('breakout_in', 1, 30, 1),
    # 'breakout_out': hp.quniform('breakout_out', 1, 30, 1),
    # 'take_profit': hp.quniform('take_profit', 0, 100, 5),
    # 'stop_loss': hp.quniform('stop_loss', 0, 40, 2),
    'trailing_stop': hp.quniform('trailing_stop', 0, 100, 1),
}

# iterationする回数
max_evals = 100

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

breakout_in = int(best['breakout_in']) if 'breakout_in' in best else breakout_in
breakout_out = int(best['breakout_out']) if 'breakout_out' in best else breakout_out
take_profit = int(best['take_profit']) if 'take_profit' in best else take_profit
stop_loss = int(best['stop_loss']) if 'stop_loss' in best else stop_loss
trailing_stop = int(best['trailing_stop']) if 'trailing_stop' in best else trailing_stop

report = channel_breakout_backtest(data, breakout_in, breakout_out, take_profit, stop_loss, trailing_stop)
report.Raw.Trades.to_csv('trades.csv')
report.Raw.PL.to_csv('pl.csv')
report.Equity.to_csv('equity.csv')
print(report)
