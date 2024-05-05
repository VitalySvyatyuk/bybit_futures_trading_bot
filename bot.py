from datetime import datetime, timedelta
from time import sleep

import numpy as np
import requests
from dotenv import load_dotenv
from talib import SMA

load_dotenv()

INTERVAL = 1  # 1,5,15,30,60
SMA_SHORT = 4
SMA_LONG = 12
URL = "https://api.bybit.com"


def get_klines(symbol="BTCUSDT"):
    url = f"{URL}/derivatives/v3/public/kline"
    now = datetime.now()
    params = {
        "symbol": symbol,
        "interval": INTERVAL,
        "start": int((now - timedelta(seconds=60 * INTERVAL * (SMA_LONG + 1))).timestamp()) * 1000,
        "end": int(now.timestamp()) * 1000,
    }
    while True:
        try:
            response = requests.get(url, params=params)
            klines = response.json()["result"]["list"][::-1]
            if datetime.fromtimestamp(int(klines[-1][0][:-3])).minute != datetime.now().minute:
                sleep(1)
                continue
            return klines[:-1]
        except Exception as e:
            print(e)


def get_ohlcv(klines):
    opens = []
    highs = []
    lows = []
    closes = []
    volumes = []
    for kline in klines:
        opens.append(kline[1])
        highs.append(kline[2])
        lows.append(kline[3])
        closes.append(kline[4])
        volumes.append(kline[5])
    return (
        np.array(opens, dtype="f8"),
        np.array(highs, dtype="f8"),
        np.array(lows, dtype="f8"),
        np.array(closes, dtype="f8"),
        np.array(volumes, dtype="f8"),
    )


def main():
    klines = get_klines()
    opens, highs, lows, closes, volumes = get_ohlcv(klines)

    sma_short = SMA(closes, timeperiod=SMA_SHORT)
    sma_long = SMA(closes, timeperiod=SMA_LONG)

    if sma_short[-2] <= sma_long[-2] and sma_short[-1] >= sma_long[-1]:
        print(datetime.fromtimestamp(int(klines[-1][0][:-3])), "buy on", klines[-1][4])
    elif sma_short[-2] >= sma_long[-2] and sma_short[-1] <= sma_long[-1]:
        print(datetime.fromtimestamp(int(klines[-1][0][:-3])), "sell on", klines[-1][4])
    else:
        print(datetime.fromtimestamp(int(klines[-1][0][:-3])), "working..")


if __name__ == "__main__":
    while True:
        now = datetime.now()
        if now.second % 60 == 0 and now.minute % INTERVAL == 0:
            main()
        sleep(1)
