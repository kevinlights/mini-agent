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