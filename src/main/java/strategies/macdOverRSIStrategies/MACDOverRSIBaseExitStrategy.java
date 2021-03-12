package strategies.macdOverRSIStrategies;

import data.DataHolder;
import strategies.ExitStrategy;

public abstract class MACDOverRSIBaseExitStrategy implements ExitStrategy {

    public boolean changedDirectionAndPositiveThreeHistogram(DataHolder realTimeData){
        double now = realTimeData.getMacdOverRsiCloseValue();
        double prev = realTimeData.getMacdOverRsiValueAtIndex(realTimeData.getLastCloseIndex() -1);
        return now > 0 && prev > 0 && realTimeData.getMacdOverRsiValueAtIndex(realTimeData.getLastCloseIndex() -2) > 0
                && Math.abs(prev) >= Math.abs(now);
    }

    public boolean changedDirectionAndNegativeThreeHistogram(DataHolder realTimeData){
        double now = realTimeData.getMacdOverRsiCloseValue();
        double prev = realTimeData.getMacdOverRsiValueAtIndex(realTimeData.getLastCloseIndex() -1);
        return now < 0 && prev < 0 && realTimeData.getMacdOverRsiValueAtIndex(realTimeData.getLastCloseIndex() -2) < 0
                && Math.abs(prev) >= Math.abs(now);
    }

    public boolean stayInTrackAndThreePositiveHistograms(DataHolder realTimeData){
        double now = realTimeData.getMacdOverRsiCloseValue();
        double prev = realTimeData.getMacdOverRsiValueAtIndex(realTimeData.getLastCloseIndex()-1);
        return Math.abs(prev) <= Math.abs(now) && now > 0 && prev > 0
                && realTimeData.getMacdOverRsiValueAtIndex(realTimeData.getLastCloseIndex() -2) > 0;
    }

    public boolean stayInTrackAndThreeNegativeHistograms(DataHolder realTimeData){
        double now = realTimeData.getMacdOverRsiCloseValue();
        double prev = realTimeData.getMacdOverRsiValueAtIndex(realTimeData.getLastCloseIndex()-1);
        return Math.abs(prev) <= Math.abs(now) && now < 0 && prev < 0
                && realTimeData.getMacdOverRsiValueAtIndex(realTimeData.getLastCloseIndex() -2) < 0;
    }
}
