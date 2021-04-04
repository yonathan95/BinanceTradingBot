import data.*;
import singletonHelpers.BinanceInfo;
import codeExecution.RealTimeCommandOperator;
import singletonHelpers.TelegramMessenger;

import java.time.ZonedDateTime;
import java.util.Date;

public class Main {
    public static void main(String[] args) {
        Config config = new Config();
        AccountBalance accountBalance = AccountBalance.getAccountBalance();
        BinanceInfo binanceInfo = BinanceInfo.getBinanceInfo();
        RealTimeCommandOperator realTimeCommandOperator = new RealTimeCommandOperator();
        TelegramMessenger.sendToTelegram("Start running: " + new Date(System.currentTimeMillis()));
        System.out.println(Config.CANDLE_NUM);
        try {
            realTimeCommandOperator.run();
        } catch (InterruptedException e) {
            e.printStackTrace();
        }
    }
}


