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