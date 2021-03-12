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

    private static class AccountBalanceHolder{
        private static AccountBalance accountBalance = new AccountBalance();
    }

    private AccountBalance(){
        assets = new ConcurrentHashMap<>();
        positions = new ConcurrentHashMap<>();
        SyncRequestClient syncRequestClient = RequestClient.getRequestClient().getSyncRequestClient();
        AccountInformation accountInformation = syncRequestClient.getAccountInformation();
        for (Position position: accountInformation.getPositions())positions.put(position.getSymbol().toLowerCase(), position);
        for (Asset asset: accountInformation.getAssets())assets.put(asset.getAsset().toLowerCase(), asset);
    }

    public static AccountBalance getAccountBalance() {
        return AccountBalanceHolder.accountBalance;
    }

    public BigDecimal getCoinBalance(String symbol) {
        if (assets.containsKey(symbol)){
            BigDecimal coinBalance = assets.get(symbol).getWalletBalance();
            return coinBalance;
        }
        return null;
    }

    public Position getPosition(String symbol) {
        if (positions.containsKey(symbol)){
            Position position = positions.get(symbol);
            return position;
        }
        return null;
    }

    public void updateBalance(String symbol, String baseCoin){
        SyncRequestClient syncRequestClient = RequestClient.getRequestClient().getSyncRequestClient();
        AccountInformation accountInformation = syncRequestClient.getAccountInformation();
        for (Position position: accountInformation.getPositions()){
            if (position.getSymbol().toLowerCase().equals(symbol)) positions.put(symbol, position);
        }
        for (Asset asset: accountInformation.getAssets()){
            if (asset.getAsset().toLowerCase().equals(baseCoin)) assets.put(baseCoin, asset);
        }
    }

//    public PositionHandler manageOldPositions(String symbol) {
//        BigDecimal positionAmt = getPosition(symbol).getPositionAmt();
//        if (positionAmt.compareTo(BigDecimal.valueOf(0.0)) > Config.ZERO){
//            return new PositionHandler(positionAmt);//TODO: add default exit strategy
//        }
//        return null;
//    }

//    public List<Position> getOpenPositions() {
//        List<Position> openPositions = new ArrayList<>();
//        Set<String> keys = positions.keySet();
//        for (String key: keys){
//            Position position = positions.get(key);
//            if (position.getPositionAmt().compareTo(BigDecimal.valueOf(0.0)) > 0){
//                openPositions.add(position);
//            }
//        }
//        return openPositions;
//    }
}

//TODO: Think about the possibility where a new asset occurs
