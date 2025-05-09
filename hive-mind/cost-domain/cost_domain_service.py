"""
Cost Domain Manager Service - FastAPI service for the Cost Domain Manager.
Provides API endpoints for budget management and cost tracking.
"""

import logging
import json
import time
import os
from typing import Dict, List, Any, Optional
from fastapi import FastAPI, HTTPException, Depends, Query, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

from cost_domain_manager import CostDomainManager, TokenUsage, Budget, SpendingAlert

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(title="Cost Domain Manager API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Cost Domain Manager
cdm = CostDomainManager(
    redis_url=os.getenv("REDIS_URL"),
    local_mode=os.getenv("LOCAL_MODE", "true").lower() == "true",
    daily_forecast_window=int(os.getenv("FORECAST_WINDOW_DAYS", "7")),
    save_interval=int(os.getenv("SAVE_INTERVAL_SECONDS", "300"))
)

# Initialize CDM on startup
@app.on_event("startup")
async def startup_event():
    await cdm.initialize()
    logger.info("Cost Domain Manager initialized")

# Cleanup on shutdown
@app.on_event("shutdown")
async def shutdown_event():
    await cdm.close()
    logger.info("Cost Domain Manager shutdown")

# Request/Response models for the API
class TokenUsageRequest(BaseModel):
    agent_id: str
    model: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    team_id: str
    task_id: Optional[str] = None

class TokenUsageResponse(BaseModel):
    usage_id: str
    agent_id: str
    model: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    team_id: str
    task_id: Optional[str]
    estimated_cost: float
    timestamp: float

class BudgetRequest(BaseModel):
    team_id: str
    total_budget: float
    start_date: Optional[float] = None
    end_date: Optional[float] = None
    alert_threshold: Optional[float] = None
    tier_constraints: Optional[Dict[str, float]] = None

class BudgetUpdateRequest(BaseModel):
    total_budget: Optional[float] = None
    end_date: Optional[float] = None
    alert_threshold: Optional[float] = None
    tier_constraints: Optional[Dict[str, float]] = None

class BudgetResponse(BaseModel):
    budget_id: str
    team_id: str
    total_budget: float
    remaining_budget: float
    start_date: float
    end_date: Optional[float]
    alert_threshold: float
    tier_constraints: Dict[str, float]
    created_at: float

class ForecastResponse(BaseModel):
    team_id: str
    avg_daily_spend: float
    forecast_30_days: float
    forecast_90_days: float
    daily_data: Dict[str, float]
    last_updated: float

class UsageBreakdownResponse(BaseModel):
    team_id: str
    period: str
    total_cost: float
    total_tokens: int
    total_requests: int
    models: Optional[Dict[str, Any]] = None
    agents: Optional[Dict[str, Any]] = None

class AlertResponse(BaseModel):
    alert_id: str
    team_id: str
    budget_id: str
    alert_type: str
    message: str
    current_spending: float
    budget_limit: float
    percentage_used: float
    timestamp: float

class BudgetCheckResponse(BaseModel):
    is_available: bool
    reason: Optional[str] = None

# API Routes

@app.post("/usage", response_model=TokenUsageResponse)
async def record_token_usage(usage: TokenUsageRequest):
    """Record token usage from an LLM call"""
    try:
        token_usage = await cdm.record_token_usage(usage.dict())
        
        # Convert to response format
        response_data = token_usage.dict()
        response_data["usage_id"] = token_usage.id if hasattr(token_usage, "id") else str(int(token_usage.timestamp))
        
        return TokenUsageResponse(**response_data)
    except Exception as e:
        logger.error(f"Error recording token usage: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/budgets", response_model=BudgetResponse)
async def create_budget(budget: BudgetRequest):
    """Create a new budget for a team"""
    try:
        # Set default start date to now if not provided
        budget_data = budget.dict()
        if budget_data.get("start_date") is None:
            budget_data["start_date"] = time.time()
            
        created_budget = await cdm.create_budget(budget_data)
        return BudgetResponse(**created_budget.dict())
    except Exception as e:
        logger.error(f"Error creating budget: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/budgets/{budget_id}", response_model=BudgetResponse)
async def get_budget(budget_id: str):
    """Get a budget by ID"""
    try:
        budget = await cdm.get_budget(budget_id)
        if budget is None:
            raise HTTPException(status_code=404, detail="Budget not found")
        return BudgetResponse(**budget.dict())
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting budget: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/budgets/{budget_id}", response_model=BudgetResponse)
async def update_budget(budget_id: str, updates: BudgetUpdateRequest):
    """Update an existing budget"""
    try:
        updated_budget = await cdm.update_budget(budget_id, updates.dict(exclude_unset=True))
        if updated_budget is None:
            raise HTTPException(status_code=404, detail="Budget not found")
        return BudgetResponse(**updated_budget.dict())
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating budget: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/teams/{team_id}/budgets", response_model=List[BudgetResponse])
async def get_team_budgets(team_id: str):
    """Get all budgets for a team"""
    try:
        budgets = await cdm.get_team_budgets(team_id)
        return [BudgetResponse(**budget.dict()) for budget in budgets]
    except Exception as e:
        logger.error(f"Error getting team budgets: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/teams/{team_id}/usage")
async def get_team_usage(
    team_id: str, 
    start_time: Optional[float] = Query(None, description="Start timestamp"),
    end_time: Optional[float] = Query(None, description="End timestamp")
):
    """Get token usage for a team within a time range"""
    try:
        usage_data = await cdm.get_token_usage(team_id, start_time, end_time)
        return [usage.dict() for usage in usage_data]
    except Exception as e:
        logger.error(f"Error getting team usage: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/teams/{team_id}/daily-spending")
async def get_team_daily_spending(
    team_id: str, 
    days: int = Query(7, description="Number of days to look back")
):
    """Get daily spending for a team"""
    try:
        daily_spending = await cdm.get_daily_spending(team_id, days)
        return daily_spending
    except Exception as e:
        logger.error(f"Error getting daily spending: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/teams/{team_id}/forecast", response_model=ForecastResponse)
async def get_team_forecast(team_id: str, background_tasks: BackgroundTasks):
    """Get spending forecast for a team"""
    try:
        forecast = await cdm.get_spending_forecast(team_id)
        
        # Update forecast in background if it's old
        if "last_updated" in forecast and time.time() - forecast["last_updated"] > 3600:
            background_tasks.add_task(cdm.forecast_spending, team_id)
            
        return ForecastResponse(**forecast)
    except Exception as e:
        logger.error(f"Error getting forecast: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/teams/{team_id}/alerts", response_model=List[AlertResponse])
async def get_team_alerts(
    team_id: str, 
    start_time: Optional[float] = Query(None, description="Start timestamp"),
    end_time: Optional[float] = Query(None, description="End timestamp")
):
    """Get alerts for a team within a time range"""
    try:
        alerts = await cdm.get_alerts(team_id, start_time, end_time)
        return [AlertResponse(**alert.dict()) for alert in alerts]
    except Exception as e:
        logger.error(f"Error getting alerts: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/teams/{team_id}/model-usage", response_model=UsageBreakdownResponse)
async def get_model_usage(
    team_id: str, 
    days: int = Query(30, description="Number of days to look back")
):
    """Get breakdown of model usage for a team"""
    try:
        breakdown = await cdm.get_model_usage_breakdown(team_id, days)
        return UsageBreakdownResponse(**breakdown)
    except Exception as e:
        logger.error(f"Error getting model usage: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/teams/{team_id}/agent-usage", response_model=UsageBreakdownResponse)
async def get_agent_usage(
    team_id: str, 
    days: int = Query(30, description="Number of days to look back")
):
    """Get breakdown of usage by agent for a team"""
    try:
        breakdown = await cdm.get_agent_usage_breakdown(team_id, days)
        return UsageBreakdownResponse(**breakdown)
    except Exception as e:
        logger.error(f"Error getting agent usage: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/teams/{team_id}/check-budget", response_model=BudgetCheckResponse)
async def check_budget_availability(team_id: str, estimated_cost: float):
    """Check if budget is available for a team"""
    try:
        is_available, reason = await cdm.check_budget_availability(team_id, estimated_cost)
        return BudgetCheckResponse(is_available=is_available, reason=reason)
    except Exception as e:
        logger.error(f"Error checking budget: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/teams/{team_id}/check-tier", response_model=BudgetCheckResponse)
async def check_tier_availability(team_id: str, tier: str, estimated_cost: float):
    """Check if a specific tier is available within budget constraints"""
    try:
        is_available, reason = await cdm.check_tier_availability(team_id, tier, estimated_cost)
        return BudgetCheckResponse(is_available=is_available, reason=reason)
    except Exception as e:
        logger.error(f"Error checking tier: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Health check endpoint
@app.get("/health")
async def health_check():
    """Check the health of the Cost Domain Manager service"""
    return {"status": "healthy", "timestamp": time.time()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080) 