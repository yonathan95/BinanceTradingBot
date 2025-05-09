"""
Agent Git Extension - Provides Git integration capabilities to any Hive Mind agent.
"""

import logging
import os
import re
import asyncio
from typing import Dict, List, Any, Optional, Tuple, Union

from hive_mind.agent_sdk.base_agent import BaseAgent, Message
from .git_integration import GitIntegration

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AgentGitExtension:
    """
    Extension class that adds Git integration capabilities to any agent.
    
    This class uses composition rather than inheritance to extend agent functionality.
    It should be instantiated within an agent class and used to handle Git operations.
    """
    
    def __init__(self, 
                agent: BaseAgent,
                workspace_path: Optional[str] = None, 
                repository_url: Optional[str] = None,
                branch_strategy: str = "gitflow"):
        """
        Initialize Git extension for an agent
        
        Args:
            agent: The agent to extend with Git capabilities
            workspace_path: Path to the workspace directory
            repository_url: URL of the git repository
            branch_strategy: Branching strategy to use (gitflow, github-flow, trunk-based)
        """
        self.agent = agent
        self.git = GitIntegration(
            workspace_path=workspace_path, 
            repository_url=repository_url, 
            agent_id=agent.agent_id,
            branch_strategy=branch_strategy
        )
        
        # Track whether we should auto-commit changes
        self.auto_commit_enabled = True
        self.auto_push_enabled = False
        self.last_commit_time = 0
        self.commit_cooldown = 60  # seconds between auto-commits
        self.pending_changes: List[str] = []
        
    async def handle_git_message(self, message: Message) -> Optional[Message]:
        """
        Handle a Git-related message
        
        Args:
            message: The incoming message
            
        Returns:
            Optional response message
        """
        # Check if this is a Git operation request
        if self._is_git_request(message.content):
            return await self._process_git_request(message)
        
        return None
        
    def _is_git_request(self, text: str) -> bool:
        """Check if a message is a Git operation request"""
        git_keywords = [
            "git", "commit", "push", "branch", "merge", "pull request", "pr",
            "checkout", "clone", "repository", "repo", "version control"
        ]
        
        text_lower = text.lower()
        
        for keyword in git_keywords:
            if keyword in text_lower:
                return True
                
        return False
        
    async def _process_git_request(self, message: Message) -> Message:
        """Process a Git request and return a response"""
        # Parse the Git operation from the message
        operation, params = self._parse_git_operation(message.content)
        
        # Handle the Git operation
        if operation == "status":
            result = self.git.get_status()
        elif operation == "commit":
            commit_message = params.get("message", f"Update by {self.agent.agent_id}")
            files = params.get("files", None)
            auto_push = params.get("push", self.auto_push_enabled)
            result = self.git.commit_changes(files=files, commit_message=commit_message, auto_push=auto_push)
        elif operation == "branch":
            branch_name = params.get("name")
            if branch_name:
                result = self.git.checkout_branch(branch_name, create=params.get("create", False))
            else:
                # Just return current branch info
                status = self.git.get_status()
                result = {
                    "status": "success",
                    "current_branch": status.get("current_branch"),
                    "branches": status.get("branches", [])
                }
        elif operation == "feature":
            feature_name = params.get("name")
            if feature_name:
                result = self.git.create_feature_branch(feature_name)
            else:
                result = {
                    "status": "error",
                    "message": "Feature name is required to create a feature branch"
                }
        elif operation == "pull":
            result = self.git.pull_latest_changes()
        elif operation == "push":
            result = self.git.push_changes()
        elif operation == "pr" or operation == "pull_request":
            title = params.get("title", f"Pull request by {self.agent.agent_id}")
            description = params.get("description")
            target = params.get("target")
            result = self.git.create_pull_request(title=title, description=description, target_branch=target)
        elif operation == "merge":
            source = params.get("source")
            target = params.get("target")
            message = params.get("message")
            if source:
                result = self.git.merge_branch(source_branch=source, target_branch=target, commit_message=message)
            else:
                result = {
                    "status": "error",
                    "message": "Source branch is required for merge operation"
                }
        elif operation == "init":
            result = self.git.init_repository()
        else:
            result = {
                "status": "error",
                "message": f"Unknown Git operation: {operation}"
            }
            
        # Construct response message
        response_content = self._format_git_result(result)
        
        # Store in agent memory if enabled
        if hasattr(self.agent, 'memory_enabled') and self.agent.memory_enabled:
            await self.agent.memory.add_memory(
                content=f"GIT OPERATION: {operation}\nResult: {response_content[:200]}...",
                metadata={
                    "type": "git_operation",
                    "operation": operation,
                    "status": result.get("status"),
                    "timestamp": asyncio.get_event_loop().time()
                },
                importance=3.0
            )
            
        # Return response message
        return await self.agent.send_message(
            recipients=[message.sender],
            content=response_content,
            context_tags=message.context_tags + ["#git_operation"],
            message_type="git_operation_result",
            thread_id=message.thread_id
        )
        
    def _parse_git_operation(self, text: str) -> Tuple[str, Dict[str, Any]]:
        """
        Parse a Git operation from text
        
        Args:
            text: The message content
            
        Returns:
            Tuple of (operation, parameters)
        """
        text_lower = text.lower()
        
        # Default operation is status
        operation = "status"
        params = {}
        
        # Check for operation types
        if "commit" in text_lower:
            operation = "commit"
            # Extract commit message
            message_match = re.search(r'commit\s+(?:message|msg)?\s*[\'"]([^\'"]+)[\'"]', text_lower)
            if message_match:
                params["message"] = message_match.group(1)
            # Check for push flag
            if "push" in text_lower:
                params["push"] = True
                
        elif "branch" in text_lower:
            operation = "branch"
            # Extract branch name
            branch_match = re.search(r'branch\s+(?:name)?\s*[\'"]?([a-zA-Z0-9_/-]+)[\'"]?', text_lower)
            if branch_match:
                params["name"] = branch_match.group(1)
            # Check for create flag
            if "create" in text_lower or "new" in text_lower:
                params["create"] = True
                
        elif "feature" in text_lower:
            operation = "feature"
            # Extract feature name
            feature_match = re.search(r'feature\s+(?:for|named?)?\s*[\'"]?([a-zA-Z0-9_\s-]+)[\'"]?', text_lower)
            if feature_match:
                params["name"] = feature_match.group(1).strip()
                
        elif "pull request" in text_lower or "pr" in text_lower:
            operation = "pull_request"
            # Extract PR title
            title_match = re.search(r'(?:title|named?)\s*[\'"]([^\'"]+)[\'"]', text_lower)
            if title_match:
                params["title"] = title_match.group(1)
            # Extract target branch
            target_match = re.search(r'(?:to|into|target)\s+(?:branch)?\s*[\'"]?([a-zA-Z0-9_/-]+)[\'"]?', text_lower)
            if target_match:
                params["target"] = target_match.group(1)
                
        elif "merge" in text_lower:
            operation = "merge"
            # Extract source branch
            source_match = re.search(r'(?:from|source)\s+(?:branch)?\s*[\'"]?([a-zA-Z0-9_/-]+)[\'"]?', text_lower)
            if source_match:
                params["source"] = source_match.group(1)
            # Extract target branch
            target_match = re.search(r'(?:to|into|target)\s+(?:branch)?\s*[\'"]?([a-zA-Z0-9_/-]+)[\'"]?', text_lower)
            if target_match:
                params["target"] = target_match.group(1)
                
        elif "pull" in text_lower:
            operation = "pull"
            
        elif "push" in text_lower:
            operation = "push"
            
        elif "init" in text_lower or "initialize" in text_lower:
            operation = "init"
            
        return operation, params
        
    def _format_git_result(self, result: Dict[str, Any]) -> str:
        """Format a Git operation result as a user-friendly message"""
        status = result.get("status", "unknown")
        message = result.get("message", "No details available")
        
        if status == "success":
            if "branch" in result:
                branch_info = f" (Branch: {result['branch']})"
            else:
                branch_info = ""
                
            response = f"✅ Git operation successful: {message}{branch_info}"
            
            # Add details for specific operations
            if "commit_message" in result:
                response += f"\nCommitted with message: \"{result['commit_message']}\""
                if result.get("push_status") == "pushed":
                    response += "\nChanges were automatically pushed to the remote repository."
                    
            if "pr_details" in result:
                pr = result["pr_details"]
                response += f"\nPull request created:"
                response += f"\n- Title: {pr['title']}"
                response += f"\n- From: {pr['source_branch']} to {pr['target_branch']}"
                if "description" in pr:
                    response += f"\n- Description: {pr['description']}"
                    
            if "details" in result and result["details"]:
                response += f"\nDetails: {result['details']}"
                
        elif status == "error":
            response = f"❌ Git operation failed: {message}"
            
        elif status == "not_initialized":
            response = f"⚠️ {message}. Please initialize the repository first with a Git init operation."
            
        elif status == "no_changes":
            response = f"ℹ️ {message}. No action was taken."
            
        elif status == "unauthorized":
            response = f"🔒 {message}"
            
        elif status == "simulation":
            response = f"ℹ️ {message}"
            if "pr_details" in result:
                pr = result["pr_details"]
                response += f"\nPull request would be created:"
                response += f"\n- Title: {pr['title']}"
                response += f"\n- From: {pr['source_branch']} to {pr['target_branch']}"
                if "description" in pr:
                    response += f"\n- Description: {pr['description']}"
                    
        else:
            # Format status information
            if status == "success" and "current_branch" in result:
                branches = result.get("branches", [])
                response = f"📊 Git Status\nCurrent branch: {result['current_branch']}\nAvailable branches: {', '.join(branches)}"
                
                if "modified_files" in result:
                    modified = result.get("modified_files", [])
                    untracked = result.get("untracked_files", [])
                    staged = result.get("staged_files", [])
                    
                    if modified or untracked or staged:
                        response += "\n\nChanges:"
                        if modified:
                            response += f"\n- Modified: {', '.join(modified)}"
                        if untracked:
                            response += f"\n- Untracked: {', '.join(untracked)}"
                        if staged:
                            response += f"\n- Staged: {', '.join(staged)}"
                    else:
                        response += "\n\nWorking directory clean, no changes."
            else:
                response = f"Git operation result: {status}"
                if message:
                    response += f" - {message}"
                    
        return response
        
    async def auto_commit_changes(self, files: List[str] = None, commit_message: str = None) -> Optional[Dict[str, Any]]:
        """
        Automatically commit changes if auto-commit is enabled
        
        Args:
            files: List of files to commit
            commit_message: Commit message
            
        Returns:
            Optional commit result
        """
        if not self.auto_commit_enabled:
            return None
            
        # Check if we're in the commit cooldown period
        current_time = asyncio.get_event_loop().time()
        if current_time - self.last_commit_time < self.commit_cooldown:
            # Just store the files for later
            if files:
                for file in files:
                    if file not in self.pending_changes:
                        self.pending_changes.append(file)
            return None
            
        # If no files specified, use pending changes
        if not files and self.pending_changes:
            files = list(self.pending_changes)
            self.pending_changes = []
            
        # Check if there are any changes to commit
        status = self.git.get_status()
        if status.get("status") != "success" or not status.get("has_changes", False):
            return None
            
        # Create commit message if not provided
        if not commit_message:
            commit_message = f"Auto-commit by {self.agent.agent_id}"
            
        # Commit changes
        result = self.git.commit_changes(
            files=files, 
            commit_message=commit_message, 
            auto_push=self.auto_push_enabled
        )
        
        # Update last commit time
        if result.get("status") == "success":
            self.last_commit_time = current_time
            
        return result
        
    def set_auto_commit(self, enabled: bool = True) -> None:
        """
        Enable or disable automatic commits
        
        Args:
            enabled: Whether auto-commit should be enabled
        """
        self.auto_commit_enabled = enabled
        
    def set_auto_push(self, enabled: bool = True) -> None:
        """
        Enable or disable automatic pushes after commits
        
        Args:
            enabled: Whether auto-push should be enabled
        """
        self.auto_push_enabled = enabled
        
    def register_file_changes(self, files: List[str]) -> None:
        """
        Register files that have been changed for the next auto-commit
        
        Args:
            files: List of files that have been modified
        """
        for file in files:
            if file not in self.pending_changes:
                self.pending_changes.append(file)
                
    async def create_pull_request_for_review(self, 
                                      title: str, 
                                      description: str = None) -> Dict[str, Any]:
        """
        Create a pull request for code review
        
        Args:
            title: Title of the pull request
            description: Description of the pull request
            
        Returns:
            Pull request creation result
        """
        # Commit any pending changes first
        if self.pending_changes:
            await self.auto_commit_changes(
                files=list(self.pending_changes),
                commit_message="Prepare for pull request"
            )
            self.pending_changes = []
            
        # Push changes to remote if not auto-pushing
        if not self.auto_push_enabled:
            self.git.push_changes()
            
        # Create pull request
        return self.git.create_pull_request(title=title, description=description)
        
    def get_current_branch(self) -> Optional[str]:
        """Get the name of the current branch"""
        status = self.git.get_status()
        if status.get("status") == "success":
            return status.get("current_branch")
        return None
        
    async def initialize_for_task(self, task_id: str, task_description: str) -> Dict[str, Any]:
        """
        Initialize Git for a new task (creates a feature branch)
        
        Args:
            task_id: ID of the task
            task_description: Description of the task
            
        Returns:
            Initialization result
        """
        # Make sure repository is initialized
        if not self.git.is_initialized:
            self.git.init_repository()
            
        # Create a feature branch for the task
        feature_name = f"{task_id}-{task_description[:20].lower().replace(' ', '-')}"
        result = self.git.create_feature_branch(feature_name)
        
        if result.get("status") == "success":
            # Reset pending changes
            self.pending_changes = []
            self.last_commit_time = asyncio.get_event_loop().time()
            
        return result 