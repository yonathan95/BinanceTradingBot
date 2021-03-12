package singletonHelpers;

import data.Config;
import com.binance.client.SubscriptionClient;

public class SubClient {
    private SubscriptionClient subscriptionClient;

    private static class SubClientHolder {
        private static SubClient subClient = new SubClient();
    }
    private SubClient() {
        subscriptionClient = SubscriptionClient.create(Config.API_KEY, Config.SECRET_KEY);
    }

    public static SubClient getSubClient(){
        return SubClientHolder.subClient;
    }
    public SubscriptionClient getSubscriptionClient() {
        return subscriptionClient;
    }
}
