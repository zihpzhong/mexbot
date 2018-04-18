# -*- coding: utf-8 -*-
import pandas as pd

# index 0 が最新値、1が1つ前、-1 が最古値であることに注意

def sma(source, window):
    return source[-1::-1].rolling(window).mean()

def ema(source, window):
    alpha = 2.0 / (window + 1)
    return source[-1::-1].ewm(alpha=alpha).mean()

def rma(source, window):
    alpha = 1.0 / (window)
    return source[-1::-1].ewm(alpha=alpha).mean()

def highest(source, window):
    return source[-1::-1].rolling(window).max()

def lowest(source, window):
    return source[-1::-1].rolling(window).min()

def stdev(source, window):
    return source[-1::-1].rolling(window).std()

def rsi(source, window):
    diff = source[-1::-1].diff()
    alpha = 1.0 / (window)
    positive = diff.clip_lower(0).ewm(alpha=alpha).mean()
    negative = diff.clip_upper(0).ewm(alpha=alpha).mean()
    rsi = 100-100/(1-positive/negative)
    return rsi

def stoch(close, high, low, window):
    hline = high[-1::-1].rolling(window).max()
    lline = low[-1::-1].rolling(window).min()
    close = close[-1::-1]
    return 100 * (close - lline) / (hline - lline)

def momentum(source, window):
    return source[-1::-1].diff(window)

def bband(source ,window, deviation=2):
    source = source[-1::-1]
    base = source.rolling(window).mean()
    sigma = source.rolling(window).std()
    upper = base+sigma*deviation
    lower = base-sigma*deviation
    return (upper, lower, base, sigma)

def macd(source, fastwin, slowwin, sigwin):
    source = source[-1::-1]
    macd = source.ewm(span=fastwin).mean() - source.ewm(span=slowwin).mean()
    signal = macd.rolling(sigwin).mean()
    return (macd, signal)

def hlband(source, window):
    source = source[-1::-1]
    return (source.rolling(window).max(), source.rolling(window).min())

if __name__ == '__main__':

    import numpy as np

    p0 = 8000 #初期値
    vola = 15.0 #ボラティリティ(%)
    dn = np.random.randint(2, size=1000)*2-1
    scale = vola/100/np.sqrt(365*24*60)
    gwalk = np.cumprod(np.exp(scale*dn))*p0
    data = pd.Series(gwalk)

    vsma = sma(data, 10)
    vema = ema(data, 10)
    vrma = rma(data, 10)
    vrsi = rsi(data, 14)

    df = pd.DataFrame({
        'data':data,
        'sma':vsma,
        'ema':vema,
        'rma':vrma,
        'rsi':vrsi
        })
    print(df.to_csv())
