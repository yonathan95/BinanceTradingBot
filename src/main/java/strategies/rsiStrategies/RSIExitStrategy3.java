package strategies.rsiStrategies;
import data.DataHolder;
import positions.PositionHandler;
import positions.SellingInstructions;
import singletonHelpers.TelegramMessenger;
import strategies.ExitStrategy;


public class RSIExitStrategy3 implements ExitStrategy {
	private double rsiValueTwoBefore = -1.0;
	private double rsiValueBefore;
	private boolean firstTime = true;

	public SellingInstructions run(DataHolder realTimeData) {
		if (firstTime) {
			rsiValueBefore = realTimeData.getRsiCloseValue(); // last closed candle rsi value
			firstTime = false;
		} // not the first time. already ran.
		double rsiValue = realTimeData.getRsiOpenValue();
		if (rsiValueBefore != realTimeData.getRsiCloseValue()) {
			updateValues(realTimeData.getRsiCloseValue());
		}
		if (lostValueOf15(rsiValueBefore,rsiValue)) {
			TelegramMessenger.sendToTelegram("Exiting with RSI exit strategy 3. Returning 100(1)");
			return new SellingInstructions(PositionHandler.ClosePositionTypes.SELL_LIMIT, RSIConstants.RSI_EXIT_OPTION_3_SELLING_PERCENTAGE);

		}
		if (rsiValueTwoBefore != -1.0 && lostValueOf15(rsiValueTwoBefore,rsiValue)) {
			TelegramMessenger.sendToTelegram("Exiting with RSI exit strategy 3. Returning 100(2)");
			return new SellingInstructions(PositionHandler.ClosePositionTypes.SELL_LIMIT, RSIConstants.RSI_EXIT_OPTION_3_SELLING_PERCENTAGE);
		}
		return null;
	}

	private boolean lostValueOf15(double oldVal, double newVal) {
		return oldVal - newVal >= 15;}

	private void updateValues(double newValue) {
		double temp = rsiValueBefore;
		rsiValueBefore = newValue;
		rsiValueTwoBefore = temp;
	}
}
