package data;

import com.binance.client.model.enums.CandlestickInterval;

import java.math.BigDecimal;

public class Config {

	public static final double DOUBLE_ZERO = 0.0;
	public static final String BASE_COIN = "usdt";
	public static String API_KEY = "h4AdqbWrKlF5wOxWmbNTKLq7IpDReZOvVXeOujGwUfU0HjXdIejUmqKvoVLbcXJ6";
	public static String SECRET_KEY = "7qqNLwB7ZXiZu2nBJhrdv7ARVpNDhImNA1Rj1oXR6eGjZFkGsRC9ayEO7HLYVm6w";
	public static String TELEGRAM_API_TOKEN= "1493781452:AAGDIQ2nVL4NIu2xEstyyprFY6J04kQbDsA";
	public static String TELEGRAM_CHAT_ID = "-482820044";
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


	public static void setApiKey(String apiKey) {
		API_KEY = apiKey;
	}

	public static void setSecretKey(String secretKey) {
		SECRET_KEY = secretKey;
	}

}