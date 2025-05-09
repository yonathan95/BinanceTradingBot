"""
Manager Agent - Coordinates other agents and manages task workflows
"""

import logging
import asyncio
import json
import time
from typing import Dict, List, Any, Optional
from .vscode_change_handler import VSCodeChangeHandler

logger = logging.getLogger(__name__)

class ManagerAgent:
    """
    Manager Agent that coordinates other agents, manages task workflows,
    and handles VS Code changes
    """
    
    def __init__(self, agent_controller):
        """
        Initialize the Manager Agent
        
        Args:
            agent_controller: Controller for communicating with other agents
        """
        self.agent_controller = agent_controller
        self.active_tasks = {}  # Map of task_id to task data
        self.task_queue = asyncio.Queue()
        self.running = False
        
        # Initialize VS Code change handler
        self.vscode_handler = VSCodeChangeHandler(self)
    
    async def start(self):
        """Start the Manager Agent processing loop"""
        if self.running:
            logger.warning("Manager Agent is already running")
            return
        
        self.running = True
        logger.info("Manager Agent started")
        
        # Start the main processing loop
        asyncio.create_task(self._process_loop())
    
    async def stop(self):
        """Stop the Manager Agent"""
        self.running = False
        logger.info("Manager Agent stopped")
    
    async def _process_loop(self):
        """Main processing loop for handling tasks"""
        while self.running:
            try:
                # Get the next item from the queue with a timeout
                # This allows us to check self.running periodically
                try:
                    item = await asyncio.wait_for(self.task_queue.get(), timeout=1.0)
                except asyncio.TimeoutError:
                    continue
                
                item_type = item.get('type')
                
                if item_type == 'task':
                    await self._handle_task(item)
                elif item_type == 'vscode_file_changes':
                    await self._handle_vscode_changes(item)
                elif item_type == 'user_message':
                    await self._handle_user_message(item)
                else:
                    logger.warning(f"Unknown item type: {item_type}")
                
                # Mark the task as processed
                self.task_queue.task_done()
                
            except Exception as e:
                logger.error(f"Error in manager processing loop: {str(e)}")
    
    async def _handle_task(self, task_data):
        """
        Handle a new task
        
        Args:
            task_data: Data for the task to handle
        """
        task_id = task_data.get('task_id')
        logger.info(f"Processing task {task_id}")
        
        # Store the task in active tasks
        self.active_tasks[task_id] = task_data
        
        # Determine task type and create a plan
        plan = await self._create_task_plan(task_data)
        
        # Update task with plan
        self.active_tasks[task_id]['plan'] = plan
        
        # Assign subtasks to appropriate agents
        await self._assign_subtasks(task_id, plan)
    
    async def _handle_vscode_changes(self, change_data):
        """
        Handle VS Code file changes
        
        Args:
            change_data: Data about the file changes
        """
        # Forward to the VS Code change handler
        await self.vscode_handler.process_file_changes(change_data)
    
    async def _handle_user_message(self, message_data):
        """
        Handle a message from the user
        
        Args:
            message_data: The message from the user
        """
        client_id = message_data.get('client_id')
        message = message_data.get('message')
        
        logger.info(f"Processing user message from client {client_id}: {message}")
        
        # Determine if this is related to an existing task
        task_id = self.vscode_handler.active_tasks.get(client_id)
        
        if task_id and task_id in self.active_tasks:
            # Update the existing task
            await self._update_task_with_user_message(task_id, message)
        else:
            # Create a new task based on the message
            await self._create_task_from_message(client_id, message)
    
    async def _create_task_plan(self, task_data):
        """
        Create a plan for executing a task
        
        Args:
            task_data: The task data
            
        Returns:
            A plan for the task
        """
        # In a real implementation, this would call the Planner Agent
        # For now, we'll create a simple dummy plan
        return {
            'steps': [
                {'id': 1, 'name': 'Analyze requirements', 'agent': 'planner'},
                {'id': 2, 'name': 'Implement solution', 'agent': 'coder'},
                {'id': 3, 'name': 'Test solution', 'agent': 'tester'}
            ]
        }
    
    async def _assign_subtasks(self, task_id, plan):
        """
        Assign subtasks to appropriate agents
        
        Args:
            task_id: The ID of the parent task
            plan: The plan for the task
        """
        # In a real implementation, this would communicate with other agents
        # For now, we'll just log the assignments
        for step in plan['steps']:
            logger.info(f"Assigning step {step['id']} ({step['name']}) to {step['agent']} agent for task {task_id}")
    
    async def _update_task_with_user_message(self, task_id, message):
        """
        Update a task with a message from the user
        
        Args:
            task_id: The ID of the task to update
            message: The message from the user
        """
        logger.info(f"Updating task {task_id} with user message: {message}")
        
        # In a real implementation, this would update the task and notify agents
    
    async def _create_task_from_message(self, client_id, message):
        """
        Create a new task based on a message from the user
        
        Args:
            client_id: The ID of the client sending the message
            message: The message from the user
        """
        # Generate a task ID
        task_id = f"task-{int(time.time())}"
        
        logger.info(f"Creating new task {task_id} from user message: {message}")
        
        # Create a task data structure
        task_data = {
            'type': 'task',
            'task_id': task_id,
            'client_id': client_id,
            'goal': message,
            'created_at': time.time()
        }
        
        # Store in active tasks
        self.active_tasks[task_id] = task_data
        
        # Register the task with the VS Code handler
        self.vscode_handler.register_client_task(client_id, task_id)
        
        # Queue the task for processing
        await self.task_queue.put(task_data)
        
        # Return the task ID for future reference
        return task_id
    
    async def process_message(self, message):
        """
        Process a message from any source
        
        Args:
            message: The message to process
        """
        # Add the message to the queue for processing
        await self.task_queue.put(message)
    
    async def get_active_tasks(self):
        """
        Get a list of active tasks
        
        Returns:
            A list of active task IDs
        """
        return list(self.active_tasks.keys())
    
    async def update_task_with_changes(self, task_id, summary, changes):
        """
        Update a task with file changes from VS Code
        
        Args:
            task_id: The ID of the task to update
            summary: A summary of the changes
            changes: The file changes
        """
        if task_id not in self.active_tasks:
            logger.warning(f"Cannot update non-existent task {task_id}")
            return
        
        logger.info(f"Updating task {task_id} with file changes: {summary}")
        
        # Add changes to the task
        if 'changes' not in self.active_tasks[task_id]:
            self.active_tasks[task_id]['changes'] = []
        
        self.active_tasks[task_id]['changes'].extend(changes)
        
        # In a real implementation, this would communicate with other agents
    
    async def evaluate_new_changes(self, client_id, summary, changes):
        """
        Evaluate new changes from VS Code to determine if a new task should be created
        
        Args:
            client_id: The ID of the client
            summary: A summary of the changes
            changes: The file changes
            
        Returns:
            A response indicating what to do with the changes
        """
        # In a real implementation, this would use some logic or ML to determine
        # if the changes warrant creating a new task
        
        # For now, always create a new task if there are significant changes
        if len(changes) > 3:
            task_id = await self._create_task_from_message(
                client_id, 
                f"Analyze and respond to code changes: {summary}"
            )
            
            return {
                'create_task': True,
                'task_id': task_id,
                'message': f"Created task {task_id} to analyze your changes"
            }
        else:
            return {
                'create_task': False,
                'message': "Changes noted, but no action required at this time"
            }
    
    async def send_vscode_message(self, client_id, message):
        """
        Send a message to a VS Code client
        
        Args:
            client_id: The ID of the client
            message: The message to send
        """
        # In a real implementation, this would use the VS Code controller
        # to send the message to the client
        logger.info(f"Sending message to VS Code client {client_id}: {message}")
        
        # Call the VS Code controller (this would be implemented elsewhere)
        # await self.agent_controller.send_vscode_message(client_id, message) 