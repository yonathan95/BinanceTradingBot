# Hive Mind: Getting Started Guide

This guide will help you set up your development environment and understand the key components of the Hive Mind platform.

## Prerequisites

- **Google Cloud Platform Account** with billing enabled
- **Terraform** (v1.0.0+)
- **Python** (3.11+)
- **Node.js** (18+)
- **Docker** and Docker Compose
- **kubectl** CLI
- **gcloud** CLI

## Local Development Environment Setup

### 1. Clone the Repository

```bash
git clone https://github.com/your-org/hive-mind.git
cd hive-mind
```

### 2. Set Up Python Environment

```bash
# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### 3. Set Up Node.js Environment (for UI)

```bash
cd ui
npm install
```

### 4. Configure Google Cloud Access

```bash
# Login to Google Cloud
gcloud auth login

# Set your project
gcloud config set project your-project-id

# Enable required APIs
gcloud services enable container.googleapis.com \
  artifactregistry.googleapis.com \
  cloudbuild.googleapis.com \
  cloudrun.googleapis.com \
  pubsub.googleapis.com \
  secretmanager.googleapis.com \
  logging.googleapis.com \
  monitoring.googleapis.com \
  storage.googleapis.com \
  bigquery.googleapis.com
```

### 5. Set up Terraform

```bash
# Initialize Terraform with the GCS backend
cd infra
terraform init
```

## Running Locally with Docker Compose

For development purposes, you can run the core components locally using Docker Compose:

```bash
# From the project root
docker-compose up -d
```

This will start:
- FastAPI Control Plane on http://localhost:8000
- React UI on http://localhost:3000
- A mock Agent Worker
- Local Qdrant instance
- Redis for local queue

## Project Structure

```
hive-mind/
├── infra/                  # Terraform infrastructure code
├── control-plane/          # FastAPI Control Plane service
├── agent-sdk/              # Agent framework and tools
├── cost-domain/            # Cost Domain Manager service
├── task-orchestrator/      # Task Orchestrator & Tier Router
├── ui/                     # React/Tauri UI
├── agents/                 # Agent implementations
├── tools/                  # Tool implementations
├── docker/                 # Docker configurations
├── docs/                   # Documentation
└── tests/                  # Test suite
```

## Key Components and How to Run Them

### Control Plane

The Control Plane is the central API server that manages teams, agents, and tasks.

```bash
# Run locally
cd control-plane
uvicorn app.main:app --reload
```

API documentation will be available at http://localhost:8000/docs

### Agent SDK

The Agent SDK provides the base classes and tools for building agents.

```bash
# Run unit tests
cd agent-sdk
pytest
```

### Running the UI

```bash
# Run in development mode
cd ui
npm run dev
```

For the Tauri desktop app:

```bash
cd ui
npm run tauri dev
```

## Deploying to GCP

### Development Environment

```bash
cd infra
terraform apply -var-file=env/dev.tfvars
```

### Building and Pushing Docker Images

```bash
# Build and push the Control Plane
gcloud builds submit --config=control-plane/cloudbuild.yaml

# Build and push an Agent Worker
gcloud builds submit --config=agents/planner/cloudbuild.yaml
```

## Creating Your First Team

1. Start the local development environment with Docker Compose.
2. Open the UI at http://localhost:3000.
3. Create a new team with the following roles:
   - Planner
   - Architect
   - Coder
4. Configure a workspace.
5. Create a simple task to test the system.

## Development Workflow

1. **Feature Branches**: Create a new branch for each feature or bugfix.
2. **Tests**: Write tests for new features and ensure all tests pass.
3. **Documentation**: Update documentation for any changes.
4. **Pull Requests**: Submit a PR for review before merging.

## Debugging

### Logs

```bash
# View Control Plane logs
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=control-plane" --limit=50

# View Agent Worker logs
kubectl logs -n hive-mind-agents -l app=planner-agent
```

### Monitoring

- Cloud Monitoring dashboards are available at: https://console.cloud.google.com/monitoring/dashboards
- Local Prometheus/Grafana is available at: http://localhost:3001

## Common Issues and Solutions

### Authentication Issues

If you encounter authentication issues with Google Cloud, ensure:
- You've run `gcloud auth login`
- Your account has the necessary permissions
- Service accounts have the correct IAM roles

### Agent Connectivity

If agents are not communicating:
- Check Pub/Sub topics and subscriptions
- Verify network connectivity between components
- Check for errors in the agent logs

### Cost Overruns

If you see unexpected costs:
- Check the Cost Domain Manager logs
- Verify budget configurations
- Look for looping agents or runaway tasks

## Next Steps

1. Explore the [Architecture Document](./architecture.md) for a deeper understanding of the system.
2. Check the [Task Breakdown](./taskBreakdown.md) for specific implementation details.
3. Review the [Development Roadmap](./developmentRoadmap.md) to understand the project timeline.

## Contributing

See [CONTRIBUTING.md](../CONTRIBUTING.md) for contribution guidelines.

## Getting Help

- Join the #hive-mind Slack channel
- Check the [FAQ](../docs/FAQ.md)
- File an issue on GitHub 