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
- **Notion 解析**：一句考點、為什麼、超短流程圖、一行筆記
- **展開/收合全部**：一鍵展開或收合所有題目卡片
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
