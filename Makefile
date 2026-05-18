# Mini-Agent Makefile
# Mini-Agent 项目的 Makefile

.PHONY: help install dev dev-frontend test lint clean build build-frontend run run-frontend stop stop-frontend stop-all

# Default target
# 默认目标
help:
	@echo "Mini-Agent - Available Commands"
	@echo "Mini-Agent - 可用命令"
	@echo ""
	@echo "  make install    - Install Python dependencies"
	@echo "  make install    - 安装 Python 依赖"
	@echo ""
	@echo "  make dev        - Start backend development server"
	@echo "  make dev        - 启动后端开发服务器"
	@echo ""
	@echo "  make dev-frontend - Start frontend development server"
	@echo "  make dev-frontend - 启动前端开发服务器"
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
	@echo "  make build      - Build backend Docker image"
	@echo "  make build      - 构建后端 Docker 镜像"
	@echo ""
	@echo "  make build-frontend - Build frontend Docker image"
	@echo "  make build-frontend - 构建前端 Docker 镜像"
	@echo ""
	@echo "  make run        - Run backend Docker container"
	@echo "  make run        - 运行后端 Docker 容器"
	@echo ""
	@echo "  make run-frontend - Run frontend Docker container"
	@echo "  make run-frontend - 运行前端 Docker 容器"
	@echo ""
	@echo "  make stop       - Stop backend Docker container"
	@echo "  make stop       - 停止后端 Docker 容器"
	@echo ""
	@echo "  make stop-frontend - Stop frontend Docker container"
	@echo "  make stop-frontend - 停止前端 Docker 容器"
	@echo ""
	@echo "  make stop-all   - Stop all Docker containers"
	@echo "  make stop-all   - 停止所有 Docker 容器"


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


# Start frontend development server
# 启动前端开发服务器
dev-frontend:
	@echo "Starting frontend development server..."
	@echo "正在启动前端开发服务器..."
	cd frontend && npm run dev


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


# Build backend Docker image
# 构建后端 Docker 镜像
build:
	@echo "Building backend Docker image..."
	@echo "正在构建后端 Docker 镜像..."
	podman build -t mini-agent-backend:latest -f backend/Dockerfile backend/


# Build frontend Docker image
# 构建前端 Docker 镜像
build-frontend:
	@echo "Building frontend Docker image..."
	@echo "正在构建前端 Docker 镜像..."
	podman build -t mini-agent-frontend:latest -f frontend/Dockerfile frontend/


# Run backend Docker container
# 运行后端 Docker 容器
run:
	@echo "Running backend Docker container..."
	@echo "正在运行后端 Docker 容器..."
	podman network create mini-agent-net 2>/dev/null || true
	podman run -d --name mini-agent-backend -p 8000:8000 --network mini-agent-net --env-file .env -e MODEL_BASE_URL=http://host.containers.internal:1234 mini-agent-backend:latest


# Run frontend Docker container
# 运行前端 Docker 容器
run-frontend:
	@echo "Running frontend Docker container..."
	@echo "正在运行前端 Docker 容器..."
	podman network create mini-agent-net 2>/dev/null || true
	podman run -d --name mini-agent-frontend -p 8001:80 --network mini-agent-net mini-agent-frontend:latest


# Stop backend Docker container
# 停止后端 Docker 容器
stop:
	@echo "Stopping backend Docker container..."
	@echo "正在停止后端 Docker 容器..."
	podman stop mini-agent-backend 2>/dev/null || true
	podman rm mini-agent-backend 2>/dev/null || true
	@echo "Backend Docker container stopped."
	@echo "后端 Docker 容器已停止。"


# Stop frontend Docker container
# 停止前端 Docker 容器
stop-frontend:
	@echo "Stopping frontend Docker container..."
	@echo "正在停止前端 Docker 容器..."
	podman stop mini-agent-frontend 2>/dev/null || true
	podman rm mini-agent-frontend 2>/dev/null || true
	@echo "Frontend Docker container stopped."
	@echo "前端 Docker 容器已停止。"


# Stop all Docker containers
# 停止所有 Docker 容器
stop-all: stop-frontend stop
	@echo "All Docker containers stopped."
	@echo "所有 Docker 容器已停止。"
