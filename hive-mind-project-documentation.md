# Hive Mind: Comprehensive Project Documentation

## Table of Contents
1. [Project Overview](#project-overview)
2. [System Architecture](#system-architecture)
3. [Core Components](#core-components)
   - [Agent Framework](#agent-framework)
   - [Control Plane](#control-plane)
   - [Cost Domain Manager](#cost-domain-manager)
   - [Task Orchestrator](#task-orchestrator)
   - [Inter-Team Communication Layer](#inter-team-communication-layer)
   - [VS Code Integration](#vs-code-integration)
4. [Agent Roles and Capabilities](#agent-roles-and-capabilities)
5. [Memory and Knowledge Base](#memory-and-knowledge-base)
6. [User Interface](#user-interface)
7. [Infrastructure and Deployment](#infrastructure-and-deployment)
8. [Development Workflow](#development-workflow)
9. [API References](#api-references)
10. [Implementation Guide](#implementation-guide)

## Project Overview

Hive Mind is a multi-agent engineering platform that enables users to create and manage AI product teams composed of specialized Large Language Model (LLM) agents. The system allows these agent teams to collaborate effectively on software engineering tasks, manage computational resources, and integrate with existing development environments like VS Code.

The platform is designed with several key principles in mind:
- **Scalability**: Support for multiple teams working on different projects
- **Cost-effectiveness**: Tiered LLM usage and budget management
- **Security**: Controlled access to system resources
- **Interoperability**: Integration with existing development tools
- **Extensibility**: Easy addition of new agent types and capabilities

The project combines a backend system for agent orchestration with a modern UI for human interaction and monitoring.

## System Architecture

Hive Mind follows a microservices architecture running primarily on Google Cloud Platform (GCP). The high-level architecture consists of these main components:

```
┌───────────────────────┐      Human & Ops API
│   React / Tauri GUI   │ ◀───────────────────────────┐
└──────────┬────────────┘                             │
           │ REST/WS                                  │ WS events
           ▼                                          ▼
┌─────────────────────────┐        ┌───────────────────────┐
│ FastAPI Control-Plane   │───────▶│ Cost Domain Manager   │
│  • CRUD: Team / Task    │ Events │                       │
│  • Auth: IAM / Firebase │        └───────────┬───────────┘
└──────────┬──────────────┘                    │
           │ PubSub                            │ Budget
           ▼                                   │ Constraints
┌─────────────────────────┐                    │
│ Task Orchestrator       │◀───────────────────┘
│  • Task Assignment      │
│  • Dependency Resolver  │
│  • Tier Router          │
└──────────┬──────────────┘
           │ RabbitMQ
           ▼
┌─────────────────────────┐
│ Agent Workers           │
│  • BaseAgent Framework  │
│  • Specialized Agents   │
│  • Tool Integration     │
└──────────┬──────────────┘
           │ API Requests
           ▼
┌─────────────────────────┐
│ LLM Providers           │
│  • OpenAI               │
│  • Anthropic            │
│  • Local Models         │
└─────────────────────────┘
```

## Core Components

### Agent Framework

The Agent Framework is the foundation of the entire Hive Mind system. It provides the base classes and interfaces that all specialized agents inherit from.

#### BaseAgent

The `BaseAgent` is an abstract class that defines the core functionality for all agents:

```python
class BaseAgent(ABC):
    """Base class for all agents in the Hive Mind system"""
    
    def __init__(self, 
                 agent_id: str, 
                 model: str, 
                 temperature: float, 
                 token_limit: int,
                 max_retries: int = 3,
                 retry_delay: float = 1.0):
        self.agent_id = agent_id
        self.model = model
        self.temperature = temperature
        self.token_limit = token_limit
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.tools = []
        self.memory = None
        self.tasks = {}
        self.token_count = 0
```

Key features of the BaseAgent:
- Message sending and receiving
- Tool integration
- Memory management
- LLM integration (multiple providers)
- Error handling and retries
- Context management
- Logging and metrics

#### Message System

Agents communicate through a structured message system:

```python
class Message:
    """Represents a message exchanged between agents"""
    sender: str
    recipients: List[str]
    context_tags: List[str]
    message_type: str
    content: str
    priority: str = "normal"
    requires_response: bool = False
    thread_id: Optional[str] = None
```

Messages include context tags that help with routing and relevance determination. This enables efficient communication between agents working on different aspects of the same task.

#### Agent Tools

Agents have access to various tools that extend their capabilities:

- **FileTool**: For file operations (read/write/create/delete)
- **ExecTool**: For executing shell commands in a sandboxed environment
- **GitTool**: For Git operations (clone/commit/push/pull)
- **WebSearchTool**: For searching the web for information
- **VectorMemoryTool**: For semantic search over stored memories
- **APITool**: For making HTTP requests to external services

### Control Plane

The Control Plane is the central management layer of the Hive Mind system. It provides:

- REST API for human interaction
- WebSocket connections for real-time updates
- Team and task CRUD operations
- Authentication and authorization
- Event routing via PubSub

The Control Plane API is built with FastAPI and includes these main route groups:
- `/teams`: Team management
- `/tasks`: Task creation and management
- `/agents`: Agent configuration
- `/vscode`: VS Code integration
- `/cost`: Budget and cost management

### Cost Domain Manager

The Cost Domain Manager handles:
- Token usage tracking
- Budget configuration and enforcement
- Cost optimization strategies
- Billing integration
- Tier management for models

It ensures that teams stay within their allocated budgets and provides alerts when thresholds are approached.

### Task Orchestrator

The Task Orchestrator manages:
- Task creation and assignment
- Dependency resolution between tasks
- Priority-based scheduling
- Model tier selection based on task complexity and budget
- Progress tracking and reporting

It uses a combination of rule-based and LLM-assisted logic to determine optimal task assignments.

### Inter-Team Communication Layer (ITCL)

The ITCL facilitates communication between different teams of agents:

- Context-based message routing
- Team relationship graph management
- Conversation summarization
- Cross-team broadcasts and directed messages

This layer allows specialized teams to collaborate on larger projects while minimizing token usage through efficient communication patterns.

### VS Code Integration

The VS Code integration (Work Mode) allows real-time collaboration between the Hive Mind system and developers:

#### Components

1. **VS Code Extension**
   - Tracks file changes made by users
   - Sends changes to the Hive Mind backend
   - Receives messages and instructions from agents
   - Provides UI for permission management

2. **Backend VS Code Controller**
   - Manages client connections via Socket.IO
   - Tracks permission status
   - Routes file changes to agents
   - Forwards agent messages to VS Code clients

3. **VS Code Change Handler**
   - Analyzes file changes
   - Determines relevance to ongoing tasks
   - Creates change summaries for agent processing
   - Manages task-client relationships

4. **Work Mode UI**
   - Displays connected clients
   - Shows real-time file changes
   - Provides messaging interface
   - Visualizes agent-client interactions

#### Features

- Permission management for all operations
- Real-time file change tracking and analysis
- Bi-directional communication between agents and developers
- Automatic task creation based on code changes
- Git branch and commit control (with user permission)

## Agent Roles and Capabilities

Hive Mind supports multiple specialized agent roles:

### Manager Agent

**Purpose**: Orchestrate team activities, manage communication flow, and ensure task completion.

**Responsibilities**:
- Coordinate activities across team members
- Route messages based on context tags
- Monitor task progress and handle blockers
- Provide status updates to users
- Summarize agent conversations to minimize token usage
- Enforce guard rails and security policies

### Planner Agent

**Purpose**: Define project scope, break down tasks, and create implementation plans.

**Responsibilities**:
- Understand high-level project requirements
- Break projects into manageable tasks
- Define task dependencies and critical paths
- Estimate complexity and budget requirements
- Update plans based on progress and feedback

### Coder Agent

**Purpose**: Write, review, and optimize code.

**Responsibilities**:
- Implement features according to specifications
- Review and refactor existing code
- Fix bugs and address technical debt
- Optimize performance
- Ensure code quality and adherence to standards

### Tester Agent

**Purpose**: Create and execute tests to ensure code quality.

**Responsibilities**:
- Design test plans and cases
- Write unit, integration, and end-to-end tests
- Perform regression testing
- Report bugs and verify fixes
- Measure test coverage

### Domain Expert Agents

These agents provide specialized knowledge in particular domains like:
- Frontend development
- Backend systems
- Security
- Database design
- DevOps
- ML/AI
- Mobile development

## Memory and Knowledge Base

Hive Mind implements a sophisticated memory system for agents:

### Agent Memory System

The system manages:
1. Storage and retrieval of memory entries
2. Semantic search across stored memories
3. Memory importance scoring and decay
4. Cross-agent memory sharing
5. Context-aware memory retrieval

#### Key Components

**MemoryEntry**: A single piece of information with properties like:
- Content
- Metadata
- Importance score
- Vector embedding
- Creation and access timestamps
- Decay rate
- Sharing information

**AgentMemory**: The main class for memory operations:
- Adding, updating, and deleting memories
- Searching for relevant memories
- Calculating memory importance
- Sharing memories between agents
- Applying memory decay over time

#### Features

**Memory Decay Mechanism**: Memories naturally decay in importance over time, following an exponential decay function:
```
decayed_importance = original_importance * exp(-decay_rate * days_passed)
```

**Importance Scoring**: Based on:
- Base importance assigned at creation
- Recency and frequency of access
- Relevance to recent queries
- Explicit importance updates

**Cross-Agent Memory Sharing**: Enables knowledge transfer between agents based on relevance and need-to-know principles.

## User Interface

The Hive Mind UI is built with React, TypeScript, and optionally Tauri for desktop applications. It includes:

### Key Components

- **Login & Authentication**: Secure access control
- **Dashboard**: Overview of teams and activities
- **Team Management**: Creation and configuration of agent teams
- **Workspace UI**: File browser and editor
- **Task Monitoring**: Tracking progress and status
- **Agent Conversation View**: Real-time agent communications
- **Cost Management**: Budget configuration and visualization
- **Settings & Preferences**: System configuration

### Implementation Status

Phase 2 of the project (UI and User Experience) has been fully implemented, including:
- UI Foundation (React/Tauri setup, authentication, dashboard)
- Workspace UI (file browser, conversation view, task monitoring)
- Cost Management UI (budget configuration, visualization, alerts)
- Advanced UI Features (real-time displays, performance metrics)

### Project Structure

The UI follows a modern React application structure:
- `src/components/`: Reusable UI components
- `src/pages/`: Main application pages
- `src/services/`: API, WebSocket, and Auth services
- `src/hooks/`: Custom React hooks
- `src/utils/`: Utility functions and helpers
- `src/styles/`: CSS and styling files

## Infrastructure and Deployment

Hive Mind is designed to run on Google Cloud Platform (GCP) with a focus on security, scalability, and cost-effectiveness.

### GCP Infrastructure (Terraform)

#### VPC and Networking
- Dedicated VPC with appropriate subnets
- Cloud NAT for outbound traffic
- Firewall rules to restrict egress to approved LLM APIs
- Private Service Connect for GKE
- Cloud DNS zones

#### GKE Cluster
- GKE Autopilot for managed Kubernetes
- Workload Identity for secure service account access
- VPC-native networking
- Node auto-provisioning
- Binary Authorization

#### Cloud Storage
- Storage buckets for ephemeral workspaces
- Lifecycle policies for automatic cleanup
- Bucket-level permissions
- FUSE configuration for pod mounting

#### Pub/Sub
- Topics for team events, agent logs, and billing alerts
- Subscriptions with appropriate retention
- Dead-letter topics

### Local Development

For local development, the system can run entirely in Docker Compose:

```yaml
services:
  control-plane:
    build: ./control-plane
    ports:
      - "5000:5000"
    environment:
      - DATABASE_URL=postgresql://postgres:postgres@db:5432/hivemind
      - RABBITMQ_URL=amqp://guest:guest@rabbitmq:5672/
      - QDRANT_URL=http://qdrant:6333
    volumes:
      - ./control-plane:/app
      - ./workspaces:/workspaces

  db:
    image: postgres:14
    environment:
      - POSTGRES_PASSWORD=postgres
      - POSTGRES_DB=hivemind
    volumes:
      - postgres_data:/var/lib/postgresql/data

  rabbitmq:
    image: rabbitmq:3-management
    ports:
      - "15672:15672"
      - "5672:5672"

  qdrant:
    image: qdrant/qdrant
    ports:
      - "6333:6333"
    volumes:
      - qdrant_data:/qdrant/storage

  agent-worker:
    build: ./agent-sdk
    environment:
      - RABBITMQ_URL=amqp://guest:guest@rabbitmq:5672/
      - CONTROL_PLANE_URL=http://control-plane:5000
    volumes:
      - ./agent-sdk:/app
      - ./workspaces:/workspaces

  cost-domain:
    build: ./cost-domain
    environment:
      - DATABASE_URL=postgresql://postgres:postgres@db:5432/hivemind
      - CONTROL_PLANE_URL=http://control-plane:5000
    volumes:
      - ./cost-domain:/app

  task-orchestrator:
    build: ./task-orchestrator
    environment:
      - RABBITMQ_URL=amqp://guest:guest@rabbitmq:5672/
      - CONTROL_PLANE_URL=http://control-plane:5000
      - DATABASE_URL=postgresql://postgres:postgres@db:5432/hivemind
    volumes:
      - ./task-orchestrator:/app

  prometheus:
    image: prom/prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./docker/prometheus:/etc/prometheus
      - prometheus_data:/prometheus

  grafana:
    image: grafana/grafana
    ports:
      - "3000:3000"
    volumes:
      - ./docker/grafana:/etc/grafana/provisioning
      - grafana_data:/var/lib/grafana

volumes:
  postgres_data:
  qdrant_data:
  prometheus_data:
  grafana_data:
```

## Development Workflow

### Setup Process

1. Clone the repository
```bash
git clone https://github.com/your-org/hive-mind.git
cd hive-mind
```

2. Create a virtual environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies
```bash
pip install -r requirements.txt
```

4. Configure environment variables
```bash
cp .env.example .env
# Edit .env with API keys and settings
```

5. Start the system with Docker Compose
```bash
docker-compose up -d
```

### Running the UI

1. Install UI dependencies
```bash
cd ui
npm install
```

2. Start the development server
```bash
npm run dev
```

The UI will be available at http://localhost:3000.

### Testing

The project includes comprehensive test suites:

- Unit tests for individual components
- Integration tests for agent interactions
- End-to-end tests for complete workflows
- Load tests for performance benchmarking

Run tests with:
```bash
pytest
```

### Contributing New Agent Types

To add a new agent type:

1. Create a new class that inherits from BaseAgent
2. Implement required abstract methods (process_message, generate_prompt)
3. Add specialized tools for the agent's domain
4. Register the agent type in the agent factory
5. Update documentation and tests

## API References

### Control Plane API

#### Team Management
- `POST /teams`: Create a new team
- `GET /teams`: List all teams
- `GET /teams/{team_id}`: Get team details
- `PUT /teams/{team_id}`: Update team configuration
- `DELETE /teams/{team_id}`: Delete a team

#### Task Management
- `POST /tasks`: Create a new task
- `GET /tasks`: List all tasks
- `GET /tasks/{task_id}`: Get task details
- `PUT /tasks/{task_id}`: Update task status
- `DELETE /tasks/{task_id}`: Delete a task

#### VS Code Integration
- `POST /api/vscode/register`: Register a new VS Code client
- `GET /api/vscode/clients`: List all registered clients
- `GET /api/vscode/client/{client_id}`: Get client details
- `POST /api/vscode/permission`: Update permission for a client
- `POST /api/vscode/checkout`: Change Git branch/commit for a client
- `POST /api/vscode/send-message/{client_id}`: Send a message to a client
- `GET /api/vscode/file-changes/{client_id}`: Get file changes for a client

### WebSocket Events

- `checkout`: Command to checkout a branch/commit
- `checkout-result`: Result of a checkout operation
- `request-permission`: Request permission from the client
- `permission-response`: Client's response to a permission request
- `file-changes`: File changes sent from VS Code
- `user-message`: Message sent to the VS Code client
- `agent-message`: Message from an agent to a client
- `task-update`: Update about a task status change
- `budget-alert`: Alert about budget threshold reached

## Implementation Guide

### Phase 1: Core Framework

1. Implement BaseAgent class
2. Create the feedback loop mechanism
3. Develop the Manager Agent
4. Implement basic tools (File, Exec, Git)
5. Build the Control Plane API
6. Set up the Task Orchestrator

### Phase 2: UI and User Experience

1. Set up React/Tauri project structure
2. Implement authentication in UI
3. Create main dashboard layout
4. Design and implement team creation interface
5. Set up WebSocket connections for real-time data
6. Create file browser/editor component
7. Implement agent conversation view
8. Build workspace visualization tools
9. Add task monitoring interface
10. Design and implement settings panel
11. Create budget configuration interface
12. Build cost visualization dashboards
13. Implement budget alert notifications
14. Add token usage reporting
15. Create model tier selection interface
16. Implement real-time agent conversation display
17. Create task dependency visualization
18. Build team performance metrics dashboard
19. Add file diff viewer for code changes
20. Implement user preference management

### Phase 3: Infrastructure & Cloud Deployment

1. Implement Terraform infrastructure
2. Set up GKE cluster
3. Configure Cloud Storage
4. Set up Pub/Sub topics and subscriptions
5. Implement CI/CD pipelines
6. Set up monitoring and alerting
7. Configure logging and diagnostics
8. Implement backup and recovery
9. Set up secret management
10. Configure network security

### Phase 4: Advanced Features

1. Implement the Inter-Team Communication Layer
2. Add specialized domain expert agents
3. Implement advanced memory features
4. Add support for more LLM providers
5. Implement fine-tuning pipelines for agent models
6. Add support for more development environments
7. Implement knowledge base integration
8. Add external tool integrations
9. Implement advanced cost optimization strategies
10. Add support for custom workflows and pipelines

## Conclusion

Hive Mind represents a significant advancement in LLM-based software development assistance. By creating teams of specialized agents that can collaborate effectively, manage resources efficiently, and integrate seamlessly with existing development workflows, the platform offers a powerful new paradigm for AI-assisted software engineering.

The documentation provided here should serve as a comprehensive guide to understanding the system architecture, components, and implementation details, enabling developers to extend and enhance the platform for their specific needs. 