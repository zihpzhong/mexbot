# -*- coding: utf-8 -*-
import pandas as pd
import numpy as np
from backtest import Backtest, BacktestReport
from hyperopt import hp, tpe, Trials, fmin, rand, anneal
from numba import jit
from indicator import *

# テストデータ読み込み
data = pd.read_csv('csv/bitmex_20180422_1m.csv', index_col='timestamp', parse_dates=True)

@jit
def rsi_backtest(ohlc, length, overBought, overSold, trailing_stop):

    # インジケーター作成
    vrsi = rsi(ohlc.close, length)

    # エントリー／イグジット
    long_entry = crossover(vrsi, overSold)
    long_exit = crossover(vrsi, overBought)
    short_entry = crossunder(vrsi, overBought)
    short_exit = crossunder(vrsi, overSold)

    long_entry_price = None
    long_exit_price = None
    short_entry_price = None
    short_exit_price = None

    long_entry[:length] = False
    long_exit[:length] = False
    short_entry[:length] = False
    short_exit[:length] = False

    entry_exit = pd.DataFrame({'close':ohlc.close, 'rsi':vrsi, 'long_entry':long_entry, 'long_exit':long_exit, 'short_entry':short_entry, 'short_exit':short_exit})
    entry_exit.to_csv('entry_exit.csv')

    return Backtest(data, buy_entry=long_entry, sell_entry=short_entry, buy_exit=long_exit, sell_exit=short_exit,
        stop_buy_entry=long_entry_price, stop_sell_entry=short_entry_price, stop_buy_exit=long_exit_price, stop_sell_exit=short_exit_price,
        lots=1, spread=0, take_profit=0, stop_loss=0, trailing_stop=trailing_stop, slippage=0)

length = 14
overBought = 78
overSold = 30
trailing_stop = 0

# report = rsi_backtest(data, length, overBought, overSold, trailing_stop)
# print(report)
# report.Raw.Trades.to_csv('trades.csv')
# report.Raw.PL.to_csv('pl.csv')
# report.Equity.to_csv('equity.csv')
# exit()

def objective(args):
    length = int(args['length'])
    overBought = int(args['overBought'])
    overSold = int(args['overSold'])
    #trailing_stop = int(args['trailing_stop'])

    # if overBought <= overSold:
    # 	return 10000

    report = rsi_backtest(data, length, overBought, overSold, trailing_stop)
    print(length, ',', overBought, ',', overSold, ',', trailing_stop, ',', report.ProfitFactor, ',', report.Profit, ',', report.GrossProfit, ',', report.GrossLoss, ',', report.Trades, ',', report.WinTrades, ',', report.LossTrades, ',', report.WinRatio, ',', report.ExpectedValue,)
    return -1 * report.ProfitFactor

# 探索するパラメータ
hyperopt_parameters = {
    'length': hp.quniform('length', 1, 30, 1),
    'overBought': hp.quniform('overBought', 1, 99, 1),
    'overSold': hp.quniform('overSold', 1, 99, 1),
    # 'trailing_stop': hp.quniform('trailing_stop', 0, 99, 1),
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

length = int(best['length']) if 'length' in best else length
overBought = int(best['overBought']) if 'overBought' in best else overBought
overSold = int(best['overSold']) if 'overSold' in best else overSold
trailing_stop = int(best['trailing_stop']) if 'trailing_stop' in best else trailing_stop

report = rsi_backtest(data, length, overBought, overSold, trailing_stop)
print(report)
