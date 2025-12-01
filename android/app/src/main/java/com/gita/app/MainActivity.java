package com.gita.app;

import android.os.Bundle;
import android.speech.tts.TextToSpeech;
import android.speech.tts.Voice;
import android.speech.tts.UtteranceProgressListener;
import android.webkit.JavascriptInterface;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import androidx.appcompat.app.AppCompatActivity;

import java.util.Arrays;
import java.util.HashSet;
import java.util.Locale;
import java.util.Set;

public class MainActivity extends AppCompatActivity {

    private WebView webView;
    private TextToSpeech tts;
    private boolean ttsReady = false;

    private String pendingText = null;
    private String pendingGender = "female";
    private String pendingSpeed  = "slow";

    // FULL male voice pattern list
    private final Set<String> MALE_PATTERNS = new HashSet<>(Arrays.asList(
            "male", "mal", "man", "m1", "m2",
            "hi-in-standard-b", "hi-in-standard-d", "hi-in-standard-e",
            "hi-in-wavenet-b", "hi-in-wavenet-d", "hi-in-wavenet-e",
            "google_hindi_male", "google-hindi-male", "hindi-male",
            "hi-in-x-hid-m", "hi-in-x-hia-m",
            "x-hid-local", "x-hid-network",
            "x-hia-local", "x-hia-network"
    ));

    private final Set<String> FEMALE_PATTERNS = new HashSet<>(Arrays.asList(
            "female", "fem", "woman", "w1", "w2",
            "hi-in-standard-a", "hi-in-standard-c"
    ));

    @Override
    protected void onCreate(Bundle b) {
        super.onCreate(b);

        webView = new WebView(this);
        setContentView(webView);

        webView.getSettings().setJavaScriptEnabled(true);
        webView.setWebViewClient(new WebViewClient());
        webView.addJavascriptInterface(new JSBridge(), "Android");

        tts = new TextToSpeech(this, status -> {
            if (status == TextToSpeech.SUCCESS) {
                ttsReady = true;
                try { tts.setLanguage(new Locale("hi", "IN")); } catch (Exception ignored) {}

                setVoiceInternal("female");

                if (pendingText != null) {
                    speakInternal(pendingText, pendingGender, pendingSpeed);
                    pendingText = null;
                }
            }
        });

        webView.loadUrl("file:///android_asset/html/gita_shlokas.html");
    }


    // ============================================================
    // JS → Android Bridge
    // ============================================================
    private class JSBridge {
        @JavascriptInterface
        public void speak(String txt, String gender, String speed) {
            speakInternal(txt, gender, speed);
        }

        @JavascriptInterface
        public void stopSpeak() {
            try { tts.stop(); } catch (Exception ignored) {}
        }

        @JavascriptInterface
        public void setVoice(String gender) {
            setVoiceInternal(gender);
        }

        @JavascriptInterface
        public void setSpeed(String speed) {
            float rate = speed.equals("very_slow") ? 0.72f :
                         speed.equals("slow")      ? 0.82f :
                                                     0.95f;
            try { tts.setSpeechRate(rate); } catch (Exception ignored) {}
        }

        @JavascriptInterface
        public void exitApp() {
            finish();
        }
    }

    // ============================================================
    // BEST Voice Selection Engine for all Android devices
    // ============================================================
    private void setVoiceInternal(String gender) {
        if (tts == null) return;
        Voice best = null;

        try {
            for (Voice v : tts.getVoices()) {
                String n = v.getName().toLowerCase();

                if (gender.equals("male")) {
                    for (String p : MALE_PATTERNS) {
                        if (n.contains(p)) { best = v; break; }
                    }
                } else {
                    for (String p : FEMALE_PATTERNS) {
                        if (n.contains(p)) { best = v; break; }
                    }
                }
                if (best != null) break;
            }

            // fallback: ANY Hindi voice
            if (best == null) {
                for (Voice v : tts.getVoices()) {
                    if (v.getLocale().getLanguage().equals("hi")) {
                        best = v;
                        break;
                    }
                }
            }

            if (best != null) tts.setVoice(best);

        } catch (Exception ignored) {}
    }

    // ============================================================
    // SPEAK ENGINE + CALLBACK
    // ============================================================
    private void speakInternal(String text, String gender, String speed) {
        if (!ttsReady) {
            pendingText  = text;
            pendingGender = gender;
            pendingSpeed  = speed;
            return;
        }

        setVoiceInternal(gender);

        float rate = speed.equals("very_slow") ? 0.72f :
                     speed.equals("slow")      ? 0.82f : 0.95f;
        tts.setSpeechRate(rate);

        tts.setOnUtteranceProgressListener(new UtteranceProgressListener() {
            @Override public void onStart(String id) {}

            @Override public void onDone(String id) {
                runOnUiThread(() ->
                    webView.evaluateJavascript("onSpeakComplete();", null)
                );
            }

            @Override public void onError(String id) {}
        });

        tts.speak(text, TextToSpeech.QUEUE_FLUSH, null, "UTTID");
    }

    @Override
    protected void onDestroy() {
        super.onDestroy();
        try { tts.stop(); tts.shutdown(); } catch (Exception ignored) {}
    }
}
