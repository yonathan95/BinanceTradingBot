"""
VS Code Change Handler for Manager Agent

This module handles the file changes coming from VS Code extensions and determines
appropriate actions based on the changes.
"""

import logging
import json
import os
from typing import Dict, List, Any, Optional
import asyncio

logger = logging.getLogger(__name__)

class VSCodeChangeHandler:
    """
    Handler for VS Code file changes that integrates with the Manager Agent
    """
    
    def __init__(self, manager_agent):
        """
        Initialize the VS Code change handler
        
        Args:
            manager_agent: The manager agent instance to interface with
        """
        self.manager_agent = manager_agent
        self.active_tasks = {}  # Map of client_id to active tasks
        self.pending_changes = {}  # Map of client_id to pending changes
        self.last_processed = {}  # Timestamp of last processed change per client
    
    async def process_file_changes(self, message: Dict[str, Any]) -> None:
        """
        Process file changes from VS Code
        
        Args:
            message: The message containing file changes
        """
        try:
            client_id = message.get('client_id')
            changes = message.get('changes', [])
            workspace_name = message.get('workspace_name')
            timestamp = message.get('timestamp')
            
            if not client_id or not changes:
                logger.warning(f"Incomplete message received: {message}")
                return
            
            logger.info(f"Processing {len(changes)} file changes from client {client_id}")
            
            # Store pending changes
            if client_id not in self.pending_changes:
                self.pending_changes[client_id] = []
            
            self.pending_changes[client_id].extend(changes)
            
            # Debounce processing to avoid overloading the system
            # Process after a short delay with no new changes
            if client_id in self.last_processed:
                # If we've recently processed changes, wait for more before processing again
                return
            
            self.last_processed[client_id] = timestamp
            
            # Schedule processing after a delay
            asyncio.create_task(self._delayed_process(client_id))
            
        except Exception as e:
            logger.error(f"Error processing VS Code file changes: {str(e)}")
    
    async def _delayed_process(self, client_id: str, delay_seconds: int = 5) -> None:
        """
        Process pending changes after a delay
        
        Args:
            client_id: The client ID to process changes for
            delay_seconds: Delay in seconds before processing
        """
        await asyncio.sleep(delay_seconds)
        
        try:
            if client_id not in self.pending_changes or not self.pending_changes[client_id]:
                logger.info(f"No pending changes to process for client {client_id}")
                self.last_processed.pop(client_id, None)
                return
            
            changes = self.pending_changes[client_id]
            self.pending_changes[client_id] = []
            
            # Analyze changes to determine if they're part of an active task
            related_task_id = await self._identify_related_task(client_id, changes)
            
            if related_task_id:
                # Changes are related to an active task
                await self._process_task_related_changes(client_id, related_task_id, changes)
            else:
                # Changes are not related to an active task
                await self._process_new_changes(client_id, changes)
            
            # Clean up
            self.last_processed.pop(client_id, None)
            
        except Exception as e:
            logger.error(f"Error in delayed processing for client {client_id}: {str(e)}")
            self.last_processed.pop(client_id, None)
    
    async def _identify_related_task(self, client_id: str, changes: List[Dict[str, Any]]) -> Optional[str]:
        """
        Identify if the changes are related to an active task
        
        Args:
            client_id: The client ID
            changes: The list of file changes
            
        Returns:
            Task ID if related to an active task, None otherwise
        """
        # Check if the client has an active task
        if client_id in self.active_tasks:
            return self.active_tasks[client_id]
        
        # Get active tasks from the manager agent
        active_tasks = await self.manager_agent.get_active_tasks()
        
        # Here we would implement logic to determine if changes match any active task
        # This could involve looking at file paths, task metadata, etc.
        # For now, we'll return None indicating no related task was found
        
        return None
    
    async def _process_task_related_changes(self, client_id: str, task_id: str, changes: List[Dict[str, Any]]) -> None:
        """
        Process changes related to an active task
        
        Args:
            client_id: The client ID
            task_id: The related task ID
            changes: The list of file changes
        """
        logger.info(f"Processing changes related to task {task_id} for client {client_id}")
        
        # Create a summary of the changes
        summary = self._create_changes_summary(changes)
        
        # Update the task with the changes
        await self.manager_agent.update_task_with_changes(task_id, summary, changes)
        
        # Send a message to the VS Code client
        await self._send_message_to_client(
            client_id,
            f"Your changes have been processed and associated with task '{task_id}'. The agent team is reviewing them."
        )
    
    async def _process_new_changes(self, client_id: str, changes: List[Dict[str, Any]]) -> None:
        """
        Process changes not related to an active task
        
        Args:
            client_id: The client ID
            changes: The list of file changes
        """
        logger.info(f"Processing new changes for client {client_id}")
        
        # Create a summary of the changes
        summary = self._create_changes_summary(changes)
        
        # Ask the manager agent to evaluate the changes
        response = await self.manager_agent.evaluate_new_changes(client_id, summary, changes)
        
        if response.get('create_task', False):
            # Manager decided to create a new task
            task_id = response.get('task_id')
            if task_id:
                self.active_tasks[client_id] = task_id
                await self._send_message_to_client(
                    client_id,
                    f"Based on your changes, a new task '{task_id}' has been created. The agent team is analyzing your changes."
                )
        else:
            # Just acknowledge the changes
            await self._send_message_to_client(
                client_id,
                "Your changes have been recorded. No immediate action is required."
            )
    
    def _create_changes_summary(self, changes: List[Dict[str, Any]]) -> str:
        """
        Create a human-readable summary of file changes
        
        Args:
            changes: The list of file changes
            
        Returns:
            A summary string
        """
        if not changes:
            return "No changes detected"
        
        modified_files = [c['path'] for c in changes if c['event'] == 'change']
        deleted_files = [c['path'] for c in changes if c['event'] == 'delete']
        
        summary_parts = []
        
        if modified_files:
            summary_parts.append(f"Modified {len(modified_files)} file(s): {', '.join(modified_files[:5])}")
            if len(modified_files) > 5:
                summary_parts[-1] += f" and {len(modified_files) - 5} more"
        
        if deleted_files:
            summary_parts.append(f"Deleted {len(deleted_files)} file(s): {', '.join(deleted_files[:5])}")
            if len(deleted_files) > 5:
                summary_parts[-1] += f" and {len(deleted_files) - 5} more"
        
        return ". ".join(summary_parts)
    
    async def _send_message_to_client(self, client_id: str, message: str) -> None:
        """
        Send a message to the VS Code client
        
        Args:
            client_id: The client ID
            message: The message to send
        """
        try:
            # This would be implemented to call the VS Code API
            # For now, we'll just log it
            logger.info(f"Would send message to client {client_id}: {message}")
            
            # In a real implementation, we'd do something like:
            # await self.manager_agent.send_vscode_message(client_id, message)
        except Exception as e:
            logger.error(f"Error sending message to client {client_id}: {str(e)}")
    
    def register_client_task(self, client_id: str, task_id: str) -> None:
        """
        Register an active task for a client
        
        Args:
            client_id: The client ID
            task_id: The task ID
        """
        self.active_tasks[client_id] = task_id
        logger.info(f"Registered task {task_id} for client {client_id}")
    
    def unregister_client_task(self, client_id: str) -> None:
        """
        Unregister an active task for a client
        
        Args:
            client_id: The client ID
        """
        if client_id in self.active_tasks:
            task_id = self.active_tasks.pop(client_id)
            logger.info(f"Unregistered task {task_id} for client {client_id}") 