package strategies.rsiStrategies;

import java.math.BigDecimal;

public class RSIConstants {

	public static final int RSI_EXIT_OPTION_1_OVER_THRESHOLD1 = 65;
	public static final int RSI_EXIT_OPTION_1_UNDER_THRESHOLD1 = 60;
	public static final int RSI_EXIT_OPTION_1_UNDER_THRESHOLD2 = 50;
	public static final int RSI_EXIT_OPTION_2_OVER_THRESHOLD1 = 73;
	public static final int RSI_EXIT_OPTION_2_UNDER_THRESHOLD1 = 70;
	public static final int RSI_EXIT_OPTION_2_UNDER_THRESHOLD2 = 60;
	public static final int RSI_EXIT_OPTION_4_UNDER_THRESHOLD = 30;
	public static final BigDecimal RSI_EXIT_OPTION_1_SELLING_PERCENTAGE1 = new BigDecimal(50);
	public static final BigDecimal RSI_EXIT_OPTION_1_SELLING_PERCENTAGE2 = new BigDecimal(100);
	public static final BigDecimal RSI_EXIT_OPTION_2_SELLING_PERCENTAGE1 = new BigDecimal(40);
	public static final BigDecimal RSI_EXIT_OPTION_2_SELLING_PERCENTAGE2 = new BigDecimal(100);
	public static final BigDecimal RSI_EXIT_OPTION_3_SELLING_PERCENTAGE = new BigDecimal(100);
	public static final BigDecimal RSI_EXIT_OPTION_4_SELLING_PERCENTAGE = new BigDecimal(100);
	public static final int RSI_ENTRY_THRESHOLD_1 = 27;
	public static final int RSI_ENTRY_THRESHOLD_2 = 30;
	public static final int RSI_ENTRY_THRESHOLD_3 = 35;
	public static final int RSI_CANDLE_NUM = 9;
    public static final double DEFAULT_STOP_LOSS_PERCENTAGE = 0.01;
	public static final int DEFAULT_LEVERAGE = 6;
	public static final BigDecimal DEFAULT_BUYING_AMOUNT = BigDecimal.valueOf(10);
	public static final double DEFAULT_TAKE_PROFIT_PERCENTAGE = 0.5;
}
