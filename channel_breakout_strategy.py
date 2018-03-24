# -*- coding: utf-8 -*-
from time import sleep
from datetime import datetime, timedelta, timezone
import sys
import ccxt
import pandas as pd
from utils import dotdict
from indicator import highest, lowest
from settings import settings

print(ccxt.__version__)

exchange = None
orders = dotdict()
position = dotdict()
balance = dotdict()

def fetch_ticker(symbol=settings.symbol, timeframe=settings.timeframe):
    ticker = dotdict(exchange.fetchTicker(symbol, params={'binSize': exchange.timeframes[timeframe]}))
    #print(ticker)
    print("TICK: ohlc {open} {high} {low} {close} bid {bid} ask {ask}".format(**ticker))
    return ticker


def fetch_ohlcv(symbol=settings.symbol, timeframe=settings.timeframe):
    """OHLCVを取得"""
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
    # d = {
    #     'open':df['close'][0],
    #     'high':df['high'][0],
    #     'low':df['low'][0],
    #     'close':df['close'][0],
    #     'volume':df['volume'][0],
    # }
    # print("OHLCV: {open} {high} {low} {close} {volume}".format(**d))
    return dotdict({
        'df': df,
        'time':df['timestamp'],
        'close':df['close'],
        'open':df['open'],
        'high':df['high'],
        'low':df['low'],
        'volume':df['volume']})


def fetch_position(symbol=settings.symbol):
    """現在のポジションを取得
    currentQty          現在のポジションサイズ（売りはマイナス）
    openOrderBuyQty     未約定買いポジションサイズ
    openOrderSellQty    未約定売りポジションサイズ
    commission          手数料率
    avgCostPrice        取得コスト
    LastPrice           ラストプライス
    """
    res = exchange.privateGetPosition()
    pos = [x for x in res if x['symbol'] == exchange.market(symbol)['id']]
    if len(pos):
        pos = dotdict(pos[0])
        pos.timestamp = pd.to_datetime(pos.timestamp)
    else:
        pos = dotdict()
        pos.currentQty = 0
        pos.avgCostPrice = None
        pos.commission = 0
        pos.lastPrice = None
    print("POSITION: qty {currentQty} cost {avgCostPrice} last {lastPrice}".format(**pos))
    return pos


def fetch_balance():
    balance = dotdict(exchange.fetch_balance())
    print("BALANCE: free {free} used {used} total {total}".format(**balance.BTC))
    return balance


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
    res = exchange.create_order(symbol, type, side, qty, None, params)
    print("ORDER: {orderID} {side} {orderQty} {price}".format(**res['info']))
    return dotdict(res)


def edit_order(id, side, qty, limit, stop, symbol=settings.symbol):
    type = 'market'
    params = {}
    if stop > 0 and limit > 0:
        type = 'stopLimit'
        params['stopPx'] = stop
        params['price'] = limit
    elif stop > 0:
        type = 'stop'
        params['stopPx'] = stop
    elif limit > 0:
        type = 'limit'
        params['price'] = limit
    res = exchange.edit_order(id, symbol, type, side, qty, None, params)
    print("EDIT: {orderID} {side} {orderQty} {price}".format(**res['info']))
    return dotdict(res)


def long(myid, qty, limit=0, stop=0, symbol=settings.symbol):
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

        # 注文状況を確認
        if myid in orders:
            order_id = orders[myid].id
            order = exchange.fetchOrder(order_id)
            if order['status'] == 'open':
                order = edit_order(order_id, 'buy', qty, limit, stop)
            else:
                order = create_order('buy', qty, limit, stop)
        else:
            order = create_order('buy', qty, limit, stop)
        orders[myid] = order


def short(myid, qty, limit=0, stop=0, symbol=settings.symbol):
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
        if myid in orders:
            order_id = orders[myid].id
            order = exchange.fetchOrder(order_id)
            if order['status'] == 'open':
                order = edit_order(order_id, 'sell', qty, limit, stop)
            else:
                order = create_order('sell', qty, limit, stop)
        else:
            order = create_order('sell', qty, limit, stop)
        orders[myid] = order


if __name__ == "__main__":
    # 取引所セットアップ
    if settings.use_testnet:
        exchange = getattr(ccxt, settings.exchange)({
            'apiKey': settings.testnet_api_key,
            'secret': settings.testnet_secret,
            })
        exchange.urls['api'] = exchange.urls['test']
    else:
        exchange = getattr(ccxt, settings.exchange)({
            'apiKey': settings.api_key,
            'secret': settings.secret,
            })
    exchange.load_markets()

    # 現在のポジションをすべて閉じる
    close_position()

    while True:
        try:
            # ティッカー取得
            ticker = fetch_ticker()

            # 資金情報取得
            balance = fetch_balance()

            # ポジション取得
            position = fetch_position()

            # 足取得
            ohlc = fetch_ohlcv()

            # エントリー/エグジット判定
            higher = highest(ohlc.high, 5)[0]
            lower = lowest(ohlc.low, 5)[0]

            # 注文
            long('L', qty=1000, stop=higher)
            short('S', qty=1000, stop=lower)

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
