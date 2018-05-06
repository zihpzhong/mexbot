# -*- coding: utf-8 -*-
from time import sleep
from datetime import datetime, timedelta, timezone
import sys
import logging
import logging.config
import ccxt
import pandas as pd
from utils import dotdict
from indicator import last
from strategy import Trading, excahge_error

class StrategyBitflyer:
    def __init__(self, yourlogic, interval=60):

        # トレーディングロジック設定
        self.yourlogic = yourlogic

        # 取引所情報
        self.settings = dotdict()
        self.settings.exchange = 'bitflyer'
        self.settings.symbol = 'FX_BTC_JPY'
        self.settings.apiKey = ''
        self.settings.secret = ''

        # 動作タイミング
        self.settings.interval = interval

        # ohlcv設定
        self.settings.timeframe = '1m'
        self.settings.partial = False

        # テストネット設定
        self.testnet = dotdict()
        self.testnet.use = False
        self.testnet.apiKey = ''
        self.testnet.secret = ''

        # リスク設定
        self.risk = dotdict()
        self.risk.max_position_size = 1000
        self.risk.max_drawdown = 5000

        # ポジション情報
        self.position = dotdict()
        self.position.currentQty = 0

        # 注文情報
        self.orders = dotdict()

        # ティッカー情報
        self.ticker = dotdict()

        # ohlcv情報
        self.ohlcv = None
        self.ohlcv_updated = False

        # ログ設定
        self.logger = logging.getLogger(__name__)


    @excahge_error
    def fetch_ticker(self, symbol=None, timeframe=None):
        symbol = symbol or self.settings.symbol
        timeframe = timeframe or self.settings.timeframe
        ticker = dotdict(self.exchange.fetch_ticker(symbol))
        ticker.datetime = pd.to_datetime(ticker.datetime)
        self.logger.info("TICK: last {last} bid {bid} ask {ask}".format(**ticker))
        return ticker

    @excahge_error
    def fetch_ohlcv(self, symbol=None, timeframe=None):
        """過去100件のOHLCVを取得"""
        pass
        # symbol = symbol or self.settings.symbol
        # timeframe = timeframe or self.settings.timeframe
        # partial = 'true' if self.settings.partial else 'false'
        # rsinf = self.resampleInfo[timeframe]
        # market = self.exchange.market(symbol)
        # req = {
        #     'symbol': market['id'],
        #     'binSize': rsinf['binSize'],
        #     'count': rsinf['count'],
        #     'partial': partial,     # True == include yet-incomplete current bins
        #     'reverse': 'false',
        #     'startTime': datetime.utcnow() - (rsinf['delta'] * rsinf['count']),
        # }
        # res = self.exchange.publicGetTradeBucketed(req)
        # df = pd.DataFrame(res)
        # df['timestamp'] = pd.to_datetime(df['timestamp'])
        # df.set_index('timestamp', inplace=True)
        # if rsinf['resample']:
        #     rule = timeframe
        #     rule = rule.replace('m','T')
        #     rule = rule.replace('d','D')
        #     df = df.resample(rule=rule, closed='right').agg({'open':'first','high':'max','low':'min','close':'last','volume':'sum'})
        # self.logger.info("OHLCV: {open} {high} {low} {close} {volume}".format(**df.iloc[-1]))
        # return df

    @excahge_error
    def fetch_position(self, symbol=None):
        """現在のポジションを取得"""
        symbol = symbol or self.settings.symbol
        market = self.exchange.market(symbol)
        req = {'product_code': market['id']}
        res = self.exchange.privateGetGetpositions(req)
        if len(res):
            pos = dotdict(res[0])
            pos.currentQty = pos.size if pos.side == 'BUY' else pos.size * -1
            pos.unrealisedPnl = pos.pnl
        else:
            pos = dotdict()
            pos.currentQty = 0
            pos.unrealisedPnl = 0
        self.logger.info("POSITION: qty {currentQty} pnl {unrealisedPnl}".format(**pos))
        return pos

    @excahge_error
    def fetch_balance(self):
        """資産情報取得"""
        pass
        # balance = dotdict(self.exchange.fetch_balance())
        # balance.BTC = dotdict(balance.BTC)
        # self.logger.info("BALANCE: free {free:.3f} used {used:.3f} total {total:.3f}".format(**balance.BTC))
        # return balance

    @excahge_error
    def close_position(self, symbol=None):
        """現在のポジションを閉じる"""
        pass
        # symbol = symbol or self.settings.symbol
        # market = self.exchange.market(symbol)
        # req = {'symbol': market['id']}
        # res = self.exchange.privatePostOrderClosePosition(req)
        # self.logger.info("CLOSE: {orderID} {side} {orderQty} {price}".format(**res))

    @excahge_error
    def cancel(self, myid, symbol=None):
        """注文をキャンセル"""
        if myid in self.orders:
            symbol = symbol or self.settings.symbol
            try:
                order_id = self.orders[myid].id
                res = self.exchange.cancel_order(id=order_id, symbol=symbol)
                self.logger.info("CANCEL: " + str(order_id))
            except ccxt.OrderNotFound as e:
                self.logger.warning(type(e).__name__ + ": {0}".format(e))
            del self.orders[myid]

    @excahge_error
    def cancel_order_all(self, symbol=None):
        """現在の注文をキャンセル"""
        symbol = symbol or self.settings.symbol
        market = self.exchange.market(symbol)
        req = {'product_code': market['id']}
        res = self.exchange.privatePostCancelallchildorders(req)
        self.logger.info("CANCEL: " + str(res))

    def create_order(self, side, qty, limit, stop, trailing_offset, symbol):
        type = 'market'
        params = {}
        if limit is not None:
            type = 'limit'
        res = self.exchange.create_order(symbol, type, side, qty, limit, params)
        self.logger.info("ORDER: {id}".format(**res))
        return dotdict(res)

    @excahge_error
    def order(self, myid, side, qty, limit=None, stop=None, trailing_offset=None, symbol=None):
        """注文"""

        qty_total = qty
        qty_limit = self.risk.max_position_size

        # 買いポジあり
        if self.position.currentQty > 0:
            # 買い増し
            if side == 'buy':
                # 現在のポジ数を加算
                qty_total = qty_total + self.position.currentQty
            else:
                # 反対売買の場合、ドテンできるように上限を引き上げる
                qty_limit = qty_limit + self.position.currentQty

        # 売りポジあり
        if self.position.currentQty < 0:
            # 売りまし
            if side == 'sell':
                # 現在のポジ数を加算
                qty_total = qty_total + -self.position.currentQty
            else:
                # 反対売買の場合、ドテンできるように上限を引き上げる
                qty_limit = qty_limit + -self.position.currentQty

        # 購入数をポジション最大サイズに抑える
        if qty_total > qty_limit:
            qty = qty - (qty_total - qty_limit)

        if qty > 0:
            symbol = symbol or self.settings.symbol

            if myid in self.orders:
                order_id = self.orders[myid].id
                order = dotdict(self.exchange.fetch_order(order_id, symbol))
                # Todo
                # 1.部分約定の確認
                if order.status == 'open':
                    if ((order.price != limit) or (order.amount != qty)):
                        order = self.exchange.cancel_order(order_id, symbol)
                        order = self.create_order(side, qty, limit, stop, trailing_offset, symbol)
                else:
                    order = self.create_order(side, qty, limit, stop, trailing_offset, symbol)
            else:
                order = self.create_order(side, qty, limit, stop, trailing_offset, symbol)

            self.orders[myid] = order

    def entry(self, myid, side, qty, limit=None, stop=None, trailing_offset=None, symbol=None):
        """注文"""

        # 買いポジションがある場合、清算する
        if side=='sell' and self.position.currentQty > 0:
            qty = qty + self.position.currentQty

        # 売りポジションがある場合、清算する
        if side=='buy' and self.position.currentQty < 0:
            qty = qty - self.position.currentQty

        # 注文
        self.order(myid, side, qty, limit, stop, symbol)

    def update_ohlcv(self, ticker_time=None, force_update=False):
        pass
        # if self.settings.partial or force_update:
        #     self.ohlcv = self.fetch_ohlcv()
        #     self.ohlcv_updated = True
        # else:
        #     # 次に足取得する時間
        #     timestamp = self.ohlcv.index
        #     t0 = timestamp[-1]
        #     t1 = timestamp[-2]
        #     next_fetch_time = t0 + (t0 - t1)
        #     # 足取得
        #     if ticker_time > next_fetch_time:
        #         self.ohlcv = self.fetch_ohlcv()
        #         # 更新確認
        #         timestamp = self.ohlcv.index
        #         if timestamp[-1] >= next_fetch_time:
        #             self.ohlcv_updated = True

    def setup(self):
        # 取引所セットアップ
        self.logger.info("Setup Exchange")
        self.exchange = getattr(ccxt, self.settings.exchange)({
            'apiKey': self.settings.apiKey,
            'secret': self.settings.secret,
            })
        self.exchange.load_markets()

        # マーケット情報表示
        for k, v in self.exchange.markets.items():
            self.logger.info('Markets: ' + v['symbol'])

        # 現在のポジションをすべて閉じる
        self.logger.info("Cancel all orders and close position")
        self.cancel_order_all()
        self.close_position()

    def start(self):
        self.setup()
        if isinstance(self.yourlogic, Trading):
            self.yourlogic.setup(self)

        self.logger.info("Start Trading")

        # 強制足取得
        self.update_ohlcv(force_update=True)

        while True:
            self.interval = self.settings.interval

            try:
                # ティッカー取得
                self.ticker = self.fetch_ticker()

                # ポジション取得
                self.position = self.fetch_position()

                # 資金情報取得
                self.balance = self.fetch_balance()

                # 足取得（足確定後取得）
                #self.update_ohlcv(ticker_time=self.ticker.datetime)

                # メインロジックコール
                arg = {
                    'strategy': self,
                    'ticker': self.ticker,
                    'ohlcv': self.ohlcv,
                    'position': self.position,
                    'balance': self.balance,
                }
                if isinstance(self.yourlogic, Trading):
                    self.yourlogic.loop(**arg)
                else:
                    self.yourlogic(**arg)

                sleep(self.interval)

            except (KeyboardInterrupt, SystemExit):
                self.logger.info('Shutdown!')
                break
            except Exception as e:
                self.logger.exception(e)

        self.logger.info("Stop Trading")

        # 全注文キャンセル
        self.cancel_order_all()

        # ポジションクローズ
        self.close_position()
