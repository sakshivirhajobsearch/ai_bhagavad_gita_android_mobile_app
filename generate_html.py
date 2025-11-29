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
        if isinstance(sec, list):
            sec = sec[0]
        title = sec.get("title", "")
        for s in sec.get("shlokas", []):
            flat.append({
                "section": title,
                "problem": s.get("problem", ""),
                "reference": s.get("reference", ""),
                "text": s.get("text", ""),
                "meaning": s.get("meaning", ""),
                "example": s.get("example", "")
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


def clean_text_for_example(t):
    if not t or not str(t).strip():
        return "—"
    return " ".join([line.strip() for line in str(t).splitlines() if line.strip()])


def generate_html(flat):
    js_entries = []

    for i, s in enumerate(flat, start=0):
        meaning = clean_text_for_example(s["meaning"])
        example = clean_text_for_example(s["example"])

        js_entries.append(
f"""        {{
            id: {i},
            section: `{js_escape(s['section'])}`,
            problem: `{js_escape(s['problem'])}`,
            reference: `{js_escape(s['reference'])}`,
            text: `{js_escape(s['text'])}`,
            meaning: `{js_escape(meaning)}`,
            example: `{js_escape(example)}`
        }}"""
        )

    js_array = ",\n".join(js_entries)

    html = """
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>AI Bhagwat Geeta by Anurag Vasu Bharti</title>
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
  <h1>AI Bhagwat Geeta by Anurag Vasu Bharti</h1>
  <hr>
  <h3>📘 भगवद गीता में अपनी समस्याओं का समाधान खोजें</h3>
  <hr>
</div>

<div class="controls-row">
  <button class="green" onclick="startReadingAll()">Start</button>
  <button class="red" onclick="stopReading()">Stop</button>
  <button class="green" onclick="resumeReading()">Resume</button>
  <button class="green" onclick="readRandom()">Random</button>
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

// ===============================
// GLOBAL DECLARATIONS FOR WEBVIEW
// ===============================
window.startReadingAll =
window.stopReading =
window.resumeReading =
window.readRandom =
window.readSingle =
window.stopSingle =
window.exitApp =
window.nextPage =
window.prevPage =
window.render =
window.readNext =
window.highlightFrame =
window.clearHighlights =
null;

// ===============================
const PER_PAGE = """ + str(SHLOKAS_PER_PAGE) + """;
let page=0, reading=false, autoIndex=0, readTimer=null;

let selectedGender = localStorage.getItem('gita_voice_gender') || 'female';
let selectedSpeed  = localStorage.getItem('gita_voice_speed')  || 'slow';

const SHLOKAS = [
""" + js_array + """
];

let browserVoice=null;

function loadVoices() {
    const list = speechSynthesis.getVoices();
    if (!list.length) return;

    if (selectedGender === 'female') {
        browserVoice = list.find(v => v.lang.includes('hi') && v.name.toLowerCase().includes('female'))
                       || list.find(v => v.lang.includes('hi'))
                       || list[0];
    } else {
        browserVoice = list.find(v => v.lang.includes('hi') && v.name.toLowerCase().includes('male'))
                       || list.find(v => v.lang.includes('hi'))
                       || list[0];
    }
}
speechSynthesis.onvoiceschanged = loadVoices;

function speedRate() {
    if (selectedSpeed === 'very_slow') return 0.72;
    if (selectedSpeed === 'slow') return 0.82;
    return 0.95;
}

function speak(text) {
    try { if (Android?.speak) { Android.speak(text,selectedGender,selectedSpeed); return; } }
    catch(e) {}

    let u = new SpeechSynthesisUtterance(text);
    u.voice = browserVoice;
    u.rate  = speedRate();
    u.pitch = selectedGender==='female' ? 1.05 : 0.95;
    u.lang  = browserVoice?.lang || 'hi-IN';
    speechSynthesis.cancel(); speechSynthesis.speak(u);
}

function stopTTS() {
    try { Android.stopSpeak(); return; } catch(e){}
    speechSynthesis.cancel();
}

window.clearHighlights = function() {
    document.querySelectorAll(".frame.highlight").forEach(e=>e.classList.remove("highlight"));
};

window.highlightFrame = function(i){
    clearHighlights();
    const el=document.getElementById("shlok_"+i);
    if(el){ el.classList.add("highlight"); el.scrollIntoView({behavior:'smooth',block:'center'}); }
};

window.startReadingAll = function(){
    stopReading();
    reading=true; autoIndex=0;
    readNext();
};

window.readNext = function(){
    if(!reading) return;

    if(autoIndex>=SHLOKAS.length){
        reading=false; clearHighlights(); return;
    }

    highlightFrame(autoIndex);

    const s=SHLOKAS[autoIndex];
    speak(s.text + "\\n\\nअर्थ:\\n" + s.meaning + "\\n\\nउदाहरण:\\n" + s.example);

    readTimer=setTimeout(()=>{ autoIndex++; readNext(); },14000);
};

window.stopReading = function(){
    reading=false;
    clearTimeout(readTimer);
    stopTTS();
    clearHighlights();
};

window.resumeReading = function(){
    if(!reading){ reading=true; readNext(); }
};

window.readRandom = function(){
    stopReading();
    const i=Math.floor(Math.random()*SHLOKAS.length);
    readSingle(i);
};

window.readSingle = function(i){
    stopReading();
    highlightFrame(i);
    const s=SHLOKAS[i];
    speak(s.text + "\\n\\nअर्थ:\\n" + s.meaning + "\\n\\nउदाहरण:\\n" + s.example);
};

window.stopSingle = function(){ stopReading(); };

window.exitApp = function(){
    try { Android.exitApp(); return; } catch(e){}
    window.close();
};

window.render = function(){
    const start=page*PER_PAGE;
    const end=Math.min(start+PER_PAGE,SHLOKAS.length);
    let html="";

    for(let i=start;i<end;i++){
        let s=SHLOKAS[i];
        html+=`
        <div class="frame" id="shlok_${i}">
            <button class="blue small-btn" onclick="readSingle(${i})">▶ Start This Shlok</button>
            <button class="red small-btn" onclick="stopSingle()">■ Stop</button>

            <h4>📗 अनुभाग: ${s.section}</h4>
            <b>समस्या:</b> ${s.problem}<br>
            <b>${s.reference}</b><br>
            <pre>${s.text}</pre>
            <b>अर्थ:</b> ${s.meaning}<br><br>
            <b>उदाहरण:</b> ${s.example}
        </div>`;
    }

    document.getElementById("content").innerHTML=html;
    document.getElementById("pageInfo").innerText =
      "Page "+(page+1)+" / "+Math.ceil(SHLOKAS.length/PER_PAGE);
};

window.nextPage = function(){
    page=(page+1)%Math.ceil(SHLOKAS.length/PER_PAGE);
    render();
};

window.prevPage = function(){
    page=(page-1+Math.ceil(SHLOKAS.length/PER_PAGE))%
         Math.ceil(SHLOKAS.length/PER_PAGE);
    render();
};

// ===============================
// VOICE CONTROL BUTTONS FIX
// ===============================
function renderVoiceControls(){
    const c=document.getElementById("voiceControls");
    c.innerHTML="";

    const g1=document.createElement("button");
    g1.textContent="♀ Female";
    g1.className="toggle"+(selectedGender==="female"?" selected":"");
    g1.onclick=()=>{ selectedGender="female"; localStorage.setItem("gita_voice_gender","female"); loadVoices(); renderVoiceControls(); };
    c.appendChild(g1);

    const g2=document.createElement("button");
    g2.textContent="♂ Male";
    g2.className="toggle"+(selectedGender==="male"?" selected":"");
    g2.onclick=()=>{ selectedGender="male"; localStorage.setItem("gita_voice_gender","male"); loadVoices(); renderVoiceControls(); };
    c.appendChild(g2);

    const speeds=[
        {key:'very_slow',label:'Very Slow'},
        {key:'slow',label:'Slow'},
        {key:'medium',label:'Medium'}
    ];

    speeds.forEach(s=>{
        const b=document.createElement("button");
        b.textContent=s.label;
        b.className="toggle"+(selectedSpeed===s.key?" speed-selected":"");
        b.onclick=()=>{ selectedSpeed=s.key; localStorage.setItem("gita_voice_speed",s.key); renderVoiceControls(); };
        c.appendChild(b);
    });
}

loadVoices();
renderVoiceControls();
render();
</script>

</body>
</html>
"""

    return html


def main():
    flat = flatten_sections(ALL_SHLOKAS)
    html = generate_html(flat)
    os.makedirs(os.path.dirname(OUTPUT_HTML), exist_ok=True)
    with open(OUTPUT_HTML, "w", encoding="utf-8") as f:
        f.write(html)
    print("✔ HTML Generated:", OUTPUT_HTML)
    try: webbrowser.open("file://" + OUTPUT_HTML)
    except: pass


if __name__ == "__main__":
    main()
