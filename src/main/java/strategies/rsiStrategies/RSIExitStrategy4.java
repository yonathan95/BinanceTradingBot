package strategies.rsiStrategies;

import data.DataHolder;
import positions.PositionHandler;
import positions.SellingInstructions;
import singletonHelpers.TelegramMessenger;
import strategies.ExitStrategy;

public class RSIExitStrategy4 implements ExitStrategy {

	public SellingInstructions run(DataHolder realTimeData) {
		if (!(realTimeData.above(DataHolder.IndicatorType.RSI,DataHolder.CandleType.OPEN, RSIConstants.RSI_EXIT_OPTION_4_UNDER_THRESHOLD))) {
			TelegramMessenger.sendToTelegram("Exiting with RSI exit strategy 4!");
			return new SellingInstructions(PositionHandler.ClosePositionTypes.SELL_LIMIT, RSIConstants.RSI_EXIT_OPTION_4_SELLING_PERCENTAGE);
		}
		return null;
	}
}
