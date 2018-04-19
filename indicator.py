# -*- coding: utf-8 -*-
import pandas as pd

# index 0 が最新値、1が1つ前、-1 が最古値であることに注意

def sma(source, period):
    return source.sort_index(ascending=True).rolling(period).mean()

def ema(source, period):
    alpha = 2.0 / (period + 1)
    return source.sort_index(ascending=True).ewm(alpha=alpha).mean()

def rma(source, period):
    alpha = 1.0 / (period)
    return source.sort_index(ascending=True).ewm(alpha=alpha).mean()

def highest(source, period):
    return source.sort_index(ascending=True).rolling(period).max()

def lowest(source, period):
    return source.sort_index(ascending=True).rolling(period).min()

def stdev(source, period):
    return source.sort_index(ascending=True).rolling(period).std()

def rsi(source, period):
    diff = source.sort_index(ascending=True).diff()
    alpha = 1.0 / (period)
    positive = diff.clip_lower(0).ewm(alpha=alpha).mean()
    negative = diff.clip_upper(0).ewm(alpha=alpha).mean()
    rsi = 100-100/(1-positive/negative)
    return rsi

def stoch(close, high, low, period):
    hline = high.sort_index(ascending=True).rolling(period).max()
    lline = low.sort_index(ascending=True).rolling(period).min()
    close = close.sort_index(ascending=True)
    return 100 * (close - lline) / (hline - lline)

def momentum(source, period):
    return source.sort_index(ascending=True).diff(period)

def bbands(source, period, mult=2):
    source = source.sort_index(ascending=True)
    middle = source.rolling(period).mean()
    sigma = source.rolling(period).std()
    upper = middle+sigma*mult
    lower = middle-sigma*mult
    return (upper, lower, middle, sigma)

def macd(source, fastlen, slowlen, siglen):
    source = source.sort_index(ascending=True)
    macd = source.ewm(span=fastlen).mean() - source.ewm(span=slowlen).mean()
    signal = macd.rolling(siglen).mean()
    return (macd, signal)

def hlband(source, period):
    source = source.sort_index(ascending=True)
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
    close = close.sort_index(ascending=True)
    low = low.sort_index(ascending=True)

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
    close = close.sort_index(ascending=True)
    high = high.sort_index(ascending=True)

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


if __name__ == '__main__':

    # import numpy as np

    # p0 = 8000 #初期値
    # vola = 15.0 #ボラティリティ(%)
    # dn = np.random.randint(2, size=1000)*2-1
    # scale = vola/100/np.sqrt(365*24*60)
    # gwalk = np.cumprod(np.exp(scale*dn))*p0
    # data = pd.Series(gwalk)

    data = pd.read_csv('latest.csv', index_col='timestamp', parse_dates=True)

    vsma = sma(data.close, 10)
    vema = ema(data.close, 10)
    vrma = rma(data.close, 10)
    vrsi = rsi(data.close, 14)
    vstoch = stoch(vrsi, vrsi, vrsi, 14)
    (vwvf, lowerBand, upperBand, rangeHigh, rangeLow) = wvf(data.close, data.high, data.low)

    df = pd.DataFrame({
        'close':data.close,
        'sma':vsma,
        'ema':vema,
        'rma':vrma,
        'rsi':vrsi,
        'stochrsi':vstoch,
        'wvf':vwvf,
        'wvf-upper':lowerBand,
        'wvf-lower':lowerBand,
        }, index=data.index)
    print(df.to_csv())
