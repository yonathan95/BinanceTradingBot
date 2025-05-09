"""
Git Integration Module - Provides Git version control functionality for all agents
in the Hive Mind system.
"""

import os
import logging
import subprocess
import re
from typing import Dict, List, Any, Optional, Tuple, Union
import asyncio

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GitIntegration:
    """
    Git integration class that provides version control functionality
    to all agents in the Hive Mind system.
    """
    
    def __init__(self, 
                workspace_path: Optional[str] = None, 
                repository_url: Optional[str] = None,
                agent_id: str = "unknown",
                branch_strategy: str = "gitflow"):
        """
        Initialize Git integration
        
        Args:
            workspace_path: Path to the workspace directory
            repository_url: URL of the git repository
            agent_id: ID of the agent using this integration
            branch_strategy: Branching strategy to use (gitflow, github-flow, trunk-based)
        """
        self.workspace_path = workspace_path or os.getcwd()
        self.repository_url = repository_url
        self.agent_id = agent_id
        self.branch_strategy = branch_strategy
        self.current_branch = None
        
        # Default branch configuration based on strategy
        if branch_strategy == "gitflow":
            self.branches = {
                "main": "main",
                "develop": "develop",
                "feature_prefix": "feature/",
                "bugfix_prefix": "bugfix/",
                "release_prefix": "release/",
                "hotfix_prefix": "hotfix/"
            }
        elif branch_strategy == "github-flow":
            self.branches = {
                "main": "main",
                "feature_prefix": "feature/",
                "bugfix_prefix": "fix/"
            }
        elif branch_strategy == "trunk-based":
            self.branches = {
                "main": "main",
                "feature_prefix": "fb/"
            }
            
        # Initialize the repository status
        self._update_repo_status()
        
    def _update_repo_status(self):
        """Update repository status information"""
        # Check if the directory is a git repository
        if os.path.exists(os.path.join(self.workspace_path, ".git")):
            self.is_initialized = True
            
            # Get current branch
            try:
                result = self._run_git_command("git branch --show-current")
                self.current_branch = result.strip() if result else None
            except Exception as e:
                logger.error(f"Error getting current branch: {str(e)}")
                self.current_branch = None
                
            # Get remote URL if not already set
            if not self.repository_url:
                try:
                    result = self._run_git_command("git config --get remote.origin.url")
                    self.repository_url = result.strip() if result else None
                except Exception as e:
                    logger.error(f"Error getting remote URL: {str(e)}")
        else:
            self.is_initialized = False
            
    def _run_git_command(self, command: str) -> str:
        """
        Run a git command and return the output
        
        Args:
            command: Git command to run
            
        Returns:
            Command output as string
        """
        try:
            # Split the command into args
            args = command.split()
            
            # Run the command
            process = subprocess.run(
                args,
                cwd=self.workspace_path,
                capture_output=True,
                text=True,
                check=True
            )
            
            return process.stdout
        except subprocess.CalledProcessError as e:
            logger.error(f"Git command failed: {command}")
            logger.error(f"Error: {e.stderr}")
            raise Exception(f"Git command failed: {e.stderr}")
            
    def init_repository(self) -> Dict[str, Any]:
        """
        Initialize a new git repository
        
        Returns:
            Status information
        """
        if self.is_initialized:
            return {"status": "already_initialized", "message": "Repository already initialized"}
            
        try:
            # Initialize repository
            self._run_git_command("git init")
            
            # Set up initial branch
            self._run_git_command(f"git checkout -b {self.branches['main']}")
            
            # Create .gitignore file with common exclusions
            gitignore_content = """
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
*.egg-info/
.installed.cfg
*.egg

# Node.js
node_modules/
npm-debug.log
yarn-debug.log
yarn-error.log
.env
.env.local
.env.development.local
.env.test.local
.env.production.local

# Editor/IDE
.idea/
.vscode/
*.swp
*.swo

# OS specific
.DS_Store
Thumbs.db
"""
            gitignore_path = os.path.join(self.workspace_path, ".gitignore")
            with open(gitignore_path, "w") as f:
                f.write(gitignore_content)
                
            # Add and commit .gitignore
            self._run_git_command("git add .gitignore")
            self._run_git_command("git commit -m \"Initial commit: Add .gitignore\"")
            
            # If repository URL is provided, add remote
            if self.repository_url:
                self._run_git_command(f"git remote add origin {self.repository_url}")
                
            # Update repository status
            self._update_repo_status()
            
            return {
                "status": "success", 
                "message": "Repository initialized successfully", 
                "branch": self.current_branch
            }
        except Exception as e:
            logger.error(f"Error initializing repository: {str(e)}")
            return {"status": "error", "message": f"Error initializing repository: {str(e)}"}
            
    def checkout_branch(self, branch_name: str, create: bool = False) -> Dict[str, Any]:
        """
        Checkout a branch
        
        Args:
            branch_name: Name of the branch to checkout
            create: Whether to create the branch if it doesn't exist
            
        Returns:
            Status information
        """
        if not self.is_initialized:
            return {"status": "not_initialized", "message": "Repository not initialized"}
            
        try:
            if create:
                # Check if branch exists
                existing_branches = self._run_git_command("git branch")
                branch_exists = branch_name in existing_branches
                
                if branch_exists:
                    self._run_git_command(f"git checkout {branch_name}")
                else:
                    self._run_git_command(f"git checkout -b {branch_name}")
            else:
                self._run_git_command(f"git checkout {branch_name}")
                
            # Update current branch
            self._update_repo_status()
            
            return {
                "status": "success", 
                "message": f"Switched to branch {branch_name}", 
                "branch": self.current_branch
            }
        except Exception as e:
            logger.error(f"Error checking out branch: {str(e)}")
            return {"status": "error", "message": f"Error checking out branch: {str(e)}"}
            
    def create_feature_branch(self, feature_name: str) -> Dict[str, Any]:
        """
        Create a new feature branch
        
        Args:
            feature_name: Name of the feature
            
        Returns:
            Status information
        """
        if not self.is_initialized:
            return {"status": "not_initialized", "message": "Repository not initialized"}
            
        # Normalize feature name (remove spaces, special chars)
        normalized_name = re.sub(r'[^a-zA-Z0-9-_]', '_', feature_name.lower())
        
        # Create branch name according to strategy
        branch_name = f"{self.branches['feature_prefix']}{normalized_name}"
        
        try:
            # Determine base branch based on strategy
            if self.branch_strategy == "gitflow":
                base_branch = self.branches["develop"]
            else:
                base_branch = self.branches["main"]
                
            # Checkout base branch
            self._run_git_command(f"git checkout {base_branch}")
            
            # Pull latest changes (if remote exists)
            if self.repository_url:
                try:
                    self._run_git_command(f"git pull origin {base_branch}")
                except Exception as e:
                    logger.warning(f"Could not pull latest changes: {str(e)}")
                    
            # Create and checkout feature branch
            self._run_git_command(f"git checkout -b {branch_name}")
            
            # Update current branch
            self._update_repo_status()
            
            return {
                "status": "success", 
                "message": f"Created feature branch {branch_name}", 
                "branch": self.current_branch
            }
        except Exception as e:
            logger.error(f"Error creating feature branch: {str(e)}")
            return {"status": "error", "message": f"Error creating feature branch: {str(e)}"}
            
    def commit_changes(self, 
                      files: List[str] = None, 
                      commit_message: str = None, 
                      auto_push: bool = False) -> Dict[str, Any]:
        """
        Commit changes to the repository
        
        Args:
            files: List of files to commit (None for all changes)
            commit_message: Commit message
            auto_push: Whether to push changes automatically after commit
            
        Returns:
            Status information
        """
        if not self.is_initialized:
            return {"status": "not_initialized", "message": "Repository not initialized"}
            
        try:
            # Check if there are changes to commit
            status = self._run_git_command("git status --porcelain")
            if not status.strip():
                return {"status": "no_changes", "message": "No changes to commit"}
                
            # Add files
            if files:
                for file in files:
                    self._run_git_command(f"git add {file}")
            else:
                self._run_git_command("git add .")
                
            # Create commit message
            if not commit_message:
                commit_message = f"Update by {self.agent_id}"
                
            # Commit changes
            self._run_git_command(f"git commit -m \"{commit_message}\"")
            
            # Push changes if requested
            if auto_push and self.repository_url:
                self._run_git_command(f"git push origin {self.current_branch}")
                push_status = "pushed"
            else:
                push_status = "not_pushed"
                
            return {
                "status": "success", 
                "message": f"Changes committed successfully", 
                "commit_message": commit_message,
                "push_status": push_status,
                "branch": self.current_branch
            }
        except Exception as e:
            logger.error(f"Error committing changes: {str(e)}")
            return {"status": "error", "message": f"Error committing changes: {str(e)}"}
            
    def create_pull_request(self, 
                          title: str, 
                          description: str = None,
                          target_branch: str = None) -> Dict[str, Any]:
        """
        Create a pull request (this is a simulation as git doesn't have PR functionality)
        
        Args:
            title: Title of the pull request
            description: Description of the pull request
            target_branch: Target branch for the pull request
            
        Returns:
            Status information with message to user
        """
        if not self.is_initialized:
            return {"status": "not_initialized", "message": "Repository not initialized"}
            
        # Determine target branch if not specified
        if not target_branch:
            if self.branch_strategy == "gitflow":
                if self.current_branch.startswith(self.branches["feature_prefix"]):
                    target_branch = self.branches["develop"]
                elif self.current_branch.startswith(self.branches["release_prefix"]):
                    target_branch = self.branches["main"]
                else:
                    target_branch = self.branches["develop"]
            else:
                target_branch = self.branches["main"]
                
        # Format the message to user with PR details
        if not description:
            description = f"Pull request created by {self.agent_id}"
            
        # This would actually call the GitHub/GitLab/BitBucket API in a real implementation
        # For now, we just return the information that would be needed
        return {
            "status": "simulation", 
            "message": "Pull request creation simulated (would require API integration)",
            "pr_details": {
                "title": title,
                "description": description,
                "source_branch": self.current_branch,
                "target_branch": target_branch,
                "creator": self.agent_id
            }
        }
        
    def get_status(self) -> Dict[str, Any]:
        """
        Get the current git status
        
        Returns:
            Repository status information
        """
        if not self.is_initialized:
            return {"status": "not_initialized", "message": "Repository not initialized"}
            
        try:
            # Get status
            status_output = self._run_git_command("git status --porcelain")
            
            # Parse status output
            modified_files = []
            untracked_files = []
            staged_files = []
            
            for line in status_output.strip().split("\n"):
                if not line.strip():
                    continue
                    
                status_code = line[:2]
                file_path = line[3:]
                
                if status_code.startswith("M"):
                    modified_files.append(file_path)
                elif status_code.startswith("A"):
                    staged_files.append(file_path)
                elif status_code.startswith("??"):
                    untracked_files.append(file_path)
                    
            # Get branch information
            branch_output = self._run_git_command("git branch")
            branches = [b.strip("* ") for b in branch_output.strip().split("\n") if b.strip()]
            
            return {
                "status": "success",
                "current_branch": self.current_branch,
                "branches": branches,
                "modified_files": modified_files,
                "untracked_files": untracked_files,
                "staged_files": staged_files,
                "has_changes": bool(status_output.strip()),
                "repository_url": self.repository_url
            }
        except Exception as e:
            logger.error(f"Error getting git status: {str(e)}")
            return {"status": "error", "message": f"Error getting git status: {str(e)}"}
            
    def pull_latest_changes(self) -> Dict[str, Any]:
        """
        Pull latest changes from remote
        
        Returns:
            Status information
        """
        if not self.is_initialized:
            return {"status": "not_initialized", "message": "Repository not initialized"}
            
        if not self.repository_url:
            return {"status": "no_remote", "message": "No remote repository configured"}
            
        try:
            # Pull changes
            output = self._run_git_command(f"git pull origin {self.current_branch}")
            
            return {
                "status": "success", 
                "message": "Changes pulled successfully", 
                "details": output.strip(),
                "branch": self.current_branch
            }
        except Exception as e:
            logger.error(f"Error pulling changes: {str(e)}")
            return {"status": "error", "message": f"Error pulling changes: {str(e)}"}
    
    def push_changes(self) -> Dict[str, Any]:
        """
        Push changes to remote
        
        Returns:
            Status information
        """
        if not self.is_initialized:
            return {"status": "not_initialized", "message": "Repository not initialized"}
            
        if not self.repository_url:
            return {"status": "no_remote", "message": "No remote repository configured"}
            
        try:
            # Push changes
            output = self._run_git_command(f"git push origin {self.current_branch}")
            
            return {
                "status": "success", 
                "message": "Changes pushed successfully", 
                "details": output.strip(),
                "branch": self.current_branch
            }
        except Exception as e:
            logger.error(f"Error pushing changes: {str(e)}")
            return {"status": "error", "message": f"Error pushing changes: {str(e)}"}
            
    def merge_branch(self, 
                   source_branch: str, 
                   target_branch: str = None,
                   commit_message: str = None) -> Dict[str, Any]:
        """
        Merge a branch into another
        
        Args:
            source_branch: Source branch for the merge
            target_branch: Target branch for the merge (current branch if None)
            commit_message: Merge commit message
            
        Returns:
            Status information
        """
        if not self.is_initialized:
            return {"status": "not_initialized", "message": "Repository not initialized"}
            
        if not target_branch:
            target_branch = self.current_branch
            
        try:
            # Checkout target branch
            if self.current_branch != target_branch:
                self._run_git_command(f"git checkout {target_branch}")
                
            # Create merge commit message if not provided
            if not commit_message:
                commit_message = f"Merge {source_branch} into {target_branch}"
                
            # Merge branch
            output = self._run_git_command(f"git merge {source_branch} -m \"{commit_message}\"")
            
            # Update current branch
            self._update_repo_status()
            
            return {
                "status": "success", 
                "message": f"Merged {source_branch} into {target_branch}", 
                "details": output.strip(),
                "branch": self.current_branch
            }
        except Exception as e:
            logger.error(f"Error merging branch: {str(e)}")
            return {"status": "error", "message": f"Error merging branch: {str(e)}"} 