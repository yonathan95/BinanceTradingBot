import json
from typing import Dict, List, Any, Optional
import uuid
import asyncio
import re

from hive_mind.agent_sdk.base_agent import BaseAgent, Message
from hive_mind.agent_sdk.feedback_loop import ValidationResult
from .common.agent_git_extension import AgentGitExtension

class ManagerAgent(BaseAgent):
    """
    Manager Agent that orchestrates the team's activities, routes messages,
    handles the feedback loop process, and approves Git operations.
    """
    
    def __init__(self, 
                agent_id: str = "manager", 
                model: str = "gpt-4o", 
                temperature: float = 0.7, 
                token_limit: int = 4096,
                workspace_path: Optional[str] = None,
                repository_url: Optional[str] = None):
        """
        Initialize the Manager Agent
        
        Args:
            agent_id: Unique identifier for the agent
            model: LLM model to use
            temperature: LLM temperature setting
            token_limit: Maximum token limit for LLM calls
            workspace_path: Path to the workspace directory
            repository_url: URL of the git repository
        """
        super().__init__(agent_id, model, temperature, token_limit)
        self.team: Dict[str, BaseAgent] = {}
        self.active_tasks: Dict[str, Dict[str, Any]] = {}
        
        # Initialize Git extension
        self.git_extension = AgentGitExtension(
            agent=self,
            workspace_path=workspace_path,
            repository_url=repository_url,
            branch_strategy="gitflow"  # Default strategy
        )
        
        # Track pending PR approvals
        self.pending_approvals: Dict[str, Dict[str, Any]] = {}
        
        # Set authorized roles for Git operations
        self.authorized_roles = ["manager", "devops"]
        
        # Project configuration
        self.project_config: Dict[str, Any] = {
            "git_strategy": "gitflow",
            "ci_cd_config": {
                "run_tests": True,
                "auto_deploy": False,
                "environments": ["dev", "staging", "production"]
            },
            "auto_approvals": False,
            "required_approvals": 1
        }
        
    def add_team_member(self, agent: BaseAgent):
        """
        Add an agent to the team
        
        Args:
            agent: The agent to add
        """
        self.team[agent.agent_id] = agent
        
    async def process_message(self, message: Message) -> Message:
        """
        Process an incoming message and route it appropriately
        
        Args:
            message: The incoming message
            
        Returns:
            A response message
        """
        # Check if this is a Git-related message that needs manager approval
        if self._is_approval_request(message):
            return await self._handle_approval_request(message)
            
        # Check if this is a Git configuration message
        if self._is_git_config_request(message):
            return await self._handle_git_config(message)
        
        # Try to handle with the Git extension first
        git_response = await self.git_extension.handle_git_message(message)
        if git_response:
            return git_response
            
        # Standard message processing
        if message.sender == "user":
            return await self._process_user_message(message)
        else:
            return await self._process_agent_message(message)
    
    async def _process_user_message(self, message: Message) -> Message:
        """
        Process a message from the user
        
        Args:
            message: The user message
            
        Returns:
            A response message
        """
        # Analyze user request and create tasks
        prompt = await self.generate_prompt({
            "user_message": message.content,
            "current_tasks": self.active_tasks,
            "team_members": list(self.team.keys()),
            "project_config": self.project_config
        })
        
        # Call to LLM model
        response = await self.call_llm(prompt)
        content = response["content"]
        
        # Create tasks and assign to team members
        tasks = await self._parse_tasks(content)
        
        # Store tasks
        for task_id, task in tasks.items():
            self.active_tasks[task_id] = task
            
            # Send task to assigned agent
            if task["assigned_to"] in self.team:
                task_message = await self.send_message(
                    recipients=[task["assigned_to"]],
                    content=task["description"],
                    context_tags=["#task", f"#{task['type']}"],
                    message_type="task_assignment",
                    thread_id=task_id,
                    requires_response=True
                )
                
                # Send the message to the agent
                await self.team[task["assigned_to"]].receive_message(task_message)
        
        # Generate status message for user
        task_list = "\n".join(f"- {task['type']}: {task['description']} (assigned to: {task['assigned_to']})" 
                             for task in tasks.values())
        
        return await self.send_message(
            recipients=["user"],
            content=f"I've analyzed your request and created the following tasks:\n\n{task_list}",
            context_tags=["#status_update"],
            message_type="status"
        )
    
    async def _process_agent_message(self, message: Message) -> Optional[Message]:
        """
        Process a message from another agent
        
        Args:
            message: The agent message
            
        Returns:
            A response message if needed
        """
        if message.message_type == "status_update":
            # Update task status
            if message.thread_id in self.active_tasks:
                self.active_tasks[message.thread_id]["status"] = message.content
                
            # Forward status to user
            return await self.send_message(
                recipients=["user"],
                content=f"Status update from {message.sender}: {message.content}",
                context_tags=["#status_update"],
                message_type="status",
                thread_id=message.thread_id
            )
            
        elif message.message_type == "question":
            # Route question to appropriate agent based on context tags
            target_agent = await self._determine_target_agent(message)
            
            if target_agent:
                # Forward the question
                question_message = await self.send_message(
                    recipients=[target_agent],
                    content=message.content,
                    context_tags=message.context_tags,
                    message_type="question",
                    thread_id=message.thread_id,
                    requires_response=True
                )
                
                # Send the message to the target agent
                response = await self.team[target_agent].receive_message(question_message)
                
                # Forward the response back to the original sender
                return await self.send_message(
                    recipients=[message.sender],
                    content=response.content,
                    context_tags=response.context_tags,
                    message_type="answer",
                    thread_id=message.thread_id
                )
            else:
                # Answer the question if no specific target
                prompt = await self.generate_prompt({
                    "question": message.content,
                    "context_tags": message.context_tags,
                    "sender": message.sender
                })
                
                response = await self.call_llm(prompt)
                
                return await self.send_message(
                    recipients=[message.sender],
                    content=response["content"],
                    context_tags=message.context_tags,
                    message_type="answer",
                    thread_id=message.thread_id
                )
                
        elif message.message_type == "task_result":
            # Handle task completion
            if message.thread_id in self.active_tasks:
                task = self.active_tasks[message.thread_id]
                
                # Validate the result if this is part of a feedback loop
                if task.get("requires_validation", False):
                    validation_result = await self._validate_task_result(
                        task_id=message.thread_id,
                        result=message.content,
                        success_criteria=task.get("success_criteria", {})
                    )
                    
                    if validation_result.success:
                        # Task completed successfully
                        task["status"] = "completed"
                        
                        # Notify user of completion
                        return await self.send_message(
                            recipients=["user"],
                            content=f"Task '{task['description']}' has been completed successfully.",
                            context_tags=["#status_update", "#completion"],
                            message_type="status",
                            thread_id=message.thread_id
                        )
                    else:
                        # Task needs revision
                        task["status"] = "revision_needed"
                        task["feedback"] = validation_result.feedback
                        task["iterations"] = task.get("iterations", 0) + 1
                        
                        if task["iterations"] >= task.get("max_iterations", 5):
                            # Max iterations reached
                            task["status"] = "failed"
                            
                            # Notify user of failure
                            return await self.send_message(
                                recipients=["user"],
                                content=f"Task '{task['description']}' has failed after maximum iterations. Feedback: {validation_result.feedback}",
                                context_tags=["#status_update", "#failure"],
                                message_type="status",
                                thread_id=message.thread_id
                            )
                        else:
                            # Send feedback to agent
                            feedback_message = await self.send_message(
                                recipients=[task["assigned_to"]],
                                content=f"Feedback on your task: {validation_result.feedback}",
                                context_tags=["#feedback"],
                                message_type="task_feedback",
                                thread_id=message.thread_id,
                                requires_response=True
                            )
                            
                            # Send the feedback to the agent
                            await self.team[task["assigned_to"]].receive_message(feedback_message)
                            
                            # Notify user of feedback
                            return await self.send_message(
                                recipients=["user"],
                                content=f"Task '{task['description']}' needs revision. Feedback has been sent to {task['assigned_to']}.",
                                context_tags=["#status_update", "#feedback"],
                                message_type="status",
                                thread_id=message.thread_id
                            )
                else:
                    # No validation required, mark as completed
                    task["status"] = "completed"
                    
                    # Notify user of completion
                    return await self.send_message(
                        recipients=["user"],
                        content=f"Task '{task['description']}' has been completed by {message.sender}.",
                        context_tags=["#status_update", "#completion"],
                        message_type="status",
                        thread_id=message.thread_id
                    )
                    
        # Return None if no response is needed
        return None
    
    async def generate_prompt(self, context: Dict[str, Any]) -> str:
        """
        Generate a prompt for the LLM based on the provided context
        
        Args:
            context: Context for prompt generation
            
        Returns:
            Generated prompt
        """
        if "user_message" in context:
            # Prompt for analyzing user message
            team_members = ", ".join(context.get("team_members", []))
            current_tasks = "\n".join([
                f"- {task_id}: {task['status']}" for task_id, task in context.get("current_tasks", {}).items()
            ])
            
            return f"""
            You are the Manager of an AI development team. Your role is to coordinate the team's activities and ensure efficient communication.
            
            Team Members: {team_members}
            Current Tasks: {current_tasks}
            Team Objective: Implement the requested features efficiently
            
            User Message: {context['user_message']}
            
            Your primary responsibilities are:
            1. Coordinate work between team members
            2. Route messages to appropriate agents
            3. Monitor task progress
            4. Provide status updates to the user
            5. Summarize conversations to minimize token usage
            6. Enforce project guard rails
            7. Approve or reject pull requests and merges
            8. Make final decisions on Git branching strategies
            
            Based on the user's message, determine what tasks need to be created and which team members should handle them.
            For each task, specify:
            1. Task ID
            2. Task description
            3. Assigned agent
            4. Task type (planning, coding, testing, etc.)
            5. Whether the task requires validation
            6. Success criteria (if validation is required)
            7. Maximum iterations for feedback loop (if applicable)
            
            Respond in JSON format with the task assignments.
            """
        elif "question" in context:
            # Prompt for answering a question
            return f"""
            You are the Manager of an AI development team. An agent has asked you a question.
            
            Question from {context.get('sender', 'an agent')}: {context['question']}
            Context Tags: {', '.join(context.get('context_tags', []))}
            
            Provide a helpful, concise response based on your knowledge and coordination role.
            """
        elif "approval_request" in context:
            # Prompt for handling approval requests
            return f"""
            You are the Manager of an AI development team. You need to review a Git operation that requires your approval.
            
            Operation: {context['operation']}
            Requested by: {context['requester']}
            Details: {context['details']}
            
            Project Git Configuration:
            - Branching Strategy: {self.project_config['git_strategy']}
            - CI/CD Configuration: {json.dumps(self.project_config['ci_cd_config'], indent=2)}
            
            Please review this request and determine if it should be approved or rejected.
            Consider:
            1. Does this follow the project's established branching strategy?
            2. Is the agent requesting the change authorized to perform this operation?
            3. Does this change follow good software engineering practices?
            4. What are the potential impacts of this change?
            
            Respond with:
            1. Your decision: "APPROVE" or "REJECT"
            2. A brief explanation for your decision
            """
        else:
            # Default prompt
            return f"""
            You are the Manager of an AI development team. Your role is to coordinate the team's activities and ensure efficient communication.
            
            Provide a clear and concise response based on the context provided.
            """
    
    async def _parse_tasks(self, llm_response: str) -> Dict[str, Dict[str, Any]]:
        """
        Parse tasks from LLM response
        
        Args:
            llm_response: Response from the LLM
            
        Returns:
            Dictionary of tasks
        """
        # Extract JSON from the response
        try:
            # Find JSON in the response
            json_start = llm_response.find('{')
            json_end = llm_response.rfind('}') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_str = llm_response[json_start:json_end]
                tasks_data = json.loads(json_str)
                
                # Process the tasks
                tasks = {}
                for task_id, task_info in tasks_data.items():
                    # Ensure task has required fields
                    if "description" in task_info and "assigned_to" in task_info:
                        # Generate a UUID if task_id is not in the right format
                        if not task_id.startswith("task-"):
                            task_id = f"task-{str(uuid.uuid4())}"
                            
                        tasks[task_id] = {
                            "description": task_info["description"],
                            "assigned_to": task_info["assigned_to"],
                            "type": task_info.get("type", "general"),
                            "status": "assigned",
                            "requires_validation": task_info.get("requires_validation", False),
                            "success_criteria": task_info.get("success_criteria", {}),
                            "max_iterations": task_info.get("max_iterations", 5),
                            "iterations": 0
                        }
                
                return tasks
        except Exception as e:
            print(f"Error parsing tasks: {str(e)}")
            
        # Fallback: create a generic task
        task_id = f"task-{str(uuid.uuid4())}"
        return {
            task_id: {
                "description": "Analyze the user request and provide a plan",
                "assigned_to": next(iter(self.team.keys()), "planner"),
                "type": "planning",
                "status": "assigned",
                "requires_validation": False,
                "iterations": 0
            }
        }
    
    async def _determine_target_agent(self, message: Message) -> Optional[str]:
        """
        Determine the best agent to handle a question based on context tags
        
        Args:
            message: The question message
            
        Returns:
            ID of the target agent or None
        """
        # Implementation would use context tags and message content to route
        # This is a simplified version
        
        # Check for specific role tags
        role_tags = {
            "#planning": "planner",
            "#architecture": "architect",
            "#coding": "coder",
            "#testing": "tester",
            "#ux": "designer",
            "#database": "database_engineer",
            "#security": "security",
            "#git": "devops",
            "#devops": "devops",
            "#infrastructure": "devops"
        }
        
        for tag in message.context_tags:
            if tag in role_tags and role_tags[tag] in self.team:
                return role_tags[tag]
                
        # Fallback: pick the most appropriate based on message content
        # This would be implemented with more sophisticated routing in a real system
        return None
    
    async def _validate_task_result(self, task_id: str, result: str, 
                                  success_criteria: Dict[str, Any]) -> ValidationResult:
        """
        Validate a task result against success criteria
        
        Args:
            task_id: ID of the task
            result: Result to validate
            success_criteria: Criteria for success
            
        Returns:
            ValidationResult
        """
        # This would be implemented with more sophisticated validation in a real system
        # For now, we'll use a simple LLM-based validation
        
        prompt = f"""
        You are validating the result of a task against defined success criteria.
        
        Task Result:
        {result}
        
        Success Criteria:
        {json.dumps(success_criteria, indent=2)}
        
        Evaluate if the result meets all the success criteria. Be strict but fair in your assessment.
        If the result does not meet the criteria, provide specific feedback on what needs to be improved.
        
        Respond with:
        1. "SUCCESS" or "FAILURE"
        2. Detailed feedback explaining your assessment
        """
        
        response = await self.call_llm(prompt)
        content = response["content"]
        
        # Parse the validation result
        if "SUCCESS" in content.upper():
            return ValidationResult(success=True, feedback="Task completed successfully")
        else:
            # Extract feedback
            feedback_lines = []
            for line in content.split('\n'):
                if "FAILURE" not in line and line.strip():
                    feedback_lines.append(line.strip())
                    
            feedback = " ".join(feedback_lines)
            
            return ValidationResult(success=False, feedback=feedback)
    
    def _is_approval_request(self, message: Message) -> bool:
        """Check if a message is a Git approval request"""
        if message.message_type == "approval_request":
            return True
            
        # Check for approval keywords in content
        approval_keywords = ["approve", "approval", "authorize", "permission", "pull request", "merge", "PR"]
        
        for keyword in approval_keywords:
            if keyword.lower() in message.content.lower():
                for tag in message.context_tags:
                    if tag in ["#git_operation", "#merge", "#pull_request"]:
                        return True
                        
        return False
    
    async def _handle_approval_request(self, message: Message) -> Message:
        """
        Handle a Git approval request
        
        Args:
            message: The approval request message
            
        Returns:
            Response message
        """
        # Extract operation details from the message
        operation = self._extract_operation_details(message.content)
        
        # Check if this is a user directly approving an existing request
        if message.sender == "user" and "approve" in message.content.lower():
            pr_id = self._extract_pr_id(message.content)
            if pr_id and pr_id in self.pending_approvals:
                # User is approving a pending request
                approval = self.pending_approvals[pr_id]
                
                # Mark as approved
                approval["status"] = "approved"
                approval["approved_by"] = "user"
                
                # Execute the approved operation
                # In a real system, this would trigger the actual merge operation
                response_content = f"✅ PR #{pr_id} approved by user. The {approval['operation']} will now be executed."
                
                # Notify the original requester
                await self.send_message(
                    recipients=[approval["requester"]],
                    content=f"Your {approval['operation']} request (PR #{pr_id}) has been approved by the user. It will now be executed.",
                    context_tags=["#git_operation", "#approval"],
                    message_type="approval_notification",
                    thread_id=message.thread_id
                )
                
                # Remove from pending approvals
                del self.pending_approvals[pr_id]
                
                return await self.send_message(
                    recipients=[message.sender],
                    content=response_content,
                    context_tags=["#git_operation", "#approval"],
                    message_type="approval_result",
                    thread_id=message.thread_id
                )
                
        # This is a new approval request from an agent
        # Generate a unique ID for this approval request
        pr_id = f"PR-{len(self.pending_approvals) + 1}"
        
        # Store the approval request
        self.pending_approvals[pr_id] = {
            "id": pr_id,
            "requester": message.sender,
            "operation": operation.get("type", "unknown"),
            "details": operation.get("details", "No details provided"),
            "status": "pending",
            "thread_id": message.thread_id,
            "timestamp": asyncio.get_event_loop().time()
        }
        
        # Automatically approve if auto-approvals are enabled and requester is authorized
        if self.project_config["auto_approvals"] and message.sender in self.authorized_roles:
            # Mark as approved
            self.pending_approvals[pr_id]["status"] = "approved"
            self.pending_approvals[pr_id]["approved_by"] = "manager"
            
            response_content = f"✅ {operation.get('type', 'Operation')} automatically approved (PR #{pr_id}). The operation will now be executed."
            
            # Remove from pending approvals
            del self.pending_approvals[pr_id]
        else:
            # Ask user for approval
            response_content = f"🔍 {operation.get('type', 'Operation')} requires approval (PR #{pr_id}).\n\nDetails: {operation.get('details', 'No details provided')}\n\nRequested by: {message.sender}\n\nTo approve, reply with: 'Approve PR #{pr_id}'"
            
            # Also send to user
            await self.send_message(
                recipients=["user"],
                content=response_content,
                context_tags=["#git_operation", "#approval_request"],
                message_type="approval_request",
                thread_id=message.thread_id
            )
        
        return await self.send_message(
            recipients=[message.sender],
            content=response_content,
            context_tags=["#git_operation", "#approval"],
            message_type="approval_response",
            thread_id=message.thread_id
        )
    
    def _extract_operation_details(self, text: str) -> Dict[str, Any]:
        """Extract Git operation details from text"""
        operation = {"type": "unknown", "details": "No details available"}
        
        # Try to identify the operation type
        if "merge" in text.lower():
            operation["type"] = "merge"
            
            # Extract source and target branches
            source_match = re.search(r'(from|source)\s+branch\s+[\'"]?([a-zA-Z0-9_/-]+)[\'"]?', text, re.IGNORECASE)
            target_match = re.search(r'(into|target)\s+branch\s+[\'"]?([a-zA-Z0-9_/-]+)[\'"]?', text, re.IGNORECASE)
            
            details = []
            if source_match:
                details.append(f"Source: {source_match.group(2)}")
            if target_match:
                details.append(f"Target: {target_match.group(2)}")
                
            operation["details"] = ", ".join(details) if details else "Merge branches"
            
        elif "pull request" in text.lower() or "pr" in text.lower():
            operation["type"] = "pull request"
            
            # Extract PR title and branches
            title_match = re.search(r'title\s+[\'"]([^\'"]+)[\'"]', text, re.IGNORECASE)
            source_match = re.search(r'(from|source)\s+branch\s+[\'"]?([a-zA-Z0-9_/-]+)[\'"]?', text, re.IGNORECASE)
            target_match = re.search(r'(into|target)\s+branch\s+[\'"]?([a-zA-Z0-9_/-]+)[\'"]?', text, re.IGNORECASE)
            
            details = []
            if title_match:
                details.append(f"Title: {title_match.group(1)}")
            if source_match:
                details.append(f"Source: {source_match.group(2)}")
            if target_match:
                details.append(f"Target: {target_match.group(2)}")
                
            operation["details"] = ", ".join(details) if details else "Create pull request"
            
        elif "push" in text.lower():
            operation["type"] = "push"
            
            # Extract branch
            branch_match = re.search(r'branch\s+[\'"]?([a-zA-Z0-9_/-]+)[\'"]?', text, re.IGNORECASE)
            if branch_match:
                operation["details"] = f"Push to {branch_match.group(1)}"
            else:
                operation["details"] = "Push changes"
        
        return operation
    
    def _extract_pr_id(self, text: str) -> Optional[str]:
        """Extract PR ID from text"""
        pr_match = re.search(r'PR[- #](\d+)', text, re.IGNORECASE)
        if pr_match:
            return f"PR-{pr_match.group(1)}"
        return None
    
    def _is_git_config_request(self, message: Message) -> bool:
        """Check if a message is requesting Git configuration changes"""
        # Check for Git config keywords
        config_keywords = [
            "git config", "git strategy", "branching strategy", "gitflow", 
            "github flow", "trunk based", "ci/cd", "ci cd", "ci-cd"
        ]
        
        for keyword in config_keywords:
            if keyword.lower() in message.content.lower():
                return True
                
        return False
    
    async def _handle_git_config(self, message: Message) -> Message:
        """
        Handle a Git configuration request
        
        Args:
            message: The configuration request message
            
        Returns:
            Response message
        """
        # Only users and the devops agent can change git configuration
        if message.sender not in ["user", "devops"]:
            return await self.send_message(
                recipients=[message.sender],
                content="You are not authorized to change Git configuration. Please contact the manager or DevOps agent.",
                context_tags=["#git_config", "#unauthorized"],
                message_type="config_response",
                thread_id=message.thread_id
            )
            
        # Extract configuration from the message
        updated_config = self._extract_git_config(message.content)
        
        # Apply configuration changes
        if updated_config:
            # Update project configuration
            for key, value in updated_config.items():
                if key in self.project_config:
                    # Update existing key
                    if isinstance(value, dict) and isinstance(self.project_config[key], dict):
                        # Merge dictionaries for nested configs
                        self.project_config[key].update(value)
                    else:
                        # Replace value
                        self.project_config[key] = value
            
            # Update Git extension configuration if needed
            if "git_strategy" in updated_config:
                # Update the branching strategy
                self.git_extension.git.branch_strategy = updated_config["git_strategy"]
                
                # Also update all team members using Git
                for agent_id, agent in self.team.items():
                    if hasattr(agent, 'git_extension'):
                        agent.git_extension.git.branch_strategy = updated_config["git_strategy"]
            
            response_content = f"✅ Git configuration updated successfully:\n\n{json.dumps(updated_config, indent=2)}"
        else:
            # Just return current configuration
            response_content = f"🔍 Current Git configuration:\n\n{json.dumps(self.project_config, indent=2)}"
        
        return await self.send_message(
            recipients=[message.sender],
            content=response_content,
            context_tags=["#git_config"],
            message_type="config_response",
            thread_id=message.thread_id
        )
    
    def _extract_git_config(self, text: str) -> Dict[str, Any]:
        """Extract Git configuration from text"""
        config = {}
        
        # Check for branching strategy
        if "gitflow" in text.lower():
            config["git_strategy"] = "gitflow"
        elif "github flow" in text.lower():
            config["git_strategy"] = "github-flow"
        elif "trunk" in text.lower() and "based" in text.lower():
            config["git_strategy"] = "trunk-based"
            
        # Check for CI/CD configuration
        ci_cd_config = {}
        
        if "auto deploy" in text.lower() or "auto-deploy" in text.lower():
            ci_cd_config["auto_deploy"] = "enable" in text.lower() or "on" in text.lower() or "true" in text.lower()
            
        if "run tests" in text.lower() or "run-tests" in text.lower():
            ci_cd_config["run_tests"] = "enable" in text.lower() or "on" in text.lower() or "true" in text.lower()
            
        if "environments" in text.lower():
            # Try to extract environments
            env_match = re.search(r'environments[: ]+\[(.*?)\]', text, re.IGNORECASE)
            if env_match:
                # Parse the environments list
                envs = [e.strip().strip('"\'') for e in env_match.group(1).split(",")]
                if envs:
                    ci_cd_config["environments"] = envs
        
        if ci_cd_config:
            config["ci_cd_config"] = ci_cd_config
            
        # Check for approval settings
        if "auto approval" in text.lower() or "auto-approval" in text.lower():
            config["auto_approvals"] = "enable" in text.lower() or "on" in text.lower() or "true" in text.lower()
            
        if "required approvals" in text.lower():
            # Try to extract number of required approvals
            approvals_match = re.search(r'required approvals[: ]+(\d+)', text, re.IGNORECASE)
            if approvals_match:
                config["required_approvals"] = int(approvals_match.group(1))
                
        return config
    
    async def update_git_strategy(self, strategy: str, auto_approvals: bool = False) -> Dict[str, Any]:
        """
        Update the Git branching strategy for the project
        
        Args:
            strategy: Git branching strategy (gitflow, github-flow, trunk-based)
            auto_approvals: Whether to enable auto-approvals
            
        Returns:
            Status information
        """
        # Validate strategy
        valid_strategies = ["gitflow", "github-flow", "trunk-based"]
        if strategy not in valid_strategies:
            return {
                "status": "error",
                "message": f"Invalid strategy: {strategy}. Valid options are: {', '.join(valid_strategies)}"
            }
            
        # Update project configuration
        self.project_config["git_strategy"] = strategy
        self.project_config["auto_approvals"] = auto_approvals
        
        # Update Git extension
        self.git_extension.git.branch_strategy = strategy
        
        # Notify team about the strategy change
        for agent_id, agent in self.team.items():
            if hasattr(agent, 'git_extension'):
                agent.git_extension.git.branch_strategy = strategy
                
            await self.send_message(
                recipients=[agent_id],
                content=f"The project Git strategy has been updated to {strategy}. Please follow this strategy for your branches and commits.",
                context_tags=["#git_config", "#strategy_update"],
                message_type="config_notification"
            )
            
        return {
            "status": "success",
            "message": f"Git strategy updated to {strategy}",
            "auto_approvals": auto_approvals
        } 