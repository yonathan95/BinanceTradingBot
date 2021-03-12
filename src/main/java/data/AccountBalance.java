package data;

import com.binance.client.SyncRequestClient;
import com.binance.client.model.trade.AccountInformation;
import com.binance.client.model.trade.Asset;
import com.binance.client.model.trade.Position;
import singletonHelpers.RequestClient;

import java.math.BigDecimal;
import java.util.ArrayList;
import java.util.List;
import java.util.Set;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.locks.ReadWriteLock;
import java.util.concurrent.locks.ReentrantReadWriteLock;

public class AccountBalance {
    private ConcurrentHashMap<String, Asset> assets;
    private ConcurrentHashMap<String, Position> positions;
    private final ReadWriteLock assetsLock = new ReentrantReadWriteLock();
    private final ReadWriteLock positionsLock = new ReentrantReadWriteLock();

    private static class AccountBalanceHolder {
        private static AccountBalance accountBalance = new AccountBalance();
    }

    private AccountBalance() {
        assets = new ConcurrentHashMap<>();
        positions = new ConcurrentHashMap<>();
        SyncRequestClient syncRequestClient = RequestClient.getRequestClient().getSyncRequestClient();
        AccountInformation accountInformation = syncRequestClient.getAccountInformation();
        for (Position position : accountInformation.getPositions())
            positions.put(position.getSymbol().toLowerCase(), position);
        for (Asset asset : accountInformation.getAssets()) assets.put(asset.getAsset().toLowerCase(), asset);
    }

    public static AccountBalance getAccountBalance() {
        return AccountBalanceHolder.accountBalance;
    }

    public BigDecimal getCoinBalance(String symbol) {
        assetsLock.readLock().lock();
        if (assets.containsKey(symbol)) {
            BigDecimal coinBalance = assets.get(symbol).getWalletBalance();
            assetsLock.readLock().unlock();
            return coinBalance;
        }
        assetsLock.readLock().unlock();
        return null;
    }

    public Position getPosition(String symbol) {
        positionsLock.readLock().lock();
        if (positions.containsKey(symbol)) {
            Position position = positions.get(symbol);
            positionsLock.readLock().unlock();
            return position;
        }
        positionsLock.readLock().unlock();
        return null;
    }

    public void updateBalance() {
        ConcurrentHashMap<String, Asset> newAssets = new ConcurrentHashMap<>();
        ConcurrentHashMap<String, Position> newPositions = new ConcurrentHashMap<>();
        SyncRequestClient syncRequestClient = RequestClient.getRequestClient().getSyncRequestClient();
        AccountInformation accountInformation = syncRequestClient.getAccountInformation();
        for (Position position : accountInformation.getPositions())
            newPositions.put(position.getSymbol().toLowerCase(), position);
        for (Asset asset : accountInformation.getAssets()) newAssets.put(asset.getAsset().toLowerCase(), asset);
        positionsLock.writeLock().lock();
        positions = newPositions;
        positionsLock.writeLock().unlock();
        assetsLock.writeLock().lock();
        assets = newAssets;
        assetsLock.writeLock().unlock();
    }

    public List<Position> getOpenPositions() {
        List<Position> openPositions = new ArrayList<>();
        positionsLock.readLock().lock();
        Set<String> keys = positions.keySet();
        for (String key : keys) {
            Position position = positions.get(key);
            if (position.getPositionAmt().compareTo(BigDecimal.valueOf(0.0)) > 0) {
                openPositions.add(position);
            }
        }
        positionsLock.readLock().unlock();
        return openPositions;
    }
}
