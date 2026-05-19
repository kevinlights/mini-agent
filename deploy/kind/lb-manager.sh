#!/bin/bash
# LoadBalancer manager for Kind cluster using cloud-provider-kind
# 使用 cloud-provider-kind 为 Kind 集群管理 LoadBalancer

set -eu

# Configuration
# 配置
PID_FILE="/tmp/cloud-provider-kind.pid"
LOG_FILE="/tmp/cloud-provider-kind.log"

# Check if cloud-provider-kind is installed
# 检查是否已安装 cloud-provider-kind
check_installed() {
    if ! command -v cloud-provider-kind &> /dev/null; then
        echo "cloud-provider-kind not found."
        # 未找到 cloud-provider-kind
        echo "Installing..."
        # 正在安装...
        go install sigs.k8s.io/cloud-provider-kind@latest
        echo "Installed."
        # 安装完成
    fi
}

# Start LoadBalancer
# 启动 LoadBalancer
start() {
    check_installed
    
    if is_running; then
        echo "cloud-provider-kind is already running (PID: $(cat $PID_FILE))"
        # cloud-provider-kind 已在运行
        return 0
    fi
    
    echo "Starting cloud-provider-kind (requires sudo)..."
    # 正在启动 cloud-provider-kind（需要 sudo）...
    
    # Get the full path to cloud-provider-kind
    # 获取 cloud-provider-kind 的完整路径
    CPK_PATH=$(which cloud-provider-kind)
    
    # Use sudo with -S to read password from stdin, or prompt in terminal
    # 使用 sudo -S 从 stdin 读取密码，或在终端中提示
    echo "Please enter sudo password if prompted:"
    # 如果提示，请输入 sudo 密码：
    sudo -v
    if [ $? -ne 0 ]; then
        echo "Sudo authentication failed."
        # sudo 认证失败
        return 1
    fi
    
    # Run with sudo in background using bash -c
    # 使用 sudo 在后台运行
    # Skip Gateway API CRD installation (already installed by Istio)
    # 跳过 Gateway API CRD 安装（已由 Istio 安装）
    sudo bash -c "nohup $CPK_PATH --gateway-channel disabled > '$LOG_FILE' 2>&1 &"
    # Get the PID of the last background process
    # 获取最后一个后台进程的 PID
    sudo bash -c "pgrep -f 'cloud-provider-kind' | tail -1" > "$PID_FILE"
    
    sleep 2
    
    if is_running; then
        echo "cloud-provider-kind started successfully (PID: $(cat $PID_FILE))"
        # cloud-provider-kind 启动成功
        echo "Log file: $LOG_FILE"
        # 日志文件：$LOG_FILE
    else
        echo "Failed to start cloud-provider-kind. Check log: $LOG_FILE"
        # 启动失败，请检查日志
        return 1
    fi
}

# Stop LoadBalancer
# 停止 LoadBalancer
stop() {
    if ! is_running; then
        echo "cloud-provider-kind is not running."
        # cloud-provider-kind 未运行
        return 0
    fi
    
    PID=$(cat "$PID_FILE")
    echo "Stopping cloud-provider-kind (PID: $PID)..."
    # 正在停止 cloud-provider-kind...
    
    sudo kill "$PID" 2>/dev/null || true
    rm -f "$PID_FILE"
    
    sleep 1
    
    if kill -0 "$PID" 2>/dev/null; then
        echo "Force killing..."
        # 强制终止...
        kill -9 "$PID" 2>/dev/null || true
    fi
    
    echo "cloud-provider-kind stopped."
    # cloud-provider-kind 已停止
}

# Check if running
# 检查是否运行中
is_running() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if kill -0 "$PID" 2>/dev/null; then
            return 0
        fi
    fi
    return 1
}

# Show status
# 显示状态
status() {
    if is_running; then
        PID=$(cat "$PID_FILE")
        echo "cloud-provider-kind is running (PID: $PID)"
        # cloud-provider-kind 正在运行
        echo "Cluster: $CLUSTER_NAME"
        echo "Log file: $LOG_FILE"
        echo ""
        echo "Recent logs:"
        # 最近日志：
        tail -10 "$LOG_FILE"
    else
        echo "cloud-provider-kind is not running."
        # cloud-provider-kind 未运行
    fi
}

# Show LoadBalancer services
# 显示 LoadBalancer 服务
show_services() {
    echo "LoadBalancer services:"
    # LoadBalancer 服务：
    kubectl get svc --all-namespaces -o wide | grep LoadBalancer || echo "No LoadBalancer services found."
    # 未找到 LoadBalancer 服务
}

# Main
# 主函数
case "${1:-status}" in
    start)
        start
        ;;
    stop)
        stop
        ;;
    restart)
        stop
        start
        ;;
    status)
        status
        ;;
    services)
        show_services
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status|services}"
        echo "用法：$0 {start|stop|restart|status|services}"
        exit 1
        ;;
esac
