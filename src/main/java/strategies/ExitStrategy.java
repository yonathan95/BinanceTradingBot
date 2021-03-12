package strategies;

import data.DataHolder;
import data.RealTimeData;
import positions.SellingInstructions;

public interface ExitStrategy {
    SellingInstructions run(DataHolder realTimeData);
}
