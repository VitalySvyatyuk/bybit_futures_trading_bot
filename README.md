Bybit Futures Trading Bot

Trading bot to trade in Bybit futures. By default, BTCUSDT is used. 

The strategy is pretty simple:
- buy when short SMA crosses long SMA up
- sell when short SMA crosses short SMA down

You can update SMA_SHORT and SMA_LONG in the `bot.py`, remember, SMA_LONG always should be higher than SMA_SHORT.
The price is set as 0.001 ($65) by default. You can change the leverage on the Bybit site. No stop losses or take profits for now.

Do you have a strategy you want to implement? Ping me.