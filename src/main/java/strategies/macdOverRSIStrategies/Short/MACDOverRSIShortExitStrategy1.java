package strategies.macdOverRSIStrategies.Short;

import data.Config;
import data.DataHolder;
import positions.PositionHandler;
import positions.SellingInstructions;
import singletonHelpers.TelegramMessenger;
import strategies.macdOverRSIStrategies.MACDOverRSIBaseExitStrategy;
import strategies.macdOverRSIStrategies.MACDOverRSIConstants;

import java.math.BigDecimal;
import java.util.Date;

public class MACDOverRSIShortExitStrategy1 extends MACDOverRSIBaseExitStrategy {

	@Override
	public SellingInstructions run(DataHolder realTimeData) {
		boolean currentPriceAboveSMA = realTimeData.getSMAValueAtIndex(realTimeData.getLastCloseIndex()) < realTimeData.getCurrentPrice();
		if (currentPriceAboveSMA) {
			TelegramMessenger.sendToTelegram("exiting position with short exit 1" + "time: " + new Date(System.currentTimeMillis()));
			return new SellingInstructions(PositionHandler.ClosePositionTypes.CLOSE_SHORT_MARKET, MACDOverRSIConstants.MACD_OVER_RSI_EXIT_SELLING_PERCENTAGE);
		}
		return null;
	}
}
