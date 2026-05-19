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
