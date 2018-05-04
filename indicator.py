# -*- coding: utf-8 -*-
import pandas as pd

def sma(source, period):
    return source.rolling(period).mean()

def ema(source, period):
    # alpha = 2.0 / (period + 1)
    return source.ewm(span=period).mean()

def rma(source, period):
    alpha = 1.0 / (period)
    return source.ewm(alpha=alpha).mean()

def highest(source, period):
    return source.rolling(period).max()

def lowest(source, period):
    return source.rolling(period).min()

def stdev(source, period):
    return source.rolling(period).std()

def rsi(source, period):
    diff = source.diff()
    alpha = 1.0 / (period)
    positive = diff.clip_lower(0).ewm(alpha=alpha).mean()
    negative = diff.clip_upper(0).ewm(alpha=alpha).mean()
    rsi = 100-100/(1-positive/negative)
    return rsi

def stoch(close, high, low, period):
    hline = high.rolling(period).max()
    lline = low.rolling(period).min()
    return 100 * (close - lline) / (hline - lline)

def momentum(source, period):
    return source.diff(period)

def bband(source, period, mult=2):
    middle = source.rolling(period).mean()
    sigma = source.rolling(period).std()
    upper = middle+sigma*mult
    lower = middle-sigma*mult
    return (upper, lower, middle, sigma)

def macd(source, fastlen, slowlen, siglen):
    macd = source.ewm(span=fastlen).mean() - source.ewm(span=slowlen).mean()
    signal = macd.rolling(siglen).mean()
    return (macd, signal, macd-signal)

def hlband(source, period):
    high = source.rolling(period).max()
    low = source.rolling(period).min()
    return (high, low)

def wvf(close, low, period = 22, bbl = 20, mult = 2.0, lb = 50, ph = 0.85, pl=1.01):
    """
    period: LookBack Period Standard Deviation High
    bbl:    Bolinger Band Length
    mult:   Bollinger Band Standard Devaition Up
    lb:     Look Back Period Percentile High
    ph:     Highest Percentile - 0.90=90%, 0.95=95%, 0.99=99%
    pl:     Lowest Percentile - 1.10=90%, 1.05=95%, 1.01=99%
    """

    # VixFix
    close_max = close.rolling(period).max()
    wvf = ((close_max - low) / close_max) * 100

    sDev = mult * wvf.rolling(bbl).std()
    midLine = wvf.rolling(bbl).mean()
    lowerBand = midLine - sDev
    upperBand = midLine + sDev
    rangeHigh = wvf.rolling(lb).max() * ph
    rangeLow = wvf.rolling(lb).min() * pl
    return (wvf, lowerBand, upperBand, rangeHigh, rangeLow)

def wvf_inv(close, high, period = 22, bbl = 20, mult = 2.0, lb = 50, ph = 0.85, pl=1.01):
    """
    period: LookBack Period Standard Deviation High
    bbl:    Bolinger Band Length
    mult:   Bollinger Band Standard Devaition Up
    lb:     Look Back Period Percentile High
    ph:     Highest Percentile - 0.90=90%, 0.95=95%, 0.99=99%
    pl:     Lowest Percentile - 1.10=90%, 1.05=95%, 1.01=99%
    """

    # VixFix_inverse
    close_min = close.rolling(period).min()
    wvf_inv = abs(((close_min - high) / close_min) * 100)

    sDev = mult * wvf_inv.rolling(bbl).std()
    midLine = wvf_inv.rolling(bbl).mean()
    lowerBand = midLine - sDev
    upperBand = midLine + sDev
    rangeHigh = wvf_inv.rolling(lb).max() * ph
    rangeLow = wvf_inv.rolling(lb).min() * pl
    return (wvf_inv, lowerBand, upperBand, rangeHigh, rangeLow)

def tr(close, high, low):
    diff_hl = high - low
    last = close.shift(1).fillna(close[0])
    diff_hc = high - last
    diff_hc = diff_hc.abs()
    diff_lc = low - last
    diff_lc = diff_lc.abs()
    tr = diff_hl
    sel = diff_hc > tr
    tr[sel] = diff_hc[sel]
    sel = diff_lc > tr
    tr[sel] = diff_lc[sel]
    return tr

def atr(close, high, low, period):
    alpha = 1.0 / (period)
    return tr(close, high, low).ewm(alpha=alpha).mean()

def crossover(a, b):
    return (a > b) & (b > a.shift(1))

def crossunder(a, b):
    return (a < b) & (b < a.shift(1))

def last(source, period=0):
    """
    last(close)     現在の足
    last(close, 0)  現在の足
    last(close, 1)  1つ前の足
    """
    return source.iat[-1-period]

def pivothigh(source, leftbars, rightbars):
    high = source.rolling(leftbars).max()
    diff = high.diff()
    pvhi = pd.Series(high[diff >= 0], index=source.index)
    return pvhi.shift(rightbars) if rightbars > 0 else pvhi

def pivotlow(source, leftbars, rightbars):
    low = source.rolling(leftbars).min()
    diff = low.diff()
    pvlo = pd.Series(low[diff <= 0], index=source.index)
    return pvlo.shift(rightbars) if rightbars > 0 else pvlo

if __name__ == '__main__':

    # import numpy as np

    # p0 = 8000 #初期値
    # vola = 15.0 #ボラティリティ(%)
    # dn = np.random.randint(2, size=1000)*2-1
    # scale = vola/100/np.sqrt(365*24*60)
    # gwalk = np.cumprod(np.exp(scale*dn))*p0
    # data = pd.Series(gwalk)

    ohlc = pd.read_csv('csv/bitmex_20180419_1m.csv', index_col='timestamp', parse_dates=True)

    vsma = sma(ohlc.close, 10)
    vema = ema(ohlc.close, 10)
    vrma = rma(ohlc.close, 10)
    vrsi = rsi(ohlc.close, 14)
    vstoch = stoch(vrsi, vrsi, vrsi, 14)
    (vwvf, lowerBand, upperBand, rangeHigh, rangeLow) = wvf(ohlc.close, ohlc.low)
    vhighest = highest(ohlc.high, 14)
    vlowest = lowest(ohlc.low, 14)
    (vmacd, vsig) = macd(ohlc.close, 9, 26, 5)
    vtr = tr(ohlc.close, ohlc.high, ohlc.low)
    vatr = atr(ohlc.close, ohlc.high, ohlc.low, 14)
    vpivoth = pivothigh(ohlc.high, 4, 2).ffill()
    vpivotl = pivotlow(ohlc.low, 4, 2).ffill()

    df = pd.DataFrame({
        'high':ohlc.high,
        'low':ohlc.low,
        'close':ohlc.close,
        'sma':vsma,
        'ema':vema,
        'rma':vrma,
        'rsi':vrsi,
        'stochrsi':vstoch,
        'wvf':vwvf,
        'wvf-upper':upperBand,
        'wvf-lower':lowerBand,
        'wvf-high':rangeHigh,
        'wvf-low':rangeLow,
        'highest':vhighest,
        'lowest':vlowest,
        'macd':vmacd,
        'macd-signal':vsig,
        'tr':vtr,
        'atr':vatr,
        'pivot high':vpivoth,
        'pivot low':vpivotl,
        }, index=ohlc.index)
    print(df.to_csv())
