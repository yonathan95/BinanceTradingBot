# Cost Domain Manager

The Cost Domain Manager (CDM) is a core component of the Hive Mind platform that tracks and enforces budget constraints across the system.

## Overview

The Cost Domain Manager is responsible for:

1. Tracking token usage and costs for all LLM calls
2. Managing team and topic-specific budgets
3. Enforcing budget constraints
4. Generating spending alerts when thresholds are reached
5. Forecasting future spending
6. Providing cost reporting and analysis

## Key Components

### TokenUsage

Represents token usage for a single LLM request, tracking:
- Agent and team IDs
- Model used
- Token counts (prompt, completion, total)
- Estimated cost
- Topic name (optional)
- Timestamp

### Budget

Represents a team-level budget with:
- Total and remaining budget amounts
- Start and end dates
- Alert thresholds
- Tier-specific constraints

### TopicBudget

Represents a topic-specific budget within a team, with:
- Total and remaining budget
- Status (active, paused, completed)
- Alert thresholds

### SpendingAlert

Represents an alert triggered when budget thresholds are reached, including:
- Alert type
- Current spending and budget limit
- Percentage used
- Team and (optional) topic information

## Key Features

### Budget Management

The CDM supports two levels of budget management:
1. **Team Budgets**: Overall spending limits for an entire team
2. **Topic Budgets**: Sub-budgets for specific topics/projects within a team

This allows for granular cost control and allocation of resources to different initiatives.

### Tier-Based Budget Constraints

Teams can set spending limits per tier (economy, standard, premium), enabling cost-effective use of different LLM models:
- Economy tier: Lower-cost models for simpler tasks
- Standard tier: Balanced models for most tasks
- Premium tier: Higher-cost models for complex tasks

### Spend Forecasting

The CDM forecasts future spending based on historical patterns, helping teams:
- Anticipate budget exhaustion
- Plan resource allocation
- Make informed decisions about model tier usage

### Budget Alerts

Automated alerts are generated when:
- A threshold percentage of a budget is reached (default: 80%)
- A budget is depleted
- A daily tier limit is approached
- A topic budget reaches its threshold

## Usage Examples

### Token Usage Tracking

```python
# Import the CDM
from cost_domain.cost_domain_manager import CostDomainManager

# Initialize the CDM
cdm = CostDomainManager()
await cdm.initialize()

# Record token usage
usage = await cdm.record_token_usage({
    "agent_id": "agent1",
    "model": "gpt-4o",
    "prompt_tokens": 500,
    "completion_tokens": 200,
    "total_tokens": 700,
    "team_id": "team1",
    "task_id": "task-123",
    "topic_name": "user-auth-feature"
})

# Get token usage for a team
team_usage = await cdm.get_token_usage(
    team_id="team1",
    start_time=yesterday,
    end_time=now
)
```

### Budget Management

```python
# Create a team budget
team_budget = await cdm.create_budget({
    "team_id": "team1",
    "total_budget": 100.0,  # USD
    "start_date": now,
    "end_date": next_month,
    "alert_threshold": 0.8,
    "tier_constraints": {
        "economy": 10.0,  # Daily limit for economy tier
        "standard": 30.0,  # Daily limit for standard tier
        "premium": 10.0    # Daily limit for premium tier
    }
})

# Create a topic budget
topic_budget = await cdm.create_topic_budget({
    "team_id": "team1",
    "topic_name": "user-auth-feature",
    "total_budget": 25.0,  # USD
    "start_date": now,
    "end_date": next_week,
    "alert_threshold": 0.75
})

# Record usage against a topic budget
success, message = await cdm.record_topic_usage(
    team_id="team1", 
    topic_name="user-auth-feature", 
    cost=2.5
)

# Pause a topic budget
await cdm.pause_topic_budget("team1", "user-auth-feature")

# Resume a topic budget
await cdm.resume_topic_budget("team1", "user-auth-feature")
```

### Cost Reporting and Analysis

```python
# Get daily spending for a team
spending = await cdm.get_daily_spending("team1", days=7)

# Get spending forecast
forecast = await cdm.get_spending_forecast("team1")

# Get model usage breakdown
model_usage = await cdm.get_model_usage_breakdown("team1", days=30)

# Get agent usage breakdown
agent_usage = await cdm.get_agent_usage_breakdown("team1", days=30)

# Get topic spending
topic_spending = await cdm.get_topic_spending("team1", "user-auth-feature", days=30)
```

### Budget Availability Checks

```python
# Check if team has budget available
available, message = await cdm.check_budget_availability("team1", 5.0)

# Check if specific tier has budget available
tier_available, tier_message = await cdm.check_tier_availability("team1", "premium", 2.0)
```

## Deployment

In production mode, the Cost Domain Manager uses:
1. Redis for real-time tracking and persistent storage
2. BigQuery export for detailed cost analysis
3. Vertex AI for spend forecasting

## Configuration

Key configuration options:
- `redis_url`: URL for Redis connection
- `local_mode`: If true, use in-memory storage instead of Redis
- `daily_forecast_window`: Number of days to look back for forecasting
- `save_interval`: How often to save state (in seconds) 