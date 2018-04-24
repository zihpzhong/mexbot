# -*- coding: utf-8 -*-
import numpy as np
import pandas as pd
from numba import jit
from utils import dotdict

# PythonでFXシストレのバックテスト(1)
# https://qiita.com/toyolab/items/e8292d2f051a88517cb2 より
@jit
def Backtest(ohlc,
    buy_entry=None, sell_entry=None, buy_exit=None, sell_exit=None,
    stop_buy_entry=None, stop_sell_entry=None, stop_buy_exit=None, stop_sell_exit=None,
    lots=0.1, spread=0, take_profit=0, stop_loss=0, trailing_stop=0, slippage=0):
    Open = ohlc.open.values #始値
    Low = ohlc.low.values #安値
    High = ohlc.high.values #高値
    Close = ohlc.close.values #始値

    N = len(ohlc) #データサイズ
    buyExecPrice = sellExecPrice = 0.0 # 売買価格
    buyStopEntry = buyStopExit = sellStopEntry = sellStopExit = 0

    LongTrade = np.zeros(N) # 買いトレード情報
    ShortTrade = np.zeros(N) # 売りトレード情報

    LongPL = np.zeros(N) # 買いポジションの損益
    ShortPL = np.zeros(N) # 売りポジションの損益

    place_holder = np.zeros(N) # プレースホルダ

    buy_entry = place_holder if buy_entry is None else buy_entry.values
    sell_entry = place_holder if sell_entry is None else sell_entry.values
    buy_exit = place_holder if buy_exit is None else buy_exit.values
    sell_exit = place_holder if sell_exit is None else sell_exit.values

    stop_buy_entry = place_holder if stop_buy_entry is None else stop_buy_entry.values
    stop_sell_entry = place_holder if stop_sell_entry is None else stop_sell_entry.values
    stop_buy_exit = place_holder if stop_buy_exit is None else stop_buy_exit.values
    stop_sell_exit = place_holder if stop_sell_exit is None else stop_sell_exit.values

    # トレーリングストップ価格を設定(STOP注文として処理する)
    if trailing_stop > 0:
        stop_buy_exit = ohlc.high - trailing_stop
        stop_sell_exit = ohlc.low + trailing_stop

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
                OpenPrice = buyStopEntry
                buyStopEntry = 0
            # 注文執行
            if OpenPrice > 0:
                buyExecPrice = OpenPrice + spread + slippage
                LongTrade[i] = buyExecPrice #買いポジションオープン
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
                ClosePrice = buyStopExit
                buyStopExit = 0
            # 注文執行
            if ClosePrice > 0:
                ClosePrice = ClosePrice - slippage
                LongTrade[i] = -ClosePrice #買いポジションクローズ
                LongPL[i] = (ClosePrice - buyExecPrice) * lots #損益確定
                buyExecPrice = 0

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
                OpenPrice = sellStopEntry
                sellStopEntry = 0
            # 注文執行
            if OpenPrice:
                sellExecPrice = OpenPrice - slippage
                ShortTrade[i] = sellExecPrice #売りポジションオープン
                SellNow = True
        else:
            ClosePrice = 0
            # 成り行き注文
            if sell_exit[i-1] > 0:
                ClosePrice = Open[i]
            # STOP注文
            if stop_sell_exit[i-1] > 0:
                sellStopExit = stop_sell_exit[i-1]
            if sellStopExit > 0 and High[i] > sellStopExit:
                ClosePrice = sellStopExit
                sellStopExit = 0
            # 注文執行
            if ClosePrice > 0:
                ClosePrice = ClosePrice + spread + slippage
                ShortTrade[i] = -ClosePrice #売りポジションクローズ
                ShortPL[i] = (sellExecPrice - ClosePrice) * lots #損益確定
                sellExecPrice = 0

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
                LongPL[i] = (ClosePrice - buyExecPrice) * lots #損益確定
                buyExecPrice = 0

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
                ShortPL[i] = (sellExecPrice - ClosePrice) * lots #損益確定
                sellExecPrice = 0

    # ポジションクローズ
    if buyExecPrice > 0:
        ClosePrice = Close[N-1]
        LongTrade[N-1] = -ClosePrice #買いポジションクローズ
        LongPL[N-1] = (ClosePrice - buyExecPrice) * lots #損益確定
    if sellExecPrice > 0:
        ClosePrice = Close[N-1]
        ShortTrade[N-1] = -ClosePrice #売りポジションクローズ
        ShortPL[N-1] = (sellExecPrice - ClosePrice) * lots #損益確定

    return BacktestReport(
        Trades=pd.DataFrame({'Long':LongTrade, 'Short':ShortTrade}, index=ohlc.index),
        PL=pd.DataFrame({'Long':LongPL, 'Short':ShortPL}, index=ohlc.index))


class BacktestReport:
    def __init__(self, Trades, PL):
        self.Raw = dotdict()
        self.Raw.Trades = Trades
        self.Raw.PL = PL

        self.Long = dotdict()
        self.Short = dotdict()

        # ロング統計
        LongPL = PL['Long']
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

        # 全体統計
        self.Trades = self.Long.Trades + self.Short.Trades
        self.WinTrades = self.Long.WinTrades + self.Short.WinTrades
        self.WinRatio = self.WinTrades / self.Trades if self.Trades > 0 else 0.0
        self.LossTrades = self.Long.LossTrades + self.Short.LossTrades
        self.GrossProfit = self.Long.GrossProfit + self.Short.GrossProfit
        self.GrossLoss = self.Long.GrossLoss + self.Short.GrossLoss
        self.WinAverage = self.GrossProfit / self.WinTrades if self.WinTrades > 0 else 0
        self.LossAverage = self.GrossLoss / self.LossTrades if self.LossTrades > 0 else 0
        self.Profit = self.GrossProfit + self.GrossLoss
        self.Equity = (LongPL + ShortPL).cumsum()
        self.DrawDown = (self.Equity.cummax() - self.Equity).max()
        self.ProfitFactor = self.GrossProfit / -self.GrossLoss if -self.GrossLoss > 0 else self.GrossProfit
        self.RecoveryFactor = self.ProfitFactor / self.DrawDown if self.DrawDown > 0 else self.ProfitFactor
        self.ExpectedProfit = (self.WinAverage * self.WinRatio) + ((1 - self.WinRatio) * self.LossAverage)
        self.ExpectedValue = (self.WinRatio * (self.WinAverage / abs(self.LossAverage))) - (1 - self.WinRatio) if self.LossAverage < 0 else 1

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
        '  Trades :' + str(self.Trades) + '\n' \
        '  WinTrades :' + str(self.WinTrades) + '\n' \
        '  WinAverage :' + str(self.WinAverage) + '\n' \
        '  WinRatio :' + str(self.WinRatio) + '\n' \
        '  LossTrades :' + str(self.LossTrades) + '\n' \
        '  LossAverage :' + str(self.LossAverage) + '\n' \
        '  GrossProfit :' + str(self.GrossProfit) + '\n' \
        '  GrossLoss :' + str(self.GrossLoss) + '\n' \
        '  Profit :' + str(self.Profit) + '\n' \
        '  DrawDown :' + str(self.DrawDown) + '\n' \
        '  ProfitFactor :' + str(self.ProfitFactor) + '\n' \
        '  RecoveryFactor :' + str(self.RecoveryFactor) + '\n' \
        '  ExpectedProfit :' + str(self.ExpectedProfit) + '\n' \
        '  ExpectedValue :' + str(self.ExpectedValue) + '\n'
