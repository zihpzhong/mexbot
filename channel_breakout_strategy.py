# -*- coding: utf-8 -*-
from strategy import Strategy
from indicator import *
from settings import settings
import logging
import logging.config
from datetime import datetime, timedelta

logging.config.fileConfig("logging.conf")
logger = logging.getLogger("ChbrkBot")

# 資産比 N% を購入
lot_ratio_to_asset = 0.3

# ブレイクアウトエントリー期間
breakout_in = 22

# トレールストップ価格
trailing_stop = 0
trailing_offset = 10

# 次にエントリーする時間
next_entry_time = datetime.utcnow()

def channel_breakout_strategy(ticker, ohlcv, position, balance, strategy):
    global next_entry_time, trailing_stop

    # エントリー/エグジット
    long_entry_price = last(highest(ohlcv.high, breakout_in))
    short_entry_price = last(lowest(ohlcv.low, breakout_in))

    # ロット数計算
    qty_lot = int(balance.BTC.free * lot_ratio_to_asset * ticker.last)
    logger.info("LOT: " + str(qty_lot))

    # 最大ポジション数設定
    strategy.risk.max_position_size = qty_lot

    # 注文
    if datetime.utcnow() > next_entry_time:
        strategy.entry('L', 'buy', qty=qty_lot, limit=max(long_entry_price, ticker.bid), stop=long_entry_price+0.5)
        strategy.entry('S', 'sell', qty=qty_lot, limit=min(short_entry_price, ticker.ask), stop=short_entry_price-0.5)
    else:
        strategy.cancel('S')
        strategy.cancel('L')

    # 利確/損切り
    if position.currentQty > 0:
        next_entry_time = datetime.utcnow() + timedelta(minutes=5)
        if ticker.ask > trailing_stop or trailing_stop == 0:
            trailing_stop = ticker.ask

        if ticker.ask <= (trailing_stop - trailing_offset):
            strategy.order('L_exit', side='sell', qty=position.currentQty, limit=ticker.ask)
            strategy.interval = 3

    elif position.currentQty < 0:
        next_entry_time = datetime.utcnow() + timedelta(minutes=5)
        if ticker.bid < trailing_stop or trailing_stop == 0:
            trailing_stop = ticker.bid

        if ticker.bid >= (trailing_stop + trailing_offset):
            strategy.order('S_exit', side='buy', qty=-position.currentQty, limit=ticker.bid)
            strategy.interval = 3

    else:
        # 利確/損切り注文キャンセル
        trailing_stop = 0
        strategy.cancel('L_exit')
        strategy.cancel('S_exit')

strategy = Strategy(channel_breakout_strategy)
strategy.settings.timeframe = '5m'
strategy.settings.interval = 10
strategy.settings.apiKey = settings.apiKey
strategy.settings.secret = settings.secret
strategy.testnet.use = True
strategy.testnet.apiKey = settings.testnet_apiKey
strategy.testnet.secret = settings.testnet_secret
strategy.start()
