import hashlib
import hmac
import json
import os
from datetime import datetime, timedelta
from time import sleep

import numpy as np
import requests
from dotenv import load_dotenv
from talib import SAR, SMA

load_dotenv()

SYMBOL = "BTCUSDT"
INTERVAL = 15  # 1,5,15,30,60
SMA_SHORT = 30
SMA_LONG = 100
URL = "https://api.bybit.com"


def add_log(text):
    with open("log.txt", "a") as log_file:
        log_file.write(f"{datetime.now()} {text}\n")


def get_klines():
    url = f"{URL}/derivatives/v3/public/kline"
    now = datetime.now()
    params = {
        "symbol": SYMBOL,
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
            add_log(e)


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


def generate_signature(payload, timestamp, recv_window):
    param_str = timestamp + os.getenv("API_KEY") + recv_window + payload
    hash = hmac.new(bytes(os.getenv("API_SECRET"), "utf-8"), param_str.encode("utf-8"), hashlib.sha256)
    signature = hash.hexdigest()
    return signature


def get_headers(params):
    timestamp = str(int(datetime.now().timestamp() * 1000))
    recv_window = str(5000)
    return {
        "X-BAPI-API-KEY": os.getenv("API_KEY"),
        "X-BAPI-SIGN-TYPE": "2",
        "X-BAPI-TIMESTAMP": timestamp,
        'X-BAPI-RECV-WINDOW': recv_window,
        "X-BAPI-SIGN": generate_signature(params, timestamp, recv_window),
    }


def place_order(side):
    url = f"{URL}/v5/order/create"
    body = json.dumps({
        "category": "linear",
        "symbol": SYMBOL,
        "side": side,
        "orderType": "Market",
        "qty": str(0),
        "reduceOnly": True,
        "closeOnTrigger": True,
    }, separators=(',', ':'))

    response = requests.post(url, data=body, headers=get_headers(body))

    body = json.dumps({
        "category": "linear",
        "symbol": SYMBOL,
        "side": side,
        "orderType": "Market",
        "qty": str(0.001),
    }, separators=(',', ':'))

    response = requests.post(url, data=body, headers=get_headers(body))

    return "success"


def main():
    klines = get_klines()
    opens, highs, lows, closes, volumes = get_ohlcv(klines)

    # sma_short = SMA(closes, timeperiod=SMA_SHORT)
    # sma_long = SMA(closes, timeperiod=SMA_LONG)
    psar = SAR(highs, lows)

    if closes[-2] < psar[-2] and closes[-1] > psar[-1]:
        if place_order("Buy") == "success":
            print(datetime.fromtimestamp(int(klines[-1][0][:-3])), "buy on", klines[-1][4])
            add_log("Buy")
            return
    elif closes[-2] > psar[-2] and closes[-1] < psar[-1]:
        if place_order("Sell") == "success":
            print(datetime.fromtimestamp(int(klines[-1][0][:-3])), "sell on", klines[-1][4])
            add_log("Sell")
            return
    else:
        print(datetime.fromtimestamp(int(klines[-1][0][:-3])), "working..")
        add_log("Working..")
        return


if __name__ == "__main__":
    while True:
        now = datetime.now()
        if now.second % 60 == 0 and now.minute % INTERVAL == 0:
            try:
                main()
            except Exception as e:
                print(e)
                add_log(e)
        sleep(1)
