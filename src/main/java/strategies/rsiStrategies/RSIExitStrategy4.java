package strategies.rsiStrategies;

import data.DataHolder;
import data.RealTimeData;
import positions.PositionHandler;
import positions.SellingInstructions;
import strategies.ExitStrategy;

public class RSIExitStrategy4 implements ExitStrategy {

	public SellingInstructions run(DataHolder realTimeData) {
		System.out.println("rsi open value: " + realTimeData.getRsiOpenValue());
		if (!(realTimeData.above(RealTimeData.IndicatorType.RSI,RealTimeData.CandleType.OPEN, RSIConstants.RSI_EXIT_OPTION_4_UNDER_THRESHOLD))) {
			System.out.println("Exiting with RSI exit strategy 4!");
			return new SellingInstructions(PositionHandler.ClosePositionTypes.SELL_LIMIT, RSIConstants.RSI_EXIT_OPTION_4_SELLING_PERCENTAGE);
		}
		return null;
	}
}
