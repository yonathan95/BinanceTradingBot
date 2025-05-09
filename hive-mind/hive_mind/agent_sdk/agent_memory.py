"""
Agent Memory System - Provides long-term memory storage for agents using vector embeddings.
"""
from typing import List, Dict, Any, Optional, Tuple
import uuid
import time
import numpy as np
from pydantic import BaseModel
import asyncio
import logging
import math

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MemoryEntry(BaseModel):
    """Represents a single memory entry in the agent's memory."""
    id: str
    content: str
    metadata: Dict[str, Any]
    embedding: Optional[List[float]] = None
    created_at: float
    importance: float = 1.0  # Scale from 0.0 to 5.0, with 5.0 being most important
    last_accessed: Optional[float] = None
    access_count: int = 0
    decay_rate: float = 0.05  # Decay rate per day
    shared_from: Optional[str] = None  # ID of agent that shared this memory
    shared_with: List[str] = []  # List of agent IDs this memory has been shared with
    
    def __init__(self, **data):
        if 'id' not in data:
            data['id'] = str(uuid.uuid4())
        if 'created_at' not in data:
            data['created_at'] = time.time()
        super().__init__(**data)
    
    def get_current_importance(self) -> float:
        """
        Calculate the current importance of the memory, factoring in decay over time.
        
        Returns:
            Current importance value
        """
        if self.decay_rate <= 0:
            return self.importance
        
        now = time.time()
        days_passed = (now - self.created_at) / (24 * 3600)
        
        # Apply decay formula: importance * exp(-decay_rate * days)
        decayed_importance = self.importance * math.exp(-self.decay_rate * days_passed)
        
        # If memory was accessed recently, boost its importance
        if self.last_accessed:
            days_since_access = (now - self.last_accessed) / (24 * 3600)
            if days_since_access < 1.0:  # Accessed within the last day
                recency_boost = 0.5 * (1.0 - days_since_access)
                decayed_importance += recency_boost
        
        # Apply boost based on access count
        if self.access_count > 0:
            access_boost = min(0.5, 0.1 * math.log(1 + self.access_count))
            decayed_importance += access_boost
        
        # Ensure importance stays within valid range
        return max(0.0, min(5.0, decayed_importance))

class AgentMemory:
    """
    Manages long-term memory for agents using vector embeddings.
    Allows agents to store, retrieve, and search past information.
    """
    
    def __init__(self, 
                embedding_model: str = "text-embedding-ada-002",
                vector_db_url: Optional[str] = None,
                local_mode: bool = True,
                agent_id: Optional[str] = None):
        """
        Initialize the Agent Memory system.
        
        Args:
            embedding_model: The model to use for creating embeddings
            vector_db_url: URL for the vector database (if None, use mock in-memory storage)
            local_mode: If True, use in-memory storage instead of external vector database
            agent_id: ID of the agent owning this memory system
        """
        self.embedding_model = embedding_model
        self.vector_db_url = vector_db_url
        self.local_mode = local_mode
        self.agent_id = agent_id
        self.memories: Dict[str, MemoryEntry] = {}
        self.embeddings: Dict[str, List[float]] = {}
        self.shared_with_others: Dict[str, List[str]] = {}  # Memory ID -> Agent IDs
        self.received_from_others: Dict[str, str] = {}  # Memory ID -> Source Agent ID
        
        # Import optimization is used to allow optional dependencies
        if not local_mode and vector_db_url:
            try:
                import qdrant_client
                self.qdrant = qdrant_client.QdrantClient(url=vector_db_url)
                logger.info(f"Connected to Qdrant at {vector_db_url}")
            except ImportError:
                logger.warning("Qdrant client not installed. Falling back to local mode.")
                self.local_mode = True
        
    async def create_embedding(self, text: str) -> List[float]:
        """
        Create an embedding vector for the provided text.
        
        Args:
            text: The text to embed
            
        Returns:
            Embedding vector as a list of floats
        """
        # This would be replaced with actual embedding API call
        # For example: response = await openai.embeddings.create(...)
        # Mock implementation for now
        if self.local_mode:
            # Create a deterministic mock embedding based on text content
            # This is just for development/testing purposes
            import hashlib
            hash_val = hashlib.md5(text.encode()).hexdigest()
            # Convert hash to a list of 1536 float values between -1 and 1
            embedding = []
            for i in range(0, len(hash_val), 2):
                if i < len(hash_val) - 1:
                    val = int(hash_val[i:i+2], 16)
                    embedding.append((val / 255.0) * 2 - 1)
            
            # Pad embedding to 1536 dimensions
            while len(embedding) < 1536:
                embedding.extend(embedding[:1536 - len(embedding)])
            
            embedding = embedding[:1536]  # Make sure it's exactly 1536 dimensions
            return embedding
        else:
            # This would be the real implementation using OpenAI or other embedding provider
            # Implement actual API call to get embeddings
            # For now, return mock data
            return [0.0] * 1536
    
    def cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        vec1 = np.array(vec1)
        vec2 = np.array(vec2)
        return np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))
    
    async def add_memory(self, content: str, metadata: Dict[str, Any] = None, 
                   importance: float = 1.0, decay_rate: float = 0.05) -> str:
        """
        Add a new memory to the agent's memory store.
        
        Args:
            content: The text content to remember
            metadata: Additional metadata about the memory
            importance: Importance score from 0.0 to 5.0
            decay_rate: Rate at which memory importance decays per day
            
        Returns:
            ID of the created memory
        """
        if metadata is None:
            metadata = {}
            
        embedding = await self.create_embedding(content)
        
        memory_entry = MemoryEntry(
            content=content,
            metadata=metadata,
            embedding=embedding,
            importance=importance,
            decay_rate=decay_rate
        )
        
        if self.local_mode:
            self.memories[memory_entry.id] = memory_entry
            self.embeddings[memory_entry.id] = embedding
        else:
            # This would store the memory in Qdrant
            # Implement actual vector DB storage
            pass
            
        return memory_entry.id
    
    async def retrieve_memory(self, memory_id: str) -> Optional[MemoryEntry]:
        """
        Retrieve a specific memory by ID.
        
        Args:
            memory_id: The ID of the memory to retrieve
            
        Returns:
            The memory entry if found, otherwise None
        """
        if self.local_mode:
            memory = self.memories.get(memory_id)
            if memory:
                # Update access stats
                memory.last_accessed = time.time()
                memory.access_count += 1
                return memory
            return None
        else:
            # This would retrieve the memory from Qdrant
            # Implement actual vector DB retrieval
            pass
    
    async def search_memory(self, query: str, limit: int = 5, 
                      min_similarity: float = 0.7,
                      include_decayed: bool = True) -> List[Tuple[MemoryEntry, float]]:
        """
        Search for memories similar to the given query.
        
        Args:
            query: The search query
            limit: Maximum number of results to return
            min_similarity: Minimum similarity score to include in results
            include_decayed: Whether to include memories that have decayed below threshold
            
        Returns:
            List of (memory, similarity_score) tuples
        """
        query_embedding = await self.create_embedding(query)
        
        if self.local_mode:
            results = []
            for memory_id, memory in self.memories.items():
                if memory.embedding:
                    similarity = self.cosine_similarity(query_embedding, memory.embedding)
                    
                    # Check importance threshold if we're excluding decayed memories
                    if not include_decayed:
                        current_importance = memory.get_current_importance()
                        if current_importance < 0.5:  # Skip low importance memories
                            continue
                    
                    if similarity >= min_similarity:
                        results.append((memory, similarity))
                        
            # Sort by combination of similarity and current importance
            results.sort(key=lambda x: (x[1] * 0.7) + (x[0].get_current_importance() / 5.0 * 0.3), reverse=True)
            
            # Update access stats for retrieved memories
            for memory, _ in results[:limit]:
                memory.last_accessed = time.time()
                memory.access_count += 1
                
            return results[:limit]
        else:
            # This would search the vector DB
            # Implement actual vector DB search
            return []
    
    async def update_memory(self, memory_id: str, 
                      content: Optional[str] = None,
                      metadata: Optional[Dict[str, Any]] = None, 
                      importance: Optional[float] = None,
                      decay_rate: Optional[float] = None) -> bool:
        """
        Update an existing memory.
        
        Args:
            memory_id: ID of the memory to update
            content: New content (if updating)
            metadata: New or updated metadata (if updating)
            importance: New importance score (if updating)
            decay_rate: New decay rate (if updating)
            
        Returns:
            True if update was successful, False otherwise
        """
        memory = await self.retrieve_memory(memory_id)
        if not memory:
            return False
            
        updated = False
        
        if content is not None and content != memory.content:
            memory.content = content
            memory.embedding = await self.create_embedding(content)
            updated = True
            
        if metadata is not None:
            memory.metadata.update(metadata)
            updated = True
            
        if importance is not None:
            memory.importance = importance
            updated = True
            
        if decay_rate is not None:
            memory.decay_rate = decay_rate
            updated = True
            
        if updated and not self.local_mode:
            # This would update the vector DB
            # Implement actual vector DB update
            pass
            
        return updated
    
    async def delete_memory(self, memory_id: str) -> bool:
        """
        Delete a memory.
        
        Args:
            memory_id: ID of the memory to delete
            
        Returns:
            True if deletion was successful, False otherwise
        """
        if self.local_mode:
            if memory_id in self.memories:
                del self.memories[memory_id]
                if memory_id in self.embeddings:
                    del self.embeddings[memory_id]
                return True
            return False
        else:
            # This would delete from the vector DB
            # Implement actual vector DB deletion
            pass
    
    async def get_semantic_context(self, query: str, 
                             max_entries: int = 10, 
                             importance_threshold: float = 0.0,
                             include_decayed: bool = True) -> List[str]:
        """
        Get relevant context based on semantic similarity to the query.
        
        Args:
            query: The context query
            max_entries: Maximum number of context entries to include
            importance_threshold: Minimum importance score to include
            include_decayed: Whether to include memories that have decayed below threshold
            
        Returns:
            List of relevant context strings
        """
        memories = await self.search_memory(query, limit=max_entries, include_decayed=include_decayed)
        
        # Filter based on importance and sort by combination of similarity and importance
        filtered_memories = [
            (memory, score) for memory, score in memories 
            if memory.get_current_importance() >= importance_threshold
        ]
        
        # Extract just the content for the final result
        return [memory.content for memory, _ in filtered_memories]
    
    async def calculate_memory_importance(self, memory_id: str, 
                                    query_relevance: float = 0.0,
                                    recency_boost: bool = True) -> float:
        """
        Calculate and update the importance of a memory based on various factors.
        
        Args:
            memory_id: ID of the memory to evaluate
            query_relevance: Relevance score from a recent query (0.0 to 1.0)
            recency_boost: Whether to boost importance based on recency
            
        Returns:
            Updated importance score
        """
        memory = await self.retrieve_memory(memory_id)
        if not memory:
            return 0.0
            
        # Start with base importance
        new_importance = memory.importance
        
        # Add query relevance factor
        if query_relevance > 0:
            new_importance += query_relevance
            
        # Add recency boost if enabled
        if recency_boost and memory.last_accessed:
            now = time.time()
            days_since_access = (now - memory.last_accessed) / (24 * 3600)
            if days_since_access < 1.0:  # Accessed within the last day
                recency_factor = 0.5 * (1.0 - days_since_access)
                new_importance += recency_factor
        
        # Add boost based on access count
        if memory.access_count > 0:
            access_boost = min(0.5, 0.1 * math.log(1 + memory.access_count))
            new_importance += access_boost
        
        # Ensure importance stays within valid range
        new_importance = max(0.0, min(5.0, new_importance))
        
        # Update the memory's importance
        memory.importance = new_importance
        
        return new_importance
    
    async def apply_memory_decay(self):
        """
        Apply decay to all memories based on their decay rates and time elapsed.
        This is typically called periodically to update memory importance.
        """
        now = time.time()
        updated_count = 0
        
        for memory_id, memory in self.memories.items():
            if memory.decay_rate <= 0:
                continue
                
            # Calculate days passed since creation
            days_passed = (now - memory.created_at) / (24 * 3600)
            
            # Apply decay formula: importance * exp(-decay_rate * days)
            original_importance = memory.importance
            decayed_importance = original_importance * math.exp(-memory.decay_rate * days_passed)
            
            # Ensure importance stays within valid range
            decayed_importance = max(0.0, min(5.0, decayed_importance))
            
            # Update if changed significantly
            if abs(decayed_importance - original_importance) > 0.1:
                memory.importance = decayed_importance
                updated_count += 1
        
        logger.info(f"Applied decay to {updated_count} memories")
        return updated_count
    
    async def share_memory(self, memory_id: str, recipient_agent_id: str) -> bool:
        """
        Share a memory with another agent.
        
        Args:
            memory_id: ID of the memory to share
            recipient_agent_id: ID of the agent to share with
            
        Returns:
            True if share was successful, False otherwise
        """
        memory = await self.retrieve_memory(memory_id)
        if not memory:
            return False
            
        # Track that we've shared this memory
        if memory_id not in self.shared_with_others:
            self.shared_with_others[memory_id] = []
            
        if recipient_agent_id not in self.shared_with_others[memory_id]:
            self.shared_with_others[memory_id].append(recipient_agent_id)
            
        # Add to memory's shared_with list
        if recipient_agent_id not in memory.shared_with:
            memory.shared_with.append(recipient_agent_id)
            
        return True
    
    async def receive_shared_memory(self, memory_data: Dict[str, Any], source_agent_id: str) -> str:
        """
        Receive a memory shared by another agent.
        
        Args:
            memory_data: Dictionary representation of the shared memory
            source_agent_id: ID of the agent that shared the memory
            
        Returns:
            ID of the imported memory
        """
        # Update the memory data to reflect it was shared
        memory_data["shared_from"] = source_agent_id
        
        # Create a new memory entry
        memory = MemoryEntry(**memory_data)
        
        # Store in this agent's memory
        self.memories[memory.id] = memory
        if memory.embedding:
            self.embeddings[memory.id] = memory.embedding
            
        # Track that this was received from another agent
        self.received_from_others[memory.id] = source_agent_id
        
        return memory.id
    
    async def get_shared_memories(self, with_agent_id: Optional[str] = None) -> List[MemoryEntry]:
        """
        Get memories that have been shared with others.
        
        Args:
            with_agent_id: If provided, only return memories shared with this agent
            
        Returns:
            List of shared memory entries
        """
        shared_memories = []
        
        for memory_id, agents in self.shared_with_others.items():
            if memory_id in self.memories:
                if with_agent_id is None or with_agent_id in agents:
                    shared_memories.append(self.memories[memory_id])
        
        return shared_memories
    
    async def get_received_memories(self, from_agent_id: Optional[str] = None) -> List[MemoryEntry]:
        """
        Get memories that have been received from others.
        
        Args:
            from_agent_id: If provided, only return memories from this agent
            
        Returns:
            List of received memory entries
        """
        received_memories = []
        
        for memory_id, source_agent in self.received_from_others.items():
            if memory_id in self.memories:
                if from_agent_id is None or from_agent_id == source_agent:
                    received_memories.append(self.memories[memory_id])
        
        return received_memories
    
    async def get_memory_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the agent's memory.
        
        Returns:
            Dictionary with memory statistics
        """
        if not self.memories:
            return {
                "total_memories": 0,
                "shared_memories": 0,
                "received_memories": 0,
                "avg_importance": 0.0,
                "high_importance_count": 0,
                "decayed_count": 0
            }
            
        now = time.time()
        high_importance = 0
        decayed_count = 0
        importance_sum = 0.0
        
        for memory in self.memories.values():
            current_importance = memory.get_current_importance()
            importance_sum += current_importance
            
            if current_importance >= 4.0:
                high_importance += 1
                
            if current_importance < 0.5:
                decayed_count += 1
        
        return {
            "total_memories": len(self.memories),
            "shared_memories": len(self.shared_with_others),
            "received_memories": len(self.received_from_others),
            "avg_importance": importance_sum / len(self.memories),
            "high_importance_count": high_importance,
            "decayed_count": decayed_count
        } 