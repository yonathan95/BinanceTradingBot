package codeExecution;

import data.AccountBalance;
import data.Config;
import singletonHelpers.ExecService;
import singletonHelpers.RequestClient;
import com.binance.client.SyncRequestClient;
import com.binance.client.model.enums.*;
import com.binance.client.model.trade.MyTrade;
import com.binance.client.model.trade.Order;
import com.binance.client.model.trade.Position;
import org.apache.commons.lang3.tuple.MutablePair;
import org.apache.commons.lang3.tuple.Pair;
import singletonHelpers.SubClient;

import java.util.*;
import java.util.concurrent.ConcurrentLinkedDeque;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.locks.ReadWriteLock;
import java.util.concurrent.locks.ReentrantReadWriteLock;


public class RealTimeCommandOperator {
    private final HashMap<String, RealTimeOperation> commandsAndOps;
    private final HashMap<Pair<String, CandlestickInterval>, InvestmentManager> investmentManagerHashMap;
    private final ReadWriteLock investmentManagerHashMapLock = new ReentrantReadWriteLock();
    private final ConcurrentLinkedDeque<InputMessage> awaitingMessages;
    private boolean shouldTerminate = false;

    public RealTimeCommandOperator() {
        investmentManagerHashMap = new HashMap<>();
        commandsAndOps = new HashMap<>();
        awaitingMessages = new ConcurrentLinkedDeque<>();

        commandsAndOps.put(RealTImeOperations.CANCEL_ALL_ORDERS, (message) -> {
            SyncRequestClient syncRequestClient = RequestClient.getRequestClient().getSyncRequestClient();
            syncRequestClient.cancelAllOpenOrder(message.getSymbol());
        });

        commandsAndOps.put(RealTImeOperations.CLOSE_ALL_POSITIONS, (message) -> {
            List<Position> openPositions = AccountBalance.getAccountBalance().getOpenPositions();
            for (Position openPosition : openPositions) {
                SyncRequestClient syncRequestClient = RequestClient.getRequestClient().getSyncRequestClient();
                if (! openPosition.getPositionSide().equals("SHORT")) {
                    syncRequestClient.postOrder(openPosition.getSymbol().toLowerCase(), OrderSide.SELL, null, OrderType.MARKET, null,
                            openPosition.getPositionAmt().toString(), null, Config.REDUCE_ONLY, null, null, null,null,null, null, null, NewOrderRespType.RESULT);
                } else {
                    syncRequestClient.postOrder(openPosition.getSymbol().toLowerCase(), OrderSide.BUY, null, OrderType.MARKET, null,
                            openPosition.getPositionAmt().toString(), null, Config.REDUCE_ONLY, null, null, null,null,null, null, null, NewOrderRespType.RESULT);
                }
            }
        });

        commandsAndOps.put(RealTImeOperations.ACTIVATE_STRATEGY, (message) -> {
            Pair<String, CandlestickInterval> pair = new MutablePair<>(message.getSymbol(), message.getInterval());
            investmentManagerHashMapLock.readLock().lock();
            if (investmentManagerHashMap.containsKey(pair)) {
                investmentManagerHashMap.get(pair).addEntryStrategy(message.getEntryStrategy());
                investmentManagerHashMapLock.readLock().unlock();
            } else {
                investmentManagerHashMapLock.readLock().unlock();
                investmentManagerHashMapLock.writeLock().lock();
                InvestmentManager investmentManager = new InvestmentManager(message.getInterval(), message.getSymbol(), message.getEntryStrategy());
                investmentManagerHashMap.put(pair, investmentManager);
                investmentManagerHashMapLock.writeLock().unlock();
                investmentManager.run();
            }
        });

        commandsAndOps.put(RealTImeOperations.DEACTIVATE_STRATEGY, (message) -> {
            Pair<String, CandlestickInterval> pair = new MutablePair<>(message.getSymbol(), message.getInterval());
            investmentManagerHashMapLock.readLock().lock();
            if (investmentManagerHashMap.containsKey(pair)) {
                investmentManagerHashMap.get(pair).removeEntryStrategy(message.getEntryStrategy());
                investmentManagerHashMapLock.readLock().unlock();
            }
        });

        commandsAndOps.put(RealTImeOperations.GET_LAST_TRADES, (message) -> {
            SyncRequestClient syncRequestClient = RequestClient.getRequestClient().getSyncRequestClient();
            List<MyTrade> myTrades = syncRequestClient.getAccountTrades(message.getSymbol(),null,null,null, 100);
            int index = 1;
            for (MyTrade trade : myTrades) {
                System.out.println("Trade " + index + ": " + trade);
                index++;
            }
        });

        commandsAndOps.put(RealTImeOperations.GET_OPEN_POSITIONS, (message) -> {
            List<Position> openPositions = AccountBalance.getAccountBalance().getOpenPositions();
            int index = 1;
            for (Position openPosition : openPositions) {
                System.out.println("Open position " + index + ": " + openPosition);
                index++;
            }
        });

        commandsAndOps.put(RealTImeOperations.GET_OPEN_ORDERS, (message) -> {
            SyncRequestClient syncRequestClient = RequestClient.getRequestClient().getSyncRequestClient();
            List<Order> openOrders = syncRequestClient.getOpenOrders(message.getSymbol());
            int index = 1;
            for (Order openOrder : openOrders) {
                System.out.println("Open order: " + index + ": " + openOrder);
                index++;
            }
        });

        commandsAndOps.put(RealTImeOperations.GET_CURRENT_BALANCE, (message) -> System.out.println("Your current balance is: " +
                AccountBalance.getAccountBalance().getCoinBalance(message.getSymbol())));

        commandsAndOps.put(RealTImeOperations.CLOSE_PROGRAM, (message) -> {
            SubClient.getSubClient().getSubscriptionClient().unsubscribeAll();
            ExecutorService executorService = ExecService.getExecService().getExecutorService();
            executorService.shutdown();
            try {
                if (!executorService.awaitTermination(800, TimeUnit.MILLISECONDS)) {
                    executorService.shutdownNow();
                }
            } catch (InterruptedException e) {
                executorService.shutdownNow();
            }
        });
    }

    public void run() throws InterruptedException {
        Thread realTimeCommandOperatorThread = new Thread(new KeyboardReader());
        realTimeCommandOperatorThread.start();
        synchronized (awaitingMessages) {
            while (!shouldTerminate) {
                InputMessage message = awaitingMessages.poll();
                if (message == null) {
                    awaitingMessages.wait();
                }
                else {
                    if (commandsAndOps.containsKey(message.getOperation())) {
                        commandsAndOps.get(message.getOperation()).run(message);
                    }
                }
            }
        }
    }
    private class KeyboardReader implements Runnable{
        public void run() {
            Scanner scan= new Scanner(System.in);
            while (true) {
                try {
                    InputMessage message = new InputMessage();
                    String input = scan.nextLine();
                    message.initialize(input);
                    String messageOperation = message.getOperation();
                    if (! messageOperation.equals(RealTImeOperations.UNKNOWN_OPERATION)){
                        synchronized (awaitingMessages) {
                            awaitingMessages.add(message);
                            awaitingMessages.notifyAll();
                        }
                        if (messageOperation.equals(RealTImeOperations.CLOSE_PROGRAM))break;
                    }
                } catch (Exception e) {
                    e.printStackTrace();
                }
            }
        }
    }

}
