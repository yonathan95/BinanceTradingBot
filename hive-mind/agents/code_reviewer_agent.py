"""
Code Reviewer Agent - Specializes in reviewing and approving code changes
for the embedded project representation. Works with the version control tool
to manage the code review workflow.
"""

import logging
import json
from typing import List, Dict, Any, Optional
import asyncio

from hive_mind.agent_sdk.base_agent import BaseAgent, Message

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CodeReviewerAgent(BaseAgent):
    """
    Code Reviewer Agent that evaluates code changes submitted by other agents,
    coordinates with skeptic agents, and approves or rejects changes to the
    embedded project representation.
    """
    
    def __init__(self, 
                agent_id: str = "code_reviewer", 
                model: str = "gpt-4", 
                temperature: float = 0.1,  # Low temperature for more consistent reviews
                token_limit: int = 4096,
                memory_enabled: bool = True,
                embedding_model: str = "text-embedding-ada-002",
                vector_db_url: Optional[str] = None,
                version_control_tool=None,
                skeptic_agents: List[str] = None):
        """Initialize the Code Reviewer Agent"""
        super().__init__(
            agent_id=agent_id, 
            model=model, 
            temperature=temperature, 
            token_limit=token_limit,
            memory_enabled=memory_enabled,
            embedding_model=embedding_model,
            vector_db_url=vector_db_url
        )
        self.version_control_tool = version_control_tool
        self.skeptic_agents = skeptic_agents or ["code_quality_skeptic", "security_skeptic"]
        self.pending_reviews = {}  # Maps review_ids to review data
        self.skeptic_feedback = {}  # Maps review_ids to skeptic feedback
    
    async def process_message(self, message: Message) -> Message:
        """
        Process an incoming message and generate a response
        
        Args:
            message: The incoming message
            
        Returns:
            A response message
        """
        if message.message_type == "review_request":
            return await self._handle_review_request(message)
        elif message.message_type == "skeptic_feedback":
            return await self._handle_skeptic_feedback(message)
        elif message.message_type == "review_update":
            return await self._handle_review_update(message)
        elif message.message_type == "file_changed_notification":
            return await self._handle_file_changed(message)
        else:
            # Default handling for other message types
            prompt = await self.generate_prompt({
                "message": message.content,
                "sender": message.sender,
                "context_tags": message.context_tags,
                "type": "default"
            })
            
            response = await self.call_llm(prompt)
            
            return await self.send_message(
                recipients=[message.sender],
                content=response["content"],
                context_tags=message.context_tags + ["#code_review"],
                message_type="response",
                thread_id=message.thread_id
            )
    
    async def _handle_review_request(self, message: Message) -> Message:
        """
        Handle a code review request
        
        Args:
            message: The review request message containing file path and review ID
            
        Returns:
            A response message acknowledging the review request
        """
        try:
            review_data = json.loads(message.content)
            path = review_data.get("path")
            review_id = review_data.get("review_id")
            
            if not path or not review_id:
                return await self.send_message(
                    recipients=[message.sender],
                    content="Invalid review request. Missing path or review_id.",
                    context_tags=["#error", "#code_review"],
                    message_type="error",
                    thread_id=message.thread_id
                )
            
            # Store the review request
            self.pending_reviews[review_id] = review_data
            
            # Fetch the file content for review from version control
            if self.version_control_tool:
                file_status = await self.version_control_tool.execute(
                    action="status",
                    path=path
                )
                
                if not file_status.get("success"):
                    return await self.send_message(
                        recipients=[message.sender],
                        content=f"Error fetching file status: {file_status.get('error')}",
                        context_tags=["#error", "#code_review"],
                        message_type="error",
                        thread_id=message.thread_id
                    )
                
                review_data = file_status.get("review_data")
                if not review_data:
                    return await self.send_message(
                        recipients=[message.sender],
                        content=f"No pending review found for {path}",
                        context_tags=["#error", "#code_review"],
                        message_type="error",
                        thread_id=message.thread_id
                    )
                
                # Store the updated review data
                self.pending_reviews[review_id] = review_data
                
                # Request feedback from skeptic agents
                await self._request_skeptic_feedback(review_id, path, review_data, message.thread_id)
                
                return await self.send_message(
                    recipients=[message.sender],
                    content=f"Review request for {path} (ID: {review_id}) received. Requesting feedback from skeptic agents.",
                    context_tags=["#code_review", "#started"],
                    message_type="review_started",
                    thread_id=message.thread_id
                )
            else:
                return await self.send_message(
                    recipients=[message.sender],
                    content="Version control tool not configured. Cannot process review request.",
                    context_tags=["#error", "#code_review"],
                    message_type="error",
                    thread_id=message.thread_id
                )
        except Exception as e:
            return await self.send_message(
                recipients=[message.sender],
                content=f"Error processing review request: {str(e)}",
                context_tags=["#error", "#code_review"],
                message_type="error",
                thread_id=message.thread_id
            )
    
    async def _request_skeptic_feedback(self, review_id: str, path: str, review_data: Dict[str, Any], thread_id: str):
        """
        Request feedback from skeptic agents
        
        Args:
            review_id: ID of the review
            path: Path to the file being reviewed
            review_data: Review data
            thread_id: Thread ID for the review conversation
        """
        self.skeptic_feedback[review_id] = {}
        
        for skeptic_id in self.skeptic_agents:
            # Check if the skeptic agent is available in our team
            if skeptic_id in self.team:
                content = json.dumps({
                    "review_id": review_id,
                    "path": path,
                    "content": review_data.get("content", ""),
                    "author": review_data.get("author", "unknown"),
                    "commit_message": review_data.get("commit_message", "")
                })
                
                await self.send_message(
                    recipients=[skeptic_id],
                    content=content,
                    context_tags=["#code_review", "#feedback_request"],
                    message_type="feedback_request",
                    thread_id=thread_id,
                    requires_response=True
                )
    
    async def _handle_skeptic_feedback(self, message: Message) -> Message:
        """
        Handle feedback from a skeptic agent
        
        Args:
            message: The feedback message
            
        Returns:
            A response acknowledging the feedback
        """
        try:
            feedback_data = json.loads(message.content)
            review_id = feedback_data.get("review_id")
            
            if not review_id:
                return await self.send_message(
                    recipients=[message.sender],
                    content="Invalid skeptic feedback. Missing review_id.",
                    context_tags=["#error", "#code_review"],
                    message_type="error",
                    thread_id=message.thread_id
                )
            
            # Store the feedback
            if review_id not in self.skeptic_feedback:
                self.skeptic_feedback[review_id] = {}
            
            self.skeptic_feedback[review_id][message.sender] = feedback_data
            
            # Check if we have feedback from all skeptics
            if review_id in self.pending_reviews:
                review_data = self.pending_reviews[review_id]
                
                # If we have feedback from all required skeptics, evaluate the review
                if self._has_all_required_feedback(review_id):
                    await self._evaluate_review(review_id, review_data, message.thread_id)
            
            return await self.send_message(
                recipients=[message.sender],
                content=f"Feedback received for review {review_id}. Thank you.",
                context_tags=["#code_review", "#feedback"],
                message_type="feedback_received",
                thread_id=message.thread_id
            )
        except Exception as e:
            return await self.send_message(
                recipients=[message.sender],
                content=f"Error processing skeptic feedback: {str(e)}",
                context_tags=["#error", "#code_review"],
                message_type="error",
                thread_id=message.thread_id
            )
    
    def _has_all_required_feedback(self, review_id: str) -> bool:
        """
        Check if we have feedback from all required skeptics
        
        Args:
            review_id: ID of the review
            
        Returns:
            True if we have all required feedback, False otherwise
        """
        if review_id not in self.skeptic_feedback:
            return False
        
        # Check if we have feedback from all available skeptics
        available_skeptics = [s for s in self.skeptic_agents if s in self.team]
        received_from = set(self.skeptic_feedback[review_id].keys())
        
        # We need feedback from at least one skeptic
        return len(received_from) > 0 and received_from.issuperset(set(available_skeptics))
    
    async def _evaluate_review(self, review_id: str, review_data: Dict[str, Any], thread_id: str):
        """
        Evaluate the review based on skeptic feedback and make a decision
        
        Args:
            review_id: ID of the review
            review_data: Review data
            thread_id: Thread ID for the review conversation
        """
        path = review_data.get("path")
        author = review_data.get("author")
        
        # Compile feedback from all skeptics
        feedback_summary = []
        blockers = []
        
        for skeptic_id, feedback in self.skeptic_feedback[review_id].items():
            feedback_content = feedback.get("feedback", "")
            is_blocking = feedback.get("is_blocking", False)
            
            feedback_summary.append(f"Feedback from {skeptic_id}:\n{feedback_content}")
            
            if is_blocking:
                blockers.append(f"{skeptic_id}: {feedback.get('blocking_reason', 'No reason specified')}")
        
        combined_feedback = "\n\n".join(feedback_summary)
        
        # Generate a prompt for decision making
        prompt = await self.generate_prompt({
            "review_id": review_id,
            "path": path,
            "content": review_data.get("content", ""),
            "author": author,
            "commit_message": review_data.get("commit_message", ""),
            "feedback": combined_feedback,
            "blockers": blockers,
            "type": "review_decision"
        })
        
        # Call LLM for decision
        decision_response = await self.call_llm(prompt)
        decision_content = decision_response["content"]
        
        # Parse the decision
        # The LLM should return a JSON-like structure with decision and rationale
        try:
            decision_data = json.loads(decision_content)
            approve = decision_data.get("approve", False)
            rationale = decision_data.get("rationale", "")
            
            if approve and not blockers:
                # Approve the changes
                if self.version_control_tool:
                    approval_result = await self.version_control_tool.execute(
                        action="approve",
                        path=path,
                        message=rationale,
                        agent_id=self.agent_id
                    )
                    
                    # Notify the author and all skeptics
                    notify_recipients = [author] + list(self.skeptic_feedback[review_id].keys())
                    
                    await self.send_message(
                        recipients=notify_recipients,
                        content=f"Changes to {path} have been APPROVED.\n\nRationale: {rationale}\n\nThe changes have been merged into the embedded project.",
                        context_tags=["#code_review", "#approved"],
                        message_type="review_decision",
                        thread_id=thread_id
                    )
            else:
                # Reject the changes
                rejection_reason = rationale
                if blockers:
                    rejection_reason += f"\n\nBlocking issues:\n" + "\n".join(blockers)
                
                if self.version_control_tool:
                    rejection_result = await self.version_control_tool.execute(
                        action="reject",
                        path=path,
                        message=rejection_reason,
                        agent_id=self.agent_id
                    )
                    
                    # Notify the author and all skeptics
                    notify_recipients = [author] + list(self.skeptic_feedback[review_id].keys())
                    
                    await self.send_message(
                        recipients=notify_recipients,
                        content=f"Changes to {path} have been REJECTED.\n\nReason: {rejection_reason}\n\nPlease address the feedback and submit an updated version.",
                        context_tags=["#code_review", "#rejected"],
                        message_type="review_decision",
                        thread_id=thread_id
                    )
            
            # Clean up
            if review_id in self.pending_reviews:
                del self.pending_reviews[review_id]
            if review_id in self.skeptic_feedback:
                del self.skeptic_feedback[review_id]
                
        except (json.JSONDecodeError, KeyError) as e:
            logger.error(f"Error parsing decision: {e}")
            
            # Send an error message
            await self.send_message(
                recipients=[author],
                content=f"Error processing review decision for {path}. Please contact an administrator.",
                context_tags=["#error", "#code_review"],
                message_type="error",
                thread_id=thread_id
            )
    
    async def _handle_review_update(self, message: Message) -> Message:
        """
        Handle a notification about a review update
        
        Args:
            message: The update message
            
        Returns:
            A response acknowledging the update
        """
        try:
            update_data = json.loads(message.content)
            review_id = update_data.get("review_id")
            path = update_data.get("path")
            
            if not review_id or not path:
                return await self.send_message(
                    recipients=[message.sender],
                    content="Invalid review update. Missing review_id or path.",
                    context_tags=["#error", "#code_review"],
                    message_type="error",
                    thread_id=message.thread_id
                )
            
            # Fetch the latest review data
            if self.version_control_tool:
                file_status = await self.version_control_tool.execute(
                    action="status",
                    path=path
                )
                
                if not file_status.get("success"):
                    return await self.send_message(
                        recipients=[message.sender],
                        content=f"Error fetching file status: {file_status.get('error')}",
                        context_tags=["#error", "#code_review"],
                        message_type="error",
                        thread_id=message.thread_id
                    )
                
                review_data = file_status.get("review_data")
                if not review_data:
                    return await self.send_message(
                        recipients=[message.sender],
                        content=f"No pending review found for {path}",
                        context_tags=["#error", "#code_review"],
                        message_type="error",
                        thread_id=message.thread_id
                    )
                
                # Update the stored review data
                self.pending_reviews[review_id] = review_data
                
                return await self.send_message(
                    recipients=[message.sender],
                    content=f"Review data updated for {path} (ID: {review_id}).",
                    context_tags=["#code_review", "#updated"],
                    message_type="review_updated",
                    thread_id=message.thread_id
                )
            else:
                return await self.send_message(
                    recipients=[message.sender],
                    content="Version control tool not configured. Cannot process review update.",
                    context_tags=["#error", "#code_review"],
                    message_type="error",
                    thread_id=message.thread_id
                )
        except Exception as e:
            return await self.send_message(
                recipients=[message.sender],
                content=f"Error processing review update: {str(e)}",
                context_tags=["#error", "#code_review"],
                message_type="error",
                thread_id=message.thread_id
            )
    
    async def _handle_file_changed(self, message: Message) -> Message:
        """
        Handle a notification about a file change in the embedded project
        
        Args:
            message: The notification message
            
        Returns:
            A response acknowledging the notification
        """
        try:
            change_data = json.loads(message.content)
            path = change_data.get("path")
            
            if not path:
                return await self.send_message(
                    recipients=[message.sender],
                    content="Invalid file change notification. Missing path.",
                    context_tags=["#error", "#file_change"],
                    message_type="error",
                    thread_id=message.thread_id
                )
            
            # Log the file change
            logger.info(f"File changed in embedded project: {path}")
            
            return await self.send_message(
                recipients=[message.sender],
                content=f"Acknowledged file change notification for {path}.",
                context_tags=["#file_change", "#acknowledged"],
                message_type="notification_ack",
                thread_id=message.thread_id
            )
        except Exception as e:
            return await self.send_message(
                recipients=[message.sender],
                content=f"Error processing file change notification: {str(e)}",
                context_tags=["#error", "#file_change"],
                message_type="error",
                thread_id=message.thread_id
            )
    
    async def generate_prompt(self, context: Dict[str, Any]) -> str:
        """
        Generate a prompt based on the context
        
        Args:
            context: The context for generating the prompt
            
        Returns:
            The generated prompt
        """
        if context.get("type") == "review_decision":
            return f"""
            You are a Code Reviewer Agent in the Hive Mind AI system. You need to make a decision about whether 
            to approve or reject changes to a file in the embedded project representation.
            
            Review details:
            - Review ID: {context.get('review_id')}
            - File path: {context.get('path')}
            - Author: {context.get('author')}
            - Commit message: {context.get('commit_message')}
            
            Here is the code content:
            ```
            {context.get('content')}
            ```
            
            Feedback from skeptic agents:
            {context.get('feedback')}
            
            Blocking issues identified:
            {context.get('blockers')}
            
            Based on the feedback and any blocking issues, decide whether to approve or reject these changes.
            Consider code quality, security, maintainability, and adherence to best practices.
            
            Return your decision in the following JSON format:
            {{
                "approve": true/false,
                "rationale": "Your detailed explanation for the decision"
            }}
            
            Provide a thorough rationale that explains your decision and summarizes the key points from the feedback.
            """
        elif context.get("type") == "default":
            return f"""
            You are a Code Reviewer Agent in the Hive Mind AI system. Your role is to coordinate the review process
            for code changes submitted to the embedded project representation.
            
            Message from {context.get('sender')}:
            {context.get('message')}
            
            Context tags: {', '.join(context.get('context_tags', []))}
            
            Respond professionally and helpfully, explaining the code review process if needed.
            """
        else:
            return f"""
            You are a Code Reviewer Agent in the Hive Mind AI system.
            
            Message from {context.get('sender')}:
            {context.get('message')}
            
            Context tags: {', '.join(context.get('context_tags', []))}
            
            Respond professionally and helpfully.
            """ 