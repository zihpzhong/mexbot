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

# ロギング設定
settings.logging_conf = {
    'version': 1,
    'formatters':{
        'simpleFormatter':{
            'format': '%(asctime)s %(levelname)s:%(name)s:%(message)s',
            'datefmt': '%Y/%m/%d %H:%M:%S'}},
    'handlers': {
        'fileHandler': {
            'formatter':'simpleFormatter',
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'level': 'INFO',
            'filename': 'bitbot.log',
            'encoding': 'utf8',
            'when': 'D',
            'interval': 1,
            'backupCount': 5},
        'consoleHandler': {
            'formatter':'simpleFormatter',
            'class': 'logging.StreamHandler',
            'level': 'INFO',
            'stream': 'ext://sys.stderr'}},
    'root': {
        'level': 'INFO',
        'handlers': ['fileHandler', 'consoleHandler']},
    'disable_existing_loggers': False
    }
