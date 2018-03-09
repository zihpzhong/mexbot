# -*- coding: utf-8 -*-
from time import sleep
import sys
import atexit
import signal
from utils import dotdict


class Strategy:
    def __init__(self, your_logic):

        # set property
        self.your_logic = your_logic
        self.period = 20

        # settings
        self.settings = dotdict()
        self.settings.exchange = ''
        self.settings.market = ''
        self.settings.api_key = ''
        self.settings.secret = ''

        # risk settings
        self.risk = dotdict()
        self.risk.allow_entry_long = True
        self.risk.allow_entry_short = True
        self.risk.max_position_size = 5
        self.risk.max_drawdown = 100000

    def start(self):
        print('start')

    def stop(self):
        cancel_all();
        close_all();

    def sanity_check(self):
        print('sanity_check')

    def print_status(self):
        print('print_status')

    def run_loop(self):
        self.start()
        while True:
            try:
                params = {
                    'strategy': self,
                    'close':210,
                    'open':200,
                    'high':250,
                    'low':180,
                    'volume':500,
                }
                self.sanity_check()
                self.print_status()
                self.your_logic(**params)
            except (KeyboardInterrupt, SystemExit):
                break
            sleep(self.period)
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
