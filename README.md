# 加班時數管理系統

這是一個用於管理和計算醫師加班時數的系統，包括前後端應用。

## 系統架構

- **前端**：React應用，提供用戶界面
- **後端**：FastAPI應用，提供API服務

## 快速開始

### 使用啟動腳本

1. 複製環境變量文件並按需修改
   ```
   cp backend/.env.example backend/.env
   ```

2. 使用啟動腳本啟動服務
   ```
   ./start.sh
   ```

3. 訪問應用
   - 前端界面：http://localhost:3000
   - 後端API：http://localhost:5000
   - API文檔：http://localhost:5000/docs

### 手動啟動開發環境

#### 後端

1. 進入後端目錄
   ```
   cd backend
   ```

2. 安裝依賴
   ```
   pip install -r requirements.txt
   ```

3. 運行開發服務器
   ```
   uvicorn src.api.main:app --reload
   ```

#### 前端

1. 進入前端目錄
   ```
   cd frontend
   ```

2. 安裝依賴
   ```
   npm install
   ```

3. 運行開發服務器
   ```
   npm start
   ```

## 數據文件

- `backend/data/duties.json`：加班記錄數據
- `backend/data/holiday_2026.json`：假日數據

## API文檔

啟動後端服務後，訪問 http://localhost:5000/docs 獲取API文檔。

## 功能特點

- 加班記錄管理：添加、查看和刪除加班記錄
- 假日日曆管理：設置和管理假日和特殊工作日
- 報表生成：按月份生成加班報表並下載

## 技術棧

- 前端：React, TypeScript, Material UI
- 後端：Python, FastAPI

## 維護

### 更新應用

```bash
# 拉取最新代碼
git pull

# 安裝後端依賴
cd backend
pip install -r requirements.txt
cd ..

# 安裝前端依賴
cd frontend
npm install
cd ..

# 啟動應用
./start.sh
```

### 備份數據

```bash
# 備份數據目錄
cp -r backend/data /backup/overtime-duty-data-$(date +%Y%m%d)
```

## 故障排除

**問題1: 網站無法訪問**  
檢查前端服務是否正常運行

**問題2: 後端API連接失敗**  
檢查後端服務是否正常運行