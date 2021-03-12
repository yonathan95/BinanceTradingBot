package codeExecution;

import strategies.EntryStrategy;
import strategies.macdOverRSIStrategies.MACDOverRSIEntryStrategy;
import strategies.rsiStrategies.RSIEntryStrategy;
import com.binance.client.model.enums.CandlestickInterval;

import java.math.BigDecimal;

public class InputMessage {
    public String operation = "";
    private String symbol;
    private CandlestickInterval interval;
    private EntryStrategy entryStrategy;
    private String apiKey;
    private String secretKey;

    public void initialize(String input) {
        String [] messageParts = input.split(", ");
        operation = messageParts[0];
        switch (operation) {
            case RealTImeOperations.CANCEL_ALL_ORDERS:

            case RealTImeOperations.BUY_NOW:

            case RealTImeOperations.GET_LAST_TRADES:

            case RealTImeOperations.GET_OPEN_ORDERS:

            case RealTImeOperations.GET_CURRENT_BALANCE:
                symbol = messageParts[1];
                break;

            case RealTImeOperations.CLOSE_ALL_POSITIONS:

            case RealTImeOperations.GET_OPEN_POSITIONS:
                break;

            case RealTImeOperations.ACTIVATE_STRATEGY:
            symbol = messageParts[1];
            for (CandlestickInterval candlestickInterval: CandlestickInterval.values()){
                if (candlestickInterval.toString().equals(messageParts[2])) interval = candlestickInterval;
            }
            entryStrategy = stringToEntryStrategy(messageParts[3]);
            if (entryStrategy != null){
                entryStrategy.setTakeProfitPercentage(Double.parseDouble(messageParts[4]));
                entryStrategy.setStopLossPercentage(Double.parseDouble(messageParts[5]));
                entryStrategy.setLeverage(Integer.parseInt(messageParts[6]));
                entryStrategy.setRequestedBuyingAmount(BigDecimal.valueOf(Double.parseDouble(messageParts[7])));
            }
                break;

            case RealTImeOperations.ACTIVATE_STRATEGY_D:
            symbol = messageParts[1];
            for (CandlestickInterval candlestickInterval: CandlestickInterval.values()){
                if (candlestickInterval.toString().equals(messageParts[2])) interval = candlestickInterval;
            }
            entryStrategy = stringToEntryStrategy(messageParts[3]);
                break;

            case RealTImeOperations.DEACTIVATE_STRATEGY:
                symbol = messageParts[1];
                for (CandlestickInterval candlestickInterval: CandlestickInterval.values()){
                    if (candlestickInterval.toString().equals(messageParts[2])) interval = candlestickInterval;
                }
                break;

            case "help":
                System.out.println("Optional commands:\n" +
                        "cancel all orders, [symbol]\n" +
                        "close all positions\n" +
                        "activate strategy, [symbol], [interval], [entryStrategy], [takeProfit], [stopLoss], [leverage], [request buying amount]\n" +
                        "activate strategy default, [symbol], [interval], [entryStrategy]\n" +
                        "deactivate strategy, [symbol], [interval]\n" +
                        "get last trades, [symbol]\n" +
                        "get open positions\n" +
                        "get open orders, [symbol]\n" +
                        "get current balance, [symbol]\n" +
                        "buy now, [symbol]\n"+
                        "\n entryStrategy options: rsi, macd" +
                        "\n interval options: 1m, 3m, 5m, 15m, 30m, 1h, 2h, 4h, 6h ,8h, 12h, 1d, 3d, 1w, 1M"
                );
                break;

            default:
                System.out.println("Wrong message");
        }
    }

    private EntryStrategy stringToEntryStrategy(String strategyName) {
        switch (strategyName) {
            case "rsi":
                return new RSIEntryStrategy();

            case "macd":
                return new MACDOverRSIEntryStrategy();

            default:
                return null;
        }
    }

    public String getSymbol() {
        return symbol;
    }

    public String getOperation() {
        return operation;
    }

    public CandlestickInterval getInterval() {
        return interval;
    }

    public EntryStrategy getEntryStrategy() {
        return entryStrategy;
    }

    public String getApiKey() {
        return apiKey;
    }

    public String getSecretKey() {
        return secretKey;
    }
}
