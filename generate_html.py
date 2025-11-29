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

        section_title = sec.get("title", "")

        for s in sec.get("shlokas", []):
            flat.append({
                "section": section_title,
                "problem": s.get("problem", ""),
                "reference": s.get("reference", ""),
                "text": s.get("text", ""),
                "meaning": s.get("meaning", ""),
                "example": s.get("example", "")
            })

    print("✔ Total Shlokas Flattened:", len(flat))
    return flat


def js_escape(text):
    if not text:
        return ""
    return (
        text.replace("\\", "\\\\")
            .replace("`", "\\`")
            .replace("</", "<\\/")
    )


def generate_html(flat_data):

    js_entries = []
    for i, s in enumerate(flat_data, start=1):
        js_entries.append(
f"""        {{
            id: {i},
            section: `{js_escape(s['section'])}`,
            problem: `{js_escape(s['problem'])}`,
            reference: `{js_escape(s['reference'])}`,
            text: `{js_escape(s['text'])}`,
            meaning: `{js_escape(s['meaning'])}`,
            example: `{js_escape(s['example'])}`
        }}"""
        )

    js_array = ",\n".join(js_entries)

    html = f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>AI Bhagwat Geeta by Anurag Vasu Bharti</title>
<meta name="viewport" content="width=device-width, initial-scale=1">

<style>

body {{
    background: #ff9800;
    font-family: Arial, sans-serif;
    margin: 0;
    padding: 12px;
}}

h1 {{
    text-align:center;
    font-size:24px;
}}

h3 {{
    text-align:center;
    font-size:18px;
}}

hr {{
    border: none;
    border-bottom: 2px solid black;
    margin: 6px 0;
}}

.frame {{
    background: white;
    border: 2px solid black;
    border-radius: 12px;
    padding: 12px;
    margin-top: 12px;
    line-height: 1.45;
}}

button {{
    padding: 7px 14px;
    border: none;
    border-radius: 14px;
    margin: 3px;
    font-size: 14px;
    font-weight: bold;
}}

.green {{ background:#2e7d32; color:white; }}
.red   {{ background:#b71c1c; color:white; }}
.blue  {{ background:#1565c0; color:white; }}

.small-btn {{
    padding:5px 10px;
    font-size:13px;
}}

pre {{
    white-space: pre-wrap;
    font-size: 16px;
    margin-top: 8px;
}}

.nav {{
    display:flex;
    justify-content: space-between;
    font-weight:bold;
    margin-top:14px;
}}

</style>
</head>

<body>

<h1>AI Bhagwat Geeta by Anurag Vasu Bharti</h1>
<hr>
<h3>📘 भगवद गीता में अपनी समस्याओं का समाधान खोजें</h3>
<hr>

<div style="text-align:center;">
    <button class="green" onclick="startReadingAll()">Start</button>
    <button class="red"   onclick="stopReading()">Stop</button>
    <button class="green" onclick="resumeReading()">Resume</button>
    <button class="green" onclick="readRandom()">Random</button>
    <button class="red"   onclick="Android.exitApp()">Exit</button>
</div>

<hr>

<div id="content"></div>

<div class="nav">
    <button onclick="prevPage()">⬅ Previous</button>
    <span id="pageInfo"></span>
    <button onclick="nextPage()">Next ➡</button>
</div>

<script>

const PER_PAGE = {SHLOKAS_PER_PAGE};
let page = 0;
let reading = false;
let autoIndex = 0;
let readTimer = null;

const SHLOKAS = [
{js_array}
];

function speak(text) {{
    if (typeof Android !== "undefined" && Android.speak) {{
        Android.speak(text);
        return;
    }}
    const msg = new SpeechSynthesisUtterance(text);
    speechSynthesis.cancel();
    speechSynthesis.speak(msg);
}}

function stopSpeaking() {{
    if (typeof Android !== "undefined" && Android.stopSpeak) {{
        Android.stopSpeak();
        return;
    }}
    speechSynthesis.cancel();
}}

function readSingle(i) {{
    stopReading();
    const s = SHLOKAS[i];
    speak(s.text + "\\nअर्थ: " + s.meaning + "\\nउदाहरण: " + s.example);
}}

function stopSingle() {{
    stopSpeaking();
}}

function render() {{
    const start = page * PER_PAGE;
    const end = Math.min(start + PER_PAGE, SHLOKAS.length);

    let html = "";

    for (let i = start; i < end; i++) {{
        const s = SHLOKAS[i];

        html += `
        <div class="frame">

            <button class="blue small-btn" onclick="readSingle(${{i}})">▶ Start This Shlok</button>
            <button class="red small-btn" onclick="stopSingle()">■ Stop</button>

            <h4>📗 अनुभाग: ${{s.section}}</h4>
            <b>समस्या:</b> ${{s.problem}}<br>
            <b>${{s.reference}}</b><br><br>

            <pre>${{s.text}}</pre>

            <b>अर्थ:</b> ${{s.meaning}}<br><br>
            <b>उदाहरण:</b> ${{s.example}}
        </div>`;
    }}

    document.getElementById("content").innerHTML = html;

    document.getElementById("pageInfo").innerText =
        "Page " + (page + 1) + " / " + Math.ceil(SHLOKAS.length / PER_PAGE);
}}

function nextPage() {{
    page = (page + 1) % Math.ceil(SHLOKAS.length / PER_PAGE);
    render();
}}

function prevPage() {{
    page = (page - 1 + Math.ceil(SHLOKAS.length / PER_PAGE)) %
           Math.ceil(SHLOKAS.length / PER_PAGE);
    render();
}}

function startReadingAll() {{
    stopReading();
    reading = true;
    autoIndex = 0;
    readNext();
}}

function readNext() {{
    if (!reading) return;

    if (autoIndex >= SHLOKAS.length) {{
        reading = false;
        return;
    }}

    const s = SHLOKAS[autoIndex];
    speak(s.text + "\\nअर्थ: " + s.meaning + "\\nउदाहरण: " + s.example);

    readTimer = setTimeout(() => {{
        autoIndex++;
        readNext();
    }}, 12000);
}}

function stopReading() {{
    reading = false;
    clearTimeout(readTimer);
    stopSpeaking();
}}

function resumeReading() {{
    if (!reading) {{
        reading = true;
        readNext();
    }}
}}

function readRandom() {{
    stopReading();
    const i = Math.floor(Math.random() * SHLOKAS.length);
    readSingle(i);
}}

render();

</script>

</body>
</html>
"""
    return html


def main():
    print("🔢 Current Sections Loaded:", len(ALL_SHLOKAS))
    flat = flatten_sections(ALL_SHLOKAS)

    print("🔹 Generating HTML...")
    html = generate_html(flat)

    os.makedirs(os.path.dirname(OUTPUT_HTML), exist_ok=True)

    with open(OUTPUT_HTML, "w", encoding="utf-8") as f:
        f.write(html)

    print("✔ HTML Generated Successfully:")
    print(OUTPUT_HTML)

    webbrowser.open("file://" + OUTPUT_HTML)


if __name__ == "__main__":
    main()
