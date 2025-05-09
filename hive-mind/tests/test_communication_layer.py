"""
Unit tests for the Inter-Team Communication Layer
"""

import asyncio
import unittest

from hive_mind.communication_layer import (
    InterTeamCommunicationLayer,
    ContextTag,
    Message,
    TeamGraph,
    ConversationSummary
)


class TestInterTeamCommunicationLayer(unittest.IsolatedAsyncioTestCase):
    """Test cases for the Inter-Team Communication Layer"""
    
    async def asyncSetUp(self):
        """Set up the test environment"""
        self.itcl = InterTeamCommunicationLayer(local_mode=True)
        await self.itcl.initialize()
        
        # Register test tags
        await self.itcl.register_context_tag(ContextTag(
            name="#frontend",
            description="Frontend development topics",
            related_tags=["#ui", "#design"]
        ))
        
        await self.itcl.register_context_tag(ContextTag(
            name="#backend",
            description="Backend development topics",
            related_tags=["#api", "#database"]
        ))
        
        await self.itcl.register_context_tag(ContextTag(
            name="#security",
            description="Security related topics",
            related_tags=["#auth", "#encryption"]
        ))
        
        # Set up team graph
        team_graph = TeamGraph(
            teams={
                "team1": {"name": "Frontend Team"},
                "team2": {"name": "Backend Team"},
                "team3": {"name": "Security Team"}
            },
            connections={
                "team1": ["team2", "team3"],
                "team2": ["team1", "team3"],
                "team3": ["team1", "team2"]
            },
            tag_routes={
                "#frontend": ["team1"],
                "#backend": ["team2"],
                "#security": ["team3"],
                "#ui": ["team1"],
                "#api": ["team2"],
                "#database": ["team2"],
                "#auth": ["team3"]
            }
        )
        await self.itcl.update_team_graph(team_graph)
    
    async def test_send_message_with_recipient(self):
        """Test sending a message with explicit recipient"""
        message = await self.itcl.send_message({
            "sender": "agent1",
            "recipients": ["team2"],
            "content": "Hello team2",
            "context_tags": ["#backend"],
            "message_type": "greeting",
            "priority": "normal",
            "requires_response": False,
            "thread_id": "test-thread-1"
        })
        
        self.assertIsNotNone(message)
        self.assertEqual(message.sender, "agent1")
        self.assertEqual(message.recipients, ["team2"])
        self.assertEqual(message.content, "Hello team2")
        self.assertEqual(message.context_tags, ["#backend"])
        
        # Verify message is stored
        stored_message = await self.itcl.get_message(message.id)
        self.assertIsNotNone(stored_message)
        self.assertEqual(stored_message.id, message.id)
    
    async def test_send_message_with_context_routing(self):
        """Test sending a message with context-based routing"""
        message = await self.itcl.send_message({
            "sender": "agent1",
            "recipients": [],  # No explicit recipients
            "content": "We need to update the authentication API",
            "context_tags": ["#auth", "#api"],
            "message_type": "task",
            "priority": "high",
            "requires_response": True,
            "thread_id": "test-thread-2"
        })
        
        self.assertIsNotNone(message)
        
        # Message should be routed to both team2 and team3 based on tags
        # In local mode, we can only check that no errors were raised
        # In real mode, we would verify delivery to both teams
    
    async def test_broadcast_message(self):
        """Test broadcasting a message to multiple teams"""
        messages = await self.itcl.broadcast_message(
            sender="manager_agent",
            content="Security update required for all services",
            tags=["#security"],
            metadata={"urgency": "high"}
        )
        
        self.assertTrue(len(messages) > 0)
        message = messages[0]
        self.assertEqual(message.sender, "manager_agent")
        self.assertEqual(message.message_type, "broadcast")
        self.assertIn("#security", message.context_tags)
    
    async def test_create_thread_summary(self):
        """Test creating a thread summary"""
        # Create multiple messages in the same thread
        thread_id = "test-thread-3"
        
        await self.itcl.send_message({
            "sender": "agent1",
            "recipients": ["team1"],
            "content": "Can we update the UI design?",
            "context_tags": ["#frontend", "#ui"],
            "message_type": "question",
            "priority": "normal",
            "requires_response": True,
            "thread_id": thread_id
        })
        
        await self.itcl.send_message({
            "sender": "team1_agent",
            "recipients": ["agent1"],
            "content": "Yes, what changes do you have in mind?",
            "context_tags": ["#frontend", "#ui"],
            "message_type": "answer",
            "priority": "normal",
            "requires_response": True,
            "thread_id": thread_id
        })
        
        await self.itcl.send_message({
            "sender": "agent1",
            "recipients": ["team1_agent"],
            "content": "Let's use a darker color scheme",
            "context_tags": ["#frontend", "#ui", "#design"],
            "message_type": "answer",
            "priority": "normal",
            "requires_response": False,
            "thread_id": thread_id
        })
        
        # Create a summary
        summary = await self.itcl.create_thread_summary(thread_id)
        
        self.assertIsNotNone(summary)
        self.assertEqual(summary.thread_id, thread_id)
        self.assertEqual(summary.message_count, 3)
        self.assertIn("agent1", summary.participants)
        self.assertIn("team1_agent", summary.participants)
        self.assertTrue(len(summary.tags) > 0)
    
    async def test_get_thread_messages(self):
        """Test retrieving all messages in a thread"""
        thread_id = "test-thread-4"
        
        # Send two messages in the thread
        await self.itcl.send_message({
            "sender": "agent1",
            "recipients": ["team2"],
            "content": "Message 1",
            "context_tags": ["#backend"],
            "message_type": "info",
            "priority": "normal",
            "requires_response": False,
            "thread_id": thread_id
        })
        
        await self.itcl.send_message({
            "sender": "agent2",
            "recipients": ["team2"],
            "content": "Message 2",
            "context_tags": ["#backend"],
            "message_type": "info",
            "priority": "normal",
            "requires_response": False,
            "thread_id": thread_id
        })
        
        # Get messages
        messages = await self.itcl.get_thread_messages(thread_id)
        
        self.assertEqual(len(messages), 2)
        self.assertEqual(messages[0].content, "Message 1")
        self.assertEqual(messages[1].content, "Message 2")
    
    async def test_forward_message(self):
        """Test forwarding a message"""
        # Create the original message
        orig_message = await self.itcl.send_message({
            "sender": "agent1",
            "recipients": ["team1"],
            "content": "Important security information",
            "context_tags": ["#security"],
            "message_type": "info",
            "priority": "high",
            "requires_response": False,
            "thread_id": "test-thread-5"
        })
        
        # Forward it
        forwarded = await self.itcl.forward_message(
            original_message_id=orig_message.id,
            new_recipients=["team3"],
            additional_context="Please review this security concern"
        )
        
        self.assertIsNotNone(forwarded)
        self.assertEqual(forwarded.message_type, "forward")
        self.assertEqual(forwarded.recipients, ["team3"])
        self.assertIn("Forwarded Message", forwarded.content)
        self.assertIn("Please review", forwarded.content)
        self.assertIn("security concern", forwarded.content)


if __name__ == '__main__':
    unittest.main() 