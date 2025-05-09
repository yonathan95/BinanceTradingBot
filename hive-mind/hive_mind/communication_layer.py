"""
Inter-Team Communication Layer (ITCL) - Manages communication between different teams in the Hive Mind system.
The ITCL is responsible for routing messages, tagging context, and summarizing conversations.
"""

import asyncio
import json
import logging
import time
import uuid
from typing import Dict, List, Any, Optional, Set, Tuple

import aioredis
from pydantic import BaseModel

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ContextTag(BaseModel):
    """Represents a context tag for message routing."""
    name: str
    description: str
    related_tags: List[str] = []


class Message(BaseModel):
    """Represents a message sent between agents or teams."""
    id: str
    sender: str
    recipients: List[str]
    content: str
    context_tags: List[str]
    message_type: str  # question, answer, update, broadcast
    priority: str  # high, normal, low
    requires_response: bool
    thread_id: str
    timestamp: float
    metadata: Dict[str, Any] = {}
    summarized: bool = False
    original_size: Optional[int] = None

    def __init__(self, **data):
        if 'id' not in data:
            data['id'] = str(uuid.uuid4())
        if 'timestamp' not in data:
            data['timestamp'] = time.time()
        if 'context_tags' not in data:
            data['context_tags'] = []
        super().__init__(**data)


class TeamGraph(BaseModel):
    """Represents the directed-acyclic graph of team relationships."""
    teams: Dict[str, Dict[str, Any]]  # Team ID -> Team info
    connections: Dict[str, List[str]]  # Team ID -> List of connected team IDs
    tag_routes: Dict[str, List[str]]  # Context tag -> List of team IDs

    def add_team(self, team_id: str, team_info: Dict[str, Any]):
        """Add a team to the graph."""
        self.teams[team_id] = team_info
        if team_id not in self.connections:
            self.connections[team_id] = []

    def add_connection(self, source_team: str, target_team: str):
        """Add a connection between teams."""
        if source_team not in self.teams or target_team not in self.teams:
            raise ValueError("Both teams must exist in the graph")
        
        if target_team not in self.connections[source_team]:
            self.connections[source_team].append(target_team)

    def add_tag_route(self, tag: str, team_ids: List[str]):
        """Add a routing rule for a specific context tag."""
        self.tag_routes[tag] = team_ids


class ConversationSummary(BaseModel):
    """Represents a summary of a conversation thread."""
    thread_id: str
    summary: str
    participants: List[str]
    latest_timestamp: float
    message_count: int
    tags: List[str]
    metadata: Dict[str, Any] = {}


class InterTeamCommunicationLayer:
    """
    Manages communication between different teams in the Hive Mind system.
    Handles message routing, context tagging, and conversation summarization.
    """
    
    def __init__(self, 
                redis_url: Optional[str] = None,
                local_mode: bool = True,
                summarization_model: str = "gpt-3.5-turbo"):
        """
        Initialize the Inter-Team Communication Layer.
        
        Args:
            redis_url: URL for Redis connection
            local_mode: If True, use in-memory storage instead of Redis
            summarization_model: Model to use for summarizing conversations
        """
        self.redis_url = redis_url
        self.local_mode = local_mode
        self.summarization_model = summarization_model
        
        # In-memory storage
        self.messages: Dict[str, Message] = {}
        self.threads: Dict[str, List[str]] = {}  # Thread ID -> List of message IDs
        self.summaries: Dict[str, ConversationSummary] = {}
        
        # Team graph for routing
        self.team_graph = TeamGraph(
            teams={},
            connections={},
            tag_routes={}
        )
        
        # Context tags
        self.tags: Dict[str, ContextTag] = {}
        
        # Redis connection
        self.redis = None
        
        logger.info(f"ITCL initialized in {'local' if local_mode else 'production'} mode")
    
    async def initialize(self):
        """Initialize the ITCL."""
        if not self.local_mode and self.redis_url:
            try:
                self.redis = await aioredis.create_redis_pool(self.redis_url)
                logger.info(f"Connected to Redis at {self.redis_url}")
                
                # Load data from Redis
                await self._load_state()
            except Exception as e:
                logger.error(f"Failed to connect to Redis: {str(e)}")
                logger.warning("Falling back to local mode")
                self.local_mode = True
    
    async def _load_state(self):
        """Load state from Redis."""
        if not self.redis:
            return
            
        # Load tags
        tag_keys = await self.redis.keys('tag:*')
        for key in tag_keys:
            tag_data = await self.redis.get(key)
            if tag_data:
                tag = ContextTag(**json.loads(tag_data))
                self.tags[tag.name] = tag
        
        # Load team graph
        graph_data = await self.redis.get('team_graph')
        if graph_data:
            self.team_graph = TeamGraph(**json.loads(graph_data))
        
        logger.info(f"Loaded {len(self.tags)} tags and team graph from Redis")
    
    async def close(self):
        """Close connections and clean up resources."""
        if self.redis:
            self.redis.close()
            await self.redis.wait_closed()
    
    async def register_context_tag(self, tag: ContextTag) -> bool:
        """
        Register a new context tag for message routing.
        
        Args:
            tag: ContextTag object with name, description, and related tags
            
        Returns:
            True if registration was successful
        """
        self.tags[tag.name] = tag
        
        if not self.local_mode and self.redis:
            await self.redis.set(f'tag:{tag.name}', json.dumps(tag.dict()))
        
        logger.info(f"Registered context tag: {tag.name}")
        return True
    
    async def update_team_graph(self, team_graph: TeamGraph) -> bool:
        """
        Update the team graph for message routing.
        
        Args:
            team_graph: Updated TeamGraph object
            
        Returns:
            True if update was successful
        """
        self.team_graph = team_graph
        
        if not self.local_mode and self.redis:
            await self.redis.set('team_graph', json.dumps(team_graph.dict()))
        
        logger.info("Updated team graph")
        return True
    
    async def send_message(self, message_data: Dict[str, Any]) -> Message:
        """
        Send a message between agents or teams.
        
        Args:
            message_data: Dictionary with message data
                {
                    "sender": str,
                    "recipients": List[str],  # Can be agent IDs or team IDs
                    "content": str,
                    "context_tags": List[str],
                    "message_type": str,
                    "priority": str,
                    "requires_response": bool,
                    "thread_id": str,
                    "metadata": Dict[str, Any]
                }
                
        Returns:
            Created Message object
        """
        message = Message(**message_data)
        
        # Store message
        self.messages[message.id] = message
        
        # Add to thread
        if message.thread_id not in self.threads:
            self.threads[message.thread_id] = []
        self.threads[message.thread_id].append(message.id)
        
        # Store in Redis if applicable
        if not self.local_mode and self.redis:
            await self.redis.set(f'message:{message.id}', json.dumps(message.dict()))
            await self.redis.rpush(f'thread:{message.thread_id}', message.id)
        
        # Route message
        await self._route_message(message)
        
        return message
    
    async def _route_message(self, message: Message):
        """
        Route a message to appropriate recipients based on context tags.
        
        Args:
            message: Message to route
        """
        # If recipients are explicitly specified, send directly
        if message.recipients:
            for recipient in message.recipients:
                await self._deliver_message(message, recipient)
            return
        
        # Otherwise, use context tags for routing
        target_teams = set()
        
        for tag in message.context_tags:
            if tag in self.team_graph.tag_routes:
                for team_id in self.team_graph.tag_routes[tag]:
                    target_teams.add(team_id)
        
        # If no routing rules match, log warning
        if not target_teams:
            logger.warning(f"No routing rules found for tags: {message.context_tags}")
            return
        
        # Deliver to target teams
        for team_id in target_teams:
            await self._deliver_message(message, team_id)
    
    async def _deliver_message(self, message: Message, recipient: str):
        """
        Deliver a message to a specific recipient.
        
        Args:
            message: Message to deliver
            recipient: Recipient ID (agent or team)
        """
        # Check if we should summarize before sending
        if self._should_summarize(message, recipient):
            summarized_message = await self._create_summarized_message(message)
            message_to_deliver = summarized_message
        else:
            message_to_deliver = message
        
        # In local mode, we just log the delivery
        if self.local_mode:
            logger.info(f"Delivered message {message_to_deliver.id} to {recipient}")
        else:
            # In production mode, publish to Redis
            if self.redis:
                await self.redis.publish(
                    f'inbox:{recipient}',
                    json.dumps(message_to_deliver.dict())
                )
    
    def _should_summarize(self, message: Message, recipient: str) -> bool:
        """
        Determine if a message should be summarized before delivery.
        
        Args:
            message: Message to check
            recipient: Recipient ID
            
        Returns:
            True if message should be summarized
        """
        # Check if message is going across team boundaries
        sender_team = self._get_team_for_agent(message.sender)
        recipient_team = recipient if recipient in self.team_graph.teams else self._get_team_for_agent(recipient)
        
        if sender_team != recipient_team:
            # Cross-team communication might need summarization
            content_length = len(message.content)
            if content_length > 500:  # If message is long
                return True
        
        return False
    
    def _get_team_for_agent(self, agent_id: str) -> Optional[str]:
        """
        Get the team ID for an agent.
        
        Args:
            agent_id: Agent ID
            
        Returns:
            Team ID or None
        """
        # This would be implemented to look up agent's team
        # For now, we use a simple convention: agent_id starts with team_ prefix
        if '_' in agent_id:
            return agent_id.split('_')[0]
        return None
    
    async def _create_summarized_message(self, original_message: Message) -> Message:
        """
        Create a summarized version of a message.
        
        Args:
            original_message: Original message to summarize
            
        Returns:
            Summarized message
        """
        # In a real implementation, this would call the LLM to summarize
        # For now, we'll just create a mock summary
        
        # Basic truncation-based summary as a fallback
        content = original_message.content
        original_size = len(content)
        
        if original_size > 500:
            summary = content[:250] + "... [summarized]..." + content[-250:]
        else:
            summary = content
        
        # Create new message with the summary
        summarized_message = Message(
            sender=original_message.sender,
            recipients=original_message.recipients,
            content=summary,
            context_tags=original_message.context_tags,
            message_type=original_message.message_type,
            priority=original_message.priority,
            requires_response=original_message.requires_response,
            thread_id=original_message.thread_id,
            metadata=original_message.metadata,
            summarized=True,
            original_size=original_size
        )
        
        return summarized_message
    
    async def get_message(self, message_id: str) -> Optional[Message]:
        """
        Retrieve a message by ID.
        
        Args:
            message_id: ID of the message
            
        Returns:
            Message object or None
        """
        if self.local_mode:
            return self.messages.get(message_id)
        else:
            if self.redis:
                message_data = await self.redis.get(f'message:{message_id}')
                if message_data:
                    return Message(**json.loads(message_data))
        return None
    
    async def get_thread_messages(self, thread_id: str) -> List[Message]:
        """
        Get all messages in a thread.
        
        Args:
            thread_id: ID of the thread
            
        Returns:
            List of Message objects
        """
        if self.local_mode:
            message_ids = self.threads.get(thread_id, [])
            return [self.messages[msg_id] for msg_id in message_ids if msg_id in self.messages]
        else:
            if self.redis:
                message_ids = await self.redis.lrange(f'thread:{thread_id}', 0, -1)
                messages = []
                for msg_id in message_ids:
                    message_data = await self.redis.get(f'message:{msg_id.decode("utf-8")}')
                    if message_data:
                        messages.append(Message(**json.loads(message_data)))
                return messages
        return []
    
    async def create_thread_summary(self, thread_id: str) -> Optional[ConversationSummary]:
        """
        Create a summary of a conversation thread.
        
        Args:
            thread_id: ID of the thread
            
        Returns:
            ConversationSummary object or None
        """
        messages = await self.get_thread_messages(thread_id)
        if not messages:
            return None
        
        # In a real implementation, this would call the LLM to create a summary
        # For now, we'll create a simple mock summary
        
        participants = list(set(msg.sender for msg in messages))
        tags = list(set(tag for msg in messages for tag in msg.context_tags))
        latest_timestamp = max(msg.timestamp for msg in messages)
        
        # Simple summary based on first and last few messages
        if len(messages) <= 2:
            summary = " | ".join(msg.content[:100] for msg in messages)
        else:
            first_msg = messages[0].content[:100]
            last_msg = messages[-1].content[:100]
            summary = f"Thread with {len(messages)} messages. Started with: '{first_msg}...' and ended with: '{last_msg}...'"
        
        summary_obj = ConversationSummary(
            thread_id=thread_id,
            summary=summary,
            participants=participants,
            latest_timestamp=latest_timestamp,
            message_count=len(messages),
            tags=tags
        )
        
        # Store summary
        self.summaries[thread_id] = summary_obj
        
        if not self.local_mode and self.redis:
            await self.redis.set(f'summary:{thread_id}', json.dumps(summary_obj.dict()))
        
        return summary_obj
    
    async def broadcast_message(self, sender: str, content: str, 
                          tags: List[str], metadata: Dict[str, Any] = None) -> List[Message]:
        """
        Broadcast a message to all teams matching the given tags.
        
        Args:
            sender: ID of the sender
            content: Message content
            tags: Context tags for routing
            metadata: Additional metadata
            
        Returns:
            List of created Message objects
        """
        if metadata is None:
            metadata = {}
            
        # Find target teams based on tags
        target_teams = set()
        for tag in tags:
            if tag in self.team_graph.tag_routes:
                for team_id in self.team_graph.tag_routes[tag]:
                    target_teams.add(team_id)
        
        messages = []
        thread_id = f"broadcast-{uuid.uuid4()}"
        
        for team_id in target_teams:
            message_data = {
                "sender": sender,
                "recipients": [team_id],
                "content": content,
                "context_tags": tags,
                "message_type": "broadcast",
                "priority": "normal",
                "requires_response": False,
                "thread_id": thread_id,
                "metadata": metadata
            }
            
            message = await self.send_message(message_data)
            messages.append(message)
        
        return messages
    
    async def forward_message(self, original_message_id: str, 
                        new_recipients: List[str], 
                        additional_context: Optional[str] = None) -> Optional[Message]:
        """
        Forward an existing message to new recipients with optional additional context.
        
        Args:
            original_message_id: ID of the message to forward
            new_recipients: List of recipient IDs
            additional_context: Optional additional context to add
            
        Returns:
            Forwarded Message object or None if original not found
        """
        original_message = await self.get_message(original_message_id)
        if not original_message:
            return None
        
        # Create forwarded content
        if additional_context:
            content = f"{additional_context}\n\n--- Forwarded Message ---\n{original_message.content}"
        else:
            content = f"--- Forwarded Message ---\n{original_message.content}"
        
        # Create new message
        message_data = {
            "sender": original_message.sender,
            "recipients": new_recipients,
            "content": content,
            "context_tags": original_message.context_tags,
            "message_type": "forward",
            "priority": original_message.priority,
            "requires_response": original_message.requires_response,
            "thread_id": original_message.thread_id,
            "metadata": {
                **original_message.metadata,
                "forwarded_from": original_message_id
            }
        }
        
        return await self.send_message(message_data) 