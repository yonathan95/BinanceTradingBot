from typing import List, Dict, Any, Callable, Optional
from pydantic import BaseModel
from datetime import datetime
import uuid

class TaskStatus(BaseModel):
    """
    Represents the status of a task in the feedback loop
    """
    task_id: str
    status: str  # "not_started", "in_progress", "review", "completed", "failed"
    assigned_to: str
    feedback: List[str] = []
    iterations: int = 0
    max_iterations: int = 5
    success_criteria: Dict[str, Any] = {}
    created_at: datetime = datetime.utcnow()
    updated_at: datetime = datetime.utcnow()
    
    def update_status(self, status: str):
        """
        Update the status of the task
        """
        self.status = status
        self.updated_at = datetime.utcnow()

class ValidationResult(BaseModel):
    """
    Result of a validation operation
    """
    success: bool
    feedback: str
    
    @classmethod
    def success_result(cls, message: str = "Validation passed"):
        """
        Create a successful validation result
        """
        return cls(success=True, feedback=message)
    
    @classmethod
    def failure_result(cls, feedback: str):
        """
        Create a failed validation result with feedback
        """
        return cls(success=False, feedback=feedback)

class FeedbackLoop:
    """
    Manages the feedback loop for task validation and improvement
    """
    def __init__(self, validation_function: Callable[[Dict[str, Any], Dict[str, Any]], ValidationResult]):
        """
        Initialize the feedback loop with a validation function
        
        Args:
            validation_function: Function that validates a submission against success criteria
                                The function should take (submission, success_criteria) and return a ValidationResult
        """
        self.validation_function = validation_function
        self.tasks: Dict[str, TaskStatus] = {}
        
    def create_task(self, 
                   assigned_to: str, 
                   success_criteria: Dict[str, Any], 
                   task_id: Optional[str] = None,
                   max_iterations: int = 5) -> str:
        """
        Create a new task in the feedback loop
        
        Args:
            assigned_to: ID of the agent assigned to the task
            success_criteria: Criteria that define success for this task
            task_id: Optional task ID (will be generated if not provided)
            max_iterations: Maximum number of iterations allowed
            
        Returns:
            The task ID
        """
        if task_id is None:
            task_id = f"task-{str(uuid.uuid4())}"
            
        self.tasks[task_id] = TaskStatus(
            task_id=task_id,
            status="not_started",
            assigned_to=assigned_to,
            success_criteria=success_criteria,
            max_iterations=max_iterations
        )
        
        return task_id
        
    def start_task(self, task_id: str) -> bool:
        """
        Start a task in the feedback loop
        
        Args:
            task_id: The ID of the task to start
            
        Returns:
            True if the task was started, False if it was not found
        """
        if task_id in self.tasks:
            self.tasks[task_id].update_status("in_progress")
            return True
        return False
            
    def submit_for_review(self, task_id: str, submission: Dict[str, Any]) -> Dict[str, Any]:
        """
        Submit a task for review
        
        Args:
            task_id: The ID of the task to review
            submission: The work to be validated
            
        Returns:
            A dictionary with status and feedback information
        """
        if task_id not in self.tasks:
            return {"error": "Task not found"}
            
        task = self.tasks[task_id]
        task.update_status("review")
        
        # Run validation
        validation_result = self.validation_function(submission, task.success_criteria)
        
        if validation_result.success:
            task.update_status("completed")
            return {
                "status": "completed", 
                "message": "Task completed successfully",
                "iterations": task.iterations
            }
        else:
            task.feedback.append(validation_result.feedback)
            task.iterations += 1
            
            if task.iterations >= task.max_iterations:
                task.update_status("failed")
                return {
                    "status": "failed", 
                    "message": "Max iterations reached", 
                    "feedback": validation_result.feedback,
                    "iterations": task.iterations
                }
            else:
                task.update_status("in_progress")
                return {
                    "status": "feedback", 
                    "message": "Revisions needed", 
                    "feedback": validation_result.feedback,
                    "iterations": task.iterations
                }
    
    def get_task_status(self, task_id: str) -> Optional[TaskStatus]:
        """
        Get the current status of a task
        
        Args:
            task_id: The ID of the task
            
        Returns:
            The TaskStatus object or None if not found
        """
        return self.tasks.get(task_id)
    
    def get_all_tasks(self) -> Dict[str, TaskStatus]:
        """
        Get all tasks in the feedback loop
        
        Returns:
            Dictionary of all tasks
        """
        return self.tasks
    
    def get_tasks_by_status(self, status: str) -> Dict[str, TaskStatus]:
        """
        Get tasks filtered by status
        
        Args:
            status: The status to filter by
            
        Returns:
            Dictionary of tasks with the specified status
        """
        return {
            task_id: task for task_id, task in self.tasks.items() 
            if task.status == status
        }
    
    def get_tasks_by_agent(self, agent_id: str) -> Dict[str, TaskStatus]:
        """
        Get tasks assigned to a specific agent
        
        Args:
            agent_id: The ID of the agent
            
        Returns:
            Dictionary of tasks assigned to the agent
        """
        return {
            task_id: task for task_id, task in self.tasks.items() 
            if task.assigned_to == agent_id
        } 