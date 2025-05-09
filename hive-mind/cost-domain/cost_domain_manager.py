"""
Cost Domain Manager - Responsible for tracking and enforcing budget constraints
across the Hive Mind system.
"""

import logging
import json
import time
import asyncio
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from pydantic import BaseModel
import uuid
import os
import aioredis

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TokenUsage(BaseModel):
    """Represents token usage for a single LLM request"""
    timestamp: float
    agent_id: str
    model: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    team_id: str
    task_id: Optional[str] = None
    topic_name: Optional[str] = None  # Added for topic-based tracking
    estimated_cost: float
    
    def __init__(self, **data):
        if 'timestamp' not in data:
            data['timestamp'] = time.time()
        if 'estimated_cost' not in data:
            # Calculate estimated cost based on token counts and model
            data['estimated_cost'] = self._calculate_cost(
                data['model'], 
                data['prompt_tokens'], 
                data['completion_tokens']
            )
        super().__init__(**data)
    
    def _calculate_cost(self, model: str, prompt_tokens: int, completion_tokens: int) -> float:
        """Calculate the estimated cost based on the model and token counts"""
        # Model pricing per 1000 tokens (approximate values, should be updated as pricing changes)
        model_pricing = {
            # OpenAI models
            "gpt-4o": {"prompt": 0.01, "completion": 0.03},
            "gpt-4": {"prompt": 0.03, "completion": 0.06},
            "gpt-3.5-turbo": {"prompt": 0.0015, "completion": 0.002},
            
            # Anthropic models
            "claude-3-opus": {"prompt": 0.015, "completion": 0.075},
            "claude-3-sonnet": {"prompt": 0.003, "completion": 0.015},
            "claude-3-haiku": {"prompt": 0.00025, "completion": 0.00125},
            
            # Default for unknown models
            "default": {"prompt": 0.01, "completion": 0.03}
        }
        
        # Get pricing for the specified model or use default
        pricing = model_pricing.get(model, model_pricing["default"])
        
        # Calculate cost
        prompt_cost = (prompt_tokens / 1000) * pricing["prompt"]
        completion_cost = (completion_tokens / 1000) * pricing["completion"]
        
        return prompt_cost + completion_cost

class Budget(BaseModel):
    """Represents a budget for a team or project"""
    budget_id: str
    team_id: str
    total_budget: float
    remaining_budget: float
    start_date: float
    end_date: Optional[float] = None
    alert_threshold: float = 0.8  # Alert when 80% of budget is used
    tier_constraints: Dict[str, float] = {}  # Maximum budget per tier
    created_at: float
    
    def __init__(self, **data):
        if 'budget_id' not in data:
            data['budget_id'] = str(uuid.uuid4())
        if 'created_at' not in data:
            data['created_at'] = time.time()
        super().__init__(**data)

class SpendingAlert(BaseModel):
    """Represents a budget alert"""
    alert_id: str
    team_id: str
    budget_id: str
    alert_type: str  # "threshold", "daily_limit", "budget_depleted", "topic_threshold", "topic_depleted"
    message: str
    current_spending: float
    budget_limit: float
    percentage_used: float
    topic_name: Optional[str] = None  # Added for topic-based alerts
    timestamp: float
    
    def __init__(self, **data):
        if 'alert_id' not in data:
            data['alert_id'] = str(uuid.uuid4())
        if 'timestamp' not in data:
            data['timestamp'] = time.time()
        super().__init__(**data)

class TopicBudget(BaseModel):
    """Represents a budget for a specific topic within a team's project"""
    budget_id: str
    team_id: str
    topic_name: str
    total_budget: float
    remaining_budget: float
    start_date: float
    end_date: Optional[float] = None
    alert_threshold: float = 0.8  # Alert when 80% of budget is used
    created_at: float
    status: str = "active"  # active, paused, completed
    
    def __init__(self, **data):
        if 'budget_id' not in data:
            data['budget_id'] = str(uuid.uuid4())
        if 'created_at' not in data:
            data['created_at'] = time.time()
        super().__init__(**data)

class CostDomainManager:
    """
    Cost Domain Manager that tracks and enforces budget constraints
    across the Hive Mind system.
    """
    
    def __init__(self, 
                redis_url: Optional[str] = None,
                local_mode: bool = True,
                daily_forecast_window: int = 7,  # Days to look back for forecasting
                save_interval: int = 300):  # Save state every 5 minutes
        """Initialize the Cost Domain Manager"""
        self.redis_url = redis_url
        self.local_mode = local_mode
        self.daily_forecast_window = daily_forecast_window
        self.save_interval = save_interval
        
        # In-memory storage for local mode
        self.token_usage: List[TokenUsage] = []
        self.budgets: Dict[str, Budget] = {}
        self.alerts: List[SpendingAlert] = []
        
        # Redis connection for production mode
        self.redis = None
        
        # Spending forecast cache
        self.spending_forecasts: Dict[str, Dict[str, Any]] = {}
        
        logger.info(f"Cost Domain Manager initialized in {'local' if local_mode else 'production'} mode")
    
    async def initialize(self):
        """Initialize the Cost Domain Manager"""
        if not self.local_mode and self.redis_url:
            try:
                self.redis = await aioredis.create_redis_pool(self.redis_url)
                logger.info(f"Connected to Redis at {self.redis_url}")
                
                # Load data from Redis
                await self._load_state()
                
                # Start background tasks
                asyncio.create_task(self._periodic_save())
                asyncio.create_task(self._periodic_forecast_update())
            except Exception as e:
                logger.error(f"Failed to connect to Redis: {str(e)}")
                logger.warning("Falling back to local mode")
                self.local_mode = True
        
        if self.local_mode:
            # Start only forecasting in local mode
            asyncio.create_task(self._periodic_forecast_update())
            
            # Load state from local file if available
            await self._load_local_state()
    
    async def _load_state(self):
        """Load state from Redis"""
        if not self.redis:
            return
            
        # Load budgets
        budget_keys = await self.redis.keys('budget:*')
        for key in budget_keys:
            budget_data = await self.redis.get(key)
            if budget_data:
                budget = Budget(**json.loads(budget_data))
                self.budgets[budget.budget_id] = budget
        
        # We don't load all usage data, as it could be too large
        # Instead, we'll query it as needed
        
        logger.info(f"Loaded {len(self.budgets)} budgets from Redis")
    
    async def _load_local_state(self):
        """Load state from local file"""
        try:
            if os.path.exists('cost_domain_state.json'):
                with open('cost_domain_state.json', 'r') as f:
                    state = json.load(f)
                    
                    # Load budgets
                    if 'budgets' in state:
                        for budget_data in state['budgets']:
                            budget = Budget(**budget_data)
                            self.budgets[budget.budget_id] = budget
                    
                    # Load recent token usage (last 7 days)
                    if 'token_usage' in state:
                        now = time.time()
                        week_ago = now - (7 * 24 * 60 * 60)
                        for usage_data in state['token_usage']:
                            if usage_data['timestamp'] >= week_ago:
                                self.token_usage.append(TokenUsage(**usage_data))
                    
                    logger.info(f"Loaded state from local file: {len(self.budgets)} budgets, {len(self.token_usage)} usage records")
        except Exception as e:
            logger.error(f"Failed to load local state: {str(e)}")
    
    async def _save_state(self):
        """Save state to Redis or local file"""
        if not self.local_mode and self.redis:
            # Save budgets to Redis
            for budget_id, budget in self.budgets.items():
                await self.redis.set(f'budget:{budget_id}', json.dumps(budget.dict()))
            
            # We don't save all usage data to Redis, as it's stored 
            # incrementally on record_token_usage
        else:
            # Save to local file
            state = {
                'budgets': [budget.dict() for budget in self.budgets.values()],
                'token_usage': [usage.dict() for usage in self.token_usage]
            }
            
            with open('cost_domain_state.json', 'w') as f:
                json.dump(state, f, indent=2)
            
            logger.info(f"Saved state to local file: {len(self.budgets)} budgets, {len(self.token_usage)} usage records")
    
    async def _periodic_save(self):
        """Periodically save state"""
        while True:
            await asyncio.sleep(self.save_interval)
            try:
                await self._save_state()
            except Exception as e:
                logger.error(f"Failed to save state: {str(e)}")
    
    async def _periodic_forecast_update(self):
        """Periodically update spending forecasts"""
        while True:
            await asyncio.sleep(3600)  # Update forecasts hourly
            try:
                # Update forecasts for all teams
                team_ids = set(budget.team_id for budget in self.budgets.values())
                for team_id in team_ids:
                    await self.forecast_spending(team_id)
            except Exception as e:
                logger.error(f"Failed to update spending forecasts: {str(e)}")
    
    async def record_token_usage(self, usage_data: Dict[str, Any]) -> TokenUsage:
        """
        Record token usage from an LLM call.
        
        Args:
            usage_data: Dictionary containing usage information
                {
                    "agent_id": str,
                    "model": str,
                    "prompt_tokens": int,
                    "completion_tokens": int,
                    "total_tokens": int,
                    "team_id": str,
                    "task_id": Optional[str]
                }
                
        Returns:
            TokenUsage object representing the recorded usage
        """
        # Create TokenUsage object
        token_usage = TokenUsage(**usage_data)
        
        if self.local_mode:
            # Store in memory
            self.token_usage.append(token_usage)
        else:
            # Store in Redis
            if self.redis:
                usage_key = f"usage:{token_usage.team_id}:{int(token_usage.timestamp)}"
                await self.redis.set(usage_key, json.dumps(token_usage.dict()))
                
                # Also add to time-series data for this team
                await self.redis.zadd(
                    f"usage_timeseries:{token_usage.team_id}", 
                    token_usage.timestamp, 
                    usage_key
                )
        
        # Update budget and check for alerts
        await self._update_budget(token_usage)
        
        return token_usage
    
    async def _update_budget(self, token_usage: TokenUsage):
        """
        Update budget based on token usage and check for alerts.
        
        Args:
            token_usage: The token usage to account for
        """
        # Find the budget for this team
        team_budget = None
        for budget in self.budgets.values():
            if (budget.team_id == token_usage.team_id and 
                budget.start_date <= token_usage.timestamp and
                (budget.end_date is None or budget.end_date >= token_usage.timestamp)):
                team_budget = budget
                break
        
        if not team_budget:
            logger.warning(f"No active budget found for team {token_usage.team_id}")
            return
            
        # Update remaining budget
        old_remaining = team_budget.remaining_budget
        team_budget.remaining_budget -= token_usage.estimated_cost
        
        # Check for alerts
        percentage_used = 1 - (team_budget.remaining_budget / team_budget.total_budget)
        
        # Threshold alert
        if percentage_used >= team_budget.alert_threshold and old_remaining > team_budget.total_budget * (1 - team_budget.alert_threshold):
            alert = SpendingAlert(
                team_id=team_budget.team_id,
                budget_id=team_budget.budget_id,
                alert_type="threshold",
                message=f"Budget threshold of {team_budget.alert_threshold*100}% reached",
                current_spending=team_budget.total_budget - team_budget.remaining_budget,
                budget_limit=team_budget.total_budget,
                percentage_used=percentage_used
            )
            
            await self._send_alert(alert)
        
        # Budget depleted alert
        if team_budget.remaining_budget <= 0 and old_remaining > 0:
            alert = SpendingAlert(
                team_id=team_budget.team_id,
                budget_id=team_budget.budget_id,
                alert_type="budget_depleted",
                message="Budget depleted",
                current_spending=team_budget.total_budget,
                budget_limit=team_budget.total_budget,
                percentage_used=1.0
            )
            
            await self._send_alert(alert)
    
    async def _send_alert(self, alert: SpendingAlert):
        """
        Send a spending alert.
        
        Args:
            alert: The alert to send
        """
        if self.local_mode:
            # Store in memory
            self.alerts.append(alert)
            logger.warning(f"Budget alert: {alert.message} for team {alert.team_id}")
        else:
            # Store in Redis
            if self.redis:
                alert_key = f"alert:{alert.team_id}:{alert.alert_id}"
                await self.redis.set(alert_key, json.dumps(alert.dict()))
                
                # Add to time-series data for this team
                await self.redis.zadd(
                    f"alert_timeseries:{alert.team_id}", 
                    alert.timestamp, 
                    alert_key
                )
                
                # Publish to Redis channel for real-time notifications
                await self.redis.publish(
                    f"budget_alerts:{alert.team_id}",
                    json.dumps(alert.dict())
                )
    
    async def create_budget(self, budget_data: Dict[str, Any]) -> Budget:
        """
        Create a new budget.
        
        Args:
            budget_data: Dictionary containing budget information
                {
                    "team_id": str,
                    "total_budget": float,
                    "start_date": float,
                    "end_date": Optional[float],
                    "alert_threshold": float,
                    "tier_constraints": Dict[str, float]
                }
                
        Returns:
            Budget object representing the created budget
        """
        # Create Budget object
        budget = Budget(**budget_data)
        budget.remaining_budget = budget.total_budget
        
        # Store budget
        self.budgets[budget.budget_id] = budget
        
        # Save state
        if not self.local_mode and self.redis:
            await self.redis.set(f'budget:{budget.budget_id}', json.dumps(budget.dict()))
        
        logger.info(f"Created budget {budget.budget_id} for team {budget.team_id}: ${budget.total_budget:.2f}")
        
        return budget
    
    async def update_budget(self, budget_id: str, updates: Dict[str, Any]) -> Optional[Budget]:
        """
        Update an existing budget.
        
        Args:
            budget_id: ID of the budget to update
            updates: Dictionary containing fields to update
                
        Returns:
            Updated Budget object or None if budget not found
        """
        if budget_id not in self.budgets:
            logger.warning(f"Budget {budget_id} not found")
            return None
            
        budget = self.budgets[budget_id]
        
        # Track if total_budget was increased
        old_total = budget.total_budget
        
        # Apply updates
        for key, value in updates.items():
            if hasattr(budget, key):
                setattr(budget, key, value)
        
        # If total budget increased, add to remaining budget
        if 'total_budget' in updates and updates['total_budget'] > old_total:
            budget.remaining_budget += (updates['total_budget'] - old_total)
        
        # Save state
        if not self.local_mode and self.redis:
            await self.redis.set(f'budget:{budget.budget_id}', json.dumps(budget.dict()))
        
        logger.info(f"Updated budget {budget.budget_id} for team {budget.team_id}")
        
        return budget
    
    async def get_budget(self, budget_id: str) -> Optional[Budget]:
        """
        Get a budget by ID.
        
        Args:
            budget_id: ID of the budget to retrieve
                
        Returns:
            Budget object or None if not found
        """
        return self.budgets.get(budget_id)
    
    async def get_team_budgets(self, team_id: str) -> List[Budget]:
        """
        Get all budgets for a team.
        
        Args:
            team_id: ID of the team
                
        Returns:
            List of Budget objects for the team
        """
        return [budget for budget in self.budgets.values() if budget.team_id == team_id]
    
    async def get_token_usage(self, 
                       team_id: str, 
                       start_time: Optional[float] = None,
                       end_time: Optional[float] = None) -> List[TokenUsage]:
        """
        Get token usage for a team within a time range.
        
        Args:
            team_id: ID of the team
            start_time: Start timestamp (if None, no lower bound)
            end_time: End timestamp (if None, no upper bound)
                
        Returns:
            List of TokenUsage objects
        """
        if start_time is None:
            start_time = 0
        if end_time is None:
            end_time = time.time()
            
        if self.local_mode:
            # Filter from in-memory storage
            return [
                usage for usage in self.token_usage 
                if usage.team_id == team_id and start_time <= usage.timestamp <= end_time
            ]
        else:
            # Query from Redis
            if self.redis:
                # Get keys from sorted set within time range
                usage_keys = await self.redis.zrangebyscore(
                    f"usage_timeseries:{team_id}",
                    start_time,
                    end_time
                )
                
                # Get usage data for each key
                results = []
                for key in usage_keys:
                    usage_data = await self.redis.get(key)
                    if usage_data:
                        results.append(TokenUsage(**json.loads(usage_data)))
                
                return results
            
        return []
    
    async def get_daily_spending(self, 
                          team_id: str, 
                          days: int = 7) -> Dict[str, float]:
        """
        Get daily spending for a team.
        
        Args:
            team_id: ID of the team
            days: Number of days to look back
                
        Returns:
            Dictionary mapping date strings to spending amounts
        """
        # Calculate time range
        end_time = time.time()
        start_time = end_time - (days * 24 * 60 * 60)
        
        # Get usage within time range
        usage_data = await self.get_token_usage(team_id, start_time, end_time)
        
        # Group by day
        daily_spending = {}
        for usage in usage_data:
            # Convert timestamp to date string
            date_str = datetime.fromtimestamp(usage.timestamp).strftime('%Y-%m-%d')
            
            # Add to daily spending
            if date_str not in daily_spending:
                daily_spending[date_str] = 0
            daily_spending[date_str] += usage.estimated_cost
        
        return daily_spending
    
    async def forecast_spending(self, team_id: str) -> Dict[str, Any]:
        """
        Forecast future spending for a team.
        
        Args:
            team_id: ID of the team
                
        Returns:
            Dictionary containing forecast information
        """
        # Get daily spending for past window
        daily_spending = await self.get_daily_spending(team_id, self.daily_forecast_window)
        
        if not daily_spending:
            return {
                "team_id": team_id,
                "avg_daily_spend": 0.0,
                "forecast_30_days": 0.0,
                "forecast_90_days": 0.0,
                "last_updated": time.time()
            }
        
        # Calculate average daily spend
        total_spend = sum(daily_spending.values())
        avg_daily_spend = total_spend / len(daily_spending) if daily_spending else 0
        
        # Create forecast
        forecast = {
            "team_id": team_id,
            "avg_daily_spend": avg_daily_spend,
            "forecast_30_days": avg_daily_spend * 30,
            "forecast_90_days": avg_daily_spend * 90,
            "daily_data": daily_spending,
            "last_updated": time.time()
        }
        
        # Cache forecast
        self.spending_forecasts[team_id] = forecast
        
        return forecast
    
    async def get_spending_forecast(self, team_id: str) -> Dict[str, Any]:
        """
        Get the cached spending forecast for a team, or generate a new one if not available.
        
        Args:
            team_id: ID of the team
                
        Returns:
            Dictionary containing forecast information
        """
        # Check if we have a recent forecast (less than 1 hour old)
        if team_id in self.spending_forecasts:
            forecast = self.spending_forecasts[team_id]
            if time.time() - forecast["last_updated"] < 3600:  # 1 hour
                return forecast
        
        # Generate new forecast
        return await self.forecast_spending(team_id)
    
    async def get_alerts(self, 
                   team_id: str, 
                   start_time: Optional[float] = None,
                   end_time: Optional[float] = None) -> List[SpendingAlert]:
        """
        Get alerts for a team within a time range.
        
        Args:
            team_id: ID of the team
            start_time: Start timestamp (if None, no lower bound)
            end_time: End timestamp (if None, no upper bound)
                
        Returns:
            List of SpendingAlert objects
        """
        if start_time is None:
            start_time = 0
        if end_time is None:
            end_time = time.time()
            
        if self.local_mode:
            # Filter from in-memory storage
            return [
                alert for alert in self.alerts 
                if alert.team_id == team_id and start_time <= alert.timestamp <= end_time
            ]
        else:
            # Query from Redis
            if self.redis:
                # Get keys from sorted set within time range
                alert_keys = await self.redis.zrangebyscore(
                    f"alert_timeseries:{team_id}",
                    start_time,
                    end_time
                )
                
                # Get alert data for each key
                results = []
                for key in alert_keys:
                    alert_data = await self.redis.get(key)
                    if alert_data:
                        results.append(SpendingAlert(**json.loads(alert_data)))
                
                return results
            
        return []
    
    async def get_model_usage_breakdown(self, team_id: str, days: int = 30) -> Dict[str, Any]:
        """
        Get breakdown of model usage for a team.
        
        Args:
            team_id: ID of the team
            days: Number of days to look back
                
        Returns:
            Dictionary containing usage breakdown by model
        """
        # Calculate time range
        end_time = time.time()
        start_time = end_time - (days * 24 * 60 * 60)
        
        # Get usage within time range
        usage_data = await self.get_token_usage(team_id, start_time, end_time)
        
        # Group by model
        model_breakdown = {}
        for usage in usage_data:
            model = usage.model
            
            # Initialize model entry if needed
            if model not in model_breakdown:
                model_breakdown[model] = {
                    "prompt_tokens": 0,
                    "completion_tokens": 0,
                    "total_tokens": 0,
                    "cost": 0.0,
                    "requests": 0
                }
            
            # Update model usage data
            model_breakdown[model]["prompt_tokens"] += usage.prompt_tokens
            model_breakdown[model]["completion_tokens"] += usage.completion_tokens
            model_breakdown[model]["total_tokens"] += usage.total_tokens
            model_breakdown[model]["cost"] += usage.estimated_cost
            model_breakdown[model]["requests"] += 1
        
        return {
            "team_id": team_id,
            "period": f"Last {days} days",
            "models": model_breakdown,
            "total_cost": sum(model["cost"] for model in model_breakdown.values()),
            "total_tokens": sum(model["total_tokens"] for model in model_breakdown.values()),
            "total_requests": sum(model["requests"] for model in model_breakdown.values())
        }
    
    async def get_agent_usage_breakdown(self, team_id: str, days: int = 30) -> Dict[str, Any]:
        """
        Get breakdown of usage by agent for a team.
        
        Args:
            team_id: ID of the team
            days: Number of days to look back
                
        Returns:
            Dictionary containing usage breakdown by agent
        """
        # Calculate time range
        end_time = time.time()
        start_time = end_time - (days * 24 * 60 * 60)
        
        # Get usage within time range
        usage_data = await self.get_token_usage(team_id, start_time, end_time)
        
        # Group by agent
        agent_breakdown = {}
        for usage in usage_data:
            agent_id = usage.agent_id
            
            # Initialize agent entry if needed
            if agent_id not in agent_breakdown:
                agent_breakdown[agent_id] = {
                    "prompt_tokens": 0,
                    "completion_tokens": 0,
                    "total_tokens": 0,
                    "cost": 0.0,
                    "requests": 0
                }
            
            # Update agent usage data
            agent_breakdown[agent_id]["prompt_tokens"] += usage.prompt_tokens
            agent_breakdown[agent_id]["completion_tokens"] += usage.completion_tokens
            agent_breakdown[agent_id]["total_tokens"] += usage.total_tokens
            agent_breakdown[agent_id]["cost"] += usage.estimated_cost
            agent_breakdown[agent_id]["requests"] += 1
        
        return {
            "team_id": team_id,
            "period": f"Last {days} days",
            "agents": agent_breakdown,
            "total_cost": sum(agent["cost"] for agent in agent_breakdown.values()),
            "total_tokens": sum(agent["total_tokens"] for agent in agent_breakdown.values()),
            "total_requests": sum(agent["requests"] for agent in agent_breakdown.values())
        }
    
    async def check_budget_availability(self, team_id: str, estimated_cost: float) -> Tuple[bool, Optional[str]]:
        """
        Check if budget is available for a team.
        
        Args:
            team_id: ID of the team
            estimated_cost: Estimated cost of the operation
                
        Returns:
            Tuple of (is_available, reason if not available)
        """
        # Find the active budget for this team
        team_budget = None
        now = time.time()
        
        for budget in self.budgets.values():
            if (budget.team_id == team_id and 
                budget.start_date <= now and
                (budget.end_date is None or budget.end_date >= now)):
                team_budget = budget
                break
        
        if not team_budget:
            return False, "No active budget found for team"
            
        if team_budget.remaining_budget <= 0:
            return False, "Budget depleted"
            
        if team_budget.remaining_budget < estimated_cost:
            return False, "Insufficient budget for operation"
            
        return True, None
    
    async def check_tier_availability(self, team_id: str, tier: str, estimated_cost: float) -> Tuple[bool, Optional[str]]:
        """
        Check if a specific tier is available within budget constraints.
        
        Args:
            team_id: ID of the team
            tier: The tier to check (e.g., "premium", "standard", "economy")
            estimated_cost: Estimated cost of the operation
                
        Returns:
            Tuple of (is_available, reason if not available)
        """
        # First check overall budget
        budget_available, reason = await self.check_budget_availability(team_id, estimated_cost)
        if not budget_available:
            return False, reason
            
        # Find the active budget for this team
        team_budget = None
        now = time.time()
        
        for budget in self.budgets.values():
            if (budget.team_id == team_id and 
                budget.start_date <= now and
                (budget.end_date is None or budget.end_date >= now)):
                team_budget = budget
                break
        
        # Check tier constraints if defined
        if team_budget and tier in team_budget.tier_constraints:
            tier_limit = team_budget.tier_constraints[tier]
            
            # Get usage for this tier today
            usage_today = await self._get_tier_usage_today(team_id, tier)
            
            if usage_today + estimated_cost > tier_limit:
                return False, f"Daily limit for {tier} tier exceeded"
        
        return True, None
    
    async def _get_tier_usage_today(self, team_id: str, tier: str) -> float:
        """
        Get the usage for a specific tier today.
        
        Args:
            team_id: ID of the team
            tier: The tier to check
                
        Returns:
            Total cost used for this tier today
        """
        # Map tiers to models
        tier_models = {
            "premium": ["gpt-4", "gpt-4o", "claude-3-opus"],
            "standard": ["gpt-4-turbo", "claude-3-sonnet"],
            "economy": ["gpt-3.5-turbo", "claude-3-haiku"]
        }
        
        if tier not in tier_models:
            return 0.0
            
        models = tier_models[tier]
        
        # Calculate today's range
        now = time.time()
        today_start = datetime.fromtimestamp(now).replace(hour=0, minute=0, second=0, microsecond=0).timestamp()
        
        # Get usage within time range
        usage_data = await self.get_token_usage(team_id, today_start, now)
        
        # Sum costs for models in the tier
        return sum(usage.estimated_cost for usage in usage_data if usage.model in models)
    
    async def close(self):
        """Close connections and clean up resources"""
        # Save state
        await self._save_state()
        
        # Close Redis connection if any
        if not self.local_mode and self.redis:
            self.redis.close()
            await self.redis.wait_closed()
            logger.info("Redis connection closed")

    async def create_topic_budget(self, budget_data: Dict[str, Any]) -> TopicBudget:
        """
        Create a new topic-specific budget.
        
        Args:
            budget_data: Dictionary containing budget information
                {
                    "team_id": str,
                    "topic_name": str,
                    "total_budget": float,
                    "start_date": float,
                    "end_date": Optional[float],
                    "alert_threshold": float
                }
                
        Returns:
            TopicBudget object representing the created budget
        """
        # Create TopicBudget object
        topic_budget = TopicBudget(**budget_data)
        topic_budget.remaining_budget = topic_budget.total_budget
        
        # Store budget
        key = f"topic_budget:{topic_budget.team_id}:{topic_budget.topic_name}"
        
        if self.local_mode:
            if not hasattr(self, "topic_budgets"):
                self.topic_budgets = {}
            self.topic_budgets[key] = topic_budget
        else:
            # Store in Redis if applicable
            if self.redis:
                await self.redis.set(key, json.dumps(topic_budget.dict()))
        
        logger.info(f"Created topic budget for team {topic_budget.team_id}, topic {topic_budget.topic_name}: ${topic_budget.total_budget:.2f}")
        
        return topic_budget

    async def get_topic_budget(self, team_id: str, topic_name: str) -> Optional[TopicBudget]:
        """
        Get a topic budget.
        
        Args:
            team_id: ID of the team
            topic_name: Name of the topic
            
        Returns:
            TopicBudget object or None if not found
        """
        key = f"topic_budget:{team_id}:{topic_name}"
        
        if self.local_mode:
            if not hasattr(self, "topic_budgets"):
                self.topic_budgets = {}
            return self.topic_budgets.get(key)
        else:
            if self.redis:
                data = await self.redis.get(key)
                if data:
                    return TopicBudget(**json.loads(data))
        return None

    async def update_topic_budget(self, team_id: str, topic_name: str, updates: Dict[str, Any]) -> Optional[TopicBudget]:
        """
        Update a topic budget.
        
        Args:
            team_id: ID of the team
            topic_name: Name of the topic
            updates: Dictionary containing fields to update
            
        Returns:
            Updated TopicBudget object or None if not found
        """
        topic_budget = await self.get_topic_budget(team_id, topic_name)
        if not topic_budget:
            logger.warning(f"Topic budget for team {team_id}, topic {topic_name} not found")
            return None
        
        # Track if total_budget was increased
        old_total = topic_budget.total_budget
        
        # Apply updates
        for key, value in updates.items():
            if hasattr(topic_budget, key):
                setattr(topic_budget, key, value)
        
        # If total budget increased, add to remaining budget
        if 'total_budget' in updates and updates['total_budget'] > old_total:
            topic_budget.remaining_budget += (updates['total_budget'] - old_total)
        
        # Store updated budget
        key = f"topic_budget:{team_id}:{topic_name}"
        
        if self.local_mode:
            if not hasattr(self, "topic_budgets"):
                self.topic_budgets = {}
            self.topic_budgets[key] = topic_budget
        else:
            if self.redis:
                await self.redis.set(key, json.dumps(topic_budget.dict()))
        
        logger.info(f"Updated topic budget for team {team_id}, topic {topic_name}")
        
        return topic_budget

    async def record_topic_usage(self, team_id: str, topic_name: str, cost: float) -> Tuple[bool, Optional[str]]:
        """
        Record usage against a topic budget.
        
        Args:
            team_id: ID of the team
            topic_name: Name of the topic
            cost: Cost to record
            
        Returns:
            Tuple of (success, message)
        """
        topic_budget = await self.get_topic_budget(team_id, topic_name)
        if not topic_budget:
            logger.warning(f"Topic budget for team {team_id}, topic {topic_name} not found")
            return False, "Topic budget not found"
        
        if topic_budget.status != "active":
            return False, f"Topic budget is {topic_budget.status}, not active"
        
        # Update remaining budget
        old_remaining = topic_budget.remaining_budget
        topic_budget.remaining_budget -= cost
        
        # Check for alerts
        percentage_used = 1 - (topic_budget.remaining_budget / topic_budget.total_budget)
        alerts_triggered = []
        
        # Threshold alert
        if percentage_used >= topic_budget.alert_threshold and old_remaining > topic_budget.total_budget * (1 - topic_budget.alert_threshold):
            alert = SpendingAlert(
                team_id=topic_budget.team_id,
                budget_id=topic_budget.budget_id,
                alert_type="topic_threshold",
                message=f"Topic budget threshold of {topic_budget.alert_threshold*100}% reached for {topic_name}",
                current_spending=topic_budget.total_budget - topic_budget.remaining_budget,
                budget_limit=topic_budget.total_budget,
                percentage_used=percentage_used,
                topic_name=topic_name
            )
            
            await self._send_alert(alert)
            alerts_triggered.append("threshold")
        
        # Budget depleted alert
        if topic_budget.remaining_budget <= 0 and old_remaining > 0:
            alert = SpendingAlert(
                team_id=topic_budget.team_id,
                budget_id=topic_budget.budget_id,
                alert_type="topic_depleted",
                message=f"Topic budget depleted for {topic_name}",
                current_spending=topic_budget.total_budget,
                budget_limit=topic_budget.total_budget,
                percentage_used=1.0,
                topic_name=topic_name
            )
            
            await self._send_alert(alert)
            
            # Auto-pause the topic budget
            topic_budget.status = "paused"
            alerts_triggered.append("depleted")
        
        # Store updated budget
        key = f"topic_budget:{team_id}:{topic_name}"
        
        if self.local_mode:
            if not hasattr(self, "topic_budgets"):
                self.topic_budgets = {}
            self.topic_budgets[key] = topic_budget
        else:
            if self.redis:
                await self.redis.set(key, json.dumps(topic_budget.dict()))
        
        if alerts_triggered:
            return True, f"Recorded usage and triggered alerts: {', '.join(alerts_triggered)}"
        return True, "Recorded usage successfully"
    
    async def get_all_topic_budgets(self, team_id: str) -> List[TopicBudget]:
        """
        Get all topic budgets for a team.
        
        Args:
            team_id: ID of the team
            
        Returns:
            List of TopicBudget objects
        """
        if self.local_mode:
            if not hasattr(self, "topic_budgets"):
                self.topic_budgets = {}
            
            prefix = f"topic_budget:{team_id}:"
            return [budget for key, budget in self.topic_budgets.items() if key.startswith(prefix)]
        else:
            if self.redis:
                keys = await self.redis.keys(f"topic_budget:{team_id}:*")
                budgets = []
                
                for key in keys:
                    data = await self.redis.get(key)
                    if data:
                        budgets.append(TopicBudget(**json.loads(data)))
                
                return budgets
        
        return []

    async def pause_topic_budget(self, team_id: str, topic_name: str) -> bool:
        """
        Pause a topic budget to prevent further spending.
        
        Args:
            team_id: ID of the team
            topic_name: Name of the topic
            
        Returns:
            True if successful
        """
        topic_budget = await self.get_topic_budget(team_id, topic_name)
        if not topic_budget:
            return False
        
        topic_budget.status = "paused"
        
        # Store updated budget
        key = f"topic_budget:{team_id}:{topic_name}"
        
        if self.local_mode:
            if not hasattr(self, "topic_budgets"):
                self.topic_budgets = {}
            self.topic_budgets[key] = topic_budget
        else:
            if self.redis:
                await self.redis.set(key, json.dumps(topic_budget.dict()))
        
        logger.info(f"Paused topic budget for team {team_id}, topic {topic_name}")
        
        return True

    async def resume_topic_budget(self, team_id: str, topic_name: str) -> bool:
        """
        Resume a paused topic budget.
        
        Args:
            team_id: ID of the team
            topic_name: Name of the topic
            
        Returns:
            True if successful
        """
        topic_budget = await self.get_topic_budget(team_id, topic_name)
        if not topic_budget:
            return False
        
        topic_budget.status = "active"
        
        # Store updated budget
        key = f"topic_budget:{team_id}:{topic_name}"
        
        if self.local_mode:
            if not hasattr(self, "topic_budgets"):
                self.topic_budgets = {}
            self.topic_budgets[key] = topic_budget
        else:
            if self.redis:
                await self.redis.set(key, json.dumps(topic_budget.dict()))
        
        logger.info(f"Resumed topic budget for team {team_id}, topic {topic_name}")
        
        return True

    async def get_topic_spending(self, team_id: str, topic_name: str, 
                          days: int = 30) -> Dict[str, float]:
        """
        Get daily spending for a specific topic.
        
        Args:
            team_id: ID of the team
            topic_name: Name of the topic
            days: Number of days to look back
            
        Returns:
            Dictionary mapping dates to spending amounts
        """
        now = time.time()
        days_ago = now - (days * 24 * 3600)
        daily_spending = {}
        
        if self.local_mode:
            # Group token usage by day
            for usage in self.token_usage:
                if (usage.team_id == team_id and 
                    usage.timestamp >= days_ago and 
                    getattr(usage, 'topic_name', None) == topic_name):
                    
                    # Convert timestamp to date string
                    date_str = datetime.fromtimestamp(usage.timestamp).strftime('%Y-%m-%d')
                    
                    if date_str not in daily_spending:
                        daily_spending[date_str] = 0.0
                        
                    daily_spending[date_str] += usage.estimated_cost
        else:
            # This would be implemented with a time-series query
            # For now, return an empty dict
            pass
        
        return daily_spending 