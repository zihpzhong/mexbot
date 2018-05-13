# -*- coding: utf-8 -*-
from strategy import Strategy
from indicator import *
from settings import settings
import logging
import logging.config

leftbars = 1
rightbars = 0

logging.config.fileConfig("logging.conf")
logger = logging.getLogger("SARBot")

def sar_strategy(ticker, ohlcv, position, balance, strategy):

    # インジケーター作成
    vsar = last(sar(ohlcv.high, ohlcv.low, 0.02, 0.02, 0.2))

	# ロット数計算
    qty_lot = int(balance.BTC.free * 0.05 * ticker.last)

    # 最大ポジション数設定
    strategy.risk.max_position_size = qty_lot

    # 注文（ポジションがある場合ドテン）
    if vsar > last(ohlcv.high):
        vsar = int(vsar)
        strategy.entry('L', 'buy', qty=qty_lot, limit=max(vsar, ticker.bid), stop=vsar)
    else:
        strategy.cancel('L')
        # 指値ささらなかったから成り行きでロング
        if position.currentQty < 0:
            strategy.entry('L', 'buy', qty=qty_lot)

    if vsar < last(ohlcv.low):
        vsar = int(vsar)
        strategy.entry('S', 'sell', qty=qty_lot, limit=min(vsar, ticker.ask), stop=vsar)
    else:
        strategy.cancel('S')
        # 指値ささらなかったから成り行きでショート
        if position.currentQty > 0:
            strategy.entry('S', 'sell', qty=qty_lot)


strategy = Strategy(sar_strategy)
strategy.settings.timeframe = '1m'
strategy.settings.interval = 5
strategy.settings.apiKey = settings.apiKey
strategy.settings.secret = settings.secret
strategy.testnet.use = False
strategy.testnet.apiKey = settings.testnet_apiKey
strategy.testnet.secret = settings.testnet_secret
strategy.start()
