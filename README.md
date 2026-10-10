# AWS DEA-C01 題庫

> AWS Certified Data Engineer - Associate (DEA-C01) 考古題庫
> 產生日期：2026-08-06｜總題數：342 題

## 簡介

從 Notion「DEA 刷題｜AI 解題紀錄」取得 342 題 AWS DEA-C01 考古題的中文解析，結合 PDF 原文的英文題目與中文翻譯，產生含中英切換的手機易讀 HTML 格式。

## 功能特色

- **中英切換**：English / 中文 / 中英對照三種模式，一鍵切換
- **考試格式呈現**：每題顯示完整題目原文 + A/B/C/D 選項，正確答案綠色、錯誤選項紅色
- **不選原因**：每個錯誤選項附帶 Notion 筆記的「為什麼不選」原因
- **中文翻譯**：每個選項下方附中文翻譯
- **關鍵字高亮**：題目和選項中出現的 Keywords 會自動加粗 + 黃底高亮，可一鍵開關
- **Notion 解析**：一句考點、為什麼、超短流程圖、一行筆記
- **展開/收合全部**：一鍵展開或收合所有題目卡片
- **手機優化版面**：topbar 僅佔 77px（原 279px），往下捲動時自動隱藏，可視區增加 44%
- **響應式設計**：自動適應手機與桌面螢幕
- **深色/淺色模式**：依系統偏好自動切換
- **即時搜尋**：依題號、標題、分層、Keywords 或內文篩選
- **記憶語言偏好**：使用 localStorage 記住上次選擇的語言模式

## 檔案結構

| 檔案 | 說明 |
|------|------|
| `index.html` | 題庫總覽首頁（含各範圍連結與使用說明） |
| `Q001-050.html` ~ `Q301-342.html` | 7 個範圍的題目頁面（50 題/頁，最後一頁 42 題） |
| `questions.json` | PDF 解析的中間資料（342 題英文原文 + 中文翻譯） |
| `parse_pdf.py` | PDF 解析腳本（PyMuPDF） |
| `parse_pdf.md` | PDF 解析腳本的 Mermaid 圖表 |
| `gen_html_v4.py` | HTML 產生腳本（Python） |
| `gen_html_v4.md` | HTML 產生腳本的 Mermaid 圖表 |
| `README.md` | 本說明文件 |

## 線上網址（GitHub Pages）

推到 `main` 後約 1 分鐘自動更新，手機、平板、電腦都能直接開：

| 版本 | 網址 |
|------|------|
| 完整版總覽（中英對照） | https://cuteman0725.github.io/aws-dea-c01-question-bank/ |
| 中文精簡版（作答練習） | https://cuteman0725.github.io/aws-dea-c01-question-bank/Short_ZH.html |
| 答案速讀版（只看正確答案） | https://cuteman0725.github.io/aws-dea-c01-question-bank/Answer_ZH.html |
| 架構圖版（點題號亮起服務與流向） | https://cuteman0725.github.io/aws-dea-c01-question-bank/Arch_ZH.html |

## 使用方式

### 本機瀏覽

1. 直接用瀏覽器開啟 `index.html` 即可使用
2. 或啟動本地伺服器：
   ```powershell
   cd D:\Project\00.Doc\AWS_DEA_C01
   python -m http.server 8899
   ```
   然後在瀏覽器開啟 `http://127.0.0.1:8899/index.html`

### 語言切換

頁面頂部有三個按鈕：
- **English**：只顯示英文題目和選項
- **中文**：只顯示中文題目和選項 + Notion 中文解析
- **中英對照**：同時顯示英文和中文
- **高亮**：切換關鍵字高亮（黃底粗體），預設為開啟
- **範圍下拉選單**：直接跳到其他題目範圍
- **放大鏡圖示**：點擊展開搜尋框，再點一次收合並還原

### 手機閱讀

- 將整個資料夾複製到手機，或透過本地伺服器存取
- 支援深色/淺色模式（依系統設定自動切換）
- 點選題目卡片可展開/收合詳細內容
- 搜尋框可依題號、關鍵字、服務名稱即時篩選

## 題目結構

每題包含以下欄位：

| 欄位 | 來源 | 說明 |
|------|------|------|
| 題號 | PDF + Notion | Q1 ~ Q342 |
| 英文題目 | PDF | 完整英文情境描述 |
| 中文題目 | PDF | 完整中文翻譯 |
| A/B/C/D 選項 | PDF | 英文 + 中文選項 |
| 正確答案 | PDF | 綠色標示 |
| 分層 | Notion | Network / Security / Data / Workload / Governance |
| Keywords | Notion | 相關 AWS 服務與技術名詞 |
| 一句考點 | Notion | 核心概念摘要 |
| 為什麼 | Notion | 正確答案的原因 |
| 超短流程圖 | Notion | 架構流程速覽 |
| 一行筆記 | Notion | 最短複習句 |

## 資料來源

- **PDF**：`aws-certified-data-engineer-associate-dea-c01_dual_Kimi+Qwen.pdf`（中英對照版，344 頁）
- **Notion**：Qman's Notion 工作區「DEA 刷題｜AI 解題紀錄」及其 7 個子頁面
- **取得方式**：PyMuPDF 解析 PDF + Notion MCP Server `notion-fetch` API

## 重新產生

```powershell
# 1. 解析 PDF（產生 questions.json）
python parse_pdf.py

# 2. 產生 HTML（讀取 questions.json + Notion overflow 檔案）
python gen_html_v4.py
```

## 相關文件

- [parse_pdf.md](parse_pdf.md) - PDF 解析腳本的 Mermaid 圖表
- [gen_html_v4.md](gen_html_v4.md) - HTML 產生腳本的 Mermaid 圖表
- [Request.md](../Request.md) - 需求記錄

## 中文精簡版（手機快速複習）

> 新增日期：2026-10-05

`Short_ZH.html`：342 題中文精簡版，題目 ≤100 字、每個選項在 360px 手機（16px 字）一行放得下（≤18 個中文字，英數算半格）。

- 點選項作答，複選題選滿題數後自動判定；答對綠、答錯紅，並顯示答案與一句考點
- 預設「依主題」排序：依 Notion 讀本的 14 章分組（章內依小節），卡片標小節編號；可切回「依題號」
- 篩選：各章主題、只看錯題／星號／複選／爭議題，或依題號範圍
- 作答狀態：「全部狀態／未作答／已作答」獨立切換，可和主題、題號範圍搭配（例如只看第 3 章還沒做的題目）；在「未作答」模式下答完的題目會留在畫面上看解答，切換篩選或重開網頁後才隱藏
- 「錯題・弱項」：最上方列出所有錯題題號（可複製；點題號直接開速讀版的那一題，或一次在速讀版只看這些錯題），下方是各章作答數與答對率（低→高），點一下只看該章
- 「接續」：記住上次作答的題目與排序、篩選；下次開啟自動捲到上次那題之後的第一個未作答題（「接續」按鈕可隨時跳回）。上次那題標「上次」，已作答的卡片左側有綠（對）／紅（錯）色條
- 作答結果與星號存在瀏覽器 localStorage；「全顯答案」快速瀏覽、「亂序」打散（依主題時在章內打散）、「重作」清除畫面上的作答
- 標「⚠ 爭議」的題目為 Notion 爭議題或社群多數票不同，答案列附說明，考前請特別確認

14 章主題：S3 儲存、資料匯入、串流、Catalog/Crawler、Glue ETL/資料品質、EMR/Spark、編排、Athena、Redshift、DynamoDB/RDS、QuickSight/OpenSearch、治理/IAM/加密、網路、監控/稽核。

| 檔案 | 說明 |
|------|------|
| `Short_ZH.html` | 中文精簡版（單一檔案，可直接傳到手機開啟） |
| `short_zh.json` | 精簡版資料（題目、選項、答案、考點） |
| `gen_short_zh.py` | 產生腳本：`prep` 切批次、`build` 檢查字數、比對 Notion 答案並產生 HTML |
| `notion_meta.json` | 從 Notion「AWS DEA C01」整理的章節名稱、每題章節、答案、爭議題與說明 |
| `gen_short_zh.md` | 產生腳本的 Mermaid 圖表 |
| `_work/` | 批次輸入（`in_*.json`）與改寫結果（`out_*.json`） |

```powershell
python gen_short_zh.py prep    # 修正答案、切批次到 _work/
python gen_short_zh.py build   # 合併 _work/out_*.json → short_zh.json、Short_ZH.html
```

## 答案速讀版（只看正確答案）

> 新增日期：2026-10-09

`Answer_ZH.html`：342 題全部直接顯示答案，不用作答，適合零碎時間快速複習。

- 每題只列題目與**正確答案**（綠框），不顯示其他選項
- 一小段說明（360px 手機 5 行內）：為什麼選這個答案
- 流程圖：2～5 格的架構／判斷路徑，橘框為關鍵；手機上放不下一行時自動改直式
- 依主題（14 章）或依題號排序、篩選章節／複選／爭議題／題號範圍、關鍵字搜尋
- 「看過，下一題 ↓」：每題底部一個按鈕，標記看過並自動捲到下一題；「接續」跳到上次標記那題之後第一個還沒看過的題目，開啟時也會自動跳過去。看過的卡片左側綠條、上次那題標「上次」，選單下緣有進度條
- 作答狀態：全部／未看過／已看過，可搭配主題；「清除看過紀錄…」可從頭再看一輪
- 記住排序與篩選；沒有標記過時，沿用上次捲到的位置
- 「只看練習版錯題」：直接讀取練習版的作答紀錄（同一台裝置、同一個瀏覽器）；也支援 `Answer_ZH.html#q17` 跳到單題、`Answer_ZH.html?q=4,17,23` 只看指定題號
- 爭議題標「⚠ 爭議」並附社群看法；說明與流程圖以 Notion 筆記為依據濃縮

| 檔案 | 說明 |
|------|------|
| `Answer_ZH.html` | 答案速讀版（單一檔案） |
| `answer_zh.json` | 速讀版資料（題目、正確答案、說明、流程圖） |
| `gen_answer_zh.py` | 產生腳本：`prep` 切批次、`check` 檢查單批、`build` 檢查長度並產生 HTML |
| `gen_answer_zh.md` | 產生腳本的 Mermaid 圖表 |
| `_work/ans_in_*.json`、`_work/ans_out_*.json` | 批次輸入（題目、答案、Notion 解析）與改寫結果（說明、流程圖） |

```powershell
python gen_answer_zh.py prep    # 從 short_zh.json、questions.json、Q*.html 切批次到 _work/
python gen_answer_zh.py build   # 合併 _work/ans_out_*.json → answer_zh.json、Answer_ZH.html
```

不需要 PDF；Notion 解析取自完整版 `Q*.html`。

## 架構圖版（點題號看資料流向）

> 新增日期：2026-10-09

`Arch_ZH.html`：一張 AWS 資料工程架構總圖（45 個服務節點），342 題都對應到圖上的路徑。

- 由左到右：來源 → 擷取・串流 → 儲存 → 目錄・治理・品質 → 處理 → 分析・資料庫 → 使用端；上方是編排・事件・通知，下方是安全・監控・網路
- 點題號：亮起該題用到的服務，橘色箭頭與編號是資料流向，橘底是答案重點，虛線框是相關服務（權限、加密、網路或並列來源）；自動縮放把整條路徑框進畫面
- 下方顯示題目、正確答案、說明（同速讀版）與路徑
- ◀ ▶ 逐題複習；可依主題、爭議題、練習版錯題，或某個服務篩選
- 點圖上的服務：看它和哪些服務最常一起考，題號列只留相關題目
- 底圖細線是至少 3 題共用的連線，越粗越常考
- 記住篩選與上次看的題目

| 檔案 | 說明 |
|------|------|
| `Arch_ZH.html` | 架構圖版（單一檔案） |
| `arch_zh.json` | 每題對應的節點路徑（path）、答案重點（key）、相關節點（also） |
| `gen_arch_zh.py` | 產生腳本：節點清單與版面、`prep` 切批次、`check` 檢查單批、`build` 產生 HTML |
| `gen_arch_zh.md` | 產生腳本的 Mermaid 圖表 |
| `_work/arch_in_*.json`、`_work/arch_out_*.json` | 批次輸入（取自 `answer_zh.json`）與對應結果 |

```powershell
python gen_answer_zh.py build   # 先產生 answer_zh.json（說明文字來源）
python gen_arch_zh.py prep      # 切批次到 _work/
python gen_arch_zh.py build     # 合併 _work/arch_out_*.json → arch_zh.json、Arch_ZH.html
```
