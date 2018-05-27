# -*- coding: utf-8 -*-
from indicator import *

# インディケータ期間
fastlen = 19
slowlen = 27
siglen = 13

# ロット計算用資産比
percent = 0.25

def macd_cross_strategy(ticker, ohlcv, position, balance, strategy):

    # インジケーター作成
    vmacd, vsig, vhist = macd(ohlcv.close, fastlen, slowlen, siglen, use_sma=True)

    # エントリー／イグジット
    long_entry = last(crossover(vmacd, vsig))
    short_entry = last(crossunder(vmacd, vsig))
    if long_entry:
        side = 'buy'
    elif short_entry:
        side = 'sell'
    else:
        side = 'none'
    logger.info('MACD {0} Signal {1} Trigger {2}'.format(last(vmacd), last(vsig), side))

    # ロット数計算
    quote = strategy.exchange.market(strategy.settings.symbol)['quote']
    if quote == 'BTC':
        qty_lot = int(balance.BTC.free * percent / ticker.last)
    else:
        qty_lot = int(balance.BTC.free * percent * ticker.last)
    logger.info('LOT: ' + str(qty_lot))

    # 最大ポジション数設定
    strategy.risk.max_position_size = qty_lot

    # 注文（ポジションがある場合ドテン）
    if long_entry:
        strategy.entry('L', 'buy', qty=qty_lot, limit=ticker.bid)
    else:
        strategy.cancel('L')

    if short_entry:
        strategy.entry('S', 'sell', qty=qty_lot, limit=ticker.ask)
    else:
        strategy.cancel('S')


if __name__ == '__main__':
    import argparse
    from strategy import Strategy
    import settings
    import logging
    import logging.config

    strategy = Strategy(macd_cross_strategy)
    strategy.settings.timeframe = '1h'
    strategy.settings.interval = 60
    strategy.settings.apiKey = settings.apiKey
    strategy.settings.secret = settings.secret
    strategy.testnet.use = True
    strategy.testnet.apiKey = settings.testnet_apiKey
    strategy.testnet.secret = settings.testnet_secret

    parser = strategy.add_arguments(argparse.ArgumentParser(description='MACD Cross Bot'))
    parser.add_argument('--parameter', nargs=3, type=int, default=[fastlen, slowlen, siglen])
    parser.add_argument('--percent', type=float, default=percent)
    args = parser.parse_args()

    logging.config.dictConfig(
        settings.loggingConf('macd-cross-bot-' + args.symbol.replace('/','_').lower() + '.log'))
    logger = logging.getLogger('MACDCrossBot')

    fastlen = args.parameter[0]
    slowlen = args.parameter[1]
    siglen = args.parameter[2]
    percent = args.percent

    strategy.start(args)
