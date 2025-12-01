import os
import webbrowser
from data.shlokas import ALL_SHLOKAS

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_HTML = os.path.join(
    BASE_DIR,
    "android", "app", "src", "main", "assets", "html", "gita_shlokas.html"
)

SHLOKAS_PER_PAGE = 2


def flatten_sections(all_sections):
    flat = []
    for sec in all_sections:
        if not isinstance(sec, dict):
            continue
        for title, shlok_list in sec.items():
            for s in shlok_list:
                chapter = s.get("chapter", "")
                verse = s.get("verse", "")

                reference = f"अध्याय {chapter} • श्लोक {verse}"

                flat.append({
                    "section": title,
                    "problem": title,
                    "reference": reference,
                    "text": s.get("sanskrit", "") or "—",
                    "meaning": s.get("hindi_arth", "") or "—",
                    "example": s.get("udaharan", "") or "—"
                })
    return flat


def js_escape(t):
    if t is None:
        return ""
    return (
        str(t)
        .replace("\\", "\\\\")
        .replace("`", "\\`")
        .replace("</", "<\\u002F")
        .replace("\r", "")
    )


def gen_js_array(flat):
    entries = []
    for i, s in enumerate(flat):
        entries.append(
            "        {\n"
            f"            id: {i},\n"
            f"            section: `{js_escape(s['section'])}`,\n"
            f"            problem: `{js_escape(s['problem'])}`,\n"
            f"            reference: `{js_escape(s['reference'])}`,\n"
            f"            text: `{js_escape(s['text'])}`,\n"
            f"            meaning: `{js_escape(s['meaning'])}`,\n"
            f"            example: `{js_escape(s['example'])}`\n"
            "        }"
        )
    return ",\n".join(entries)


def generate_html(flat):
    js_array = gen_js_array(flat)

    html = """<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>Bhagwat Geeta</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
body { margin:0; padding:12px; font-family:Arial; background:#ff9800; }
.title-block { text-align:center; width:100%; }
h1 { font-size:24px; margin:6px 0; }
h3 { font-size:21px; margin:0 0 6px 0; }
hr { border:none; border-bottom:2px solid black; margin:6px 0; }
.container { display:flex; flex-direction:column; min-height:calc(100vh - 140px); }
.content-wrap { overflow:auto; padding-bottom:12px; }
.frame {
  background:white; border:2px solid black; border-radius:12px;
  padding:12px; margin-top:12px; min-height:160px;
}
.frame.highlight {
  background:#e7f9e6; border-color:#8fd19b;
  box-shadow:0 0 12px rgba(0,128,64,0.25);
}
button {
  padding:7px 14px; border:none; border-radius:14px;
  margin:3px; font-size:14px; font-weight:bold; cursor:pointer;
}
.green { background:#2e7d32; color:white; }
.red { background:#b71c1c; color:white; }
.blue { background:#1565c0; color:white; }
.small-btn { padding:5px 10px; font-size:13px; }
pre { white-space:pre-wrap; font-size:16px; margin-top:8px; }
.controls-row { text-align:center; margin:8px 0; }
.voice-controls { display:inline-block; margin-left:14px; }
.toggle {
  margin:0 6px; padding:6px 10px; border-radius:10px;
  background:white; border:1px solid rgba(0,0,0,0.12); cursor:pointer;
}
.selected { background:#1976d2; color:white; }
.speed-selected { background:#388e3c; color:white; }
.nav {
  display:flex; justify-content:space-between; font-weight:bold;
  margin-top:12px; position:sticky; bottom:0; padding-top:10px;
}
</style>
</head>
<body>

<div class="title-block">
  <h1>Bhagwat Geeta</h1>
  <hr>
  <h3>📘 भगवद गीता में अपनी समस्याओं का समाधान खोजें</h3>
  <hr>
</div>

<div class="controls-row">
  <button class="green" onclick="startSequential()">Start</button>
  <button class="green" onclick="nextButton()">Next</button>
  <button class="red" onclick="stopReading()">Stop</button>
  <button class="green" onclick="resumeReading()">Resume</button>
  <button class="green" onclick="startRandom()">Random</button>
  <button class="red" onclick="exitApp()">Exit</button>
  <span id="voiceControls" class="voice-controls"></span>
</div>

<div class="container">
  <div class="content-wrap" id="contentWrap"><div id="content"></div></div>
  <div class="nav">
    <button onclick="prevPage()">⬅ Previous</button>
    <span id="pageInfo"></span>
    <button onclick="nextPage()">Next ➡</button>
  </div>
</div>

<script>
const PER_PAGE = __PER_PAGE__;
const SHLOKAS = [
__JS_ARRAY__
];

let page = 0;
let mode = null; // "seq" | "random" | null
let playing = false;
let seqIndex = 0;     // next index to play in sequential mode
let randomList = [];  // shuffled list of indices
let randomPos = 0;    // position in randomList
let currentIndex = -1; // index currently being read (highlighted)

// Voice & speed settings (persisted)
let selectedGender = localStorage.getItem("gita_voice_gender") || "female";
let selectedSpeed = localStorage.getItem("gita_voice_speed") || "slow";

// Browser voice fallback
let browserVoice = null;
function loadBrowserVoices(){
    const list = speechSynthesis.getVoices();
    if(!list || !list.length) return;
    if(selectedGender === "female"){
        browserVoice = list.find(v => v.lang && v.lang.toLowerCase().includes('hi') && v.name && v.name.toLowerCase().includes('female'))
            || list.find(v => v.lang && v.lang.toLowerCase().includes('hi'))
            || list[0];
    } else {
        browserVoice = list.find(v => v.lang && v.lang.toLowerCase().includes('hi') && v.name && v.name.toLowerCase().includes('male'))
            || list.find(v => v.lang && v.lang.toLowerCase().includes('hi'))
            || list[0];
    }
}
speechSynthesis.onvoiceschanged = loadBrowserVoices;
loadBrowserVoices();

// Highlight helpers
function clearHighlights(){
    document.querySelectorAll(".frame.highlight").forEach(e=>e.classList.remove("highlight"));
}
function highlightFrame(i){
    clearHighlights();
    const el = document.getElementById("shlok_"+i);
    if(el){
        el.classList.add("highlight");
        el.scrollIntoView({behavior:'smooth', block:'center'});
    }
}

// Called by Android via evaluateJavascript (MainActivity) when TTS finishes
function onSpeakComplete(){
    try {
        // continue based on current mode
        if(!playing) return;
        if(mode === "seq"){
            playNextSequential();
        } else if(mode === "random"){
            playNextRandom();
        }
    } catch(e){}
}
window.onSpeakComplete = onSpeakComplete; // expose globally

// Speak (prefer Android, fallback to browser)
function speakNowIndex(i){
    currentIndex = i;
    const s = SHLOKAS[i];
    const textToSpeak = "अनुभाग: " + s.section + "\\n" +
                        s.reference + "\\n" +
                        "संस्कृत:\\n" + s.text + "\\n" +
                        "हिंदी अर्थ:\\n" + s.meaning + "\\n" +
                        "उदाहरण:\\n" + s.example;

    // Try Android first
    try {
        if(typeof Android !== "undefined" && Android && Android.speak){
            try { Android.speak(textToSpeak, selectedGender, selectedSpeed); } catch(e){}
            return;
        }
    } catch(e){}

    // Browser fallback using SpeechSynthesis
    try {
        speechSynthesis.cancel();
        const u = new SpeechSynthesisUtterance(textToSpeak);
        if(browserVoice) u.voice = browserVoice;
        if(selectedSpeed === "very_slow") u.rate = 0.72;
        else if(selectedSpeed === "slow") u.rate = 0.82;
        else u.rate = 0.95;
        u.lang = (browserVoice && browserVoice.lang) ? browserVoice.lang : 'hi-IN';
        u.onend = function(){ try{ onSpeakComplete(); } catch(e){} };
        speechSynthesis.speak(u);
    } catch(e){
        // fallback: avoid deadlock — call onSpeakComplete after short delay
        setTimeout(()=>{ try{ onSpeakComplete(); }catch(e){} }, 1000);
    }
}

// ------------------ SEQUENTIAL MODE ------------------
function startSequential(){
    stopReading();
    mode = "seq";
    playing = true;
    seqIndex = 0;
    if(seqIndex < SHLOKAS.length){
        page = Math.floor(seqIndex / PER_PAGE);
        render();
        setTimeout(()=>{ highlightFrame(seqIndex); speakNowIndex(seqIndex); seqIndex++; }, 180);
    } else {
        playing = false;
    }
}

function playNextSequential(){
    if(!playing || mode !== "seq") return;
    if(seqIndex >= SHLOKAS.length){
        playing = false;
        clearHighlights();
        return;
    }
    let i = seqIndex;
    seqIndex++;
    page = Math.floor(i / PER_PAGE);
    render();
    setTimeout(()=>{ highlightFrame(i); speakNowIndex(i); }, 180);
}

// NEXT button behavior: start from next highlighted and continue sequentially
function nextButton(){
    stopReading();
    mode = "seq";
    playing = true;

    // find highlighted index
    let highlighted = -1;
    document.querySelectorAll('.frame').forEach(function(f){
        if(f.classList.contains('highlight')){
            highlighted = Number(f.id.replace('shlok_',''));
        }
    });

    seqIndex = (highlighted === -1) ? 0 : highlighted + 1;
    if(seqIndex < 0) seqIndex = 0;
    if(seqIndex >= SHLOKAS.length){
        playing = false;
        return;
    }

    let i = seqIndex;
    seqIndex++;
    page = Math.floor(i / PER_PAGE);
    render();
    setTimeout(()=>{ highlightFrame(i); speakNowIndex(i); }, 180);
}

// ------------------ RANDOM MODE ------------------
function startRandom(){
    stopReading();
    mode = "random";
    playing = true;

    // build shuffled list
    randomList = [];
    for(let i=0;i<SHLOKAS.length;i++) randomList.push(i);
    for(let i=randomList.length-1;i>0;i--){
        const j = Math.floor(Math.random()*(i+1));
        const tmp = randomList[i]; randomList[i] = randomList[j]; randomList[j] = tmp;
    }
    randomPos = 0;

    if(randomPos < randomList.length){
        let i = randomList[randomPos++];
        page = Math.floor(i / PER_PAGE);
        render();
        setTimeout(()=>{ highlightFrame(i); speakNowIndex(i); }, 180);
    } else {
        playing = false;
    }
}

function playNextRandom(){
    if(!playing || mode !== "random") return;
    if(randomPos >= randomList.length){
        // reshuffle and continue
        for(let i=randomList.length-1;i>0;i--){
            const j = Math.floor(Math.random()*(i+1));
            const tmp = randomList[i]; randomList[i] = randomList[j]; randomList[j] = tmp;
        }
        randomPos = 0;
    }
    if(randomPos < randomList.length){
        let i = randomList[randomPos++];
        page = Math.floor(i / PER_PAGE);
        render();
        setTimeout(()=>{ highlightFrame(i); speakNowIndex(i); }, 180);
    } else {
        playing = false;
    }
}

// Read a single shlok (user clicks this shlok's play button) — doesn't change mode; plays that one only
function readSingle(i){
    stopReading();
    mode = null;
    playing = true;
    currentIndex = i;
    page = Math.floor(i / PER_PAGE);
    render();
    setTimeout(()=>{ highlightFrame(i); speakNowIndex(i); }, 180);
}

// STOP / RESUME / EXIT
function stopReading(){
    playing = false;
    try { if(typeof Android !== "undefined" && Android && Android.stopSpeak) Android.stopSpeak(); } catch(e){}
    try { speechSynthesis.cancel(); } catch(e){}
    clearHighlights();
}

function resumeReading(){
    if(playing) return; // already playing
    // resume depending on mode
    if(mode === "seq"){
        if(seqIndex < SHLOKAS.length){
            playing = true;
            let i = seqIndex;
            seqIndex++;
            page = Math.floor(i / PER_PAGE);
            render();
            setTimeout(()=>{ highlightFrame(i); speakNowIndex(i); }, 180);
        }
    } else if(mode === "random"){
        if(randomPos < randomList.length){
            playing = true;
            let i = randomList[randomPos++];
            page = Math.floor(i / PER_PAGE);
            render();
            setTimeout(()=>{ highlightFrame(i); speakNowIndex(i); }, 180);
        }
    }
}

function exitApp(){
    try { if(typeof Android !== "undefined" && Android && Android.exitApp) Android.exitApp(); } catch(e){}
    try { window.close(); } catch(e){}
}

// ------------------ RENDER / PAGINATION ------------------
function render(){
    const start = page * PER_PAGE;
    const end = Math.min(start + PER_PAGE, SHLOKAS.length);
    let html = "";
    for(let i=start;i<end;i++){
        let s = SHLOKAS[i];
        html += `
        <div class="frame" id="shlok_${i}">
            <div style="font-weight:bold; margin-bottom:6px;">
                ${i+1})
                <button class="blue small-btn" onclick="readSingle(${i})">▶ Start This Shlok</button>
                <button class="red small-btn" onclick="stopReading()">■ Stop</button>
            </div>

            <h4>📗 अनुभाग: ${s.section}</h4>
            <b>समस्या:</b> ${s.problem}<br><br>

            <b>${s.reference}</b><br><br>

            <b>संस्कृत:</b><br>
            <pre>${s.text}</pre>

            <b>हिंदी अर्थ:</b><br>
            ${s.meaning}<br><br>

            <b>उदाहरण:</b><br>
            ${s.example}
        </div>`;
    }
    document.getElementById("content").innerHTML = html;
    document.getElementById("pageInfo").innerText = "Page "+(page+1)+" / "+Math.ceil(SHLOKAS.length/PER_PAGE);
}

function nextPage(){
    page = (page + 1) % Math.ceil(SHLOKAS.length/PER_PAGE);
    render();
}
function prevPage(){
    page = (page - 1 + Math.ceil(SHLOKAS.length/PER_PAGE)) % Math.ceil(SHLOKAS.length/PER_PAGE);
    render();
}

// ------------------ VOICE & SPEED UI ------------------
function renderVoiceControls(){
    const c = document.getElementById("voiceControls");
    c.innerHTML = "";

    const g1 = document.createElement("button");
    g1.textContent = "♀ Female";
    g1.className = "toggle" + (selectedGender==="female" ? " selected" : "");
    g1.onclick = function(){
        selectedGender = "female";
        localStorage.setItem("gita_voice_gender","female");
        try { if(typeof Android !== "undefined" && Android && Android.setVoice) Android.setVoice("female"); } catch(e){}
        loadBrowserVoices();
        renderVoiceControls();
    };
    c.appendChild(g1);

    const g2 = document.createElement("button");
    g2.textContent = "Male";
    g2.className = "toggle" + (selectedGender==="male" ? " selected" : "");
    g2.onclick = function(){
        selectedGender = "male";
        localStorage.setItem("gita_voice_gender","male");
        try { if(typeof Android !== "undefined" && Android && Android.setVoice) Android.setVoice("male"); } catch(e){}
        loadBrowserVoices();
        renderVoiceControls();
    };
    c.appendChild(g2);

    const speeds = [
        {key:'very_slow', label:'Very Slow'},
        {key:'slow', label:'Slow'},
        {key:'medium', label:'Medium'}
    ];
    speeds.forEach(function(s){
        const b = document.createElement("button");
        b.textContent = s.label;
        b.className = "toggle" + (selectedSpeed===s.key ? " speed-selected" : "");
        b.onclick = function(){
            selectedSpeed = s.key;
            localStorage.setItem("gita_voice_speed", s.key);
            try { if(typeof Android !== "undefined" && Android && Android.setSpeed) Android.setSpeed(s.key); } catch(e){}
            renderVoiceControls();
        };
        c.appendChild(b);
    });
}

// initial
renderVoiceControls();
render();

</script>
</body>
</html>
"""
    html = html.replace("__PER_PAGE__", str(SHLOKAS_PER_PAGE))
    html = html.replace("__JS_ARRAY__", js_array)
    return html


def main():
    flat = flatten_sections(ALL_SHLOKAS)
    html = generate_html(flat)

    os.makedirs(os.path.dirname(OUTPUT_HTML), exist_ok=True)
    with open(OUTPUT_HTML, "w", encoding="utf-8") as f:
        f.write(html)

    print("✔ HTML Generated:", OUTPUT_HTML)
    try:
        webbrowser.open("file://" + OUTPUT_HTML)
    except:
        pass


if __name__ == "__main__":
    main()
