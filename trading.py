# -*- coding: utf-8 -*-
from datetime import datetime
from strategy import Strategy, Trading

class mylogic(Trading):
    def setup(self, strategy):
    	print('setup')

    def loop(self, strategy):
        funding = strategy.fetch_funding()
        timestamp = funding['timestamp']
        print(funding.head())
        print(datetime.utcnow())
        delta = (timestamp[0] - timestamp[1])
        next = timestamp[0] + delta
        print(next)
        print(delta)
        rate = funding.fundingRate
        print(rate[0])


strategy = Strategy(mylogic(), 60)
strategy.settings.timeframe = '1m'
strategy.settings.interval = 10
strategy.settings.partial_ohlcv = True
strategy.testnet.use = True
strategy.testnet.apiKey = 'JmvnFgDTLwTjJb2RiKhXJ-7G'
strategy.testnet.secret = '0gW-9UhhfVLaNDbIviLh_AwuWmEk5xHtoWNzrhJcGh0fFdbb'
strategy.start()
