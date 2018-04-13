# -*- coding: utf-8 -*-
import pandas as pd
import numpy as np
from backtest import Backtest, BacktestReport
from hyperopt import hp, tpe, Trials, fmin, rand, anneal
from numba import jit

def highest(series, window):
    return series.rolling(window).max()

def lowest(series, window):
    return series.rolling(window).min()

# テストデータ読み込み
data = pd.read_csv('bitmex_201804_1m.csv', index_col='timestamp', parse_dates=True)
#print(data.head())

@jit
def channel_breakout_backtest(ohlc, breakout_in, breakout_out, take_profit=0, stop_loss=0):
    # インジケーター作成
    long_entry_price = highest(ohlc.high, breakout_in)
    long_exit_price = lowest(ohlc.low, breakout_out)

    short_entry_price = lowest(ohlc.low, breakout_in)
    short_exit_price = highest(ohlc.high, breakout_out)

    # エントリー／イグジット
    long_entry = ohlc.close > long_entry_price.shift(1)
    long_exit = ohlc.close < long_exit_price.shift(1)

    short_entry = ohlc.close < short_entry_price.shift(1)
    short_exit = ohlc.close > short_exit_price.shift(1)

    long_entry[:breakout_in] = False
    short_entry[:breakout_in] = False
    long_exit[:breakout_out] = False
    short_exit[:breakout_out] = False

    # バックテスト実施
    # entry_exit = pd.DataFrame({'close':ohlc.close, 'open':ohlc.open,
    #     'long_entry_price':long_entry_price, 'long_exit_price':long_exit_price, 'long_entry':long_entry, 'long_exit':long_exit,
    #     'short_entry_price':short_entry_price, 'short_entry':short_entry, 'short_exit_price':short_exit_price, 'short_exit':short_exit}, index=data.index)
    # print(entry_exit.to_csv())

    return Backtest(data, buy_entry=long_entry, sell_entry=short_entry, buy_exit=long_exit, sell_exit=short_exit, lots=1, spread=0.5, take_profit=take_profit, stop_loss=stop_loss)

# 参考
# https://qiita.com/kenchin110100/items/ac3edb480d789481f134

take_profit = 0
stop_loss = 40

def objective(args):
    breakout_in = int(args['breakout_in'])
    breakout_out = int(args['breakout_out'])

    # if breakout_in < breakout_out:
    #     return 10000

    report = channel_breakout_backtest(data, breakout_in, breakout_out, take_profit, stop_loss)

    print(breakout_in, ',', breakout_out, ',', take_profit, ',', stop_loss, ',', report.ProfitFactor, ',', report.Profit, ',', report.GrossProfit, ',', report.GrossLoss, ',', report.Trades, ',', report.WinTrades, ',', report.LossTrades, ',', report.WinRatio)
    return -1 * report.ProfitFactor

# 探索するパラメータ
hyperopt_parameters = {
    'breakout_in': hp.quniform('breakout_in', 5, 100, 2),
    'breakout_out': hp.quniform('breakout_out', 5, 100, 2),
}

# iterationする回数
max_evals = 200

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

report = channel_breakout_backtest(data, int(best['breakout_in']), int(best['breakout_out']), take_profit, stop_loss)
print(report)
