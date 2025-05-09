import json
import time
import asyncio
from typing import Dict, List, Any, Optional, Tuple, Set
import uuid

from .base_agent import BaseAgent, Message


class MeetingProtocol:
    """
    Facilitates collaborative meetings between agents, particularly between regular agents and skeptic agents.
    Manages the discussion flow, records the meeting transcript, and helps reach consensus.
    """
    
    def __init__(self, 
                 meeting_id: Optional[str] = None,
                 topic: str = "",
                 description: str = "",
                 facilitator: Optional[BaseAgent] = None):
        """
        Initialize a meeting protocol
        
        Args:
            meeting_id: Unique identifier for the meeting (generated if not provided)
            topic: The topic of the meeting
            description: A description of the meeting purpose
            facilitator: The agent that facilitates the meeting (typically a Manager agent)
        """
        self.meeting_id = meeting_id or f"meeting_{str(uuid.uuid4())}"
        self.topic = topic
        self.description = description
        self.facilitator = facilitator
        self.participants: List[BaseAgent] = []
        self.transcript: List[Dict[str, Any]] = []
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None
        self.status = "created"  # created, in_progress, completed, cancelled
        self.decisions: List[Dict[str, Any]] = []
        self.action_items: List[Dict[str, Any]] = []
        self.consensus: Dict[str, Any] = {}
        
    def add_participant(self, agent: BaseAgent) -> None:
        """
        Add a participant to the meeting
        
        Args:
            agent: The agent to add to the meeting
        """
        if agent not in self.participants:
            self.participants.append(agent)
    
    async def start_meeting(self) -> None:
        """
        Start the meeting, notifying all participants
        """
        self.start_time = time.time()
        self.status = "in_progress"
        
        # Prepare the meeting context
        meeting_context = {
            "meeting_id": self.meeting_id,
            "topic": self.topic,
            "description": self.description,
            "participants": [agent.agent_id for agent in self.participants],
            "start_time": self.start_time
        }
        
        # Notify all participants that the meeting has started
        start_message = Message(
            sender="meeting_system",
            recipients=[agent.agent_id for agent in self.participants],
            context_tags=["#meeting", "#start"],
            message_type="meeting_start",
            content=f"Meeting {self.meeting_id} has started. Topic: {self.topic}. {self.description}",
            thread_id=self.meeting_id,
            metadata=meeting_context
        )
        
        # Send the message to all participants
        for participant in self.participants:
            await participant.receive_message(start_message)
            
        # Record this in the transcript
        self.transcript.append({
            "timestamp": time.time(),
            "type": "system",
            "content": start_message.content,
            "metadata": meeting_context
        })
    
    async def end_meeting(self, summary: Optional[str] = None) -> Dict[str, Any]:
        """
        End the meeting, providing a summary of decisions and action items
        
        Args:
            summary: Optional summary of the meeting
            
        Returns:
            Summary information about the meeting
        """
        self.end_time = time.time()
        self.status = "completed"
        
        # Generate a summary if none was provided
        if not summary:
            summary = self._generate_summary()
        
        # Prepare the meeting results
        meeting_results = {
            "meeting_id": self.meeting_id,
            "topic": self.topic,
            "description": self.description,
            "participants": [agent.agent_id for agent in self.participants],
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration_minutes": round((self.end_time - self.start_time) / 60, 2) if self.start_time else 0,
            "decisions": self.decisions,
            "action_items": self.action_items,
            "consensus": self.consensus,
            "summary": summary
        }
        
        # Notify all participants that the meeting has ended
        end_message = Message(
            sender="meeting_system",
            recipients=[agent.agent_id for agent in self.participants],
            context_tags=["#meeting", "#end"],
            message_type="meeting_end",
            content=f"Meeting {self.meeting_id} has ended. Summary: {summary}",
            thread_id=self.meeting_id,
            metadata=meeting_results
        )
        
        # Send the message to all participants and store in their memory
        for participant in self.participants:
            await participant.receive_message(end_message)
            
            # Store meeting results in agent memory if it has memory capabilities
            if hasattr(participant, 'memory') and participant.memory:
                await participant.memory.add_memory(
                    content=json.dumps(meeting_results),
                    metadata={
                        "type": "meeting_record",
                        "meeting_id": self.meeting_id,
                        "topic": self.topic,
                        "participants": [agent.agent_id for agent in self.participants],
                        "timestamp": time.time()
                    },
                    importance=1.5  # Meetings are important memory items
                )
        
        # Record this in the transcript
        self.transcript.append({
            "timestamp": time.time(),
            "type": "system",
            "content": end_message.content,
            "metadata": meeting_results
        })
        
        return meeting_results
    
    async def facilitate_discussion(self, max_rounds: int = 5) -> Dict[str, Any]:
        """
        Facilitate a full discussion between participants, managing turns and topics
        
        Args:
            max_rounds: Maximum number of discussion rounds
            
        Returns:
            Meeting results including decisions and consensus
        """
        await self.start_meeting()
        
        # Initial introductions
        for participant in self.participants:
            intro_message = Message(
                sender="meeting_system",
                recipients=[participant.agent_id],
                context_tags=["#meeting", "#introduction"],
                message_type="meeting_prompt",
                content=f"Please introduce yourself and your perspective on the topic: {self.topic}",
                thread_id=self.meeting_id
            )
            
            response = await participant.receive_message(intro_message)
            await self._broadcast_message(response)
        
        # Main discussion rounds
        skeptic_agents = [agent for agent in self.participants if "skeptic" in agent.agent_id or "critic" in agent.agent_id]
        regular_agents = [agent for agent in self.participants if agent not in skeptic_agents]
        
        for round_num in range(max_rounds):
            # Skip rounds if we've reached consensus
            if self.consensus.get("reached", False):
                break
                
            # Skeptics challenge regular agents
            if skeptic_agents:
                for skeptic in skeptic_agents:
                    challenge_message = Message(
                        sender="meeting_system",
                        recipients=[skeptic.agent_id],
                        context_tags=["#meeting", "#challenge"],
                        message_type="meeting_prompt",
                        content=f"Please challenge the current approach or implementation regarding: {self.topic}. What concerns or improvements do you see?",
                        thread_id=self.meeting_id
                    )
                    
                    challenge_response = await skeptic.receive_message(challenge_message)
                    await self._broadcast_message(challenge_response)
                    
                    # Let regular agents respond to challenges
                    for regular in regular_agents:
                        response_message = Message(
                            sender="meeting_system",
                            recipients=[regular.agent_id],
                            context_tags=["#meeting", "#response"],
                            message_type="meeting_prompt",
                            content=f"How would you respond to the concerns raised by {skeptic.agent_id}? Do you agree with any points?",
                            thread_id=self.meeting_id
                        )
                        
                        regular_response = await regular.receive_message(response_message)
                        await self._broadcast_message(regular_response)
            
            # Check for consensus after each round
            await self._check_consensus(round_num)
        
        # Final statements and meeting summary
        for participant in self.participants:
            final_message = Message(
                sender="meeting_system",
                recipients=[participant.agent_id],
                context_tags=["#meeting", "#final_statement"],
                message_type="meeting_prompt",
                content=f"Please provide your final thoughts on this discussion and any changes you would make based on it.",
                thread_id=self.meeting_id
            )
            
            response = await participant.receive_message(final_message)
            await self._broadcast_message(response)
        
        # End the meeting and return results
        return await self.end_meeting()
    
    async def _broadcast_message(self, message: Message) -> None:
        """
        Broadcast a message to all participants except the sender
        
        Args:
            message: The message to broadcast
        """
        # Record in transcript
        self.transcript.append({
            "timestamp": time.time(),
            "sender": message.sender,
            "content": message.content,
            "context_tags": message.context_tags,
            "message_type": message.message_type
        })
        
        # Send to all participants except the sender
        for participant in self.participants:
            if participant.agent_id != message.sender:
                # Create a copy with the participant as the recipient
                broadcast_message = Message(
                    sender=message.sender,
                    recipients=[participant.agent_id],
                    context_tags=message.context_tags,
                    message_type=message.message_type,
                    content=message.content,
                    thread_id=message.thread_id,
                    metadata=message.metadata
                )
                
                await participant.receive_message(broadcast_message)
    
    async def _check_consensus(self, round_num: int) -> bool:
        """
        Check if the participants have reached consensus
        
        Args:
            round_num: The current discussion round
            
        Returns:
            True if consensus has been reached, False otherwise
        """
        # First, identify the skeptic and regular agents
        skeptic_agents = [agent for agent in self.participants if "skeptic" in agent.agent_id or "critic" in agent.agent_id]
        regular_agents = [agent for agent in self.participants if agent not in skeptic_agents]
        
        # If no skeptics or no regular agents, we can't reach consensus
        if not skeptic_agents or not regular_agents:
            return False
        
        # Ask all participants about consensus
        consensus_votes = {}
        consensus_statements = {}
        
        for participant in self.participants:
            consensus_message = Message(
                sender="meeting_system",
                recipients=[participant.agent_id],
                context_tags=["#meeting", "#consensus_check"],
                message_type="consensus_request",
                content=f"Have we reached consensus on changes needed for {self.topic}? Answer YES or NO, followed by a brief explanation.",
                thread_id=self.meeting_id
            )
            
            response = await participant.receive_message(consensus_message)
            
            # Parse the response to determine if consensus is reached
            consensus_votes[participant.agent_id] = "YES" in response.content.upper().split()[0]
            consensus_statements[participant.agent_id] = response.content
        
        # For a 1:1 meeting, both agents must agree
        if len(self.participants) == 2:
            consensus_reached = all(consensus_votes.values())
        # For a 1:2 meeting, the skeptic and at least one regular agent must agree
        elif len(skeptic_agents) == 1 and len(regular_agents) == 2:
            skeptic_id = skeptic_agents[0].agent_id
            skeptic_agrees = consensus_votes.get(skeptic_id, False)
            # Count how many regular agents agree
            regular_agreements = sum(1 for agent in regular_agents if consensus_votes.get(agent.agent_id, False))
            consensus_reached = skeptic_agrees and regular_agreements >= 1
        else:
            # For other meetings, majority rules
            consensus_reached = sum(consensus_votes.values()) > len(consensus_votes) / 2
        
        # Store consensus information
        self.consensus = {
            "reached": consensus_reached,
            "round": round_num,
            "votes": consensus_votes,
            "statements": consensus_statements
        }
        
        # If consensus is reached, capture the decisions
        if consensus_reached:
            # Ask the skeptic agent to summarize the agreed changes
            for skeptic in skeptic_agents:
                summary_message = Message(
                    sender="meeting_system",
                    recipients=[skeptic.agent_id],
                    context_tags=["#meeting", "#decision_summary"],
                    message_type="meeting_prompt",
                    content=f"Please summarize the specific changes that were agreed upon for {self.topic}.",
                    thread_id=self.meeting_id
                )
                
                summary_response = await skeptic.receive_message(summary_message)
                
                # Record as a decision
                self.decisions.append({
                    "timestamp": time.time(),
                    "topic": self.topic,
                    "decision": summary_response.content,
                    "proposed_by": skeptic.agent_id
                })
                
                # Broadcast the decision to all participants
                await self._broadcast_message(summary_response)
        
        return consensus_reached
        
    def _generate_summary(self) -> str:
        """
        Generate a summary of the meeting from the transcript
        
        Returns:
            A summary string
        """
        # In a real implementation, this would use an LLM to summarize the meeting
        # For now, just create a simple summary
        
        num_messages = len(self.transcript)
        num_decisions = len(self.decisions)
        num_action_items = len(self.action_items)
        consensus_reached = self.consensus.get("reached", False)
        
        summary = (
            f"Meeting on '{self.topic}' with {len(self.participants)} participants. "
            f"The discussion had {num_messages} exchanges and resulted in "
            f"{num_decisions} decisions and {num_action_items} action items. "
        )
        
        if consensus_reached:
            summary += "Consensus was reached on the necessary changes."
        else:
            summary += "No consensus was reached."
            
        # Add the decisions if any
        if self.decisions:
            summary += "\n\nKey decisions:"
            for i, decision in enumerate(self.decisions, 1):
                summary += f"\n{i}. {decision['decision']}"
                
        return summary


class CollaborationManager:
    """
    Manages collaborative interactions between agents, particularly focusing on meetings
    between regular agents and skeptic agents, and implementing the results.
    """
    
    def __init__(self, prompt_engineer_agent: Optional[BaseAgent] = None):
        """
        Initialize the collaboration manager
        
        Args:
            prompt_engineer_agent: The prompt engineer agent to use for implementing agreed changes
        """
        self.prompt_engineer_agent = prompt_engineer_agent
        self.meetings: Dict[str, MeetingProtocol] = {}
        self.architecture_embedding: Optional[Any] = None  # Holds the project architecture embedding
    
    def create_meeting(self, 
                      topic: str, 
                      description: str,
                      skeptic_agent: BaseAgent,
                      regular_agents: List[BaseAgent],
                      facilitator: Optional[BaseAgent] = None) -> MeetingProtocol:
        """
        Create a new meeting between a skeptic agent and regular agents
        
        Args:
            topic: The topic of the meeting
            description: A description of the meeting purpose
            skeptic_agent: The skeptic agent that will challenge ideas
            regular_agents: The regular agents that will respond to challenges
            facilitator: Optional facilitator agent (e.g., a Manager)
            
        Returns:
            The created meeting protocol
        """
        meeting = MeetingProtocol(
            topic=topic,
            description=description,
            facilitator=facilitator
        )
        
        # Add the participants
        meeting.add_participant(skeptic_agent)
        for agent in regular_agents:
            meeting.add_participant(agent)
            
        # Store the meeting
        self.meetings[meeting.meeting_id] = meeting
        
        return meeting
    
    async def run_one_on_one_meeting(self, 
                                    skeptic_agent: BaseAgent, 
                                    regular_agent: BaseAgent,
                                    topic: str, 
                                    description: str,
                                    max_rounds: int = 5) -> Dict[str, Any]:
        """
        Run a 1:1 meeting between a skeptic agent and a regular agent
        
        Args:
            skeptic_agent: The skeptic agent
            regular_agent: The regular agent
            topic: The topic of the meeting
            description: A description of the meeting purpose
            max_rounds: Maximum number of discussion rounds
            
        Returns:
            Meeting results including decisions and consensus
        """
        meeting = self.create_meeting(
            topic=topic,
            description=description,
            skeptic_agent=skeptic_agent,
            regular_agents=[regular_agent]
        )
        
        # Run the meeting
        results = await meeting.facilitate_discussion(max_rounds=max_rounds)
        
        # Check if implementation changes are needed
        if results["consensus"]["reached"]:
            # If consensus was reached, there should be decisions
            if results["decisions"]:
                # Implement the changes using the prompt engineer agent if available
                if self.prompt_engineer_agent:
                    await self._implement_changes(
                        decisions=results["decisions"],
                        agents=[regular_agent],
                        meeting_id=meeting.meeting_id
                    )
        
        return results
    
    async def run_one_on_two_meeting(self, 
                                    skeptic_agent: BaseAgent, 
                                    regular_agents: List[BaseAgent],
                                    topic: str, 
                                    description: str,
                                    max_rounds: int = 5) -> Dict[str, Any]:
        """
        Run a 1:2 meeting between a skeptic agent and two regular agents
        
        Args:
            skeptic_agent: The skeptic agent
            regular_agents: Two regular agents (should be of the same domain)
            topic: The topic of the meeting
            description: A description of the meeting purpose
            max_rounds: Maximum number of discussion rounds
            
        Returns:
            Meeting results including decisions and consensus
        """
        if len(regular_agents) != 2:
            raise ValueError("One-on-two meetings require exactly two regular agents")
            
        meeting = self.create_meeting(
            topic=topic,
            description=description,
            skeptic_agent=skeptic_agent,
            regular_agents=regular_agents
        )
        
        # Run the meeting
        results = await meeting.facilitate_discussion(max_rounds=max_rounds)
        
        # Check if implementation changes are needed
        if results["consensus"]["reached"]:
            # If consensus was reached, there should be decisions
            if results["decisions"]:
                # Implement the changes using the prompt engineer agent if available
                if self.prompt_engineer_agent:
                    await self._implement_changes(
                        decisions=results["decisions"],
                        agents=regular_agents,
                        meeting_id=meeting.meeting_id
                    )
        
        return results
    
    async def get_meeting_results(self, meeting_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the results of a meeting
        
        Args:
            meeting_id: The meeting ID
            
        Returns:
            Meeting results or None if the meeting doesn't exist
        """
        meeting = self.meetings.get(meeting_id)
        if not meeting:
            return None
            
        if meeting.status == "completed":
            return {
                "meeting_id": meeting.meeting_id,
                "topic": meeting.topic,
                "description": meeting.description,
                "participants": [agent.agent_id for agent in meeting.participants],
                "start_time": meeting.start_time,
                "end_time": meeting.end_time,
                "duration_minutes": round((meeting.end_time - meeting.start_time) / 60, 2) if meeting.start_time and meeting.end_time else 0,
                "decisions": meeting.decisions,
                "action_items": meeting.action_items,
                "consensus": meeting.consensus,
                "status": meeting.status
            }
        else:
            return {
                "meeting_id": meeting.meeting_id,
                "topic": meeting.topic,
                "description": meeting.description,
                "participants": [agent.agent_id for agent in meeting.participants],
                "status": meeting.status
            }
    
    async def _implement_changes(self, 
                               decisions: List[Dict[str, Any]], 
                               agents: List[BaseAgent],
                               meeting_id: str) -> bool:
        """
        Implement changes agreed upon in a meeting using the prompt engineer
        
        Args:
            decisions: The decisions from the meeting
            agents: The agents that need updated prompts
            meeting_id: The meeting ID
            
        Returns:
            True if changes were implemented, False otherwise
        """
        if not self.prompt_engineer_agent:
            return False
            
        # For each agent that needs updates
        for agent in agents:
            # Compile the requirements for the new prompt
            requirements = []
            for decision in decisions:
                requirements.append(decision["decision"])
                
            # Create a prompt creation request
            prompt_request = {
                "agent_type": agent.agent_id,
                "task_type": "general",  # Could be more specific based on the agent's role
                "context": {
                    "meeting_id": meeting_id,
                    "decisions": [d["decision"] for d in decisions]
                },
                "requirements": requirements,
                "agent_personality": {
                    "description": f"Enhanced {agent.agent_id} with improvements from {meeting_id}"
                }
            }
            
            # Format the request as a message
            create_prompt_message = Message(
                sender="collaboration_manager",
                recipients=[self.prompt_engineer_agent.agent_id],
                context_tags=["#prompt_engineering", "#meeting_implementation"],
                message_type="create_prompt",
                content=json.dumps(prompt_request),
                thread_id=meeting_id
            )
            
            # Send to the prompt engineer agent
            response = await self.prompt_engineer_agent.receive_message(create_prompt_message)
            
            # Parse the response to get the new prompt
            try:
                response_data = json.loads(response.content)
                new_prompt = response_data.get("created_prompt", "")
                
                if new_prompt:
                    # Apply the new prompt to the agent
                    # This would depend on the specific agent implementation
                    # For now, we'll just notify the agent about the new prompt
                    update_message = Message(
                        sender="collaboration_manager",
                        recipients=[agent.agent_id],
                        context_tags=["#prompt_update", "#meeting_implementation"],
                        message_type="prompt_update",
                        content=f"Your prompt has been updated based on the meeting {meeting_id}. New prompt: {new_prompt[:100]}...",
                        thread_id=meeting_id,
                        metadata={
                            "meeting_id": meeting_id,
                            "new_prompt": new_prompt,
                            "decisions": [d["decision"] for d in decisions]
                        }
                    )
                    
                    await agent.receive_message(update_message)
            except (json.JSONDecodeError, AttributeError):
                # If we couldn't parse the response, continue to the next agent
                continue
                
        return True
    
    async def set_architecture_embedding(self, embedding: Any) -> None:
        """
        Set the project architecture embedding for all agents
        
        Args:
            embedding: The architecture embedding vector
        """
        self.architecture_embedding = embedding
        
        # Store the architecture embedding in each agent's memory
        for meeting in self.meetings.values():
            for agent in meeting.participants:
                if hasattr(agent, 'memory') and agent.memory:
                    await agent.memory.add_memory(
                        content="Project architecture embedding",
                        metadata={
                            "type": "architecture_embedding",
                            "timestamp": time.time()
                        },
                        embedding=embedding,
                        importance=2.0  # Architecture understanding is very important
                    )
                    
    async def get_agent_meetings(self, agent_id: str) -> List[str]:
        """
        Get all meetings that an agent has participated in
        
        Args:
            agent_id: The agent ID
            
        Returns:
            List of meeting IDs
        """
        meeting_ids = []
        for meeting_id, meeting in self.meetings.items():
            participant_ids = [agent.agent_id for agent in meeting.participants]
            if agent_id in participant_ids:
                meeting_ids.append(meeting_id)
                
        return meeting_ids 