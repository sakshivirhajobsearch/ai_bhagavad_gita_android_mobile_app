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
import java.util.Set;

public class MainActivity extends AppCompatActivity {

    private WebView webView;
    private TextToSpeech tts;
    private boolean ttsReady = false;
    private String pendingText = null;
    private String pendingGender = "female";
    private String pendingSpeed = "slow";

    @Override
    protected void onCreate(@Nullable Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        webView = new WebView(this);
        setContentView(webView);

        webView.getSettings().setJavaScriptEnabled(true);
        webView.setWebViewClient(new WebViewClient());
        webView.addJavascriptInterface(new JsBridge(), "Android");

        tts = new TextToSpeech(this, status -> {
            if (status == TextToSpeech.SUCCESS) {
                ttsReady = true;
                try {
                    tts.setLanguage(new Locale("hi", "IN"));
                } catch (Exception ignored) {}

                // apply default female voice if available
                applyVoice("female");

                if (pendingText != null) {
                    speakInternal(pendingText, pendingGender, pendingSpeed);
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
            if (tts != null) {
                tts.stop();
                tts.shutdown();
            }
        } catch (Exception ignored) {}
    }

    // Robust voice detection across devices
    private Voice findVoice(String gender) {
        if (tts == null) return null;
        try {
            Set<Voice> voices = tts.getVoices();
            if (voices == null) return null;

            // Prefer explicit male/female markers in name
            for (Voice v : voices) {
                String name = v.getName().toLowerCase();
                if (gender.equals("male")) {
                    if (name.contains("male") || name.contains("standard-b") ||
                            name.contains("standard-d") || name.contains("-m") || name.contains("male_local") ||
                            name.contains("hi-in-x-hid") || name.contains("hi-in-x-hid-local"))
                        return v;
                } else {
                    if (name.contains("female") || name.contains("standard-a") ||
                            name.contains("standard-c") || name.contains("-f") || name.contains("female_local") ||
                            name.contains("hi-in-x-hia") || name.contains("hi-in-x-hia-local"))
                        return v;
                }
            }

            // If not found, try matching locale hi-IN voices first
            for (Voice v : voices) {
                if (v.getLocale() != null && v.getLocale().getLanguage().equals("hi")) {
                    String name = v.getName().toLowerCase();
                    if (gender.equals("male") && (name.contains("b") || name.contains("m") || name.contains("male")))
                        return v;
                    if (gender.equals("female") && (name.contains("a") || name.contains("c") || name.contains("female")))
                        return v;
                }
            }

            // fallback: first voice with hi locale
            for (Voice v : voices) {
                if (v.getLocale() != null && "hi".equals(v.getLocale().getLanguage())) return v;
            }

            // last resort: any voice
            for (Voice v : voices) return v;

        } catch (Exception ignored) {}
        return null;
    }

    private void applyVoice(String gender) {
        Voice v = findVoice(gender);
        if (v != null) {
            try { tts.setVoice(v); } catch (Exception ignored) {}
        }
    }

    private class JsBridge {

        @JavascriptInterface
        public void speak(String text, String gender, String speed) {
            speakInternal(text, gender, speed);
        }

        @JavascriptInterface
        public boolean isSpeaking() {
            try { return tts != null && tts.isSpeaking(); } catch (Exception e) { return false; }
        }

        @JavascriptInterface
        public void stopSpeak() {
            try { if (tts != null) tts.stop(); } catch (Exception ignored) {}
        }

        @JavascriptInterface
        public void setVoice(String gender) {
            try { applyVoice(gender); } catch (Exception ignored) {}
        }

        @JavascriptInterface
        public void setSpeed(String speed) {
            try {
                float rate = 0.82f;
                if ("very_slow".equals(speed)) rate = 0.72f;
                else if ("medium".equals(speed)) rate = 0.95f;
                tts.setSpeechRate(rate);
            } catch (Exception ignored) {}
        }

        @JavascriptInterface
        public void exitApp() {
            finish();
        }
    }

    private void speakInternal(String text, String gender, String speed) {
        if (!ttsReady) {
            pendingText = text;
            pendingGender = gender == null ? "female" : gender;
            pendingSpeed = speed == null ? "slow" : speed;
            return;
        }

        // set voice
        applyVoice(gender == null ? "female" : gender);

        // set speed
        float rate = 0.82f;
        if ("very_slow".equals(speed)) rate = 0.72f;
        else if ("medium".equals(speed)) rate = 0.95f;
        try { tts.setSpeechRate(rate); } catch (Exception ignored) {}

        // set utterance listener — notify JS when done
        tts.setOnUtteranceProgressListener(new UtteranceProgressListener() {
            @Override public void onStart(String utteranceId) {}

            @Override
            public void onDone(String utteranceId) {
                runOnUiThread(() -> {
                    try {
                        webView.evaluateJavascript("onSpeakComplete();", null);
                    } catch (Exception ignored) {}
                });
            }

            @Override public void onError(String utteranceId) {}
        });

        try {
            tts.speak(text, TextToSpeech.QUEUE_FLUSH, null, "GITA_TTS");
        } catch (Exception e) {
            // fallback: try resetting locale and speak
            try {
                tts.setLanguage(new Locale("hi", "IN"));
                tts.speak(text, TextToSpeech.QUEUE_FLUSH, null, "GITA_TTS");
            } catch (Exception ignored) {}
        }
    }
}
