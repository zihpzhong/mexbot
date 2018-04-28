# -*- coding: utf-8 -*-
from strategy import Strategy
from indicator import *
from settings import settings
import logging
import logging.config

leftbars = 1
rightbars = 0

logging.config.fileConfig("logging.conf")

def pivot_highlow_strategy(ticker, ohlcv, position, balance, strategy):

	# エントリー・エグジット条件作成
    long_entry_price = last(pivothigh(ohlcv.high, leftbars, rightbars).ffill())
    short_entry_price = last(pivotlow(ohlcv.low, leftbars, rightbars).ffill())

	# ロット数計算
    qty_lot = int(balance.BTC.free * 0.1 * ticker.last)

    # 最大ポジション数設定
    strategy.risk.max_position_size = qty_lot

    # 注文（ポジションがある場合ドテン）
    strategy.entry('L', 'buy', qty=qty_lot, limit=max(long_entry_price, ticker.ask), stop=long_entry_price+0.5)
    strategy.entry('S', 'sell', qty=qty_lot, limit=min(short_entry_price, ticker.bid), stop=short_entry_price-0.5)

strategy = Strategy(pivot_highlow_strategy)
strategy.settings.timeframe = '1m'
strategy.settings.interval = 5
strategy.settings.apiKey = settings.apiKey
strategy.settings.secret = settings.secret
strategy.testnet.use = False
strategy.testnet.apiKey = settings.testnet_apiKey
strategy.testnet.secret = settings.testnet_secret
strategy.start()
