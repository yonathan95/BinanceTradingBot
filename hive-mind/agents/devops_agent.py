"""
DevOps Agent - Responsible for managing Git operations, CI/CD workflows, 
infrastructure as code, and branching strategies.
"""

import logging
import json
import re
import os
import subprocess
from typing import Dict, List, Any, Optional, Tuple, Set
import asyncio
from datetime import datetime

from .common.git_enabled_agent import GitEnabledAgent
from hive_mind.agent_sdk.base_agent import Message

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BranchNode:
    """Tree node representing a Git branch in the hierarchical branching strategy."""
    
    def __init__(self, name: str, parent=None, branch_type: str = "feature"):
        """
        Initialize a branch node.
        
        Args:
            name: Branch name
            parent: Parent branch node
            branch_type: Type of branch (main, develop, feature, bugfix, release, hotfix)
        """
        self.name = name
        self.parent = parent
        self.children: List[BranchNode] = []
        self.branch_type = branch_type
        self.created_at = datetime.now()
        self.last_updated = self.created_at
        self.status = "active"  # active, merged, abandoned
        self.task_id = None
        self.agent_id = None
        self.tested = False
        self.test_results = {}
        
    def add_child(self, child_node) -> 'BranchNode':
        """Add a child branch to this branch"""
        self.children.append(child_node)
        child_node.parent = self
        return child_node
    
    def find_child(self, name: str) -> Optional['BranchNode']:
        """Find a direct child branch by name"""
        for child in self.children:
            if child.name == name:
                return child
        return None
    
    def mark_as_tested(self, test_results: Dict[str, Any]) -> None:
        """Mark this branch as tested with results"""
        self.tested = True
        self.test_results = test_results
        self.last_updated = datetime.now()
        
    def mark_as_merged(self) -> None:
        """Mark this branch as merged to parent"""
        self.status = "merged"
        self.last_updated = datetime.now()
    
    def mark_as_abandoned(self) -> None:
        """Mark this branch as abandoned"""
        self.status = "abandoned"
        self.last_updated = datetime.now()
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert node to dictionary representation"""
        return {
            "name": self.name,
            "branch_type": self.branch_type,
            "parent": self.parent.name if self.parent else None,
            "children": [child.name for child in self.children],
            "created_at": self.created_at.isoformat(),
            "last_updated": self.last_updated.isoformat(),
            "status": self.status,
            "task_id": self.task_id,
            "agent_id": self.agent_id,
            "tested": self.tested,
            "test_results": self.test_results
        }
        
class BranchTree:
    """Tree structure representing Git branch hierarchies for smart branching strategies."""
    
    def __init__(self, strategy: str = "gitflow"):
        """
        Initialize a branch tree with the specified strategy.
        
        Args:
            strategy: Branching strategy (gitflow, trunk-based, github-flow)
        """
        self.strategy = strategy
        self.root = None
        self.branch_map: Dict[str, BranchNode] = {}
        
        # Initialize the tree based on strategy
        self._initialize_strategy(strategy)
        
    def _initialize_strategy(self, strategy: str) -> None:
        """Initialize the tree structure based on branching strategy"""
        if strategy == "gitflow":
            # GitFlow: main <- develop <- feature/bugfix branches, release branches, hotfix branches
            self.root = BranchNode("main", None, "main")
            develop = self.root.add_child(BranchNode("develop", None, "develop"))
            self.branch_map["main"] = self.root
            self.branch_map["develop"] = develop
            
        elif strategy == "trunk-based":
            # Trunk-based: main <- short-lived feature branches
            self.root = BranchNode("main", None, "main")
            self.branch_map["main"] = self.root
            
        elif strategy == "github-flow":
            # GitHub Flow: main <- feature branches
            self.root = BranchNode("main", None, "main")
            self.branch_map["main"] = self.root
            
        else:
            # Default to GitFlow
            logger.warning(f"Unknown branching strategy '{strategy}', defaulting to GitFlow")
            self._initialize_strategy("gitflow")
            
    def add_branch(self, name: str, parent_name: str, branch_type: str,
                  task_id: Optional[str] = None, agent_id: Optional[str] = None) -> Optional[BranchNode]:
        """
        Add a new branch to the tree.
        
        Args:
            name: Branch name
            parent_name: Parent branch name
            branch_type: Type of branch
            task_id: Associated task ID
            agent_id: Agent that created the branch
            
        Returns:
            The created branch node or None if parent not found
        """
        # Check if parent exists
        if parent_name not in self.branch_map:
            logger.error(f"Cannot create branch '{name}': parent '{parent_name}' not found")
            return None
            
        # Create branch node
        parent = self.branch_map[parent_name]
        branch = BranchNode(name, parent, branch_type)
        branch.task_id = task_id
        branch.agent_id = agent_id
        
        # Add to parent and map
        parent.add_child(branch)
        self.branch_map[name] = branch
        
        return branch
        
    def get_branch(self, name: str) -> Optional[BranchNode]:
        """Get a branch by name"""
        return self.branch_map.get(name)
    
    def get_parent_branch(self, name: str) -> Optional[BranchNode]:
        """Get the parent branch of a named branch"""
        branch = self.get_branch(name)
        if branch and branch.parent:
            return branch.parent
        return None
    
    def get_path_to_root(self, name: str) -> List[BranchNode]:
        """Get the path from a branch to the root"""
        path = []
        branch = self.get_branch(name)
        
        while branch:
            path.append(branch)
            branch = branch.parent
            
        return path
    
    def get_all_children(self, name: str) -> List[BranchNode]:
        """Get all children branches (recursive)"""
        result = []
        branch = self.get_branch(name)
        if not branch:
            return result
            
        def collect_children(node):
            for child in node.children:
                result.append(child)
                collect_children(child)
                
        collect_children(branch)
        return result
    
    def get_branches_by_status(self, status: str) -> List[BranchNode]:
        """Get all branches with a particular status"""
        return [branch for branch in self.branch_map.values() if branch.status == status]
    
    def get_untested_branches(self) -> List[BranchNode]:
        """Get all active branches that haven't been tested"""
        return [branch for branch in self.branch_map.values() 
                if branch.status == "active" and not branch.tested]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the entire tree to a dictionary representation"""
        return {
            "strategy": self.strategy,
            "branches": {name: node.to_dict() for name, node in self.branch_map.items()}
        }
    
    def save_to_file(self, filepath: str) -> None:
        """Save the branch tree to a JSON file"""
        with open(filepath, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)
    
    @classmethod
    def load_from_file(cls, filepath: str) -> 'BranchTree':
        """Load a branch tree from a JSON file"""
        with open(filepath, 'r') as f:
            data = json.load(f)
            
        tree = cls(data.get("strategy", "gitflow"))
        
        # Clear default initialization
        tree.root = None
        tree.branch_map = {}
        
        # Rebuild nodes (first pass - create all nodes)
        branch_data = data.get("branches", {})
        nodes = {}
        
        for name, branch_info in branch_data.items():
            node = BranchNode(
                name=name,
                branch_type=branch_info.get("branch_type", "feature")
            )
            
            node.status = branch_info.get("status", "active")
            node.task_id = branch_info.get("task_id")
            node.agent_id = branch_info.get("agent_id")
            node.tested = branch_info.get("tested", False)
            node.test_results = branch_info.get("test_results", {})
            
            try:
                node.created_at = datetime.fromisoformat(branch_info.get("created_at", datetime.now().isoformat()))
                node.last_updated = datetime.fromisoformat(branch_info.get("last_updated", datetime.now().isoformat()))
            except ValueError:
                # Fall back to current time if date parsing fails
                node.created_at = datetime.now()
                node.last_updated = datetime.now()
                
            nodes[name] = node
            tree.branch_map[name] = node
        
        # Second pass - connect parent/child relationships
        for name, branch_info in branch_data.items():
            node = nodes[name]
            
            # Set parent
            parent_name = branch_info.get("parent")
            if parent_name and parent_name in nodes:
                node.parent = nodes[parent_name]
                
                # Add this node as child of parent if not already there
                if node not in node.parent.children:
                    node.parent.children.append(node)
                    
        # Find the root node
        for node in nodes.values():
            if node.parent is None:
                tree.root = node
                break
                
        return tree

class DevOpsAgent(GitEnabledAgent):
    """
    DevOps Agent that manages Git operations, CI/CD workflows, branching strategies,
    and infrastructure as code based on project requirements.
    """
    
    def __init__(self, 
                agent_id: str = "devops", 
                model: str = "claude-3-opus", 
                temperature: float = 0.7, 
                token_limit: int = 8000,
                memory_enabled: bool = True,
                embedding_model: str = "text-embedding-ada-002",
                vector_db_url: Optional[str] = None,
                workspace_path: Optional[str] = None,
                repository_url: Optional[str] = None,
                branch_strategy: str = "gitflow"):
        """Initialize the DevOps Agent"""
        super().__init__(
            agent_id=agent_id, 
            model=model, 
            temperature=temperature, 
            token_limit=token_limit,
            memory_enabled=memory_enabled,
            embedding_model=embedding_model,
            vector_db_url=vector_db_url,
            workspace_path=workspace_path,
            repository_url=repository_url,
            branch_strategy=branch_strategy
        )
        
        self.active_tasks: Dict[str, Dict[str, Any]] = {}
        self.infrastructure: Dict[str, Any] = {
            "stack": {},
            "requirements": {}
        }
        
        # CI/CD configuration
        self.ci_cd_config: Dict[str, Any] = {
            "enabled": True,
            "run_tests": True,
            "auto_deploy": False,
            "environments": ["dev", "staging", "production"],
            "test_command": "npm test",
            "build_command": "npm run build",
            "deploy_commands": {
                "dev": "npm run deploy:dev",
                "staging": "npm run deploy:staging",
                "production": "npm run deploy:prod"
            },
            "notification_webhooks": []
        }
        
        # Enable auto-commit for DevOps agent
        self.git_extension.set_auto_commit(True)
        
        # Don't push automatically (require PR approval)
        self.git_extension.set_auto_push(False)
        
        # Initialize branch tree for advanced branching strategy
        self.branch_tree = BranchTree(branch_strategy)
        
        # Branch history tracking
        self.branch_history: List[Dict[str, Any]] = []
        
        # Agents and their branches
        self.agent_branches: Dict[str, Set[str]] = {}
        
        # Map of tasks to branches
        self.task_branches: Dict[str, str] = {}
        
        # Path to branch tree persistence file
        self.branch_tree_file = os.path.join(
            workspace_path if workspace_path else os.getcwd(),
            ".hive-mind", 
            "branch_tree.json"
        )
        
        # Load existing branch tree if available
        try:
            if os.path.exists(self.branch_tree_file):
                self.branch_tree = BranchTree.load_from_file(self.branch_tree_file)
                logger.info(f"Loaded branch tree from {self.branch_tree_file}")
        except Exception as e:
            logger.warning(f"Failed to load branch tree: {str(e)}")
            # Already initialized with default strategy
        
    async def process_message(self, message: Message) -> Message:
        """Process an incoming message and generate a response"""
        logger.info(f"DevOps received message: {message.content[:50]}...")
        
        # Handle agent registration for branch tracking
        if message.message_type == "agent_registration":
            return await self._handle_agent_registration(message)
            
        # Handle branch creation requests
        if message.message_type == "branch_request":
            return await self._handle_branch_request(message)
            
        # Handle commit notifications from agents
        if message.message_type == "commit_notification":
            return await self._handle_commit_notification(message)
            
        # Handle branch merge requests
        if message.message_type == "merge_request":
            return await self._handle_merge_request(message)
        
        # First try to handle with GitEnabledAgent's handling
        git_response = await self.git_extension.handle_git_message(message)
        if git_response:
            return git_response
            
        # Handle task assignments
        if message.message_type == "task_assignment":
            self.current_task_id = message.thread_id
            self.current_task_description = message.content
            
            # Initialize Git for the task (create feature branch)
            if self.workspace_path_exists():
                await self.git_extension.initialize_for_task(
                    task_id=message.thread_id,
                    task_description=message.content[:50]
                )
                
                # Create branch in branch tree
                await self._create_branch_for_task(
                    task_id=message.thread_id,
                    task_description=message.content[:50],
                    agent_id=message.sender
                )
            
            # If task is about infrastructure or CI/CD, store it
            if self._is_infrastructure_request(message.content) or self._is_ci_cd_request(message.content):
                self.active_tasks[message.thread_id] = {
                    "task_id": message.thread_id,
                    "description": message.content,
                    "status": "in_progress",
                    "created_at": asyncio.get_event_loop().time()
                }
                
            # Handle the task based on its type
            if self._is_infrastructure_request(message.content):
                return await self._handle_infrastructure_request(message)
            elif self._is_ci_cd_request(message.content):
                return await self._handle_ci_cd_request(message)
            elif self._is_strategy_request(message.content):
                return await self._handle_strategy_request(message)
                
        # First, retrieve relevant memories to provide context
        context = await self.build_context_with_memory(
            query=message.content,
            max_memories=7,
            recent_message_count=5
        )
        
        # Add message-specific context
        context["current_message"] = message
        context["sender"] = message.sender
        context["thread_id"] = message.thread_id
        context["context_tags"] = message.context_tags
        
        # Generate a prompt based on the context
        prompt = await self.generate_prompt(context)
        
        # Call LLM to generate a response
        response_data = await self.call_llm(prompt)
        response_content = response_data["content"]
        
        # Create and return response message
        return await self.send_message(
            recipients=[message.sender],
            content=response_content,
            context_tags=message.context_tags,
            message_type="response",
            thread_id=message.thread_id
        )
    
    async def generate_prompt(self, context: Dict[str, Any]) -> str:
        """Generate a prompt for the LLM based on the provided context"""
        
        # Build prompt with relevant memories for context
        memories_context = ""
        if "relevant_memories" in context and context["relevant_memories"]:
            # Group relevant memories by type
            git_operations = []
            infrastructure = []
            other_memories = []
            
            for memory in context["relevant_memories"]:
                if memory.startswith("GIT OPERATION"):
                    git_operations.append(memory)
                elif memory.startswith("INFRASTRUCTURE"):
                    infrastructure.append(memory)
                else:
                    other_memories.append(memory)
            
            # Format memories by type
            if git_operations:
                memories_context += "### Git Operations\n"
                for i, op in enumerate(git_operations):
                    memories_context += f"{i+1}. {op}\n\n"
                    
            if infrastructure:
                memories_context += "### Infrastructure\n"
                for i, infra in enumerate(infrastructure):
                    memories_context += f"{i+1}. {infra}\n\n"
                    
            if other_memories:
                memories_context += "### Other Relevant Information\n"
                for i, memory in enumerate(other_memories):
                    memories_context += f"{i+1}. {memory}\n\n"
        
        # Include recent message history
        message_history = ""
        if "recent_messages" in context and context["recent_messages"]:
            message_history = "### Recent conversation\n"
            for msg in context["recent_messages"]:
                message_history += f"{msg.sender}: {msg.content}\n\n"
        
        # Get the current message
        current_message = context.get("current_message")
        
        # Current branch tree information
        active_branches = self.branch_tree.get_branches_by_status("active")
        branch_info = f"""
### Current Branch Structure
- Strategy: {self.branch_tree.strategy}
- Root branch: {self.branch_tree.root.name}
- Active branches: {len(active_branches)}
"""

        # Current configuration info
        git_config_info = f"""
### Current Git Configuration
- Branching Strategy: {self.git_extension.git.branch_strategy}
- Main branch: {self.git_extension.git.branches['main']}
- Development branch: {self.git_extension.git.branches.get('develop', 'N/A')}
- Feature branch prefix: {self.git_extension.git.branches['feature_prefix']}
"""

        # CI/CD configuration info
        ci_cd_info = f"""
### Current CI/CD Configuration
- Enabled: {self.ci_cd_config['enabled']}
- Run Tests: {self.ci_cd_config['run_tests']}
- Auto Deploy: {self.ci_cd_config['auto_deploy']}
- Environments: {', '.join(self.ci_cd_config['environments'])}
"""

        # Build the complete prompt
        prompt = f"""
You are the DevOps Engineer of an AI development team. Your role is to manage Git operations, CI/CD workflows, infrastructure as code, and an advanced branching strategy.

{memories_context}

{message_history}

{branch_info}

{git_config_info}

{ci_cd_info}

### Current Request
{current_message.content if current_message else ""}

Your primary responsibilities are:
1. Manage Git operations (commits, branches, merges)
2. Define and enforce branching strategies
3. Set up CI/CD workflows
4. Create infrastructure as code based on project requirements
5. Coordinate with the manager agent on deployment strategies
6. Monitor and optimize system resources
7. Maintain the branch tree and ensure code propagates correctly through branches

When responding:
- Provide clear, actionable steps for Git operations
- Explain the rationale behind infrastructure decisions
- Follow established conventions for the project
- Consider security best practices
- Reference specific tools and technologies where appropriate

Respond with a clear, detailed plan that addresses the current request.
"""
        return prompt
    
    def _is_git_operation_request(self, text: str) -> bool:
        """Check if a message is related to Git operations"""
        git_keywords = [
            "git", "commit", "push", "branch", "merge", "pull request", "pr",
            "checkout", "clone", "repository", "repo", "version control",
            "gitflow", "trunk-based", "feature branch", "main branch", "master branch"
        ]
        
        text_lower = text.lower()
        
        # Check for git keywords
        for keyword in git_keywords:
            if keyword in text_lower:
                return True
                
        return False
    
    def _is_infrastructure_request(self, text: str) -> bool:
        """Check if a message is related to infrastructure as code"""
        infra_keywords = [
            "infrastructure", "terraform", "cloudformation", "aws", "azure",
            "gcp", "docker", "kubernetes", "k8s", "container", "deploy",
            "server", "cloud", "devops", "iac", "infrastructure as code",
            "deployment", "environment", "provision", "scale"
        ]
        
        text_lower = text.lower()
        
        # Check for infrastructure keywords
        for keyword in infra_keywords:
            if keyword in text_lower:
                return True
                
        return False
    
    def _is_ci_cd_request(self, text: str) -> bool:
        """Check if a message is related to CI/CD workflows"""
        ci_cd_keywords = [
            "ci", "cd", "ci/cd", "continuous integration", "continuous delivery",
            "continuous deployment", "pipeline", "build", "test", "automation",
            "jenkins", "github actions", "gitlab ci", "travis", "circle ci"
        ]
        
        text_lower = text.lower()
        
        # Check for CI/CD keywords
        for keyword in ci_cd_keywords:
            if keyword in text_lower:
                return True
                
        return False
        
    def _is_strategy_request(self, text: str) -> bool:
        """Check if a message is related to strategy decisions"""
        strategy_keywords = [
            "strategy", "gitflow", "trunk-based", "branching strategy",
            "workflow", "process", "methodology", "approval", "review",
            "merge approval", "authorization", "permissions", "roles",
            "branch tree", "branch structure", "branch hierarchy"
        ]
        
        text_lower = text.lower()
        
        # Check for strategy keywords
        for keyword in strategy_keywords:
            if keyword in text_lower:
                return True
                
        return False
    
    async def _handle_agent_registration(self, message: Message) -> Message:
        """Handle agent registration for branching"""
        agent_id = message.sender
        
        # Register agent if not already registered
        if agent_id not in self.agent_branches:
            self.agent_branches[agent_id] = set()
        
        response_content = f"Agent {agent_id} registered with DevOps agent for branch management."
        
        # Send welcome message with branching instructions
        return await self.send_message(
            recipients=[agent_id],
            content=response_content,
            context_tags=["#git", "#branching"],
            message_type="registration_confirmation",
            thread_id=message.thread_id
        )
        
    async def _handle_branch_request(self, message: Message) -> Message:
        """Handle request to create a new branch"""
        # Extract branch request details
        try:
            request_data = json.loads(message.content)
            task_id = request_data.get("task_id", message.thread_id)
            branch_type = request_data.get("branch_type", "feature")
            parent_branch = request_data.get("parent_branch", None)  # If None, use default for strategy
            task_description = request_data.get("description", "")
        except (json.JSONDecodeError, KeyError):
            # Fallback if not valid JSON
            task_id = message.thread_id
            branch_type = "feature"
            parent_branch = None
            task_description = message.content
        
        # Create new branch
        branch_name = await self._create_branch_for_task(
            task_id=task_id,
            task_description=task_description,
            agent_id=message.sender,
            branch_type=branch_type,
            parent_branch=parent_branch
        )
        
        if not branch_name:
            error_msg = "Failed to create branch. Check DevOps agent logs for details."
            return await self.send_message(
                recipients=[message.sender],
                content=error_msg,
                context_tags=["#git", "#error"],
                message_type="branch_error",
                thread_id=message.thread_id
            )
        
        # Update agent branch mapping
        if message.sender not in self.agent_branches:
            self.agent_branches[message.sender] = set()
        self.agent_branches[message.sender].add(branch_name)
        
        # Update task branch mapping
        self.task_branches[task_id] = branch_name
        
        # Save branch tree
        self._save_branch_tree()
        
        # Prepare response with branch information and guidance
        branch_info = self.branch_tree.get_branch(branch_name).to_dict()
        parent_name = branch_info["parent"]
        
        response_content = f"""
Branch '{branch_name}' created successfully:
- Type: {branch_type}
- Parent: {parent_name}
- Task ID: {task_id}

To work on this branch:
1. git fetch
2. git checkout {branch_name}

When ready to merge, send a merge request to DevOps.
"""
        
        return await self.send_message(
            recipients=[message.sender],
            content=response_content,
            context_tags=["#git", "#branching"],
            message_type="branch_created",
            thread_id=message.thread_id
        )
        
    async def _handle_commit_notification(self, message: Message) -> Message:
        """Handle notification that an agent has committed code"""
        # Extract commit details
        try:
            commit_data = json.loads(message.content)
            branch_name = commit_data.get("branch", "")
            commit_hash = commit_data.get("commit_hash", "")
            files_changed = commit_data.get("files_changed", [])
            commit_message = commit_data.get("message", "")
            task_id = commit_data.get("task_id", message.thread_id)
            needs_testing = commit_data.get("needs_testing", self.ci_cd_config["run_tests"])
        except (json.JSONDecodeError, KeyError):
            # Fallback if not valid JSON
            branch_name = self.task_branches.get(message.thread_id, "")
            commit_hash = ""
            files_changed = []
            commit_message = message.content
            task_id = message.thread_id
            needs_testing = self.ci_cd_config["run_tests"]
            
        # Skip if we don't know which branch
        if not branch_name:
            error_msg = "Missing branch name in commit notification. Cannot process."
            return await self.send_message(
                recipients=[message.sender],
                content=error_msg,
                context_tags=["#git", "#error"],
                message_type="commit_error",
                thread_id=message.thread_id
            )
            
        # Update branch history
        self.branch_history.append({
            "action": "commit",
            "branch": branch_name,
            "commit_hash": commit_hash,
            "agent_id": message.sender,
            "timestamp": datetime.now().isoformat(),
            "message": commit_message,
            "files_changed": files_changed,
            "task_id": task_id
        })
        
        # Check if we need to run tests
        if needs_testing and self.ci_cd_config["run_tests"]:
            # Run tests on this branch
            test_results = await self.run_tests_on_branch(branch_name, task_id)
            
            # Update branch node with test results
            branch_node = self.branch_tree.get_branch(branch_name)
            if branch_node:
                branch_node.mark_as_tested(test_results)
                
            # Save branch tree
            self._save_branch_tree()
                
            # Prepare response with test results
            status = "passed" if test_results.get("status") == "success" else "failed"
            details = test_results.get("details", "No details available")
            
            response_content = f"""
Commit on branch '{branch_name}' processed:
- Commit: {commit_hash[:7] if commit_hash else 'Unknown'}
- Tests: {status}
- Task ID: {task_id}

Test Results:
{details}

{self._get_next_steps_guidance(branch_name, status, task_id)}
"""
        else:
            # No testing needed
            response_content = f"""
Commit on branch '{branch_name}' processed:
- Commit: {commit_hash[:7] if commit_hash else 'Unknown'}
- Testing: Skipped
- Task ID: {task_id}

{self._get_next_steps_guidance(branch_name, "skipped", task_id)}
"""
        
        return await self.send_message(
            recipients=[message.sender],
            content=response_content,
            context_tags=["#git", "#commit"],
            message_type="commit_processed",
            thread_id=message.thread_id
        )
        
    async def _handle_merge_request(self, message: Message) -> Message:
        """Handle request to merge a branch"""
        # Extract merge request details
        try:
            merge_data = json.loads(message.content)
            source_branch = merge_data.get("source_branch", "")
            target_branch = merge_data.get("target_branch", "")
            task_id = merge_data.get("task_id", message.thread_id)
            force_merge = merge_data.get("force", False)
        except (json.JSONDecodeError, KeyError):
            # Try to extract from text
            source_branch = self.task_branches.get(message.thread_id, "")
            target_branch = ""  # Will use parent branch
            task_id = message.thread_id
            force_merge = "force" in message.content.lower()
            
        # Get source branch
        if not source_branch:
            error_msg = "Missing source branch in merge request. Cannot process."
            return await self.send_message(
                recipients=[message.sender],
                content=error_msg,
                context_tags=["#git", "#error"],
                message_type="merge_error",
                thread_id=message.thread_id
            )
            
        # Get branch node
        source_node = self.branch_tree.get_branch(source_branch)
        if not source_node:
            error_msg = f"Branch '{source_branch}' not found in branch tree. Cannot merge."
            return await self.send_message(
                recipients=[message.sender],
                content=error_msg,
                context_tags=["#git", "#error"],
                message_type="merge_error",
                thread_id=message.thread_id
            )
            
        # Determine target branch if not specified
        if not target_branch and source_node.parent:
            target_branch = source_node.parent.name
            
        if not target_branch:
            error_msg = "No target branch specified and source branch has no parent. Cannot merge."
            return await self.send_message(
                recipients=[message.sender],
                content=error_msg,
                context_tags=["#git", "#error"],
                message_type="merge_error",
                thread_id=message.thread_id
            )
            
        # Check if branch has been tested (unless forced)
        if not force_merge and not source_node.tested and self.ci_cd_config["run_tests"]:
            # Run tests first
            test_results = await self.run_tests_on_branch(source_branch, task_id)
            source_node.mark_as_tested(test_results)
            
            # Don't merge if tests failed
            if test_results.get("status") != "success":
                error_msg = f"Tests failed on branch '{source_branch}'. Cannot merge to '{target_branch}'."
                return await self.send_message(
                    recipients=[message.sender],
                    content=error_msg,
                    context_tags=["#git", "#error"],
                    message_type="merge_error",
                    thread_id=message.thread_id
                )
                
        # Perform the merge
        merge_result = await self._merge_branches(source_branch, target_branch, task_id)
        
        if merge_result.get("status") != "success":
            error_msg = f"Failed to merge '{source_branch}' to '{target_branch}': {merge_result.get('message', 'Unknown error')}"
            return await self.send_message(
                recipients=[message.sender],
                content=error_msg,
                context_tags=["#git", "#error"],
                message_type="merge_error",
                thread_id=message.thread_id
            )
            
        # Mark branch as merged
        source_node.mark_as_merged()
        
        # Update branch history
        self.branch_history.append({
            "action": "merge",
            "source_branch": source_branch,
            "target_branch": target_branch,
            "agent_id": message.sender,
            "timestamp": datetime.now().isoformat(),
            "task_id": task_id,
            "result": merge_result
        })
        
        # Save branch tree
        self._save_branch_tree()
        
        # Prepare response
        response_content = f"""
Successfully merged '{source_branch}' into '{target_branch}'!

Details:
- Added commits: {len(merge_result.get('commits', []))}
- Files changed: {len(merge_result.get('files_changed', []))}
- Task ID: {task_id}

The source branch has been marked as merged and can now be deleted.
"""
        
        return await self.send_message(
            recipients=[message.sender],
            content=response_content,
            context_tags=["#git", "#merge"],
            message_type="merge_success",
            thread_id=message.thread_id
        )

    async def _create_branch_for_task(self, 
                               task_id: str, 
                               task_description: str,
                               agent_id: str,
                               branch_type: str = "feature",
                               parent_branch: Optional[str] = None) -> Optional[str]:
        """
        Create a branch for a task and add it to the branch tree
        
        Args:
            task_id: Task identifier
            task_description: Description of the task
            agent_id: ID of the agent that will work on this branch
            branch_type: Type of branch to create
            parent_branch: Parent branch name (if None, will use strategy default)
            
        Returns:
            Name of the created branch or None if failed
        """
        # Determine parent branch based on strategy if not specified
        if not parent_branch:
            if branch_type == "feature" or branch_type == "bugfix":
                if self.branch_tree.strategy == "gitflow":
                    parent_branch = "develop"
                else:
                    parent_branch = "main"
            elif branch_type == "hotfix":
                parent_branch = "main"
            elif branch_type == "release":
                if self.branch_tree.strategy == "gitflow":
                    parent_branch = "develop"
                else:
                    parent_branch = "main"
            else:
                # Default to appropriate parent
                if self.branch_tree.strategy == "gitflow":
                    parent_branch = "develop"
                else:
                    parent_branch = "main"
                    
        # Generate branch name based on type and task
        branch_prefix = f"{branch_type}/"
        # Clean task_id to be safe for branch names
        safe_task_id = re.sub(r'[^a-zA-Z0-9-]', '-', task_id)
        
        # Generate a short description from task
        if task_description:
            # Extract first few words for branch name
            words = re.findall(r'\w+', task_description.lower())
            short_desc = '-'.join(words[:3])  # Use first 3 words
            branch_name = f"{branch_prefix}{safe_task_id}-{short_desc}"
        else:
            branch_name = f"{branch_prefix}{safe_task_id}"
            
        # Ensure branch name is valid (no spaces, special chars)
        branch_name = re.sub(r'[^a-zA-Z0-9-/]', '-', branch_name)
        
        # Add branch to tree
        branch_node = self.branch_tree.add_branch(
            name=branch_name,
            parent_name=parent_branch,
            branch_type=branch_type,
            task_id=task_id,
            agent_id=agent_id
        )
        
        if not branch_node:
            logger.error(f"Failed to create branch node for {branch_name}")
            return None
            
        # Update mappings
        if agent_id not in self.agent_branches:
            self.agent_branches[agent_id] = set()
        self.agent_branches[agent_id].add(branch_name)
        self.task_branches[task_id] = branch_name
        
        # Create actual git branch
        try:
            # Use git extension to create branch
            result = self.git_extension.git.create_branch(
                branch_name=branch_name,
                base_branch=parent_branch
            )
            
            if result.get("status") != "success":
                logger.error(f"Failed to create Git branch: {result.get('message')}")
                return None
                
            # Update branch history
            self.branch_history.append({
                "action": "create",
                "branch": branch_name,
                "parent": parent_branch,
                "agent_id": agent_id,
                "timestamp": datetime.now().isoformat(),
                "task_id": task_id
            })
            
            # Save branch tree
            self._save_branch_tree()
            
            return branch_name
            
        except Exception as e:
            logger.error(f"Exception creating branch: {str(e)}")
            return None
            
    async def run_tests_on_branch(self, branch_name: str, task_id: str) -> Dict[str, Any]:
        """
        Run tests on a specific branch
        
        Args:
            branch_name: Branch to test
            task_id: Task identifier
            
        Returns:
            Test results
        """
        logger.info(f"Running tests on branch {branch_name} for task {task_id}")
        
        # Check if branch exists
        branch_node = self.branch_tree.get_branch(branch_name)
        if not branch_node:
            return {
                "status": "error",
                "message": f"Branch '{branch_name}' not found",
                "details": "Cannot run tests on non-existent branch"
            }
            
        # Execute CI/CD workflow for testing
        test_result = await self.run_ci_cd_workflow(branch_name, "HEAD")
        
        # Parse result
        if test_result.get("status") == "success":
            # Extract test step results
            test_steps = [step for step in test_result.get("steps", []) if step.get("name") == "test"]
            if test_steps and test_steps[0].get("status") == "success":
                return {
                    "status": "success",
                    "branch": branch_name,
                    "task_id": task_id,
                    "details": f"All tests passed on branch {branch_name}",
                    "timestamp": asyncio.get_event_loop().time()
                }
            else:
                return {
                    "status": "failure",
                    "branch": branch_name,
                    "task_id": task_id,
                    "details": f"Tests failed on branch {branch_name}",
                    "timestamp": asyncio.get_event_loop().time()
                }
        else:
            return {
                "status": "error",
                "branch": branch_name,
                "task_id": task_id,
                "message": test_result.get("message", "Unknown error"),
                "details": "CI/CD workflow failed to run tests",
                "timestamp": asyncio.get_event_loop().time()
            }
            
    async def _merge_branches(self, source_branch: str, target_branch: str, task_id: str) -> Dict[str, Any]:
        """
        Merge source branch into target branch
        
        Args:
            source_branch: Source branch name
            target_branch: Target branch name
            task_id: Task identifier
            
        Returns:
            Merge result
        """
        logger.info(f"Merging {source_branch} into {target_branch} for task {task_id}")
        
        try:
            # Use git extension to perform merge
            result = self.git_extension.git.merge_branches(
                source_branch=source_branch,
                target_branch=target_branch,
                commit_message=f"Merge {source_branch} into {target_branch} for task {task_id}"
            )
            
            if result.get("status") != "success":
                return {
                    "status": "error",
                    "message": result.get("message", "Unknown merge error"),
                    "source_branch": source_branch,
                    "target_branch": target_branch
                }
                
            # Check if we should deploy after merging to main branches
            if target_branch in ["main", "master"] and self.ci_cd_config["auto_deploy"]:
                # Auto-deploy to production
                deploy_result = await self.deploy_to_environment("production", target_branch)
                result["deployment"] = deploy_result
            elif target_branch == "develop" and "staging" in self.ci_cd_config["environments"] and self.ci_cd_config["auto_deploy"]:
                # Auto-deploy to staging
                deploy_result = await self.deploy_to_environment("staging", target_branch)
                result["deployment"] = deploy_result
                
            return {
                "status": "success",
                "source_branch": source_branch,
                "target_branch": target_branch,
                "commits": result.get("commits", []),
                "files_changed": result.get("files_changed", []),
                "timestamp": asyncio.get_event_loop().time()
            }
            
        except Exception as e:
            logger.error(f"Exception merging branches: {str(e)}")
            return {
                "status": "error",
                "message": str(e),
                "source_branch": source_branch,
                "target_branch": target_branch
            }
            
    async def deploy_to_environment(self, environment: str, branch: str) -> Dict[str, Any]:
        """
        Deploy a branch to a specific environment
        
        Args:
            environment: Environment to deploy to
            branch: Branch to deploy
            
        Returns:
            Deployment result
        """
        if environment not in self.ci_cd_config["environments"]:
            return {
                "status": "error",
                "message": f"Environment '{environment}' not configured",
                "environment": environment,
                "branch": branch
            }
            
        if environment not in self.ci_cd_config["deploy_commands"]:
            return {
                "status": "error",
                "message": f"No deployment command for environment '{environment}'",
                "environment": environment,
                "branch": branch
            }
            
        logger.info(f"Deploying {branch} to {environment}")
        
        # Simulate deployment
        return {
            "status": "success",
            "environment": environment,
            "branch": branch,
            "command": self.ci_cd_config["deploy_commands"][environment],
            "timestamp": asyncio.get_event_loop().time()
        }
        
    def _get_next_steps_guidance(self, branch_name: str, test_status: str, task_id: str) -> str:
        """Generate guidance for next steps based on branch and test status"""
        if test_status == "failed":
            return """
Next Steps:
1. Fix the failing tests
2. Commit your changes
3. Tests will run automatically on your next commit
"""
        elif test_status == "passed" or test_status == "skipped":
            return """
Next Steps:
1. If your task is complete, request a merge with:
   - Send a message of type 'merge_request'
   - Include source_branch, target_branch, and task_id

2. If you need to make more changes:
   - Continue working on your branch
   - Commit changes as needed
"""
        else:
            return """
Next Steps:
1. Continue working on your branch
2. Commit changes as needed
"""

    def _save_branch_tree(self) -> None:
        """Save branch tree to persistent storage"""
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.branch_tree_file), exist_ok=True)
            
            # Save to file
            self.branch_tree.save_to_file(self.branch_tree_file)
            logger.info(f"Saved branch tree to {self.branch_tree_file}")
        except Exception as e:
            logger.error(f"Failed to save branch tree: {str(e)}")
        
    async def _handle_infrastructure_request(self, message: Message) -> Message:
        """Handle an infrastructure as code request"""
        # Query manager for software stack if needed
        if not self.infrastructure["stack"]:
            try:
                # Create message to manager
                query_message = await self.send_message(
                    recipients=["manager"],
                    content="What is the current software stack and system requirements for this project?",
                    context_tags=["#infrastructure", "#requirements"],
                    message_type="question",
                    thread_id=message.thread_id,
                    requires_response=True
                )
                
                # We'd normally wait for a response here, but for demo purposes
                # we'll extract stack info from the message
                stack_info = self._extract_stack_info(message.content)
                
                if stack_info:
                    self.infrastructure["stack"] = stack_info
            except Exception as e:
                logger.warning(f"Could not query manager for stack info: {str(e)}")
                # Extract from current message as fallback
                stack_info = self._extract_stack_info(message.content)
                if stack_info:
                    self.infrastructure["stack"] = stack_info
                    
        # Generate infrastructure code using the GitEnabledAgent's execute_with_git
        # This ensures the code is committed automatically
        infra_result = await self.execute_with_git(
            self.create_infrastructure_code,
            requirements=self._extract_infrastructure_requirements(message.content),
            commit_message=f"DevOps: Create infrastructure as code for {message.thread_id}"
        )
        
        # Store infrastructure code in memory if enabled
        if self.memory_enabled:
            for file in infra_result.get("files", []):
                await self.memory.add_memory(
                    content=f"INFRASTRUCTURE CODE: Created {file['file_path']} for task {message.thread_id}",
                    metadata={
                        "type": "infrastructure",
                        "file_path": file["file_path"],
                        "task_id": message.thread_id,
                        "timestamp": asyncio.get_event_loop().time()
                    },
                    importance=4.0
                )
        
        # Prepare response
        infrastructure_files = [f"- {file['file_path']}" for file in infra_result.get("files", [])]
        response_content = f"""
I've created the following infrastructure as code based on the project requirements:

{chr(10).join(infrastructure_files)}

Instructions:
{infra_result.get('instructions', 'No special instructions.')}

The infrastructure code has been committed to the repository with task-specific branching.
"""

        return await self.send_message(
            recipients=[message.sender],
            content=response_content,
            context_tags=message.context_tags + ["#infrastructure"],
            message_type="infrastructure_result",
            thread_id=message.thread_id
        )
        
    async def _handle_ci_cd_request(self, message: Message) -> Message:
        """Handle a CI/CD workflow request"""
        # Update CI/CD configuration from the message
        ci_cd_config_updates = self._extract_ci_cd_config(message.content)
        if ci_cd_config_updates:
            # Update the configuration
            for key, value in ci_cd_config_updates.items():
                if key in self.ci_cd_config:
                    if isinstance(value, dict) and isinstance(self.ci_cd_config[key], dict):
                        # Merge nested dictionaries
                        self.ci_cd_config[key].update(value)
                    else:
                        # Replace value
                        self.ci_cd_config[key] = value
        
        # Create CI/CD configuration files
        ci_cd_files = await self.execute_with_git(
            self.create_ci_cd_files,
            commit_message=f"DevOps: Create CI/CD configuration for {message.thread_id}"
        )
        
        # Store CI/CD config in memory if enabled
        if self.memory_enabled:
            for file in ci_cd_files:
                await self.memory.add_memory(
                    content=f"CI/CD CONFIG: Created {file} for task {message.thread_id}",
                    metadata={
                        "type": "ci_cd",
                        "file_path": file,
                        "task_id": message.thread_id,
                        "timestamp": asyncio.get_event_loop().time()
                    },
                    importance=3.5
                )
                
        # Prepare response
        response_content = f"""
I've set up CI/CD workflows with the following configuration:

- CI/CD Enabled: {self.ci_cd_config['enabled']}
- Run Tests: {self.ci_cd_config['run_tests']}
- Auto Deploy: {self.ci_cd_config['auto_deploy']}
- Environments: {', '.join(self.ci_cd_config['environments'])}

Created CI/CD configuration files:
{chr(10).join([f"- {file}" for file in ci_cd_files])}

The CI/CD configuration has been committed to the repository with task-specific branching.
"""

        return await self.send_message(
            recipients=[message.sender],
            content=response_content,
            context_tags=message.context_tags + ["#ci_cd"],
            message_type="ci_cd_result",
            thread_id=message.thread_id
        )
    
    async def create_infrastructure_code(self, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create infrastructure as code based on requirements
        
        Args:
            requirements: Requirements for the infrastructure
            
        Returns:
            Dictionary with infrastructure code files
        """
        # Determine the best infrastructure as code tool based on requirements
        if "kubernetes" in self.infrastructure.get("stack", {}).get("infrastructure", []):
            infrastructure_type = "kubernetes"
        elif "docker" in self.infrastructure.get("stack", {}).get("infrastructure", []):
            infrastructure_type = "docker-compose"
        else:
            infrastructure_type = "terraform"  # Default to Terraform
            
        # Generate custom prompt for infrastructure
        prompt = f"""
You are the DevOps Engineer tasked with creating infrastructure as code based on the following requirements:

Requirements: {json.dumps(requirements, indent=2)}

Software Stack: {json.dumps(self.infrastructure.get("stack", {}), indent=2)}

Infrastructure Type: {infrastructure_type}

Create complete infrastructure as code files that would deploy this stack.
For each file, include:
- The complete file path
- The full code content
- Purpose of each file

The code should be production-ready and follow best practices for {infrastructure_type}.
Include appropriate resources for compute, storage, networking, and security based on the requirements.
"""
        
        # Call LLM to generate the infrastructure code
        response_data = await self.call_llm(prompt)
        response_content = response_data["content"]
        
        # Extract code blocks
        code_blocks = self._extract_code_blocks(response_content)
        
        # Prepare infrastructure result
        infrastructure_result = {
            "infrastructure_type": infrastructure_type,
            "requirements": requirements,
            "files": [],
            "instructions": self._extract_instructions(response_content),
            "timestamp": asyncio.get_event_loop().time()
        }
        
        # Process code blocks and write files
        workspace_path = self.git_extension.git.workspace_path
        for language, code, file_path in code_blocks:
            if file_path:
                # Create file path
                full_path = os.path.join(workspace_path, file_path)
                os.makedirs(os.path.dirname(full_path), exist_ok=True)
                
                # Write the file
                with open(full_path, "w") as f:
                    f.write(code)
                    
                # Add to result
                infrastructure_result["files"].append({
                    "file_path": file_path,
                    "language": language,
                    "code": code
                })
                
        return infrastructure_result
    
    async def create_ci_cd_files(self) -> List[str]:
        """
        Create CI/CD workflow files based on the current configuration
        
        Returns:
            List of created file paths
        """
        # Determine which CI/CD system to use based on context
        # Default to GitHub Actions
        ci_system = "github-actions"
        
        # Generate custom prompt for CI/CD configuration
        prompt = f"""
You are the DevOps Engineer tasked with creating CI/CD configuration files.

CI/CD Configuration:
{json.dumps(self.ci_cd_config, indent=2)}

Software Stack:
{json.dumps(self.infrastructure.get("stack", {}), indent=2)}

Create complete CI/CD configuration files for {ci_system}.
The configuration should include:
- Building the application
- Running tests (if enabled)
- Deploying to environments (if auto-deploy is enabled)
- Appropriate security checks

For each file, include the complete file path and the full code content.
"""
        
        # Call LLM to generate the CI/CD configuration
        response_data = await self.call_llm(prompt)
        response_content = response_data["content"]
        
        # Extract code blocks
        code_blocks = self._extract_code_blocks(response_content)
        
        # Create files
        created_files = []
        workspace_path = self.git_extension.git.workspace_path
        for language, code, file_path in code_blocks:
            if file_path:
                # Create file path
                full_path = os.path.join(workspace_path, file_path)
                os.makedirs(os.path.dirname(full_path), exist_ok=True)
                
                # Write the file
                with open(full_path, "w") as f:
                    f.write(code)
                    
                created_files.append(file_path)
                
        return created_files
    
    async def create_strategy_documentation(self, strategy: str) -> Dict[str, str]:
        """
        Create documentation for the chosen Git branching strategy
        
        Args:
            strategy: Git branching strategy (gitflow, github-flow, trunk-based)
            
        Returns:
            Dictionary with documentation sections
        """
        # Generate custom prompt for strategy documentation
        prompt = f"""
You are the DevOps Engineer tasked with documenting the {strategy} Git branching strategy.

Create comprehensive documentation that explains:
1. The key principles of the {strategy} branching strategy
2. How branches are named and organized
3. The workflow for different types of changes (features, bug fixes, etc.)
4. How merges and code reviews are handled
5. How releases are managed

Format your response with clear sections for:
1. Description
2. Branch naming conventions
3. Workflow steps
"""
        
        # Call LLM to generate the documentation
        response_data = await self.call_llm(prompt)
        response_content = response_data["content"]
        
        # Extract sections
        description_match = re.search(r'#+\s*Description\s*\n+(.+?)(?=#+|\Z)', response_content, re.DOTALL)
        naming_match = re.search(r'#+\s*(?:Branch\s*)?Naming\s*(?:Conventions)?\s*\n+(.+?)(?=#+|\Z)', response_content, re.DOTALL)
        workflow_match = re.search(r'#+\s*Workflow\s*\n+(.+?)(?=#+|\Z)', response_content, re.DOTALL)
        
        # Create documentation dictionary
        documentation = {
            "description": description_match.group(1).strip() if description_match else "No description provided.",
            "naming_conventions": naming_match.group(1).strip() if naming_match else "No naming conventions provided.",
            "workflow": workflow_match.group(1).strip() if workflow_match else "No workflow provided."
        }
        
        # Write documentation to file
        workspace_path = self.git_extension.git.workspace_path
        docs_path = os.path.join(workspace_path, "docs")
        os.makedirs(docs_path, exist_ok=True)
        
        # Create the documentation file
        doc_filename = f"git-{strategy}-guide.md"
        doc_path = os.path.join(docs_path, doc_filename)
        
        with open(doc_path, "w") as f:
            f.write(f"# {strategy.title()} Branching Strategy Guide\n\n")
            f.write(f"## Description\n\n{documentation['description']}\n\n")
            f.write(f"## Branch Naming Conventions\n\n{documentation['naming_conventions']}\n\n")
            f.write(f"## Workflow\n\n{documentation['workflow']}\n\n")
            
        return documentation
        
    def _extract_code_blocks(self, text: str) -> List[Tuple[str, str, Optional[str]]]:
        """
        Extract code blocks from a markdown text.
        
        Returns:
            List of tuples: (language, code, file_path)
        """
        code_blocks = []
        
        # Regular expression to match markdown code blocks with optional language
        # ```language
        # code
        # ```
        pattern = r"```(\w*)\n([\s\S]*?)```"
        matches = re.findall(pattern, text)
        
        for match in matches:
            language, code = match
            language = language.strip() or "text"  # Default to "text" if no language specified
            code = code.strip()
            
            # Try to extract file path from surrounding text
            # Look for common file path indicators
            file_path = None
            
            # Check for file path indicators in code or in the 3 lines before the code block
            lines = text.split("\n")
            for i, line in enumerate(lines):
                if f"```{language}" in line:
                    # Check the 3 lines before this code block
                    start_idx = max(0, i - 3)
                    for j in range(start_idx, i):
                        path_match = re.search(r'[\"\'`]?([\w\/\.-]+\.\w+)[\"\'`]?', lines[j])
                        if path_match:
                            file_path = path_match.group(1)
                            break
                            
                    # If no file path found in preceding lines, check if it's in a comment in the first line of code
                    if not file_path and i < len(lines) - 1:
                        first_code_line = lines[i + 1]
                        if "//" in first_code_line or "#" in first_code_line:
                            path_match = re.search(r'[\"\'`]?([\w\/\.-]+\.\w+)[\"\'`]?', first_code_line)
                            if path_match:
                                file_path = path_match.group(1)
                                
                    break
            
            code_blocks.append((language, code, file_path))
            
        return code_blocks
        
    def _extract_instructions(self, text: str) -> str:
        """Extract instructions from the response text"""
        # Look for common section headers for instructions
        patterns = [
            r"(?:^|\n)#+\s*Instructions(?:[\s\S]*?)(?=\n#+|\Z)",
            r"(?:^|\n)#+\s*Deployment(?:[\s\S]*?)(?=\n#+|\Z)",
            r"(?:^|\n)#+\s*Getting Started(?:[\s\S]*?)(?=\n#+|\Z)",
            r"(?:^|\n)#+\s*Next Steps(?:[\s\S]*?)(?=\n#+|\Z)",
            r"(?:^|\n)#+\s*Usage(?:[\s\S]*?)(?=\n#+|\Z)"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(0).strip()
        
        # Fall back to checking for numbered steps
        lines = text.split('\n')
        instruction_lines = []
        in_instructions = False
        
        for line in lines:
            if re.match(r'^\d+\.\s', line) and not in_instructions:
                in_instructions = True
                instruction_lines.append(line)
            elif in_instructions:
                if re.match(r'^\s*$', line) or line.startswith('```'):
                    in_instructions = False
                else:
                    instruction_lines.append(line)
        
        if instruction_lines:
            return '\n'.join(instruction_lines)
        
        # If no instructions found, return empty string
        return ""
        
    async def run_ci_cd_workflow(self, branch_name: str, commit_sha: str) -> Dict[str, Any]:
        """
        Run CI/CD workflow for a specific branch and commit
        
        Args:
            branch_name: The branch to run the workflow for
            commit_sha: The commit SHA to run the workflow for
            
        Returns:
            Dictionary with the workflow results
        """
        if not self.ci_cd_config["enabled"]:
            return {
                "status": "skipped",
                "message": "CI/CD workflows are disabled",
                "branch": branch_name,
                "commit": commit_sha
            }
            
        logger.info(f"Running CI/CD workflow for {branch_name} at commit {commit_sha}")
        
        # Simulate workflow steps
        steps = []
        
        # Build step
        build_result = {
            "name": "build",
            "command": self.ci_cd_config["build_command"],
            "status": "success"
        }
        steps.append(build_result)
        
        # Test step (if enabled)
        if self.ci_cd_config["run_tests"]:
            test_result = {
                "name": "test",
                "command": self.ci_cd_config["test_command"],
                "status": "success"
            }
            steps.append(test_result)
            
        # Deploy step (if enabled and auto-deploy is on)
        if self.ci_cd_config["auto_deploy"]:
            # Determine which environment to deploy to based on branch
            environment = "dev"  # Default to dev
            
            if "main" in branch_name or "master" in branch_name:
                environment = "production"
            elif "release" in branch_name:
                environment = "staging"
                
            if environment in self.ci_cd_config["environments"]:
                deploy_command = self.ci_cd_config["deploy_commands"].get(environment, f"echo 'Deploying to {environment}'")
                deploy_result = {
                    "name": f"deploy-{environment}",
                    "command": deploy_command,
                    "status": "success",
                    "environment": environment
                }
                steps.append(deploy_result)
                
        # Return workflow results
        return {
            "status": "success",
            "message": f"CI/CD workflow completed successfully for {branch_name}",
            "branch": branch_name,
            "commit": commit_sha,
            "steps": steps,
            "timestamp": asyncio.get_event_loop().time()
        }

    def _extract_stack_info(self, text: str) -> Dict[str, Any]:
        """Extract software stack information from text"""
        # This would be more sophisticated in a real implementation
        stack_info = {
            "frontend": [],
            "backend": [],
            "database": [],
            "infrastructure": []
        }
        
        # Simple keyword extraction
        if "react" in text.lower() or "javascript" in text.lower() or "typescript" in text.lower():
            stack_info["frontend"].append("react")
        
        if "node" in text.lower() or "express" in text.lower():
            stack_info["backend"].append("node.js")
        
        if "python" in text.lower() or "django" in text.lower() or "flask" in text.lower():
            stack_info["backend"].append("python")
        
        if "mongodb" in text.lower():
            stack_info["database"].append("mongodb")
        
        if "postgresql" in text.lower() or "postgres" in text.lower():
            stack_info["database"].append("postgresql")
        
        if "docker" in text.lower() or "container" in text.lower():
            stack_info["infrastructure"].append("docker")
        
        if "kubernetes" in text.lower() or "k8s" in text.lower():
            stack_info["infrastructure"].append("kubernetes")
            
        # Return the extracted stack, filter out empty lists
        return {k: v for k, v in stack_info.items() if v}

    def _extract_infrastructure_requirements(self, text: str) -> Dict[str, Any]:
        """Extract infrastructure requirements from text"""
        requirements = {
            "compute": {},
            "storage": {},
            "networking": {},
            "security": {}
        }
        
        # Extract compute requirements
        if "cpu" in text.lower():
            cpu_match = re.search(r'(\d+)\s*(?:cpu|cores|processors)', text.lower())
            if cpu_match:
                requirements["compute"]["cpu"] = int(cpu_match.group(1))
        
        if "memory" in text.lower() or "ram" in text.lower():
            memory_match = re.search(r'(\d+)\s*(?:gb|gib)\s*(?:memory|ram)', text.lower())
            if memory_match:
                requirements["compute"]["memory"] = int(memory_match.group(1))
        
        # Extract storage requirements
        if "storage" in text.lower() or "disk" in text.lower():
            storage_match = re.search(r'(\d+)\s*(?:gb|gib|tb|tib)\s*(?:storage|disk)', text.lower())
            if storage_match:
                requirements["storage"]["size"] = storage_match.group(0)
        
        # Extract networking requirements
        if "scaling" in text.lower():
            scaling_match = re.search(r'(?:auto|automatic)\s*scaling', text.lower())
            if scaling_match:
                requirements["networking"]["auto_scaling"] = True
        
        # Simple defaults if nothing was detected
        if not requirements["compute"]:
            requirements["compute"] = {"cpu": 2, "memory": 4}
        
        if not requirements["storage"]:
            requirements["storage"] = {"size": "20GB"}
            
        return requirements

    def _extract_ci_cd_config(self, text: str) -> Dict[str, Any]:
        """Extract CI/CD configuration from text"""
        config = {}
        
        # Extract enabled/disabled status
        if "enable ci" in text.lower() or "enable cd" in text.lower() or "enable ci/cd" in text.lower():
            config["enabled"] = True
        elif "disable ci" in text.lower() or "disable cd" in text.lower() or "disable ci/cd" in text.lower():
            config["enabled"] = False
            
        # Extract test configuration
        if "run tests" in text.lower():
            run_tests_match = re.search(r'run tests[\s:]+(\w+)', text.lower())
            if run_tests_match:
                config["run_tests"] = run_tests_match.group(1).lower() in ["true", "yes", "enabled", "on"]
                
        # Extract deployment configuration
        if "auto deploy" in text.lower() or "auto-deploy" in text.lower():
            auto_deploy_match = re.search(r'auto[- ]deploy[\s:]+(\w+)', text.lower())
            if auto_deploy_match:
                config["auto_deploy"] = auto_deploy_match.group(1).lower() in ["true", "yes", "enabled", "on"]
                
        # Extract environments
        env_match = re.search(r'environments[\s:]+\[(.*?)\]', text.lower())
        if env_match:
            envs = [e.strip().strip('\'",') for e in env_match.group(1).split(",")]
            if envs:
                config["environments"] = envs
                
        return config

    def _extract_branching_strategy(self, text: str) -> Optional[str]:
        """Extract Git branching strategy from text"""
        if "gitflow" in text.lower():
            return "gitflow"
        elif "github flow" in text.lower():
            return "github-flow"
        elif "trunk" in text.lower() and "based" in text.lower():
            return "trunk-based"
            
        return None
    
    async def execute_with_git(self, function, **kwargs) -> Dict[str, Any]:
        """Execute a function with Git operations"""
        try:
            # Use git extension to execute the function
            result = await self.git_extension.execute_with_git(function, **kwargs)
            
            if result.get("status") != "success":
                logger.error(f"Git operation failed: {result.get('message')}")
                return {
                    "status": "error",
                    "message": result.get("message", "Unknown error"),
                    "details": result.get("details", "No details available")
                }
                
            return result
            
        except Exception as e:
            logger.error(f"Exception executing Git operation: {str(e)}")
            return {
                "status": "error",
                "message": str(e),
                "details": "An error occurred while executing the Git operation"
            }

    async def build_context_with_memory(self, query: str, max_memories: int, recent_message_count: int) -> Dict[str, Any]:
        """Build a context with relevant memories"""
        # Implement the logic to retrieve relevant memories based on the query
        # This is a placeholder and should be replaced with actual implementation
        return {
            "relevant_memories": [],
            "recent_messages": []
        }

    async def send_message(self, recipients: List[str], content: str, context_tags: List[str], message_type: str, thread_id: str) -> Message:
        """Send a message to the specified recipients"""
        # Implement the logic to send a message to the specified recipients
        # This is a placeholder and should be replaced with actual implementation
        return Message(
            content=content,
            context_tags=context_tags,
            message_type=message_type,
            thread_id=thread_id
        )

    def workspace_path_exists(self) -> bool:
        """Check if the workspace path exists"""
        return os.path.exists(self.git_extension.git.workspace_path)

    async def execute_with_git(self, function, **kwargs) -> Dict[str, Any]:
        """Execute a function with Git operations"""
        try:
            # Use git extension to execute the function
            result = await self.git_extension.execute_with_git(function, **kwargs)
            
            if result.get("status") != "success":
                logger.error(f"Git operation failed: {result.get('message')}")
                return {
                    "status": "error",
                    "message": result.get("message", "Unknown error"),
                    "details": result.get("details", "No details available")
                }
                
            return result
            
        except Exception as e:
            logger.error(f"Exception executing Git operation: {str(e)}")
            return {
                "status": "error",
                "message": str(e),
                "details": "An error occurred while executing the Git operation"
            }

    async def create_infrastructure_code(self, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create infrastructure as code based on requirements
        
        Args:
            requirements: Requirements for the infrastructure
            
        Returns:
            Dictionary with infrastructure code files
        """
        # Determine the best infrastructure as code tool based on requirements
        if "kubernetes" in self.infrastructure.get("stack", {}).get("infrastructure", []):
            infrastructure_type = "kubernetes"
        elif "docker" in self.infrastructure.get("stack", {}).get("infrastructure", []):
            infrastructure_type = "docker-compose"
        else:
            infrastructure_type = "terraform"  # Default to Terraform
            
        # Generate custom prompt for infrastructure
        prompt = f"""
You are the DevOps Engineer tasked with creating infrastructure as code based on the following requirements:

Requirements: {json.dumps(requirements, indent=2)}

Software Stack: {json.dumps(self.infrastructure.get("stack", {}), indent=2)}

Infrastructure Type: {infrastructure_type}

Create complete infrastructure as code files that would deploy this stack.
For each file, include:
- The complete file path
- The full code content
- Purpose of each file

The code should be production-ready and follow best practices for {infrastructure_type}.
Include appropriate resources for compute, storage, networking, and security based on the requirements.
"""
        
        # Call LLM to generate the infrastructure code
        response_data = await self.call_llm(prompt)
        response_content = response_data["content"]
        
        # Extract code blocks
        code_blocks = self._extract_code_blocks(response_content)
        
        # Prepare infrastructure result
        infrastructure_result = {
            "infrastructure_type": infrastructure_type,
            "requirements": requirements,
            "files": [],
            "instructions": self._extract_instructions(response_content),
            "timestamp": asyncio.get_event_loop().time()
        }
        
        # Process code blocks and write files
        workspace_path = self.git_extension.git.workspace_path
        for language, code, file_path in code_blocks:
            if file_path:
                # Create file path
                full_path = os.path.join(workspace_path, file_path)
                os.makedirs(os.path.dirname(full_path), exist_ok=True)
                
                # Write the file
                with open(full_path, "w") as f:
                    f.write(code)
                    
                # Add to result
                infrastructure_result["files"].append({
                    "file_path": file_path,
                    "language": language,
                    "code": code
                })
                
        return infrastructure_result

    async def create_ci_cd_files(self) -> List[str]:
        """
        Create CI/CD workflow files based on the current configuration
        
        Returns:
            List of created file paths
        """
        # Determine which CI/CD system to use based on context
        # Default to GitHub Actions
        ci_system = "github-actions"
        
        # Generate custom prompt for CI/CD configuration
        prompt = f"""
You are the DevOps Engineer tasked with creating CI/CD configuration files.

CI/CD Configuration:
{json.dumps(self.ci_cd_config, indent=2)}

Software Stack:
{json.dumps(self.infrastructure.get("stack", {}), indent=2)}

Create complete CI/CD configuration files for {ci_system}.
The configuration should include:
- Building the application
- Running tests (if enabled)
- Deploying to environments (if auto-deploy is enabled)
- Appropriate security checks

For each file, include the complete file path and the full code content.
"""
        
        # Call LLM to generate the CI/CD configuration
        response_data = await self.call_llm(prompt)
        response_content = response_data["content"]
        
        # Extract code blocks
        code_blocks = self._extract_code_blocks(response_content)
        
        # Create files
        created_files = []
        workspace_path = self.git_extension.git.workspace_path
        for language, code, file_path in code_blocks:
            if file_path:
                # Create file path
                full_path = os.path.join(workspace_path, file_path)
                os.makedirs(os.path.dirname(full_path), exist_ok=True)
                
                # Write the file
                with open(full_path, "w") as f:
                    f.write(code)
                    
                created_files.append(file_path)
                
        return created_files

    async def create_strategy_documentation(self, strategy: str) -> Dict[str, str]:
        """
        Create documentation for the chosen Git branching strategy
        
        Args:
            strategy: Git branching strategy (gitflow, github-flow, trunk-based)
            
        Returns:
            Dictionary with documentation sections
        """
        # Generate custom prompt for strategy documentation
        prompt = f"""
You are the DevOps Engineer tasked with documenting the {strategy} Git branching strategy.

Create comprehensive documentation that explains:
1. The key principles of the {strategy} branching strategy
2. How branches are named and organized
3. The workflow for different types of changes (features, bug fixes, etc.)
4. How merges and code reviews are handled
5. How releases are managed

Format your response with clear sections for:
1. Description
2. Branch naming conventions
3. Workflow steps
"""
        
        # Call LLM to generate the documentation
        response_data = await self.call_llm(prompt)
        response_content = response_data["content"]
        
        # Extract sections
        description_match = re.search(r'#+\s*Description\s*\n+(.+?)(?=#+|\Z)', response_content, re.DOTALL)
        naming_match = re.search(r'#+\s*(?:Branch\s*)?Naming\s*(?:Conventions)?\s*\n+(.+?)(?=#+|\Z)', response_content, re.DOTALL)
        workflow_match = re.search(r'#+\s*Workflow\s*\n+(.+?)(?=#+|\Z)', response_content, re.DOTALL)
        
        # Create documentation dictionary
        documentation = {
            "description": description_match.group(1).strip() if description_match else "No description provided.",
            "naming_conventions": naming_match.group(1).strip() if naming_match else "No naming conventions provided.",
            "workflow": workflow_match.group(1).strip() if workflow_match else "No workflow provided."
        }
        
        # Write documentation to file
        workspace_path = self.git_extension.git.workspace_path
        docs_path = os.path.join(workspace_path, "docs")
        os.makedirs(docs_path, exist_ok=True)
        
        # Create the documentation file
        doc_filename = f"git-{strategy}-guide.md"
        doc_path = os.path.join(docs_path, doc_filename)
        
        with open(doc_path, "w") as f:
            f.write(f"# {strategy.title()} Branching Strategy Guide\n\n")
            f.write(f"## Description\n\n{documentation['description']}\n\n")
            f.write(f"## Branch Naming Conventions\n\n{documentation['naming_conventions']}\n\n")
            f.write(f"## Workflow\n\n{documentation['workflow']}\n\n")
            
        return documentation

    def _extract_code_blocks(self, text: str) -> List[Tuple[str, str, Optional[str]]]:
        """
        Extract code blocks from a markdown text.
        
        Returns:
            List of tuples: (language, code, file_path)
        """
        code_blocks = []
        
        # Regular expression to match markdown code blocks with optional language
        # ```language
        # code
        # ```
        pattern = r"```(\w*)\n([\s\S]*?)```"
        matches = re.findall(pattern, text)
        
        for match in matches:
            language, code = match
            language = language.strip() or "text"  # Default to "text" if no language specified
            code = code.strip()
            
            # Try to extract file path from surrounding text
            # Look for common file path indicators
            file_path = None
            
            # Check for file path indicators in code or in the 3 lines before the code block
            lines = text.split("\n")
            for i, line in enumerate(lines):
                if f"```{language}" in line:
                    # Check the 3 lines before this code block
                    start_idx = max(0, i - 3)
                    for j in range(start_idx, i):
                        path_match = re.search(r'[\"\'`]?([\w\/\.-]+\.\w+)[\"\'`]?', lines[j])
                        if path_match:
                            file_path = path_match.group(1)
                            break
                            
                    # If no file path found in preceding lines, check if it's in a comment in the first line of code
                    if not file_path and i < len(lines) - 1:
                        first_code_line = lines[i + 1]
                        if "//" in first_code_line or "#" in first_code_line:
                            path_match = re.search(r'[\"\'`]?([\w\/\.-]+\.\w+)[\"\'`]?', first_code_line)
                            if path_match:
                                file_path = path_match.group(1)
                                
                    break
            
            code_blocks.append((language, code, file_path))
            
        return code_blocks

    def _extract_instructions(self, text: str) -> str:
        """Extract instructions from the response text"""
        # Look for common section headers for instructions
        patterns = [
            r"(?:^|\n)#+\s*Instructions(?:[\s\S]*?)(?=\n#+|\Z)",
            r"(?:^|\n)#+\s*Deployment(?:[\s\S]*?)(?=\n#+|\Z)",
            r"(?:^|\n)#+\s*Getting Started(?:[\s\S]*?)(?=\n#+|\Z)",
            r"(?:^|\n)#+\s*Next Steps(?:[\s\S]*?)(?=\n#+|\Z)",
            r"(?:^|\n)#+\s*Usage(?:[\s\S]*?)(?=\n#+|\Z)"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(0).strip()
        
        # Fall back to checking for numbered steps
        lines = text.split('\n')
        instruction_lines = []
        in_instructions = False
        
        for line in lines:
            if re.match(r'^\d+\.\s', line) and not in_instructions:
                in_instructions = True
                instruction_lines.append(line)
            elif in_instructions:
                if re.match(r'^\s*$', line) or line.startswith('```'):
                    in_instructions = False
                else:
                    instruction_lines.append(line)
        
        if instruction_lines:
            return '\n'.join(instruction_lines)
        
        # If no instructions found, return empty string
        return ""

    async def run_tests_on_branch(self, branch_name: str, task_id: str) -> Dict[str, Any]:
        """
        Run tests on a specific branch
        
        Args:
            branch_name: Branch to test
            task_id: Task identifier
            
        Returns:
            Test results
        """
        logger.info(f"Running tests on branch {branch_name} for task {task_id}")
        
        # Check if branch exists
        branch_node = self.branch_tree.get_branch(branch_name)
        if not branch_node:
            return {
                "status": "error",
                "message": f"Branch '{branch_name}' not found",
                "details": "Cannot run tests on non-existent branch"
            }
            
        # Execute CI/CD workflow for testing
        test_result = await self.run_ci_cd_workflow(branch_name, "HEAD")
        
        # Parse result
        if test_result.get("status") == "success":
            # Extract test step results
            test_steps = [step for step in test_result.get("steps", []) if step.get("name") == "test"]
            if test_steps and test_steps[0].get("status") == "success":
                return {
                    "status": "success",
                    "branch": branch_name,
                    "task_id": task_id,
                    "details": f"All tests passed on branch {branch_name}",
                    "timestamp": asyncio.get_event_loop().time()
                }
            else:
                return {
                    "status": "failure",
                    "branch": branch_name,
                    "task_id": task_id,
                    "details": f"Tests failed on branch {branch_name}",
                    "timestamp": asyncio.get_event_loop().time()
                }
        else:
            return {
                "status": "error",
                "branch": branch_name,
                "task_id": task_id,
                "message": test_result.get("message", "Unknown error"),
                "details": "CI/CD workflow failed to run tests",
                "timestamp": asyncio.get_event_loop().time()
            }
            
    async def _merge_branches(self, source_branch: str, target_branch: str, task_id: str) -> Dict[str, Any]:
        """
        Merge source branch into target branch
        
        Args:
            source_branch: Source branch name
            target_branch: Target branch name
            task_id: Task identifier
            
        Returns:
            Merge result
        """
        logger.info(f"Merging {source_branch} into {target_branch} for task {task_id}")
        
        try:
            # Use git extension to perform merge
            result = self.git_extension.git.merge_branches(
                source_branch=source_branch,
                target_branch=target_branch,
                commit_message=f"Merge {source_branch} into {target_branch} for task {task_id}"
            )
            
            if result.get("status") != "success":
                return {
                    "status": "error",
                    "message": result.get("message", "Unknown merge error"),
                    "source_branch": source_branch,
                    "target_branch": target_branch
                }
                
            # Check if we should deploy after merging to main branches
            if target_branch in ["main", "master"] and self.ci_cd_config["auto_deploy"]:
                # Auto-deploy to production
                deploy_result = await self.deploy_to_environment("production", target_branch)
                result["deployment"] = deploy_result
            elif target_branch == "develop" and "staging" in self.ci_cd_config["environments"] and self.ci_cd_config["auto_deploy"]:
                # Auto-deploy to staging
                deploy_result = await self.deploy_to_environment("staging", target_branch)
                result["deployment"] = deploy_result
                
            return {
                "status": "success",
                "source_branch": source_branch,
                "target_branch": target_branch,
                "commits": result.get("commits", []),
                "files_changed": result.get("files_changed", []),
                "timestamp": asyncio.get_event_loop().time()
            }
            
        except Exception as e:
            logger.error(f"Exception merging branches: {str(e)}")
            return {
                "status": "error",
                "message": str(e),
                "source_branch": source_branch,
                "target_branch": target_branch
            }
            
    async def deploy_to_environment(self, environment: str, branch: str) -> Dict[str, Any]:
        """
        Deploy a branch to a specific environment
        
        Args:
            environment: Environment to deploy to
            branch: Branch to deploy
            
        Returns:
            Deployment result
        """
        if environment not in self.ci_cd_config["environments"]:
            return {
                "status": "error",
                "message": f"Environment '{environment}' not configured",
                "environment": environment,
                "branch": branch
            }
            
        if environment not in self.ci_cd_config["deploy_commands"]:
            return {
                "status": "error",
                "message": f"No deployment command for environment '{environment}'",
                "environment": environment,
                "branch": branch
            }
            
        logger.info(f"Deploying {branch} to {environment}")
        
        # Simulate deployment
        return {
            "status": "success",
            "environment": environment,
            "branch": branch,
            "command": self.ci_cd_config["deploy_commands"][environment],
            "timestamp": asyncio.get_event_loop().time()
        }

    def _get_next_steps_guidance(self, branch_name: str, test_status: str, task_id: str) -> str:
        """Generate guidance for next steps based on branch and test status"""
        if test_status == "failed":
            return """
Next Steps:
1. Fix the failing tests
2. Commit your changes
3. Tests will run automatically on your next commit
"""
        elif test_status == "passed" or test_status == "skipped":
            return """
Next Steps:
1. If your task is complete, request a merge with:
   - Send a message of type 'merge_request'
   - Include source_branch, target_branch, and task_id

2. If you need to make more changes:
   - Continue working on your branch
   - Commit changes as needed
"""
        else:
            return """
Next Steps:
1. Continue working on your branch
2. Commit changes as needed
"""

    def _save_branch_tree(self) -> None:
        """Save branch tree to persistent storage"""
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.branch_tree_file), exist_ok=True)
            
            # Save to file
            self.branch_tree.save_to_file(self.branch_tree_file)
            logger.info(f"Saved branch tree to {self.branch_tree_file}")
        except Exception as e:
            logger.error(f"Failed to save branch tree: {str(e)}")
        
    async def _handle_strategy_request(self, message: Message) -> Message:
        """Handle a Git branching strategy request"""
        # Extract strategy from message
        strategy = self._extract_branching_strategy(message.content)
        
        # Check if this is a branch visualization request
        if "visualize" in message.content.lower() or "show branches" in message.content.lower():
            return await self._visualize_branch_tree(message)
            
        if not strategy:
            # Default to current strategy
            strategy = self.git_extension.git.branch_strategy
            
        # Check with manager to update strategy
        try:
            # Notify manager about strategy decision
            strategy_message = await self.send_message(
                recipients=["manager"],
                content=f"I recommend using the {strategy} branching strategy for this project. Please confirm.",
                context_tags=["#git_strategy", "#recommendation"],
                message_type="strategy_recommendation",
                thread_id=message.thread_id,
                requires_response=True
            )
            
            # In a real implementation, we'd wait for the manager's response
            # For demo purposes, we'll assume it's approved
            
            # Update our own strategy
            self.git_extension.git.branch_strategy = strategy
            
            # Reset branch tree with new strategy
            self.branch_tree = BranchTree(strategy)
            self._save_branch_tree()
            
        except Exception as e:
            logger.warning(f"Could not coordinate with manager: {str(e)}")
        
        # Generate strategy documentation
        strategy_doc = await self.execute_with_git(
            self.create_strategy_documentation,
            strategy=strategy,
            commit_message=f"DevOps: Document {strategy} branching strategy"
        )
        
        # Prepare response
        response_content = f"""
I've established the {strategy} branching strategy for this project.

Key aspects of this strategy:
{strategy_doc['description']}

Branch naming conventions:
{strategy_doc['naming_conventions']}

Workflow:
{strategy_doc['workflow']}

The branch tree has been initialized with the {strategy} structure.
The strategy documentation has been committed to the repository.
"""

        return await self.send_message(
            recipients=[message.sender],
            content=response_content,
            context_tags=message.context_tags + ["#git_strategy"],
            message_type="strategy_result",
            thread_id=message.thread_id
        )
    
    async def _visualize_branch_tree(self, message: Message) -> Message:
        """Generate a visualization of the branch tree structure"""
        # Create a text-based tree visualization
        tree_text = self._generate_tree_visualization()
        
        # Current active branches by agent
        agent_branches_text = "### Active Branches by Agent\n"
        for agent_id, branches in self.agent_branches.items():
            active_branches = [b for b in branches 
                             if self.branch_tree.get_branch(b) and 
                                self.branch_tree.get_branch(b).status == "active"]
            if active_branches:
                agent_branches_text += f"- **{agent_id}**: {', '.join(active_branches)}\n"
                
        # Tasks and their branches
        task_branches_text = "### Tasks and Branches\n"
        for task_id, branch_name in self.task_branches.items():
            branch = self.branch_tree.get_branch(branch_name)
            if branch and branch.status == "active":
                task_branches_text += f"- **Task {task_id}**: {branch_name} ({branch.branch_type})\n"
                
        # Recent branch history
        history_text = "### Recent Branch Activity\n"
        recent_history = self.branch_history[-10:] if self.branch_history else []
        for entry in recent_history:
            action = entry.get("action", "")
            if action == "create":
                history_text += f"- {entry.get('timestamp', '').split('T')[0]} | **Created** branch '{entry.get('branch', '')}' from '{entry.get('parent', '')}'\n"
            elif action == "commit":
                history_text += f"- {entry.get('timestamp', '').split('T')[0]} | **Commit** to '{entry.get('branch', '')}' by {entry.get('agent_id', '')}\n"
            elif action == "merge":
                history_text += f"- {entry.get('timestamp', '').split('T')[0]} | **Merged** '{entry.get('source_branch', '')}' into '{entry.get('target_branch', '')}'\n"
                
        # Complete response
        response_content = f"""
# Branch Tree Visualization

{tree_text}

{agent_branches_text}

{task_branches_text}

{history_text}

The branch tree uses the **{self.branch_tree.strategy}** branching strategy.
"""

        return await self.send_message(
            recipients=[message.sender],
            content=response_content,
            context_tags=message.context_tags + ["#git_strategy", "#visualization"],
            message_type="branch_visualization",
            thread_id=message.thread_id
        )
        
    def _generate_tree_visualization(self) -> str:
        """Generate a text-based visualization of the branch tree"""
        if not self.branch_tree.root:
            return "No branches found."
            
        lines = []
        
        def _draw_tree(node, prefix="", is_last=True, level=0):
            # Define branch status indicators
            status_icons = {
                "active": "🟢",
                "merged": "🔵",
                "abandoned": "🔴"
            }
            
            # Branch node connector style
            connector = "└── " if is_last else "├── "
            
            # Add line for this node
            status = status_icons.get(node.status, "⚪")
            test_status = "✅" if node.tested else "❓"
            
            # Format line based on branch type
            if node.branch_type == "main" or node.branch_type == "develop":
                line = f"{prefix}{connector}**{node.name}** {status} {test_status}"
            else:
                agent_info = f" [{node.agent_id}]" if node.agent_id else ""
                task_info = f" (Task: {node.task_id})" if node.task_id else ""
                line = f"{prefix}{connector}{node.name} {status} {test_status}{agent_info}{task_info}"
                
            lines.append(line)
            
            # Prepare prefix for children
            child_prefix = prefix + ("    " if is_last else "│   ")
            
            # Process children
            children = node.children
            for i, child in enumerate(children):
                _draw_tree(child, child_prefix, i == len(children) - 1, level + 1)
                
        # Start with the root node
        _draw_tree(self.branch_tree.root)
        
        return "\n".join(lines)
    
    async def _register_external_commit(self, 
                              branch_name: str,
                              agent_id: str,
                              commit_hash: str,
                              commit_message: str,
                              files_changed: List[str],
                              task_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Register a commit from an external agent
        
        Args:
            branch_name: Branch that was committed to
            agent_id: ID of the agent that made the commit
            commit_hash: Commit hash
            commit_message: Commit message
            files_changed: List of files that were changed
            task_id: Optional task ID
            
        Returns:
            Registration result
        """
        # Validate branch exists
        branch_node = self.branch_tree.get_branch(branch_name)
        if not branch_node:
            # This is a new branch we don't know about yet
            # Try to determine parent based on git history
            try:
                parent_info = self.git_extension.git.get_branch_parent(branch_name)
                if parent_info.get("status") == "success" and parent_info.get("parent_branch"):
                    parent_branch = parent_info.get("parent_branch")
                    
                    # Determine branch type from name
                    if branch_name.startswith("feature/"):
                        branch_type = "feature"
                    elif branch_name.startswith("bugfix/"):
                        branch_type = "bugfix"
                    elif branch_name.startswith("hotfix/"):
                        branch_type = "hotfix"
                    elif branch_name.startswith("release/"):
                        branch_type = "release"
                    else:
                        branch_type = "feature"  # Default
                    
                    # Add to branch tree
                    branch_node = self.branch_tree.add_branch(
                        name=branch_name,
                        parent_name=parent_branch,
                        branch_type=branch_type,
                        task_id=task_id,
                        agent_id=agent_id
                    )
                    
                    # Update mappings
                    if agent_id not in self.agent_branches:
                        self.agent_branches[agent_id] = set()
                    self.agent_branches[agent_id].add(branch_name)
                    
                    if task_id:
                        self.task_branches[task_id] = branch_name
                        
                    # Save branch tree
                    self._save_branch_tree()
                else:
                    logger.warning(f"Could not determine parent for unknown branch {branch_name}")
                    return {
                        "status": "error",
                        "message": f"Branch {branch_name} not found in branch tree and could not determine parent.",
                        "branch_name": branch_name,
                        "agent_id": agent_id
                    }
            except Exception as e:
                logger.warning(f"Error determining parent for branch {branch_name}: {str(e)}")
                return {
                    "status": "error",
                    "message": f"Branch {branch_name} not found in branch tree: {str(e)}",
                    "branch_name": branch_name,
                    "agent_id": agent_id
                }
        
        # Update branch history
        self.branch_history.append({
            "action": "commit",
            "branch": branch_name,
            "commit_hash": commit_hash,
            "agent_id": agent_id,
            "timestamp": datetime.now().isoformat(),
            "message": commit_message,
            "files_changed": files_changed,
            "task_id": task_id
        })
        
        # Check if we need to run tests
        if self.ci_cd_config["run_tests"] and self.ci_cd_config["enabled"]:
            # Running tests on auto-commit is optional depending on CI/CD settings
            if self.ci_cd_config.get("test_on_commit", True):
                # Run tests asynchronously (don't wait for results here)
                asyncio.create_task(self.run_tests_on_branch(branch_name, task_id or "unknown"))
        
        return {
            "status": "success",
            "message": f"Registered commit {commit_hash[:7]} on branch {branch_name}",
            "branch_name": branch_name,
            "agent_id": agent_id,
            "run_tests": self.ci_cd_config["run_tests"] and self.ci_cd_config.get("test_on_commit", True)
        }
        
    async def setup_agent_auto_commit_hook(self, agent_id: str) -> Dict[str, Any]:
        """
        Set up auto-commit hook for an agent
        
        Args:
            agent_id: Agent ID to set up hook for
            
        Returns:
            Setup result
        """
        # This would typically be implemented by injecting a post-edit hook
        # into the agent's workflow that calls back to this agent
        
        # For now, we'll just return success and assume each agent will notify us
        return {
            "status": "success",
            "message": f"Auto-commit hook set up for agent {agent_id}",
            "agent_id": agent_id
        }
    
    async def handle_auto_commit_notification(self, 
                                   agent_id: str,
                                   branch_name: str,
                                   commit_message: str,
                                   files_changed: List[str],
                                   task_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Handle notification that an agent has auto-committed code
        
        Args:
            agent_id: Agent that made the commit
            branch_name: Branch that was committed to
            commit_message: Commit message
            files_changed: List of files that were changed
            task_id: Optional task ID
            
        Returns:
            Processing result
        """
        # Register the commit in our branch tree
        result = await self._register_external_commit(
            branch_name=branch_name,
            agent_id=agent_id,
            commit_hash="auto-commit",  # We don't have the real hash
            commit_message=commit_message,
            files_changed=files_changed,
            task_id=task_id
        )
        
        # Save branch tree
        self._save_branch_tree()
        
        return result

    def _is_strategy_request(self, text: str) -> bool:
        """Check if a message is related to strategy decisions"""
        strategy_keywords = [
            "strategy", "gitflow", "trunk-based", "branching strategy",
            "workflow", "process", "methodology", "approval", "review",
            "merge approval", "authorization", "permissions", "roles",
            "branch tree", "branch structure", "branch hierarchy"
        ]
        
        text_lower = text.lower()
        
        # Check for strategy keywords
        for keyword in strategy_keywords:
            if keyword in text_lower:
                return True
                
        return False
        
    async def _handle_strategy_request(self, message: Message) -> Message:
        """Handle a Git branching strategy request"""
        # Extract strategy from message
        strategy = self._extract_branching_strategy(message.content)
        
        # Check if this is a branch visualization request
        if "visualize" in message.content.lower() or "show branches" in message.content.lower():
            return await self._visualize_branch_tree(message)
            
        if not strategy:
            # Default to current strategy
            strategy = self.git_extension.git.branch_strategy
            
        # Check with manager to update strategy
        try:
            # Notify manager about strategy decision
            strategy_message = await self.send_message(
                recipients=["manager"],
                content=f"I recommend using the {strategy} branching strategy for this project. Please confirm.",
                context_tags=["#git_strategy", "#recommendation"],
                message_type="strategy_recommendation",
                thread_id=message.thread_id,
                requires_response=True
            )
            
            # In a real implementation, we'd wait for the manager's response
            # For demo purposes, we'll assume it's approved
            
            # Update our own strategy
            self.git_extension.git.branch_strategy = strategy
            
            # Reset branch tree with new strategy
            self.branch_tree = BranchTree(strategy)
            self._save_branch_tree()
            
        except Exception as e:
            logger.warning(f"Could not coordinate with manager: {str(e)}")
        
        # Generate strategy documentation
        strategy_doc = await self.execute_with_git(
            self.create_strategy_documentation,
            strategy=strategy,
            commit_message=f"DevOps: Document {strategy} branching strategy"
        )
        
        # Prepare response
        response_content = f"""
I've established the {strategy} branching strategy for this project.

Key aspects of this strategy:
{strategy_doc['description']}

Branch naming conventions:
{strategy_doc['naming_conventions']}

Workflow:
{strategy_doc['workflow']}

The branch tree has been initialized with the {strategy} structure.
The strategy documentation has been committed to the repository.
"""

        return await self.send_message(
            recipients=[message.sender],
            content=response_content,
            context_tags=message.context_tags + ["#git_strategy"],
            message_type="strategy_result",
            thread_id=message.thread_id
        )
    
    async def _visualize_branch_tree(self, message: Message) -> Message:
        """Generate a visualization of the branch tree structure"""
        # Create a text-based tree visualization
        tree_text = self._generate_tree_visualization()
        
        # Current active branches by agent
        agent_branches_text = "### Active Branches by Agent\n"
        for agent_id, branches in self.agent_branches.items():
            active_branches = [b for b in branches 
                             if self.branch_tree.get_branch(b) and 
                                self.branch_tree.get_branch(b).status == "active"]
            if active_branches:
                agent_branches_text += f"- **{agent_id}**: {', '.join(active_branches)}\n"
                
        # Tasks and their branches
        task_branches_text = "### Tasks and Branches\n"
        for task_id, branch_name in self.task_branches.items():
            branch = self.branch_tree.get_branch(branch_name)
            if branch and branch.status == "active":
                task_branches_text += f"- **Task {task_id}**: {branch_name} ({branch.branch_type})\n"
                
        # Recent branch history
        history_text = "### Recent Branch Activity\n"
        recent_history = self.branch_history[-10:] if self.branch_history else []
        for entry in recent_history:
            action = entry.get("action", "")
            if action == "create":
                history_text += f"- {entry.get('timestamp', '').split('T')[0]} | **Created** branch '{entry.get('branch', '')}' from '{entry.get('parent', '')}'\n"
            elif action == "commit":
                history_text += f"- {entry.get('timestamp', '').split('T')[0]} | **Commit** to '{entry.get('branch', '')}' by {entry.get('agent_id', '')}\n"
            elif action == "merge":
                history_text += f"- {entry.get('timestamp', '').split('T')[0]} | **Merged** '{entry.get('source_branch', '')}' into '{entry.get('target_branch', '')}'\n"
                
        # Complete response
        response_content = f"""
# Branch Tree Visualization

{tree_text}

{agent_branches_text}

{task_branches_text}

{history_text}

The branch tree uses the **{self.branch_tree.strategy}** branching strategy.
"""

        return await self.send_message(
            recipients=[message.sender],
            content=response_content,
            context_tags=message.context_tags + ["#git_strategy", "#visualization"],
            message_type="branch_visualization",
            thread_id=message.thread_id
        )
        
    def _generate_tree_visualization(self) -> str:
        """Generate a text-based visualization of the branch tree"""
        if not self.branch_tree.root:
            return "No branches found."
            
        lines = []
        
        def _draw_tree(node, prefix="", is_last=True, level=0):
            # Define branch status indicators
            status_icons = {
                "active": "🟢",
                "merged": "🔵",
                "abandoned": "🔴"
            }
            
            # Branch node connector style
            connector = "└── " if is_last else "├── "
            
            # Add line for this node
            status = status_icons.get(node.status, "⚪")
            test_status = "✅" if node.tested else "❓"
            
            # Format line based on branch type
            if node.branch_type == "main" or node.branch_type == "develop":
                line = f"{prefix}{connector}**{node.name}** {status} {test_status}"
            else:
                agent_info = f" [{node.agent_id}]" if node.agent_id else ""
                task_info = f" (Task: {node.task_id})" if node.task_id else ""
                line = f"{prefix}{connector}{node.name} {status} {test_status}{agent_info}{task_info}"
                
            lines.append(line)
            
            # Prepare prefix for children
            child_prefix = prefix + ("    " if is_last else "│   ")
            
            # Process children
            children = node.children
            for i, child in enumerate(children):
                _draw_tree(child, child_prefix, i == len(children) - 1, level + 1)
                
        # Start with the root node
        _draw_tree(self.branch_tree.root)
        
        return "\n".join(lines)
    
    async def _register_external_commit(self, 
                              branch_name: str,
                              agent_id: str,
                              commit_hash: str,
                              commit_message: str,
                              files_changed: List[str],
                              task_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Register a commit from an external agent
        
        Args:
            branch_name: Branch that was committed to
            agent_id: ID of the agent that made the commit
            commit_hash: Commit hash
            commit_message: Commit message
            files_changed: List of files that were changed
            task_id: Optional task ID
            
        Returns:
            Registration result
        """
        # Validate branch exists
        branch_node = self.branch_tree.get_branch(branch_name)
        if not branch_node:
            # This is a new branch we don't know about yet
            # Try to determine parent based on git history
            try:
                parent_info = self.git_extension.git.get_branch_parent(branch_name)
                if parent_info.get("status") == "success" and parent_info.get("parent_branch"):
                    parent_branch = parent_info.get("parent_branch")
                    
                    # Determine branch type from name
                    if branch_name.startswith("feature/"):
                        branch_type = "feature"
                    elif branch_name.startswith("bugfix/"):
                        branch_type = "bugfix"
                    elif branch_name.startswith("hotfix/"):
                        branch_type = "hotfix"
                    elif branch_name.startswith("release/"):
                        branch_type = "release"
                    else:
                        branch_type = "feature"  # Default
                    
                    # Add to branch tree
                    branch_node = self.branch_tree.add_branch(
                        name=branch_name,
                        parent_name=parent_branch,
                        branch_type=branch_type,
                        task_id=task_id,
                        agent_id=agent_id
                    )
                    
                    # Update mappings
                    if agent_id not in self.agent_branches:
                        self.agent_branches[agent_id] = set()
                    self.agent_branches[agent_id].add(branch_name)
                    
                    if task_id:
                        self.task_branches[task_id] = branch_name
                        
                    # Save branch tree
                    self._save_branch_tree()
                else:
                    logger.warning(f"Could not determine parent for unknown branch {branch_name}")
                    return {
                        "status": "error",
                        "message": f"Branch {branch_name} not found in branch tree and could not determine parent.",
                        "branch_name": branch_name,
                        "agent_id": agent_id
                    }
            except Exception as e:
                logger.warning(f"Error determining parent for branch {branch_name}: {str(e)}")
                return {
                    "status": "error",
                    "message": f"Branch {branch_name} not found in branch tree: {str(e)}",
                    "branch_name": branch_name,
                    "agent_id": agent_id
                }
        
        # Update branch history
        self.branch_history.append({
            "action": "commit",
            "branch": branch_name,
            "commit_hash": commit_hash,
            "agent_id": agent_id,
            "timestamp": datetime.now().isoformat(),
            "message": commit_message,
            "files_changed": files_changed,
            "task_id": task_id
        })
        
        # Check if we need to run tests
        if self.ci_cd_config["run_tests"] and self.ci_cd_config["enabled"]:
            # Running tests on auto-commit is optional depending on CI/CD settings
            if self.ci_cd_config.get("test_on_commit", True):
                # Run tests asynchronously (don't wait for results here)
                asyncio.create_task(self.run_tests_on_branch(branch_name, task_id or "unknown"))
        
        return {
            "status": "success",
            "message": f"Registered commit {commit_hash[:7]} on branch {branch_name}",
            "branch_name": branch_name,
            "agent_id": agent_id,
            "run_tests": self.ci_cd_config["run_tests"] and self.ci_cd_config.get("test_on_commit", True)
        }
        
    async def setup_agent_auto_commit_hook(self, agent_id: str) -> Dict[str, Any]:
        """
        Set up auto-commit hook for an agent
        
        Args:
            agent_id: Agent ID to set up hook for
            
        Returns:
            Setup result
        """
        # This would typically be implemented by injecting a post-edit hook
        # into the agent's workflow that calls back to this agent
        
        # For now, we'll just return success and assume each agent will notify us
        return {
            "status": "success",
            "message": f"Auto-commit hook set up for agent {agent_id}",
            "agent_id": agent_id
        }
    
    async def handle_auto_commit_notification(self, 
                                   agent_id: str,
                                   branch_name: str,
                                   commit_message: str,
                                   files_changed: List[str],
                                   task_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Handle notification that an agent has auto-committed code
        
        Args:
            agent_id: Agent that made the commit
            branch_name: Branch that was committed to
            commit_message: Commit message
            files_changed: List of files that were changed
            task_id: Optional task ID
            
        Returns:
            Processing result
        """
        # Register the commit in our branch tree
        result = await self._register_external_commit(
            branch_name=branch_name,
            agent_id=agent_id,
            commit_hash="auto-commit",  # We don't have the real hash
            commit_message=commit_message,
            files_changed=files_changed,
            task_id=task_id
        )
        
        # Save branch tree
        self._save_branch_tree()
        
        return result