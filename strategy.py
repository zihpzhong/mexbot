# -*- coding: utf-8 -*-
from time import sleep
import sys
import atexit
import signal
from utils import dotdict


class Strategy:
    def __init__(self, your_logic):
        # set your logic
        self.your_logic = your_logic

        # default settings
        self.settings = dotdict()
        self.settings.period = 20
        self.settings.exchange = ''
        self.settings.market = ''
        self.settings.api_key = ''
        self.settings.secret = ''

        # register exit proc
        atexit.register(self.exit)
        signal.signal(signal.SIGTERM, self.exit)

    def init(self):
        print('init')

    def exit(self):
        print('exit')
        sys.exit()

    def sanity_check(self):
        print('sanity_check')

    def print_status(self):
        print('print_status')

    def run_loop(self):
        self.init()
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
                sys.exit()
            sleep(self.settings.period)
