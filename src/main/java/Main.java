import data.*;
import singletonHelpers.BinanceInfo;
import codeExecution.RealTimeCommandOperator;
import singletonHelpers.TelegramMessenger;

import java.time.ZonedDateTime;
import java.util.Date;

public class Main {
    public static void main(String[] args) {
        AccountBalance accountBalance = AccountBalance.getAccountBalance(); //!Don't touch
        BinanceInfo binanceInfo = BinanceInfo.getBinanceInfo(); //!Don't touch
        RealTimeCommandOperator realTimeCommandOperator = new RealTimeCommandOperator();
        TelegramMessenger.sendToTelegram("Start running: " + new Date(System.currentTimeMillis()));
        try {
            realTimeCommandOperator.run();
        } catch (InterruptedException e) {
            e.printStackTrace();
        }
    }
}


