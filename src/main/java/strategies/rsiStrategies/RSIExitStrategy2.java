package strategies.rsiStrategies;

import data.DataHolder;
import positions.PositionHandler;
import positions.SellingInstructions;
import singletonHelpers.TelegramMessenger;
import strategies.ExitStrategy;
import strategies.PositionInStrategy;

public class RSIExitStrategy2 implements ExitStrategy {
	private PositionInStrategy positionInStrategy = PositionInStrategy.POSITION_ONE;

	/**
	 * Checks if the current close of RSIIndicator value is above 73, and then below 70 and then below 60.
	 * @param realTimeData
	 * @return the percentage of quantity to sell, null otherwise.
	 */
	public SellingInstructions run(DataHolder realTimeData) {
		if (positionInStrategy == PositionInStrategy.POSITION_ONE) {
			if (realTimeData.above(DataHolder.IndicatorType.RSI,DataHolder.CandleType.CLOSE, RSIConstants.RSI_EXIT_OPTION_2_OVER_THRESHOLD1)) {
				positionInStrategy = PositionInStrategy.POSITION_TWO;
			}
			return null;
		} else if (positionInStrategy == PositionInStrategy.POSITION_TWO) {
			if (! realTimeData.above(DataHolder.IndicatorType.RSI,DataHolder.CandleType.CLOSE, RSIConstants.RSI_EXIT_OPTION_2_UNDER_THRESHOLD1)) {
				TelegramMessenger.sendToTelegram(this.getClass().getSimpleName() + "Switching to Position 3. Returning 40% ");
				positionInStrategy = PositionInStrategy.POSITION_THREE;
				return new SellingInstructions(PositionHandler.ClosePositionTypes.SELL_LIMIT, RSIConstants.RSI_EXIT_OPTION_2_SELLING_PERCENTAGE1);

			}
		} else if(positionInStrategy == PositionInStrategy.POSITION_THREE) {
			if (! realTimeData.above(DataHolder.IndicatorType.RSI,DataHolder.CandleType.CLOSE, RSIConstants.RSI_EXIT_OPTION_2_UNDER_THRESHOLD2)) {
				positionInStrategy = PositionInStrategy.POSITION_ONE;
				TelegramMessenger.sendToTelegram(this.getClass().getSimpleName() + "Switching to Position 1. Returning 100% ");
				return new SellingInstructions(PositionHandler.ClosePositionTypes.SELL_LIMIT, RSIConstants.RSI_EXIT_OPTION_2_SELLING_PERCENTAGE2);
			}
		}
		return null;
	}
}
