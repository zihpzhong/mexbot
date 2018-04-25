# -*- coding: utf-8 -*-
from strategy import Strategy, Trading

class mylogic(Trading):
    def setup(self, strategy):
        pass

    def loop(self, ticker, ohlcv, position, balance, strategy):
        print(ticker)


strategy = Strategy(mylogic())
strategy.settings.timeframe = '1m'
strategy.settings.interval = 10
strategy.settings.partial_ohlcv = True
# strategy.testnet.use = True
# strategy.testnet.apiKey = ''
# strategy.testnet.secret = ''
strategy.start()
