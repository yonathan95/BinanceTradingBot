# Hive Mind Task Breakdown

This document provides detailed technical specifications and requirements for the key components of the Hive Mind platform.

## Core Components

### 1. GCP Infrastructure (Terraform)

#### VPC and Networking
- Create dedicated VPC with appropriate subnets
- Configure Cloud NAT for outbound traffic
- Set up firewall rules to restrict egress to approved LLM APIs
- Implement Private Service Connect for GKE
- Configure Cloud DNS zones

```terraform
module "vpc" {
  source  = "terraform-google-modules/network/google"
  version = "~> 4.0"
  
  network_name = "hive-mind-network"
  project_id   = var.project_id
  
  subnets = [
    {
      subnet_name   = "gke-subnet"
      subnet_ip     = "10.0.0.0/22"
      subnet_region = var.region
    },
    {
      subnet_name   = "services-subnet"
      subnet_ip     = "10.0.4.0/22"
      subnet_region = var.region
    }
  ]
}
```

#### GKE Cluster
- Use GKE Autopilot for managed Kubernetes
- Configure Workload Identity for secure service account access
- Enable VPC-native networking
- Set up node auto-provisioning
- Configure Binary Authorization

```terraform
resource "google_container_cluster" "primary" {
  name     = "hive-mind-cluster"
  location = var.region
  
  enable_autopilot = true
  
  workload_identity_config {
    workload_pool = "${var.project_id}.svc.id.goog"
  }
  
  binary_authorization {
    evaluation_mode = "PROJECT_SINGLETON_POLICY_ENFORCE"
  }
}
```

#### Cloud Storage
- Create storage buckets for ephemeral workspaces
- Set up lifecycle policies for automatic cleanup
- Configure bucket-level permissions
- Set up FUSE configuration for pod mounting

#### Pub/Sub
- Create topics for team events, agent logs, and billing alerts
- Configure subscriptions with appropriate retention
- Set up dead-letter topics

### 2. Agent Framework

#### BaseAgent Class
- Implement abstract base class for all agents
- Add support for persona configuration
- Implement tool registration mechanism
- Add streaming token handling
- Implement context management
- Add rate limiting and retry logic

```python
class BaseAgent:
    def __init__(self, model_config, persona, tools=None):
        self.model_config = model_config
        self.persona = persona
        self.tools = tools or []
        self.context = []
        self.token_count = 0
        
    def register_tool(self, tool):
        self.tools.append(tool)
        
    async def execute(self, message, stream=True):
        """Execute the agent with the given message"""
        # Format context and tools for prompt
        prompt = self._format_prompt(message)
        
        # Call LLM with appropriate model settings
        response = await self._call_llm(prompt, stream)
        
        # Track token usage
        self._update_token_count(response)
        
        # Parse response and handle tool calls
        result = self._parse_response(response)
        
        return result
        
    def _format_prompt(self, message):
        # Implementation details
        pass
        
    async def _call_llm(self, prompt, stream):
        # Implementation details
        pass
```

#### Tool Implementation
- Create base Tool interface
- Implement FileTool for workspace operations
- Build ExecTool for running shell commands
- Create SearchTool for web access
- Implement UnitTestTool for testing code
- Add SQLTool for database operations

```python
class Tool:
    def __init__(self, name, description):
        self.name = name
        self.description = description
        
    async def execute(self, **params):
        """Execute the tool with the given parameters"""
        raise NotImplementedError("Tool subclasses must implement execute")

class FileTool(Tool):
    def __init__(self, workspace_path):
        super().__init__(
            name="file_tool",
            description="Read, write, and manipulate files in the workspace"
        )
        self.workspace_path = workspace_path
        
    async def execute(self, action, path, content=None):
        """Execute file operations"""
        full_path = os.path.join(self.workspace_path, path)
        
        if action == "read":
            return await self._read_file(full_path)
        elif action == "write":
            return await self._write_file(full_path, content)
        elif action == "list":
            return await self._list_files(full_path)
        else:
            raise ValueError(f"Unknown action: {action}")
```

### 3. Control Plane API

#### FastAPI Implementation
- Create RESTful API for team and agent management
- Implement GraphQL for complex queries
- Add WebSocket support for real-time logs
- Implement authentication middleware
- Add rate limiting and request validation

```python
from fastapi import FastAPI, Depends, HTTPException, WebSocket
from fastapi.security import OAuth2PasswordBearer

app = FastAPI(title="Hive Mind API")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

@app.post("/teams")
async def create_team(team: TeamCreate, token: str = Depends(oauth2_scheme)):
    """Create a new team with the specified configuration"""
    user = await get_current_user(token)
    if not user.has_permission("create_team"):
        raise HTTPException(status_code=403, detail="Not authorized")
    
    team_id = await team_service.create_team(team, user.id)
    return {"team_id": team_id}

@app.websocket("/ws/team/{team_id}/logs")
async def team_logs(websocket: WebSocket, team_id: str):
    """Stream logs for a specific team"""
    await websocket.accept()
    
    # Authenticate
    token = await websocket.receive_text()
    user = await get_current_user(token)
    if not user.has_permission("view_team", team_id):
        await websocket.close(code=1008)
        return
    
    # Subscribe to log topic
    subscription = await pubsub_client.subscribe(f"team-logs-{team_id}")
    
    try:
        # Forward messages to WebSocket
        async for message in subscription:
            await websocket.send_json(message.data)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        await subscription.close()
        await websocket.close()
```

### 4. Cost Domain Manager

#### Budget Model
```python
class Budget:
    def __init__(self, topic, team_id, max_usd, alert_threshold=0.8):
        self.topic = topic
        self.team_id = team_id
        self.max_usd = max_usd
        self.alert_threshold = alert_threshold
        self.current_spend = 0.0
        self.last_updated = datetime.utcnow()
        
    def is_over_threshold(self):
        """Check if spending is over the alert threshold"""
        return self.current_spend >= (self.max_usd * self.alert_threshold)
        
    def is_over_budget(self):
        """Check if spending is over budget"""
        return self.current_spend >= self.max_usd
```

#### Token Tracking
- Implement middleware to track token usage
- Store usage data in BigQuery
- Create aggregation queries for reporting
- Set up webhooks for LLM provider usage events

#### Budget Enforcement
- Create Cloud Function for budget alerts
- Implement auto-pause mechanism
- Add down-tiering logic when approaching budget limits
- Create notification system for budget events

### 5. Task Orchestrator & Tier Router

#### Task Model
```python
class Task:
    def __init__(self, id, goal, complexity, budget, owner_team, dependencies=None):
        self.id = id
        self.goal = goal
        self.complexity = complexity  # "L", "M", or "H"
        self.budget = budget  # Maximum USD for this task
        self.owner_team = owner_team
        self.dependencies = dependencies or []
        self.status = "pending"
        self.assigned_agent = None
        self.created_at = datetime.utcnow()
```

#### Tier Configuration
```yaml
tiers:
  prod_mgmt:
    model: "gpt-3.5-turbo"
    max_tokens: 2048
    temperature: 0.2
    cost_per_1k_tokens: 0.0015
  
  standard:
    model: "gpt-4o"
    max_tokens: 4096
    temperature: 0.7
    cost_per_1k_tokens: 0.01
  
  premium:
    model: "claude-3-opus"
    max_tokens: 8000
    temperature: 0.7
    cost_per_1k_tokens: 0.03

routing_rules:
  - when: complexity == "L"
    use: prod_mgmt
  
  - when: complexity == "M"
    use: standard
  
  - when: complexity == "H" && budget > 5.0
    use: premium
  
  - when: complexity == "H" && budget <= 5.0
    use: standard
```

#### Task Assignment Algorithm
- Implement priority queue for tasks
- Add dependency resolution
- Create agent load balancing logic
- Implement token usage tracking for assignment decisions
- Add support for task splitting and merging

### 6. Inter-Team Communication Layer

#### Message Routing
- Implement tag-based routing (#frontend, #backend, etc.)
- Create team graph for message forwarding
- Add message summarization using economy tier models
- Implement broadcast capability for reviews and announcements

#### Context Management
- Create context pruning to minimize token usage
- Implement vector embeddings for relevant context retrieval
- Add context pinning for critical information
- Create memory mechanisms for long-running tasks

### 7. GUI (Tauri/React)

#### Main Components
- Team Builder: Drag-and-drop interface for creating teams
- Workspace Explorer: File browser and editor
- Conversation View: Real-time agent chat display
- Task Manager: Task creation and monitoring
- Budget Dashboard: Spending visualization and alerts
- Settings: Configuration for agents, teams, and system

#### Desktop Integration
- File system access for local workspaces
- Notification integration
- Offline capability for selected operations
- Local caching of resources

## Testing Strategy

### Unit Testing
- Implement pytest framework for Python components
- Use Jest for React components
- Implement mock LLM responses for deterministic testing
- Add property-based testing for critical components

### Integration Testing
- Create test harness for agent interaction
- Implement end-to-end workflow tests
- Add performance testing for scaling validation
- Create security testing suite

### Evaluation Framework
- Implement automatic evaluation of agent outputs
- Create benchmark suite for common tasks
- Add regression testing to prevent quality degradation
- Implement continuous evaluation pipeline

## Deployment Pipeline

### CI/CD
- Set up Cloud Build for automated builds
- Implement GitHub Actions for testing
- Create deployment pipeline for GKE
- Add canary and blue/green deployment strategies

### Environment Management
- Create dev, staging, and production environments
- Implement environment-specific configuration
- Add secret rotation mechanism
- Create disaster recovery procedures

## Documentation

### Technical Documentation
- Architecture diagrams and explanations
- API references
- Deployment guides
- Security considerations

### User Documentation
- Getting started guides
- Team creation tutorials
- Budget management guides
- Troubleshooting guides 