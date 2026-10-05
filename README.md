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
- 篩選：各章主題、只看未作答／錯題／星號／複選／爭議題，或依題號範圍
- 「弱項」：各章作答數與答對率（低→高），點一下只看該章
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
