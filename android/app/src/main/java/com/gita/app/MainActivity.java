package com.gita.app;

import android.annotation.SuppressLint;
import android.os.Bundle;
import android.speech.tts.TextToSpeech;
import android.speech.tts.UtteranceProgressListener;
import android.speech.tts.Voice;
import android.util.Log;
import android.webkit.JavascriptInterface;
import android.webkit.WebView;
import android.webkit.WebViewClient;

import androidx.annotation.Nullable;
import androidx.appcompat.app.AppCompatActivity;

import java.util.Locale;

public class MainActivity extends AppCompatActivity {

    private WebView webView;
    private TextToSpeech tts;
    private boolean ttsReady = false;
    private String pendingText = null;

    @Override
    protected void onCreate(@Nullable Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        webView = new WebView(this);
        setContentView(webView);

        webView.getSettings().setJavaScriptEnabled(true);
        webView.setWebViewClient(new WebViewClient());
        webView.addJavascriptInterface(new JsBridge(), "Android");

        // INIT TTS
        tts = new TextToSpeech(this, status -> {
            if (status == TextToSpeech.SUCCESS) {
                ttsReady = true;
                try {
                    tts.setLanguage(new Locale("hi", "IN"));
                    applyVoice("female"); // Default female
                } catch (Exception ignored) {}

                if (pendingText != null) {
                    speakInternal(pendingText, "female", "slow");
                    pendingText = null;
                }
            }
        });

        webView.loadUrl("file:///android_asset/html/gita_shlokas.html");
    }

    @Override
    protected void onDestroy() {
        super.onDestroy();
        try {
            tts.stop();
            tts.shutdown();
        } catch (Exception ignored) {}
    }

    // =======================================================================
    // UNIVERSAL VOICE DETECTION — WORKS ON ALL ANDROID DEVICES (MALE FIXED)
    // =======================================================================
    private Voice findVoice(String gender) {
        try {
            for (Voice v : tts.getVoices()) {
                String name = v.getName().toLowerCase();

                // Detect MALE voices
                if (gender.equals("male")) {
                    if (name.contains("male") ||
                        name.contains("standard-b") ||
                        name.contains("standard-d") ||
                        name.contains("male-local") ||
                        name.endsWith("-m") ) {
                        return v;
                    }
                }

                // Detect FEMALE voices
                if (gender.equals("female")) {
                    if (name.contains("female") ||
                        name.contains("standard-a") ||
                        name.contains("standard-c") ||
                        name.contains("female-local") ||
                        name.endsWith("-f") ) {
                        return v;
                    }
                }
            }
        } catch (Exception ignored) {}
        return null;
    }

    private void applyVoice(String gender) {
        Voice v = findVoice(gender);
        if (v != null) {
            try { tts.setVoice(v); } catch (Exception ignored) {}
        }
    }

    // =======================================================================
    // JS BRIDGE
    // =======================================================================
    private class JsBridge {

        @JavascriptInterface
        public void speak(String text, String gender, String speed) {
            speakInternal(text, gender, speed);
        }

        @JavascriptInterface
        public boolean isSpeaking() {
            try { return tts != null && tts.isSpeaking(); }
            catch (Exception e) { return false; }
        }

        @JavascriptInterface
        public void stopSpeak() {
            try { if (tts != null) tts.stop(); }
            catch (Exception ignored) {}
        }

        @JavascriptInterface
        public void setVoice(String gender) {
            applyVoice(gender);
        }

        @JavascriptInterface
        public void setSpeed(String speed) {
            float rate = 0.82f;
            if (speed.equals("very_slow")) rate = 0.72f;
            else if (speed.equals("medium")) rate = 0.95f;

            try { tts.setSpeechRate(rate); }
            catch (Exception ignored) {}
        }

        @JavascriptInterface
        public void exitApp() {
            finish();
        }
    }

    // =======================================================================
    // TTS ENGINE
    // =======================================================================
    private void speakInternal(String text, String gender, String speed) {
        if (!ttsReady) {
            pendingText = text;
            return;
        }

        // Select voice
        applyVoice(gender);

        // Speech speed
        float rate = 0.82f;
        if ("very_slow".equals(speed)) rate = 0.72f;
        else if ("medium".equals(speed)) rate = 0.95f;
        tts.setSpeechRate(rate);

        // Notify JS when reading completes
        tts.setOnUtteranceProgressListener(new UtteranceProgressListener() {
            @Override public void onStart(String id) {}

            @Override
            public void onDone(String id) {
                runOnUiThread(() ->
                    webView.evaluateJavascript("onSpeakComplete();", null)
                );
            }

            @Override public void onError(String id) {}
        });

        // Speak
        try {
            tts.speak(text, TextToSpeech.QUEUE_FLUSH, null, "GITA_TTS");
        } catch (Exception ignored) {}
    }
}
