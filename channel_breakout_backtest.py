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
data = pd.read_csv('bitmex_201804_5m.csv', index_col='timestamp', parse_dates=True)
#print(data.head())

@jit
def channel_breakout_backtest(ohlc, breakout_in, breakout_out):
    # インジケーター作成
    long_entry_price = highest(ohlc.high, breakout_in)
    short_entry_price = lowest(ohlc.low, breakout_in)

    long_exit_price = lowest(ohlc.low, breakout_out)
    short_exit_price = highest(ohlc.high, breakout_out)

    # エントリー／イグジット
    long_entry = ohlc.close > long_entry_price.shift(1)
    short_entry = ohlc.close < short_entry_price.shift(1)
    long_exit = ohlc.close < long_exit_price.shift(1)
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

    return Backtest(data, buy_entry=long_entry, sell_entry=short_entry, buy_exit=long_exit, sell_exit=short_exit, lots=1)


# 参考
# https://qiita.com/kenchin110100/items/ac3edb480d789481f134

def objective(args):
    breakout_in = int(args['breakout_in'])
    breakout_out = int(args['breakout_out'])

    if breakout_in < breakout_out:
        return 10000

    (Trades, PL) = channel_breakout_backtest(data, breakout_in, breakout_out)

    LongPL = PL['Long']
    LongTrades = np.count_nonzero(Trades['Long'])//2
    LongWinTrades = np.count_nonzero(LongPL.clip_lower(0))
    LongLoseTrades = np.count_nonzero(LongPL.clip_upper(0))

    ShortPL = PL['Short']
    ShortTrades = np.count_nonzero(Trades['Short'])//2
    ShortWinTrades = np.count_nonzero(ShortPL.clip_lower(0))
    ShortLoseTrades = np.count_nonzero(ShortPL.clip_upper(0))

    Trades = LongTrades + ShortTrades
    WinTrades = LongWinTrades+ShortWinTrades
    LoseTrades = LongLoseTrades+ShortLoseTrades

    GrossProfit = LongPL.clip_lower(0).sum() + ShortPL.clip_lower(0).sum()
    GrossLoss = LongPL.clip_upper(0).sum() + ShortPL.clip_upper(0).sum()
    ProfitFactor = -(GrossProfit / GrossLoss)

    print(breakout_in, ',', breakout_out, ',', ProfitFactor, ',', GrossProfit+GrossLoss, ',', GrossProfit, ',', GrossLoss, ',', Trades, ',', WinTrades, ',', LoseTrades, ',', WinTrades/Trades)
    return -1 * ProfitFactor

# 探索するパラメータ
hyperopt_parameters = {
    'breakout_in': hp.quniform('breakout_in', 5, 200, 2), # 
    'breakout_out': hp.quniform('breakout_out', 5, 200, 2),
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

(Trades, PL) = channel_breakout_backtest(data, int(best['breakout_in']), int(best['breakout_out']))
Equity = BacktestReport(Trades, PL)
#print(Equity.to_csv())
