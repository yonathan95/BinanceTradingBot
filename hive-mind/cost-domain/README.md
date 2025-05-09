# Cost Domain Manager

The Cost Domain Manager (CDM) is responsible for tracking, monitoring, and enforcing budget constraints across the Hive Mind system.

## Overview

The CDM provides the following core functionalities:

- **Token Usage Tracking**: Records and stores token usage from LLM calls
- **Budget Management**: Creates and enforces budgets for teams
- **Spending Analysis**: Provides insights into spending patterns
- **Cost Forecasting**: Predicts future costs based on usage patterns
- **Tier Enforcement**: Enforces constraints on model tier usage
- **Alert Generation**: Sends alerts when budget thresholds are reached

## Architecture

The CDM consists of two main components:

1. **Cost Domain Manager Core**: Implements the core functionality for tracking, analyzing, and enforcing budgets
2. **Cost Domain Service**: FastAPI service exposing the CDM functionality via a REST API

The CDM supports two operation modes:

- **Local Mode**: Uses in-memory storage for development and testing
- **Production Mode**: Uses Redis for distributed storage and scalability

## API Endpoints

The Cost Domain Manager API provides the following endpoints:

### Token Usage Endpoints

- `POST /usage`: Record token usage from an LLM call
- `GET /teams/{team_id}/usage`: Get token usage for a team within a time range
- `GET /teams/{team_id}/daily-spending`: Get daily spending for a team
- `GET /teams/{team_id}/model-usage`: Get breakdown of model usage for a team
- `GET /teams/{team_id}/agent-usage`: Get breakdown of usage by agent for a team

### Budget Management Endpoints

- `POST /budgets`: Create a new budget for a team
- `GET /budgets/{budget_id}`: Get a budget by ID
- `PUT /budgets/{budget_id}`: Update an existing budget
- `GET /teams/{team_id}/budgets`: Get all budgets for a team

### Budget Enforcement Endpoints

- `POST /teams/{team_id}/check-budget`: Check if budget is available for a team
- `POST /teams/{team_id}/check-tier`: Check if a specific tier is available within budget constraints

### Analytics and Forecasting Endpoints

- `GET /teams/{team_id}/forecast`: Get spending forecast for a team
- `GET /teams/{team_id}/alerts`: Get alerts for a team within a time range

### Health Check

- `GET /health`: Check the health of the Cost Domain Manager service

## Environment Variables

The CDM can be configured with the following environment variables:

- `REDIS_URL`: URL of the Redis server (for production mode)
- `LOCAL_MODE`: Whether to use local mode (true/false)
- `FORECAST_WINDOW_DAYS`: Number of days to look back for forecasting (default: 7)
- `SAVE_INTERVAL_SECONDS`: Interval for saving state in local mode (default: 300)
- `LOG_LEVEL`: Logging level (default: INFO)

## Usage

### Docker

The CDM can be run using Docker:

```bash
docker build -t hive-mind/cost-domain .
docker run -p 8080:8080 -e REDIS_URL=redis://redis:6379 -e LOCAL_MODE=false hive-mind/cost-domain
```

### Local Development

For local development:

```bash
cd cost-domain
pip install -r requirements.txt
uvicorn cost_domain_service:app --reload
```

## Integration with Agents

Agents should record their token usage by sending a request to the CDM after each LLM call:

```python
async def record_token_usage(agent_id, model, prompt_tokens, completion_tokens, team_id, task_id=None):
    url = "http://cost-domain:8080/usage"
    data = {
        "agent_id": agent_id,
        "model": model,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": prompt_tokens + completion_tokens,
        "team_id": team_id,
        "task_id": task_id
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=data) as response:
            return await response.json()
```

## Integration with Task Orchestrator

The Task Orchestrator should check budget availability before assigning tasks to higher-tier models:

```python
async def check_tier_availability(team_id, tier, estimated_cost):
    url = f"http://cost-domain:8080/teams/{team_id}/check-tier"
    params = {
        "tier": tier,
        "estimated_cost": estimated_cost
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.post(url, params=params) as response:
            result = await response.json()
            return result["is_available"], result.get("reason")
```

## Model Pricing

The CDM includes a pricing model for various LLM models based on their token costs. This pricing is used to estimate costs for token usage and budget enforcement.

Current supported models include:

- **OpenAI Models**: GPT-4o, GPT-4, GPT-3.5-Turbo
- **Anthropic Models**: Claude-3-Opus, Claude-3-Sonnet, Claude-3-Haiku

## Future Enhancements

Planned enhancements for the CDM include:

1. Integration with BigQuery for more sophisticated cost analysis
2. AI-powered usage forecasting with Vertex AI
3. Automated cost optimization recommendations
4. Integration with external billing systems
5. Fine-grained budget controls at the project and task level 