package strategies.macdOverRSIStrategies.Long;

import data.DataHolder;
import data.RealTimeData;
import positions.PositionHandler;
import positions.SellingInstructions;
import singletonHelpers.TelegramMessenger;
import strategies.macdOverRSIStrategies.MACDOverRSIBaseExitStrategy;
import strategies.macdOverRSIStrategies.MACDOverRSIConstants;

import java.util.Date;

public class MACDOverRSILongExitStrategy6 extends MACDOverRSIBaseExitStrategy {

    @Override
    public SellingInstructions run(DataHolder realTimeData) {
//        boolean crossedUpperBollinger = currentPriceCrossedBollinger(realTimeData, RealTimeData.CrossType.UP, BollingerType.LOWER);
//        if (crossedUpperBollinger) {
//            TelegramMessenger.sendToTelegram("exiting position with long exit 6: " + new Date(System.currentTimeMillis()));
//            return new SellingInstructions(PositionHandler.ClosePositionTypes.SELL_MARKET,MACDOverRSIConstants.MACD_OVER_RSI_EXIT_SELLING_PERCENTAGE);
//        }
        return null;
    }
}
