# -*- coding: utf-8 -*-
import pandas as pd
import numpy as np
from functools import lru_cache

def sma(source, period):
    return source.rolling(int(period)).mean()

def ema(source, period):
    # alpha = 2.0 / (period + 1)
    return source.ewm(span=period).mean()

def rma(source, period):
    alpha = 1.0 / (period)
    return source.ewm(alpha=alpha).mean()

def highest(source, period):
    return source.rolling(int(period)).max()

def lowest(source, period):
    return source.rolling(int(period)).min()

def stdev(source, period):
    return source.rolling(int(period)).std()

def rsi(source, period):
    diff = source.diff()
    alpha = 1.0 / (period)
    positive = diff.clip_lower(0).ewm(alpha=alpha).mean()
    negative = diff.clip_upper(0).ewm(alpha=alpha).mean()
    rsi = 100-100/(1-positive/negative)
    return rsi

def stoch(close, high, low, period):
    period = int(period)
    hline = high.rolling(period).max()
    lline = low.rolling(period).min()
    return 100 * (close - lline) / (hline - lline)

def momentum(source, period):
    return source.diff(int(period))

def bband(source, period, mult=2.0):
    period = int(period)
    middle = source.rolling(period).mean()
    sigma = source.rolling(period).std()
    upper = middle+sigma*mult
    lower = middle-sigma*mult
    return (upper, lower, middle, sigma)

def macd(source, fastlen, slowlen, siglen, use_sma=False):
    if use_sma:
        macd = source.rolling(int(fastlen)).mean() - source.rolling(int(slowlen)).mean()
    else:
        macd = source.ewm(span=fastlen).mean() - source.ewm(span=slowlen).mean()
    signal = macd.rolling(int(siglen)).mean()
    return (macd, signal, macd-signal)

def hlband(source, period):
    period = int(period)
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
    bbl = int(bbl)
    lb = int(lb)
    period = int(period)
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
    bbl = int(bbl)
    lb = int(lb)
    period = int(period)
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
    last = close.shift(1).fillna(close[0])
    tr = high - low
    diff_hc = (high - last).abs()
    diff_lc = (low - last).abs()
    tr[diff_hc > tr] = diff_hc
    tr[diff_lc > tr] = diff_lc
    return tr

def atr(close, high, low, period):
    last = close.shift(1).fillna(close[0])
    tr = high - low
    diff_hc = (high - last).abs()
    diff_lc = (low - last).abs()
    tr[diff_hc > tr] = diff_hc
    tr[diff_lc > tr] = diff_lc
    return tr.ewm(alpha=1.0/period).mean()

def crossover(a, b):
    cond1 = (a > b)
    return cond1 & (~cond1).shift(1)

def crossunder(a, b):
    cond1 = (a < b)
    return cond1 & (~cond1).shift(1)

def last(source, period=0):
    """
    last(close)     現在の足
    last(close, 0)  現在の足
    last(close, 1)  1つ前の足
    """
    return source.iat[-1-int(period)]

def pivothigh(source, leftbars, rightbars):
    leftbars = int(leftbars)
    rightbars = int(rightbars)
    high = source.rolling(leftbars).max()
    diff = high.diff()
    pvhi = pd.Series(high[diff >= 0], index=source.index)
    return pvhi.shift(rightbars) if rightbars > 0 else pvhi

def pivotlow(source, leftbars, rightbars):
    leftbars = int(leftbars)
    rightbars = int(rightbars)
    low = source.rolling(leftbars).min()
    diff = low.diff()
    pvlo = pd.Series(low[diff <= 0], index=source.index)
    return pvlo.shift(rightbars) if rightbars > 0 else pvlo

def sar(high, low, start, inc, max):
    index = high.index
    high = high.values
    low = low.values
    n = len(high)
    sar = np.zeros(n)
    sar[0] = low[0]
    ep = high[0]
    acc = start
    long = True
    for i in range(1, n):
        sar[i] = sar[i-1] + acc * (ep - sar[i-1])
        if long:
            if high[i] > ep:
                ep = high[i]
                if acc < max:
                    acc += inc
            if sar[i] > low[i]:
                long = False
                acc = start
                sar[i] = ep
        else:
            if low[i] < ep:
                ep = low[i]
                if acc < max:
                    acc += inc
            if sar[i] < high[i]:
                long = True
                acc = start
                sar[i] = ep
    return pd.Series(sar, index=index)

def minimum(a, b, period):
    c = a.copy()
    c[a > b] = b
    return c.rolling(int(period)).min()

def maximum(a, b, period):
    c = a.copy()
    c[a < b] = b
    return c.rolling(int(period)).max()

@lru_cache(maxsize=None)
def fib(n):
    n = int(n)
    fib = [0] * n
    fib[1] = 1
    for i in range(2, n):
        fib[i] = fib[i-2] + fib[i-1]
    return pd.Series(fib)

@lru_cache(maxsize=None)
def fibratio(n):
    n = int(n)
    f = fib(n)
    return f / f.iat[n-1]

if __name__ == '__main__':

    from functools import wraps
    import time
    def stop_watch(func) :
        @wraps(func)
        def wrapper(*args, **kargs) :
            start = time.time()
            result = func(*args,**kargs)
            process_time =  (time.time() - start)*10000
            print(f"{func.__name__} は {process_time:.3f} ミリ秒かかりました")
            return result
        return wrapper

    # import numpy as np

    # p0 = 8000 #初期値
    # vola = 15.0 #ボラティリティ(%)
    # dn = np.random.randint(2, size=1000)*2-1
    # scale = vola/100/np.sqrt(365*24*60)
    # gwalk = np.cumprod(np.exp(scale*dn))*p0
    # data = pd.Series(gwalk)

    ohlc = pd.read_csv('csv/bitmex_2018_1h.csv', index_col='timestamp', parse_dates=True)

    sma = stop_watch(sma)
    ema = stop_watch(ema)
    rma = stop_watch(rma)
    rsi = stop_watch(rsi)
    stoch = stop_watch(stoch)
    wvf = stop_watch(wvf)
    highest = stop_watch(highest)
    lowest = stop_watch(lowest)
    macd = stop_watch(macd)
    tr = stop_watch(tr)
    atr = stop_watch(atr)
    pivothigh = stop_watch(pivothigh)
    pivotlow = stop_watch(pivotlow)
    pivotlow = stop_watch(pivotlow)
    sar = stop_watch(sar)
    minimum = stop_watch(minimum)
    maximum = stop_watch(maximum)

    vsma = sma(ohlc.close, 10)
    vema = ema(ohlc.close, 10)
    vrma = rma(ohlc.close, 10)
    vrsi = rsi(ohlc.close, 14)
    vstoch = stoch(vrsi, vrsi, vrsi, 14)
    (vwvf, lowerBand, upperBand, rangeHigh, rangeLow) = wvf(ohlc.close, ohlc.low)
    vhighest = highest(ohlc.high, 14)
    vlowest = lowest(ohlc.low, 14)
    (vmacd, vsig, vhist) = macd(ohlc.close, 9, 26, 5)
    vtr = tr(ohlc.close, ohlc.high, ohlc.low)
    vatr = atr(ohlc.close, ohlc.high, ohlc.low, 14)
    vpivoth = pivothigh(ohlc.high, 4, 2).ffill()
    vpivotl = pivotlow(ohlc.low, 4, 2).ffill()
    vsar = sar(ohlc.high, ohlc.low, 0.02, 0.02, 0.2)
    vmin = minimum(ohlc.open, ohlc.close, 14)
    vmax = maximum(ohlc.open, ohlc.close, 14)
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
        'sar':vsar,
        'min':vmin,
        'max':vmax,
        }, index=ohlc.index)
    print(df.to_csv())
