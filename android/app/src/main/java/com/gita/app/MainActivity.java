package com.gita.app;

import android.annotation.SuppressLint;
import android.os.Bundle;
import android.speech.tts.TextToSpeech;
import android.speech.tts.UtteranceProgressListener;
import android.speech.tts.Voice;
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

                // default pitch/voice
                applyVoiceAndPitch("female");

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

    private Voice findVoiceByGender(String gender) {
        if (tts == null) return null;
        try {
            Set<Voice> voices = tts.getVoices();
            if (voices == null) return null;

            // 1) prefer hi-IN locale voices and names indicating male/female
            for (Voice v : voices) {
                Locale loc = v.getLocale();
                String name = v.getName().toLowerCase();
                if (loc != null && "hi".equals(loc.getLanguage())) {
                    if (gender.equals("male") && (name.contains("male") || name.contains("b") || name.contains("m"))) {
                        return v;
                    }
                    if (gender.equals("female") && (name.contains("female") || name.contains("a") || name.contains("c"))) {
                        return v;
                    }
                }
            }

            // 2) fallback: any hi locale voice
            for (Voice v : voices) {
                Locale loc = v.getLocale();
                if (loc != null && "hi".equals(loc.getLanguage())) return v;
            }

            // 3) last resort: first available voice
            for (Voice v : voices) return v;

        } catch (Exception ignored) {}
        return null;
    }

    private void applyVoiceAndPitch(String gender) {
        try {
            Voice v = findVoiceByGender(gender);
            if (v != null) {
                try { tts.setVoice(v); } catch (Exception ignored) {}
            }
        } catch (Exception ignored) {}

        // If no explicit male voice is found, lower pitch a bit for "male" to give male-sounding result
        try {
            if ("male".equalsIgnoreCase(gender)) tts.setPitch(0.9f);
            else tts.setPitch(1.05f);
        } catch (Exception ignored) {}
    }

    private class JsBridge {
        @JavascriptInterface
        public void speak(String text, String gender, String speed) {
            speakInternal(text, gender, speed);
        }

        @JavascriptInterface
        public void stopSpeak() {
            try { if (tts != null) tts.stop(); } catch (Exception ignored) {}
        }

        @JavascriptInterface
        public void setVoice(String gender) {
            try { applyVoiceAndPitch(gender); } catch (Exception ignored) {}
        }

        @JavascriptInterface
        public void setSpeed(String speed) {
            try {
                float rate = 0.82f;
                if ("very_slow".equalsIgnoreCase(speed)) rate = 0.72f;
                else if ("medium".equalsIgnoreCase(speed)) rate = 0.95f;
                tts.setSpeechRate(rate);
            } catch (Exception ignored) {}
        }

        @JavascriptInterface
        public boolean isSpeaking() {
            try { return tts != null && tts.isSpeaking(); } catch (Exception e) { return false; }
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

        if (gender == null) gender = "female";
        if (speed == null) speed = "slow";

        // apply voice & pitch first
        applyVoiceAndPitch(gender);

        // set rate
        float rate = 0.82f;
        if ("very_slow".equalsIgnoreCase(speed)) rate = 0.72f;
        else if ("medium".equalsIgnoreCase(speed)) rate = 0.95f;
        try { tts.setSpeechRate(rate); } catch (Exception ignored) {}

        // Utterance listener -> call JS callback on completion
        tts.setOnUtteranceProgressListener(new UtteranceProgressListener() {
            @Override public void onStart(String utteranceId) {}
            @Override public void onDone(String utteranceId) {
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
            try {
                tts.setLanguage(new Locale("hi", "IN"));
                tts.speak(text, TextToSpeech.QUEUE_FLUSH, null, "GITA_TTS");
            } catch (Exception ignored) {}
        }
    }
}
