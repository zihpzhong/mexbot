# -*- coding: utf-8 -*-
from indicator import *
from utils import reloadable_jsondict

params = reloadable_jsondict('params/macd_cross_params.json')

def macd_cross_strategy(ticker, ohlcv, position, balance, strategy):

    # パラメータ更新チェック
    prm = params.reload()[strategy.settings.symbol]
    if params.reloaded:
        logger.info('PARAM reloaded {fastlen} {slowlen} {siglen} {percent}'.format(**prm))
        params.reloaded = False

    # インジケーター作成
    vmacd, vsig, vhist = macd(ohlcv.close, prm.fastlen, prm.slowlen, prm.siglen, use_sma=True)

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
        qty_lot = int(balance.BTC.total * prm.percent / ticker.last)
    else:
        qty_lot = int(balance.BTC.total * prm.percent * ticker.last)
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
    args = parser.parse_args()

    logging.config.dictConfig(settings.loggingConf(params[args.symbol].logfilename))
    logger = logging.getLogger('MACDCrossBot')

    strategy.start(args)
