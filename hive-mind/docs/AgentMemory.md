# Agent Memory System

The Agent Memory System is a core component of the Hive Mind platform that provides long-term memory storage and retrieval for agents using vector embeddings.

## Overview

The Agent Memory System manages the following aspects of agent memory:

1. Storage and retrieval of information as memory entries
2. Semantic search across stored memories
3. Memory importance scoring and decay
4. Cross-agent memory sharing
5. Context-aware memory retrieval

## Key Components

### MemoryEntry

Represents a single piece of information stored in an agent's memory, with properties like:
- Content: The actual information
- Metadata: Additional context about the memory
- Importance: A score (0-5) indicating how important the memory is
- Embedding: Vector representation for semantic search
- Creation and access timestamps
- Decay rate: How quickly the memory's importance fades over time
- Sharing information: Which agents the memory has been shared with

### AgentMemory

The main class that manages memory storage, retrieval, and operations with methods for:
- Adding, updating, and deleting memories
- Searching for relevant memories
- Calculating memory importance
- Sharing memories between agents
- Applying memory decay over time

## Key Features

### Memory Decay Mechanism

Memories naturally decay in importance over time, following an exponential decay function:

```
decayed_importance = original_importance * exp(-decay_rate * days_passed)
```

This mimics the natural forgetting process. Memories that haven't been accessed recently will gradually become less important.

### Importance Scoring

Memory importance is calculated dynamically based on several factors:
- Base importance assigned at creation
- Recency of access
- Frequency of access (access count)
- Relevance to recent queries
- Explicit importance updates

### Cross-Agent Memory Sharing

Agents can share memories with each other, enabling collaborative knowledge building:
- Memories track which agents they've been shared with
- Importance scores can differ between agents for the same shared memory
- Memory decay operates independently for each agent

### Context Retrieval

The system can retrieve relevant context for a given query, considering:
- Semantic relevance
- Current importance
- Recency
- Optional filtering of decayed memories

## Usage Examples

### Basic Usage

```python
# Import the memory system
from hive_mind.agent_sdk.agent_memory import AgentMemory

# Initialize the memory system
memory = AgentMemory(agent_id="agent1")

# Add a memory
memory_id = await memory.add_memory(
    content="The API key for the database service is DB_API_12345",
    metadata={"source": "configuration", "service": "database"},
    importance=4.0,  # High importance (0-5 scale)
    decay_rate=0.02  # Slow decay
)

# Search for memories
results = await memory.search_memory(
    query="What is the database API key?",
    limit=5,
    min_similarity=0.7
)

# Get most relevant contexts
contexts = await memory.get_semantic_context(
    query="database configuration",
    max_entries=3,
    importance_threshold=1.0
)
```

### Memory Sharing

```python
# Share a memory with another agent
await memory.share_memory(memory_id, "agent2")

# Get all memories shared with others
shared_memories = await memory.get_shared_memories()

# Get memories received from specific agent
received_memories = await memory.get_received_memories(from_agent_id="agent3")
```

### Memory Management

```python
# Update memory importance
await memory.update_memory(memory_id, importance=5.0)

# Apply decay to all memories
updated_count = await memory.apply_memory_decay()

# Calculate importance with additional factors
new_importance = await memory.calculate_memory_importance(
    memory_id,
    query_relevance=0.8,
    recency_boost=True
)

# Get memory statistics
stats = await memory.get_memory_stats()
```

## Deployment

In production mode, the Agent Memory System uses a vector database (Qdrant) for:
1. Efficient vector similarity search
2. Persistent storage of memories
3. Scaling to large memory collections

## Configuration

Key configuration options:
- `embedding_model`: Model to use for creating embeddings (default: text-embedding-ada-002)
- `vector_db_url`: URL for the vector database (Qdrant)
- `local_mode`: If true, use in-memory storage instead of vector database
- `agent_id`: ID of the agent owning this memory system 