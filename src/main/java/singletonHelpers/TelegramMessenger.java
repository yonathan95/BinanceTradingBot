package singletonHelpers;

import java.io.BufferedInputStream;
import java.io.IOException;
import java.io.InputStream;
import java.net.URL;
import java.net.URLConnection;

public class TelegramMessenger {
    private static String apiToken = "1493781452:AAGDIQ2nVL4NIu2xEstyyprFY6J04kQbDsA";
    private static String chatId = "-482820044";


    public static synchronized void sendToTelegram(String text) {
        String urlString = "https://api.telegram.org/bot%s/sendMessage?chat_id=%s&text=%s";
        urlString = String.format(urlString, apiToken, chatId, text);

        try {
            URL url = new URL(urlString);
            URLConnection conn = url.openConnection();
            InputStream is = new BufferedInputStream(conn.getInputStream());
        } catch (Exception ignored) {}
    }
}
