# 使用Node.js官方鏡像作為構建環境
FROM node:16-alpine as build

# 設置工作目錄
WORKDIR /app

# 複製依賴文件
COPY package.json package-lock.json ./

# 安裝依賴
RUN npm ci

# 複製源代碼
COPY . .

# 修改應用標題為"加班產生器2.0"
RUN sed -i 's/<title>React App<\/title>/<title>加班產生器2.0<\/title>/g' public/index.html

# 構建應用
RUN npm run build

# 使用nginx輕量級鏡像來託管前端應用
FROM nginx:stable-alpine

# 複製Nginx配置文件
COPY nginx.conf /etc/nginx/conf.d/default.conf

# 從構建階段複製構建產物
COPY --from=build /app/build /usr/share/nginx/html

# 暴露80端口
EXPOSE 80

# 啟動nginx服務
CMD ["nginx", "-g", "daemon off;"] 