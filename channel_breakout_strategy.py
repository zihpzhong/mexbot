# -*- coding: utf-8 -*-
from time import sleep
from datetime import datetime, timedelta, timezone
import sys
import ccxt
import pandas as pd
from utils import dotdict
from indicator import highest, lowest

# テストネット
testnet = True

# ストラテジー設定
settings = dotdict()
settings.exchange = 'bitmex'
settings.symbol = 'BTC/USD'
if testnet:
    settings.api_key = 'VGJehwSbSB0L8GhgoIH5dA7V'
    settings.secret = 'qRSpVr6tGKCwP0m3Svxn0h9h2H3_v4yk30WlikDBFWS9rBJg'
else:
    settings.api_key = 'N5xVisqiOL_tPwfWQxor0Wwh'
    settings.secret = 'NDcub9OvQZKxTHTNrLumOlVh1IM3pci48vVf8szQjvuLmNF3'
settings.timeframe = '1m'
settings.max_position_size = 100
settings.interval = 30

symbol = ''
orders = dotdict()
position = dotdict()

def fetch_ohlc(symbol=settings.symbol, timeframe=settings.timeframe):
    """OHLCを取得"""
    market = exchange.market(symbol)
    req = {
        'symbol': market['id'],
        'binSize': exchange.timeframes[timeframe],
        'partial': True,     # True == include yet-incomplete current bins
        'reverse': True,
    }
    res = exchange.publicGetTradeBucketed(req)
    df = pd.DataFrame(res)
    df['timestamp'] = pd.to_datetime(df['timestamp']) + timedelta(hours=+9)
    return dotdict({
        'df': df,
        'time':df['timestamp'],
        'close':df['close'],
        'open':df['open'],
        'high':df['high'],
        'low':df['low'],
        'volume':df['volume']})

def fetch_position():
    """現在のポジションを取得
    currentQty    現在のポジションサイズ（売りはマイナス）
    openOrderBuyQty        未約定買いポジションサイズ
    openOrderSellQty    未約定売りポジションサイズ
    isOpen    True:ポジションあり
    """
    res = exchange.privateGetPosition()
    if len(res):
        res = dotdict(res[0])
        res['timestamp'] = pd.to_datetime(res['timestamp'])
    else:
        res = dotdict()
        res.currentQty = 0
        res.currentCost = 0
    print(res)
    print("POSITION: {currentQty}".format(**res))
    return res

def close_position(symbol=settings.symbol):
    """現在のポジションを閉じる"""
    market = exchange.market(symbol)
    req = {'symbol': market['id']}
    res = exchange.privatePostOrderClosePosition(req)
    print("CLOSE: {orderID} {side} {orderQty} {price}".format(**res))

def cancel_order_all(symbol=settings.symbol):
    """現在の注文をキャンセル"""
    market = exchange.market(symbol)
    req = {'symbol': market['id']}
    res = exchange.privateDeleteOrderAll(req)
    for r in res:
        print("CANCEL: {orderID} {side} {orderQty} {price}".format(**r))

def create_order(side, qty, limit, stop, symbol=settings.symbol):
    type = 'market'
    params = {}
    if stop > 0 and limit > 0:
        type = 'stopLimit'
        params['stopPx'] = stop
        params['execInst'] = 'LastPrice'
        params['price'] = limit
    elif stop > 0:
        type = 'stop'
        params['stopPx'] = stop
        params['execInst'] = 'LastPrice'
    elif limit > 0:
        type = 'limit'
        params['price'] = limit
    #create_order(self, symbol, type, side, amount, price=None, params={}):
    res = exchange.create_order(symbol, type, side, qty, limit, params)
    print("ORDER: {orderID} {side} {orderQty} {price}".format(**res['info']))

def long(qty, limit=0, stop=0, symbol=settings.symbol):
    """買い"""
    total = qty
    # 現在のポジションが買いの場合、currentQtyを加算する
    if position.currentQty > 0:
        total = total + position.currentQty

    # ポジション最大サイズに抑える
    if total > settings.max_position_size:
        qty = qty - (total - settings.max_position_size)

    # 買う必要があるなら注文を出す
    if qty > 0:
        # 売りポジションがある場合、清算する
        if position.currentQty < 0:
            qty = qty - position.currentQty
        create_order('buy', qty, limit, stop)

def short(qty, limit=0, stop=0, symbol=settings.symbol):
    """売り"""
    # 現在のポジションが売りの場合、currentQtyを加算する
    # 買いポジションの場合、反転させるため加算する
    total = qty
    if position.currentQty < 0:
        total = total - position.currentQty

    # ポジション最大サイズに抑える
    if total > settings.max_position_size:
        qty = qty - (total - settings.max_position_size)

    # 得る必要があるなら注文を出す
    if qty > 0:
        # 買いポジションがある場合、清算する
        if position.currentQty > 0:
            qty = qty + position.currentQty
        create_order('sell', qty, limit, stop)


if __name__ == "__main__":
    # 取引所セットアップ
    exchange = getattr(ccxt, settings.exchange)({
        'apiKey': settings.api_key,
        'secret': settings.secret,
        })
    if testnet:
        exchange.urls['api'] = exchange.urls['test']
    exchange.load_markets()

    # 現在のポジションをすべて閉じる
    close_position()

    while True:
        try:
            # 足取得
            ohlc = fetch_ohlc()
            d = {
                'open':ohlc.open[0],
                'high':ohlc.high[0],
                'low':ohlc.low[0],
                'close':ohlc.close[0],
                'volume':ohlc.volume[0],
            }
            print("TICK: o:{open} h:{high} l:{low} c:{close} v:{volume}".format(**d))

            # ポジション取得
            position = fetch_position()

            # 現在の注文をすべて閉じる
            cancel_order_all()

            # 注文
            higher = highest(ohlc.high, 90)[0]
            lower = lowest(ohlc.low, 90)[0]

            long(qty=100, stop=higher+1.5)
            short(qty=100, stop=lower-1.5)

            # 次の足確定後、10秒経過するまで待機
            # delta = ohlc.time[0] - datetime.now() + timedelta(seconds=10)
            # sleep(delta.seconds)
            sleep(settings.interval)

        except ccxt.DDoSProtection as e:
            print(type(e).__name__, e.args, 'DDoS Protection (ignoring)')
        except ccxt.RequestTimeout as e:
            print(type(e).__name__, e.args, 'Request Timeout (ignoring)')
        except ccxt.ExchangeNotAvailable as e:
            print(type(e).__name__, e.args, 'Exchange Not Available due to downtime or maintenance (ignoring)')
            sleep(60)
        except ccxt.AuthenticationError as e:
            print(type(e).__name__, e.args, 'Authentication Error (missing API keys, ignoring)')
        except ccxt.ExchangeError as e:
            print(type(e).__name__, e.args, 'Exchange Error(hmmm...)')
            sleep(5)
        except (KeyboardInterrupt, SystemExit):
            cancel_order_all()
            close_position()
            sys.exit()
