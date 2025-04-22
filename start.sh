#!/bin/bash

# 加班單產生器2.0啟動腳本
echo "正在啟動加班單產生器2.0..."

# 檢查Docker是否安裝
if ! command -v docker &> /dev/null; then
    echo "錯誤: Docker未安裝。請先安裝Docker Desktop。"
    echo "訪問 https://www.docker.com/products/docker-desktop/ 下載安裝"
    exit 1
fi

# 檢查Docker是否正在運行
if ! docker info &> /dev/null; then
    echo "錯誤: Docker守護進程未運行。"
    echo "在MacOS上，請確保您已啟動Docker Desktop應用程序。"
    echo "請打開Docker Desktop應用，等待狀態變為'運行中'後再次運行此腳本。"
    exit 1
fi

# 檢查 Docker Compose 支援：優先使用 docker-compose，否則嘗試 docker compose
if command -v docker-compose &> /dev/null; then
    DC_CMD="docker-compose"
elif docker compose version &> /dev/null; then
    DC_CMD="docker compose"
else
    echo "錯誤: Docker Compose 未安裝。請先安裝 docker-compose 或 Docker Compose plugin。"
    exit 1
fi

# 確保腳本在項目根目錄運行
if [ ! -f "docker-compose.yml" ]; then
    echo "錯誤: 未找到docker-compose.yml文件，請確保在項目根目錄運行此腳本。"
    exit 1
fi

# 檢查後端數據目錄是否存在
if [ ! -d "backend/data" ]; then
    echo "創建後端數據目錄..."
    mkdir -p backend/data/output
fi

# 檢查後端環境變量文件是否存在
if [ ! -f "backend/.env" ]; then
    echo "環境變量文件 .env 不存在，正在從 .env.example 複製..."
    cp backend/.env.example backend/.env
fi

# 啟動項目
echo "部署容器..."
$DC_CMD down
$DC_CMD up -d

# 檢查服務是否成功啟動
if [ $? -eq 0 ]; then
    echo "服務啟動成功！"
    
    # 獲取本地IP地址（兼容MacOS和Linux）
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # MacOS
        IP_ADDRESS=$(ipconfig getifaddr en0 2>/dev/null || ipconfig getifaddr en1 2>/dev/null || echo "localhost")
    else
        # Linux和其他系統
        IP_ADDRESS=$(hostname -I | awk '{print $1}' || echo "localhost")
    fi
    
    echo "======================================"
    echo "加班單產生器2.0已成功啟動！"
    echo "前端地址: http://$IP_ADDRESS:9527"
    echo "後端API地址: http://$IP_ADDRESS:5000"
    echo "API文檔: http://$IP_ADDRESS:5000/docs"
    echo "======================================"
else
    echo "服務啟動失敗，請檢查日誌以獲取更多信息。"
    $DC_CMD logs
fi 