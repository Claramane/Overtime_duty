#!/bin/bash

# 加班單產生器2.0啟動腳本
echo "正在啟動加班單產生器2.0..."

# 檢查Python是否安裝
if ! command -v python3 &> /dev/null; then
    echo "錯誤: Python3未安裝。請先安裝Python3。"
    exit 1
fi

# 檢查Node.js是否安裝
if ! command -v node &> /dev/null; then
    echo "錯誤: Node.js未安裝。請先安裝Node.js。"
    exit 1
fi

# 檢查npm是否安裝
if ! command -v npm &> /dev/null; then
    echo "錯誤: npm未安裝。請先安裝npm。"
    exit 1
fi

# 確保腳本在項目根目錄運行
if [ ! -f "package.json" ]; then
    echo "錯誤: 未找到package.json文件，請確保在項目根目錄運行此腳本。"
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
    if [ -f "backend/.env.example" ]; then
        cp backend/.env.example backend/.env
    else
        echo "錯誤: .env.example文件不存在。"
        exit 1
    fi
fi

# 啟動後端服務
echo "啟動後端服務..."
cd backend
python3 -m pip install -r requirements.txt
cd ..
echo "後端依賴安裝完成"

# 啟動前端服務
echo "啟動前端服務..."
cd frontend
npm install
cd ..
echo "前端依賴安裝完成"

# 啟動前後端服務
echo "正在啟動服務..."

# 獲取本地IP地址（兼容MacOS和Linux）
if [[ "$OSTYPE" == "darwin"* ]]; then
    # MacOS
    IP_ADDRESS=$(ipconfig getifaddr en0 2>/dev/null || ipconfig getifaddr en1 2>/dev/null || echo "localhost")
else
    # Linux和其他系統
    IP_ADDRESS=$(hostname -I | awk '{print $1}' || echo "localhost")
fi

# 在新的終端窗口中啟動後端
echo "啟動後端服務..."
cd backend
osascript -e 'tell app "Terminal" to do script "cd '$(pwd)' && python3 -m uvicorn src.api.main:app --reload --host 0.0.0.0 --port 5000"' || {
    echo "無法使用osascript啟動新終端，嘗試使用後台方式啟動..."
    python3 -m uvicorn src.api.main:app --reload --host 0.0.0.0 --port 5000 &
}
cd ..

# 在新的終端窗口中啟動前端
echo "啟動前端服務..."
cd frontend
osascript -e 'tell app "Terminal" to do script "cd '$(pwd)' && npm start"' || {
    echo "無法使用osascript啟動新終端，嘗試使用後台方式啟動..."
    npm start &
}
cd ..

echo "======================================"
echo "加班單產生器2.0已成功啟動！"
echo "前端地址: http://$IP_ADDRESS:3000"
echo "後端API地址: http://$IP_ADDRESS:5000"
echo "API文檔: http://$IP_ADDRESS:5000/docs"
echo "======================================" 