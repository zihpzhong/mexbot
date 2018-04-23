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
def rsi_backtest(ohlc, length, overBought, overSold):

    # インジケーター作成
    vrsi = rsi(ohlc.close, length)
    vrsi_last = vrsi.shift(1)

    # エントリー／イグジット
    long_entry = (vrsi > overSold) & (vrsi_last < overSold)
    long_exit = (vrsi > overBought) & (vrsi_last < overBought)
    short_entry = (vrsi < overBought) & (vrsi_last > overBought)
    short_exit = (vrsi < overSold) & (vrsi_last > overSold)

    long_entry_price = None
    long_exit_price = None
    short_entry_price = None
    short_exit_price = None

    long_entry[:length] = False
    long_exit[:length] = False
    short_entry[:length] = False
    short_exit[:length] = False

    # long_entry_price[:length] = 0
    # long_exit_price[:length] = 0
    # short_entry_price[:length] = 0
    # short_exit_price[:length] = 0

    entry_exit = pd.DataFrame({'close':ohlc.close, 'rsi':vrsi, 'rsi-last':vrsi_last,
        'long_entry_price':long_entry_price, 'long_exit_price':long_exit_price, 'long_entry':long_entry, 'long_exit':long_exit,
        'short_entry_price':short_entry_price, 'short_entry':short_entry, 'short_exit_price':short_exit_price, 'short_exit':short_exit})#, index=data.index)
    entry_exit.to_csv('entry_exit.csv')

    return Backtest(data, buy_entry=long_entry, sell_entry=short_entry, buy_exit=long_exit, sell_exit=short_exit,
        stop_buy_entry=long_entry_price, stop_sell_entry=short_entry_price, stop_buy_exit=long_exit_price, stop_sell_exit=short_exit_price,
        lots=1, spread=0, take_profit=0, stop_loss=0, trailing_stop=10, slippage=0)

length = 14
overBought = 78
overSold = 30

report = rsi_backtest(data, length, overBought, overSold)
print(report)
report.Raw.Trades.to_csv('trades.csv')
report.Raw.PL.to_csv('pl.csv')
report.Equity.to_csv('equity.csv')
exit()

def objective(args):
    length = int(args['length'])
    overBought = int(args['overBought'])
    overSold = int(args['overSold'])

    if overBought <= overSold:
    	return 10000

    report = rsi_backtest(data, length, overBought, overSold)

    print(length, ',', overBought, ',', overSold, ',', report.ProfitFactor, ',', report.Profit, ',', report.GrossProfit, ',', report.GrossLoss, ',', report.Trades, ',', report.WinTrades, ',', report.LossTrades, ',', report.WinRatio)
    return -1 * report.Profit

# 探索するパラメータ
hyperopt_parameters = {
    'length': hp.quniform('length', 1, 30, 1),
    'overBought': hp.quniform('overBought', 1, 99, 3),
    'overSold': hp.quniform('overSold', 1, 99, 3),
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

report = rsi_backtest(data, int(best['length']), int(best['overBought']), int(best['overSold']))
print(report)
