# 加班時數管理系統

這是一個用於管理和計算醫師加班時數的系統，包括前後端應用。

## 系統架構

- **前端**：React應用，提供用戶界面
- **後端**：FastAPI應用，提供API服務

## 快速開始

### 使用Docker部署

1. 複製環境變量文件並按需修改
   ```
   cp backend/.env.example backend/.env
   ```

2. 使用docker-compose啟動服務
   ```
   docker-compose up -d
   ```

3. 訪問應用
   - 前端界面：http://localhost:9527
   - 後端API：http://localhost/api

### 本地開發

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
- `backend/data/holiday_2025.json`：假日數據

## API文檔

啟動後端服務後，訪問 http://localhost:5000/docs 獲取API文檔。

## 功能特點

- 加班記錄管理：添加、查看和刪除加班記錄
- 假日日曆管理：設置和管理假日和特殊工作日
- 報表生成：按月份生成加班報表並下載

## 技術棧

- 前端：React, TypeScript, Material UI
- 後端：Python, FastAPI
- 容器化：Docker, Docker Compose

## 在樹莓派上部署

### 前置條件

- 樹莓派4B或更高版本（建議至少2GB RAM）
- 樹莓派OS (64位) 或其他Linux發行版
- 已安裝Docker和Docker Compose

### 部署步驟

1. 克隆專案到樹莓派

```bash
git clone https://github.com/yourusername/overtime-duty.git
cd overtime-duty
```

2. 使用Docker Compose啟動應用

```bash
docker-compose up -d
```

這將啟動前端和後端服務。前端在9527端口可訪問，後端API在8088端口。

3. 訪問應用

在瀏覽器中訪問 `http://your-raspberry-pi-ip:9527`

### 配置說明

- 所有後端數據存儲在 `backend/data` 目錄中，並通過卷映射到容器內
- 可以通過修改 `docker-compose.yml` 更改端口和資源限制

## 維護

### 更新應用

```bash
# 拉取最新代碼
git pull

# 重建並重啟容器
docker-compose down
docker-compose build
docker-compose up -d
```

### 查看日誌

```bash
# 查看所有容器日誌
docker-compose logs

# 查看特定服務日誌
docker-compose logs backend
docker-compose logs frontend

# 持續查看日誌
docker-compose logs -f
```

### 備份數據

```bash
# 備份數據目錄
cp -r backend/data /backup/overtime-duty-data-$(date +%Y%m%d)
```

## 針對樹莓派的優化說明

1. 資源限制：Docker Compose配置中限制了CPU和內存使用，防止系統資源過度使用
2. 持久化存儲：所有數據通過卷映射保存在宿主機上，確保容器重啟後數據不丟失
3. 服務自動重啟：配置了服務自動重啟，提高系統穩定性

## 故障排除

**問題1: 網站無法訪問**  
檢查Docker容器是否正常運行：`docker-compose ps`

**問題2: 後端API連接失敗**  
檢查後端日誌：`docker-compose logs backend`

**問題3: 樹莓派性能問題**  
調整`docker-compose.yml`中的資源限制，降低CPU和內存限制