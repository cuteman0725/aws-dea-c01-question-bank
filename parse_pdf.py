import fitz
import json
import re

pdf_path = r"D:\Project\00.Doc\AWS_DEA_C01\aws-certified-data-engineer-associate-dea-c01_dual_Kimi+Qwen.pdf"
output_path = r"D:\Project\00.Doc\AWS_DEA_C01\questions.json"

PAGE_MARK = re.compile(r'Page\s+\d+\s+of\s+\d+|第\s*\d+\s*頁\s*，\s*共\s*\d+\s*頁')
CTRL = re.compile(r'[\x00-\x08\x0b\x0c\x0e-\x1f]')
FOOTER = re.compile(r'Amazon\s*[-\u2011]\s*AWS[^\n]*?SecExams\.com')
PAGENUM = re.compile(r'(?m)^\s*\d{1,3}\s*$')
PROMO = re.compile(r'(?m)^.*Only on What.s Needed to Pass!.*$')

doc = fitz.open(pdf_path)
en_parts, zh_parts = [], []
for i in range(doc.page_count):
    t = CTRL.sub('', doc[i].get_text())
    marks = list(PAGE_MARK.finditer(t))
    if len(marks) >= 2:
        en_parts.append(t[:marks[0].start()])
        zh_parts.append(t[marks[0].end():marks[1].start()])
    elif len(marks) == 1:
        en_parts.append(t[:marks[0].start()])
        zh_parts.append(t[marks[0].end():])
    else:
        en_parts.append(t)
doc.close()


def clean(s):
    s = FOOTER.sub('', s)
    s = PROMO.sub('', s)
    return PAGENUM.sub('', s)


en_doc = clean("\n".join(en_parts))
zh_doc = clean("\n".join(zh_parts))
print(f"EN doc: {len(en_doc)}   ZH doc: {len(zh_doc)}")

EN_RE = re.compile(r'Question\s*#\s*(\d{1,3})\s*\n')
ZH_RE = re.compile(r'問題\s*#\s*(\d{1,3})\s*\n')
EN_STOP = re.compile(r'\n\s*(Explanation|Correct Answer\s*:|Community Discussion|Selected Answer)')
ZH_STOP = re.compile(r'\n\s*(說明|正確答案\s*[：:]|社群討論|選取的答案)')
# answer marker in either language, with or without brackets
MARK = re.compile(r'[（(]\s*(?:正\s*確\s*答\s*案|Correct\s+Answer)\s*[）)]')
ANS_LINE = re.compile(r'(?:Correct Answer|正\s*確\s*答\s*案)\s*[：:]\s*([A-E])')
LETTERS = "ABCDE"


def norm(s):
    s = re.sub(r'[ \t]*\n[ \t]*', ' ', s)
    return re.sub(r'\s{2,}', ' ', s).strip()


def find_blocks(text, marker_re):
    real = []
    for m in marker_re.finditer(text):
        after = text[m.end():m.end() + 120]
        if re.match(r'^\s*[\u2022\n]', after):
            continue
        if re.match(r'^\s*(Question\s*#|問題\s*#)', after):
            continue
        real.append(m)
    out = {}
    for i, m in enumerate(real):
        stop = real[i + 1].start() if i + 1 < len(real) else len(text)
        out[int(m.group(1))] = text[m.end():stop]
    return out


def locate_option_starts(body):
    """Find A) B) C) D) E) in sequence; each may sit mid-line."""
    starts = []
    pos = 0
    for idx, L in enumerate(LETTERS):
        pat = re.compile((r'(?m)^\s*' if idx == 0 else r'') + re.escape(L) + r'\)')
        m = pat.search(body, pos)
        if not m and idx > 0:
            m = re.compile(re.escape(L) + r'\)').search(body, pos)
        if not m:
            break
        starts.append((L, m.start(), m.end()))
        pos = m.end()
    return starts


def parse_block(block, stop_re):
    sm = stop_re.search(block)
    body = block[:sm.start()] if sm else block
    tail = block[sm.start():] if sm else ""

    starts = locate_option_starts(body)
    if starts:
        question = norm(body[:starts[0][1]])
    else:
        question = norm(body)

    options, correct = {}, ""
    for i, (L, s, e) in enumerate(starts):
        end = starts[i + 1][1] if i + 1 < len(starts) else len(body)
        text = body[e:end]
        if MARK.search(text):
            correct = L
        options[L] = {'text': norm(MARK.sub('', text)), 'correct': False}

    am = ANS_LINE.search(tail)
    if am:
        correct = am.group(1)
    for L in options:
        options[L]['correct'] = (L == correct)
    return question, options, correct


en_blocks = find_blocks(en_doc, EN_RE)
zh_blocks = find_blocks(zh_doc, ZH_RE)
print(f"EN blocks: {len(en_blocks)}   ZH blocks: {len(zh_blocks)}")

questions = {}
for num in sorted(set(en_blocks) | set(zh_blocks)):
    q = {'number': num, 'en_question': '', 'en_options': {},
         'zh_question': '', 'zh_options': {}, 'correct_answer': ''}
    if num in en_blocks:
        q['en_question'], q['en_options'], c = parse_block(en_blocks[num], EN_STOP)
        if c:
            q['correct_answer'] = c
    if num in zh_blocks:
        q['zh_question'], q['zh_options'], c = parse_block(zh_blocks[num], ZH_STOP)
        if c and not q['correct_answer']:
            q['correct_answer'] = c
    questions[num] = q

q_list = [questions[k] for k in sorted(questions)]

cjk = re.compile(r'[\u4e00-\u9fff]')


def ratio(s):
    return (sum(1 for ch in s if cjk.match(ch)) / len(s)) if s else 0


bad_en = [q['number'] for q in q_list if ratio(q['en_question']) > 0.15]
bad_zh = [q['number'] for q in q_list if q['zh_question'] and ratio(q['zh_question']) < 0.15]
bad_eo = [q['number'] for q in q_list if any(ratio(o['text']) > 0.2 for o in q['en_options'].values())]
no_ans = [q['number'] for q in q_list if not q['correct_answer']]
few_en = [q['number'] for q in q_list if len(q['en_options']) < 4]
few_zh = [q['number'] for q in q_list if len(q['zh_options']) < 4]
empty_opt = [q['number'] for q in q_list if any(not o['text'] for o in q['en_options'].values())]
leftover = [q['number'] for q in q_list for k in ('en_options', 'zh_options')
            for o in q[k].values() if MARK.search(o['text'])]

print(f"Total {len(q_list)} | EN text {sum(1 for q in q_list if q['en_question'])} | ZH text {sum(1 for q in q_list if q['zh_question'])}")
print(f"Correct answers {len(q_list)-len(no_ans)} missing {no_ans[:10]}")
print(f"EN q CJK {len(bad_en)} | ZH q nonCJK {len(bad_zh)} | EN opts CJK {len(bad_eo)} {bad_eo[:8]}")
print(f"EN opts<4 {len(few_en)} {few_en[:8]} | ZH opts<4 {len(few_zh)} {few_zh[:8]}")
print(f"empty EN option text {len(empty_opt)} {empty_opt[:8]}")
print(f"leftover marker {len(leftover)} {leftover[:8]}")

json.dump(q_list, open(output_path, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
print("Saved")
