# -*- coding: utf-8 -*-
import pandas as pd
import numpy as np
from backtest import Backtest, BacktestReport
from hyperopt import hp, tpe, Trials, fmin, rand, anneal
from numba import jit
from indicator import *

# テストデータ読み込み
data = pd.read_csv('csv/bitmex_20180501-5m.csv', index_col='timestamp', parse_dates=True)

@jit
def bband_backtest(ohlc, length, multi):

    # インジケーター作成
    source = ohlc.close
    basis = sma(source, length)
    dev = multi * stdev(source, length)
    upper = basis + dev
    lower = basis - dev

    buyEntry = crossover(source, lower)
    sellEntry = crossunder(source, upper)

    # エントリー／イグジット
    long_entry = buyEntry
    long_exit = sellEntry
    short_entry = sellEntry
    short_exit = buyEntry

    long_entry[:length] = False
    long_exit[:length] = False
    short_entry[:length] = False
    short_exit[:length] = False

    # long_entry_price = upper
    # long_entry_price[~buyEntry] = 0

    # short_entry_price = lower
    # short_entry_price[~sellEntry] = 0

    # long_exit_price = short_entry_price
    # short_exit_price = long_entry_price

    # long_entry_price[:length] = 0
    # long_exit_price[:length] = 0
    # short_entry_price[:length] = 0
    # short_exit_price[:length] = 0

    entry_exit = pd.DataFrame({'close':ohlc.close, 'upper':upper, 'lower':lower,
    	'long_entry':long_entry, 'long_exit':long_exit, 'short_entry':short_entry, 'short_exit':short_exit,
    	#'long_entry_price':long_entry_price, 'long_exit_price':long_exit_price, 'short_entry_price':short_entry_price, 'short_exit_price':short_exit_price,
    	})
    entry_exit.to_csv('entry_exit.csv')

    return Backtest(data,
    	buy_entry=long_entry, sell_entry=short_entry, buy_exit=long_exit, sell_exit=short_exit,
        #stop_buy_entry=long_entry_price, stop_sell_entry=short_entry_price, stop_buy_exit=long_exit_price, stop_sell_exit=short_exit_price,
        lots=1, spread=0, take_profit=0, stop_loss=0, trailing_stop=0, slippage=0)

length = 20
multi = 2

# report = bband_backtest(data, length, multi)
# print(report)
# report.Raw.Trades.to_csv('trades.csv')
# report.Raw.PL.to_csv('pl.csv')
# report.Equity.to_csv('equity.csv')
# exit()

def objective(args):
    #length = int(args['length'])
    multi = args['multi']

    report = bband_backtest(data, length, multi)
    print(length, ',', multi, ',', report.ProfitFactor, ',', report.Profit, ',', report.GrossProfit, ',', report.GrossLoss, ',', report.Trades, ',', report.WinTrades, ',', report.LossTrades, ',', report.WinRatio, ',', report.ExpectedValue,)
    return -1 * report.ProfitFactor

# 探索するパラメータ
hyperopt_parameters = {
    #'length': hp.quniform('length', 1, 60, 1),
    'multi': hp.uniform('multi', 0.1, 3.0),
}

# iterationする回数
max_evals = 500

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

length = int(best['length']) if 'length' in best else length
multi = best['multi'] if 'multi' in best else multi

report = bband_backtest(data, length, multi)
print(report)
