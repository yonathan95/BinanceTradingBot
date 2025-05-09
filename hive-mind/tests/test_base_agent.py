import pytest
import asyncio
from hive_mind.agent_sdk.base_agent import BaseAgent, Message, AgentTool
from typing import Dict, Any, List

# Create a simple concrete implementation of BaseAgent for testing
class TestAgent(BaseAgent):
    """Test implementation of BaseAgent for unit testing"""
    
    def __init__(self, agent_id: str = "test_agent"):
        super().__init__(
            agent_id=agent_id,
            model="gpt-3.5-turbo",
            temperature=0.7,
            token_limit=2048
        )
        self.processed_messages = []
    
    async def process_message(self, message: Message) -> Message:
        """Simple implementation that just stores and echoes the message"""
        self.processed_messages.append(message)
        
        return await self.send_message(
            recipients=[message.sender],
            content=f"Received: {message.content}",
            context_tags=message.context_tags,
            message_type="response",
            thread_id=message.thread_id
        )
    
    async def generate_prompt(self, context: Dict[str, Any]) -> str:
        """Simple implementation that just returns a fixed prompt"""
        return "This is a test prompt."

# Create a simple tool implementation for testing
class EchoTool(AgentTool):
    """Test implementation of AgentTool that echoes its input"""
    
    def __init__(self):
        super().__init__(
            name="echo_tool",
            description="A tool that echoes its input",
            parameters={
                "message": "The message to echo back"
            }
        )
    
    async def execute(self, message: str) -> Dict[str, Any]:
        """Echo back the input message"""
        return {
            "success": True,
            "echo": message
        }

@pytest.mark.asyncio
async def test_message_creation():
    """Test that messages are created correctly"""
    message = Message(
        sender="user",
        recipients=["test_agent"],
        context_tags=["#test"],
        message_type="request",
        content="Hello, agent!",
        priority="high",
        requires_response=True
    )
    
    assert message.sender == "user"
    assert message.recipients == ["test_agent"]
    assert "#test" in message.context_tags
    assert message.message_type == "request"
    assert message.content == "Hello, agent!"
    assert message.priority == "high"
    assert message.requires_response is True
    assert message.thread_id is not None  # Thread ID should be auto-generated

@pytest.mark.asyncio
async def test_agent_message_handling():
    """Test that agents can receive and process messages"""
    agent = TestAgent()
    
    message = Message(
        sender="user",
        recipients=["test_agent"],
        context_tags=["#test"],
        message_type="request",
        content="Hello, agent!",
        priority="normal",
        requires_response=True
    )
    
    response = await agent.receive_message(message)
    
    assert response.sender == "test_agent"
    assert response.recipients == ["user"]
    assert response.content == "Received: Hello, agent!"
    assert response.thread_id == message.thread_id
    assert len(agent.processed_messages) == 1
    assert agent.processed_messages[0].content == "Hello, agent!"

@pytest.mark.asyncio
async def test_agent_tool_registration():
    """Test that agents can register and use tools"""
    agent = TestAgent()
    echo_tool = EchoTool()
    
    # Register the tool
    agent.add_tool(echo_tool)
    
    # Check that the tool was registered
    assert len(agent.tools) == 1
    assert agent.tools[0].name == "echo_tool"
    
    # Test using the tool
    result = await agent.tools[0].execute(message="Test message")
    
    assert result["success"] is True
    assert result["echo"] == "Test message"

@pytest.mark.asyncio
async def test_agent_llm_call():
    """Test that agents can call LLMs with retry logic"""
    agent = TestAgent()
    
    # Test the mock LLM call
    response = await agent.call_llm("This is a test prompt")
    
    assert "content" in response
    assert "token_usage" in response
    assert agent.token_count > 0

@pytest.mark.asyncio
async def test_thread_continuity():
    """Test that message threading works correctly"""
    agent = TestAgent()
    
    # Send first message in thread
    message1 = Message(
        sender="user",
        recipients=["test_agent"],
        context_tags=["#test"],
        message_type="request",
        content="First message",
        thread_id="test-thread-123"
    )
    
    response1 = await agent.receive_message(message1)
    
    # Send second message in same thread
    message2 = Message(
        sender="user",
        recipients=["test_agent"],
        context_tags=["#test"],
        message_type="request",
        content="Second message",
        thread_id="test-thread-123"
    )
    
    response2 = await agent.receive_message(message2)
    
    # Check thread continuity
    assert response1.thread_id == "test-thread-123"
    assert response2.thread_id == "test-thread-123"
    assert len(agent.processed_messages) == 2
    assert agent.processed_messages[0].thread_id == agent.processed_messages[1].thread_id 