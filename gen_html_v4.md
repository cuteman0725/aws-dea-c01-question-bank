# AWS DEA-C01 HTML 產生器 v4 - Mermaid 圖表

> 產生日期：2026-08-06
> 結合 PDF 英文原文 + Notion 中文解析，產生含中英切換的 HTML

## 類別圖（Class Diagram）

```mermaid
classDiagram
    class PdfQuestion {
        +Int number
        +String en_question
        +Dict en_options
        +String zh_question
        +Dict zh_options
        +String correct_answer
    }

    class NotionQuestion {
        +Int number
        +String title
        +String layer
        +String answer
        +String keywords
        +String keypoint
        +String why
        +String flow
        +String note
        +Dict other_reasons
    }

    class Option {
        +String letter
        +String text
        +String zh_text
        +String reason
        +Boolean isCorrect
    }

    class HtmlGenerator {
        +String targetDir
        +String css
        +String js
        +loadPdfQuestions() : List
        +loadNotionContent() : Dict
        +buildCard() : String
        +buildOptionHtml() : String
        +main() : void
    }

    class HtmlOutput {
        +String fileName
        +Int questionCount
        +Int fileSizeKB
    }

    PdfQuestion "1" --> "4" Option : has
    NotionQuestion "1" --> "4" Option : reasons
    HtmlGenerator "1" --> "342" PdfQuestion : reads
    HtmlGenerator "1" --> "342" NotionQuestion : reads
    HtmlGenerator "1" --> "8" HtmlOutput : produces
```

## 循序圖（Sequence Diagram）

```mermaid
sequenceDiagram
    participant User as 使用者
    participant Script as gen_html_v4.py
    participant PDF as PDF 檔案
    participant Notion as Notion MCP
    participant FS as 檔案系統
    participant Browser as 瀏覽器

    User->>Script: 執行 gen_html_v4.py
    Script->>PDF: PyMuPDF 解析 PDF
    PDF-->>Script: questions.json (342 題英文+中文)
    Script->>Notion: notion-fetch 7 個範圍頁面
    Notion-->>FS: overflow content.txt
    Script->>FS: 讀取 overflow 檔案
    FS-->>Script: Notion Markdown 內容
    
    loop 每個範圍 (7 個)
        Script->>Script: 合併 PDF + Notion 資料
        loop 每個題目 (50 題)
            Script->>Script: buildCard()
            Script->>Script: 組裝英文題目+選項
            Script->>Script: 組裝中文翻譯+選項
            Script->>Script: 加入 Notion 解析
            Script->>Script: 加上 lang-en/lang-zh CSS class
        end
        Script->>FS: 寫入 HTML 檔案
    end
    
    Script->>FS: 寫入 index.html
    User->>Browser: 開啟 HTML
    Browser-->>User: 顯示中英切換題庫
```

## 流程圖（Flowchart）

```mermaid
flowchart TD
    A[開始] --> B[載入 questions.json]
    B --> C[載入 7 個 Notion overflow 檔案]
    C --> D[解析 Notion Markdown]
    D --> E[合併 PDF + Notion 資料]
    E --> F{每個範圍 7 個}
    F --> G[取得該範圍題目]
    G --> H{每個題目}
    H --> I[組裝英文題目情境]
    H --> J[組裝中文題目情境]
    H --> K[組裝 A/B/C/D 選項]
    K --> K1[英文選項 + 中文翻譯]
    K --> K2[Notion 不選原因]
    K --> K3[標記正確/錯誤]
    I --> L[組裝 card HTML]
    J --> L
    K1 --> L
    K2 --> L
    K3 --> L
    L --> L1[加入 lang-en/lang-zh class]
    L1 --> M{還有題目?}
    M -- 是 --> H
    M -- 否 --> N[組裝範圍 HTML]
    N --> O[寫入 HTML 檔案]
    O --> P{還有範圍?}
    P -- 是 --> F
    P -- 否 --> Q[產生 index.html]
    Q --> R[完成：342 題]
```

## UseCase 圖

```mermaid
graph LR
    User((使用者))
    
    UC1[瀏覽題庫總覽]
    UC2[依範圍瀏覽題目]
    UC3[搜尋題目]
    UC4[展開/收合題目]
    UC5[切換英文/中文/對照]
    UC6[展開/收合全部]
    
    User --> UC1
    User --> UC2
    User --> UC3
    User --> UC4
    User --> UC5
    User --> UC6
    
    UC1 --> System[HTML 題庫系統 v4]
    UC2 --> System
    UC3 --> System
    UC4 --> System
    UC5 --> System
    UC6 --> System
```

## 資料結構 ER Model

```mermaid
erDiagram
    PDF_QUESTION ||--o{ OPTION : has_en_options
    PDF_QUESTION ||--o{ ZH_OPTION : has_zh_options
    NOTION_QUESTION ||--|| PDF_QUESTION : matched_by_number
    NOTION_QUESTION ||--o{ OTHER_REASON : has_reasons
    
    PDF_QUESTION {
        int number PK
        string en_question
        string zh_question
        string correct_answer
    }
    
    OPTION {
        int question_number FK
        string letter
        string text
        boolean is_correct
    }
    
    ZH_OPTION {
        int question_number FK
        string letter
        string text
        boolean is_correct
    }
    
    NOTION_QUESTION {
        int number PK
        string title
        string layer
        string keypoint
        string why
        string flow
        string note
    }
    
    OTHER_REASON {
        int question_number FK
        string letter
        string reason
    }
```

## 語言切換機制

`body` 的 class 決定顯示哪一種語言，內容元素則掛 `lang-en` / `lang-zh`。

> **重要**：body 的 class 必須用 `mode-*` 前綴，不能與內容的 `lang-*` 同名。
> 若 body 也叫 `lang-en`，`.lang-en{display:none}` 會直接把整個 body 隱藏，造成全白畫面。

```mermaid
stateDiagram-v2
    [*] --> both : 預設 / localStorage
    both --> en : 點 English
    both --> zh : 點 中文
    en --> zh : 點 中文
    en --> both : 點 中英對照
    zh --> en : 點 English
    zh --> both : 點 中英對照

    state both {
        [*] --> 顯示英文與中文
    }
    state en {
        [*] --> 只顯示英文
    }
    state zh {
        [*] --> 只顯示中文與Notion解析
    }
```

| body class | 顯示的內容 |
|------------|-----------|
| `mode-en` | `.lang-en`（英文題目、英文選項） |
| `mode-zh` | `.lang-zh`（中文題目、中文選項、不選原因、Notion 解析） |
| `mode-both` | 兩者皆顯示，中文以虛線分隔並淡化 |

對應 CSS：

```css
.lang-en,.lang-zh{display:none}
body.mode-en .lang-en{display:block}
body.mode-zh .lang-zh{display:block}
body.mode-both .lang-en,body.mode-both .lang-zh{display:block}
```

語言偏好以 `localStorage.dea-lang` 記憶，下次開啟自動套用。

## 關鍵字高亮機制（v4.1 新增）

題目展開後，最下方的 Keywords 標籤列中的關鍵字，會在題目情境和選項中被加粗 + 高亮。

### 運作流程

```mermaid
flowchart TD
    A[取得 Notion Keywords 列表] --> B[按長度降序排列]
    B --> C[逐個關鍵字處理]
    C --> D[用 placeholder 標記文字中的關鍵字]
    D --> E[跳過已標記區域避免巢狀]
    E --> F[esc_html 轉換]
    F --> G[Markdown 轉換]
    G --> H[placeholder 換成 mark tag]
    H --> I[輸出含 kw-hl class 的 HTML]
    C --> J{還有關鍵字?}
    J -- 是 --> C
    J -- 否 --> I
```

### CSS 切換

```mermaid
stateDiagram-v2
    [*] --> hl_on : 預設 / localStorage = on
    hl_on --> hl_off : 點 Highlight 按鈕
    hl_off --> hl_on : 再點 Highlight 按鈕

    state hl_on {
        [*] --> 黃底黑字粗體
    }
    state hl_off {
        [*] --> 繼承父層樣式
    }
```

| body class | 高亮樣式 |
|------------|---------|
| （無 kw-off） | 黃底 `#fff59d`、黑字、粗體 600 |
| `kw-off` | 背景透明、文字正常、非粗體 |

### 關鍵字處理邏輯

| 步驟 | 說明 |
|------|------|
| 1. 過濾 | 只保留長度 ≥ 3 的關鍵字 |
| 2. 排序 | 按長度降序，避免短關鍵字破壞長關鍵字 |
| 3. 分段 | 用 regex 把已標記區域 `\x00...\x01` 分開 |
| 4. 替換 | 只在未標記段中做 case-insensitive 替換 |
| 5. 轉換 | esc_html → Markdown → placeholder 換成 `<mark>` |

## 手機版 topbar 瘦身（v4.2 新增）

原本 topbar 在 360×740 手機上佔 279px（38% 螢幕），加上瀏覽器網址列後幾乎佔掉一半。

### 優化前後對照

| 區塊 | 優化前 | 優化後 |
|------|--------|--------|
| 標題 h1 | 29px（18px 字） | 29px（15px 字，與下拉選單同排） |
| 搜尋框 | 39px 常駐 | 0px（改放大鏡圖示，點擊才展開） |
| 按鈕列 | 68px（2 排，英文長標籤） | 29px（1 排，EN/中/雙語/展開/收合/高亮） |
| 範圍導航 | 98px（8 個連結排 3 排） | 0px（改 `<select>` 下拉，併入標題排） |
| padding | 45px | 19px |
| **合計** | **279px（38%）** | **77px（10%）** |
| **可視區** | 461px | **663px（+44%）** |

再加上捲動自動隱藏，往下看題目時 topbar 完全消失，可視區達 100%。

### 版面結構

```mermaid
graph TD
    TB[topbar #tb]
    TB --> R1[".tbr 第一排 29px"]
    TB --> S[".search 隱藏 0px"]
    TB --> R2[".controls 第二排 29px"]

    R1 --> H1["h1 標題<br/>flex:1 + ellipsis"]
    R1 --> SEL["select.rsel<br/>範圍下拉"]
    R1 --> BTN["button.ib-search<br/>放大鏡"]

    S --> INP["input.search<br/>.on 時才 display:block"]

    R2 --> L["EN / 中 / 雙語"]
    R2 --> SP["spacer flex:1"]
    R2 --> E["展開 / 收合 / 高亮"]
```

### 捲動自動隱藏狀態機

```mermaid
stateDiagram-v2
    [*] --> 顯示
    顯示 --> 隱藏 : scrollY > 140 且往下捲 > 4px
    隱藏 --> 顯示 : 往上捲 > 4px
    隱藏 --> 顯示 : scrollY <= 140

    state 顯示 {
        [*] --> transform_none
    }
    state 隱藏 {
        [*] --> translateY_minus100
    }
```

實作重點：

| 項目 | 說明 |
|------|------|
| 觸發門檻 | `scrollY > 140` 才開始隱藏，避免頂端抖動 |
| 遲滯 | 位移需 > 4px 才動作，避免慣性捲動時閃爍 |
| 動畫 | `transform:translateY(-100%)` + `transition .25s`，用 GPU 合成不觸發 reflow |
| 效能 | `addEventListener(..., {passive:true})` 不阻塞捲動 |

### 搜尋框展開/收合

```mermaid
sequenceDiagram
    participant U as 使用者
    participant B as 放大鏡按鈕
    participant S as .search
    participant F as filt()

    U->>B: 點擊
    B->>S: classList.toggle("on")
    alt 展開
        S->>S: display:block
        S->>S: focus()
    else 收合
        S->>S: display:none
        S->>S: value = ""
        S->>F: filt("") 還原全部題目
    end
```

收合時會清空搜尋字並呼叫 `filt("")`，避免題目還被篩選卻看不到搜尋框。