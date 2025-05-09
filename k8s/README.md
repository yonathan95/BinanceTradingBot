# Hive Mind on Kubernetes with Minikube

This directory contains Kubernetes manifests and deployment scripts to run the Hive Mind backend on a local Kubernetes cluster using Minikube.

## Prerequisites

Before you begin, ensure that you have the following tools installed:

- [Minikube](https://minikube.sigs.k8s.io/docs/start/)
- [kubectl](https://kubernetes.io/docs/tasks/tools/)
- [Docker](https://docs.docker.com/get-docker/)

## Getting Started

### 1. Setup Minikube

Minikube is a tool that makes it easy to run Kubernetes locally. It runs a single-node Kubernetes cluster on your personal computer.

```bash
# Start Minikube
minikube start --driver=docker

# Enable the Ingress addon
minikube addons enable ingress
```

### 2. Deploy to Minikube

To deploy the entire Hive Mind backend to Minikube, you can use the provided deployment scripts:

#### On Windows:
```bash
.\k8s\deploy-to-minikube.bat
```

#### On macOS/Linux:
```bash
chmod +x ./k8s/deploy-to-minikube.sh
./k8s/deploy-to-minikube.sh
```

The script will:
1. Start Minikube if it's not already running
2. Enable the Ingress addon
3. Configure Docker to use Minikube's Docker daemon
4. Build all required Docker images
5. Deploy all Kubernetes resources
6. Display information on how to access the services

### 3. Configure Host File

For the ingress to work correctly with the domain name `hivemind.local`, you need to add an entry to your hosts file:

```
<minikube-ip> hivemind.local
```

Where `<minikube-ip>` is the IP address of your Minikube cluster (displayed by the deployment script).

### 4. Access the Services

After deployment, you can access the services at:

- API: http://hivemind.local/api
- Cost Domain: http://hivemind.local/cost-domain
- Prometheus: http://hivemind.local/prometheus
- Grafana: http://hivemind.local/grafana

Alternatively, you can use the following command to see all the service URLs:

```bash
minikube service list -n hivemind
```

## Kubernetes Resource Structure

The deployment consists of the following Kubernetes resources:

- Namespace: `hivemind`
- Persistent Volume Claims: For PostgreSQL, Prometheus, and Grafana data
- ConfigMaps: For Prometheus configuration
- Deployments: 
  - PostgreSQL database
  - API service
  - Cost Domain service
  - Prometheus monitoring
  - Grafana dashboards
- Services: For exposing the deployments within the cluster
- Ingress: For external access to the services

## Troubleshooting

### Checking Pod Status

If you encounter issues, you can check the status of the pods:

```bash
kubectl get pods -n hivemind
```

### Viewing Pod Logs

To view the logs of a specific pod:

```bash
kubectl logs -n hivemind <pod-name>
```

### Restarting a Deployment

If you need to restart a deployment:

```bash
kubectl rollout restart deployment <deployment-name> -n hivemind
```

## Cleanup

To delete all resources created for the Hive Mind application:

```bash
kubectl delete namespace hivemind
```

To stop Minikube:

```bash
minikube stop
```

To completely remove Minikube:

```bash
minikube delete
``` 