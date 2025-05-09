# Hive Mind Architecture

## System Overview

Hive Mind is a GCP-based multi-agent engineering platform that enables users to create AI product teams composed of specialized LLM agents. The architecture is designed to be scalable, secure, and cost-effective, with particular attention to features like cost management, tiered LLM usage, and inter-team communication.

## Architecture Diagram

```
┌───────────────────────┐      Human & Ops API
│   React / Tauri GUI   │ ◀───────────────────────────┐
└──────────┬────────────┘                           │10. WS
           │2. REST/WS                              │   events
           ▼                                        ▼
┌─────────────────────────┐        ┌───────────────┐     7. budget alerts
│ FastAPI Control-Plane   │──────▶ │ Cost Domain   │◀────────────────┐
│  • CRUD: Team / Task    │  5.    │  Manager      │                 │
│  • Auth: IAM / Firebase │  Events└──────┬────────┘                 │
└────┬───────────┬────────┘               │8. spend forecast         │
     │           │3. Pub/Sub topics       ▼                          │
     │           └───────────────┐ ┌───────────────┐                │
     │                           │ │ Task-Orchestr │                │
     │                           │ │ & Tier Router │                │
     │                           │ └────────┬──────┘                │
     │                           │4. assign │                       │
     ▼6. metrics                 ▼          ▼                       │
┌───────────────┐      ┌────────────────┐ ┌────────────────┐        │
│ CloudLogging  │      │ Agent Worker   │ │  Manager Agent │        │
└───────────────┘      │  (GKE Pod)     │ │ (orchestrator) │        │
                       └────────┬───────┘ └────────┬───────┘        │
                                │shell PTY         │                │
                                ▼                  ▼                │
                 ┌───────────────────────┐   ┌───────────────┐      │
                 │  Ephemeral Workspace  │   │ Vector Memory │      │
                 │   (GCS-Fuse / PV)     │   │  (Qdrant)     │      │
                 └───────────────────────┘   └───────────────┘      │
                                                                     │
                        ┌───────────────────────────────┐            │
                        │   BigQuery (billing export)   │────────────┘
                        └───────────────────────────────┘
```

## Component Descriptions

### 1. User Interface (React/Tauri)

The user interface is built using React for the web version and Tauri for the desktop application. It provides the following key functionalities:

- Team creation and management interface
- Workspace file browser and editor
- Real-time agent conversation display
- Task creation and monitoring
- Budget dashboards and alerts
- System configuration

#### Communication Interfaces
- REST API calls to Control Plane for CRUD operations
- WebSocket connections for real-time logs and events
- Local filesystem access for desktop version

### 2. Control Plane API (FastAPI)

The Control Plane is the central management layer that handles all user requests and orchestrates the system components.

#### Key Components
- REST API endpoints for team, agent, and task management
- GraphQL API for complex data querying
- WebSocket handlers for real-time communication
- Authentication and authorization middleware
- Rate limiting and request validation

#### Communication Interfaces
- Incoming: REST/GraphQL/WebSocket from UI
- Outgoing: Pub/Sub messages to Task Orchestrator and Agent Workers
- Outgoing: Cloud Logging for system metrics

### 3. Cost Domain Manager (CDM)

The CDM is responsible for tracking and enforcing budget constraints across the system.

#### Key Components
- Budget model and storage
- Token usage tracking middleware
- BigQuery integration for cost data
- Spend forecasting with Vertex AI
- Budget enforcement mechanisms

#### Communication Interfaces
- Incoming: Usage data from Agent Workers
- Incoming: Billing export data from BigQuery
- Outgoing: Budget alerts to Control Plane
- Outgoing: Team configuration updates (e.g., pausing or down-tiering)

### 4. Task Orchestrator & Tier Router (TOTR)

The TOTR handles task assignment, dependency management, and model tier selection.

#### Key Components
- Task queue and priority management
- Tier selection based on complexity and budget
- Agent load balancing
- Dependency resolution

#### Communication Interfaces
- Incoming: Task creation from Control Plane
- Outgoing: Task assignments to Agent Workers
- Bidirectional: Communication with Manager Agent for orchestration

### 5. Agent Workers (GKE Pods)

Agent Workers are containerized instances that run individual LLM agents with specific roles.

#### Key Components
- BaseAgent implementation
- Tool registry and execution
- Context management
- Token usage tracking

#### Communication Interfaces
- Incoming: Task assignments from TOTR
- Outgoing: Task results and metrics
- Outgoing: Token usage to CDM
- Bidirectional: Inter-agent communication via Manager Agent

### 6. Manager Agent (Orchestrator)

The Manager Agent coordinates the activities of other agents and facilitates their communication.

#### Key Components
- LangGraph-based orchestration flow
- Inter-Team Communication Layer
- Context aggregation and summarization
- Error handling and recovery

#### Communication Interfaces
- Bidirectional: Communication with all agents
- Bidirectional: Communication with TOTR
- Outgoing: Progress updates to Control Plane

### 7. Ephemeral Workspace

The Ephemeral Workspace provides a secure environment for agents to read and write files.

#### Key Components
- GCS buckets for persistent storage
- GCS-FUSE for filesystem mounting
- Lifecycle policies for cleanup

#### Communication Interfaces
- Accessed by Agent Workers through FileTool
- Managed by Control Plane for provisioning and cleanup

### 8. Vector Memory (Qdrant)

Vector Memory stores embeddings for long-term context management.

#### Key Components
- Qdrant vector database (self-hosted on GKE)
- Embedding generation service
- Context retrieval API

#### Communication Interfaces
- Used by Manager Agent for context retrieval
- Updated by Agent Workers with new information

## Data Flows

### 1. Team Creation Flow
1. User creates team configuration in UI
2. Request sent to Control Plane via REST API
3. Control Plane validates and stores team configuration
4. Control Plane provisions workspace in GCS
5. Control Plane creates appropriate Pub/Sub topics
6. Team status returned to UI

### 2. Task Execution Flow
1. User or agent creates a task
2. Control Plane validates and forwards to TOTR
3. TOTR selects appropriate tier and agent
4. Task assigned to Agent Worker
5. Agent Worker executes task, potentially using tools
6. Results returned to Manager Agent
7. Manager Agent updates task status
8. Status updates streamed to UI via WebSocket

### 3. Cost Management Flow
1. Agent Worker tracks token usage during execution
2. Usage metrics sent to CDM
3. CDM aggregates usage data by team/topic
4. BigQuery export provides additional billing data
5. CDM forecasts future spending
6. If approaching budget limits:
   a. CDM sends alert to Control Plane
   b. Control Plane notifies UI
   c. CDM may auto-pause or down-tier agents
   d. User can adjust budgets or approve overages

### 4. Inter-Team Communication Flow
1. Agent generates message with context tag (#frontend, #backend)
2. Message sent to Manager Agent
3. Manager Agent uses ITCL to determine routing
4. ITCL summarizes message if needed
5. Message forwarded to appropriate team(s)
6. Receiving team's Manager Agent adds to context
7. Response follows same path in reverse

## Security Architecture

### Authentication & Authorization
- Firebase Authentication for user login
- IAM for service account management
- Workload Identity for secure Kubernetes-to-GCP authentication
- RBAC for fine-grained access control

### Data Security
- VPC-native networking with no direct internet access
- Secret Manager for sensitive configuration
- Cloud KMS for encryption keys
- Data Loss Prevention API for PII scanning

### Workload Security
- GKE Autopilot with hardened node images
- Binary Authorization for trusted images only
- Container sandboxing with gVisor
- Seccomp profiles for limiting system calls
- Non-root containers with minimal permissions

## Deployment Architecture

### Environments
- Development: Minimal GKE cluster, single-zone
- Staging: Regional GKE, full component set
- Production: Multi-regional, high-availability

### CI/CD Pipeline
- GitHub Actions for testing
- Cloud Build for container building
- Artifact Registry for image storage
- Terraform Cloud for infrastructure deployment

## System Interfaces

### External APIs
- OpenAI API for GPT models
- Anthropic API for Claude models
- Google Vertex AI for Gemini models
- GitHub API for code repository integration
- Web Search API for research

### Internal APIs
- Agent Tool API: Standardized interface for all agent tools
- Vector Memory API: Embedding storage and retrieval
- Budget API: Cost tracking and enforcement
- Team Management API: Create and configure teams
- Task API: Task creation and status tracking

## Scalability Considerations

### Horizontal Scaling
- Agent Workers scale with GKE Autopilot
- Control Plane scales with Cloud Run
- Vector Memory scales with Qdrant cluster size

### Performance Optimizations
- Token caching for repetitive patterns
- Context pruning to minimize token usage
- Efficient tiering to minimize costs
- Parallel task execution when dependencies allow

## Monitoring and Observability

### Metrics Collection
- Cloud Monitoring for system metrics
- Custom metrics for token usage and task completion
- Latency tracking for LLM calls

### Logging
- Structured logging with Cloud Logging
- Log-based metrics for alerting
- Audit logs for security monitoring

### Dashboards
- Operational dashboards for system health
- Cost dashboards for budget tracking
- Performance dashboards for LLM usage

## Disaster Recovery

### Backup Strategy
- GCS bucket versioning for workspaces
- Database backups for configuration
- Terraform state backup

### Recovery Procedures
- Environment rebuild from Terraform
- Data restoration from backups
- Automated testing after recovery

## Configuration Management

### Infrastructure Configuration
- Terraform modules for all GCP resources
- Environment-specific variable files
- Secret management via Secret Manager

### Application Configuration
- ConfigMaps for non-sensitive configuration
- Secrets for sensitive configuration
- Feature flags for gradual rollout 