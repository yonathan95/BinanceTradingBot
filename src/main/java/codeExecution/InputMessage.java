package codeExecution;

import singletonHelpers.BinanceInfo;
import strategies.EntryStrategy;
import strategies.macdOverRSIStrategies.MACDOverRSIEntryStrategy;
import strategies.rsiStrategies.RSIEntryStrategy;
import com.binance.client.model.enums.CandlestickInterval;

import java.math.BigDecimal;

public class InputMessage {
    public String operation = RealTImeOperations.UNKNOWN_OPERATION;
    private String symbol;
    private CandlestickInterval interval;
    private EntryStrategy entryStrategy;
    private String apiKey;
    private String secretKey;

    public void initialize(String input) {
        String [] messageParts = input.split(" ");
        operation = messageParts[0];
        switch (operation) {
            case RealTImeOperations.CANCEL_ALL_ORDERS:

            case RealTImeOperations.GET_LAST_TRADES:

            case RealTImeOperations.GET_OPEN_ORDERS:

            case RealTImeOperations.GET_CURRENT_BALANCE:
                symbol = messageParts[1];
                if (!BinanceInfo.isSymbolExists(symbol)){
                    System.out.println("Wrong symbol");
                    operation = RealTImeOperations.UNKNOWN_OPERATION;
                }
                break;

            case RealTImeOperations.CLOSE_ALL_POSITIONS:

            case RealTImeOperations.CLOSE_PROGRAM:

            case RealTImeOperations.GET_OPEN_POSITIONS:
                break;

            case RealTImeOperations.ACTIVATE_STRATEGY:

            case RealTImeOperations.DEACTIVATE_STRATEGY:
                entryStrategy = stringToEntryStrategy(messageParts[1]);
                symbol = messageParts[2];
                interval = null;
                for (CandlestickInterval candlestickInterval: CandlestickInterval.values()){
                    if (candlestickInterval.toString().equals(messageParts[3])) interval = candlestickInterval;
                }
                if (entryStrategy == null){
                    System.out.println("This strategy don't exists");
                    operation = RealTImeOperations.UNKNOWN_OPERATION;
                    break;
                }
                if (!BinanceInfo.isSymbolExists(symbol)){
                    System.out.println("Wrong symbol");
                    operation = RealTImeOperations.UNKNOWN_OPERATION;
                    break;
                }
                if (interval == null){
                    System.out.println("Wrong interval");
                    operation = RealTImeOperations.UNKNOWN_OPERATION;
                    break;
                }
                break;

            case "help":
                System.out.println("Optional commands:\n" +
                        "cao [symbol] - Cancel all orders, for [symbol]\n" +
                        "cap - Close all open positions\n" +
                        "as [strategy] [symbol] [interval] - Activate strategy [strategy] with [symbol] and candlestick interval[interval]\n" +
                        "ds  [strategy] [symbol] [interval] - Deactivate strategy with [symbol] and candlestick interval [interval]\n" +
                        "glt [symbol] - Get last trades for [symbol]\n" +
                        "gop - get all Open positions\n" +
                        "goo [symbol] - Get all open orders for [symbol]\n" +
                        "gcb [symbol] - Get current balance for [symbol]\n" +
                        "cp - Close program\n" +
                        "\n entryStrategy options: rsi, macd" +
                        "\n interval options: 1m, 3m, 5m, 15m, 30m, 1h, 2h, 4h, 6h ,8h, 12h, 1d, 3d, 1w, 1M"
                );
                break;

            default:
                System.out.println("Wrong operation");
                operation = RealTImeOperations.UNKNOWN_OPERATION;
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
