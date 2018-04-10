# -*- coding: utf-8 -*-
import sys
from time import sleep
import ccxt
import pandas as pd
from datetime import datetime, timedelta
from utils import dotdict


class Trading:
    def setup(self, strategy):
        pass

    def loop(self, strategy):
        pass


class Strategy:
    def __init__(self, yourlogic, interval=60):

        # トレーディングロジック設定
        self.yourlogic = yourlogic

        # 動作タイミング
        self.settings.interval = interval

        # 取引所情報
        self.settings = dotdict()
        self.settings.exchange = 'bitmex'
        self.settings.symbol = 'BTC/USD'
        self.settings.api_key = ''
        self.settings.secret = ''

        # OHLCV設定
        self.settings.timeframe = '1m'
        self.settings.partial = False

        # テストネット設定
        self.testnet = dotdict()
        self.testnet.use = False
        self.testnet.apiKey = ''
        self.testnet.secret = ''

        # リスク設定
        self.risk = dotdict()
        self.risk.max_position_size = 100
        self.risk.max_drawdown = 1000

        # ポジション情報
        self.position = dotdict()
        self.position.current_qty = 0
        self.position.avg_price = 0
        self.position.profit_and_loss = 0
        self.position.profit_and_loss_pct = 0

        # 注文情報
        self.orders = dotdict()

        # ティッカー情報
        self.ticker = dotdict()

        # ohlcv情報
        self.df_ohlcv = None

    def safe_symbol(self, symbol):
        if symbol is None:
            symbol = self.settings.symbol
        return symbol

    def safe_timeframe(self, timeframe):
        if timeframe is None:
            timeframe = self.settings.timeframe
        return timeframe

    def fetch_ticker(self, symbol=None, timeframe=None):
        symbol = self.safe_symbol(symbol)
        timeframe = self.safe_timeframe(timeframe)
        ticker = dotdict(self.exchange.fetchTicker(symbol, params={self.exchange.timeframes[timeframe]}))
        #print("{datetime} TICK: ohlc {open} {high} {low} {close} bid {bid} ask {ask}".format(**ticker))
        return ticker

    def fetch_ohlcv(self, symbol=None, timeframe=None):
        """OHLCVを取得"""
        symbol = self.safe_symbol(symbol)
        timeframe = self.safe_timeframe(timeframe)
        market = self.exchange.market(symbol)
        req = {
            'symbol': market['id'],
            'binSize': self.exchange.timeframes[timeframe],
            'partial': 'true' if self.settings.partial else 'false',     # True == include yet-incomplete current bins
            'reverse': 'true',
        }
        res = self.exchange.publicGetTradeBucketed(req)
        df = pd.DataFrame(res)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        return df

    def fetch_position(self, symbol=None):
        """現在のポジションを取得"""
        symbol = self.safe_symbol(symbol)
        res = self.exchange.privateGetPosition()
        market = self.exchange.market(symbol)
        pos = [x for x in res if x['symbol'] == market['id']]
        if len(pos):
            pos = dotdict(pos[0])
            pos.timestamp = pd.to_datetime(pos.timestamp)
            if pos.avgCostPrice is not None:
                pos.avg_price = pos.avgCostPrice
                current_cost = pos.currentQty / pos.avgCostPrice
                if pos.currentQty > 0:
                    unrealized_cost = pos.currentQty / self.ticker.ask
                    pos.profit_and_loss = int((current_cost - unrealized_cost) * 100000000)
                    pos.profit_and_loss_pct = ((current_cost / unrealized_cost) * 100) - 100
                else:
                    unrealized_cost = pos.currentQty / self.ticker.bid
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
            pos.avgCostPrice = None
            pos.commission = 0
            pos.lastPrice = None
            pos.avg_price = 0
            pos.profit_and_loss = 0
            pos.profit_and_loss_pct = 0
        #print("{currentTimestamp} POSITION: qty {currentQty} cost {avg_price} pnl {profit_and_loss}({profit_and_loss_pct:.2f}%) {realisedPnl}".format(**pos))
        return pos

    def fetch_balance(self):
        """資産情報取得"""
        balance = dotdict(self.exchange.fetch_balance())
        #print("BALANCE: free {free} used {used} total {total}".format(**balance.BTC))
        return balance

    def fetch_funding(self, symbol=None):
        """資金調達"""
        symbol = self.safe_symbol(symbol)
        market = self.exchange.market(symbol)
        req = {
            'symbol': market['id'],
            'reverse': 'true',
        }
        res = self.exchange.publicGetFunding(req)
        df = pd.DataFrame(res)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        #print("FUNDING:".format(**balance.BTC))
        return df

    def close_position(self, symbol=None):
        """現在のポジションを閉じる"""
        symbol = self.safe_symbol(symbol)
        market = self.exchange.market(symbol)
        req = {'symbol': market['id']}
        res = self.exchange.privatePostOrderClosePosition(req)
        print("{timestamp} CLOSE: {orderID} {side} {orderQty} {price}".format(**res))

    def cancel_order_all(self, symbol=None):
        """現在の注文をキャンセル"""
        symbol = self.safe_symbol(symbol)
        market = self.exchange.market(symbol)
        req = {'symbol': market['id']}
        res = self.exchange.privateDeleteOrderAll(req)
        for r in res:
            print("{timestamp} CANCEL: {orderID} {side} {orderQty} {price}".format(**r))

    def create_order(self, side, qty, limit, stop, symbol):
        symbol = self.safe_symbol(symbol)
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
        res = self.exchange.create_order(symbol, type, side, qty, None, params)
        print("{timestamp} ORDER: {orderID} {side} {orderQty} {price}({stopPx})".format(**res['info']))
        return dotdict(res)

    def edit_order(self, id, side, qty, limit, stop, symbol):
        symbol = self.safe_symbol(symbol)
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
        res = self.exchange.edit_order(id, symbol, type, side, qty, None, params)
        print("{timestamp} EDIT: {orderID} {side} {orderQty} {price}".format(**res['info']))
        return dotdict(res)

    def order(self, myid, side, qty, limit=None, stop=None, symbol=None):
        """注文"""
        symbol = self.safe_symbol(symbol)

        qty_total = qty
        qty_limit = self.risk.max_position_size

        # 買いポジあり
        if securrent_lf.position.qty > 0:
            # 買い増し
            if side == 'buy':
                # 現在のポジ数を加算
                qty_total = qty_total + self.position.current_qty
            else:
                # 反対売買の場合、ドテンできるように上限を引き上げる
                qty_limit = qty_limit + self.position.current_qty

        # 売りポジあり
        if self.position.current_qty < 0:
            # 売りまし
            if side == 'sell':
                # 現在のポジ数を加算
                qty_total = qty_total + -self.position.current_qty
            else:
                # 反対売買の場合、ドテンできるように上限を引き上げる
                qty_limit = qty_limit + -self.position.current_qty

        # 購入数をポジション最大サイズに抑える
        if qty_total > qty_limit:
            qty = qty - (qty_total - qty_limit)

        # 注文
        if qty > 0:
            if myid in self.orders:
                order_id = self.orders[myid].id
                order = dotdict(self.exchange.fetchOrder(order_id))
                # Todo
                # 1.部分利確の確認
                # 2.指値STOP注文の場合、トリガーされたかの確認
                # どちのら場合もキャンセル必要と思う
                if order.status == 'open':
                    if order.type == 'stoplimit' and order.info['triggered'] == 'StopOrderTriggered':
                        order = self.exchange.cancel_order(order_id)
                        order = self.create_order(side, qty, limit, stop, symbol)
                    else:
                        order = edit_order(order_id, side, qty, limit, stop, symbol)
                else:
                    order = self.create_order(side, qty, limit, stop, symbol)
            else:
                order = self.create_order(side, qty, limit, stop, symbol)
            self.orders[myid] = order

    def entry(self, myid, side, qty, limit=None, stop=None, symbol=None):
        """注文"""
        symbol = self.safe_symbol(symbol)

        # 買いポジションがある場合、清算する
        if side=='sell' and self.position.current_qty > 0:
            qty = qty + self.position.current_qty

        # 売りポジションがある場合、清算する
        if side=='buy' and self.position.current_qty < 0:
            qty = qty - self.position.current_qty

        # 注文
        self.order(myid, side, qty, limit, stop, symbol)

    def prepare(self):
        # 取引所セットアップ
        if self.testnet.use:
            self.exchange = getattr(ccxt, self.settings.exchange)({
                'apiKey': self.testnet.apiKey,
                'secret': self.testnet.secret,
                })
            self.exchange.urls['api'] = self.exchange.urls['test']
        else:
            self.exchange = getattr(ccxt, self.settings.exchange)({
                'apiKey': self.settings.apiKey,
                'secret': self.settings.secret,
                })
        self.exchange.load_markets()

    def start(self):
        self.prepare()
        self.yourlogic.setup(self)

        next_fetch_ohlcv_time = None

        while True:
            try:
                # ティッカー取得
                self.ticker = self.fetch_ticker()

                # ポジション取得
                self.position = self.fetch_position()

                # 資金情報取得
                #self.balance = self.fetch_balance()

                # 足取得（10経過後取得）
                if next_fetch_ohlcv_time is None or datetime.utcnow() > next_fetch_ohlcv_time:
                    self.df_ohlcv = self.fetch_ohlcv()
                    timestamp = self.df_ohlcv['timestamp']
                    if self.settings.partial:
                        next_fetch_ohlcv_time = None
                    else:
                        next_fetch_ohlcv_time = timestamp[0] + (timestamp[0] - timestamp[1])
                        next_fetch_ohlcv_time = next_fetch_ohlcv_time + timedelta(seconds=10)

                # メインロジックコール
                self.yourlogic.loop(self)

            except Exception as e:
                print(e)
                break
            sleep(self.settings.interval)

        # 全注文キャンセル
        self.cancel_order_all()

        # ポジションクローズ
        self.close_position()
