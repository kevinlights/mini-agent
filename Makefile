# Mini-Agent Makefile
# Mini-Agent 项目的 Makefile

.PHONY: help install dev test lint clean build docker run stop

# Default target
# 默认目标
help:
	@echo "Mini-Agent - Available Commands"
	@echo "Mini-Agent - 可用命令"
	@echo ""
	@echo "  make install    - Install Python dependencies"
	@echo "  make install    - 安装 Python 依赖"
	@echo ""
	@echo "  make dev        - Start development server"
	@echo "  make dev        - 启动开发服务器"
	@echo ""
	@echo "  make test       - Run tests"
	@echo "  make test       - 运行测试"
	@echo ""
	@echo "  make test-cov   - Run tests with coverage"
	@echo "  make test-cov   - 运行测试并生成覆盖率报告"
	@echo ""
	@echo "  make lint       - Run linter"
	@echo "  make lint       - 运行代码检查"
	@echo ""
	@echo "  make format     - Format code"
	@echo "  make format     - 格式化代码"
	@echo ""
	@echo "  make clean      - Clean up"
	@echo "  make clean      - 清理"
	@echo ""
	@echo "  make build      - Build Docker image"
	@echo "  make build      - 构建 Docker 镜像"
	@echo ""
	@echo "  make run        - Run Docker container"
	@echo "  make run        - 运行 Docker 容器"
	@echo ""
	@echo "  make stop       - Stop Docker container"
	@echo "  make stop       - 停止 Docker 容器"


# Install dependencies
# 安装依赖
install:
	@echo "Installing Python dependencies..."
	@echo "正在安装 Python 依赖..."
	pip install -r backend/requirements.txt
	@echo "Dependencies installed."
	@echo "依赖安装完成。"


# Start development server
# 启动开发服务器
dev:
	@echo "Starting development server..."
	@echo "正在启动开发服务器..."
	cd backend && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload


# Run tests
# 运行测试
test:
	@echo "Running tests..."
	@echo "正在运行测试..."
	cd backend && pytest tests/ -v


# Run tests with coverage
# 运行测试并生成覆盖率报告
test-cov:
	@echo "Running tests with coverage..."
	@echo "正在运行测试并生成覆盖率报告..."
	cd backend && pytest tests/ -v --cov=app --cov-report=term-missing --cov-report=html


# Run linter
# 运行代码检查
lint:
	@echo "Running linter..."
	@echo "正在运行代码检查..."
	cd backend && ruff check app/


# Format code
# 格式化代码
format:
	@echo "Formatting code..."
	@echo "正在格式化代码..."
	cd backend && ruff format app/


# Clean up
# 清理
clean:
	@echo "Cleaning up..."
	@echo "正在清理..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name "*.pyo" -delete 2>/dev/null || true
	rm -rf backend/htmlcov 2>/dev/null || true
	rm -rf backend/.coverage 2>/dev/null || true
	@echo "Clean up complete."
	@echo "清理完成。"


# Build Docker image
# 构建 Docker 镜像
build:
	@echo "Building Docker image..."
	@echo "正在构建 Docker 镜像..."
	podman build -t mini-agent:latest -f backend/Dockerfile backend/


# Run Docker container
# 运行 Docker 容器
run:
	@echo "Running Docker container..."
	@echo "正在运行 Docker 容器..."
	podman run -d --name mini-agent -p 8000:8000 --env-file .env -e MODEL_BASE_URL=http://host.containers.internal:1234 mini-agent:latest


# Stop Docker container
# 停止 Docker 容器
stop:
	@echo "Stopping Docker container..."
	@echo "正在停止 Docker 容器..."
	podman stop mini-agent 2>/dev/null || true
	podman rm mini-agent 2>/dev/null || true
	@echo "Docker container stopped."
	@echo "Docker 容器已停止。"
