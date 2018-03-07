# -*- coding: utf-8 -*-
from time import sleep
import sys
import atexit
import signal
from utils import dotdict


class strategy:
    def __init__(self):
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

    def run_loop(self, your_logic):
        self.init()
        while True:
            try:
                self.sanity_check()
                self.print_status()
                your_logic()
            except (KeyboardInterrupt, SystemExit):
                sys.exit()
            sleep(self.settings.period)

## Valiables
open = []
high = []
low = []
close = []
volume = []
