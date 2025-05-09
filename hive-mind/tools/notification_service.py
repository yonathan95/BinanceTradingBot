"""
Notification service for the Hive Mind system.
Handles notifications about file changes in the embedded project representation
and other events that agents need to be notified about.
"""

import asyncio
import json
import logging
from typing import Dict, Any, List, Set, Optional, Callable
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NotificationService:
    """
    Service for managing notifications between agents about file changes
    and other events in the embedded project.
    """
    
    def __init__(self, 
                team_manager=None,
                message_bus=None):
        """
        Initialize the notification service
        
        Args:
            team_manager: Optional team manager for accessing agents
            message_bus: Optional message bus for agent communication
        """
        self.team_manager = team_manager
        self.message_bus = message_bus
        self.file_watchers = {}  # Maps file paths to sets of agent_idsa
        self.project_watchers = set()  # Set of agent_ids watching the entire project
        self.last_modified = {}  # Maps file paths to last modified timestamps
        self.event_callbacks = {}  # Maps event types to callback functions
        self.pending_notifications = []  # Queue of pending notifications
    
    def register_file_watcher(self, agent_id: str, file_path: str) -> bool:
        """
        Register an agent as a watcher for a specific file
        
        Ar
            agent_id: ID of the agent that wants to watch the file
            file_path: Path to the file to watch
            
        Returns:
            True if registration was successful
        """
        if file_path not in self.file_watchers:
            self.file_watchers[file_path] = set()
            
        self.file_watchers[file_path].add(agent_id)
        logger.info(f"Agent {agent_id} is now watching file {file_path}")
        
        return True
    
    def unregister_file_watcher(self, agent_id: str, file_path: str) -> bool:
        """
        Unregister an agent as a watcher for a specific file
        
        Args:
            agent_id: ID of the agent that wants to stop watching
            file_path: Path to the file to stop watching
            
        Returns:
            True if unregistration was successful
        """
        if file_path in self.file_watchers and agent_id in self.file_watchers[file_path]:
            self.file_watchers[file_path].remove(agent_id)
            logger.info(f"Agent {agent_id} is no longer watching file {file_path}")
            
            # Clean up empty watcher sets
            if not self.file_watchers[file_path]:
                del self.file_watchers[file_path]
                
        return True
    
    def register_project_watcher(self, agent_id: str) -> bool:
        """
        Register an agent as a watcher for the entire project
        
        Args:
            agent_id: ID of the agent that wants to watch the project
            
        Returns:
            True if registration was successful
        """
        self.project_watchers.add(agent_id)
        logger.info(f"Agent {agent_id} is now watching the entire project")
        
        return True
    
    def unregister_project_watcher(self, agent_id: str) -> bool:
        """
        Unregister an agent as a watcher for the entire project
        
        Args:
            agent_id: ID of the agent that wants to stop watching
            
        Returns:
            True if unregistration was successful
        """
        if agent_id in self.project_watchers:
            self.project_watchers.remove(agent_id)
            logger.info(f"Agent {agent_id} is no longer watching the entire project")
            
        return True
    
    def register_event_callback(self, event_type: str, callback: Callable) -> bool:
        """
        Register a callback function for a specific event type
        
        Args:
            event_type: Type of event to register for
            callback: Callback function to call when the event occurs
            
        Returns:
            True if registration was successful
        """
        self.event_callbacks[event_type] = callback
        logger.info(f"Registered callback for event type: {event_type}")
        
        return True
    
    async def notify_file_change(self, 
                               file_path: str, 
                               content: str, 
                               version: str, 
                               change_type: str, 
                               change_author: str) -> None:
        """
        Notify all interested agents about a file change
        
        Args:
            file_path: Path to the file that changed
            content: New content of the file
            version: Version identifier for the new file state
            change_type: Type of change (create, update, delete)
            change_author: ID of the agent that made the change
        """
        # Update the last modified timestamp
        self.last_modified[file_path] = time.time()
        
        # Create notification data
        notification_data = {
            "type": "file_changed",
            "path": file_path,
            "content": content,
            "version": version,
            "change_type": change_type,
            "author": change_author,
            "timestamp": time.time()
        }
        
        # Collect all agents that need to be notified
        agents_to_notify = set(self.project_watchers)
        
        if file_path in self.file_watchers:
            agents_to_notify.update(self.file_watchers[file_path])
        
        # Don't notify the author of the change
        if change_author in agents_to_notify:
            agents_to_notify.remove(change_author)
        
        # Send notifications
        notification_tasks = []
        
        # First, check if there's a specific callback for file changes
        if "file_changed" in self.event_callbacks:
            try:
                await self.event_callbacks["file_changed"](notification_data)
            except Exception as e:
                logger.error(f"Error in file_changed callback: {str(e)}")
        
        # Use team manager to notify agents if available
        if self.team_manager:
            for agent_id in agents_to_notify:
                if agent_id in self.team_manager.agents:
                    try:
                        agent = self.team_manager.agents[agent_id]
                        notification_tasks.append(
                            agent.receive_message({
                                "sender": "notification_service",
                                "message_type": "file_changed_notification",
                                "content": json.dumps(notification_data),
                                "context_tags": ["#file_change", f"#{change_type}"],
                                "thread_id": f"file_change_{file_path}_{int(time.time())}"
                            })
                        )
                    except Exception as e:
                        logger.error(f"Error preparing notification for agent {agent_id}: {str(e)}")
        
        # Use message bus for notification if available
        elif self.message_bus:
            for agent_id in agents_to_notify:
                try:
                    notification_tasks.append(
                        self.message_bus.send_message(
                            sender="notification_service",
                            recipients=[agent_id],
                            message_type="file_changed_notification",
                            content=json.dumps(notification_data),
                            context_tags=["#file_change", f"#{change_type}"],
                            thread_id=f"file_change_{file_path}_{int(time.time())}"
                        )
                    )
                except Exception as e:
                    logger.error(f"Error preparing notification via message bus for agent {agent_id}: {str(e)}")
        
        # Otherwise, queue notifications for later delivery
        else:
            for agent_id in agents_to_notify:
                self.pending_notifications.append({
                    "agent_id": agent_id,
                    "data": notification_data
                })
            logger.warning("No team manager or message bus available. Notifications queued for later delivery.")
            return
        
        # Send all notifications concurrently
        if notification_tasks:
            try:
                await asyncio.gather(*notification_tasks)
                logger.info(f"Notified {len(notification_tasks)} agents about change to {file_path}")
            except Exception as e:
                logger.error(f"Error sending notifications: {str(e)}")
    
    async def notify_review_created(self, review_data: Dict[str, Any]) -> None:
        """
        Notify the code reviewer agent about a new review
        
        Args:
            review_data: Data about the review
        """
        notification_data = {
            "type": "review_created",
            **review_data
        }
        
        # Check if there's a specific callback for review creation
        if "review_created" in self.event_callbacks:
            try:
                await self.event_callbacks["review_created"](notification_data)
            except Exception as e:
                logger.error(f"Error in review_created callback: {str(e)}")
        
        # Always notify the code reviewer agent
        if self.team_manager and "code_reviewer" in self.team_manager.agents:
            try:
                await self.team_manager.agents["code_reviewer"].receive_message({
                    "sender": "notification_service",
                    "message_type": "review_request",
                    "content": json.dumps(notification_data),
                    "context_tags": ["#code_review", "#new_review"],
                    "thread_id": f"review_{review_data.get('review_id', 'unknown')}"
                })
                logger.info(f"Notified code reviewer about new review: {review_data.get('review_id', 'unknown')}")
            except Exception as e:
                logger.error(f"Error notifying code reviewer: {str(e)}")
        elif self.message_bus:
            try:
                await self.message_bus.send_message(
                    sender="notification_service",
                    recipients=["code_reviewer"],
                    message_type="review_request",
                    content=json.dumps(notification_data),
                    context_tags=["#code_review", "#new_review"],
                    thread_id=f"review_{review_data.get('review_id', 'unknown')}"
                )
                logger.info(f"Notified code reviewer via message bus about new review: {review_data.get('review_id', 'unknown')}")
            except Exception as e:
                logger.error(f"Error notifying code reviewer via message bus: {str(e)}")
        else:
            self.pending_notifications.append({
                "agent_id": "code_reviewer",
                "data": notification_data,
                "message_type": "review_request"
            })
            logger.warning("No team manager or message bus available. Notification queued for later delivery.")
    
    async def notify_review_updated(self, review_data: Dict[str, Any]) -> None:
        """
        Notify relevant agents about a review update
        
        Args:
            review_data: Data about the review update
        """
        notification_data = {
            "type": "review_updated",
            **review_data
        }
        
        # Check if there's a specific callback for review updates
        if "review_updated" in self.event_callbacks:
            try:
                await self.event_callbacks["review_updated"](notification_data)
            except Exception as e:
                logger.error(f"Error in review_updated callback: {str(e)}")
        
        # Notify the code reviewer and the author
        recipients = ["code_reviewer"]
        if "author" in review_data:
            recipients.append(review_data["author"])
        
        if self.team_manager:
            notification_tasks = []
            for agent_id in recipients:
                if agent_id in self.team_manager.agents:
                    try:
                        notification_tasks.append(
                            self.team_manager.agents[agent_id].receive_message({
                                "sender": "notification_service",
                                "message_type": "review_update",
                                "content": json.dumps(notification_data),
                                "context_tags": ["#code_review", "#update"],
                                "thread_id": f"review_{review_data.get('review_id', 'unknown')}"
                            })
                        )
                    except Exception as e:
                        logger.error(f"Error preparing notification for agent {agent_id}: {str(e)}")
            
            if notification_tasks:
                try:
                    await asyncio.gather(*notification_tasks)
                    logger.info(f"Notified {len(notification_tasks)} agents about review update: {review_data.get('review_id', 'unknown')}")
                except Exception as e:
                    logger.error(f"Error sending review update notifications: {str(e)}")
        elif self.message_bus:
            try:
                await self.message_bus.send_message(
                    sender="notification_service",
                    recipients=recipients,
                    message_type="review_update",
                    content=json.dumps(notification_data),
                    context_tags=["#code_review", "#update"],
                    thread_id=f"review_{review_data.get('review_id', 'unknown')}"
                )
                logger.info(f"Notified agents via message bus about review update: {review_data.get('review_id', 'unknown')}")
            except Exception as e:
                logger.error(f"Error notifying agents via message bus: {str(e)}")
        else:
            for agent_id in recipients:
                self.pending_notifications.append({
                    "agent_id": agent_id,
                    "data": notification_data,
                    "message_type": "review_update"
                })
            logger.warning("No team manager or message bus available. Notifications queued for later delivery.")
    
    async def deliver_pending_notifications(self) -> None:
        """
        Deliver any pending notifications that couldn't be sent earlier
        """
        if not self.team_manager and not self.message_bus:
            logger.warning("Still no team manager or message bus available. Cannot deliver pending notifications.")
            return
        
        notification_tasks = []
        delivered_indices = []
        
        for i, notification in enumerate(self.pending_notifications):
            agent_id = notification["agent_id"]
            data = notification["data"]
            message_type = notification.get("message_type", "file_changed_notification")
            
            # Use team manager if available
            if self.team_manager and agent_id in self.team_manager.agents:
                try:
                    notification_tasks.append(
                        self.team_manager.agents[agent_id].receive_message({
                            "sender": "notification_service",
                            "message_type": message_type,
                            "content": json.dumps(data),
                            "context_tags": [f"#{data.get('type', 'notification')}"],
                            "thread_id": f"{data.get('type', 'notification')}_{int(time.time())}"
                        })
                    )
                    delivered_indices.append(i)
                except Exception as e:
                    logger.error(f"Error preparing notification for agent {agent_id}: {str(e)}")
            # Otherwise use message bus
            elif self.message_bus:
                try:
                    notification_tasks.append(
                        self.message_bus.send_message(
                            sender="notification_service",
                            recipients=[agent_id],
                            message_type=message_type,
                            content=json.dumps(data),
                            context_tags=[f"#{data.get('type', 'notification')}"],
                            thread_id=f"{data.get('type', 'notification')}_{int(time.time())}"
                        )
                    )
                    delivered_indices.append(i)
                except Exception as e:
                    logger.error(f"Error preparing notification via message bus for agent {agent_id}: {str(e)}")
        
        # Send all notifications concurrently
        if notification_tasks:
            try:
                await asyncio.gather(*notification_tasks)
                logger.info(f"Delivered {len(notification_tasks)} pending notifications")
                
                # Remove delivered notifications
                self.pending_notifications = [n for i, n in enumerate(self.pending_notifications) if i not in delivered_indices]
            except Exception as e:
                logger.error(f"Error sending pending notifications: {str(e)}")
    
    async def handle_notification(self, notification_data: Dict[str, Any]) -> None:
        """
        Process a notification and distribute it to the appropriate handlers
        
        Args:
            notification_data: Data about the notification
        """
        notification_type = notification_data.get("type")
        
        if not notification_type:
            logger.error("Received notification with no type")
            return
        
        # Check if there's a specific callback for this notification type
        if notification_type in self.event_callbacks:
            try:
                await self.event_callbacks[notification_type](notification_data)
            except Exception as e:
                logger.error(f"Error in {notification_type} callback: {str(e)}")
        
        # Handle specific notification types
        if notification_type == "file_changed":
            await self.notify_file_change(
                notification_data.get("path", ""),
                notification_data.get("content", ""),
                notification_data.get("version", "unknown"),
                notification_data.get("change_type", "update"),
                notification_data.get("author", "unknown")
            )
        elif notification_type == "pending_review":
            await self.notify_review_created(notification_data)
        elif notification_type in ["review_added", "commit_approved", "commit_rejected"]:
            await self.notify_review_updated(notification_data)
    
    def get_file_watchers(self, file_path: str) -> List[str]:
        """
        Get the list of agents watching a file
        
        Args:
            file_path: Path to the file
            
        Returns:
            List of agent IDs watching the file
        """
        watchers = list(self.project_watchers)
        
        if file_path in self.file_watchers:
            watchers.extend(list(self.file_watchers[file_path]))
            
        # Remove duplicates
        return list(set(watchers))
    
    def get_last_modified(self, file_path: str) -> Optional[float]:
        """
        Get the timestamp when a file was last modified
        
        Args:
            file_path: Path to the file
            
        Returns:
            Timestamp of last modification, or None if unknown
        """
        return self.last_modified.get(file_path) 