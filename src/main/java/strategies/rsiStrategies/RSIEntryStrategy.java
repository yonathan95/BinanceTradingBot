package strategies.rsiStrategies;

import data.DataHolder;
import singletonHelpers.TelegramMessenger;
import strategies.EntryStrategy;
import positions.PositionHandler;
import strategies.ExitStrategy;
import strategies.PositionInStrategy;
import utils.Utils;
import com.binance.client.SyncRequestClient;
import com.binance.client.model.enums.*;
import com.binance.client.model.trade.Order;
import singletonHelpers.RequestClient;

import java.math.BigDecimal;
import java.util.ArrayList;
import java.util.Date;

public class RSIEntryStrategy implements EntryStrategy {
    double takeProfitPercentage = RSIConstants.TAKE_PROFIT_PERCENTAGE;
    private double stopLossPercentage = RSIConstants.STOP_LOSS_PERCENTAGE;
    private int leverage = RSIConstants.LEVERAGE;
    private  double requestedBuyingAmount = RSIConstants.BUYING_AMOUNT;
    private PositionInStrategy positionInStrategy = PositionInStrategy.POSITION_ONE;
    private int time_passed_from_position_2 = 0;
    double rsiValueToCheckForPosition3 = -1;

    public synchronized PositionHandler run(DataHolder realTimeData,String symbol) {
        if (positionInStrategy == PositionInStrategy.POSITION_ONE) {
            if (realTimeData.crossed(DataHolder.IndicatorType.RSI,DataHolder.CrossType.DOWN, DataHolder.CandleType.CLOSE, RSIConstants.RSI_ENTRY_THRESHOLD_1)) {
                positionInStrategy = PositionInStrategy.POSITION_TWO;
            }
            return null;
        } else if (positionInStrategy == PositionInStrategy.POSITION_TWO) {
            if (realTimeData.crossed(DataHolder.IndicatorType.RSI,DataHolder.CrossType.UP, DataHolder.CandleType.CLOSE, RSIConstants.RSI_ENTRY_THRESHOLD_2)) {
                rsiValueToCheckForPosition3 = realTimeData.getRsiCloseValue();
                positionInStrategy = PositionInStrategy.POSITION_THREE;
            }
            return null;
        } else if (positionInStrategy == PositionInStrategy.POSITION_THREE) {
            if (time_passed_from_position_2 >= 2) {
                time_passed_from_position_2 = 0;
                rsiValueToCheckForPosition3 = -1;
                positionInStrategy = PositionInStrategy.POSITION_TWO;
                return null;
            }
            if(rsiValueToCheckForPosition3 != realTimeData.getRsiCloseValue()) {
                time_passed_from_position_2 ++;
            }
            if (realTimeData.above(DataHolder.IndicatorType.RSI, DataHolder.CandleType.CLOSE, RSIConstants.RSI_ENTRY_THRESHOLD_3)) {
                time_passed_from_position_2 = 0;
                positionInStrategy = PositionInStrategy.POSITION_ONE;
                rsiValueToCheckForPosition3 = -1;
                SyncRequestClient syncRequestClient = RequestClient.getRequestClient().getSyncRequestClient();
                syncRequestClient.changeInitialLeverage(symbol,leverage);
                String buyingQty = Utils.getBuyingQtyAsString(realTimeData.getCurrentPrice(),symbol,leverage,requestedBuyingAmount);
                try{
                    TelegramMessenger.sendToTelegram("buying long: " + new Date(System.currentTimeMillis()));
                    Order buyOrder = syncRequestClient.postOrder(symbol, OrderSide.BUY, null, OrderType.MARKET, null,
                            buyingQty,null,null,null, null,null,null, null, WorkingType.MARK_PRICE, null, NewOrderRespType.RESULT);
                    String takeProfitPrice = Utils.getTakeProfitPriceAsString(realTimeData, symbol,takeProfitPercentage);
                    syncRequestClient.postOrder(symbol, OrderSide.SELL, null,OrderType.TAKE_PROFIT, TimeInForce.GTC,
                            buyingQty,takeProfitPrice,null,null,takeProfitPrice,null,null, null,WorkingType.MARK_PRICE, null, NewOrderRespType.RESULT);
                    String stopLossPrice = Utils.getStopLossPriceAsString(realTimeData, symbol, stopLossPercentage);
                    syncRequestClient.postOrder(symbol, OrderSide.SELL, null, OrderType.STOP, TimeInForce.GTC,
                            buyingQty,stopLossPrice,null,null, stopLossPrice,null,null,null, WorkingType.MARK_PRICE,null, NewOrderRespType.RESULT);
                    TelegramMessenger.sendToTelegram("Buy order: " + buyOrder + " " + new Date(System.currentTimeMillis()));
                    ArrayList<ExitStrategy> exitStrategies = new ArrayList<>();
                    exitStrategies.add(new RSIExitStrategy1());
                    exitStrategies.add(new RSIExitStrategy2());
                    exitStrategies.add(new RSIExitStrategy3());
                    exitStrategies.add(new RSIExitStrategy4());
                    return new PositionHandler(buyOrder, exitStrategies);
                }catch (Exception e){System.out.println("exception in RSI: " + e);}
            }
        }
        return null;
    }

    public void setTakeProfitPercentage(double takeProfitPercentage) {
        this.takeProfitPercentage = takeProfitPercentage;
    }

    public void setStopLossPercentage(double stopLossPercentage) {
        this.stopLossPercentage = stopLossPercentage;
    }

    public void setLeverage(int leverage) {
        this.leverage = leverage;
    }

    public void setRequestedBuyingAmount(double requestedBuyingAmount) {
        this.requestedBuyingAmount = requestedBuyingAmount;
    }
}
