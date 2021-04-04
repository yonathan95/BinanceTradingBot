package strategies.macdOverRSIStrategies;

import java.math.BigDecimal;

public class MACDOverRSIConstants {
    public static final int FAST_BAR_COUNT = 14;
    public static final int SLOW_BAR_COUNT = 24;
    public static final double TAKE_PROFIT_PERCENTAGE = 0.0;
    public static final double STOP_LOSS_PERCENTAGE = 0.0;
    public static final int LEVERAGE = 60;
    public static final double BUYING_AMOUNT = 20;
    public static final int SIGNAL_LENGTH = 9;
    public static final int RSI_CANDLE_NUM = 9;
    public static final int SMA_CANDLE_NUM = 100;
    public static final double MACD_OVER_RSI_EXIT_SELLING_PERCENTAGE = 100;
    public static final double POSITIVE_TRAILING_PERCENTAGE = 0.15;
    public static final double CONSTANT_TRAILING_PERCENTAGE = 0.25;
    public static final double LONG_EXIT2_OPEN_THRESHOLD = -0.05;
    public static final double SHORT_EXIT2_OPEN_THRESHOLD = 0.05;
}
