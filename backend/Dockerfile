# 使用Python官方鏡像作為基礎鏡像
FROM python:3.9-slim

# 設置工作目錄
WORKDIR /app

# 複製依賴文件
COPY requirements.txt ./

# 安裝依賴
RUN pip install --no-cache-dir -r requirements.txt

# 複製源代碼
COPY . .

# 設置環境變量
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# 暴露端口
EXPOSE 5000

# 啟動應用
CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "5000"] 