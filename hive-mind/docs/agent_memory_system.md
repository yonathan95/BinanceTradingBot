# Agent Memory System

## Overview

The Agent Memory System provides long-term memory capabilities for agents in the Hive Mind platform. It uses vector embeddings to store and retrieve relevant information based on semantic similarity, allowing agents to remember past interactions, code snippets, task contexts, and other relevant information.

## Architecture

The memory system consists of two main components:

1. **Memory Repository**: Stores memory entries with their associated vector embeddings
   - In-memory storage for local development
   - Qdrant vector database for production

2. **Memory Management**: Handles the storage, retrieval, and organization of memories
   - Adding new memories
   - Retrieving specific memories
   - Searching for semantically similar memories
   - Managing memory importance and relevance

## Core Features

### Memory Storage

Each memory entry includes:
- Content (the text to remember)
- Metadata (additional information about the memory)
- Vector embedding (for semantic search)
- Importance score (to prioritize memories)
- Access statistics (last accessed, access count)

```python
class MemoryEntry:
    id: str                       # Unique identifier
    content: str                  # The text content to remember
    metadata: Dict[str, Any]      # Additional metadata
    embedding: List[float]        # Vector embedding of the content
    created_at: float             # Creation timestamp
    importance: float             # Importance score (0.0-5.0)
    last_accessed: Optional[float] # Last access timestamp
    access_count: int             # Number of times accessed
```

### Semantic Search

The memory system enables agents to search for relevant memories based on semantic similarity using:
- Cosine similarity between embeddings
- Importance-weighted search results
- Customizable similarity thresholds
- Filtering based on metadata

### Memory Types

The system handles various types of memories:
- **Conversations**: Agent interactions and messages
- **Code Snippets**: Implemented code and solutions
- **Task Information**: Requirements, specifications, and feedback
- **Bug Reports**: Identified issues and their solutions
- **Test Cases**: Test plans and implementations
- **Implementation Decisions**: Architectural choices and reasoning

## Integration with Agent Framework

The memory system is integrated with the BaseAgent class, allowing all agents to:
- Store incoming and outgoing messages
- Remember LLM interactions (prompts and responses)
- Track tool usage and results
- Store task submissions and feedback
- Maintain context across conversations

## Usage

Agents can use the memory system to enhance their capabilities:

### Contextual Prompting

```python
# Retrieve relevant memories for a query
memories = await agent.retrieve_relevant_memories(
    query="How to implement authentication",
    max_memories=5
)

# Build context with these memories
context = await agent.build_context_with_memory(
    query="User authentication implementation",
    max_memories=5,
    recent_message_count=3
)
```

### Storing Important Information

```python
# Store a new memory with metadata
await agent.memory.add_memory(
    content="The authentication system should use JWT tokens",
    metadata={
        "type": "requirement",
        "component": "authentication",
        "priority": "high"
    },
    importance=3.5  # Higher importance (0.0-5.0 scale)
)
```

## Local vs. Production Mode

The memory system supports two modes of operation:

### Local Mode
- Uses in-memory Python dictionaries for storage
- Mock embedding function for development
- No external dependencies required

### Production Mode
- Uses Qdrant vector database for scalable storage
- Real embedding models from OpenAI or other providers
- Supports distributed agent deployment

## Configuration

The memory system can be configured when initializing an agent:

```python
agent = CoderAgent(
    agent_id="coder",
    memory_enabled=True,                        # Enable/disable memory
    embedding_model="text-embedding-ada-002",   # Embedding model to use
    vector_db_url="http://qdrant:6333",         # Vector DB URL (None for local)
    local_memory_mode=True                      # Use local memory mode
)
```

## Performance Considerations

- Embeddings are cached to reduce API calls
- Memory importance helps prioritize relevant information
- Access statistics track usage patterns
- Local mode provides fast development experience

## Planned Enhancements

1. **Memory Pruning**: Automatically remove or archive less important memories
2. **Contextual Compression**: Summarize and compress related memories
3. **Hierarchical Memory**: Organize memories in hierarchical structures
4. **Cross-Agent Memory Sharing**: Enable memory sharing between agents
5. **Memory Reflection**: Allow agents to reflect on and analyze their memories 