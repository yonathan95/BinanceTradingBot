package codeExecution;

import java.util.Date;
import java.util.concurrent.*;

import data.*;
import positions.PositionHandler;
import singletonHelpers.TelegramMessenger;
import strategies.EntryStrategy;
import com.binance.client.SubscriptionClient;
import com.binance.client.model.enums.*;
import singletonHelpers.ExecService;
import singletonHelpers.SubClient;

public class InvestmentManager implements Runnable{
    private final CandlestickInterval interval;
    private final String symbol;
    ConcurrentLinkedDeque<EntryStrategy> entryStrategies;
    ConcurrentLinkedDeque<PositionHandler> positionHandlers;
    ConcurrentLinkedDeque<Future<?>> futures;



    public InvestmentManager(CandlestickInterval interval, String symbol, EntryStrategy entryStrategy) {
        this.interval = interval;
        this.symbol = symbol;
        entryStrategies = new ConcurrentLinkedDeque<>();
        positionHandlers = new ConcurrentLinkedDeque<>();
        futures = new ConcurrentLinkedDeque<>();
        entryStrategies.add(entryStrategy);
    }

    public void run(){
        RealTimeData realTimeData = new RealTimeData(symbol, interval);
        SubscriptionClient subscriptionClient = SubClient.getSubClient().getSubscriptionClient();
        ExecutorService iterationExecutorService = ExecService.getExecService().getExecutorService();
        TelegramMessenger.sendToTelegram(symbol + " balance:  " + AccountBalance.getAccountBalance().getCoinBalance("usdt") +", " + new Date(System.currentTimeMillis()));

        subscriptionClient.subscribeCandlestickEvent(symbol, interval, ((event) -> iterationExecutorService.execute(()->{
            DataHolder dataHolder = realTimeData.updateData(event);
            if (dataHolder != null){
                AccountBalance.getAccountBalance().updateBalance();
                for (PositionHandler positionHandler :positionHandlers){
                    positionHandler.update(dataHolder, interval);
                    if (positionHandler.isSoldOut()){
                        positionHandler.terminate();
                        positionHandlers.remove(positionHandler);
                    }
                    else{
                        positionHandler.run(dataHolder);
                    }
                }
                for (EntryStrategy entryStrategy: entryStrategies){
                    PositionHandler positionHandler = entryStrategy.run(dataHolder, symbol);
                    if (positionHandler != null){
                        positionHandlers.add(positionHandler);
                    }
                }
            }
        })), System.out::println);
    }

    public void addEntryStrategy(EntryStrategy entryStrategy){
        entryStrategies.add(entryStrategy);
    }

    public void removeEntryStrategy(EntryStrategy entryStrategy) {
        entryStrategies.remove(entryStrategy);
    }

}
