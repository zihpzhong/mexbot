# -*- coding: utf-8 -*-
import numpy as np
import pandas as pd
from numba import jit

# PythonでFXシストレのバックテスト(1)
# https://qiita.com/toyolab/items/e8292d2f051a88517cb2 より
@jit
def Backtest(ohlc, buy_entry, sell_entry, buy_exit, sell_exit, lots=0.1, spread=2, fee=0):
    Open = ohlc['open'].values #始値
    N = len(ohlc) #データサイズ
    buy_exit[N-2] = sell_exit[N-2] = True #最後に強制エグジット
    BuyPrice = SellPrice = 0.0 # 売買価格

    LongTrade = np.zeros(N) # 買いトレード情報
    ShortTrade = np.zeros(N) # 売りトレード情報

    LongPL = np.zeros(N) # 買いポジションの損益
    ShortPL = np.zeros(N) # 売りポジションの損益

    for i in range(1, N):
        if buy_entry[i-1] and BuyPrice == 0: #買いエントリーシグナル
            BuyPrice = Open[i] + spread
            LongTrade[i] = BuyPrice #買いポジションオープン
        elif buy_exit[i-1] and BuyPrice != 0: #買いエグジットシグナル
            ClosePrice = Open[i]
            LongTrade[i] = -ClosePrice #買いポジションクローズ
            LongPL[i] = (ClosePrice - BuyPrice) * lots #損益確定
            BuyPrice = 0

        if sell_entry[i-1] and SellPrice == 0: #売りエントリーシグナル
            SellPrice = Open[i]
            ShortTrade[i] = SellPrice #売りポジションオープン
        elif sell_exit[i-1] and SellPrice != 0: #売りエグジットシグナル
            ClosePrice = Open[i] + spread
            ShortTrade[i] = -ClosePrice #売りポジションクローズ
            ShortPL[i] = (SellPrice - ClosePrice) * lots #損益確定
            SellPrice = 0

    return pd.DataFrame({'Long':LongTrade, 'Short':ShortTrade}, index=ohlc.index),\
            pd.DataFrame({'Long':LongPL, 'Short':ShortPL}, index=ohlc.index)


def BacktestReport(Trade, PL):
    LongPL = PL['Long']
    LongTrades = np.count_nonzero(Trade['Long'])//2
    LongWinTrades = np.count_nonzero(LongPL.clip_lower(0))
    LongLoseTrades = np.count_nonzero(LongPL.clip_upper(0))
    print('買いトレード数 =', LongTrades)
    print('勝トレード数 =', LongWinTrades)
    print('最大勝トレード =', LongPL.max())
    print('平均勝トレード =', round(LongPL.clip_lower(0).sum()/LongWinTrades if LongWinTrades else 0, 2))
    print('負トレード数 =', LongLoseTrades)
    print('最大負トレード =', LongPL.min())
    print('平均負トレード =', round(LongPL.clip_upper(0).sum()/LongLoseTrades if LongLoseTrades else 0, 2))
    print('勝率 =', round(LongWinTrades/LongTrades*100, 2) if LongTrades else 0, '%\n')

    ShortPL = PL['Short']
    ShortTrades = np.count_nonzero(Trade['Short'])//2
    ShortWinTrades = np.count_nonzero(ShortPL.clip_lower(0))
    ShortLoseTrades = np.count_nonzero(ShortPL.clip_upper(0))
    print('売りトレード数 =', ShortTrades)
    print('勝トレード数 =', ShortWinTrades)
    print('最大勝トレード =', ShortPL.max())
    print('平均勝トレード =', round(ShortPL.clip_lower(0).sum()/ShortWinTrades, 2) if ShortWinTrades else 0)
    print('負トレード数 =', ShortLoseTrades)
    print('最大負トレード =', ShortPL.min())
    print('平均負トレード =', round(ShortPL.clip_upper(0).sum()/ShortLoseTrades, 2) if ShortLoseTrades else 0)
    print('勝率 =', round(ShortWinTrades/ShortTrades*100, 2) if ShortTrades else 0, '%\n')

    Trades = LongTrades + ShortTrades
    WinTrades = LongWinTrades+ShortWinTrades
    LoseTrades = LongLoseTrades+ShortLoseTrades
    print('総トレード数 =', Trades)
    print('勝トレード数 =', WinTrades)
    print('最大勝トレード =', max(LongPL.max(), ShortPL.max()))
    print('平均勝トレード =', round((LongPL.clip_lower(0).sum()+ShortPL.clip_lower(0).sum())/WinTrades if WinTrades else 0, 2))
    print('負トレード数 =', LoseTrades)
    print('最大負トレード =', min(LongPL.min(), ShortPL.min()))
    print('平均負トレード =', round((LongPL.clip_upper(0).sum()+ShortPL.clip_upper(0).sum())/LoseTrades if LoseTrades else 0, 2))
    print('勝率 =', round(WinTrades/Trades*100, 2) if Trades else 0, '%\n')

    GrossProfit = LongPL.clip_lower(0).sum()+ShortPL.clip_lower(0).sum()
    GrossLoss = LongPL.clip_upper(0).sum()+ShortPL.clip_upper(0).sum()
    Profit = GrossProfit+GrossLoss
    Equity = (LongPL+ShortPL).cumsum()
    MDD = (Equity.cummax()-Equity).max()
    print('総利益 =', round(GrossProfit, 2))
    print('総損失 =', round(GrossLoss, 2))
    print('総損益 =', round(Profit, 2))
    print('プロフィットファクター =', round(-GrossProfit/GrossLoss, 2))
    print('平均損益 =', round(Profit/Trades, 2))
    print('最大ドローダウン =', round(MDD, 2))
    print('リカバリーファクター =', round(Profit/MDD, 2))
    return Equity
