# -*- coding: utf-8 -*-
from time import sleep
import sys
import atexit
import signal
from utils import dotdict
import ccxt
import pandas as pd

class Strategy:
    def __init__(self, your_logic):

        # set property
        self.your_logic = your_logic
        self.interval = 5

        # settings
        self.settings = dotdict()
        self.settings.exchange = 'bitmex'
        self.settings.symbol = 'BTC/USD'
        self.settings.api_key = ''
        self.settings.secret = ''
        self.settings.timeframe = '1m'

        # risk settings
        self.risk = dotdict()
        self.risk.max_position_size = 100
        self.risk.max_drawdown = 1000

    def start(self):
        self.exchange = getattr(ccxt, self.settings.exchange)({
            'apiKey': self.settings.api_key,
            'secret': self.settings.secret,
            })
        self.exchange.load_markets()
        self.symbol = self.settings.symbol
        self.timeframe = self.settings.timeframe

    def stop(self):
        cancel_all();
        close_all();

    def fetch_bitmex_ohlc(self):
        market = self.exchange.market(self.symbol)
        req = {
            'symbol': market['id'],
            'binSize': self.exchange.timeframes[self.timeframe],
            'partial': True,     # True == include yet-incomplete current bins
            'reverse': True,
        }
        res = self.exchange.publicGetTradeBucketed(req)
        df = pd.DataFrame(res)
        return dotdict({
            'df': df,
            'time':df['timestamp'],
            'close':df['close'],
            'open':df['open'],
            'high':df['high'],
            'low':df['low'],
            'volume':df['volume']})

    def sanity_check(self):
        pass

    def print_status(self):
        pass

    def run_loop(self):
        self.start()
        while True:
            try:
                params = self.fetch_bitmex_ohlc()
                params.strategy = self

                self.sanity_check()
                self.print_status()
                self.your_logic(**params)
            except (KeyboardInterrupt, SystemExit):
                break
            sleep(self.interval)
        self.stop()

    def entry(self, id, long, qty, limit = 0, stop = 0):
        pass

    def exit(self, id, from_id, qty, limit = 0, stop = 0):
        pass

    def long(self, id, qty, limit = 0, stop = 0):
        entry(id, True, qty, limit, stop)

    def short(self, id, qty, limit = 0, stop = 0):
        entry(id, False, qty, limit, stop)

    def close(self, id):
        pass

    def close_all(self):
        pass

    def cancel_all(self):
        pass
