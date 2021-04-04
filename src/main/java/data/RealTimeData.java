package data;

import strategies.macdOverRSIStrategies.MACDOverRSIConstants;
import strategies.rsiStrategies.RSIConstants;
import com.binance.client.SyncRequestClient;
import com.binance.client.model.enums.CandlestickInterval;
import com.binance.client.model.event.CandlestickEvent;
import com.binance.client.model.market.Candlestick;
import org.ta4j.core.BaseBarSeries;
import org.ta4j.core.indicators.EMAIndicator;
import org.ta4j.core.indicators.MACDIndicator;
import org.ta4j.core.indicators.RSIIndicator;
import org.ta4j.core.indicators.SMAIndicator;
import org.ta4j.core.indicators.helpers.ClosePriceIndicator;
import singletonHelpers.RequestClient;

import java.math.BigDecimal;
import java.time.Duration;
import java.time.ZonedDateTime;
import java.util.List;

//* For us, in realTimeData, the last candle is always open. The previous ones are closed.
public class RealTimeData{

    private Long lastCandleOpenTime;
    private BaseBarSeries realTimeData;
    private double currentPrice;
    private RSIIndicator rsiIndicator;
    private MACDIndicator macdOverRsiIndicator;
    private SMAIndicator smaIndicator;
    private int updateCounter = 0;


    public RealTimeData(String symbol, CandlestickInterval interval){
        realTimeData = new BaseBarSeries();
        SyncRequestClient syncRequestClient = RequestClient.getRequestClient().getSyncRequestClient();
        List<Candlestick> candlestickBars = syncRequestClient.getCandlestick(symbol, interval, null, null, Config.CANDLE_NUM);
        lastCandleOpenTime = candlestickBars.get(candlestickBars.size() - 1).getOpenTime();
        currentPrice = candlestickBars.get(candlestickBars.size() -1).getClose().doubleValue();
        fillRealTimeData(candlestickBars);
        calculateIndicators();
    }


    /**
     * Receives the current candlestick - usually an open one.
     * The function updateData updates realTimeData in the following way: if the candle received is closed => push to the end
     * of realTimeData and erase the first. If the candle is open - delete the last one from real time data and push the new one.
     * Calculates the RSIIndicators in either case - to get the most accurate data.
     * to realTimeData
     * @param event - the new Candlestick received from the subscribeCandleStickEvent.
     */
    public synchronized DataHolder updateData(CandlestickEvent event){
        boolean isNewCandle = updateLastCandle(event);
        updateCounter += 1;
        if (! isNewCandle && updateCounter != 20) return null;
        updateCounter = 0;
        calculateIndicators();
        return new DataHolder(currentPrice, rsiIndicator, macdOverRsiIndicator, smaIndicator, realTimeData.getEndIndex());
    }

    private boolean updateLastCandle(CandlestickEvent event) {
        currentPrice = event.getClose().doubleValue();
        boolean isNewCandle = !(event.getStartTime().doubleValue() == lastCandleOpenTime);
        ZonedDateTime closeTime = utils.Utils.getZonedDateTime(event.getCloseTime());
        Duration candleDuration = Duration.ofMillis(event.getCloseTime() - event.getStartTime());
        double open = event.getOpen().doubleValue();
        double high = event.getHigh().doubleValue();
        double low = event.getLow().doubleValue();
        double close = event.getClose().doubleValue();
        double volume = event.getVolume().doubleValue();
        lastCandleOpenTime = event.getStartTime();
        if (isNewCandle){
            realTimeData = realTimeData.getSubSeries(1, realTimeData.getEndIndex() + 1);
        }
        else{
            realTimeData = realTimeData.getSubSeries(0, realTimeData.getEndIndex());
        }
        realTimeData.addBar(candleDuration, closeTime, open, high, low, close, volume);
        return isNewCandle;
    }

    private void fillRealTimeData(List<Candlestick> candlestickBars){
        for (Candlestick candlestickBar : candlestickBars) {
            ZonedDateTime closeTime = utils.Utils.getZonedDateTime(candlestickBar.getCloseTime());
            Duration candleDuration = Duration.ofMillis(candlestickBar.getCloseTime()
                    - candlestickBar.getOpenTime());
            double open = candlestickBar.getOpen().doubleValue();
            double high = candlestickBar.getHigh().doubleValue();
            double low = candlestickBar.getLow().doubleValue();
            double close = candlestickBar.getClose().doubleValue();
            double volume = candlestickBar.getVolume().doubleValue();
            realTimeData.addBar(candleDuration, closeTime, open, high, low, close, volume);
        }
    }

    private void calculateIndicators() {
        rsiIndicator = calculateRSI(RSIConstants.RSI_CANDLE_NUM);
        macdOverRsiIndicator = calculateMacdOverRsi();
        smaIndicator = new SMAIndicator(new ClosePriceIndicator(realTimeData), MACDOverRSIConstants.SMA_CANDLE_NUM);
    }

    public double getMacdOverRsiSignalLineValueAtIndex(int index) {
        EMAIndicator signal = new EMAIndicator(macdOverRsiIndicator, MACDOverRSIConstants.SIGNAL_LENGTH);
        return signal.getValue(index).doubleValue();
    }

    public double getMacdOverRsiMacdLineValueAtIndex(int index) {
        return macdOverRsiIndicator.getValue(index).doubleValue();
    }

    public double getMacdOverRsiValueAtIndex(int index) {
        return getMacdOverRsiMacdLineValueAtIndex(index) - getMacdOverRsiSignalLineValueAtIndex(index);
    }

    private MACDIndicator calculateMacdOverRsi() {
        RSIIndicator rsiIndicator14 = calculateRSI(MACDOverRSIConstants.RSI_CANDLE_NUM);
        return new MACDIndicator(rsiIndicator14, MACDOverRSIConstants.FAST_BAR_COUNT, MACDOverRSIConstants.SLOW_BAR_COUNT);
    }

    private RSIIndicator calculateRSI(int candleNum) {
        ClosePriceIndicator closePriceIndicator = new ClosePriceIndicator(realTimeData);
        return new RSIIndicator(closePriceIndicator, candleNum);
    }

    public double getCurrentPrice() {
        return currentPrice;
    }

    public BaseBarSeries getRealTimeData() {
        return realTimeData;
    }
}
