"""DEA-C01 答案速讀版：只列題目、正確答案、5 行內說明與流程圖。

用法：
  python gen_answer_zh.py prep    # 從 short_zh.json + questions.json + Q*.html（Notion 解析）切批次到 _work/ans_in_*.json
  python gen_answer_zh.py check _work/ans_out_001-038.json   # 檢查單一批次
  python gen_answer_zh.py build   # 合併 _work/ans_out_*.json，檢查長度，產生 answer_zh.json 與 Answer_ZH.html
"""
import glob
import html
import json
import os
import re
import sys

from gen_short_zh import COMMUNITY, MERGE_E_INTO_D, NOTE, load_notion, sec_key, units

BASE = os.path.dirname(os.path.abspath(__file__))
SHORT = os.path.join(BASE, "short_zh.json")
SRC = os.path.join(BASE, "questions.json")
WORK = os.path.join(BASE, "_work")
OUT_JSON = os.path.join(BASE, "answer_zh.json")
OUT_HTML = os.path.join(BASE, "Answer_ZH.html")

BATCH = 38
WHY_MAX_UNITS = 180   # 說明寬度上限（半形單位，中文 = 2）；360px 手機約 5 行
NODE_MAX_UNITS = 26   # 流程圖每一格寬度上限
NODES = (2, 5)        # 流程圖格數


def text(s):
    return html.unescape(re.sub(r"<[^>]+>", "", s)).strip()


def notion_sections():
    """從完整版 Q*.html 取回 Notion 解析（一句考點、為什麼、超短流程圖）。"""
    out = {}
    for f in sorted(glob.glob(os.path.join(BASE, "Q*.html"))):
        s = open(f, encoding="utf-8").read()
        for m in re.finditer(r'<div class="card" data-qnum="(\d+)"(.*?)(?=<div class="card" data-qnum=|<script)', s, re.S):
            secs = dict(re.findall(r'<div class="section lang-zh"><h4>(.*?)</h4>(.*?)</div>', m.group(2), re.S))
            out[int(m.group(1))] = {
                "keypoint": text(secs.get("一句考點", "")),
                "why": [text(li) for li in re.findall(r"<li>(.*?)</li>", secs.get("為什麼", ""), re.S)],
                "flow": text(secs.get("超短流程圖", "")),
            }
    return out


def prep():
    os.makedirs(WORK, exist_ok=True)
    short = json.load(open(SHORT, encoding="utf-8"))
    src = {q["number"]: q for q in json.load(open(SRC, encoding="utf-8"))}
    notion = notion_sections()
    meta, _, _ = load_notion()
    dnote = {int(k): v for k, v in meta["disputed_note"].items()}
    slim = []
    for it in short:
        n, a = it["number"], it["answer"]
        en = {k: v["text"] for k, v in src[n]["en_options"].items()}
        if n in MERGE_E_INTO_D and "E" in en:
            en["D"] += "E" + en.pop("E")
        slim.append({
            "number": n,
            "answer": a,
            "q_zh": it["q"],
            "q_en": src[n]["en_question"],
            "answer_zh": {k: it["opts"][k] for k in a},
            "answer_en": {k: en[k] for k in a},
            "notion": notion.get(n, {}),
            "disputed": dnote.get(n, "") or (f"社群多選 {COMMUNITY[n]}" if n in COMMUNITY else ""),
        })
    for i in range(0, len(slim), BATCH):
        part = slim[i:i + BATCH]
        name = f"ans_in_{part[0]['number']:03d}-{part[-1]['number']:03d}.json"
        json.dump(part, open(os.path.join(WORK, name), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print(name, len(part))


def check(items, numbers):
    problems = []
    for n in numbers:
        it = items.get(n)
        if not it:
            problems.append(f"Q{n}: 缺少")
            continue
        if not it.get("why") or units(it["why"]) > WHY_MAX_UNITS:
            problems.append(f"Q{n}: 說明寬 {units(it.get('why', ''))} > {WHY_MAX_UNITS}")
        flow = it.get("flow") or []
        if not NODES[0] <= len(flow) <= NODES[1]:
            problems.append(f"Q{n}: 流程圖 {len(flow)} 格")
        if sum(x.startswith("*") for x in flow) > 1:
            problems.append(f"Q{n}: 重點格超過 1 個")
        for x in flow:
            if not x.lstrip("*") or units(x.lstrip("*")) > NODE_MAX_UNITS:
                problems.append(f"Q{n}: 流程格寬 {units(x.lstrip('*'))} > {NODE_MAX_UNITS}「{x}」")
    return problems


def build():
    short = json.load(open(SHORT, encoding="utf-8"))
    meta, _, _ = load_notion()
    items = {}
    for f in sorted(glob.glob(os.path.join(WORK, "ans_out_*.json"))):
        for it in json.load(open(f, encoding="utf-8")):
            items[it["number"]] = it
    problems = check(items, [it["number"] for it in short])
    for p in problems:
        print(p)
    print(f"共 {len(items)} 題，問題 {len(problems)} 筆")

    data = []
    for it in short:
        n = it["number"]
        x = items.get(n, {})
        data.append({"number": n, "q": it["q"], "answer": it["answer"],
                     "answer_text": {k: it["opts"][k] for k in it["answer"]},
                     "section": it["section"], "why": x.get("why", ""), "flow": x.get("flow", [])})
    json.dump(data, open(OUT_JSON, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    open(OUT_HTML, "w", encoding="utf-8").write(render(data, meta))
    print("已輸出", OUT_JSON, OUT_HTML)


CSS = """
*{box-sizing:border-box}
:root{--bg:#f4f5f7;--card:#fff;--fg:#1d1d1f;--sub:#666;--line:#e3e3e8;--ok:#1a7f37;--okbg:#e6f6ea;--ng:#c62828;--ngbg:#fdecea;--acc:#ff9900;--accbg:#fff3df}
@media(prefers-color-scheme:dark){:root{--bg:#111;--card:#1c1c1e;--fg:#eee;--sub:#999;--line:#333;--ok:#4cc26a;--okbg:#14301c;--ng:#ff6b6b;--ngbg:#3a1616;--accbg:#3a2a10}}
body{margin:0;background:var(--bg);color:var(--fg);font:16px/1.55 -apple-system,"Noto Sans TC","Microsoft JhengHei",sans-serif}
header{position:sticky;top:0;z-index:9;background:var(--card);border-bottom:1px solid var(--line);padding:6px 10px;display:flex;gap:6px;align-items:center;flex-wrap:wrap}
header b{font-size:15px;margin-right:auto}
header select,header input{font-size:14px;padding:4px 8px;border:1px solid var(--line);border-radius:6px;background:var(--bg);color:var(--fg)}
#flt{max-width:40%}
#kw{flex:1;min-width:0}
header a{font-size:13px;color:var(--acc);white-space:nowrap}
main{padding:6px 4px}
.c{background:var(--card);border-radius:10px;padding:8px 8px;margin:0 0 10px;border:1px solid var(--line)}
.h{display:flex;gap:6px;align-items:center;font-size:13px;color:var(--sub);margin-bottom:4px}
.tag{border-radius:4px;padding:0 6px;font-size:12px;background:var(--line);color:var(--fg)}
.tag.m{background:var(--acc);color:#000}
.tag.s{background:none;border:1px solid var(--line);color:var(--sub)}
.tag.w{background:var(--ngbg);color:var(--ng)}
.q{margin:0 0 6px}
.a{display:flex;gap:6px;padding:5px 6px;border-radius:6px;border:1px solid var(--ok);background:var(--okbg);color:var(--ok);margin-top:5px;font-weight:600}
.a i{font-style:normal;flex:none}
.y{margin:8px 0 0;font-size:15px}
.f{display:flex;flex-wrap:wrap;align-items:center;gap:6px 4px;margin-top:8px;font-size:13px}
.f span{border:1px solid var(--line);border-radius:6px;padding:2px 7px;background:var(--bg)}
.f span.x{border-color:var(--acc);background:var(--accbg);font-weight:600}
.f i{font-style:normal;color:var(--sub)}
.f i::before{content:"→"}
@media(max-width:600px){
.f.w{flex-direction:column;align-items:flex-start;gap:0}
.f.w i{line-height:1.2;padding-left:14px}
.f.w i::before{content:"↓"}}
.n{margin-top:6px;font-size:13px;color:var(--sub)}
.c.hit{outline:3px solid var(--acc)}
.ch{font-size:15px;margin:14px 2px 8px;padding:6px 8px;border-left:4px solid var(--acc);background:var(--card);border-radius:4px}
.ch small{color:var(--sub);font-weight:400;margin-left:6px}
body.num .ch{display:none}
"""

JS = """
const LS='dea_answer_zh_',$=id=>document.getElementById(id);
history.scrollRestoration='manual';
const main=document.querySelector('main'),cards=[...document.querySelectorAll('.c')],heads=[...document.querySelectorAll('.ch')],hdr=document.querySelector('header');
// 練習版（Short_ZH）的錯題：同一個網站共用 localStorage
function wrongSet(){try{const r=JSON.parse(localStorage.getItem('dea_short_zh_res')||'{}');return new Set(Object.keys(r).filter(n=>r[n]===0))}catch(e){return new Set()}}
const WR=wrongSet(),qp=new URLSearchParams(location.search).get('q');
const LIST=qp?new Set(qp.split(',').map(x=>x.trim()).filter(x=>/^\d+$/.test(x))):null;
$('flt').querySelector('option[value="wrong"]').textContent=`只看練習版錯題（${WR.size}）`;
if(LIST)$('flt').querySelector('optgroup[label="篩選"]').prepend(new Option(`連結指定的 ${LIST.size} 題`,'list'));
function layout(){
  const num=$('ord').value==='num';document.body.classList.toggle('num',num);
  if(num)[...cards].sort((a,b)=>a.dataset.n-b.dataset.n).forEach(c=>main.appendChild(c));
  else heads.forEach(h=>{main.appendChild(h);cards.filter(c=>c.dataset.c===h.dataset.c).sort((a,b)=>a.dataset.o-b.dataset.o).forEach(c=>main.appendChild(c))})}
function apply(){
  const v=$('flt').value,k=$('kw').value.trim().toLowerCase();
  cards.forEach(c=>{const n=c.dataset.n;let s=true;
    if(v==='multi')s=c.dataset.a.length>1;else if(v==='dis')s=!!c.dataset.d;
    else if(v==='wrong')s=WR.has(n);else if(v==='list')s=LIST.has(n);
    else if(v[0]==='c')s=c.dataset.c===v.slice(1);
    else if(v.includes('-')){const[a,b]=v.split('-').map(Number);s=+n>=a&&+n<=b}
    if(s&&k)s=('q'+n+' '+c.textContent).toLowerCase().includes(k);
    c.style.display=s?'':'none'});
  heads.forEach(h=>h.style.display=cards.some(c=>c.dataset.c===h.dataset.c&&c.style.display!=='none')?'':'none');
  $('cnt').textContent=cards.filter(c=>c.style.display!=='none').length}
function firstVisible(){const y=hdr.offsetHeight;return cards.find(c=>c.style.display!=='none'&&c.getBoundingClientRect().bottom>y+4)}
function go(c){scrollTo(0,c.getBoundingClientRect().top+scrollY-hdr.offsetHeight-6)}
let t;addEventListener('scroll',()=>{clearTimeout(t);t=setTimeout(()=>{const c=firstVisible();if(c)localStorage.setItem(LS+'at',c.dataset.n)},200)});
$('ord').onchange=()=>{localStorage.setItem(LS+'ord',$('ord').value);layout();scrollTo(0,0)};
$('flt').onchange=()=>{localStorage.setItem(LS+'flt',$('flt').value);apply();scrollTo(0,0)};
$('kw').oninput=()=>{apply();scrollTo(0,0)};
const so=localStorage.getItem(LS+'ord'),sf=localStorage.getItem(LS+'flt'),at=localStorage.getItem(LS+'at');
if(so)$('ord').value=so;
if(sf&&[...$('flt').options].some(o=>o.value===sf))$('flt').value=sf;
if(LIST)$('flt').value='list';
// #q17：從練習版點題號過來，直接捲到那一題
function hashGo(){const m=location.hash.match(/^#q(\d+)$/),c=m&&cards.find(x=>x.dataset.n===m[1]);if(!c)return false;
  if(c.style.display==='none'){$('kw').value='';$('flt').value='all';apply()}
  cards.forEach(x=>x.classList.toggle('hit',x===c));go(c);return true}
addEventListener('hashchange',hashGo);
layout();apply();
if(!hashGo()&&!LIST){const c0=cards.find(c=>c.dataset.n===at&&c.style.display!=='none');if(c0)go(c0)}
"""


PHONE_LINE_UNITS = 44   # 手機一行約可放的流程圖寬度；超過就在窄螢幕改成直式


def flow_html(flow):
    if not flow:
        return ""
    parts = []
    for x in flow:
        cls = ' class="x"' if x.startswith("*") else ""
        parts.append(f'<span{cls}>{html.escape(x.lstrip("*"))}</span>')
    width = sum(units(x.lstrip("*")) + 4 for x in flow) + 3 * (len(flow) - 1)
    cls = "f w" if width > PHONE_LINE_UNITS else "f"
    return f'<div class="{cls}">' + "<i></i>".join(parts) + "</div>"


def render(data, meta):
    chapters = meta["chapters"]
    disputed = set(meta["disputed"]) | set(COMMUNITY)
    dnote = {int(k): v for k, v in meta["disputed_note"].items()}
    ranges = "".join(f'<option value="{a}-{min(a + 49, 342)}">Q{a}–{min(a + 49, 342)}</option>'
                     for a in range(1, 343, 50))
    ch_opts = "".join(f'<option value="c{c}">{c}. {html.escape(v)}</option>' for c, v in chapters.items())
    order = sorted(data, key=lambda it: (sec_key(it["section"]), it["number"]))
    rank = {it["number"]: i for i, it in enumerate(order)}
    count = {}
    for it in data:
        c = it["section"].split(".")[0]
        count[c] = count.get(c, 0) + 1
    heads = "".join(
        f'<h2 class="ch" data-c="{c}">{c}. {html.escape(v)}<small>{count.get(c, 0)} 題</small></h2>'
        for c, v in chapters.items())
    cards = []
    for it in data:
        n, a, s = it["number"], it["answer"], it["section"]
        tag = f'<span class="tag m">複選 {len(a)}</span>' if len(a) > 1 else '<span class="tag">單選</span>'
        tag += f'<span class="tag s">{s}</span>'
        dis, notes = "", []
        if n in disputed:
            dis = ' data-d="1"'
            tag += '<span class="tag w">⚠ 爭議</span>'
            ds = [f"社群多選 {COMMUNITY[n]}"] if n in COMMUNITY else []
            if n in dnote and (n not in COMMUNITY or COMMUNITY[n] not in dnote[n]):
                ds.append(dnote[n])
            notes.append("⚠ " + html.escape("；".join(ds) or "社群答案有分歧"))
        if n in NOTE:
            notes.append("※ " + html.escape(NOTE[n]))
        ans = "".join(f'<div class="a"><i>{k}</i><span>{html.escape(v)}</span></div>'
                      for k, v in it["answer_text"].items())
        note = f'<div class="n">{"<br>".join(notes)}</div>' if notes else ""
        cards.append(
            f'<div class="c" data-n="{n}" data-a="{a}" data-c="{s.split(".")[0]}" data-o="{rank[n]}"{dis}>'
            f'<div class="h"><b>Q{n}</b>{tag}</div><p class="q">{html.escape(it["q"])}</p>{ans}'
            f'<p class="y">{html.escape(it["why"])}</p>{flow_html(it["flow"])}{note}</div>')
    return f"""<!DOCTYPE html><html lang="zh-Hant"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>DEA-C01 答案速讀</title><style>{CSS}</style></head><body>
<header><b>DEA-C01 答案速讀 <span id="cnt">342</span> 題</b><a href="Short_ZH.html">作答練習版 →</a>
<div style="width:100%;display:flex;gap:6px"><select id="ord"><option value="topic">依主題</option><option value="num">依題號</option></select>
<select id="flt"><option value="all">全部</option><optgroup label="主題">{ch_opts}</optgroup>
<optgroup label="篩選"><option value="wrong">只看練習版錯題</option><option value="multi">只看複選</option><option value="dis">只看爭議題</option></optgroup>
<optgroup label="題號">{ranges}</optgroup></select>
<input id="kw" type="search" placeholder="搜尋"></div></header>
<main>{heads}{''.join(cards)}</main><script>{JS}</script></body></html>"""


def check_file(path):
    """檢查單一批次輸出：python gen_answer_zh.py check _work/ans_out_001-038.json"""
    src = os.path.join(os.path.dirname(path), os.path.basename(path).replace("ans_out_", "ans_in_"))
    numbers = [it["number"] for it in json.load(open(src, encoding="utf-8"))]
    items = {it["number"]: it for it in json.load(open(path, encoding="utf-8"))}
    problems = check(items, numbers) + [f"Q{n}: 不屬於這一批" for n in items if n not in numbers]
    for p in problems:
        print(p)
    print(f"{os.path.basename(path)}：{len(items)}/{len(numbers)} 題，問題 {len(problems)} 筆")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "build"
    if cmd == "check":
        check_file(sys.argv[2])
    else:
        {"prep": prep, "build": build}[cmd]()
