# -*- coding: utf-8 -*-
from strategy import Strategy
import settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Sample")

def mylogic(ticker, ohlcv, position, balance, strategy):
    pass

strategy = Strategy(mylogic)
strategy.settings.timeframe = '1m'
strategy.settings.interval = 10
strategy.settings.partial_ohlcv = True
strategy.testnet.use = True
strategy.testnet.apiKey = settings.testnet_apiKey
strategy.testnet.secret = settings.testnet_secret
strategy.start()
