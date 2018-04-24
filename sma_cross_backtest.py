# -*- coding: utf-8 -*-
import pandas as pd
import numpy as np
from backtest import Backtest, BacktestReport
from hyperopt import hp, tpe, Trials, fmin, rand, anneal
from numba import jit
from indicator import *

# テストデータ読み込み
data = pd.read_csv('csv/bitmex_20180420_1m.csv', index_col='timestamp', parse_dates=True)

@jit
def sma_cross_backtest(ohlc, fastlen, slowlen, trailing_stop):

    # インジケーター作成
    vfast = sma(ohlc.close, fastlen)
    vslow = sma(ohlc.close, slowlen)
    vslow_last = vslow.shift(1)

    # エントリー／イグジット
    long_entry = crossover(vfast, vslow)
    long_exit = crossunder(vfast, vslow)

    short_entry = long_exit
    short_exit = long_entry

    long_entry_price = None
    long_exit_price = None
    short_entry_price = None
    short_exit_price = None

    ignore = max(fastlen, slowlen)
    long_entry[:ignore] = False
    long_exit[:ignore] = False
    short_entry[:ignore] = False
    short_exit[:ignore] = False

    # long_entry_price[:ignore] = 0
    # long_exit_price[:ignore] = 0
    # short_entry_price[:ignore] = 0
    # short_exit_price[:ignore] = 0

    entry_exit = pd.DataFrame({'close':ohlc.close, 'fast':vfast, 'slow':vslow,
        'long_entry_price':long_entry_price, 'long_exit_price':long_exit_price, 'long_entry':long_entry, 'long_exit':long_exit,
        'short_entry_price':short_entry_price, 'short_entry':short_entry, 'short_exit_price':short_exit_price, 'short_exit':short_exit})#, index=data.index)
    entry_exit.to_csv('entry_exit.csv')

    return Backtest(data, buy_entry=long_entry, sell_entry=short_entry, buy_exit=long_exit, sell_exit=short_exit,
        stop_buy_entry=long_entry_price, stop_sell_entry=short_entry_price, stop_buy_exit=long_exit_price, stop_sell_exit=short_exit_price,
        lots=1, spread=0, take_profit=0, stop_loss=0, trailing_stop=trailing_stop, slippage=0)

fastlength = 19#9
slowlength = 28#25
trailing_stop = 10

report = sma_cross_backtest(data, fastlength, slowlength, trailing_stop)
report.Raw.Trades.to_csv('trades.csv')
report.Raw.PL.to_csv('pl.csv')
report.Equity.to_csv('equity.csv')
print(report)
exit()

def objective(args):
    fastlength = int(args['fastlength'])
    slowlength = int(args['slowlength'])
    # trailing_stop = int(args['trailing_stop'])

    if fastlength >= slowlength:
        return 10000

    report = sma_cross_backtest(data, fastlength, slowlength, trailing_stop)

    print(fastlength, ',', slowlength, ',', trailing_stop, ',', report.ProfitFactor, ',', report.Profit, ',', report.GrossProfit, ',', report.GrossLoss, ',', report.Trades, ',', report.WinTrades, ',', report.LossTrades, ',', report.WinRatio)
    return -1 * report.Profit

# 探索するパラメータ
hyperopt_parameters = {
    'fastlength': hp.quniform('fastlength', 1, 50, 1),
    'slowlength': hp.quniform('slowlength', 1, 50, 1),
    # 'trailing_stop': hp.quniform('trailing_stop', 0, 20, 1),
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

fastlength = int(best['fastlength']) if 'fastlength' in best else fastlength
slowlength = int(best['slowlength']) if 'slowlength' in best else slowlength
trailing_stop = int(best['trailing_stop']) if 'trailing_stop' in best else trailing_stop

report = sma_cross_backtest(data, fastlength, slowlength, trailing_stop)
print(report)
