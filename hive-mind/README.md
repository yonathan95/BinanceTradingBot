# Hive Mind

A GCP-based multi-agent engineering platform where users can spin up "AI product teams" composed of specialized LLM agents that collaborate to accomplish tasks.

## Overview

Hive Mind allows you to create teams of AI agents, each with a specific role (Planner, Architect, Coder, Tester, etc.), that work together in a shared environment to complete tasks. The system features:

- **Team Builder**: Create and configure teams with specific agent roles
- **Feedback Loop**: Agents iterate on tasks until success criteria are met
- **Cost Management**: Budget controls and model tier selection
- **Task Orchestration**: Smart task assignment based on complexity and budget
- **Agent Memory**: Long-term memory using vector embeddings for contextual assistance

## Features

- **Agent Framework**: Foundation for creating specialized agents with different roles
- **Feedback Loop**: Validation, iteration, and improvement cycle for tasks
- **Smart Tasking**: Tier-based model selection for cost efficiency
- **Cost Tracking**: Budget management and spending monitoring
- **Local Development**: Run the full system on your local machine with Docker
- **Memory System**: Vector-based memory for agents to recall past interactions and knowledge

## Architecture

The system consists of several key components:

- **Control Plane**: FastAPI service for managing teams, tasks, and agent communication
- **Agent SDK**: Base classes and utilities for building agents
- **Task Orchestrator**: Assigns tasks to agents based on complexity and budget
- **Cost Domain Manager**: Tracks and enforces budget constraints
- **Tools**: File operations, shell command execution, etc.
- **Vector Memory**: Stores and retrieves relevant context using semantic similarity

## Getting Started

### Prerequisites

- [Docker](https://www.docker.com/get-started) and Docker Compose
- Python 3.11+
- Node.js 18+

### Local Development

1. Clone the repository:
   ```bash
   git clone https://github.com/your-org/hive-mind.git
   cd hive-mind
   ```

2. Set up environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your API keys and settings
   ```

3. Start the services with Docker Compose:
   ```bash
   docker-compose up -d
   ```

4. Access the services:
   - Control Plane API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs
   - UI (when implemented): http://localhost:3000
   - RabbitMQ Management: http://localhost:15672
   - Prometheus: http://localhost:9090
   - Grafana: http://localhost:3001

## Project Structure

```
hive-mind/
├── agent-sdk/            # Agent framework and utilities
├── agents/               # Agent implementations
├── control-plane/        # FastAPI Control Plane service
├── cost-domain/          # Cost Domain Manager service
├── docker/               # Docker configurations
├── docs/                 # Documentation
├── infra/                # Terraform infrastructure code
├── task-orchestrator/    # Task Orchestrator & Tier Router
├── tests/                # Test suite
├── tools/                # Tool implementations
├── ui/                   # React/Tauri UI
├── docker-compose.yml    # Local development setup
├── requirements.txt      # Python dependencies
└── README.md             # This file
```

## Agent Roles

The system supports various agent roles, including:

- **Manager**: Orchestrates the team and handles communication
- **Planner**: Breaks down projects into tasks and creates strategic plans
- **Architect**: Designs system architecture and makes technology decisions
- **Coder**: Implements features according to specifications
- **Tester**: Verifies code quality and tests implementations

## Agent Memory System

Hive Mind includes a sophisticated memory system for agents:

- **Semantic Search**: Find relevant past information using vector embeddings
- **Contextual Retrieval**: Provide agents with context from previous interactions
- **Memory Types**: Store code snippets, task information, conversations, and more
- **Importance Scoring**: Prioritize memories based on relevance and importance
- **Integration**: Seamlessly incorporated into the agent workflow

Read more about the [Agent Memory System](docs/agent_memory_system.md).

## Development Status

This project is currently in active development:

- [x] BaseAgent implementation
- [x] Feedback Loop Framework
- [x] Manager Agent
- [x] Planner Agent
- [x] Coder Agent
- [x] Tester Agent
- [x] Core Tools (File, Exec)
- [x] Control Plane API
- [x] Task Orchestrator
- [x] Agent Memory System
- [ ] Cost Domain Manager
- [ ] Inter-Team Communication Layer
- [ ] UI
- [ ] Documentation Agent

## Contributing

Contributions are welcome! Please check the [CONTRIBUTING.md](CONTRIBUTING.md) file for guidelines.

## License

This project is licensed under the [MIT License](LICENSE).

## Acknowledgements

- OpenAI and Anthropic for providing the underlying LLM models
- The open-source community for tools and libraries that make this possible 