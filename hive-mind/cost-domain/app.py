#!/usr/bin/env python3
"""
Cost Domain Service for Hive Mind

This service is responsible for:
1. Tracking agent usage costs
2. Managing team budgets
3. Providing cost analytics
4. Sending alerts when budgets are close to depletion
"""

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from prometheus_client import Counter, Histogram, start_http_server
import asyncio
import json
import uuid
import os
import logging
import random

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Get port from environment variable or use default
PORT = int(os.environ.get("PORT", 8081))

# Constants
COST_PER_TOKEN = {
    "input": {
        "gpt-3.5-turbo": 0.0000015,
        "gpt-3.5-turbo-16k": 0.000003,
        "gpt-4o": 0.00001,
        "gpt-4-turbo": 0.00001,
        "claude-instant-1": 0.0000008,
        "claude-3-opus": 0.00001
    },
    "output": {
        "gpt-3.5-turbo": 0.000002,
        "gpt-3.5-turbo-16k": 0.000004,
        "gpt-4o": 0.00003,
        "gpt-4-turbo": 0.00003,
        "claude-instant-1": 0.0000024,
        "claude-3-opus": 0.00003
    }
}

# Models
class UsageRecord(BaseModel):
    agent_id: str
    team_id: str
    model: str
    input_tokens: int
    output_tokens: int
    duration_ms: int
    timestamp: datetime = Field(default_factory=datetime.now)
    task_id: Optional[str] = None
    task_type: Optional[str] = None
    project_id: Optional[str] = None


class BudgetAlert(BaseModel):
    team_id: str
    alert_type: str
    percentage_used: float
    current_spending: float
    budget_limit: float
    message: str
    timestamp: datetime = Field(default_factory=datetime.now)


class TeamBudget(BaseModel):
    team_id: str
    total_budget: float
    remaining_budget: float
    start_date: datetime
    end_date: Optional[datetime] = None
    alert_threshold: float = 0.8


# In-memory storage (would be replaced with DB in production)
usage_records: List[UsageRecord] = []
budget_alerts: List[BudgetAlert] = []
team_budgets: Dict[str, TeamBudget] = {}

# Prometheus metrics
cost_counter = Counter('hivemind_token_cost_total', 'Total cost of tokens used', ['team_id', 'model'])
token_counter = Counter('hivemind_tokens_total', 'Total number of tokens used', ['team_id', 'model', 'type'])
request_latency = Histogram('hivemind_request_latency_seconds', 'Request latency in seconds')

# FastAPI app
app = FastAPI(title="Hive Mind Cost Domain Service")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development - restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    # Start Prometheus metrics server on a different port to avoid conflicts
    metrics_port = PORT + 100  # Use PORT + 100 for metrics
    start_http_server(metrics_port)
    logger.info(f"Started Prometheus metrics server on port {metrics_port}")
    logger.info(f"API running on port {PORT}")
    
    # Pre-populate with some example data
    await load_example_data()


async def load_example_data():
    """Load example data for testing"""
    # Example team budgets
    team_budgets["team-1"] = TeamBudget(
        team_id="team-1",
        total_budget=200.0,
        remaining_budget=150.0,
        start_date=datetime.now() - timedelta(days=30),
        end_date=datetime.now() + timedelta(days=60),
        alert_threshold=0.8
    )
    
    team_budgets["team-2"] = TeamBudget(
        team_id="team-2",
        total_budget=150.0,
        remaining_budget=100.0,
        start_date=datetime.now() - timedelta(days=15),
        end_date=datetime.now() + timedelta(days=75),
        alert_threshold=0.8
    )
    
    team_budgets["team-3"] = TeamBudget(
        team_id="team-3",
        total_budget=300.0,
        remaining_budget=200.0,
        start_date=datetime.now() - timedelta(days=45),
        end_date=datetime.now() + timedelta(days=45),
        alert_threshold=0.8
    )
    
    # Generate some example usage data
    models = ["gpt-3.5-turbo", "gpt-4o", "claude-3-opus"]
    teams = ["team-1", "team-2", "team-3"]
    agents = [f"agent-{i}" for i in range(1, 10)]
    task_types = ["code", "planning", "testing", "documentation"]
    
    for _ in range(100):
        team_id = random.choice(teams)
        model = random.choice(models)
        input_tokens = random.randint(200, 1000)
        output_tokens = random.randint(500, 3000)
        
        record = UsageRecord(
            agent_id=random.choice(agents),
            team_id=team_id,
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            duration_ms=random.randint(500, 5000),
            timestamp=datetime.now() - timedelta(minutes=random.randint(0, 60*24*7)),
            task_id=f"task-{random.randint(1, 20)}",
            task_type=random.choice(task_types),
            project_id=f"project-{random.randint(1, 5)}"
        )
        
        # Calculate cost
        input_cost = input_tokens * COST_PER_TOKEN["input"].get(model, 0.00001)
        output_cost = output_tokens * COST_PER_TOKEN["output"].get(model, 0.00003)
        total_cost = input_cost + output_cost
        
        # Update metrics
        cost_counter.labels(team_id=team_id, model=model).inc(total_cost)
        token_counter.labels(team_id=team_id, model=model, type="input").inc(input_tokens)
        token_counter.labels(team_id=team_id, model=model, type="output").inc(output_tokens)
        
        usage_records.append(record)
    
    logger.info(f"Loaded {len(usage_records)} example usage records and {len(team_budgets)} team budgets")


@app.get("/")
async def root():
    return {"status": "ok", "service": "cost-domain", "port": PORT}


@app.post("/usage", status_code=201)
async def record_usage(record: UsageRecord, background_tasks: BackgroundTasks):
    """Record a new usage record and update metrics"""
    usage_records.append(record)
    
    # Calculate cost
    input_cost = record.input_tokens * COST_PER_TOKEN["input"].get(record.model, 0.00001)
    output_cost = record.output_tokens * COST_PER_TOKEN["output"].get(record.model, 0.00003)
    total_cost = input_cost + output_cost
    
    # Update metrics
    cost_counter.labels(team_id=record.team_id, model=record.model).inc(total_cost)
    token_counter.labels(team_id=record.team_id, model=record.model, type="input").inc(record.input_tokens)
    token_counter.labels(team_id=record.team_id, model=record.model, type="output").inc(record.output_tokens)
    
    # Update team budget in background
    background_tasks.add_task(update_team_budget, record.team_id, total_cost)
    
    return {"id": len(usage_records) - 1, "cost": total_cost}


async def update_team_budget(team_id: str, cost: float):
    """Update a team's budget and generate alerts if needed"""
    if team_id in team_budgets:
        budget = team_budgets[team_id]
        budget.remaining_budget -= cost
        
        # Check if we need to generate an alert
        percentage_used = (budget.total_budget - budget.remaining_budget) / budget.total_budget
        
        if percentage_used >= budget.alert_threshold:
            alert = BudgetAlert(
                team_id=team_id,
                alert_type="budget_threshold",
                percentage_used=percentage_used,
                current_spending=budget.total_budget - budget.remaining_budget,
                budget_limit=budget.total_budget,
                message=f"Team {team_id} has used {percentage_used:.1%} of its budget"
            )
            budget_alerts.append(alert)
            logger.info(f"Generated budget alert for team {team_id}: {percentage_used:.1%} used")


@app.get("/teams/{team_id}/budget")
async def get_team_budget(team_id: str):
    """Get budget information for a team"""
    if team_id not in team_budgets:
        raise HTTPException(status_code=404, detail="Team budget not found")
    
    budget = team_budgets[team_id]
    
    # Calculate additional metrics
    usage = budget.total_budget - budget.remaining_budget
    percentage_used = usage / budget.total_budget if budget.total_budget > 0 else 0
    
    return {
        **budget.dict(),
        "usage": usage,
        "percentage_used": percentage_used
    }


@app.get("/teams/{team_id}/usage")
async def get_team_usage(team_id: str, days: int = 7):
    """Get usage data for a team"""
    cutoff = datetime.now() - timedelta(days=days)
    team_usage = [r for r in usage_records if r.team_id == team_id and r.timestamp >= cutoff]
    
    if not team_usage:
        return {"usage": [], "total_cost": 0}
    
    # Calculate total cost
    total_cost = 0
    for record in team_usage:
        input_cost = record.input_tokens * COST_PER_TOKEN["input"].get(record.model, 0.00001)
        output_cost = record.output_tokens * COST_PER_TOKEN["output"].get(record.model, 0.00003)
        total_cost += input_cost + output_cost
    
    return {
        "usage": team_usage,
        "total_cost": total_cost,
        "record_count": len(team_usage)
    }


@app.post("/teams/{team_id}/budget")
async def set_team_budget(team_id: str, budget: TeamBudget):
    """Set or update a team's budget"""
    team_budgets[team_id] = budget
    return {"status": "ok", "team_id": team_id}


@app.get("/alerts")
async def get_alerts(team_id: Optional[str] = None, days: int = 7):
    """Get budget alerts, optionally filtered by team"""
    cutoff = datetime.now() - timedelta(days=days)
    
    if team_id:
        filtered_alerts = [a for a in budget_alerts if a.team_id == team_id and a.timestamp >= cutoff]
    else:
        filtered_alerts = [a for a in budget_alerts if a.timestamp >= cutoff]
    
    return {"alerts": filtered_alerts, "count": len(filtered_alerts)}


@app.get("/cost/models")
async def get_model_costs():
    """Get cost information for different models"""
    return {"cost_per_token": COST_PER_TOKEN}


@app.get("/metrics/summary")
async def get_metrics_summary():
    """Get a summary of key metrics"""
    # Calculate total costs per team
    team_costs = {}
    for record in usage_records:
        team_id = record.team_id
        if team_id not in team_costs:
            team_costs[team_id] = 0
            
        input_cost = record.input_tokens * COST_PER_TOKEN["input"].get(record.model, 0.00001)
        output_cost = record.output_tokens * COST_PER_TOKEN["output"].get(record.model, 0.00003)
        team_costs[team_id] += input_cost + output_cost
    
    # Get budget status
    budget_status = []
    for team_id, budget in team_budgets.items():
        usage = budget.total_budget - budget.remaining_budget
        percentage_used = usage / budget.total_budget if budget.total_budget > 0 else 0
        
        budget_status.append({
            "team_id": team_id,
            "total_budget": budget.total_budget,
            "remaining_budget": budget.remaining_budget,
            "usage": usage,
            "percentage_used": percentage_used
        })
    
    return {
        "team_costs": team_costs,
        "budget_status": budget_status,
        "total_records": len(usage_records),
        "total_alerts": len(budget_alerts)
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=PORT) 