package com.gita.app; // update to your actual package

import android.annotation.SuppressLint;
import android.os.Bundle;
import android.speech.tts.TextToSpeech;
import android.speech.tts.Voice;
import android.util.Log;
import android.webkit.JavascriptInterface;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import androidx.annotation.Nullable;
import androidx.appcompat.app.AppCompatActivity;
import java.util.HashSet;
import java.util.Locale;
import java.util.Set;

public class MainActivity extends AppCompatActivity {

    private WebView webView;
    private TextToSpeech tts;
    private boolean ttsReady = false;
    private String pendingText = null;

    private final String FEMALE_VOICE = "hi-IN-Standard-A"; // preferred female
    private final String MALE_VOICE = "hi-IN-Standard-B";   // preferred male

    @Override
    protected void onCreate(@Nullable Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        // Make sure you have a layout with a WebView (or create one programmatically)
        webView = new WebView(this);
        setContentView(webView);

        webView.getSettings().setJavaScriptEnabled(true);
        webView.setWebViewClient(new WebViewClient());

        // Add JS interface names used by HTML: Android
        webView.addJavascriptInterface(new JsBridge(), "Android");

        // Init TTS
        tts = new TextToSpeech(this, status -> {
            if (status == TextToSpeech.SUCCESS) {
                ttsReady = true;
                // set default locale and voice
                try {
                    Locale lok = new Locale("hi", "IN");
                    int res = tts.setLanguage(lok);
                    // try to set preferred voice if available
                    for (Voice v : tts.getVoices()) {
                        if (v.getName().contains(FEMALE_VOICE)) {
                            tts.setVoice(v);
                            break;
                        }
                    }
                } catch (Exception e) {
                    Log.w("MainActivity", "tts init voice set failed", e);
                }
                if (pendingText != null) {
                    speakInternal(pendingText, "female", "slow");
                    pendingText = null;
                }
            } else {
                ttsReady = false;
            }
        });

        // Load the local HTML file (assets)
        webView.loadUrl("file:///android_asset/html/gita_shlokas.html");
    }

    @Override
    protected void onDestroy() {
        super.onDestroy();
        if (tts != null) {
            try {
                tts.stop();
                tts.shutdown();
            } catch (Exception e) { }
        }
    }

    @SuppressLint("SetJavaScriptEnabled")
    private class JsBridge {

        @JavascriptInterface
        public void speak(String text, String gender, String speed) {
            speakInternal(text, gender, speed);
        }

        @JavascriptInterface
        public void stopSpeak() {
            try {
                if (tts != null) tts.stop();
            } catch (Exception e) { }
        }

        @JavascriptInterface
        public void setVoice(String gender) {
            // switch voice; gender = "female" or "male"
            try {
                if (tts == null) return;
                String target = FEMALE_VOICE;
                if ("male".equalsIgnoreCase(gender)) target = MALE_VOICE;
                for (Voice v : tts.getVoices()) {
                    if (v.getName().contains(target)) {
                        tts.setVoice(v);
                        break;
                    }
                }
            } catch (Exception e) { }
        }

        @JavascriptInterface
        public void setSpeed(String speed) {
            // speed: "very_slow", "slow", "medium"
            float rate = 0.82f;
            if ("very_slow".equalsIgnoreCase(speed)) rate = 0.72f;
            else if ("slow".equalsIgnoreCase(speed)) rate = 0.82f;
            else if ("medium".equalsIgnoreCase(speed)) rate = 0.95f;
            try {
                if (tts != null) tts.setSpeechRate(rate);
            } catch (Exception e) { }
        }

        @JavascriptInterface
        public void exitApp() {
            finish();
        }
    }

    private void speakInternal(String text, String gender, String speed) {
        if (!ttsReady) {
            pendingText = text;
            return;
        }

        // set voice
        try {
            String target = FEMALE_VOICE;
            if ("male".equalsIgnoreCase(gender)) target = MALE_VOICE;

            for (Voice v : tts.getVoices()) {
                if (v.getName().contains(target)) {
                    tts.setVoice(v);
                    break;
                }
            }
        } catch (Exception e) { /* ignore */ }

        float rate = 0.82f;
        if ("very_slow".equalsIgnoreCase(speed)) rate = 0.72f;
        else if ("slow".equalsIgnoreCase(speed)) rate = 0.82f;
        else if ("medium".equalsIgnoreCase(speed)) rate = 0.95f;

        try {
            tts.setSpeechRate(rate);
            tts.speak(text, TextToSpeech.QUEUE_FLUSH, null, "GITA_TTS");
        } catch (Exception e) {
            // fallback: set locale hi-IN and speak
            try {
                tts.setLanguage(new Locale("hi", "IN"));
                tts.speak(text, TextToSpeech.QUEUE_FLUSH, null, "GITA_TTS");
            } catch (Exception ex) {
                // give up quietly
            }
        }
    }
}
