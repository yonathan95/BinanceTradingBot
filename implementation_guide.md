# Hive Mind Implementation Guide

## Implementation Status

The core framework of the Hive Mind system has been implemented, including the BaseAgent, Feedback Loop Framework, Manager Agent, and essential tools. The system can be run locally using Docker Compose for development and testing.

For a detailed status update, see [IMPLEMENTATION_STATUS.md](hive-mind/IMPLEMENTATION_STATUS.md).

## Local Development Setup

### Environment Setup

```bash
# Clone the repository
git clone https://github.com/your-org/hive-mind.git
cd hive-mind

# Set up virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Configuration

Create a `.env` file based on the provided `.env.example`:

```bash
cp .env.example .env
# Edit the .env file with your API keys and settings
```

### Running with Docker Compose

```bash
# Start all services
docker-compose up -d

# Check logs of a specific service
docker-compose logs -f control-plane

# Stop all services
docker-compose down
```

## Core Components Implementation

### 1. Agent Framework

The BaseAgent class serves as the foundation for all agents in the system:

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
        self.tools: List[AgentTool] = []
        self.memory: List[Message] = []
        self.tasks: Dict[str, TaskStatus] = {}
        self.token_count = 0
        
    def add_tool(self, tool: AgentTool):
        """Add a tool to the agent's toolkit"""
        self.tools.append(tool)
    
    async def receive_message(self, message: Message):
        """Process an incoming message and generate a response"""
        self.memory.append(message)
        return await self.process_message(message)
    
    @abstractmethod
    async def process_message(self, message: Message) -> Message:
        """Process a message and generate a response"""
        pass
    
    @abstractmethod
    async def generate_prompt(self, context: Dict[str, Any]) -> str:
        """Generate a prompt for the LLM based on the provided context"""
        pass
```

### 2. Feedback Loop Implementation

The Feedback Loop mechanism allows agents to submit work, receive feedback, and iterate on solutions:

```python
class FeedbackLoop:
    """
    Manages the feedback loop for task validation and improvement
    """
    def __init__(self, validation_function: Callable[[Dict[str, Any], Dict[str, Any]], ValidationResult]):
        """
        Initialize the feedback loop with a validation function
        """
        self.validation_function = validation_function
        self.tasks: Dict[str, TaskStatus] = {}
        
    def create_task(self, 
                   assigned_to: str, 
                   success_criteria: Dict[str, Any], 
                   task_id: Optional[str] = None,
                   max_iterations: int = 5) -> str:
        """Create a new task in the feedback loop"""
        # Implementation details...
        
    def start_task(self, task_id: str) -> bool:
        """Start a task in the feedback loop"""
        # Implementation details...
            
    def submit_for_review(self, task_id: str, submission: Dict[str, Any]) -> Dict[str, Any]:
        """Submit a task for review"""
        # Implementation details...
```

### 3. Manager Agent Implementation

The Manager Agent orchestrates the team's activities, routes messages, and handles the feedback loop process:

```python
class ManagerAgent(BaseAgent):
    """
    Manager Agent that orchestrates the team's activities, routes messages,
    and handles the feedback loop process.
    """
    
    def __init__(self, 
                agent_id: str = "manager", 
                model: str = "gpt-4o", 
                temperature: float = 0.7, 
                token_limit: int = 4096):
        """Initialize the Manager Agent"""
        super().__init__(agent_id, model, temperature, token_limit)
        self.team: Dict[str, BaseAgent] = {}
        self.active_tasks: Dict[str, Dict[str, Any]] = {}
        
    def add_team_member(self, agent: BaseAgent):
        """Add an agent to the team"""
        self.team[agent.agent_id] = agent
        
    async def process_message(self, message: Message) -> Message:
        """Process an incoming message and route it appropriately"""
        # Implementation details...
```

### 4. Tools Implementation

The system includes several tools that agents can use:

#### FileTool
```python
class FileTool(AgentTool):
    """
    Tool for working with files in the agent workspace
    """
    
    def __init__(self, workspace_path: str):
        """Initialize the FileTool with a workspace path"""
        # Implementation details...
    
    async def execute(self, 
                    action: str, 
                    path: str, 
                    content: Optional[str] = None,
                    overwrite: bool = False) -> Dict[str, Any]:
        """Execute file operations"""
        # Implementation details...
```

#### ExecTool
```python
class ExecTool(AgentTool):
    """
    Tool for executing shell commands in a sandboxed environment
    """
    
    # Security features and implementation...
    
    async def execute(self, command: str, timeout: int = 30) -> Dict[str, Any]:
        """Execute a shell command"""
        # Implementation details...
```

### 5. Control Plane API

The Control Plane API provides endpoints for team management, task handling, and WebSocket support:

```python
app = FastAPI(title="Hive Mind Control Plane API")

# Team management endpoints
@app.post("/teams", response_model=TeamResponse)
async def create_team(
    team: TeamCreate, 
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Create a new team with the specified configuration"""
    # Implementation details...

# Task management endpoints
@app.post("/tasks", response_model=TaskResponse)
async def create_task(
    task: TaskCreate, 
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Create a new task"""
    # Implementation details...

# WebSocket connections
@app.websocket("/ws/events")
async def events_websocket(websocket: WebSocket):
    """WebSocket endpoint for real-time events"""
    # Implementation details...
```

### 6. Task Orchestrator

The Task Orchestrator handles task assignment, dependency resolution, and model tier selection:

```python
class TaskOrchestrator:
    """
    Task Orchestrator & Tier Router for the Hive Mind system.
    Handles task assignment, dependency resolution, and model tier selection.
    """
    
    def __init__(self, redis_url: str, tier_config_path: str = "config/tiers.yaml"):
        """Initialize the Task Orchestrator"""
        # Implementation details...
    
    async def create_task(self, task_data: Dict[str, Any]) -> str:
        """Create a new task"""
        # Implementation details...
    
    async def choose_tier(self, complexity: str, budget: float) -> str:
        """Choose the appropriate tier based on task complexity and budget"""
        # Implementation details...
    
    async def assign_task(self, task_data: Dict[str, Any]) -> str:
        """Assign a task to the most appropriate agent"""
        # Implementation details...
```

## Next Steps

The next phase of implementation will focus on:

1. Creating the remaining agent roles (Planner, Coder, Tester)
2. Implementing the Cost Domain Manager
3. Building the UI for user interaction
4. Creating comprehensive tests
5. Deploying to Google Cloud Platform

See the [Development Roadmap](project%20planing/developmentRoadmap.md) for the full development plan. 