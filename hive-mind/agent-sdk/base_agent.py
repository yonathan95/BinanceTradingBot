from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Callable
from pydantic import BaseModel
import time
import uuid

class Message(BaseModel):
    """Represents a message exchanged between agents"""
    sender: str
    recipients: List[str]
    context_tags: List[str]
    message_type: str
    content: str
    priority: str = "normal"
    requires_response: bool = False
    thread_id: Optional[str] = None

    def __init__(self, **data):
        super().__init__(**data)
        if self.thread_id is None:
            self.thread_id = str(uuid.uuid4())

class AgentTool(BaseModel):
    """Base class for tools that agents can use"""
    name: str
    description: str
    parameters: Dict[str, Any]
    
    async def execute(self, **kwargs):
        """Execute the tool with the given parameters"""
        raise NotImplementedError("Tool subclasses must implement execute")

class TaskStatus(BaseModel):
    """Represents the status of a task in a feedback loop"""
    task_id: str
    status: str  # "not_started", "in_progress", "review", "completed", "failed"
    assigned_to: str
    feedback: List[str] = []
    iterations: int = 0
    max_iterations: int = 5
    success_criteria: Dict[str, Any] = {}

class ValidationResult(BaseModel):
    """Result of a validation operation in a feedback loop"""
    success: bool
    feedback: str

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
    
    async def send_message(self, 
                     recipients: List[str], 
                     content: str, 
                     context_tags: List[str], 
                     message_type: str,
                     priority: str = "normal", 
                     requires_response: bool = False,
                     thread_id: str = None) -> Message:
        """Create and send a message to the specified recipients"""
        message = Message(
            sender=self.agent_id,
            recipients=recipients,
            context_tags=context_tags,
            message_type=message_type,
            content=content,
            priority=priority,
            requires_response=requires_response,
            thread_id=thread_id
        )
        return message
    
    async def call_llm(self, prompt: str, stream: bool = False) -> Dict[str, Any]:
        """Call the configured LLM model with retry logic"""
        attempts = 0
        while attempts < self.max_retries:
            try:
                # This would be replaced with actual LLM client code
                # For example: response = await openai.chat.completions.create(...)
                # Mock implementation for now
                response = {
                    "content": f"This is a mock response from {self.model}",
                    "token_usage": {
                        "prompt_tokens": len(prompt) // 4,
                        "completion_tokens": 50,
                        "total_tokens": len(prompt) // 4 + 50
                    }
                }
                
                # Update token count
                self.token_count += response["token_usage"]["total_tokens"]
                
                return response
            except Exception as e:
                attempts += 1
                if attempts < self.max_retries:
                    # Exponential backoff
                    wait_time = self.retry_delay * (2 ** (attempts - 1))
                    time.sleep(wait_time)
                else:
                    raise e
    
    def create_task(self, task_id: str, assigned_to: str, 
                   success_criteria: Dict[str, Any], max_iterations: int = 5):
        """Create a new task for the feedback loop"""
        self.tasks[task_id] = TaskStatus(
            task_id=task_id,
            status="not_started",
            assigned_to=assigned_to,
            success_criteria=success_criteria,
            max_iterations=max_iterations
        )
        
    def start_task(self, task_id: str):
        """Start a task in the feedback loop"""
        if task_id in self.tasks:
            self.tasks[task_id].status = "in_progress"
            
    async def submit_for_review(self, task_id: str, submission: Dict[str, Any],
                         validator: Callable[[Dict[str, Any], Dict[str, Any]], ValidationResult]):
        """Submit a task for review in the feedback loop"""
        if task_id not in self.tasks:
            return {"error": "Task not found"}
            
        task = self.tasks[task_id]
        task.status = "review"
        
        # Run validation
        validation_result = validator(submission, task.success_criteria)
        
        if validation_result.success:
            task.status = "completed"
            return {"status": "completed", "message": "Task completed successfully"}
        else:
            task.feedback.append(validation_result.feedback)
            task.iterations += 1
            
            if task.iterations >= task.max_iterations:
                task.status = "failed"
                return {"status": "failed", "message": "Max iterations reached", "feedback": validation_result.feedback}
            else:
                task.status = "in_progress"
                return {"status": "feedback", "message": "Revisions needed", "feedback": validation_result.feedback}
    
    def get_task_status(self, task_id: str) -> Optional[TaskStatus]:
        """Get the current status of a task"""
        return self.tasks.get(task_id)
    
    def get_token_usage(self) -> int:
        """Get the total token usage for this agent"""
        return self.token_count 