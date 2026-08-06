# AWS DEA-C01 PDF 解析器 - Mermaid 圖表

> 產生日期：2026-08-06
> 解析中英對照 PDF，分離英文半頁與中文半頁後提取題目原文與選項

## 解析策略

PDF 每一頁的版面為「上半英文、下半中文」，兩半各自以頁尾標記結尾：

| 半頁 | 頁尾標記 |
|------|----------|
| 英文 | `Page N of 344` |
| 中文 | `Page N of 344` 或 `第N頁，共344頁` |

若直接把整份 PDF 串成一份文字解析，跨頁題目會出現「英文-中文-英文-中文」交錯，導致區塊切割錯亂。
因此先依頁尾標記把每頁拆成兩半，分別串接成 `en_doc` 與 `zh_doc`，再各自解析。

## 類別圖（Class Diagram）

```mermaid
classDiagram
    class PdfParser {
        +String pdfPath
        +String outputPath
        +String en_doc
        +String zh_doc
        +splitPageHalves() : void
        +clean() : String
        +findBlocks() : Dict
        +locateOptionStarts() : List
        +parseBlock() : Tuple
        +saveToJson() : void
    }

    class PageHalf {
        +Int pageNo
        +String lang
        +String text
    }

    class PdfQuestion {
        +Int number
        +String en_question
        +Dict en_options
        +String zh_question
        +Dict zh_options
        +String correct_answer
    }

    class PdfOption {
        +String letter
        +String text
        +Boolean isCorrect
    }

    PdfParser "1" --> "688" PageHalf : splits
    PdfParser "1" --> "342" PdfQuestion : produces
    PdfQuestion "1" --> "4" PdfOption : en_options
    PdfQuestion "1" --> "4" PdfOption : zh_options
```

## 循序圖（Sequence Diagram）

```mermaid
sequenceDiagram
    participant User as 使用者
    participant Parser as parse_pdf.py
    participant PDF as PDF 檔案
    participant FS as 檔案系統

    User->>Parser: 執行 parse_pdf.py
    Parser->>PDF: fitz.open() 開啟 PDF
    loop 每一頁 (344 頁)
        Parser->>PDF: get_text()
        Parser->>Parser: 移除控制字元
        Parser->>Parser: 找 Page N of / 第N頁 標記
        Parser->>Parser: 切成英文半頁 + 中文半頁
    end
    Parser->>Parser: 串接成 en_doc / zh_doc
    Parser->>Parser: 移除頁尾、頁碼、廣告列

    par 英文解析
        Parser->>Parser: regex 找 Question #N
        Parser->>Parser: 過濾目錄項目
        Parser->>Parser: 依序定位 A) B) C) D)
        Parser->>Parser: 標記 (Correct Answer)
    and 中文解析
        Parser->>Parser: regex 找 問題#N
        Parser->>Parser: 過濾目錄項目
        Parser->>Parser: 依序定位 A) B) C) D)
        Parser->>Parser: 標記（正確答案）
    end

    Parser->>Parser: 依題號合併中英資料
    Parser->>Parser: 品質檢查（語言錯置、選項數、殘留標記）
    Parser->>FS: 儲存 questions.json
    FS-->>User: 342 題完整資料
```

## 流程圖（Flowchart）

```mermaid
flowchart TD
    A[開始] --> B[PyMuPDF 逐頁讀取]
    B --> C{頁尾標記數量}
    C -- ">= 2" --> D[前段=英文 中段=中文]
    C -- "= 1" --> E[前段=英文 後段=中文]
    C -- "= 0" --> F[整頁視為英文]
    D --> G[串接 en_doc / zh_doc]
    E --> G
    F --> G
    G --> H[清理頁尾/頁碼/廣告]
    H --> I[英文: 找 Question #N]
    H --> J[中文: 找 問題#N]
    I --> K{是目錄項目?}
    J --> K
    K -- 是 --> L[略過]
    K -- 否 --> M[切出題目區塊]
    M --> N[以 Explanation / 說明 切出題幹區]
    N --> O[依序定位 A→B→C→D→E]
    O --> P[抽出選項文字]
    P --> Q[偵測答案標記]
    Q --> R[以 Correct Answer: X 覆寫]
    R --> S[依題號合併中英]
    S --> T[品質檢查]
    T --> U[輸出 questions.json]
    U --> V[完成：342 題]
```

## UseCase 圖

```mermaid
graph LR
    Dev((開發者))

    UC1[分離中英半頁]
    UC2[提取題目原文]
    UC3[提取 A/B/C/D 選項]
    UC4[標記正確答案]
    UC5[品質檢查]
    UC6[輸出 JSON]

    Dev --> UC1
    Dev --> UC2
    Dev --> UC3
    Dev --> UC4
    Dev --> UC5
    Dev --> UC6

    UC1 --> Parser[parse_pdf.py]
    UC2 --> Parser
    UC3 --> Parser
    UC4 --> Parser
    UC5 --> Parser
    UC6 --> Parser
```

## 資料結構 ER Model

```mermaid
erDiagram
    QUESTION ||--|{ EN_OPTION : has
    QUESTION ||--|{ ZH_OPTION : has
    QUESTION {
        int number PK
        string en_question
        string zh_question
        string correct_answer
    }
    EN_OPTION {
        int question_number FK
        string letter PK
        string text
        boolean is_correct
    }
    ZH_OPTION {
        int question_number FK
        string letter PK
        string text
        boolean is_correct
    }
```

## 解析結果

| 檢查項目 | 結果 |
|----------|------|
| 總題數 | 342 |
| 英文題目 | 342 |
| 中文題目 | 342 |
| 正確答案 | 342 |
| 英文題目誤含中文 | 0 |
| 中文題目誤含英文 | 0 |
| 英文選項誤含中文 | 0 |
| 選項數不足 4 個 | 0 |
| 殘留答案標記 | 0 |
| 選項為空 | 1（Q323，PDF 中選項為 SQL 圖片） |