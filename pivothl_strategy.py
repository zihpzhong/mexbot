# -*- coding: utf-8 -*-
from strategy import Strategy
from indicator import *
from settings import settings

leftbars = 25
rightbars = 2

def pivot_highlow_strategy(self, ticker, ohlcv, position, balance, strategy):

	# エントリー・エグジット条件作成
    long_entry_price = pivothigh(ohlcv.high, leftbars, rightbars).ffill()
    short_entry_price = pivotlow(ohlcv.low, leftbars, rightbars).ffill()

	# ロット数計算
    qty_lot = int(balance.BTC.free * 0.25 * ticker.last)

    # 注文（ポジションがある場合、ドテンしてくれる）
    entry('L', 'buy', qty=qty_lot, limit=max(long_entry_price, ticker.ask), stop=long_entry_price+0.5)
    entry('S', 'sell', qty=qty_lot, limit=min(short_entry_price, ticker.bid), stop=short_entry_price-0.5)


strategy = Strategy(pivot_highlow_strategy)
strategy.settings.timeframe = '5m'
strategy.settings.interval = 10
strategy.settings.partial_ohlcv = True
# strategy.testnet.use = True
# strategy.testnet.apiKey = ''
# strategy.testnet.secret = ''
strategy.start()
