"""
AWS DEA-C01 HTML 產生器 v4
- 讀取 PDF 解析的 questions.json（英文原文 + 中文翻譯）
- 讀取 Notion overflow 檔案（中文筆記解析）
- 產生含中英切換的 HTML：全英文版 + 中英對照版
"""
import json
import re
import os
import sys

TARGET_DIR = r"D:\Project\00.Doc\AWS_DEA_C01"
QUESTIONS_JSON = os.path.join(TARGET_DIR, "questions.json")

# Notion overflow files (same as gen3.ps1)
NOTION_FILES = [
    ("Q001-050", "Q1-Q50", r"C:\Users\user\AppData\Local\Temp\devin.exe-overflows\8af22963\content.txt"),
    ("Q051-100", "Q51-Q100", r"C:\Users\user\AppData\Local\Temp\devin.exe-overflows\79cb750e\content.txt"),
    ("Q101-150", "Q101-Q150", r"C:\Users\user\AppData\Local\Temp\devin.exe-overflows\37005ac9\content.txt"),
    ("Q151-200", "Q151-Q200", r"C:\Users\user\AppData\Local\Temp\devin.exe-overflows\4bbc4dea\content.txt"),
    ("Q201-250", "Q201-Q250", r"C:\Users\user\AppData\Local\Temp\devin.exe-overflows\54a96ea2\content.txt"),
    ("Q251-300", "Q251-Q300", r"C:\Users\user\AppData\Local\Temp\devin.exe-overflows\c013e474\content.txt"),
    ("Q301-342", "Q301-Q342", r"C:\Users\user\AppData\Local\Temp\devin.exe-overflows\d31f6316\content.txt"),
]

# Unicode chars for Notion parsing
U_LAYER = ''.join(chr(c) for c in [0x5206, 0x5C64])  # 分層
U_ANS = ''.join(chr(c) for c in [0x7B54, 0x6848, 0xFF08, 0x5B98, 0x65B9, 0xFF09])  # 答案（官方）
U_COLON = chr(0xFF1A)  # ：
U_PIPE = chr(0xFF5C)  # ｜
U_KEYPOINT = ''.join(chr(c) for c in [0x4E00, 0x53E5, 0x8003, 0x9EDE])  # 一句考點
U_WHY = ''.join(chr(c) for c in [0x70BA, 0x4EC0, 0x9EBC])  # 為什麼
U_FLOW = ''.join(chr(c) for c in [0x8D85, 0x77ED, 0x6D41, 0x7A0B, 0x5716])  # 超短流程圖
U_NOTE = ''.join(chr(c) for c in [0x4E00, 0x884C, 0x7B46, 0x8A18])  # 一行筆記


def load_pdf_questions():
    with open(QUESTIONS_JSON, "r", encoding="utf-8") as f:
        return json.load(f)


def get_notion_content(path):
    """Read Notion overflow file and extract content section."""
    with open(path, "rb") as f:
        raw = f.read()
    jstr = raw.decode("utf-8")
    obj = json.loads(jstr)
    text = obj["text"]
    si = text.index("<content>") + 9
    ei = text.index("</content>", si)
    return text[si:ei]


def parse_notion_questions(content):
    """Parse Notion content to extract question notes."""
    questions = {}
    # Find all ## QN｜title markers
    pattern = r'## Q(\d+)' + re.escape(U_PIPE) + r'\s*([^\n]+)'
    matches = list(re.finditer(pattern, content))

    for i, m in enumerate(matches):
        qnum = int(m.group(1))
        title = m.group(2).strip()
        start = m.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(content)
        block = content[start:end].strip()
        block = re.sub(r'\n---\n?$', '', block)

        # Extract fields
        layer = ""
        ans = ""
        keywords = ""

        lm = re.search(r'\*\*' + re.escape(U_LAYER) + r'\*\*' + re.escape(U_COLON) + r'([^\n]+)', block)
        if lm:
            layer = lm.group(1).strip()

        am = re.search(r'\*\*' + re.escape(U_ANS) + r'\*\*' + re.escape(U_COLON) + r'([^\n]+)', block)
        if am:
            ans = am.group(1).strip()

        km = re.search(r'### Keywords\n(.+?)(?=\n###|\n---|$)', block, re.DOTALL)
        if km:
            keywords = km.group(1).strip()

        # Extract sections
        def extract_section(name):
            pat = r'### ' + re.escape(name) + r'\n(.+?)(?=\n### |\n---|$)'
            mm = re.search(pat, block, re.DOTALL)
            return mm.group(1).strip() if mm else ""

        keypoint = extract_section(U_KEYPOINT)
        why = extract_section(U_WHY)
        flow = extract_section(U_FLOW)
        note = extract_section(U_NOTE)

        # Parse other options (錯誤選項的原因)
        other_reasons = {}
        opt_matches = re.finditer(r'^-?\s*([A-D])\)\s*(.+)', block, re.MULTILINE)
        for om in opt_matches:
            letter = om.group(1)
            otext = om.group(2).strip()
            # Skip answer line
            if U_ANS in otext:
                continue
            # Split text and reason
            opt_text = otext
            opt_reason = ""
            if U_COLON in otext:
                parts = otext.split(U_COLON, 1)
                opt_text = parts[0].strip()
                opt_reason = parts[1].strip()
            elif ":" in otext:
                parts = otext.split(":", 1)
                opt_text = parts[0].strip()
                opt_reason = parts[1].strip()
            other_reasons[letter] = opt_reason

        questions[qnum] = {
            "title": title,
            "layer": layer,
            "answer": ans,
            "keywords": keywords,
            "keypoint": keypoint,
            "why": why,
            "flow": flow,
            "note": note,
            "other_reasons": other_reasons,
        }

    return questions


def esc_html(s):
    """Escape HTML special characters."""
    s = s.replace("&", "&amp;")
    s = s.replace("<", "&lt;")
    s = s.replace(">", "&gt;")
    return s


def highlight_keywords(text, keywords):
    """在 raw text 中用 \x00...\x01 placeholder 標記關鍵字，之後再轉成 <mark>。"""
    if not text or not keywords:
        return text
    kws = sorted(
        [k.strip().lstrip("- ") for k in keywords.split("\n") if k.strip() and len(k.strip()) >= 3],
        key=len, reverse=True
    )
    if not kws:
        return text
    for kw in kws:
        kw_esc = re.escape(kw)
        # 把 text 按 \x00...\x01 分段，只對未標記段做替換
        parts = re.split(r'(\x00.*?\x01)', text, flags=re.DOTALL)
        for i, part in enumerate(parts):
            if part.startswith('\x00'):
                continue
            parts[i] = re.sub(r'(' + kw_esc + r')', lambda m: '\x00' + m.group(0) + '\x01', part, flags=re.IGNORECASE)
        text = ''.join(parts)
    return text


def md_inline(s, keywords=None):
    """Convert inline markdown to HTML, optionally highlighting keywords."""
    if keywords:
        s = highlight_keywords(s, keywords)
    s = esc_html(s)
    s = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', s)
    s = re.sub(r'`([^`]+)`', r'<code>\1</code>', s)
    if keywords:
        s = s.replace('\x00', '<mark class="kw-hl">').replace('\x01', '</mark>')
    return s


def why_to_html(why_text):
    """Convert why section (bullet list) to HTML."""
    if not why_text:
        return ""
    lines = why_text.split("\n")
    items = []
    for ln in lines:
        t = ln.strip()
        if t.startswith("- "):
            items.append(f"<li>{md_inline(t[2:])}</li>")
        elif t:
            items.append(f"<p>{md_inline(t)}</p>")
    if items:
        return "<ul>" + "".join(items) + "</ul>"
    return ""


CSS = """
:root{--bg:#1a1a2e;--card:#16213e;--text:#e0e0e0;--accent:#0f3460;--hl:#e94560;--green:#4ecca3;--orange:#f0a500;--border:#233;--qbg:#0d1b2a;--opt:#1a1a2e;--opt-c:#1a3a2a;--opt-w:#3a1a1a;--zh-bg:#111}
@media(prefers-color-scheme:light){:root{--bg:#f5f5f5;--card:#fff;--text:#333;--accent:#e8f0fe;--hl:#d32f2f;--green:#2e7d32;--orange:#f57c00;--border:#ddd;--qbg:#f0f4ff;--opt:#f9f9f9;--opt-c:#e8f5e9;--opt-w:#fce4ec;--zh-bg:#f8f8ff}}
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","Noto Sans TC",sans-serif;background:var(--bg);color:var(--text);line-height:1.6;font-size:16px;-webkit-text-size-adjust:100%}
.topbar{position:sticky;top:0;z-index:100;background:var(--card);border-bottom:1px solid var(--border);padding:6px 10px;transition:transform .25s ease;will-change:transform}
.topbar.hide{transform:translateY(-100%)}
.tbr{display:flex;align-items:center;gap:6px}
.topbar h1{font-size:15px;color:var(--hl);margin:0;flex:1;min-width:0;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.rsel{padding:5px 6px;border:1px solid var(--border);border-radius:6px;background:var(--accent);color:var(--text);font-size:13px;max-width:120px}
.ib{flex-shrink:0;padding:5px 9px;border:1px solid var(--border);border-radius:6px;background:var(--accent);color:var(--text);cursor:pointer;font-size:14px;line-height:1.2}
.ib:hover,.ib.active{background:var(--hl);color:#fff}
.search{display:none;width:100%;padding:8px 12px;border:1px solid var(--border);border-radius:8px;background:var(--bg);color:var(--text);font-size:15px;margin-top:6px}
.search.on{display:block}
.controls{display:flex;flex-wrap:wrap;gap:6px;margin-top:6px;align-items:center}
.btn{padding:5px 11px;border:1px solid var(--border);border-radius:6px;background:var(--accent);color:var(--text);cursor:pointer;font-size:13px;line-height:1.3}
.btn:hover,.btn.active{background:var(--hl);color:#fff}
.nav{display:flex;flex-wrap:wrap;gap:6px;margin-top:6px}
.nav a{padding:4px 10px;border-radius:6px;background:var(--accent);color:var(--text);text-decoration:none;font-size:13px;white-space:nowrap}
.nav a:hover,.nav a.active{background:var(--hl);color:#fff}
.container{max-width:800px;margin:0 auto;padding:12px 16px 60px}
.card{background:var(--card);border:1px solid var(--border);border-radius:12px;margin-bottom:14px;overflow:hidden}
.ch{padding:14px 16px;cursor:pointer;display:flex;align-items:flex-start;gap:10px}
.ch:hover{background:var(--accent)}
.qn{flex-shrink:0;background:var(--hl);color:#fff;border-radius:6px;padding:2px 8px;font-size:13px;font-weight:bold;min-width:52px;text-align:center}
.qt{flex:1;font-size:15px;font-weight:600;line-height:1.4}
.toggle{flex-shrink:0;font-size:14px;color:var(--text);transition:transform .2s}
.card.open .toggle{transform:rotate(90deg)}
.cb{display:none;padding:0 16px 16px;border-top:1px solid var(--border)}
.card.open .cb{display:block}
.q-scenario{background:var(--qbg);border-radius:8px;padding:14px;margin:12px 0;font-size:15px;line-height:1.6}
.q-scenario.zh{background:var(--zh-bg);border-left:3px solid var(--orange)}
.q-scenario strong{color:var(--hl)}
.opts{margin:12px 0}
.opt{display:flex;align-items:flex-start;gap:10px;padding:10px 12px;margin-bottom:6px;border:1px solid var(--border);border-radius:8px;background:var(--opt);font-size:14px;line-height:1.5}
.opt.correct{background:var(--opt-c);border-color:var(--green)}
.opt.wrong{background:var(--opt-w);border-color:var(--hl);opacity:.85}
.opt-label{flex-shrink:0;font-weight:bold;font-size:15px;min-width:24px;text-align:center}
.opt.correct .opt-label{color:var(--green)}
.opt.wrong .opt-label{color:var(--hl)}
.opt-text{flex:1}
.opt-reason{font-size:12px;color:var(--text);opacity:.7;margin-top:4px;font-style:italic}
.opt-zh{font-size:14px;color:var(--text)}
body.mode-both .opt-zh{font-size:13px;opacity:.7;margin-top:4px;padding-top:4px;border-top:1px dashed var(--border)}
.ans-banner{background:var(--green);color:#fff;padding:8px 14px;border-radius:8px;margin:12px 0;font-weight:bold;font-size:15px;text-align:center}
.meta{display:flex;flex-wrap:wrap;gap:8px;margin:12px 0}
.tag{padding:3px 10px;border-radius:12px;font-size:12px;font-weight:500}
.tag.l{background:var(--accent);color:var(--text)}
.section{margin:14px 0;padding:10px 14px;border-left:3px solid var(--accent);border-radius:0 6px 6px 0;background:var(--qbg)}
.section h4{color:var(--orange);font-size:14px;margin:0 0 6px;font-weight:700}
.section p{margin:4px 0;font-size:14px}
.section ul{margin:4px 0 4px 20px}
.section li{font-size:14px;margin:3px 0}
.section code{background:var(--accent);padding:2px 6px;border-radius:4px;font-size:13px;word-break:break-all}
.section strong{color:var(--hl)}
.divider{border:0;border-top:1px dashed var(--border);margin:14px 0}
.kw-hl{background:#fff59d;color:#000;font-weight:600;border-radius:3px;padding:0 2px}
body.kw-off .kw-hl{background:inherit;color:inherit;font-weight:inherit;padding:0}
.lang-en,.lang-zh{display:none}
body.mode-en .lang-en{display:block}
body.mode-zh .lang-zh{display:block}
body.mode-both .lang-en,body.mode-both .lang-zh{display:block}
.footer{text-align:center;padding:20px;color:var(--text);opacity:.5;font-size:13px}
.nores{display:none;text-align:center;padding:40px;color:var(--text);opacity:.5}
"""

JS = """
function tog(h){h.parentElement.classList.toggle("open")}
function filt(q){q=q.toLowerCase().trim();var c=document.querySelectorAll(".card");var f=false;c.forEach(function(x){var n=x.getAttribute("data-qnum");var t=x.getAttribute("data-title").toLowerCase();var l=x.getAttribute("data-layer").toLowerCase();var k=x.getAttribute("data-kw").toLowerCase();var b=x.textContent.toLowerCase();if(!q||n.indexOf(q)>=0||t.indexOf(q)>=0||l.indexOf(q)>=0||k.indexOf(q)>=0||b.indexOf(q)>=0){x.style.display="";f=true}else{x.style.display="none"}});document.querySelector(".nores").style.display=f?"none":"block"}
function expandAll(o){document.querySelectorAll(".card").forEach(function(c){if(c.style.display!=="none"){if(o)c.classList.add("open");else c.classList.remove("open")}})}
function setLang(lang){if(["en","zh","both"].indexOf(lang)<0)lang="both";document.body.className="mode-"+lang;document.querySelectorAll(".btn-lang").forEach(function(b){b.classList.toggle("active",b.getAttribute("data-lang")===lang)});try{localStorage.setItem("dea-lang",lang)}catch(e){}}
function toggleSearch(){var s=document.querySelector(".search");if(!s)return;var on=s.classList.toggle("on");var b=document.querySelector(".ib-search");if(b)b.classList.toggle("active",on);if(on){s.focus()}else{s.value="";filt("")}}
function setHighlight(on){document.body.classList.toggle("kw-off",!on);document.querySelectorAll(".btn-hl").forEach(function(b){b.classList.toggle("active",on)});try{localStorage.setItem("dea-hl",on?"on":"off")}catch(e){}}
(function(){var saved="both";try{saved=localStorage.getItem("dea-lang")||"both"}catch(e){}setLang(saved);var hl="on";try{hl=localStorage.getItem("dea-hl")||"on"}catch(e){}setHighlight(hl==="on")})();
(function(){var tb=document.getElementById("tb");if(!tb)return;var last=0;addEventListener("scroll",function(){var y=window.pageYOffset||document.documentElement.scrollTop;if(y>140&&y>last+4){tb.classList.add("hide")}else if(y<last-4||y<=140){tb.classList.remove("hide")}last=y},{passive:true})})();
"""


def build_option_html(letter, opt_data, zh_opt_data, notion_reason, correct_answer, keywords=None):
    """Build HTML for a single option."""
    is_correct = (letter == correct_answer)
    cls = "correct" if is_correct else "wrong"

    en_text = md_inline(opt_data.get("text", ""), keywords)
    en_html = f'<div class="lang-en">{en_text}</div>' if en_text else ""

    zh_text = md_inline(zh_opt_data["text"], keywords) if (zh_opt_data and zh_opt_data.get("text")) else ""
    zh_html = f'<div class="opt-zh lang-zh">{zh_text}</div>' if zh_text else ""

    reason_html = ""
    if notion_reason:
        reason_html = f'<div class="opt-reason lang-zh">{md_inline(notion_reason)}</div>'

    return f'<div class="opt {cls}"><span class="opt-label">{letter})</span><div class="opt-text">{en_html}{zh_html}{reason_html}</div></div>'


def build_card(q, notion_q, range_name):
    """Build HTML card for one question."""
    qnum = q["number"]
    correct = q.get("correct_answer", "")
    en_opts = q.get("en_options", {})
    zh_opts = q.get("zh_options", {})
    en_question = q.get("en_question", "")
    zh_question = q.get("zh_question", "")

    # Notion data
    nq = notion_q or {}
    title = nq.get("title", f"Q{qnum}")
    layer = nq.get("layer", "")
    keywords = nq.get("keywords", "")
    keypoint = nq.get("keypoint", "")
    why = nq.get("why", "")
    flow = nq.get("flow", "")
    note = nq.get("note", "")
    other_reasons = nq.get("other_reasons", {})

    # Scenario (English) — pass keywords for highlighting
    en_scenario = f'<div class="q-scenario lang-en"><strong>Q{qnum}.</strong> {md_inline(en_question, keywords)}</div>'
    zh_scenario = f'<div class="q-scenario zh lang-zh"><strong>Q{qnum}.</strong> {md_inline(zh_question, keywords)}</div>'

    # Options
    opts_html = '<div class="opts">'
    all_letters = sorted(set(list(en_opts.keys()) + list(zh_opts.keys())))
    for letter in all_letters:
        en_opt = en_opts.get(letter, {})
        zh_opt = zh_opts.get(letter, {})
        reason = other_reasons.get(letter, "")
        opts_html += build_option_html(letter, en_opt, zh_opt, reason, correct, keywords)
    opts_html += '</div>'

    # Answer banner
    ans_banner = f'<div class="ans-banner">&#10004; Correct Answer: {correct}</div>' if correct else ""

    # Tags
    layer_tag = f'<span class="tag l">{esc_html(layer)}</span>' if layer else ""
    kw_tags = ""
    if keywords:
        kw_items = [k.strip().lstrip("- ") for k in keywords.split("\n") if k.strip()]
        kw_tags = " ".join(f'<span class="tag l">{esc_html(k)}</span>' for k in kw_items)

    # Notion sections (Chinese analysis)
    kp_html = f'<div class="section lang-zh"><h4>{U_KEYPOINT}</h4><p>{md_inline(keypoint)}</p></div>' if keypoint else ""
    why_html = f'<div class="section lang-zh"><h4>{U_WHY}</h4>{why_to_html(why)}</div>' if why else ""
    flow_html = f'<div class="section lang-zh"><h4>{U_FLOW}</h4><p><code>{esc_html(flow)}</code></p></div>' if flow else ""
    note_html = f'<div class="section lang-zh"><h4>{U_NOTE}</h4><p>{md_inline(note)}</p></div>' if note else ""

    body = en_scenario + zh_scenario + opts_html + ans_banner + f'<div class="meta">{layer_tag}</div>' + f'<div class="meta">{kw_tags}</div>' + kp_html + why_html + flow_html + note_html

    return f'<div class="card" data-qnum="{qnum}" data-title="{esc_html(title)}" data-layer="{esc_html(layer)}" data-kw="{esc_html(keywords)}"><div class="ch" onclick="tog(this)"><span class="qn">Q{qnum}</span><span class="qt">{esc_html(title)}</span><span class="toggle">&#9654;</span></div><div class="cb">{body}</div></div>'


def main():
    print("Loading PDF questions...")
    pdf_qs = load_pdf_questions()
    pdf_by_num = {q["number"]: q for q in pdf_qs}
    print(f"  Loaded {len(pdf_qs)} PDF questions")

    # Load Notion content
    print("Loading Notion content...")
    notion_all = {}
    for name, label, path in NOTION_FILES:
        if not os.path.exists(path):
            print(f"  WARNING: {path} not found, skipping")
            continue
        content = get_notion_content(path)
        nq = parse_notion_questions(content)
        notion_all.update(nq)
        print(f"  {name}: {len(nq)} questions")

    print(f"  Total Notion questions: {len(notion_all)}")

    # Build range info
    ranges = [
        ("Q001-050", "Q1-Q50", 1, 50),
        ("Q051-100", "Q51-Q100", 51, 100),
        ("Q101-150", "Q101-Q150", 101, 150),
        ("Q151-200", "Q151-Q200", 151, 200),
        ("Q201-250", "Q201-Q250", 201, 250),
        ("Q251-300", "Q251-Q300", 251, 300),
        ("Q301-342", "Q301-Q342", 301, 342),
    ]

    total = 0
    for name, label, start, end in ranges:
        # Build cards for this range
        cards = ""
        count = 0
        for qnum in range(start, end + 1):
            q = pdf_by_num.get(qnum)
            if not q:
                continue
            nq = notion_all.get(qnum, {})
            cards += build_card(q, nq, name)
            count += 1
        total += count

        # Build range dropdown
        rsel = '<option value="index.html">總覽</option>'
        for r_name, r_label, _, _ in ranges:
            sel = " selected" if r_name == name else ""
            rsel += f'<option value="{r_name}.html"{sel}>{r_label}</option>'

        # Controls
        controls = """
        <div class="controls">
          <button class="btn btn-lang" data-lang="en" onclick="setLang('en')">EN</button>
          <button class="btn btn-lang" data-lang="zh" onclick="setLang('zh')">中</button>
          <button class="btn btn-lang" data-lang="both" onclick="setLang('both')">雙語</button>
          <span style="flex:1"></span>
          <button class="btn" onclick="expandAll(true)">展開</button>
          <button class="btn" onclick="expandAll(false)">收合</button>
          <button class="btn btn-hl" onclick="setHighlight(document.body.classList.contains('kw-off'))">高亮</button>
        </div>"""

        html = f"""<!DOCTYPE html>
<html lang="zh-TW">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0,maximum-scale=5.0">
<meta name="theme-color" content="#1a1a2e">
<title>AWS DEA - {label}</title>
<style>{CSS}</style>
</head>
<body class="mode-both">
<div class="topbar" id="tb">
  <div class="tbr">
    <h1>DEA-C01 · {label} · {count}</h1>
    <select class="rsel" onchange="if(this.value)location.href=this.value">{rsel}</select>
    <button class="ib ib-search" onclick="toggleSearch()" aria-label="Search">&#128269;</button>
  </div>
  <input type="text" class="search" placeholder="題號 / 關鍵字 / 服務名稱" oninput="filt(this.value)">
  {controls}
</div>
<div class="container">
  <div class="nores">No matching questions</div>
  {cards}
</div>
<div class="footer">AWS DEA-C01 | {count} questions | 2026-08-06</div>
<script>{JS}</script>
</body>
</html>"""

        out_path = os.path.join(TARGET_DIR, f"{name}.html")
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"  Written: {name}.html ({count} questions)")

    # Build index page
    rcards = ""
    for name, label, start, end in ranges:
        cnt = end - start + 1
        if name == "Q301-342":
            cnt = 42
        rcards += f'<a href="{name}.html" style="text-decoration:none"><div style="background:var(--card);border:1px solid var(--border);border-radius:12px;padding:20px;margin-bottom:12px"><div style="font-size:20px;font-weight:bold;color:var(--hl)">{label}</div><div style="font-size:14px;opacity:.7;margin-top:4px">{cnt} questions</div></div></a>'

    idxsel = '<option value="index.html" selected>總覽</option>'
    for r_name, r_label, _, _ in ranges:
        idxsel += f'<option value="{r_name}.html">{r_label}</option>'

    idx_html = f"""<!DOCTYPE html>
<html lang="zh-TW">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0,maximum-scale=5.0">
<meta name="theme-color" content="#1a1a2e">
<title>AWS DEA-C01 Overview</title>
<style>{CSS}</style>
</head>
<body class="mode-both">
<div class="topbar" id="tb">
  <div class="tbr">
    <h1>AWS DEA-C01 題庫</h1>
    <select class="rsel" onchange="if(this.value)location.href=this.value">{idxsel}</select>
  </div>
  <div class="controls">
    <button class="btn btn-lang" data-lang="en" onclick="setLang('en')">EN</button>
    <button class="btn btn-lang" data-lang="zh" onclick="setLang('zh')">中</button>
    <button class="btn btn-lang" data-lang="both" onclick="setLang('both')">雙語</button>
    <span style="flex:1"></span>
    <button class="btn btn-hl" onclick="setHighlight(document.body.classList.contains('kw-off'))">高亮</button>
  </div>
</div>
<div class="container">
  <div style="text-align:center;padding:20px 0 30px">
    <div style="font-size:48px;font-weight:bold;color:var(--hl)">{total}</div>
    <div style="font-size:16px;opacity:.7">Total Questions</div>
  </div>
  {rcards}
  <div style="margin-top:20px">
    <h3 style="color:var(--orange);margin-bottom:10px">Usage</h3>
    <ul style="margin-left:20px;font-size:14px;line-height:2">
      <li>Click range links to browse questions</li>
      <li>Click question cards to expand/collapse</li>
      <li>Use search box to filter by Q number, keyword, or service</li>
      <li>Toggle English / 中文 / 中英對照 mode</li>
      <li>Correct answers shown in green, wrong options in red</li>
      <li>Supports dark/light mode (auto)</li>
    </ul>
  </div>
</div>
<div class="footer">AWS DEA-C01 | 2026-08-06</div>
<script>{JS}</script>
</body>
</html>"""

    idx_path = os.path.join(TARGET_DIR, "index.html")
    with open(idx_path, "w", encoding="utf-8") as f:
        f.write(idx_html)
    print(f"\n  Written: index.html")
    print(f"  Total: {total} questions")


if __name__ == "__main__":
    main()
