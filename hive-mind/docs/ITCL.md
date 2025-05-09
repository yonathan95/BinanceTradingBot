# Inter-Team Communication Layer (ITCL)

The Inter-Team Communication Layer is a core component of the Hive Mind platform that facilitates efficient and context-aware communication between different teams of agents.

## Overview

The ITCL is responsible for:

1. Routing messages between teams based on context tags
2. Summarizing conversations to minimize token usage
3. Managing the team relationship graph
4. Handling cross-team broadcasts and directed messages

## Key Components

### ContextTag

Context tags are used to categorize messages and determine routing. Examples include `#frontend`, `#backend`, `#security`, etc. Each tag can have related tags and a description to help with routing decisions.

### Message

The core communication unit with properties like:
- Sender ID
- Recipients (optional, can be auto-routed)
- Content
- Context tags
- Priority
- Thread ID

### TeamGraph

Represents the directed-acyclic graph of team relationships. Prevents circular communication loops and enables efficient message routing based on context tags.

### ConversationSummary

Summaries of conversation threads that can be shared between teams to provide context without sharing the full conversation history.

## Usage Examples

### Message Routing

```python
# Import the layer
from hive_mind.communication_layer import InterTeamCommunicationLayer, ContextTag, TeamGraph

# Initialize the layer
itcl = InterTeamCommunicationLayer()
await itcl.initialize()

# Register context tags
await itcl.register_context_tag(ContextTag(
    name="#frontend",
    description="Frontend development topics",
    related_tags=["#ui", "#design"]
))

# Set up team graph
team_graph = TeamGraph(
    teams={
        "team1": {"name": "Frontend Team"},
        "team2": {"name": "Backend Team"}
    },
    connections={
        "team1": ["team2"],
        "team2": ["team1"]
    },
    tag_routes={
        "#frontend": ["team1"],
        "#backend": ["team2"]
    }
)
await itcl.update_team_graph(team_graph)

# Send a message with context tags
message = await itcl.send_message({
    "sender": "agent1",
    "content": "We need to update the API endpoints for the new UI",
    "context_tags": ["#frontend", "#backend"],
    "message_type": "update",
    "priority": "high",
    "requires_response": True,
    "thread_id": "ui-api-integration"
})

# Broadcast to all teams with specific tags
messages = await itcl.broadcast_message(
    sender="manager_agent",
    content="Security update required for all services",
    tags=["#security"],
    metadata={"urgency": "high"}
)
```

## Message Summarization

The ITCL automatically summarizes messages when they cross team boundaries to reduce token usage. Summarization is triggered when:

1. The message is crossing team boundaries
2. The message content is longer than a configurable threshold (default: 500 characters)

## Thread Management

Conversations are grouped by thread ID, allowing related messages to be tracked and summarized together.

## Deployment

In production mode, the ITCL uses Redis for:
1. Persistent storage of tags and team relationships
2. Pub/Sub for real-time message delivery
3. Time-series data for conversation history

## Configuration

Key configuration options:
- `redis_url`: URL for Redis connection
- `local_mode`: If true, use in-memory storage instead of Redis
- `summarization_model`: LLM model to use for summarization (default: gpt-3.5-turbo) 