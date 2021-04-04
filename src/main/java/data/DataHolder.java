package data;

import org.ta4j.core.indicators.EMAIndicator;
import org.ta4j.core.indicators.MACDIndicator;
import org.ta4j.core.indicators.RSIIndicator;
import org.ta4j.core.indicators.SMAIndicator;
import strategies.macdOverRSIStrategies.MACDOverRSIConstants;

import java.math.BigDecimal;

public class DataHolder {
    private final Double currentPrice;
    private final RSIIndicator rsiIndicator;
    private final MACDIndicator macdOverRsiIndicator;
    private final double macdOverRsiCloseValue;
    private final SMAIndicator smaIndicator;
    private final int endIndex;

    public DataHolder(double currentPrice, RSIIndicator rsiIndicator, MACDIndicator macdOverRsiIndicator, SMAIndicator smaIndicator, int endIndex) {
        this.currentPrice = currentPrice;
        this.rsiIndicator = rsiIndicator;
        this.macdOverRsiIndicator = macdOverRsiIndicator;
        this.smaIndicator = smaIndicator;
        this.endIndex = endIndex;
        this.macdOverRsiCloseValue = getMacdOverRsiValueAtIndex(endIndex - 1);
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

    public double getMacdOverRsiCloseValue() {
        return macdOverRsiCloseValue;
    }

    public double getRsiOpenValue() {
        return rsiIndicator.getValue(endIndex).doubleValue();
    }

    public double getRsiCloseValue() {
        return rsiIndicator.getValue(endIndex-1).doubleValue();
    }

    public double getRSIValueAtIndex(int index) {
        return rsiIndicator.getValue(index).doubleValue();
    }

    public  double getSMAValueAtIndex(int index) {
        return smaIndicator.getValue(index).doubleValue();
    }


    public boolean crossed(IndicatorType indicatorType, CrossType crossType, CandleType candleType, double threshold) {
        switch (indicatorType) {
            case RSI:
                return rsiCrossed(crossType,candleType,threshold);
            case MACD_OVER_RSI:
                return macdOverRsiCrossed(crossType,candleType,threshold);
        }
        return true; // will not come to this!

    }
    private boolean rsiCrossed(CrossType crossType, CandleType candleType, double threshold) {
        double rsiValueNow,rsiValuePrev;
        if (candleType == CandleType.OPEN) {
            rsiValueNow = getRsiOpenValue();
            rsiValuePrev = getRsiCloseValue();
        }
        else {
            rsiValueNow = getRsiCloseValue();
            rsiValuePrev = getRSIValueAtIndex(endIndex-2);
        }
        if (crossType == CrossType.UP) return rsiValueNow > threshold && rsiValuePrev <= threshold;
        return rsiValuePrev >= threshold && rsiValueNow < threshold;
    }
    private boolean macdOverRsiCrossed(CrossType crossType, CandleType candleType, double threshold) {
        double currentMacdOverRsiValue,prevMacdOverRsiValue;
        if (candleType == CandleType.OPEN) {
            currentMacdOverRsiValue = getMacdOverRsiValueAtIndex(endIndex);
            prevMacdOverRsiValue  = macdOverRsiCloseValue;
        } else {
            currentMacdOverRsiValue = macdOverRsiCloseValue;
            prevMacdOverRsiValue = getMacdOverRsiValueAtIndex(endIndex-2);
        }
        if (crossType == CrossType.UP) return currentMacdOverRsiValue > threshold && prevMacdOverRsiValue <= threshold;
        return prevMacdOverRsiValue >= threshold && currentMacdOverRsiValue < threshold;
    }

    public boolean above(IndicatorType indicatorType, CandleType type, int threshold) {
        if (indicatorType == IndicatorType.RSI) {
            if (type == CandleType.OPEN) {
                return getRsiOpenValue() > threshold;
            } else {
                return getRsiCloseValue() > threshold;
            }
        } else if(indicatorType == IndicatorType.MACD_OVER_RSI) {
            if (type == CandleType.OPEN) {
                return getMacdOverRsiValueAtIndex(endIndex) > threshold;
            } else {
                return  getMacdOverRsiValueAtIndex(endIndex -1) > threshold;
            }
        } else {
            if (type == CandleType.OPEN) {
                return getSMAValueAtIndex(endIndex)>threshold;
            } else {
                return getSMAValueAtIndex(endIndex-1) > threshold;
            }
        }
    }

    public synchronized Double getCurrentPrice() { return currentPrice;}

    public int getLastIndex(){return endIndex;}

    public int getLastCloseIndex(){return endIndex-1;}


    public enum CandleType {
        OPEN,CLOSE
    }

    public enum CrossType {
        UP,DOWN
    }
    public enum IndicatorType {
        RSI,MACD_OVER_RSI, SMA
    }
}
