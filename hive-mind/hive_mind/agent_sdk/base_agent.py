from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Callable, Tuple
from pydantic import BaseModel
import time
import uuid
import logging

from .agent_memory import AgentMemory

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
                 retry_delay: float = 1.0,
                 memory_enabled: bool = True,
                 embedding_model: str = "text-embedding-ada-002",
                 vector_db_url: Optional[str] = None,
                 local_memory_mode: bool = True):
        self.agent_id = agent_id
        self.model = model
        self.temperature = temperature
        self.token_limit = token_limit
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.tools: List[AgentTool] = []
        self.message_history: List[Message] = []
        self.tasks: Dict[str, TaskStatus] = {}
        self.token_count = 0
        
        # Initialize memory system if enabled
        self.memory_enabled = memory_enabled
        if memory_enabled:
            self.memory = AgentMemory(
                embedding_model=embedding_model,
                vector_db_url=vector_db_url,
                local_mode=local_memory_mode
            )
            logger.info(f"Memory system initialized for agent {agent_id}")
        else:
            self.memory = None
            logger.info(f"Memory system disabled for agent {agent_id}")
        
    def add_tool(self, tool: AgentTool):
        """Add a tool to the agent's toolkit"""
        self.tools.append(tool)
    
    async def receive_message(self, message: Message):
        """Process an incoming message and generate a response"""
        self.message_history.append(message)
        
        # Store message in memory if enabled
        if self.memory_enabled:
            metadata = {
                "sender": message.sender,
                "recipients": message.recipients,
                "context_tags": message.context_tags,
                "message_type": message.message_type,
                "thread_id": message.thread_id,
                "timestamp": time.time()
            }
            
            # Determine importance based on message properties
            importance = 1.0  # Default importance
            if message.priority == "high":
                importance += 1.0
            
            # Store in memory
            await self.memory.add_memory(
                content=message.content,
                metadata=metadata,
                importance=importance
            )
            
        return await self.process_message(message)
    
    @abstractmethod
    async def process_message(self, message: Message) -> Message:
        """Process a message and generate a response"""
        pass
    
    @abstractmethod
    async def generate_prompt(self, context: Dict[str, Any]) -> str:
        """Generate a prompt for the LLM based on the provided context"""
        pass
    
    async def retrieve_relevant_memories(self, query: str, 
                                   max_memories: int = 5) -> List[str]:
        """
        Retrieve memories relevant to the current context.
        
        Args:
            query: The query to search for relevant memories
            max_memories: Maximum number of memories to retrieve
            
        Returns:
            List of relevant memory contents
        """
        if not self.memory_enabled:
            return []
            
        return await self.memory.get_semantic_context(
            query=query,
            max_entries=max_memories,
            importance_threshold=0.0
        )
    
    async def build_context_with_memory(self, 
                                  query: str, 
                                  max_memories: int = 5,
                                  recent_message_count: int = 3) -> Dict[str, Any]:
        """
        Build a context dictionary that includes relevant memories.
        
        Args:
            query: The context query for retrieving memories
            max_memories: Maximum number of memories to include
            recent_message_count: Number of recent messages to include
            
        Returns:
            Context dictionary with recent_messages and relevant_memories
        """
        # Get recent messages
        recent_messages = self.message_history[-recent_message_count:] if len(self.message_history) > 0 else []
        
        # Get relevant memories if memory is enabled
        relevant_memories = []
        if self.memory_enabled:
            relevant_memories = await self.retrieve_relevant_memories(query, max_memories)
            
        return {
            "recent_messages": recent_messages,
            "relevant_memories": relevant_memories
        }
    
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
        
        # Store outgoing message in memory if enabled
        if self.memory_enabled:
            metadata = {
                "sender": self.agent_id,
                "recipients": recipients,
                "context_tags": context_tags,
                "message_type": message_type,
                "thread_id": thread_id if thread_id else str(uuid.uuid4()),
                "timestamp": time.time(),
                "outgoing": True
            }
            
            # Determine importance based on message properties
            importance = 1.0  # Default importance
            if priority == "high":
                importance += 1.0
            
            # Store in memory
            await self.memory.add_memory(
                content=content,
                metadata=metadata,
                importance=importance
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
                
                # Store the interaction in memory if enabled
                if self.memory_enabled:
                    metadata = {
                        "interaction_type": "llm_call",
                        "model": self.model,
                        "temperature": self.temperature,
                        "timestamp": time.time(),
                        "tokens": response["token_usage"]["total_tokens"]
                    }
                    
                    # Store prompt with moderate importance
                    await self.memory.add_memory(
                        content=f"PROMPT: {prompt}",
                        metadata=metadata,
                        importance=1.0
                    )
                    
                    # Store response with higher importance (as it's the actual knowledge)
                    await self.memory.add_memory(
                        content=f"RESPONSE: {response['content']}",
                        metadata=metadata,
                        importance=2.0
                    )
                
                return response
            except Exception as e:
                attempts += 1
                if attempts < self.max_retries:
                    # Exponential backoff
                    wait_time = self.retry_delay * (2 ** (attempts - 1))
                    time.sleep(wait_time)
                else:
                    # Log the error
                    logger.error(f"LLM call failed after {self.max_retries} attempts: {str(e)}")
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
        
        # Store task submission and feedback in memory if enabled
        if self.memory_enabled:
            # Store submission
            submission_metadata = {
                "task_id": task_id,
                "iteration": task.iterations,
                "timestamp": time.time(),
                "type": "task_submission"
            }
            
            # Convert submission dict to a string representation
            submission_str = str(submission)
            
            await self.memory.add_memory(
                content=f"TASK SUBMISSION ({task_id}, iteration {task.iterations}): {submission_str}",
                metadata=submission_metadata,
                importance=3.0  # Higher importance for task submissions
            )
            
            # Store feedback if provided
            if validation_result and validation_result.feedback:
                feedback_metadata = {
                    "task_id": task_id,
                    "iteration": task.iterations,
                    "timestamp": time.time(),
                    "success": validation_result.success,
                    "type": "task_feedback"
                }
                
                await self.memory.add_memory(
                    content=f"TASK FEEDBACK ({task_id}, iteration {task.iterations}): {validation_result.feedback}",
                    metadata=feedback_metadata,
                    importance=3.5  # Even higher importance for feedback
                )
        
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

    async def remember_tool_use(self, tool_name: str, 
                          parameters: Dict[str, Any], 
                          result: Any) -> None:
        """
        Store tool usage in memory.
        
        Args:
            tool_name: Name of the tool used
            parameters: Parameters passed to the tool
            result: Result returned by the tool
        """
        if not self.memory_enabled:
            return
            
        # Create memory entry for tool usage
        metadata = {
            "tool_name": tool_name,
            "parameters": parameters,
            "timestamp": time.time(),
            "type": "tool_usage"
        }
        
        # Convert parameters and result to strings if they aren't already
        params_str = str(parameters)
        result_str = str(result)
        
        content = f"TOOL USE: {tool_name}\nParameters: {params_str}\nResult: {result_str}"
        
        # Store with relatively high importance
        await self.memory.add_memory(
            content=content,
            metadata=metadata,
            importance=2.5
        ) 