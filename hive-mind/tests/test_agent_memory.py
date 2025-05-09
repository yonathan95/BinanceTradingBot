"""
Unit tests for the Agent Memory System
"""

import asyncio
import unittest
import time
import math
from unittest.mock import patch

from hive_mind.agent_sdk.agent_memory import AgentMemory, MemoryEntry


class TestAgentMemory(unittest.IsolatedAsyncioTestCase):
    """Test cases for the Agent Memory System"""
    
    async def asyncSetUp(self):
        """Set up the test environment"""
        self.memory = AgentMemory(
            embedding_model="text-embedding-ada-002",
            local_mode=True,
            agent_id="test_agent"
        )
    
    async def test_add_and_retrieve_memory(self):
        """Test adding and retrieving a memory"""
        memory_id = await self.memory.add_memory(
            content="The API key for the database service is DB_API_12345",
            metadata={"source": "configuration", "service": "database"},
            importance=4.0,
            decay_rate=0.05
        )
        
        self.assertIsNotNone(memory_id)
        
        # Retrieve the memory
        memory = await self.memory.retrieve_memory(memory_id)
        
        self.assertIsNotNone(memory)
        self.assertEqual(memory.content, "The API key for the database service is DB_API_12345")
        self.assertEqual(memory.metadata["source"], "configuration")
        self.assertEqual(memory.metadata["service"], "database")
        self.assertEqual(memory.importance, 4.0)
        self.assertEqual(memory.decay_rate, 0.05)
        self.assertEqual(memory.access_count, 1)  # First access during retrieval
    
    async def test_search_memory(self):
        """Test searching for memories"""
        # Add multiple memories
        await self.memory.add_memory(
            content="The frontend uses React with Material UI",
            metadata={"topic": "frontend"},
            importance=3.0
        )
        
        await self.memory.add_memory(
            content="The backend is built with FastAPI and PostgreSQL",
            metadata={"topic": "backend"},
            importance=3.5
        )
        
        await self.memory.add_memory(
            content="The database password is 'secure_password123'",
            metadata={"topic": "database", "sensitive": True},
            importance=5.0
        )
        
        # Search for memories
        results = await self.memory.search_memory(
            query="What database do we use?",
            limit=2,
            min_similarity=0.0  # Low threshold for testing
        )
        
        self.assertTrue(len(results) > 0)
        
        # Results should be sorted by combination of similarity and importance
        for memory, similarity in results:
            self.assertIsInstance(memory, MemoryEntry)
            self.assertGreaterEqual(similarity, 0.0)
    
    async def test_memory_decay(self):
        """Test memory decay mechanism"""
        # Add a memory with high decay rate
        memory_id = await self.memory.add_memory(
            content="Temporary information that should decay quickly",
            metadata={"temporary": True},
            importance=3.0,
            decay_rate=0.5  # High decay rate
        )
        
        # Get the memory
        memory = await self.memory.retrieve_memory(memory_id)
        original_importance = memory.importance
        
        # Simulate time passing (mocking the time calculation)
        with patch.object(memory, 'created_at', return_value=time.time() - 5 * 24 * 3600):
            # Get current importance after 5 days
            current_importance = memory.get_current_importance()
            
            # Verify it has decayed
            self.assertLess(current_importance, original_importance)
            
            # Verify decay formula is working correctly
            expected_decay = original_importance * math.exp(-0.5 * 5)
            self.assertAlmostEqual(current_importance, expected_decay, delta=1.0)
        
        # Apply decay to all memories
        updated_count = await self.memory.apply_memory_decay()
        self.assertGreaterEqual(updated_count, 0)
    
    async def test_memory_importance_scoring(self):
        """Test memory importance scoring mechanism"""
        memory_id = await self.memory.add_memory(
            content="Important information that should be scored",
            metadata={"critical": True},
            importance=2.0
        )
        
        # Update importance based on various factors
        new_importance = await self.memory.calculate_memory_importance(
            memory_id=memory_id,
            query_relevance=0.8,  # High relevance to recent query
            recency_boost=True    # Apply recency boost
        )
        
        # Verify importance increased
        self.assertGreater(new_importance, 2.0)
        
        # Retrieve memory and check its updated importance
        memory = await self.memory.retrieve_memory(memory_id)
        self.assertEqual(memory.importance, new_importance)
    
    async def test_memory_sharing(self):
        """Test cross-agent memory sharing"""
        # Add a memory to share
        memory_id = await self.memory.add_memory(
            content="Shared information between agents",
            metadata={"shareable": True},
            importance=3.5
        )
        
        # Share with another agent
        other_agent_id = "other_agent"
        success = await self.memory.share_memory(memory_id, other_agent_id)
        
        self.assertTrue(success)
        
        # Get shared memories
        shared_memories = await self.memory.get_shared_memories()
        self.assertEqual(len(shared_memories), 1)
        self.assertEqual(shared_memories[0].id, memory_id)
        
        # Verify it was shared with the correct agent
        shared_with_specific = await self.memory.get_shared_memories(with_agent_id=other_agent_id)
        self.assertEqual(len(shared_with_specific), 1)
        
        # Create a second agent memory system
        other_memory = AgentMemory(
            embedding_model="text-embedding-ada-002",
            local_mode=True,
            agent_id=other_agent_id
        )
        
        # Simulate receiving shared memory
        memory = await self.memory.retrieve_memory(memory_id)
        received_id = await other_memory.receive_shared_memory(
            memory_data=memory.dict(),
            source_agent_id="test_agent"
        )
        
        self.assertEqual(received_id, memory_id)
        
        # Verify it was received
        received_memories = await other_memory.get_received_memories(from_agent_id="test_agent")
        self.assertEqual(len(received_memories), 1)
        self.assertEqual(received_memories[0].id, memory_id)
        self.assertEqual(received_memories[0].shared_from, "test_agent")
    
    async def test_semantic_context(self):
        """Test retrieving semantic context"""
        # Add multiple memories
        await self.memory.add_memory(
            content="The API rate limit is 100 requests per minute",
            metadata={"topic": "api"},
            importance=3.0
        )
        
        await self.memory.add_memory(
            content="The database connection string is 'postgresql://user:pass@localhost/db'",
            metadata={"topic": "database"},
            importance=4.0
        )
        
        await self.memory.add_memory(
            content="The secret key for JWT tokens is 'jwt_secret_123'",
            metadata={"topic": "security"},
            importance=5.0
        )
        
        # Get semantic context for a query
        contexts = await self.memory.get_semantic_context(
            query="How do I connect to the database?",
            max_entries=2,
            importance_threshold=2.0
        )
        
        self.assertTrue(len(contexts) > 0)
        self.assertLessEqual(len(contexts), 2)
    
    async def test_memory_stats(self):
        """Test memory statistics generation"""
        # Add some memories
        await self.memory.add_memory(
            content="Memory 1",
            importance=1.0
        )
        
        await self.memory.add_memory(
            content="Memory 2",
            importance=3.0
        )
        
        await self.memory.add_memory(
            content="Memory 3",
            importance=5.0
        )
        
        # Get memory stats
        stats = await self.memory.get_memory_stats()
        
        self.assertEqual(stats["total_memories"], 3)
        self.assertGreaterEqual(stats["high_importance_count"], 1)  # Memory 3 has importance 5.0
        self.assertGreaterEqual(stats["avg_importance"], 1.0)
        

if __name__ == '__main__':
    unittest.main() 