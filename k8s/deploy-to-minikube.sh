#!/bin/bash
set -e

# Start minikube if not already running
if ! minikube status &>/dev/null; then
  echo "Starting minikube..."
  minikube start --driver=docker
else
  echo "Minikube is already running"
fi

# Enable ingress addon if not already enabled
if ! minikube addons list | grep -q "ingress: enabled"; then
  echo "Enabling ingress addon..."
  minikube addons enable ingress
fi

# Set docker to use minikube's docker daemon
echo "Setting up docker environment for minikube..."
eval $(minikube docker-env)

# Build docker images
echo "Building API Docker image..."
docker build -t hivemind-api:latest -f ./hive-mind/docker/Dockerfile.backend ./hive-mind

echo "Building Cost Domain Docker image..."
docker build -t hivemind-cost-domain:latest -f ./hive-mind/cost-domain/Dockerfile ./hive-mind/cost-domain

# Create namespace
echo "Creating Kubernetes resources..."
kubectl apply -f k8s/manifests/namespace.yaml

# Apply persistent volume claims
kubectl apply -f k8s/manifests/persistent-volumes.yaml

# Apply ConfigMaps
kubectl apply -f k8s/manifests/prometheus-configmap.yaml

# Apply deployments and services
kubectl apply -f k8s/manifests/postgres.yaml
kubectl apply -f k8s/manifests/api.yaml
kubectl apply -f k8s/manifests/cost-domain.yaml
kubectl apply -f k8s/manifests/prometheus.yaml
kubectl apply -f k8s/manifests/grafana.yaml

# Apply ingress last
kubectl apply -f k8s/manifests/ingress.yaml

# Print service URLs
echo "Getting minikube IP..."
MINIKUBE_IP=$(minikube ip)

echo "============================================"
echo "Add the following entry to your hosts file:"
echo "$MINIKUBE_IP hivemind.local"
echo "============================================"

echo "Services should be available at:"
echo "API: http://hivemind.local/api"
echo "Cost Domain: http://hivemind.local/cost-domain"
echo "Prometheus: http://hivemind.local/prometheus"
echo "Grafana: http://hivemind.local/grafana"

echo "Or you can access the services directly using:"
minikube service list -n hivemind 
