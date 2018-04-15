# -*- coding: utf-8 -*-
from time import sleep
from datetime import datetime, timedelta, timezone
import sys
import logging
import logging.config
import ccxt
import pandas as pd
from utils import dotdict
from indicator import *
from settings import settings

exchange = None
orders = dotdict()
position = dotdict()
balance = dotdict()
ticker = dotdict()

qty_lot = 10
profit_trigger = 80
loss_trigger = -20
trailing_offset = 20
breakout_in = 25

def fetch_ticker(symbol=settings.symbol, timeframe=settings.timeframe):
    ticker = dotdict(exchange.fetchTicker(symbol, params={'binSize': exchange.timeframes[timeframe]}))
    logger.info("TICK: ohlc {open} {high} {low} {close} bid {bid} ask {ask}".format(**ticker))
    return ticker


def fetch_ohlcv(symbol=settings.symbol, timeframe=settings.timeframe):
    """OHLCVを取得"""
    market = exchange.market(symbol)
    req = {
        'symbol': market['id'],
        'binSize': exchange.timeframes[timeframe],
        'partial': 'false',     # True == include yet-incomplete current bins
        'reverse': 'true',
    }
    res = exchange.publicGetTradeBucketed(req)
    df = pd.DataFrame(res)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    #df['timestamp'] = pd.to_datetime(df['timestamp']) + timedelta(hours=+9)
    # d = {
    #     'open':df['close'][0],
    #     'high':df['high'][0],
    #     'low':df['low'][0],
    #     'close':df['close'][0],
    #     'volume':df['volume'][0],
    # }
    # logger.info("OHLCV: {open} {high} {low} {close} {volume}".format(**d))
    return (df['open'], df['high'], df['low'], df['close'], df['volume'])


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
        if pos.avgCostPrice is not None:
            pos.avg_price = pos.avgCostPrice
            current_cost = pos.currentQty / pos.avgCostPrice
            if pos.currentQty > 0:
                unrealized_cost = pos.currentQty / ticker.ask
                pos.profit_and_loss = int((current_cost - unrealized_cost) * 100000000)
                pos.profit_and_loss_pct = ((current_cost / unrealized_cost) * 100) - 100
            else:
                unrealized_cost = pos.currentQty / ticker.bid
                pos.profit_and_loss = int((current_cost - unrealized_cost) * 100000000)
                pos.profit_and_loss_pct = 100 - ((current_cost / unrealized_cost) * 100)
        else:
            pos.profit_and_loss = 0
            pos.profit_and_loss_pct = 0
            pos.avg_price = 0
        #pos.profit_and_loss = pos.simplePnl * 100
        #pos.profit_and_loss_pct = pos.simplePnlPcnt * 100
    else:
        pos = dotdict()
        pos.currentQty = 0
        pos.avg_price = 0
        pos.profit_and_loss = 0
        pos.profit_and_loss_pct = 0
        pos.realisedPnl = 0
    logger.info("POSITION: qty {currentQty} cost {avg_price} pnl {profit_and_loss}({profit_and_loss_pct:.2f}%) {realisedPnl}".format(**pos))
    return pos


def fetch_balance():
    balance = dotdict(exchange.fetch_balance())
    logger.info("BALANCE: free {free} used {used} total {total}".format(**balance.BTC))
    return balance


def close_position(symbol=settings.symbol):
    """現在のポジションを閉じる"""
    market = exchange.market(symbol)
    req = {'symbol': market['id']}
    res = exchange.privatePostOrderClosePosition(req)
    logger.info("CLOSE: {orderID} {side} {orderQty} {price}".format(**res))


def cancel(myid):
    """注文をキャンセル"""
    if myid in orders:
        order_id = orders[myid].id
        res = exchange.cancel_order(order_id)
        logger.info("CANCEL: {orderID} {side} {orderQty} {price}".format(**res['info']))
        del orders[myid]


def cancel_order_all(symbol=settings.symbol):
    """現在の注文をキャンセル"""
    market = exchange.market(symbol)
    req = {'symbol': market['id']}
    res = exchange.privateDeleteOrderAll(req)
    for r in res:
        logger.info("CANCEL: {orderID} {side} {orderQty} {price}".format(**r))


def create_order(side, qty, limit, stop, symbol):
    type = 'market'
    params = {}
    if stop is not None and limit is not None:
        type = 'stopLimit'
        params['stopPx'] = stop
        params['execInst'] = 'LastPrice'
        params['price'] = limit
    elif stop is not None:
        type = 'stop'
        params['stopPx'] = stop
        params['execInst'] = 'LastPrice'
    elif limit is not None:
        type = 'limit'
        params['price'] = limit
    res = exchange.create_order(symbol, type, side, qty, None, params)
    logger.info("ORDER: {orderID} {side} {orderQty} {price}({stopPx})".format(**res['info']))
    return dotdict(res)


def edit_order(id, side, qty, limit, stop, symbol):
    type = 'market'
    params = {}
    if stop is not None and limit is not None:
        type = 'stopLimit'
        params['stopPx'] = stop
        params['price'] = limit
    elif stop is not None:
        type = 'stop'
        params['stopPx'] = stop
    elif limit is not None:
        type = 'limit'
        params['price'] = limit
    res = exchange.edit_order(id, symbol, type, side, qty, None, params)
    logger.info("EDIT: {orderID} {side} {orderQty} {price}({stopPx})".format(**res['info']))
    return dotdict(res)


def order(myid, side, qty, limit=None, stop=None, symbol=settings.symbol):
    """注文"""

    qty_total = qty
    qty_limit = settings.max_position_size

    # 買いポジあり
    if position.currentQty > 0:
        # 買い増し
        if side == 'buy':
            # 現在のポジ数を加算
            qty_total = qty_total + position.currentQty
        else:
            # 反対売買の場合、ドテンできるように上限を引き上げる
            qty_limit = qty_limit + position.currentQty

    # 売りポジあり
    if position.currentQty < 0:
        # 売りまし
        if side == 'sell':
            # 現在のポジ数を加算
            qty_total = qty_total + -position.currentQty
        else:
            # 反対売買の場合、ドテンできるように上限を引き上げる
            qty_limit = qty_limit + -position.currentQty

    # 購入数をポジション最大サイズに抑える
    if qty_total > qty_limit:
        qty = qty - (qty_total - qty_limit)

    # 注文
    if qty > 0:
        if myid in orders:
            order_id = orders[myid].id
            order = dotdict(exchange.fetchOrder(order_id))
            # Todo
            # 1.部分利確の確認
            # 2.指値STOP注文の場合、トリガーされたかの確認
            # どちのら場合もキャンセル必要と思う
            if order.status == 'open':
                if order.type == 'stoplimit' and order.info['triggered'] == 'StopOrderTriggered':
                    order = exchange.cancel_order(order_id)
                    order = create_order(side, qty, limit, stop, symbol)
                else:
                    order = edit_order(order_id, side, qty, limit, stop, symbol)
            else:
                order = create_order(side, qty, limit, stop, symbol)
        else:
            order = create_order(side, qty, limit, stop, symbol)
        orders[myid] = order


def entry(myid, side, qty, limit=None, stop=None, symbol=settings.symbol):
    """注文"""
    # 買いポジションがある場合、清算する
    if side=='sell' and position.currentQty > 0:
        qty = qty + position.currentQty

    # 売りポジションがある場合、清算する
    if side=='buy' and position.currentQty < 0:
        qty = qty - position.currentQty

    # 注文
    order(myid, side, qty, limit, stop, symbol)


if __name__ == "__main__":
    # ログ設定
    logging.config.fileConfig("logging.conf")
    logger = logging.getLogger("app")
    logger.setLevel(logging.DEBUG)
    logger.info("Starting")

    # 取引所セットアップ
    logger.info("Setup Exchange")
    if settings.use_testnet:
        exchange = getattr(ccxt, settings.exchange)({
            'apiKey': settings.testnet_apiKey,
            'secret': settings.testnet_secret,
            })
        exchange.urls['api'] = exchange.urls['test']
    else:
        exchange = getattr(ccxt, settings.exchange)({
            'apiKey': settings.apiKey,
            'secret': settings.secret,
            })
    exchange.load_markets()

    # 現在のポジションをすべて閉じる
    logger.info("Cancel all orders and close position")
    cancel_order_all()
    close_position()

    # トレールストップ価格
    trailing_stop = 0

    while True:
        try:
            # ティッカー取得
            ticker = fetch_ticker()

            # ポジション取得
            position = fetch_position()

            # 資金情報取得
            #balance = fetch_balance()

            # 足取得
            (open, high, low, close, volume) = fetch_ohlcv()

            # エントリー/エグジット
            long_entry_price = highest(high, breakout_in)
            short_entry_price = lowest(low, breakout_in)

            # 注文
            # if position.currentQty == 0:
            #     order('L', 'buy', qty=qty_lot, limit=int(long_entry_price[0]+0.5), stop=int(long_entry_price[0]+0.5))
            #     order('S', 'sell', qty=qty_lot, limit=int(short_entry_price[0]-0.5), stop=int(short_entry_price[0]-0.5))
            entry('L', 'buy', qty=qty_lot, limit=int(long_entry_price[0]+0.5), stop=int(long_entry_price[0]+0.5))
            entry('S', 'sell', qty=qty_lot, limit=int(short_entry_price[0]-0.5), stop=int(short_entry_price[0]-0.5))

            # 利確/損切り
            if position.currentQty > 0:
                if ticker.ask > trailing_stop or trailing_stop == 0:
                    trailing_stop = ticker.ask
                order('L_exit', side='sell', qty=position.currentQty, stop=trailing_stop - trailing_offset)
                # pnl = ticker.ask - position.avg_price
                # if pnl >= profit_trigger:
                #     order('L_exit', side='sell', qty=position.currentQty, limit=ticker.ask)
                # elif pnl <= loss_trigger:
                #     order('L_exit', side='sell', qty=position.currentQty)
            elif position.currentQty < 0:
                if ticker.bid < trailing_stop or trailing_stop == 0:
                    trailing_stop = ticker.bid
                order('S_exit', side='buy', qty=-position.currentQty, stop=trailing_stop + trailing_offset)
                # pnl = position.avg_price - ticker.bid
                # if pnl >= profit_trigger:
                #     order('S_exit', side='buy', qty=-position.currentQty, limit=ticker.bid)
                # elif pnl <= loss_trigger:
                #     order('S_exit', side='buy', qty=-position.currentQty)
            else:
                trailing_stop = 0
                cancel('L_exit')
                cancel('S_exit')

            # 待機
            sleep(settings.interval)

        except ccxt.DDoSProtection as e:
            logging.exception('DDoS Protection (ignoring)')
            sleep(5)
        except ccxt.RequestTimeout as e:
            logging.exception('Request Timeout (ignoring)')
            sleep(5)
        except ccxt.ExchangeNotAvailable as e:
            logging.exception('Exchange Not Available due to downtime or maintenance (ignoring)')
            sleep(60)
        except ccxt.AuthenticationError as e:
            logging.exception('Authentication Error (missing API keys, ignoring)')
        except ccxt.ExchangeError as e:
            logging.exception('Exchange Error (hmmm...)')
            sleep(5)
        except (KeyboardInterrupt, SystemExit):
            logging.info('Shutdown...')
            cancel_order_all()
            close_position()
            sys.exit()
        except Exception as e:
            logging.exception(e)
            sleep(5)
