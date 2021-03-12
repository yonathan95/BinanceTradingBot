# Cryptocurrency Trading Bot

## Overview
The first Machine-Dance cryptocurrency traiding bot!

This is a bot that's written in Java that buys and sells cryptocurrency using Binance's API, managing user balances and dispalys information.
This project incorporate multiple threads, use of WebSocket and Rest APIs and object-oriented programming.
It required research on crypto currency strategies and their employment in Java with Binance's API.

## Strategies
The bot acquires the 500 most recent candles from Binance based on the symbol typed in by the user, and then runs on one or more from the following strategies.
Metholodgy - each entry strategy corresponds to its similary-named exit strategies. For example, RSI entry strategy will enter into position that listens on the four possible RSI exit strategies. 

### Entry strategies
1. [Relative Strength Index (RSI)](https://www.investopedia.com/terms/r/rsi.asp) with 9 candles.
* To enter position the RSI needs to cross 27,30 and 35 fast (last 2 close candles).
3. [Long MACD Over RSI](https://www.investopedia.com/terms/m/macd.asp) with 9 rsi values, fast bar: 14, slow bar: 24.
* If the price is above SMA 100, we need or that macd over rsi value crossed zero upwards, or we have a three negative downwards pyramid.
5. [Short MACD Over RSI](https://www.investopedia.com/terms/m/macd.asp)
* If the price is below SMA 100, we need that macd over rsi value crossed zero downwards or that we have three positive upwards pyramid.

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
* Crosing the zero line upwards -> Limit
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
In order to run the bot, **you need to press "help" to view all the possible commands the bot offers.**
#### Possible values:
* [symbol] - binance legal symbol, for example: btcusdt
* [interval] - the candlestick interval, possible values: 1m, 3m, 5m, 15m, 30m, 1h, 2h, 4h, 6h, 8h, 12h, 1d, 3d, 1w, 1M
* [takeprofit] - in percentage, for example, 0.5
* [stoploss] - in percentage, for example, 0.01.
* [leverage] - for example, 6.
* [request buying amount] - in percentage, for example 10. 
* [entry strategy] - rsi, macd long, macd short
* [apikey]- your api key
* [secretkey] - your secretkey.

## Creators
[Yonathan Wolloch](https://github.com/yonathan95)

[Uri Bek](https://github.com/urib94)

[Omri Attal](https://github.com/omriattal)



