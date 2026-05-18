# Mini-Agent Backend Dockerfile
# Mini-Agent 后端 Dockerfile

# Use Python 3.13 slim image with Tsinghua mirror
# 使用 Python 3.13 slim 镜像，配置清华镜像源
FROM docker.m.daocloud.io/python:3.13-slim

# Set working directory
# 设置工作目录
WORKDIR /app

# Configure pip to use Tsinghua mirror
# 配置 pip 使用清华镜像源
RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple && \
    pip config set global.trusted-host pypi.tuna.tsinghua.edu.cn

# Copy requirements first for better caching
# 先复制 requirements 以利用缓存
COPY requirements.txt .

# Install dependencies
# 安装依赖
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
# 复制应用代码
COPY app/ ./app/

# Create data directory for memories
# 创建记忆数据目录
RUN mkdir -p /app/data

# Expose port
# 暴露端口
EXPOSE 8000

# Health check
# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8000/api/v1/health').raise_for_status()"

# Run application
# 运行应用
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
