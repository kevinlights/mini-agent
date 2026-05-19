#!/bin/bash
# DNS configuration for custom domain access to mini-agent
# mini-agent 自定义域名访问的 DNS 配置

set -eu

# Configuration
# 配置
DOMAIN="mini-agent.local"
DNS_PORT=5153
DNS_WEB_PORT=5380
DNS_NETWORK="mini-agent-dns-net"
DNS_SUBNET="10.89.2.0/24"
DNS_IP="10.89.2.100"

# Get Kind cluster node IP
# 获取 Kind 集群节点 IP
echo "Getting Kind cluster node IP..."
# 获取 Kind 集群节点 IP
KIND_NODE_IP=$(podman inspect mini-agent-control-plane --format='{{.NetworkSettings.Networks.kind.IPAddress}}' 2>/dev/null || echo "127.0.0.1")

# If running on macOS, use localhost for port-forward
# 如果在 macOS 上运行，使用 localhost 进行端口转发
if [[ "$(uname)" == "Darwin" ]]; then
    echo "macOS detected, using localhost for access"
    # 检测到 macOS，使用 localhost 访问
    GATEWAY_HOST="127.0.0.1"
    # Get NodePort from mini-agent namespace (where Istio Gateway service is)
    # 从 mini-agent 命名空间获取 NodePort（Istio Gateway 服务所在位置）
    NODE_PORT=$(kubectl get svc -n mini-agent -l gateway.networking.k8s.io/gateway-name=mini-agent -o jsonpath='{.items[0].spec.ports[?(@.port==80)].nodePort}' 2>/dev/null || echo "30364")
    echo "Gateway NodePort: $NODE_PORT"
else
    GATEWAY_HOST="$KIND_NODE_IP"
    # Get NodePort
    # 获取 NodePort
    NODE_PORT=$(kubectl get svc -n mini-agent -l gateway.networking.k8s.io/gateway-name=mini-agent -o jsonpath='{.items[0].spec.ports[?(@.port==80)].nodePort}' 2>/dev/null || echo "30364")
fi

echo "Gateway Host: $GATEWAY_HOST"
# 网关主机：$GATEWAY_HOST

# Create DNS network
# 创建 DNS 网络
echo "Creating DNS network..."
# 创建 DNS 网络
podman network rm "$DNS_NETWORK" 2>/dev/null || true
podman network create --subnet "$DNS_SUBNET" "$DNS_NETWORK"

# Start dnsmasq
# 启动 dnsmasq
echo "Starting dnsmasq..."
# 启动 dnsmasq
podman run -d --rm \
    --name mini-agent-dnsmasq \
    -p ${DNS_PORT}:53/udp \
    -p ${DNS_WEB_PORT}:8080 \
    --ip "$DNS_IP" \
    --network "$DNS_NETWORK" \
    swr.cn-north-4.myhuaweicloud.com/ddn-k8s/docker.io/jpillora/dnsmasq:latest

# Wait for dnsmasq to start
# 等待 dnsmasq 启动
sleep 2

echo ""
echo "========================================="
echo "DNS Configuration Complete"
echo "DNS 配置完成"
echo "========================================="
echo ""
echo "DNS Server: 127.0.0.1:${DNS_PORT}"
echo "DNS Web UI: http://localhost:${DNS_WEB_PORT}"
echo "Domain: ${DOMAIN} -> ${GATEWAY_HOST}"
echo ""
echo "DNS 服务器：127.0.0.1:${DNS_PORT}"
echo "DNS Web 界面：http://localhost:${DNS_WEB_PORT}"
echo "域名：${DOMAIN} -> ${GATEWAY_HOST}"
echo ""
echo "Test DNS resolution:"
# 测试 DNS 解析：
echo "  dig @127.0.0.1 -p ${DNS_PORT} ${DOMAIN} A"
echo ""
echo "Access mini-agent:"
# 访问 mini-agent：
echo "  curl http://${DOMAIN}:${NODE_PORT}"
echo "  Open browser: http://${DOMAIN}:${NODE_PORT}"
echo ""
echo "To use with Chrome via SOCKS5 proxy:"
# 通过 SOCKS5 代理在 Chrome 中使用：
echo "  podman run -d --name mini-agent-socks5 -p 1080:1080 --network ${DNS_NETWORK} --dns ${DNS_IP} swr.cn-north-4.myhuaweicloud.com/ddn-k8s/docker.io/serjs/go-socks5-proxy:latest-linuxarm64"
echo "  /Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --user-data-dir=/tmp/mini-agent-chrome --proxy-server=\"socks5://127.0.0.1:1080\" --host-resolver-rules=\"MAP * ~NOTFOUND, EXCLUDE 127.0.0.1\""
echo ""

# Stop script
# 停止脚本
cat << 'EOF'
To stop DNS server:
# 停止 DNS 服务器：
  podman stop mini-agent-dnsmasq

EOF
