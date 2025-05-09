@echo off
setlocal EnableDelayedExpansion

REM Start minikube if not already running
minikube status > nul 2>&1
if %ERRORLEVEL% NEQ 0 (
  echo Starting minikube...
  minikube start --driver=docker
) else (
  echo Minikube is already running
)

REM Enable ingress addon if not already enabled
minikube addons list | findstr "ingress.*enabled" > nul
if %ERRORLEVEL% NEQ 0 (
  echo Enabling ingress addon...
  minikube addons enable ingress
)

REM Set docker to use minikube's docker daemon
echo Setting up docker environment for minikube...
FOR /F "tokens=*" %%i IN ('minikube -p minikube docker-env --shell cmd') DO %%i

REM Build docker images
echo Building API Docker image...
docker build -t hivemind-api:latest -f ./hive-mind/docker/Dockerfile.backend ./hive-mind

echo Building Cost Domain Docker image...
docker build -t hivemind-cost-domain:latest -f ./hive-mind/cost-domain/Dockerfile ./hive-mind/cost-domain

REM Create namespace
echo Creating Kubernetes resources...
kubectl apply -f k8s/manifests/namespace.yaml

REM Apply persistent volume claims
kubectl apply -f k8s/manifests/persistent-volumes.yaml

REM Apply ConfigMaps
kubectl apply -f k8s/manifests/prometheus-configmap.yaml

REM Apply deployments and services
kubectl apply -f k8s/manifests/postgres.yaml
kubectl apply -f k8s/manifests/api.yaml
kubectl apply -f k8s/manifests/cost-domain.yaml
kubectl apply -f k8s/manifests/prometheus.yaml
kubectl apply -f k8s/manifests/grafana.yaml

REM Apply ingress last
kubectl apply -f k8s/manifests/ingress.yaml

REM Print service URLs
echo Getting minikube IP...
FOR /F "tokens=*" %%i IN ('minikube ip') DO set MINIKUBE_IP=%%i

echo ============================================
echo Add the following entry to your hosts file:
echo %MINIKUBE_IP% hivemind.local
echo ============================================

echo Services should be available at:
echo API: http://hivemind.local/api
echo Cost Domain: http://hivemind.local/cost-domain
echo Prometheus: http://hivemind.local/prometheus
echo Grafana: http://hivemind.local/grafana

echo Or you can access the services directly using:
minikube service list -n hivemind 