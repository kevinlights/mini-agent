set -eu

# https://istio.io/latest/docs/ambient/getting-started/
# https://istio.io/latest/docs/ambient/install/helm/
# https://github.com/istio/istio/tree/master/manifests/charts
# https://istio.io/latest/docs/ambient/getting-started/deploy-sample-app/
# https://istio.io/latest/docs/ambient/getting-started/secure-and-visualize/#add-bookinfo-to-the-mesh
# https://docker.aityp.com/r/docker.io/istio/pilot

curl -L https://istio.io/downloadIstio | sh -
cd istio-1.30.0

helm repo add istio https://istio-release.storage.googleapis.com/charts

# base component
helm install istio-base istio/base -n istio-system --create-namespace --wait

# install kubernetes gateway api
# kubectl get crd gateways.gateway.networking.k8s.io &> /dev/null || \
#   kubectl apply --server-side -f https://github.com/kubernetes-sigs/gateway-api/releases/download/v1.5.1/experimental-install.yaml

# registry.istio.io/release/pilot:1.30.0-distroless
# podman pull docker.m.daocloud.io/istio/pilot:1.30.0-distroless

## control plane
helm show values istio/istiod | grep -B 30 registry.istio.io
helm install istiod istio/istiod --namespace istio-system --set profile=ambient --set global.hub=docker.m.daocloud.io/istio --wait

# cni node agent
helm show values istio/cni | grep -B 30 registry.istio.io
helm install istio-cni istio/cni -n istio-system --set profile=ambient --set global.hub=docker.m.daocloud.io/istio --wait

# data plane
helm show values istio/ztunnel | grep -B 30 registry.istio.io
helm install ztunnel istio/ztunnel -n istio-system --set hub=docker.m.daocloud.io/istio --wait

helm ls -n istio-system

mkdir -p bookinfo
wget https://raw.githubusercontent.com/istio/istio/release-1.30/samples/bookinfo/platform/kube/bookinfo.yaml -O bookinfo/bookinfo.yaml
kubectl apply -f bookinfo/bookinfo.yaml

wget https://raw.githubusercontent.com/istio/istio/release-1.30/samples/bookinfo/platform/kube/bookinfo-versions.yaml -O bookinfo/bookinfo-versions.yaml
kubectl apply -f bookinfo/bookinfo-versions.yaml

kubectl get pods

wget https://raw.githubusercontent.com/istio/istio/release-1.30/samples/bookinfo/gateway-api/bookinfo-gateway.yaml -O bookinfo/bookinfo-gateway.yaml
kubectl apply -f bookinfo/bookinfo-gateway.yaml

# By default, Istio creates a LoadBalancer service for a gateway. As you will access this gateway by a tunnel, you don’t need a load balancer. Change the service type to ClusterIP by annotating the gateway:
kubectl annotate gateway bookinfo-gateway networking.istio.io/service-type=ClusterIP --namespace=default
Wait for the gateway to show as programmed before continuing.

# Wait for the gateway to show as programmed before continuing.
kubectl get gateway

kubectl port-forward svc/bookinfo-gateway-istio 8081:80
# http://localhost:8081/productpage
# If you refresh the page, you should see the display of the book ratings changing as the requests are distributed across the different versions of the reviews service.

# hostnames:
#   - bookinfo.klkl.ai
# curl -H "Host: bookinfo.klkl.ai" --resolve bookinfo.klkl.ai:8081:127.0.0.1 -- http://bookinfo.klkl.ai:8081/productpage

# You can enable all pods in a given namespace to be part of an ambient mesh by simply labeling the namespace:
kubectl label namespace default istio.io/dataplane-mode=ambient

curl -H "Host: bookinfo.klkl.ai" --resolve bookinfo.klkl.ai:8081:127.0.0.1 -- http://bookinfo.klkl.ai:8081/productpage

# # https://docker.aityp.com/image/docker.io/4km3/dnsmasq:latest
# podman run -d \
#   --name my-dns \
#   -p 5353:53/udp \
#   -p 5353:53/tcp \
#   swr.cn-north-4.myhuaweicloud.com/ddn-k8s/docker.io/4km3/dnsmasq:latest \
#   --address=/bookinfo.klkl.ai/127.0.0.1 \
#   --log-queries

podman network rm dns-net
podman network create --subnet 10.89.1.0/24 dns-net

# https://docker.aityp.com/image/docker.io/jpillora/dnsmasq:latest
podman run --rm \
    --name dnsmasq \
    -p 5153:53/udp \
    -p 5380:8080 \
    --ip 10.89.1.100 \
    --network dns-net \
    swr.cn-north-4.myhuaweicloud.com/ddn-k8s/docker.io/jpillora/dnsmasq:latest

# http://localhost:5380
# address=/bookinfo.klkl.ai/127.0.0.1

# check port 5353
# netstat -an | grep 5353

dig @127.0.0.1 -p 5153 bookinfo.klkl.ai A

# https://docker.aityp.com/image/docker.io/serjs/go-socks5-proxy:latest?platform=linux/arm64
podman run --rm --name socks5-proxy \
  -p 1080:1080 \
  -e PROXY_PORT=1080 \
  --network dns-net \
  --dns 10.89.1.100 \
  swr.cn-north-4.myhuaweicloud.com/ddn-k8s/docker.io/serjs/go-socks5-proxy:latest-linuxarm64

/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
  --user-data-dir=/tmp/chrome-test-profile \
  --proxy-server="socks5://127.0.0.1:1080" \
  --host-resolver-rules="MAP * ~NOTFOUND, EXCLUDE 127.0.0.1"
