"""
Git-Enabled Agent - Base agent class with Git integration capabilities.
"""

import logging
import os
from typing import Dict, List, Any, Optional, Union, Callable, Awaitable

from hive_mind.agent_sdk.base_agent import BaseAgent, Message
from .agent_git_extension import AgentGitExtension
from .vscode_git_service import VSCodeGitService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GitEnabledAgent(BaseAgent):
    """
    Base agent class with built-in Git integration capabilities.
    
    All agents that need to work with Git should inherit from this class
    instead of directly from BaseAgent.
    """
    
    def __init__(self, 
                agent_id: str, 
                model: str, 
                temperature: float = 0.7, 
                token_limit: int = 4096,
                memory_enabled: bool = True,
                embedding_model: str = "text-embedding-ada-002",
                vector_db_url: Optional[str] = None,
                workspace_path: Optional[str] = None,
                repository_url: Optional[str] = None,
                branch_strategy: str = "gitflow",
                control_plane_url: str = "http://localhost:5000",
                vscode_integration_enabled: bool = False):
        """
        Initialize Git-enabled agent
        
        Args:
            agent_id: Unique identifier for the agent
            model: LLM model to use
            temperature: LLM temperature setting
            token_limit: Maximum token limit for LLM calls
            memory_enabled: Whether to enable memory
            embedding_model: Model to use for embeddings
            vector_db_url: URL for the vector database
            workspace_path: Path to the workspace directory
            repository_url: URL of the git repository
            branch_strategy: Branching strategy to use
            control_plane_url: URL of the Hive Mind control plane
            vscode_integration_enabled: Whether to enable VS Code integration
        """
        super().__init__(
            agent_id=agent_id, 
            model=model, 
            temperature=temperature, 
            token_limit=token_limit,
            memory_enabled=memory_enabled,
            embedding_model=embedding_model,
            vector_db_url=vector_db_url
        )
        
        # Initialize Git extension
        self.git_extension = AgentGitExtension(
            agent=self,
            workspace_path=workspace_path,
            repository_url=repository_url,
            branch_strategy=branch_strategy
        )
        
        # Store modified files during operations
        self.modified_files: List[str] = []
        
        # Allow auto-committing by default
        self.git_extension.set_auto_commit(True)
        
        # Keep track of current task for branch naming
        self.current_task_id: Optional[str] = None
        self.current_task_description: Optional[str] = None
        
        # Initialize VS Code integration if enabled
        self.vscode_integration_enabled = vscode_integration_enabled
        if vscode_integration_enabled:
            self.vscode_service = VSCodeGitService(control_plane_url=control_plane_url)
            self.vscode_clients: Dict[str, str] = {}  # Map workspace names to client IDs
        
    async def process_message(self, message: Message) -> Message:
        """
        Process an incoming message - override this in child classes.
        
        This implementation just provides Git handling, but should be overridden
        with agent-specific processing in child classes.
        
        Args:
            message: The incoming message
            
        Returns:
            Response message
        """
        # First try to handle git messages
        git_response = await self.git_extension.handle_git_message(message)
        if git_response:
            return git_response
            
        # Handle task assignments to create feature branches
        if message.message_type == "task_assignment":
            self.current_task_id = message.thread_id
            self.current_task_description = message.content
            
            # Initialize Git for the task (create feature branch)
            if self.workspace_path_exists():
                await self.git_extension.initialize_for_task(
                    task_id=message.thread_id,
                    task_description=message.content[:50]  # Use first 50 chars as description
                )
        
        # Override this in child classes
        return await self.send_message(
            recipients=[message.sender],
            content="This is a base implementation. Override process_message in your agent class.",
            message_type="response",
            thread_id=message.thread_id
        )
    
    def workspace_path_exists(self) -> bool:
        """Check if the workspace path exists"""
        return (
            hasattr(self.git_extension, 'git') and 
            hasattr(self.git_extension.git, 'workspace_path') and
            os.path.exists(self.git_extension.git.workspace_path)
        )
    
    async def commit_file_changes(self, 
                            files: List[str], 
                            commit_message: Optional[str] = None) -> None:
        """
        Commit changes to files
        
        Args:
            files: List of files that were modified
            commit_message: Optional commit message
        """
        # Register files as modified
        for file in files:
            self.modified_files.append(file)
            self.git_extension.register_file_changes([file])
            
        # Trigger auto-commit
        await self.git_extension.auto_commit_changes(
            files=files,
            commit_message=commit_message
        )
        
    async def execute_with_git(self, 
                        operation: Callable[..., Awaitable[Any]], 
                        *args, 
                        commit_message: Optional[str] = None,
                        **kwargs) -> Any:
        """
        Execute an operation and commit any resulting file changes
        
        Args:
            operation: Async function to execute
            *args: Arguments to pass to the operation
            commit_message: Optional commit message for the changes
            **kwargs: Keyword arguments to pass to the operation
            
        Returns:
            Result of the operation
        """
        # Store the list of files before the operation
        status_before = self.git_extension.git.get_status()
        files_before = set()
        
        if status_before.get("status") == "success":
            files_before.update(status_before.get("modified_files", []))
            files_before.update(status_before.get("untracked_files", []))
            files_before.update(status_before.get("staged_files", []))
            
        # Execute the operation
        result = await operation(*args, **kwargs)
        
        # Get the list of files after the operation
        status_after = self.git_extension.git.get_status()
        files_after = set()
        
        if status_after.get("status") == "success":
            files_after.update(status_after.get("modified_files", []))
            files_after.update(status_after.get("untracked_files", []))
            files_after.update(status_after.get("staged_files", []))
            
        # Determine which files were modified during the operation
        modified_files = list(files_after - files_before)
        
        # Commit the changes if there are modified files
        if modified_files:
            if not commit_message:
                # Generate a commit message based on the current task
                if self.current_task_description:
                    commit_message = f"{self.agent_id}: {self.current_task_description[:50]}"
                else:
                    commit_message = f"{self.agent_id}: File changes"
                    
            await self.commit_file_changes(
                files=modified_files,
                commit_message=commit_message
            )
            
        return result
    
    async def create_pull_request(self, 
                           title: Optional[str] = None,
                           description: Optional[str] = None) -> Dict[str, Any]:
        """
        Create a pull request for the current branch
        
        Args:
            title: Optional title for the pull request
            description: Optional description for the pull request
            
        Returns:
            Pull request creation result
        """
        # Generate title if not provided
        if not title and self.current_task_description:
            title = f"{self.agent_id}: {self.current_task_description[:50]}"
        elif not title:
            title = f"Pull request by {self.agent_id}"
            
        # Generate description if not provided
        if not description:
            # Include task details in the description
            task_details = []
            if self.current_task_id:
                task_details.append(f"Task ID: {self.current_task_id}")
            if self.current_task_description:
                task_details.append(f"Task: {self.current_task_description}")
                
            # Include modified files in the description
            if self.modified_files:
                task_details.append("\nModified files:")
                for file in set(self.modified_files):
                    task_details.append(f"- {file}")
                    
            description = "\n".join(task_details)
            
        # Create the pull request
        return await self.git_extension.create_pull_request_for_review(
            title=title,
            description=description
        )
        
    # VS Code Integration Methods
    
    async def get_vscode_clients(self) -> Dict[str, Any]:
        """
        Get all connected VS Code clients
        
        Returns:
            List of connected clients
        """
        if not self.vscode_integration_enabled:
            return {"error": "VS Code integration not enabled"}
            
        return await self.vscode_service.get_connected_clients()
    
    async def set_vscode_client_branch(self, 
                                    workspace_name: str, 
                                    branch: str, 
                                    commit: Optional[str] = None) -> Dict[str, Any]:
        """
        Set the branch and commit for a VS Code client by workspace name
        
        Args:
            workspace_name: Name of the workspace
            branch: Name of the branch to checkout
            commit: Optional commit hash to checkout
            
        Returns:
            Command result
        """
        if not self.vscode_integration_enabled:
            return {"error": "VS Code integration not enabled"}
            
        # Check if we already know this client's ID
        client_id = self.vscode_clients.get(workspace_name)
        
        # If not, look it up
        if not client_id:
            client_id = await self.vscode_service.find_client_by_workspace_name(workspace_name)
            if client_id:
                self.vscode_clients[workspace_name] = client_id
                
        if not client_id:
            return {"error": f"VS Code client for workspace '{workspace_name}' not found"}
            
        # Generate a user-friendly message
        message = f"Checking out {branch}"
        if commit:
            message += f" at commit {commit[:7]}"
        message += f" (requested by {self.agent_id})"
        
        # Send checkout command
        return await self.vscode_service.checkout_branch(
            client_id=client_id,
            branch=branch,
            commit=commit,
            message=message
        )
    
    async def sync_vscode_with_git(self, workspace_name: str) -> Dict[str, Any]:
        """
        Sync a VS Code client with the current Git state
        
        Args:
            workspace_name: Name of the workspace
            
        Returns:
            Sync result
        """
        if not self.vscode_integration_enabled:
            return {"error": "VS Code integration not enabled"}
            
        # Get current branch
        current_branch = self.git_extension.get_current_branch()
        if not current_branch:
            return {"error": "Could not determine current branch"}
            
        # Checkout the branch in VS Code
        return await self.set_vscode_client_branch(
            workspace_name=workspace_name,
            branch=current_branch
        ) 