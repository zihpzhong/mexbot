# -*- coding: utf-8 -*-
import logging
from strategy_bitflyer import StrategyBitflyer
from settings_bitflyer import settings
from time import sleep

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("SampleBot")

def bitflyer_sample_strategy(ticker, ohlcv, position, balance, strategy):
	if position.currentQty > -0.01:
		strategy.order('test', 'sell', qty=0.01, limit=ticker.ask)
	else:
		strategy.order('test', 'buy', qty=-position.currentQty, limit=ticker.bid)

strategy = StrategyBitflyer(bitflyer_sample_strategy)
strategy.settings.timeframe = '1m'
strategy.settings.interval = 5
strategy.risk.max_position_size = 0.02
strategy.settings.apiKey = settings.apiKey
strategy.settings.secret = settings.secret
strategy.start()
