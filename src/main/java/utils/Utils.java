package utils;

import data.DataHolder;
import data.RealTimeData;
import singletonHelpers.BinanceInfo;
import com.binance.client.model.enums.CandlestickInterval;

import java.math.BigDecimal;
import java.math.MathContext;
import java.time.*;

public class Utils {
	public static Long candleStickIntervalToMilliseconds(CandlestickInterval interval) {
		String intervalCode = interval.toString();
		int value = Integer.parseInt(intervalCode.substring(0,intervalCode.length()-1));
		char typeOfTime = intervalCode.charAt(intervalCode.length()-1);
		switch (typeOfTime) {
			case 'm':
				return (long) value * TimeConstants.MINUTES_TO_MILLISECONDS_CONVERTER;
			case 'h':
				return (long) value * TimeConstants.HOURS_TO_MILLISECONDS_CONVERTER;
			case 'd':
				return (long) value * TimeConstants.DAYS_TO_MILLISECONDS_CONVERTER;
			case 'w':
				return (long) value * TimeConstants.WEEKS_TO_MILLISECONDS_CONVERTER;
			case 'M':
				return (long) value * TimeConstants.MONTHS_TO_MILLISECONDS_CONVERTER;
			default:
				return -1L;
		}
	}

	public static ZonedDateTime getZonedDateTime(Long timestamp) {
		return ZonedDateTime.ofInstant(Instant.ofEpochMilli(timestamp),
				ZoneId.systemDefault());
	}

	public static String getBuyingQtyAsString(BigDecimal currentPrice , String symbol, int leverage, BigDecimal requestedBuyingAmount) {
		BigDecimal buyingQty = requestedBuyingAmount.multiply(BigDecimal.valueOf(leverage)).divide(currentPrice, MathContext.DECIMAL32);
		return fixQuantity(BinanceInfo.formatQty(buyingQty, symbol));
	}

	public static String getTakeProfitPriceAsString(DataHolder realTimeData, String symbol, double takeProfitPercentage) {
		BigDecimal takeProfitPrice = realTimeData.getCurrentPrice().add((realTimeData.getCurrentPrice().multiply(BigDecimal.valueOf(takeProfitPercentage))));
		return BinanceInfo.formatPrice(takeProfitPrice, symbol);
	}

	public static String getStopLossPriceAsString(DataHolder realTimeData, String symbol, double stopLossPercentage) {
		BigDecimal stopLossPrice = realTimeData.getCurrentPrice().subtract(realTimeData.getCurrentPrice().multiply(BigDecimal.valueOf(stopLossPercentage)));
		return BinanceInfo.formatPrice(stopLossPrice, symbol);
	}

	public static String fixQuantity(String amt) {
		if (Double.parseDouble(amt) == 0) {
			amt = amt.substring(0, amt.length()-1).concat("1");
		}
		return amt;
	}
	//
}
