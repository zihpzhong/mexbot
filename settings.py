# -*- coding: utf-8 -*-
from utils import dotdict

settings = dotdict()

# APIキー設定
settings.apiKey = ''
settings.secret = ''

# ストラテジー設定
settings.exchange = 'bitmex'
settings.symbol = 'BTC/USD'
settings.timeframe = '1h'
settings.max_position_size = 100
settings.interval = 60

# テストネット利用
settings.use_testnet = True
settings.testnet_apiKey = ''
settings.testnet_secret = ''
