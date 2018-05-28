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
    f8[:],f8,
    f8,f8,f8,f8,f8,f8,f8,
    f8[:],f8[:],f8[:],f8[:],f8[:],f8[:]), nopython=True)
def BacktestCore(Open, High, Low, Close, N,
    buy_entry, sell_entry, buy_exit, sell_exit,
    stop_buy_entry, stop_sell_entry, stop_buy_exit, stop_sell_exit,
    lots, max_size,
    spread, take_profit, stop_loss, trailing_stop, slippage, percent, capital,
    LongTrade, LongPL, LongPct, ShortTrade, ShortPL, ShortPct):

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
        if buyExecLot < max_size:
            OpenPrice = 0
            # 成り行き注文
            if buy_entry[i-1]:
                OpenPrice = Open[i]
            # STOP注文
            if stop_buy_entry[i-1] > 0:
                buyStopEntry = stop_buy_entry[i-1]
            if buyStopEntry > 0 and High[i] >= buyStopEntry:
                OpenPrice = buyStopEntry
                buyStopEntry = 0
            # 注文執行
            if OpenPrice > 0:
                execPrice = OpenPrice + spread + slippage
                LongTrade[i] = execPrice #買いポジションオープン
                execLot =  calclots(capital, OpenPrice, percent, lots[i])
                buyExecPrice = ((execPrice*execLot)+(buyExecPrice*buyExecLot))/(buyExecLot+execLot)
                buyExecLot = buyExecLot + execLot
                BuyNow = True

        # 買い手仕舞い
        if buyExecPrice > 0 and not BuyNow:
            ClosePrice = 0
            # 成り行き注文
            if buy_exit[i-1] > 0:
                ClosePrice = Open[i]
            # STOP注文
            if stop_buy_exit[i-1] > 0:
                buyStopExit = stop_buy_exit[i-1]
            if buyStopExit > 0 and Low[i] <= buyStopExit:
                ClosePrice = buyStopExit
                buyStopExit = 0
            # 注文執行
            if ClosePrice > 0:
                ClosePrice = ClosePrice - slippage
                LongTrade[i] = -ClosePrice #買いポジションクローズ
                LongPL[i] = (ClosePrice - buyExecPrice) * buyExecLot #損益確定
                LongPct[i] = LongPL[i] / buyExecPrice
                buyExecPrice = buyExecLot = 0

        # 売り注文処理
        if sellExecLot < max_size:
            OpenPrice = 0
            # 成り行き注文
            if sell_entry[i-1] > 0:
                OpenPrice = Open[i]
            # STOP注文
            if stop_sell_entry[i-1] > 0:
                sellStopEntry = stop_sell_entry[i-1]
            if sellStopEntry > 0 and Low[i] <= sellStopEntry:
                OpenPrice = sellStopEntry
                sellStopEntry = 0
            # 注文執行
            if OpenPrice:
                execPrice = OpenPrice - slippage
                ShortTrade[i] = execPrice #売りポジションオープン
                execLot = calclots(capital, OpenPrice, percent, lots[i])
                sellExecPrice = ((execPrice*execLot)+(sellExecPrice*sellExecLot))/(sellExecLot+execLot)
                sellExecLot = sellExecLot + execLot
                SellNow = True

        # 売り手仕舞い
        if sellExecPrice > 0 and not SellNow:
            ClosePrice = 0
            # 成り行き注文
            if sell_exit[i-1] > 0:
                ClosePrice = Open[i]
            # STOP注文
            if stop_sell_exit[i-1] > 0:
                sellStopExit = stop_sell_exit[i-1]
            if sellStopExit > 0 and High[i] >= sellStopExit:
                ClosePrice = sellStopExit
                sellStopExit = 0
            # 注文執行
            if ClosePrice > 0:
                ClosePrice = ClosePrice + spread + slippage
                ShortTrade[i] = -ClosePrice #売りポジションクローズ
                ShortPL[i] = (sellExecPrice - ClosePrice) * sellExecLot #損益確定
                ShortPct[i] = ShortPL[i] / sellExecPrice
                sellExecPrice = sellExecLot = 0

        # 利確 or 損切によるポジションの決済(エントリーと同じ足で決済しない)
        if buyExecPrice > 0 and not BuyNow:
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
                LongPct[i] = LongPL[i] / buyExecPrice
                buyExecPrice = buyExecLot = 0

        if sellExecPrice > 0 and not SellNow:
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
                ShortPct[i] = ShortPL[i] / sellExecPrice
                sellExecPrice = sellExecLot = 0

        capital = capital + ShortPL[i] + LongPL[i]

    # ポジションクローズ
    if buyExecPrice > 0:
        ClosePrice = Close[N-1]
        LongTrade[N-1] = -ClosePrice #買いポジションクローズ
        LongPL[N-1] = (ClosePrice - buyExecPrice) * buyExecLot #損益確定
        LongPct[N-1] = LongPL[N-1] / buyExecPrice
    if sellExecPrice > 0:
        ClosePrice = Close[N-1]
        ShortTrade[N-1] = -ClosePrice #売りポジションクローズ
        ShortPL[N-1] = (sellExecPrice - ClosePrice) * sellExecLot #損益確定
        ShortPct[N-1] = ShortPL[N-1] / sellExecPrice


def Backtest(ohlcv,
    buy_entry=None, sell_entry=None, buy_exit=None, sell_exit=None,
    stop_buy_entry=None, stop_sell_entry=None, stop_buy_exit=None, stop_sell_exit=None,
    lots=1.0, max_size=1.0, spread=0, take_profit=0, stop_loss=0, trailing_stop=0, slippage=0, percent_of_equity=0.0, initial_capital=0.0, **kwargs):
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

    LongPct = np.zeros(N) # 買いポジションの損益率
    ShortPct = np.zeros(N) # 売りポジションの損益率

    place_holder = np.zeros(N) # プレースホルダ
    bool_place_holder = np.zeros(N, dtype=np.bool) # プレースホルダ
    if isinstance(lots, pd.Series):
        lots = lots.values
    else:
        lots = np.full(shape=(N), fill_value=float(lots))

    buy_entry = bool_place_holder if buy_entry is None else buy_entry.values
    sell_entry = bool_place_holder if sell_entry is None else sell_entry.values
    buy_exit = bool_place_holder if buy_exit is None else buy_exit.values
    sell_exit = bool_place_holder if sell_exit is None else sell_exit.values

    # トレーリングストップ価格を設定(STOP注文として処理する)
    if trailing_stop > 0:
        stop_buy_exit = ohlcv.high - trailing_stop
        stop_sell_exit = ohlcv.low + trailing_stop

    stop_buy_entry = place_holder if stop_buy_entry is None else stop_buy_entry.values
    stop_sell_entry = place_holder if stop_sell_entry is None else stop_sell_entry.values
    stop_buy_exit = place_holder if stop_buy_exit is None else stop_buy_exit.values
    stop_sell_exit = place_holder if stop_sell_exit is None else stop_sell_exit.values

    percent = percent_of_equity
    capital = initial_capital

    BacktestCore(Open, High, Low, Close, N,
        buy_entry, sell_entry, buy_exit, sell_exit,
        stop_buy_entry, stop_sell_entry, stop_buy_exit, stop_sell_exit,
        lots, float(max_size),
        float(spread), float(take_profit), float(stop_loss), float(trailing_stop), float(slippage), float(percent), float(capital),
        LongTrade, LongPL, LongPct, ShortTrade, ShortPL, ShortPct)

    return BacktestReport(pd.DataFrame({
        'LongTrade':LongTrade, 'ShortTrade':ShortTrade,
        'LongPL':LongPL, 'ShortPL':ShortPL,
        'LongPct':LongPct, 'ShortPct':ShortPct,
        }, index=ohlcv.index))


class BacktestReport:
    def __init__(self, DataFrame):
        self.DataFrame = DataFrame

        # ロング統計
        LongPL = DataFrame['LongPL']
        self.Long = dotdict()
        self.Long.PL = LongPL
        self.Long.Pct = DataFrame['LongPct']
        self.Long.Trades = np.count_nonzero(LongPL)
        self.Long.GrossProfit = LongPL.clip_lower(0).sum()
        self.Long.GrossLoss =  LongPL.clip_upper(0).sum()
        self.Long.Profit = self.Long.GrossProfit + self.Long.GrossLoss
        self.Long.Ratio = self.Long.GrossProfit + self.Long.GrossLoss
        self.Long.AvgReturn = self.Long.Pct[self.Long.Pct!=0].mean()
        self.Long.WinTrades = np.count_nonzero(LongPL.clip_lower(0))
        self.Long.WinMax = LongPL.max()
        if self.Long.WinTrades > 0:
            self.Long.WinAverage = self.Long.GrossProfit / self.Long.WinTrades
            self.Long.WinReturn = self.Long.Pct[self.Long.Pct > 0].mean()
            self.Long.WinRatio = self.Long.WinTrades / self.Long.Trades
        else:
            self.Long.WinAverage = 0.0
            self.Long.WinReturn = 0.0
            self.Long.WinRatio = 0.0
        self.Long.LossTrades = np.count_nonzero(LongPL.clip_upper(0))
        self.Long.LossMax = LongPL.min()
        if self.Long.LossTrades > 0:
            self.Long.LossAverage = self.Long.GrossLoss / self.Long.LossTrades
        else:
            self.Long.LossAverage = 0

        # ショート統計
        ShortPL = DataFrame['ShortPL']
        self.Short = dotdict()
        self.Short.PL = ShortPL
        self.Short.Pct = DataFrame['ShortPct']
        self.Short.Trades = np.count_nonzero(ShortPL)
        self.Short.GrossProfit = ShortPL.clip_lower(0).sum()
        self.Short.GrossLoss = ShortPL.clip_upper(0).sum()
        self.Short.Profit = self.Short.GrossProfit + self.Short.GrossLoss
        self.Short.AvgReturn = self.Short.Pct[self.Short.Pct!=0].mean()
        self.Short.WinTrades = np.count_nonzero(ShortPL.clip_lower(0))
        self.Short.WinMax = ShortPL.max()
        if self.Short.WinTrades > 0:
            self.Short.WinAverage = self.Short.GrossProfit / self.Short.WinTrades
            self.Short.WinReturn = self.Short.Pct[self.Short.Pct > 0].mean()
            self.Short.WinRatio = self.Short.WinTrades / self.Short.Trades
        else:
            self.Short.WinAverage = 0.0
            self.Short.WinReturn = 0.0
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
        self.All = dotdict()
        self.All.Trades = self.Long.Trades + self.Short.Trades
        self.All.WinTrades = self.Long.WinTrades + self.Short.WinTrades
        self.All.WinReturn = (self.Long.WinReturn + self.Short.WinReturn) / 2
        self.All.WinRatio = self.All.WinTrades / self.All.Trades if self.All.Trades > 0 else 0.0
        self.All.LossTrades = self.Long.LossTrades + self.Short.LossTrades
        self.All.GrossProfit = self.Long.GrossProfit + self.Short.GrossProfit
        self.All.GrossLoss = self.Long.GrossLoss + self.Short.GrossLoss
        self.All.WinAverage = self.All.GrossProfit / self.All.WinTrades if self.All.WinTrades > 0 else 0
        self.All.LossAverage = self.All.GrossLoss / self.All.LossTrades if self.All.LossTrades > 0 else 0
        self.All.Profit = self.All.GrossProfit + self.All.GrossLoss
        self.All.AvgReturn = (self.Long.AvgReturn + self.Short.AvgReturn) / 2
        self.All.DrawDown = (self.Equity.cummax() - self.Equity).max()
        self.All.ProfitFactor = self.All.GrossProfit / -self.All.GrossLoss if -self.All.GrossLoss > 0 else 0
        pct = pd.concat([self.Long.Pct, self.Short.Pct])
        pct = pct[pct > 0]
        self.All.SharpeRatio = pct.mean() / pct.std()
        self.All.RecoveryFactor = self.All.ProfitFactor / self.All.DrawDown if self.All.DrawDown > 0 else 0
        self.All.ExpectedProfit = (self.All.WinAverage * self.All.WinRatio) + ((1 - self.All.WinRatio) * self.All.LossAverage)
        self.All.ExpectedValue = (self.All.WinRatio * (self.All.WinAverage / abs(self.All.LossAverage))) - (1 - self.All.WinRatio) if self.All.LossAverage < 0 else 1


    def __str__(self):
        return 'Long\n' \
        '  Trades :' + str(self.Long.Trades) + '\n' \
        '  WinTrades :' + str(self.Long.WinTrades) + '\n' \
        '  WinMax :' + str(self.Long.WinMax) + '\n' \
        '  WinAverage :' + str(self.Long.WinAverage) + '\n' \
        '  WinReturn :' + str(self.Long.WinReturn) + '\n' \
        '  WinRatio :' + str(self.Long.WinRatio) + '\n' \
        '  LossTrades :' + str(self.Long.LossTrades) + '\n' \
        '  LossMax :' + str(self.Long.LossMax) + '\n' \
        '  LossAverage :' + str(self.Long.LossAverage) + '\n' \
        '  GrossProfit :' + str(self.Long.GrossProfit) + '\n' \
        '  GrossLoss :' + str(self.Long.GrossLoss) + '\n' \
        '  Profit :' + str(self.Long.Profit) + '\n' \
        '  AvgReturn :' + str(self.Long.AvgReturn) + '\n' \
        '\nShort\n' \
        '  Trades :' + str(self.Short.Trades) + '\n' \
        '  WinTrades :' + str(self.Short.WinTrades) + '\n' \
        '  WinMax :' + str(self.Short.WinMax) + '\n' \
        '  WinAverage :' + str(self.Short.WinAverage) + '\n' \
        '  WinReturn :' + str(self.Short.WinReturn) + '\n' \
        '  WinRatio :' + str(self.Short.WinRatio) + '\n' \
        '  LossTrades :' + str(self.Short.LossTrades) + '\n' \
        '  LossMax :' + str(self.Short.LossMax) + '\n' \
        '  LossAverage :' + str(self.Short.LossAverage) + '\n' \
        '  GrossProfit :' + str(self.Short.GrossProfit) + '\n' \
        '  GrossLoss :' + str(self.Short.GrossLoss) + '\n' \
        '  Profit :' + str(self.Short.Profit) + '\n' \
        '  AvgReturn :' + str(self.Short.AvgReturn) + '\n' \
        '\nAll\n' \
        '  Trades :' + str(self.All.Trades) + '\n' \
        '  WinTrades :' + str(self.All.WinTrades) + '\n' \
        '  WinAverage :' + str(self.All.WinAverage) + '\n' \
        '  WinReturn :' + str(self.All.WinReturn) + '\n' \
        '  WinRatio :' + str(self.All.WinRatio) + '\n' \
        '  LossTrades :' + str(self.All.LossTrades) + '\n' \
        '  LossAverage :' + str(self.All.LossAverage) + '\n' \
        '  GrossProfit :' + str(self.All.GrossProfit) + '\n' \
        '  GrossLoss :' + str(self.All.GrossLoss) + '\n' \
        '  Profit :' + str(self.All.Profit) + '\n' \
        '  AvgReturn :' + str(self.All.AvgReturn) + '\n' \
        '  DrawDown :' + str(self.All.DrawDown) + '\n' \
        '  ProfitFactor :' + str(self.All.ProfitFactor) + '\n' \
        '  SharpeRatio :' + str(self.All.SharpeRatio) + '\n'

# 参考
# https://qiita.com/kenchin110100/items/ac3edb480d789481f134

def BacktestIteration(testfunc, default_parameters, hyperopt_parameters, max_evals, maximize=lambda r:r.All.ProfitFactor):

    needs_header = [True]

    def go(args):
        params = default_parameters.copy()
        params.update(args)
        report = testfunc(**params)
        if 'ohlcv' in params:
            del params['ohlcv']
        params.update(report.All)
        if needs_header[0]:
            print(','.join(params.keys()))
        print(','.join([str(x) for x in params.values()]))
        needs_header[0] = False
        return report

    if max_evals > 0:
        # 試行の過程を記録するインスタンス
        trials = Trials()

        best = fmin(
            # 最小化する値を定義した関数
            lambda args: -1 * maximize(go(args)),
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
    report = go(params)
    print(report)
    return (params, report)


if __name__ == '__main__':

    from utils import stop_watch

    ohlcv = pd.read_csv('csv/bitmex_2018_1m.csv', index_col='timestamp', parse_dates=True)
    long_entry = ohlcv.close > ohlcv.close.shift(1)
    short_entry = ohlcv.close < ohlcv.close.shift(1)
    long_exit = short_entry
    short_exit = long_entry
    Backtest = stop_watch(Backtest)

    Backtest(ohlcv, buy_entry=long_entry, sell_entry=short_entry, buy_exit=long_exit, sell_exit=short_exit, lots=1)
    Backtest(ohlcv, buy_entry=long_entry, sell_entry=short_entry, buy_exit=long_exit, sell_exit=short_exit, lots=1)
    Backtest(ohlcv, buy_entry=long_entry, sell_entry=short_entry, buy_exit=long_exit, sell_exit=short_exit, lots=1)
    Backtest(ohlcv, buy_entry=long_entry, sell_entry=short_entry, buy_exit=long_exit, sell_exit=short_exit, lots=1)
