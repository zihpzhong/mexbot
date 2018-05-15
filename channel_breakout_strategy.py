# -*- coding: utf-8 -*-
from indicator import *

# ロット計算用資産比
percent = 0.3

# ブレイクアウト期間
breakout_in = 22
breakout_out = 6

def channel_breakout_strategy(ticker, ohlcv, position, balance, strategy):

    # エントリー/エグジット
    long_entry_price = last(highest(ohlcv.high, breakout_in)) + 0.5
    short_entry_price = last(lowest(ohlcv.low, breakout_in)) - 0.5

    long_exit_price = last(lowest(ohlcv.low, breakout_out)) - 0.5
    short_exit_price = last(highest(ohlcv.high, breakout_out)) + 0.5

    sma_filter = last(sma(ohlcv.close, 25))
    close = last(ohlcv.close)

    # ロット数計算
    qty_lot = int(balance.BTC.free * percent * ticker.last)
    logger.info("LOT: " + str(qty_lot))

    # 最大ポジション数設定
    strategy.risk.max_position_size = qty_lot

    # 注文
    if position.currentQty > 0:
        strategy.order('L_exit', side='sell', qty=position.currentQty, limit=min(long_exit_price, ticker.ask), stop=long_exit_price)
        strategy.ohlcv_updated = False
    elif position.currentQty < 0:
        strategy.order('S_exit', side='buy', qty=-position.currentQty, limit=max(short_exit_price, ticker.bid), stop=short_exit_price)
        strategy.ohlcv_updated = False
    else:
        if strategy.ohlcv_updated:
            if close > sma_filter:
                logger.info("Filter: " + str(close) + " > " + str(sma_filter))
                strategy.order('L', 'buy', qty=qty_lot, limit=max(long_entry_price, ticker.bid), stop=long_entry_price)
                strategy.cancel('S')
            if close < sma_filter:
                logger.info("Filter: " + str(close) + " < " + str(sma_filter))
                strategy.order('S', 'sell', qty=qty_lot, limit=min(short_entry_price, ticker.ask), stop=short_entry_price)
                strategy.cancel('L')
        else:
            logger.info("Waiting for OHLCV update...")


if __name__ == '__main__':
    import argparse
    from strategy import Strategy
    import settings
    import logging
    import logging.config

    strategy = Strategy(channel_breakout_strategy)
    strategy.settings.timeframe = '5m'
    strategy.settings.interval = 10
    strategy.settings.apiKey = settings.apiKey
    strategy.settings.secret = settings.secret
    strategy.testnet.use = False
    strategy.testnet.apiKey = settings.testnet_apiKey
    strategy.testnet.secret = settings.testnet_secret

    parser = strategy.add_arguments(argparse.ArgumentParser(description='Channel Breakout Bot'))
    parser.add_argument('--parameter', nargs=3, type=int, default=[breakout_in, breakout_out])
    parser.add_argument('--percent', type=float, default=percent)
    args = parser.parse_args()

    logging.config.dictConfig(
        settings.loggingConf('chbrk-bot-' + args.symbol.replace('/','_').lower() + '.log'))
    logger = logging.getLogger('ChbrkBot')

    breakout_in = args.parameter[0]
    breakout_out = args.parameter[1]
    percent = args.percent

    strategy.start(args)
