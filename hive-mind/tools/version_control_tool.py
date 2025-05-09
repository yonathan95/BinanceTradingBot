import os
import json
import time
import asyncio
import hashlib
from typing import Dict, Any, List, Optional, Set
from pathlib import Path
import aiofiles
import shutil

from hive_mind.agent_sdk.base_agent import AgentTool
from hive_mind.agent_sdk.message import Message

class VersionControlTool(AgentTool):
    """
    Tool for version control operations in the agent workspace.
    Manages an embedded representation of the project that agents can access
    and commit changes to, with a review and approval workflow.
    """
    
    def __init__(self, 
                workspace_path: str, 
                embedded_project_path: str,
                notification_callback=None):
        """
        Initialize the VersionControlTool with paths for workspace and embedded project
        
        Args:
            workspace_path: Base directory for agent workspace operations
            embedded_project_path: Directory for the embedded project representation
            notification_callback: Optional callback function to notify agents of changes
        """
        super().__init__(
            name="version_control_tool",
            description="Manage version control operations for the embedded project",
            parameters={
                "action": "The action to perform (commit, review, approve, reject, status, fetch)",
                "path": "The path to the file or directory, relative to the embedded project",
                "content": "The content to commit (for commit action only)",
                "message": "Commit message or review comments",
                "agent_id": "ID of the agent performing the action"
            }
        )
        self.workspace_path = Path(workspace_path)
        self.embedded_path = Path(embedded_project_path)
        self.notification_callback = notification_callback
        
        # Tracking structures
        self.pending_reviews = {}  # Maps file paths to pending review data
        self.commit_history = []   # History of all commits
        self.file_versions = {}    # Maps file paths to their latest version hash
        self.file_watchers = {}    # Maps file paths to sets of agent_ids watching them
        
        # Ensure directories exist
        os.makedirs(self.workspace_path, exist_ok=True)
        os.makedirs(self.embedded_path, exist_ok=True)
        os.makedirs(self.embedded_path / ".reviews", exist_ok=True)
        os.makedirs(self.embedded_path / ".history", exist_ok=True)
        
        # Load existing state if available
        self._load_state()
    
    def _load_state(self):
        """Load existing version control state from disk"""
        history_path = self.embedded_path / ".history" / "commit_history.json"
        reviews_path = self.embedded_path / ".reviews" / "pending.json"
        versions_path = self.embedded_path / ".history" / "file_versions.json"
        watchers_path = self.embedded_path / ".history" / "file_watchers.json"
        
        try:
            if history_path.exists():
                with open(history_path, 'r') as f:
                    self.commit_history = json.load(f)
            
            if reviews_path.exists():
                with open(reviews_path, 'r') as f:
                    self.pending_reviews = json.load(f)
            
            if versions_path.exists():
                with open(versions_path, 'r') as f:
                    self.file_versions = json.load(f)
                    
            if watchers_path.exists():
                with open(watchers_path, 'r') as f:
                    watchers_data = json.load(f)
                    # Convert lists back to sets
                    self.file_watchers = {k: set(v) for k, v in watchers_data.items()}
        except Exception as e:
            print(f"Error loading version control state: {e}")
    
    def _save_state(self):
        """Save current version control state to disk"""
        history_path = self.embedded_path / ".history" / "commit_history.json"
        reviews_path = self.embedded_path / ".reviews" / "pending.json"
        versions_path = self.embedded_path / ".history" / "file_versions.json"
        watchers_path = self.embedded_path / ".history" / "file_watchers.json"
        
        try:
            with open(history_path, 'w') as f:
                json.dump(self.commit_history, f, indent=2)
            
            with open(reviews_path, 'w') as f:
                json.dump(self.pending_reviews, f, indent=2)
            
            with open(versions_path, 'w') as f:
                json.dump(self.file_versions, f, indent=2)
                
            # Convert sets to lists for JSON serialization
            watchers_data = {k: list(v) for k, v in self.file_watchers.items()}
            with open(watchers_path, 'w') as f:
                json.dump(watchers_data, f, indent=2)
        except Exception as e:
            print(f"Error saving version control state: {e}")
    
    def _get_file_hash(self, content: str) -> str:
        """Generate a hash for file content"""
        return hashlib.sha256(content.encode('utf-8')).hexdigest()
    
    def _get_safe_path(self, path: str, base_path: Path) -> Path:
        """
        Ensure the path doesn't escape the specified base path
        
        Args:
            path: The requested path
            base_path: The base path (workspace or embedded project)
            
        Returns:
            A safe Path object
        
        Raises:
            ValueError: If the path attempts to escape the base path
        """
        # Normalize the path and resolve any symlinks
        full_path = (base_path / path).resolve()
        
        # Check if it's within the base path
        if not str(full_path).startswith(str(base_path.resolve())):
            raise ValueError(f"Path {path} attempts to escape the base path")
            
        return full_path
    
    async def execute(self, 
                    action: str, 
                    path: Optional[str] = None,
                    content: Optional[str] = None,
                    message: Optional[str] = None,
                    agent_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Execute version control operations
        
        Args:
            action: The action to perform (commit, review, approve, reject, status, fetch)
            path: The path to the file or directory
            content: The content to commit (for commit action only)
            message: Commit message or review comments
            agent_id: ID of the agent performing the action
            
        Returns:
            A dictionary with the operation result
        """
        try:
            if action == "commit":
                return await self._commit_file(path, content, message, agent_id)
            elif action == "review":
                return await self._review_commit(path, message, agent_id)
            elif action == "approve":
                return await self._approve_commit(path, message, agent_id)
            elif action == "reject":
                return await self._reject_commit(path, message, agent_id)
            elif action == "status":
                return await self._get_status(path)
            elif action == "fetch":
                return await self._fetch_file(path)
            elif action == "watch":
                return await self._watch_file(path, agent_id)
            elif action == "unwatch":
                return await self._unwatch_file(path, agent_id)
            else:
                return {
                    "success": False,
                    "error": f"Unknown action: {action}"
                }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _commit_file(self, path: str, content: str, message: str, agent_id: str) -> Dict[str, Any]:
        """
        Commit a file to the embedded project (creates a pending review)
        
        Args:
            path: Path to the file in the embedded project
            content: New file content
            message: Commit message
            agent_id: ID of the agent committing the file
            
        Returns:
            Status of the operation
        """
        if not path or not content or not message or not agent_id:
            return {
                "success": False,
                "error": "Missing required parameters"
            }
        
        # Ensure path is safe
        full_path = self._get_safe_path(path, self.embedded_path)
        
        # Create a content hash
        content_hash = self._get_file_hash(content)
        
        # Check if this exact content is already in the current file (if it exists)
        if full_path.exists() and full_path.is_file():
            async with aiofiles.open(full_path, 'r', encoding='utf-8') as f:
                current_content = await f.read()
                current_hash = self._get_file_hash(current_content)
                
                if current_hash == content_hash:
                    return {
                        "success": False,
                        "error": "No changes detected in file"
                    }
        
        # Create or update the review request
        review_id = f"{agent_id}_{path}_{int(time.time())}"
        review_data = {
            "review_id": review_id,
            "path": path,
            "content": content,
            "content_hash": content_hash,
            "commit_message": message,
            "author": agent_id,
            "timestamp": time.time(),
            "status": "pending",
            "reviews": [],
            "is_approved": False
        }
        
        # Store the review request
        self.pending_reviews[path] = review_data
        
        # Save the pending review to disk for persistence
        reviews_dir = self.embedded_path / ".reviews"
        os.makedirs(reviews_dir, exist_ok=True)
        review_path = reviews_dir / f"{review_id}.json"
        
        async with aiofiles.open(review_path, 'w', encoding='utf-8') as f:
            await f.write(json.dumps(review_data, indent=2))
        
        # Update pending reviews index
        self._save_state()
        
        # Notify about the new pending review
        if self.notification_callback:
            await self.notification_callback({
                "type": "pending_review",
                "path": path,
                "review_id": review_id,
                "author": agent_id,
                "message": message
            })
        
        return {
            "success": True,
            "review_id": review_id,
            "status": "pending_review",
            "message": f"Changes committed and pending review for {path}"
        }
    
    async def _review_commit(self, path: str, comments: str, reviewer_id: str) -> Dict[str, Any]:
        """
        Add review comments to a pending commit
        
        Args:
            path: Path to the file with pending review
            comments: Review comments
            reviewer_id: ID of the reviewing agent
            
        Returns:
            Status of the operation
        """
        if path not in self.pending_reviews:
            return {
                "success": False,
                "error": f"No pending review found for {path}"
            }
        
        review_data = self.pending_reviews[path]
        
        # Add review comments
        review = {
            "reviewer": reviewer_id,
            "timestamp": time.time(),
            "comments": comments
        }
        
        review_data["reviews"].append(review)
        
        # Update the review data
        self.pending_reviews[path] = review_data
        
        # Save updated review to disk
        review_path = self.embedded_path / ".reviews" / f"{review_data['review_id']}.json"
        
        async with aiofiles.open(review_path, 'w', encoding='utf-8') as f:
            await f.write(json.dumps(review_data, indent=2))
        
        # Save state
        self._save_state()
        
        # Notify about the review
        if self.notification_callback:
            await self.notification_callback({
                "type": "review_added",
                "path": path,
                "review_id": review_data["review_id"],
                "reviewer": reviewer_id,
                "comments": comments
            })
        
        return {
            "success": True,
            "message": f"Review added to {path}",
            "review_id": review_data["review_id"]
        }
    
    async def _approve_commit(self, path: str, message: str, approver_id: str) -> Dict[str, Any]:
        """
        Approve and merge a pending commit
        
        Args:
            path: Path to the file with pending review
            message: Approval message
            approver_id: ID of the approving agent
            
        Returns:
            Status of the operation
        """
        if path not in self.pending_reviews:
            return {
                "success": False,
                "error": f"No pending review found for {path}"
            }
        
        review_data = self.pending_reviews[path]
        
        # Check if reviewer is not the same as author
        if review_data["author"] == approver_id:
            return {
                "success": False,
                "error": "Author cannot approve their own changes"
            }
        
        # Add approval
        approval = {
            "reviewer": approver_id,
            "timestamp": time.time(),
            "approved": True,
            "message": message
        }
        
        review_data["reviews"].append(approval)
        review_data["is_approved"] = True
        review_data["status"] = "approved"
        review_data["approver"] = approver_id
        review_data["approval_timestamp"] = time.time()
        
        # Get the full path for the file
        full_path = self._get_safe_path(path, self.embedded_path)
        
        # Ensure parent directory exists
        os.makedirs(full_path.parent, exist_ok=True)
        
        # Write the approved content to the file
        async with aiofiles.open(full_path, 'w', encoding='utf-8') as f:
            await f.write(review_data["content"])
        
        # Update file version
        self.file_versions[path] = review_data["content_hash"]
        
        # Add to commit history
        commit = {
            "commit_id": f"{review_data['review_id']}_approved",
            "path": path,
            "content_hash": review_data["content_hash"],
            "author": review_data["author"],
            "approver": approver_id,
            "message": review_data["commit_message"],
            "approval_message": message,
            "timestamp": time.time()
        }
        
        self.commit_history.append(commit)
        
        # Remove from pending reviews
        del self.pending_reviews[path]
        
        # Save state
        self._save_state()
        
        # Move the review file to history
        review_path = self.embedded_path / ".reviews" / f"{review_data['review_id']}.json"
        history_path = self.embedded_path / ".history" / f"{review_data['review_id']}_approved.json"
        
        if review_path.exists():
            # Update the review data first
            async with aiofiles.open(review_path, 'w', encoding='utf-8') as f:
                await f.write(json.dumps(review_data, indent=2))
            
            # Move to history
            shutil.move(str(review_path), str(history_path))
        
        # Notify about the approval and merged changes
        if self.notification_callback:
            await self.notification_callback({
                "type": "commit_approved",
                "path": path,
                "review_id": review_data["review_id"],
                "author": review_data["author"],
                "approver": approver_id,
                "message": message
            })
        
        # Notify watching agents about file changes
        await self._notify_file_watchers(path)
        
        return {
            "success": True,
            "message": f"Changes to {path} approved and merged",
            "commit_id": commit["commit_id"]
        }
    
    async def _reject_commit(self, path: str, message: str, reviewer_id: str) -> Dict[str, Any]:
        """
        Reject a pending commit
        
        Args:
            path: Path to the file with pending review
            message: Rejection message with feedback
            reviewer_id: ID of the reviewer agent
            
        Returns:
            Status of the operation
        """
        if path not in self.pending_reviews:
            return {
                "success": False,
                "error": f"No pending review found for {path}"
            }
        
        review_data = self.pending_reviews[path]
        
        # Add rejection
        rejection = {
            "reviewer": reviewer_id,
            "timestamp": time.time(),
            "approved": False,
            "message": message
        }
        
        review_data["reviews"].append(rejection)
        review_data["is_approved"] = False
        review_data["status"] = "rejected"
        review_data["rejection_timestamp"] = time.time()
        
        # Update the review data
        self.pending_reviews[path] = review_data
        
        # Save updated review to disk
        review_path = self.embedded_path / ".reviews" / f"{review_data['review_id']}.json"
        
        async with aiofiles.open(review_path, 'w', encoding='utf-8') as f:
            await f.write(json.dumps(review_data, indent=2))
        
        # Save state
        self._save_state()
        
        # Notify about the rejection
        if self.notification_callback:
            await self.notification_callback({
                "type": "commit_rejected",
                "path": path,
                "review_id": review_data["review_id"],
                "author": review_data["author"],
                "reviewer": reviewer_id,
                "message": message
            })
        
        return {
            "success": True,
            "message": f"Changes to {path} rejected with feedback",
            "review_id": review_data["review_id"]
        }
    
    async def _get_status(self, path: Optional[str] = None) -> Dict[str, Any]:
        """
        Get status of files in the embedded project
        
        Args:
            path: Optional path to check status for a specific file
            
        Returns:
            Status information
        """
        if path:
            # Get status for a specific file
            full_path = self._get_safe_path(path, self.embedded_path)
            
            if not full_path.exists():
                return {
                    "success": True,
                    "exists": False,
                    "message": f"File {path} does not exist in the embedded project"
                }
            
            # Check if it has a pending review
            pending_review = self.pending_reviews.get(path, None)
            
            # Get version info
            version = self.file_versions.get(path, "unknown")
            
            return {
                "success": True,
                "exists": True,
                "is_file": full_path.is_file(),
                "is_directory": full_path.is_dir(),
                "pending_review": pending_review is not None,
                "review_data": pending_review,
                "version": version
            }
        else:
            # Get overall status
            return {
                "success": True,
                "pending_reviews": list(self.pending_reviews.keys()),
                "total_commits": len(self.commit_history),
                "last_commit": self.commit_history[-1] if self.commit_history else None
            }
    
    async def _fetch_file(self, path: str) -> Dict[str, Any]:
        """
        Fetch a file from the embedded project
        
        Args:
            path: Path to the file
            
        Returns:
            File content if successful
        """
        if not path:
            return {
                "success": False,
                "error": "Path is required"
            }
        
        full_path = self._get_safe_path(path, self.embedded_path)
        
        if not full_path.exists():
            return {
                "success": False,
                "error": f"File {path} does not exist in the embedded project"
            }
        
        if not full_path.is_file():
            return {
                "success": False,
                "error": f"{path} is a directory, not a file"
            }
        
        try:
            async with aiofiles.open(full_path, 'r', encoding='utf-8') as f:
                content = await f.read()
            
            return {
                "success": True,
                "path": path,
                "content": content,
                "version": self.file_versions.get(path, "unknown")
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Error reading file: {str(e)}"
            }
    
    async def _watch_file(self, path: str, agent_id: str) -> Dict[str, Any]:
        """
        Add an agent to the watchers list for a file
        
        Args:
            path: Path to the file to watch
            agent_id: ID of the agent that wants to watch the file
            
        Returns:
            Success status
        """
        if path not in self.file_watchers:
            self.file_watchers[path] = set()
            
        self.file_watchers[path].add(agent_id)
        self._save_state()
        
        return {
            "success": True,
            "message": f"Agent {agent_id} is now watching {path}",
            "watchers_count": len(self.file_watchers[path])
        }
    
    async def _unwatch_file(self, path: str, agent_id: str) -> Dict[str, Any]:
        """
        Remove an agent from the watchers list for a file
        
        Args:
            path: Path to the file to unwatch
            agent_id: ID of the agent that wants to stop watching
            
        Returns:
            Success status
        """
        if path in self.file_watchers and agent_id in self.file_watchers[path]:
            self.file_watchers[path].remove(agent_id)
            self._save_state()
            
        return {
            "success": True,
            "message": f"Agent {agent_id} is no longer watching {path}",
            "watchers_count": len(self.file_watchers.get(path, set()))
        }
    
    async def _notify_file_watchers(self, path: str) -> None:
        """
        Notify all agents watching a file that it has changed
        
        Args:
            path: Path to the file that changed
        """
        if not self.notification_callback or path not in self.file_watchers:
            return
        
        watchers = self.file_watchers[path]
        if not watchers:
            return
            
        # Get the file content
        file_data = await self._fetch_file(path)
        
        if not file_data["success"]:
            return
            
        for agent_id in watchers:
            await self.notification_callback({
                "type": "file_changed",
                "path": path,
                "content": file_data["content"],
                "version": file_data["version"],
                "agent_id": agent_id
            }) 