# Binance Trading Bot 
This repo is no longer supported.

## Overview
A crypto trading bot, using Binance exchange futures market.

This is a bot that's written in Java that buys and sells cryptocurrency using Binance's API, managing user balances and dispalys information.
This project incorporate multiple threads, use of WebSocket and Rest APIs and object-oriented programming.
It required research on cryptocurrency strategies and their employment in Java with Binance's API.

## Strategies
The bot acquires the 150 most recent candles from Binance based on the symbol typed in by the user, and then runs on one or more from the strategies described below. It will try to buy in the right time as defined by the strategy and sell as well. 
Methodolodgy - each entry strategy corresponds to its similary-named exit strategies. For example, RSI entry strategy will enter into position that listens on the four possible RSI exit strategies.

### Entry strategies
1. [Relative Strength Index (RSI)](https://www.investopedia.com/terms/r/rsi.asp) with 9 candles.
* To enter position the RSI needs to cross 27,30 and 35 fast (last 2 close candles).
2. [Long MACD Over RSI](https://www.investopedia.com/terms/m/macd.asp) with 9 rsi values, fast bar: 14, slow bar: 24.
* If the price is above SMA 100, we need or that macd over rsi value crossed zero upwards, or we have a three negative downwards pyramid.
3. [Short MACD Over RSI](https://www.investopedia.com/terms/m/macd.asp)
* If the price is below SMA 100, we need that macd over rsi value crossed zero downwards or that we have three positive upwards pyramid.

The Long MACD and Short MACD are in the same class, while the RSI is in its own class.

### Exit strategies
1. Four possible RSI Exit strategies.
* Cross 65 and until 73 up -> cross 60 down (selling 50% of position) -> cross 50 down (selling all position).
* Cross 73 up -> cross 70 down (selling 40% of position) -> cross 60 down (selling all position).
* The RSI loses a value of at least 15 in the last 2 candles (including the open one) - selling all position
* Crossing 30 down (selling all position), safety net.
2. Five possible Long MACD Over RSI strategies.
* Current price below SMA 100 -> Market
* Crossing the zero line downwards -> Limit
* Not currently trailing -> If we have three positive candles downwards pyramid, activate trailing. Currently trailing -> two positive candles pyramid, deactivate trailing. Currently trailing -> If we need to sell by our trailing rules -> sell. 
* Not currently trailing -> If we have three negative downwards pyramid, activate trailing. Not currenly trailing -> three negative candle values and the current candle is not bigger than the prev, deactivate trailing. Not Currently trailing -> If we need to sell by trailing rules -> sell.
* Safety net.
3. Five possible Short MACD Over RSI strategies.
* Current price above SMA 100 -> Market
* Crossing the zero line upwards -> Limit
* Not currently trailing -> If we have three negative downwards pyramid, activate trailing. Currently trailing ->  if the current candle is bigger than the previous and are both negative, deactivate trailing. Not currently trailing -> If we need to sell by our trailing rules -> sell.
* Not currently trailing -> If we have three positive upwards pyramid, activate trailing. Currently trailing -> if the current candle is not bigger than the previous one and are positive, deactivate trailing. Not currently trailing -> If we need to sell by our own trailing rules -> sell.
* Saftety net.

## Project structure
We have 6 packages in our project:
1. codeExecution - The code runner. Expects user input, creates the investment manager. Basically starts the bot.
2. data - Holds the real time data, which is the main object that holds the candles, calculate indicators more. the package also has account balance which manages the account. The DataHolder class holds the box of information that's needed for each strategy, used for thread-safe implementaion.
3. positions - Holds the position handler - which handles the current position and listen on the exit strategies. Selling instructions is the class that has the information we need for selling.
4. singleton Helpers - Helper package that contains singleton classes that we use in our project.
5. strategies - holds the main logic of the bot. Has the entry and exit strategies of rsi, long macd, short macd and useful constants.
6. utils - Contains common utility functions and time constants.

The Main.java files instantiate the necessary classes to boot and starts the code that's present in codeExecution.

## How to run
1. **Connect to your Binance account:**
In order to connect the bot to your balance in Binance, you need to change the variables API_KEY, SECRET_KEY in the Config class that's present in the data package.
The bot will receive all of your information and will manage it and hopefully will earn you money!

2. **Set up the telegram messenger:**
In order to run the bot, the Telegram Messenger class should contain the right attributes. The Telegram Messenger will send you updates about the bot's actions, for example if the bot is entering position, you will be notified straight away in the Telegeram App.
To do that, you need to change the TELEGRAM_API_KEY and TELEGRAM_CHAT_ID variables to your liking in the Config class that's present in the data package.
A guide on how to get these values: https://www.siteguarding.com/en/how-to-get-telegram-bot-api-token.

Variables to change for 1 and 2 in data.Config class:
```
public static String API_KEY = "<Your binance api key>";
public static String SECRET_KEY = "<Your binance secret key>";
public static String TELEGRAM_API_TOKEN= "<Your telegram bot api token>";
public static String TELEGRAM_CHAT_ID = "<Your telegram group chat id>";
```

3. **Possible command values:**
In order to run the bot, **you need to press "help" to view all the possible commands the bot offers.**
* [symbol] - binance legal symbol, for example: btcusdt
* [interval] - the candlestick interval, possible values: 1m, 3m, 5m, 15m, 30m, 1h, 2h, 4h, 6h, 8h, 12h, 1d, 3d, 1w, 1M
* [takeprofit] - in percentage, for example, 0.5
* [stoploss] - in percentage, for example, 0.01.
* [leverage] - for example, 6.
* [request buying amount] - in percentage, for example 10. 
* [entry strategy] - rsi, macd


## Creators
[Yonathan Wolloch](https://github.com/yonathan95)

[Uri Bek](https://github.com/urib94)

[Omri Attal](https://github.com/omriattal)



