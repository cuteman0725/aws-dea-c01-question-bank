"""DEA-C01 中文精簡版：手機快速複習用。

用法：
  python gen_short_zh.py prep    # 修正答案並切批次輸入檔到 _work/
  python gen_short_zh.py build   # 合併 _work/out_*.json，檢查字數，產生 short_zh.json 與 Short_ZH.html
"""
import glob
import html
import json
import os
import re
import sys
import unicodedata

BASE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(BASE, "questions.json")
WORK = os.path.join(BASE, "_work")
OUT_JSON = os.path.join(BASE, "short_zh.json")
OUT_HTML = os.path.join(BASE, "Short_ZH.html")
META = os.path.join(BASE, "notion_meta.json")

BATCH = 38
Q_MAX = 100          # 題目字數上限
OPT_MAX_UNITS = 36   # 選項顯示寬度上限（半形單位，中文 = 2）

# PDF 的 "Correct Answer:" 只標一個字母、帶問號，改用社群多數答案
ANSWER_FIX = {87: "AC", 177: "BE"}
# "(SPICE)" 的 "E)" 被誤判成選項 E，需把 E 併回 D
MERGE_E_INTO_D = {215, 233}
# PDF 答案與社群多數票不同，卡片上加註提醒（不改答案）
COMMUNITY = {23: "B", 39: "C", 44: "B", 101: "A", 127: "D", 145: "A", 210: "AC", 221: "D"}
NOTE = {323: "原題選項為 SQL 圖片，選項文字為依題意重建"}


def full_answers():
    """從 PDF 原文重新抓多字母答案（原 questions.json 只存第一個字母）。"""
    import fitz
    pdf = glob.glob(os.path.join(BASE, "*.pdf"))[0]
    doc = fitz.open(pdf)
    text = "".join(p.get_text() for p in doc)
    doc.close()
    marks = [m for m in re.finditer(r"Question\s*#\s*(\d{1,3})\s*\n", text)
             if not re.match(r"^\s*[\u2022\n]", text[m.end():m.end() + 5])
             and not re.match(r"^\s*Question", text[m.end():m.end() + 20])]
    ans = {}
    for i, m in enumerate(marks):
        n = int(m.group(1))
        end = marks[i + 1].start() if i + 1 < len(marks) else len(text)
        a = re.search(r"Correct Answer\s*[:：]\s*([A-E]+)", text[m.end():end])
        if a and n not in ans:
            ans[n] = a.group(1)
    return ans


def load_fixed():
    qs = json.load(open(SRC, encoding="utf-8"))
    ans = full_answers()
    for q in qs:
        n = q["number"]
        if n in MERGE_E_INTO_D:
            for k in ("en_options", "zh_options"):
                o = q[k]
                if "E" in o:
                    o["D"]["text"] = o["D"]["text"] + "E" + o.pop("E")["text"]
        q["correct_answer"] = ANSWER_FIX.get(n, ans.get(n, q["correct_answer"]))
        q["multi"] = len(q["correct_answer"]) > 1
    return qs


def prep():
    os.makedirs(WORK, exist_ok=True)
    qs = load_fixed()
    slim = [{
        "number": q["number"],
        "answer": q["correct_answer"],
        "multi": q["multi"],
        "en_question": q["en_question"],
        "en_options": {k: v["text"] for k, v in q["en_options"].items()},
        "zh_question": q["zh_question"],
    } for q in qs]
    for i in range(0, len(slim), BATCH):
        part = slim[i:i + BATCH]
        name = f"in_{part[0]['number']:03d}-{part[-1]['number']:03d}.json"
        json.dump(part, open(os.path.join(WORK, name), "w", encoding="utf-8"),
                  ensure_ascii=False, indent=1)
        print(name, len(part))


def units(s):
    return sum(2 if unicodedata.east_asian_width(c) in "WF" else 1 for c in s)


def load_notion():
    m = json.load(open(META, encoding="utf-8"))
    answers = {int(re.match(r"\d+", t).group()): re.sub(r"^\d+", "", t) for t in m["answers"].split()}
    sections = {int(q): s for q, s in re.findall(r"Q(\d+) → (\d+\.\d+)", m["chapter_index"])}
    return m, answers, sections


def build():
    src = {q["number"]: q for q in load_fixed()}
    meta, notion_ans, sections = load_notion()
    items = {}
    for f in sorted(glob.glob(os.path.join(WORK, "out_*.json"))):
        for it in json.load(open(f, encoding="utf-8")):
            items[it["number"]] = it

    problems = []
    for n, q in src.items():
        it = items.get(n)
        if not it:
            problems.append(f"Q{n}: 缺少")
            continue
        it["answer"] = q["correct_answer"]
        it["multi"] = q["multi"]
        it["section"] = sections.get(n, "")
        if notion_ans.get(n) != it["answer"]:
            problems.append(f"Q{n}: 答案 {it['answer']} 與 Notion {notion_ans.get(n)} 不同")
        if not it["section"]:
            problems.append(f"Q{n}: Notion 無章節")
        if set(it["opts"]) != set(q["en_options"]):
            problems.append(f"Q{n}: 選項字母不符 {sorted(it['opts'])}")
        if len(it["q"]) > Q_MAX:
            problems.append(f"Q{n}: 題目 {len(it['q'])} 字")
        for k, v in it["opts"].items():
            if units(v) > OPT_MAX_UNITS:
                problems.append(f"Q{n}{k}: 選項寬 {units(v)} > {OPT_MAX_UNITS}「{v}」")
    for p in problems:
        print(p)
    print(f"共 {len(items)} 題，問題 {len(problems)} 筆")

    data = [items[n] for n in sorted(items)]
    json.dump(data, open(OUT_JSON, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    open(OUT_HTML, "w", encoding="utf-8").write(render(data, meta))
    print("已輸出", OUT_JSON, OUT_HTML)


CSS = """
*{box-sizing:border-box}
:root{--bg:#f4f5f7;--card:#fff;--fg:#1d1d1f;--sub:#666;--line:#e3e3e8;--ok:#1a7f37;--okbg:#e6f6ea;--ng:#c62828;--ngbg:#fdecea;--acc:#ff9900}
@media(prefers-color-scheme:dark){:root{--bg:#111;--card:#1c1c1e;--fg:#eee;--sub:#999;--line:#333;--ok:#4cc26a;--okbg:#14301c;--ng:#ff6b6b;--ngbg:#3a1616}}
body{margin:0;background:var(--bg);color:var(--fg);font:16px/1.55 -apple-system,"Noto Sans TC","Microsoft JhengHei",sans-serif}
header{position:sticky;top:0;z-index:9;background:var(--card);border-bottom:1px solid var(--line);padding:6px 10px;display:flex;gap:6px;align-items:center;flex-wrap:wrap}
header b{font-size:15px;margin-right:auto}
header button,header select{font-size:14px;padding:4px 8px;border:1px solid var(--line);border-radius:6px;background:var(--bg);color:var(--fg)}
header button.on{background:var(--acc);color:#000;border-color:var(--acc)}
#stat{font-size:13px;color:var(--sub);width:100%}
main{padding:6px 4px}
.c{background:var(--card);border-radius:10px;padding:8px 8px;margin:0 0 10px;border:1px solid var(--line)}
.h{display:flex;gap:6px;align-items:center;font-size:13px;color:var(--sub);margin-bottom:4px}
.tag{border-radius:4px;padding:0 6px;font-size:12px;background:var(--line);color:var(--fg)}
.tag.m{background:var(--acc);color:#000}
.tag.w{background:var(--ngbg);color:var(--ng)}
.star{margin-left:auto;cursor:pointer;font-size:18px;line-height:1;color:var(--sub)}
.star.on{color:var(--acc)}
.q{margin:0 0 6px}
.o{display:flex;gap:4px;padding:5px 5px;border-radius:6px;border:1px solid var(--line);margin-top:5px;cursor:pointer;white-space:nowrap;overflow:hidden}
.o i{font-style:normal;font-weight:700;width:13px;flex:none}
.o span{overflow:hidden;text-overflow:ellipsis}
.o.pick{border-color:var(--acc)}
.done .o.ok{background:var(--okbg);border-color:var(--ok);color:var(--ok)}
.done .o.pick:not(.ok){background:var(--ngbg);border-color:var(--ng);color:var(--ng)}
.k{display:none;margin-top:6px;font-size:14px;color:var(--sub)}
.done .k{display:block}
.btn{margin-top:6px;font-size:14px;padding:4px 10px;border-radius:6px;border:1px solid var(--line);background:var(--bg);color:var(--fg)}
body.show .o.ok{background:var(--okbg);border-color:var(--ok);color:var(--ok)}
body.show .k{display:block}
body.show .btn{display:none}
.tag.s{background:none;border:1px solid var(--line);color:var(--sub)}
.ch{font-size:15px;margin:14px 2px 8px;padding:6px 8px;border-left:4px solid var(--acc);background:var(--card);border-radius:4px}
.ch small{color:var(--sub);font-weight:400;margin-left:6px}
body.num .ch{display:none}
#weak{display:none;width:100%;max-height:60vh;overflow:auto;font-size:14px}
#weak.on{display:block}
#weak div{display:flex;gap:6px;align-items:center;padding:5px 2px;border-top:1px solid var(--line);cursor:pointer}
#weak div span:first-child{flex:1;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
#weak i{font-style:normal;width:44px;flex:none;text-align:right}
#weak u{width:40px;flex:none}
#weak b{display:block;height:6px;border-radius:3px;background:var(--ng)}
#weak b.g{background:var(--ok)}
#weak b.y{background:var(--acc)}
.c.a1{border-left:4px solid var(--ok)}
.c.a0{border-left:4px solid var(--ng)}
.c.last{outline:2px solid var(--acc)}
.tag.l{display:none;background:var(--acc);color:#000}
.c.last .tag.l{display:inline}
.c.go{outline:2px dashed var(--acc)}
"""

JS = """
const LS='dea_short_zh_',$=id=>document.getElementById(id);
history.scrollRestoration='manual';
const res=JSON.parse(localStorage.getItem(LS+'res')||'{}');
JSON.parse(localStorage.getItem(LS+'wrong')||'[]').forEach(n=>{if(!(n in res))res[n]=0});
const star=new Set(JSON.parse(localStorage.getItem(LS+'star')||'[]'));
let last=localStorage.getItem(LS+'last');
const main=document.querySelector('main'),cards=[...document.querySelectorAll('.c')],heads=[...document.querySelectorAll('.ch')];
let rnd=false;
const save=()=>{localStorage.setItem(LS+'res',JSON.stringify(res));localStorage.removeItem(LS+'wrong');
  localStorage.setItem(LS+'star',JSON.stringify([...star]));stat();weak()};
function stat(){const v=Object.values(res),w=v.filter(x=>!x).length,d=v.length;
  $('stat').textContent=`已作答 ${d}｜答對率 ${d?Math.round((d-w)*100/d):0}%｜錯題 ${w}｜星號 ${star.size}｜顯示 ${cards.filter(c=>c.style.display!=='none').length} 題`+(last?`｜上次 Q${last}`:'')}
function mark(c){const n=c.dataset.n;c.classList.toggle('a1',res[n]===1);c.classList.toggle('a0',res[n]===0);c.classList.toggle('last',n===last)}
function resume(){
  const vis=[...main.querySelectorAll('.c')].filter(c=>c.style.display!=='none'),i=vis.findIndex(c=>c.dataset.n===last),
    t=vis.slice(i+1).find(c=>!(c.dataset.n in res))||vis.find(c=>!(c.dataset.n in res))||vis[i];
  if(!t)return;
  cards.forEach(c=>c.classList.toggle('go',c===t));
  scrollTo(0,t.getBoundingClientRect().top+scrollY-document.querySelector('header').offsetHeight-6)}
function weak(){
  const rows=heads.map(h=>{const c=h.dataset.c,cs=cards.filter(x=>x.dataset.c===c),
    d=cs.filter(x=>x.dataset.n in res).length,ok=cs.filter(x=>res[x.dataset.n]===1).length;
    return {c,name:h.dataset.name,t:cs.length,d,p:d?ok/d:-1}});
  rows.sort((a,b)=>(a.p<0)-(b.p<0)||a.p-b.p);
  $('weak').innerHTML='<div style="cursor:default"><span>弱→強（點選只看該章）</span><i>作答</i><i>答對</i><u></u></div>'+
    rows.map(r=>`<div data-c="${r.c}"><span>${r.c}. ${r.name}</span><i>${r.d}/${r.t}</i><i>${r.p<0?'—':Math.round(r.p*100)+'%'}</i>`+
    `<u><b class="${r.p>=.8?'g':r.p>=.6?'y':''}" style="width:${r.p<0?0:Math.max(4,r.p*40)}px"></b></u></div>`).join('');
  $('weak').querySelectorAll('div[data-c]').forEach(e=>e.onclick=()=>{$('flt').value='c'+e.dataset.c;apply();$('wk').click()})}
function judge(c){
  const need=c.dataset.a.length,picks=[...c.querySelectorAll('.o.pick')];
  if(picks.length<need)return;
  c.classList.add('done');
  res[c.dataset.n]=picks.every(p=>p.classList.contains('ok'))?1:0;
  last=c.dataset.n;localStorage.setItem(LS+'last',last);cards.forEach(mark);save()}
function layout(){
  const num=$('ord').value==='num';document.body.classList.toggle('num',num);
  const key=rnd?(c=>+c.dataset.r):num?(c=>+c.dataset.n):(c=>+c.dataset.o);
  if(num){[...cards].sort((a,b)=>key(a)-key(b)).forEach(c=>main.appendChild(c))}
  else heads.forEach(h=>{main.appendChild(h);cards.filter(c=>c.dataset.c===h.dataset.c).sort((a,b)=>key(a)-key(b)).forEach(c=>main.appendChild(c))})}
function apply(){
  const v=$('flt').value,st=$('st').value;localStorage.setItem(LS+'flt',v);localStorage.setItem(LS+'st',st);
  cards.forEach(c=>{const n=c.dataset.n;let s=st==='all'||(st==='done')===(n in res);
    if(!s);else if(v==='wrong')s=res[n]===0;else if(v==='star')s=star.has(n);
    else if(v==='multi')s=c.dataset.a.length>1;else if(v==='dis')s=!!c.dataset.d;
    else if(v[0]==='c')s=c.dataset.c===v.slice(1);
    else if(v.includes('-')){const[a,b]=v.split('-').map(Number);s=+n>=a&&+n<=b}
    c.style.display=s?'':'none'});
  heads.forEach(h=>h.style.display=cards.some(c=>c.dataset.c===h.dataset.c&&c.style.display!=='none')?'':'none');
  stat();scrollTo(0,0)}
cards.forEach(c=>{
  const n=c.dataset.n;
  if(star.has(n))c.querySelector('.star').classList.add('on');
  c.querySelectorAll('.o').forEach(o=>o.onclick=()=>{if(c.classList.contains('done'))return;o.classList.toggle('pick');judge(c)});
  c.querySelector('.btn').onclick=()=>{c.classList.toggle('done')};
  c.querySelector('.star').onclick=e=>{const s=e.target;s.classList.toggle('on');s.classList.contains('on')?star.add(n):star.delete(n);save()};
});
$('show').onclick=e=>{document.body.classList.toggle('show');e.target.classList.toggle('on')};
$('reset').onclick=()=>cards.forEach(c=>{c.classList.remove('done');c.querySelectorAll('.pick').forEach(p=>p.classList.remove('pick'))});
$('flt').onchange=apply;$('st').onchange=apply;
$('ord').onchange=()=>{localStorage.setItem(LS+'ord',$('ord').value);rnd=false;layout();scrollTo(0,0)};
$('go').onclick=resume;
$('shuf').onclick=()=>{rnd=true;cards.forEach(c=>c.dataset.r=Math.random());layout();scrollTo(0,0)};
$('wk').onclick=e=>{$('weak').classList.toggle('on');e.target.classList.toggle('on')};
let so=localStorage.getItem(LS+'ord'),sf=localStorage.getItem(LS+'flt'),ss=localStorage.getItem(LS+'st');
if(sf==='todo'){sf='all';ss='todo'}
if(so)$('ord').value=so;
if(ss)$('st').value=ss;
if(sf&&[...$('flt').options].some(o=>o.value===sf))$('flt').value=sf;
layout();weak();apply();cards.forEach(mark);
if(last)resume();
"""


def sec_key(s):
    c, m = s.split(".")
    return int(c), int(m)


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
        f'<h2 class="ch" data-c="{c}" data-name="{html.escape(v)}">{c}. {html.escape(v)}<small>{count.get(c, 0)} 題</small></h2>'
        for c, v in chapters.items())
    cards = []
    for it in data:
        n, a, s = it["number"], it["answer"], it["section"]
        tag = f'<span class="tag m">複選 {len(a)}</span>' if len(a) > 1 else '<span class="tag">單選</span>'
        tag += f'<span class="tag s">{s}</span>'
        opts = "".join(
            f'<div class="o{" ok" if k in a else ""}"><i>{k}</i><span>{html.escape(v)}</span></div>'
            for k, v in sorted(it["opts"].items()))
        key = html.escape(it.get("key", ""))
        dis = ""
        if n in disputed:
            dis = ' data-d="1"'
            tag += '<span class="tag w">⚠ 爭議</span>'
            notes = [f"社群多選 {COMMUNITY[n]}"] if n in COMMUNITY else []
            if n in dnote and (n not in COMMUNITY or COMMUNITY[n] not in dnote[n]):
                notes.append(dnote[n])
            key += f"<br>⚠ {html.escape('；'.join(notes) or '社群答案有分歧')}"
        if n in NOTE:
            key += f"<br>※ {html.escape(NOTE[n])}"
        cards.append(
            f'<div class="c" data-n="{n}" data-a="{a}" data-c="{s.split(".")[0]}" data-o="{rank[n]}"{dis}>'
            f'<div class="h"><b>Q{n}</b>{tag}<span class="tag l">上次</span>'
            f'<span class="star">★</span></div><p class="q">{html.escape(it["q"])}</p>{opts}'
            f'<div class="k">答案 <b>{a}</b>｜{key}</div><button class="btn">看答案</button></div>')
    return f"""<!DOCTYPE html><html lang="zh-Hant"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>DEA-C01 中文精簡版</title><style>{CSS}</style></head><body>
<header><b>DEA-C01 精簡 342 題</b>
<select id="ord"><option value="topic">依主題</option><option value="num">依題號</option></select>
<select id="st"><option value="all">全部狀態</option><option value="todo">未作答</option><option value="done">已作答</option></select>
<select id="flt"><option value="all">全部</option><optgroup label="主題">{ch_opts}</optgroup>
<optgroup label="篩選"><option value="wrong">只看錯題</option>
<option value="star">只看星號</option><option value="multi">只看複選</option><option value="dis">只看爭議題</option></optgroup>
<optgroup label="題號">{ranges}</optgroup></select>
<button id="go">接續</button><button id="wk">弱項</button><button id="show">全顯答案</button><button id="shuf">亂序</button><button id="reset">重作</button>
<div id="stat"></div><div id="weak"></div></header>
<main>{heads}{''.join(cards)}</main><script>{JS}</script></body></html>"""


if __name__ == "__main__":
    {"prep": prep, "build": build}[sys.argv[1] if len(sys.argv) > 1 else "build"]()
