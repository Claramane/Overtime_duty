# 加班時數報表產生器 API

此專案提供一個 API，用於從 Google Calendar 事件和手動記錄 (`duties.json`) 產生醫師加班時數的 Excel 報表。

## 專案結構

```
Overtime_duty/
├── .venv/                  # Python 虛擬環境
├── data/                   # 資料與設定檔
│   ├── holiday_2026.json   # 假日定義
│   ├── duties.json         # 手動排班記錄
│   ├── members.json        # 成員與日曆 ID
│   ├── VSduty_template.xlsx # Excel 模板
│   ├── service_account.json # Google Service Account 金鑰
│   └── output/             # 存放產生的 Excel 報表
├── src/                    # 原始碼
│   ├── __init__.py
│   ├── services/           # 服務模組 (假日、Excel)
│   │   ├── __init__.py
│   │   ├── holiday_service.py
│   │   └── excel_service.py
│   ├── core/               # 核心邏輯 (報表產生)
│   │   ├── __init__.py
│   │   └── report_generator.py
│   └── api/                # API 伺服器
│       ├── __init__.py
│       └── main.py           # FastAPI 應用程式
├── requirements.txt        # 專案依賴
└── README.md               # 本檔案
```

## 設定步驟

1.  **Clone 專案** (如果尚未完成)
2.  **建立虛擬環境**:
    ```bash
    python -m venv .venv
    source .venv/bin/activate  # macOS / Linux
    # .venv\Scripts\activate  # Windows
    ```
3.  **安裝依賴**:
    ```bash
    pip install -r requirements.txt
    ```
4.  **設定 Google Service Account**:
    *   確保你擁有一個 Google Cloud Platform 專案，並已啟用 Google Calendar API。
    *   建立一個服務帳號，並下載其 JSON 金鑰檔案。
    *   將下載的 JSON 金鑰檔案命名為 `service_account.json` 並放置在 `data/` 目錄下。
    *   **重要**: 與每個成員的 Google Calendar 共享行事曆讀取權限給這個服務帳號的電子郵件地址 (可在 `service_account.json` 中找到 `client_email`)。
5.  **準備資料檔案**:
    *   確保 `data/members.json` 包含正確的成員 ID、姓名、員工編號 (`employee_id`) 和 Google Calendar ID (`calendar_id`)。
    *   確保 `data/holiday_2026.json` 包含正確的假日資訊。
    *   確保 `data/duties.json` 包含手動排班記錄 (如果需要)。
    *   確保 `data/VSduty_template.xlsx` 是正確的 Excel 模板。

## 運行服務

### 後端 API 伺服器

在專案根目錄 (`Overtime_duty/`) 下執行以下命令：

```bash
cd backend
python run.py
```

或者直接使用 uvicorn：

```bash
cd backend
uvicorn src.api.main:app --host 0.0.0.0 --port 8088 --reload
```

*   `--host 0.0.0.0`: 讓伺服器可以從外部網路訪問 (如果需要)。如果只想在本機訪問，可以使用 `127.0.0.1`。
*   `--port 8088`: 指定監聽的埠號。
*   `--reload`: 開發模式下啟用自動重新載入。當程式碼變更時，伺服器會自動重啟。

### 前端開發伺服器

在另一個終端視窗中執行：

```bash
cd frontend
npm start
```

前端將在 `http://localhost:9527` 啟動。

## API 文檔

伺服器啟動後，你可以訪問：

*   **API 端點**: `http://localhost:8088/generate_report/{year_month}` (使用 POST 方法)
*   **自動文件 (Swagger UI)**: `http://localhost:8088/docs`
*   **備選文件 (ReDoc)**: `http://localhost:8088/redoc`

## 使用 API

你可以使用 `curl` 或任何 API 客戶端工具 (如 Postman, Insomnia) 向 `/generate_report/{year_month}` 端點發送 POST 請求。

**範例 (使用 curl):**

*   **產生 2025 年 4 月所有成員的報表:**
    ```bash
    curl -X POST "http://localhost:8088/generate_report/202504" -H "accept: application/json"
    ```
*   **只產生 2025 年 4 月成員 'A' 的報表:**
    ```bash
    curl -X POST "http://localhost:8088/generate_report/202504?member_id=A" -H "accept: application/json"
    ```

**回應範例 (成功):**

```json
{
  "message": "成功為 202504 (成員: 所有) 產生報表。",
  "generated_files": [
    {
      "path": "/Users/jasmac/Documents/Overtime_duty/data/output/202504_林怡芸.xlsx",
      "url": "/download/202504_林怡芸.xlsx"
    },
    {
      "path": "/Users/jasmac/Documents/Overtime_duty/data/output/202504_游雅盛.xlsx",
      "url": "/download/202504_游雅盛.xlsx"
    }
    // ... 其他成員 ...
  ]
}
```

**注意**: 回應中的 `url` 欄位 `/download/...` 目前僅為示例。若要實際提供下載功能，需要在 FastAPI 中額外設定靜態檔案路由來服務 `data/output/` 目錄下的檔案。

## 待辦事項 / 可能的改進

*   在 API 中實現實際的檔案下載功能 (例如，透過 `/download/{filename}` 端點)。
*   增加更詳細的錯誤處理和日誌記錄。
*   加入單元測試和整合測試。
*   考慮將設定 (如檔案路徑) 移到環境變數或設定檔中。
*   針對大量成員或長時間範圍的請求，考慮使用背景任務 (如 Celery) 來處理報表產生，避免 API 請求超時。 