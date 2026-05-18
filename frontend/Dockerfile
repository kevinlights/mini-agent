# Mini-Agent Frontend Dockerfile
# Mini-Agent 前端 Dockerfile

# Build stage
# 构建阶段
FROM docker.m.daocloud.io/node:20-alpine AS builder

# Set working directory
# 设置工作目录
WORKDIR /app

# Configure npm to use Taobao mirror
# 配置 npm 使用淘宝镜像
RUN npm config set registry https://registry.npmmirror.com

# Copy package files
# 复制包文件
COPY package.json package-lock.json* ./

# Install dependencies
# 安装依赖
RUN npm ci

# Copy source code
# 复制源代码
COPY . .

# Build production bundle
# 构建生产包
RUN npm run build

# Production stage
# 生产阶段
FROM docker.m.daocloud.io/nginx:alpine

# Copy built files to nginx
# 将构建文件复制到 nginx
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy nginx configuration
# 复制 nginx 配置
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expose port
# 暴露端口
EXPOSE 80

# Health check
# 健康检查
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD wget -qO- http://localhost/ || exit 1

# Start nginx
# 启动 nginx
CMD ["nginx", "-g", "daemon off;"]
