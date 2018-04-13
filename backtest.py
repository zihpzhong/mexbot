# -*- coding: utf-8 -*-
import numpy as np
import pandas as pd
from numba import jit
from utils import dotdict

# PythonでFXシストレのバックテスト(1)
# https://qiita.com/toyolab/items/e8292d2f051a88517cb2 より
@jit
def Backtest(ohlc, buy_entry, sell_entry, buy_exit, sell_exit, lots=0.1, spread=0, take_profit=0, stop_loss=0):
    Open = ohlc.open.values #始値
    Low = ohlc.low.values #安値
    High = ohlc.high.values #高値
    Close = ohlc.close.values #始値

    buy_entry = buy_entry.values
    sell_entry = sell_entry.values
    buy_exit = buy_exit.values
    sell_exit = sell_exit.values

    N = len(ohlc) #データサイズ
    buy_exit[N-2] = sell_exit[N-2] = True #最後に強制エグジット
    BuyPrice = SellPrice = 0.0 # 売買価格

    LongTrade = np.zeros(N) # 買いトレード情報
    ShortTrade = np.zeros(N) # 売りトレード情報

    LongPL = np.zeros(N) # 買いポジションの損益
    ShortPL = np.zeros(N) # 売りポジションの損益

    #
    # シグナルが出た次の足の始値で成行売買を行う
    #
    for i in range(1, N):
        # エントリー／イグジット
        if buy_entry[i-1] and BuyPrice == 0: #買いエントリーシグナル
            BuyPrice = Open[i] + spread
            LongTrade[i] = BuyPrice #買いポジションオープン

        if buy_exit[i-1] and BuyPrice != 0: #買いエグジットシグナル
            ClosePrice = Open[i]
            LongTrade[i] = -ClosePrice #買いポジションクローズ
            LongPL[i] = (ClosePrice - BuyPrice) * lots #損益確定
            BuyPrice = 0

        if sell_entry[i-1] and SellPrice == 0: #売りエントリーシグナル
            SellPrice = Open[i]
            ShortTrade[i] = SellPrice #売りポジションオープン

        if sell_exit[i-1] and SellPrice != 0: #売りエグジットシグナル
            ClosePrice = Open[i] + spread
            ShortTrade[i] = -ClosePrice #売りポジションクローズ
            ShortPL[i] = (SellPrice - ClosePrice) * lots #損益確定
            SellPrice = 0

        # 利確 or 損切によるポジションの決済
        if BuyPrice != 0:
            ClosePrice = 0
            if stop_loss > 0:
                # 損切判定 Open -> Low
                StopPrice = BuyPrice - stop_loss
                if Open[i] <= StopPrice:
                    ClosePrice = Open[i]
                elif Low[i] <= StopPrice:
                    ClosePrice = Low[i]
            elif take_profit > 0:
                # 利確判定
                LimitPrice = BuyPrice + take_profit
                if High[i] >= LimitPrice:
                    ClosePrice = LimitPrice
            if ClosePrice > 0:
                LongTrade[i] = -ClosePrice #買いポジションクローズ
                LongPL[i] = (ClosePrice - BuyPrice) * lots #損益確定
                BuyPrice = 0

        if SellPrice != 0:
            ClosePrice = 0
            if stop_loss > 0:
                # 損切判定 Open -> High
                StopPrice = SellPrice + stop_loss
                if Open[i] >= StopPrice:
                    ClosePrice = Open[i]
                elif High[i] >= StopPrice:
                    ClosePrice = High[i]
            elif take_profit > 0:
                # 利確判定
                LimitPrice = SellPrice - take_profit
                if Low[i] <= LimitPrice:
                    ClosePrice = LimitPrice
            if ClosePrice > 0:
                ShortTrade[i] = -ClosePrice #売りポジションクローズ
                ShortPL[i] = (SellPrice - ClosePrice) * lots #損益確定
                SellPrice = 0


    return BacktestReport(
        Trades=pd.DataFrame({'Long':LongTrade, 'Short':ShortTrade}, index=ohlc.index),
        PL=pd.DataFrame({'Long':LongPL, 'Short':ShortPL}, index=ohlc.index))


class BacktestReport:
    def __init__(self, Trades, PL):
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

        # 全体統計
        self.Trades = self.Long.Trades + self.Short.Trades
        self.WinTrades = self.Long.WinTrades + self.Short.WinTrades
        self.WinRatio = self.WinTrades / self.Trades if self.Trades > 0 else 0.0
        self.LossTrades = self.Long.LossTrades + self.Short.LossTrades
        self.GrossProfit = self.Long.GrossProfit + self.Short.GrossProfit
        self.GrossLoss = self.Long.GrossLoss + self.Short.GrossLoss
        self.Profit = self.GrossProfit + self.GrossLoss
        self.Equity = (LongPL + ShortPL).cumsum()
        self.DrawDown = (self.Equity.cummax() - self.Equity).max()
        self.ProfitFactor = self.GrossProfit / -self.GrossLoss if -self.GrossLoss > 0 else 0.0
        self.RecoveryFactor = self.ProfitFactor / self.DrawDown if self.DrawDown > 0 else 0.0

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
        '  WinRatio :' + str(self.WinRatio) + '\n' \
        '  LossTrades :' + str(self.LossTrades) + '\n' \
        '  GrossProfit :' + str(self.GrossProfit) + '\n' \
        '  GrossLoss :' + str(self.GrossLoss) + '\n' \
        '  Profit :' + str(self.Profit) + '\n' \
        '  DrawDown :' + str(self.DrawDown) + '\n' \
        '  ProfitFactor :' + str(self.ProfitFactor) + '\n' \
        '  RecoveryFactor :' + str(self.RecoveryFactor) + '\n'
