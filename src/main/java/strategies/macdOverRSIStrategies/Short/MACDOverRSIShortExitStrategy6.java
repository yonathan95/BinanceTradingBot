package strategies.macdOverRSIStrategies.Short;

import data.DataHolder;
import data.RealTimeData;
import positions.PositionHandler;
import positions.SellingInstructions;
import singletonHelpers.TelegramMessenger;
import strategies.macdOverRSIStrategies.MACDOverRSIBaseExitStrategy;
import strategies.macdOverRSIStrategies.MACDOverRSIConstants;

import java.util.Date;

public class MACDOverRSIShortExitStrategy6 extends MACDOverRSIBaseExitStrategy {
    @Override
    public SellingInstructions run(DataHolder realTimeData) {
//        boolean crossedLowerBollinger = currentPriceCrossedBollinger(realTimeData, RealTimeData.CrossType.DOWN, MACDOverRSIBaseExitStrategy.BollingerType.UPPER);
//        if (crossedLowerBollinger) {
//            TelegramMessenger.sendToTelegram("exiting position with short exit 6: " + new Date(System.currentTimeMillis()));
//            return new SellingInstructions(PositionHandler.ClosePositionTypes.SELL_MARKET, MACDOverRSIConstants.MACD_OVER_RSI_EXIT_SELLING_PERCENTAGE);
//        }
        return null;
    }
}
