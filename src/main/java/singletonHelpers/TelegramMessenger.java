package singletonHelpers;

import data.Config;

import java.io.BufferedInputStream;
import java.io.InputStream;
import java.net.URL;
import java.net.URLConnection;

public class TelegramMessenger {
    private static String apiToken = Config.TELEGRAM_API_TOKEN;
    private static String chatId = Config.TELEGRAM_CHAT_ID;

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
