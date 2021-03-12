package data;

import com.binance.client.model.enums.CandlestickInterval;

import java.math.BigDecimal;

public class Config {

	//Personal information:
	public static String API_KEY = "<Your binance api key>";
	public static String SECRET_KEY = "<Your binance secret key>";
	public static String TELEGRAM_API_TOKEN= "<Your telegram bot api token>";
	public static String TELEGRAM_CHAT_ID = "<Your telegram group chat id>";


	public static final double DOUBLE_ZERO = 0.0;
	public static final int THREAD_NUM = 6;
	public static final String SYMBOL = "btcusdt";
	public static final int CANDLE_NUM = 150;
	public static final String NEW = "NEW";
	public static final String PARTIALLY_FILLED = "PARTIALLY_FILLED";
	public static final String FILLED = "FILLED";
	public static final String CANCELED = "CANCELED";
	public static final String EXPIRED = "EXPIRED";
	public static final int ZERO = 0;
	public static final String REDUCE_ONLY = "true";
}