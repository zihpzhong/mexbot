# -*- coding: utf-8 -*-
import numpy as np
import pandas as pd
from numba import jit, b1, f8, i8, void
from utils import dotdict
from hyperopt import hp, tpe, Trials, fmin, rand, anneal

# PythonでFXシストレのバックテスト(1)
# https://qiita.com/toyolab/items/e8292d2f051a88517cb2 より

@jit(f8(f8,f8,f8,f8),nopython=True)
def calclots(capital, price, percent, lot):
    if percent > 0:
        if capital > 0:
            return ((capital * percent) / price)
        else:
            return 0
    else:
        return lot

@jit(void(f8[:],f8[:],f8[:],f8[:],i8,
    b1[:],b1[:],b1[:],b1[:],
    f8[:],f8[:],f8[:],f8[:],
    f8[:],
    f8,f8,f8,f8,f8,f8,f8,
    f8[:],f8[:],f8[:],f8[:]), nopython=True)
def BacktestCore(Open, High, Low, Close, N,
    buy_entry, sell_entry, buy_exit, sell_exit,
    stop_buy_entry, stop_sell_entry, stop_buy_exit, stop_sell_exit,
    lots,
    spread, take_profit, stop_loss, trailing_stop, slippage, percent, capital,
    LongTrade, LongPL, ShortTrade, ShortPL):

    buyExecPrice = sellExecPrice = 0.0 # 売買価格
    buyStopEntry = buyStopExit = sellStopEntry = sellStopExit = 0
    buyExecLot = sellExecLot = 0

    #
    # 1.シグナルが出た次の足の始値で成行
    # 2.1.ストップ注文がでたら次の足でトリガー値で注文
    # 2.2.買い注文の場合、High > トリガーで約定
    #     売り注文の場合、Low < トリガーで約定
    #
    for i in range(1, N):
        BuyNow = SellNow = False

        # 買い注文処理
        if buyExecPrice == 0:
            OpenPrice = 0
            # 成り行き注文
            if buy_entry[i-1]:
                OpenPrice = Open[i]
            # STOP注文
            if stop_buy_entry[i-1] > 0:
                buyStopEntry = stop_buy_entry[i-1]
            if buyStopEntry > 0 and High[i] >= buyStopEntry:
                if Open[i] <= buyStopEntry:
                    OpenPrice = buyStopEntry
                else:
                    OpenPrice = Open[i]
                buyStopEntry = 0
            # 注文執行
            if OpenPrice > 0:
                buyExecPrice = OpenPrice + spread + slippage
                LongTrade[i] = buyExecPrice #買いポジションオープン
                buyExecLot =  calclots(capital, OpenPrice, percent, lots[i])
                BuyNow = True
        else:
            ClosePrice = 0
            # 成り行き注文
            if buy_exit[i-1] > 0:
                ClosePrice = Open[i]
            # STOP注文
            if stop_buy_exit[i-1] > 0:
                buyStopExit = stop_buy_exit[i-1]
            if buyStopExit > 0 and Low[i] <= buyStopExit:
                if Open[i] >= buyStopExit:
                    ClosePrice = buyStopExit
                else:
                    ClosePrice = Open[i]
                buyStopExit = 0
            # 注文執行
            if ClosePrice > 0:
                ClosePrice = ClosePrice - slippage
                LongTrade[i] = -ClosePrice #買いポジションクローズ
                LongPL[i] = (ClosePrice - buyExecPrice) * buyExecLot #損益確定
                buyExecPrice = buyExecLot = 0

        # 売り注文処理
        if sellExecPrice == 0:
            OpenPrice = 0
            # 成り行き注文
            if sell_entry[i-1] > 0:
                OpenPrice = Open[i]
            # STOP注文
            if stop_sell_entry[i-1] > 0:
                sellStopEntry = stop_sell_entry[i-1]
            if sellStopEntry > 0 and Low[i] <= sellStopEntry:
                if Open[i] >= sellStopEntry:
                    OpenPrice = sellStopEntry
                else:
                    OpenPrice = Open[i]
                sellStopEntry = 0
            # 注文執行
            if OpenPrice:
                sellExecPrice = OpenPrice - slippage
                ShortTrade[i] = sellExecPrice #売りポジションオープン
                sellExecLot = calclots(capital, OpenPrice, percent, lots[i])
                SellNow = True
        else:
            ClosePrice = 0
            # 成り行き注文
            if sell_exit[i-1] > 0:
                ClosePrice = Open[i]
            # STOP注文
            if stop_sell_exit[i-1] > 0:
                sellStopExit = stop_sell_exit[i-1]
            if sellStopExit > 0 and High[i] >= sellStopExit:
                if Open[i] <= sellStopExit:
                    ClosePrice = sellStopExit
                else:
                    ClosePrice = Open[i]
                sellStopExit = 0
            # 注文執行
            if ClosePrice > 0:
                ClosePrice = ClosePrice + spread + slippage
                ShortTrade[i] = -ClosePrice #売りポジションクローズ
                ShortPL[i] = (sellExecPrice - ClosePrice) * sellExecLot #損益確定
                sellExecPrice = sellExecLot = 0

        # 利確 or 損切によるポジションの決済(エントリーと同じ足で決済しない)
        if buyExecPrice != 0 and not BuyNow:
            ClosePrice = 0
            if stop_loss > 0:
                # 損切判定 Open -> Low
                StopPrice = buyExecPrice - stop_loss
                if Low[i] <= StopPrice:
                    ClosePrice = StopPrice - slippage
            elif take_profit > 0:
                # 利確判定
                LimitPrice = buyExecPrice + take_profit
                if High[i] >= LimitPrice:
                    ClosePrice = LimitPrice - slippage
            if ClosePrice > 0:
                LongTrade[i] = -ClosePrice #買いポジションクローズ
                LongPL[i] = (ClosePrice - buyExecPrice) * buyExecLot #損益確定
                buyExecPrice = buyExecLot = 0

        if sellExecPrice != 0 and not SellNow:
            ClosePrice = 0
            if stop_loss > 0:
                # 損切判定 Open -> High
                StopPrice = sellExecPrice + stop_loss
                if High[i] >= StopPrice:
                    ClosePrice = StopPrice + slippage
            elif take_profit > 0:
                # 利確判定
                LimitPrice = sellExecPrice - take_profit
                if Low[i] <= LimitPrice:
                    ClosePrice = LimitPrice + slippage
            if ClosePrice > 0:
                ShortTrade[i] = -ClosePrice #売りポジションクローズ
                ShortPL[i] = (sellExecPrice - ClosePrice) * sellExecLot #損益確定
                sellExecPrice = sellExecLot = 0

        capital = capital + ShortPL[i] + LongPL[i]

    # ポジションクローズ
    if buyExecPrice > 0:
        ClosePrice = Close[N-1]
        LongTrade[N-1] = -ClosePrice #買いポジションクローズ
        LongPL[N-1] = (ClosePrice - buyExecPrice) * buyExecLot #損益確定
    if sellExecPrice > 0:
        ClosePrice = Close[N-1]
        ShortTrade[N-1] = -ClosePrice #売りポジションクローズ
        ShortPL[N-1] = (sellExecPrice - ClosePrice) * sellExecLot #損益確定


def Backtest(ohlcv,
    buy_entry=None, sell_entry=None, buy_exit=None, sell_exit=None,
    stop_buy_entry=None, stop_sell_entry=None, stop_buy_exit=None, stop_sell_exit=None,
    lots=0.1, spread=0, take_profit=0, stop_loss=0, trailing_stop=0, slippage=0, percent_of_equity=(0.0, 0.0)):
    Open = ohlcv.open.values #始値
    Low = ohlcv.low.values #安値
    High = ohlcv.high.values #高値
    Close = ohlcv.close.values #始値

    N = len(ohlcv) #データサイズ
    buyExecPrice = sellExecPrice = 0.0 # 売買価格
    buyStopEntry = buyStopExit = sellStopEntry = sellStopExit = 0
    buyExecLot = sellExecLot = 0

    LongTrade = np.zeros(N) # 買いトレード情報
    ShortTrade = np.zeros(N) # 売りトレード情報

    LongPL = np.zeros(N) # 買いポジションの損益
    ShortPL = np.zeros(N) # 売りポジションの損益

    place_holder = np.zeros(N) # プレースホルダ
    if isinstance(lots, pd.Series):
        lots = lots.values
    else:
        lots = np.full(shape=(N), fill_value=float(lots))

    buy_entry = place_holder if buy_entry is None else buy_entry.values
    sell_entry = place_holder if sell_entry is None else sell_entry.values
    buy_exit = place_holder if buy_exit is None else buy_exit.values
    sell_exit = place_holder if sell_exit is None else sell_exit.values

    # トレーリングストップ価格を設定(STOP注文として処理する)
    if trailing_stop > 0:
        stop_buy_exit = ohlcv.high - trailing_stop
        stop_sell_exit = ohlcv.low + trailing_stop

    stop_buy_entry = place_holder if stop_buy_entry is None else stop_buy_entry.values
    stop_sell_entry = place_holder if stop_sell_entry is None else stop_sell_entry.values
    stop_buy_exit = place_holder if stop_buy_exit is None else stop_buy_exit.values
    stop_sell_exit = place_holder if stop_sell_exit is None else stop_sell_exit.values

    percent = percent_of_equity[0]
    capital = percent_of_equity[1]

    BacktestCore(Open, High, Low, Close, N,
        buy_entry, sell_entry, buy_exit, sell_exit,
        stop_buy_entry, stop_sell_entry, stop_buy_exit, stop_sell_exit,
        lots,
        float(spread), float(take_profit), float(stop_loss), float(trailing_stop), float(slippage), float(percent), float(capital),
        LongTrade, LongPL, ShortTrade, ShortPL)

    return BacktestReport(
        Trades=pd.DataFrame({'Long':LongTrade, 'Short':ShortTrade}, index=ohlcv.index),
        PL=pd.DataFrame({'Long':LongPL, 'Short':ShortPL}, index=ohlcv.index))


class BacktestReport:
    def __init__(self, Trades, PL):
        self.Raw = dotdict()
        self.Raw.Trades = Trades
        self.Raw.PL = PL

        # ロング統計
        LongPL = PL['Long']
        self.Long = dotdict()
        self.Long.Trades = np.count_nonzero(LongPL)
        self.Long.GrossProfit = LongPL.clip_lower(0).sum()
        self.Long.GrossLoss =  LongPL.clip_upper(0).sum()
        self.Long.Profit = self.Long.GrossProfit + self.Long.GrossLoss
        self.Long.WinTrades = np.count_nonzero(LongPL.clip_lower(0))
        self.Long.WinMax = LongPL.max()
        if self.Long.WinTrades > 0:
            self.Long.WinAverage = self.Long.GrossProfit / self.Long.WinTrades
            self.Long.WinRatio = self.Long.WinTrades / self.Long.Trades
        else:
            self.Long.WinAverage = 0.0
            self.Long.WinRatio = 0.0
        self.Long.LossTrades = np.count_nonzero(LongPL.clip_upper(0))
        self.Long.LossMax = LongPL.min()
        if self.Long.LossTrades > 0:
            self.Long.LossAverage = self.Long.GrossLoss / self.Long.LossTrades
        else:
            self.Long.LossAverage = 0

        # ショート統計
        ShortPL = PL['Short']
        self.Short = dotdict()
        self.Short.Trades = np.count_nonzero(ShortPL)
        self.Short.GrossProfit = ShortPL.clip_lower(0).sum()
        self.Short.GrossLoss = ShortPL.clip_upper(0).sum()
        self.Short.Profit = self.Short.GrossProfit + self.Short.GrossLoss
        self.Short.WinTrades = np.count_nonzero(ShortPL.clip_lower(0))
        self.Short.WinMax = ShortPL.max()
        if self.Short.WinTrades > 0:
            self.Short.WinAverage = self.Short.GrossProfit / self.Short.WinTrades
            self.Short.WinRatio = self.Short.WinTrades / self.Short.Trades
        else:
            self.Short.WinAverage = 0.0
            self.Short.WinRatio = 0.0
        self.Short.LossTrades = np.count_nonzero(ShortPL.clip_upper(0))
        self.Short.LossMax = ShortPL.min()
        if self.Short.LossTrades > 0:
            self.Short.LossAverage = self.Short.GrossLoss / self.Short.LossTrades
        else:
            self.Short.LossTrades = 0

        # 資産
        self.Equity = (LongPL + ShortPL).cumsum()

        # 全体統計
        self.Total = dotdict()
        self.Total.Trades = self.Long.Trades + self.Short.Trades
        self.Total.WinTrades = self.Long.WinTrades + self.Short.WinTrades
        self.Total.WinRatio = self.Total.WinTrades / self.Total.Trades if self.Total.Trades > 0 else 0.0
        self.Total.LossTrades = self.Long.LossTrades + self.Short.LossTrades
        self.Total.GrossProfit = self.Long.GrossProfit + self.Short.GrossProfit
        self.Total.GrossLoss = self.Long.GrossLoss + self.Short.GrossLoss
        self.Total.WinAverage = self.Total.GrossProfit / self.Total.WinTrades if self.Total.WinTrades > 0 else 0
        self.Total.LossAverage = self.Total.GrossLoss / self.Total.LossTrades if self.Total.LossTrades > 0 else 0
        self.Total.Profit = self.Total.GrossProfit + self.Total.GrossLoss
        self.Total.DrawDown = (self.Equity.cummax() - self.Equity).max()
        self.Total.ProfitFactor = self.Total.GrossProfit / -self.Total.GrossLoss if -self.Total.GrossLoss > 0 else 0
        self.Total.RecoveryFactor = self.Total.ProfitFactor / self.Total.DrawDown if self.Total.DrawDown > 0 else 0
        self.Total.ExpectedProfit = (self.Total.WinAverage * self.Total.WinRatio) + ((1 - self.Total.WinRatio) * self.Total.LossAverage)
        self.Total.ExpectedValue = (self.Total.WinRatio * (self.Total.WinAverage / abs(self.Total.LossAverage))) - (1 - self.Total.WinRatio) if self.Total.LossAverage < 0 else 1

    # def to_csv(self, header=False)
    #     csv = ''
    #     if header:
    #         total_header = self.Total.keys()
    #         long_header = self.Long.keys()
    #         short_header = self.Short.keys()
    #         csv = csv +       ','.join(total_header)
    #         csv = csv + ',' + ','.join(long_header)
    #         csv = csv + ',' + ','.join(short_header)
    #         csv = csv + '\n'
    #     total_values = [str(x) for x in self.Total.values()]
    #     long_values = [str(x) for x in self.Long.values()]
    #     short_values = [str(x) for x in self.Short.values()]
    #     csv = csv +       ','.join(total_values)
    #     csv = csv + ',' + ','.join(long_values)
    #     csv = csv + ',' + ','.join(short_values)
    #     return csv

    def __str__(self):
        return 'Long\n' \
        '  Trades :' + str(self.Long.Trades) + '\n' \
        '  WinTrades :' + str(self.Long.WinTrades) + '\n' \
        '  WinMax :' + str(self.Long.WinMax) + '\n' \
        '  WinAverage :' + str(self.Long.WinAverage) + '\n' \
        '  WinRatio :' + str(self.Long.WinRatio) + '\n' \
        '  LossTrades :' + str(self.Long.LossTrades) + '\n' \
        '  LossMax :' + str(self.Long.LossMax) + '\n' \
        '  LossAverage :' + str(self.Long.LossAverage) + '\n' \
        '  GrossProfit :' + str(self.Long.GrossProfit) + '\n' \
        '  GrossLoss :' + str(self.Long.GrossLoss) + '\n' \
        '  Profit :' + str(self.Long.Profit) + '\n' \
        '\nShort\n' \
        '  Trades :' + str(self.Short.Trades) + '\n' \
        '  WinTrades :' + str(self.Short.WinTrades) + '\n' \
        '  WinMax :' + str(self.Short.WinMax) + '\n' \
        '  WinAverage :' + str(self.Short.WinAverage) + '\n' \
        '  WinRatio :' + str(self.Short.WinRatio) + '\n' \
        '  LossTrades :' + str(self.Short.LossTrades) + '\n' \
        '  LossMax :' + str(self.Short.LossMax) + '\n' \
        '  LossAverage :' + str(self.Short.LossAverage) + '\n' \
        '  GrossProfit :' + str(self.Short.GrossProfit) + '\n' \
        '  GrossLoss :' + str(self.Short.GrossLoss) + '\n' \
        '  Profit :' + str(self.Short.Profit) + '\n' \
        '\nTotal\n' \
        '  Trades :' + str(self.Total.Trades) + '\n' \
        '  WinTrades :' + str(self.Total.WinTrades) + '\n' \
        '  WinAverage :' + str(self.Total.WinAverage) + '\n' \
        '  WinRatio :' + str(self.Total.WinRatio) + '\n' \
        '  LossTrades :' + str(self.Total.LossTrades) + '\n' \
        '  LossAverage :' + str(self.Total.LossAverage) + '\n' \
        '  GrossProfit :' + str(self.Total.GrossProfit) + '\n' \
        '  GrossLoss :' + str(self.Total.GrossLoss) + '\n' \
        '  Profit :' + str(self.Total.Profit) + '\n' \
        '  DrawDown :' + str(self.Total.DrawDown) + '\n' \
        '  ProfitFactor :' + str(self.Total.ProfitFactor) + '\n' \
        '  RecoveryFactor :' + str(self.Total.RecoveryFactor) + '\n' \
        '  ExpectedProfit :' + str(self.Total.ExpectedProfit) + '\n' \
        '  ExpectedValue :' + str(self.Total.ExpectedValue) + '\n'

# 参考
# https://qiita.com/kenchin110100/items/ac3edb480d789481f134

def BacktestIteration(testfunc, default_parameters, hyperopt_parameters, max_evals):

    needs_header = [True]

    def objective(args):
        params = default_parameters.copy()
        params.update(args)
        report = testfunc(**params)
        params.update(report.Total)
        if needs_header[0]:
            print(','.join(params.keys()))
        values = [str(x) for x in params.values()]
        print(','.join(values))
        needs_header[0] = False
        return -1 * report.Total.ProfitFactor

    # 試行の過程を記録するインスタンス
    trials = Trials()

    if max_evals > 0:
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
    else:
        best = default_parameters

    params = default_parameters.copy()
    params.update(best)
    report = testfunc(**params)
    params.update(report.Total)
    values = [str(x) for x in params.values()]
    print(','.join(values))

    report.Raw.Trades.to_csv('trades.csv')
    report.Raw.PL.to_csv('pl.csv')
    report.Equity.to_csv('equity.csv')
    print(report)

if __name__ == '__main__':

    from utils import stop_watch

    ohlcv = pd.read_csv('csv/bitmex_2018_1h.csv', index_col='timestamp', parse_dates=True)
    long_entry = ohlcv.close > ohlcv.close.shift(1)
    short_entry = ohlcv.close < ohlcv.close.shift(1)
    long_exit = short_entry
    short_exit = long_entry
    Backtest = stop_watch(Backtest)

    Backtest(ohlcv, buy_entry=long_entry, sell_entry=short_entry, buy_exit=long_exit, sell_exit=short_exit, lots=1)
    Backtest(ohlcv, buy_entry=long_entry, sell_entry=short_entry, buy_exit=long_exit, sell_exit=short_exit, lots=1)
    Backtest(ohlcv, buy_entry=long_entry, sell_entry=short_entry, buy_exit=long_exit, sell_exit=short_exit, lots=1)
    Backtest(ohlcv, buy_entry=long_entry, sell_entry=short_entry, buy_exit=long_exit, sell_exit=short_exit, lots=1)
