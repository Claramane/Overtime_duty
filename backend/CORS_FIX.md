# CORS 設定修正指南

## 問題描述
前端網域 `https://eckanesovertime.claramane.com` 無法訪問後端 API `https://eckanesovertimebackend.claramane.com`，因為 CORS 政策阻擋了跨域請求。

## 解決方案

### 1. 程式碼已更新
- ✅ 已在 `src/api/main.py` 中添加生產環境網域到預設 CORS 設定
- ✅ 已更新 `.env.example` 檔案，添加 CORS 設定範例

### 2. Zeabur 環境變數設定（重要！）

請在 Zeabur 後端服務的環境變數中添加：

```
BACKEND_CORS_ORIGINS=https://eckanesovertime.claramane.com,http://localhost:9527,http://127.0.0.1:9527
```

#### 設定步驟：
1. 登入 Zeabur 控制台
2. 選擇你的後端服務（eckanesovertimebackend）
3. 進入「環境變數」(Environment Variables) 設定
4. 添加新的環境變數：
   - **變數名稱**: `BACKEND_CORS_ORIGINS`
   - **變數值**: `https://eckanesovertime.claramane.com,http://localhost:9527,http://127.0.0.1:9527`
5. 儲存並重新部署服務

### 3. 驗證修正

設定完成後，請執行以下步驟驗證：

1. **重新部署後端服務**
   - 在 Zeabur 控制台觸發重新部署
   - 或推送新的 commit 到 GitHub 觸發自動部署

2. **檢查日誌**
   - 查看後端服務啟動日誌
   - 應該會看到：`CORS 允許的來源: ['https://eckanesovertime.claramane.com', ...]`

3. **測試前端請求**
   - 打開前端網站 `https://eckanesovertime.claramane.com`
   - 開啟瀏覽器開發者工具 (F12)
   - 重新載入頁面
   - 檢查 Network 標籤，確認 API 請求成功

### 4. 其他可能需要的 CORS 網域

如果你有其他前端網域，請一併添加到環境變數中，用逗號分隔：

```
BACKEND_CORS_ORIGINS=https://eckanesovertime.claramane.com,https://www.eckanesovertime.claramane.com,http://localhost:9527
```

## 技術說明

### 什麼是 CORS？
CORS (Cross-Origin Resource Sharing) 是瀏覽器的安全機制，防止網頁從不同來源載入資源。

### 為什麼需要設定？
- 前端網域：`https://eckanesovertime.claramane.com`
- 後端網域：`https://eckanesovertimebackend.claramane.com`
- 這兩個是不同的來源，需要後端明確允許前端訪問

### 程式碼變更說明
在 `src/api/main.py` 中：
```python
# 添加了生產環境網域到預設值
BACKEND_CORS_ORIGINS = os.getenv(
    "BACKEND_CORS_ORIGINS",
    "http://localhost:9527,http://127.0.0.1:9527,http://127.0.0.1:3000,https://eckanesovertime.claramane.com"
)
```

這樣即使沒有設定環境變數，也會包含生產環境網域。

## 常見問題

### Q: 設定後還是出現 CORS 錯誤？
A: 
1. 確認已重新部署後端服務
2. 清除瀏覽器快取並重新載入
3. 檢查環境變數是否正確設定（沒有多餘的空格）
4. 確認網域拼寫正確（包括 https/http）

### Q: 本地開發時如何設定？
A: 
1. 在 `backend/` 目錄下創建 `.env` 檔案
2. 複製 `.env.example` 的內容
3. 根據需要調整 `BACKEND_CORS_ORIGINS`

### Q: 如何允許所有來源（不建議用於生產環境）？
A: 
```python
allow_origins=["*"]  # 允許所有來源，僅用於開發測試
```

## 提交變更到 GitHub

執行以下命令提交變更：

```bash
git add backend/src/api/main.py backend/.env.example
git commit -m "修正 CORS 設定，添加生產環境網域支援"
git push origin master
```

推送後，Zeabur 會自動重新部署（如果有設定自動部署）。
