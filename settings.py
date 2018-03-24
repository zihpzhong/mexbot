# -*- coding: utf-8 -*-
from utils import dotdict

settings = dotdict()

# APIキー設定
settings.api_key = ''
settings.secret = ''

# ストラテジー設定
settings.exchange = 'bitmex'
settings.symbol = 'BTC/USD'
settings.timeframe = '1m'
settings.max_position_size = 1000
settings.interval = 10

# テストネット利用
settings.use_testnet = True
settings.testnet_api_key = ''
settings.testnet_secret = ''
