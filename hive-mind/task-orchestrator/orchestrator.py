import asyncio
import json
import os
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import yaml
import aioredis

# Configure logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("task_orchestrator")

class TaskOrchestrator:
    """
    Task Orchestrator & Tier Router for the Hive Mind system.
    Handles task assignment, dependency resolution, and model tier selection.
    """
    
    def __init__(self, redis_url: str, tier_config_path: str = "config/tiers.yaml"):
        """
        Initialize the Task Orchestrator
        
        Args:
            redis_url: URL for Redis connection
            tier_config_path: Path to the tier configuration YAML file
        """
        self.redis_url = redis_url
        self.redis = None  # Will be initialized in start()
        self.tier_config_path = tier_config_path
        self.tiers = {}
        self.routing_rules = []
        self.task_queue = {}
        self.active_tasks = {}
        self.agent_stats = {}
    
    async def start(self):
        """
        Start the Task Orchestrator
        """
        # Connect to Redis
        self.redis = await aioredis.create_redis_pool(self.redis_url)
        logger.info("Connected to Redis")
        
        # Load tier configuration
        await self.load_tier_config()
        
        # Start the task processor
        asyncio.create_task(self.process_task_queue())
        
        logger.info("Task Orchestrator started")
    
    async def stop(self):
        """
        Stop the Task Orchestrator
        """
        if self.redis:
            self.redis.close()
            await self.redis.wait_closed()
            logger.info("Redis connection closed")
    
    async def load_tier_config(self):
        """
        Load tier and routing configuration from YAML file
        """
        try:
            with open(self.tier_config_path, 'r') as f:
                config = yaml.safe_load(f)
                
            self.tiers = config.get('tiers', {})
            self.routing_rules = config.get('routing_rules', [])
            
            logger.info(f"Loaded tier configuration with {len(self.tiers)} tiers and {len(self.routing_rules)} routing rules")
        except Exception as e:
            logger.error(f"Error loading tier configuration: {str(e)}")
            # Set up default configuration
            self.tiers = {
                "prod_mgmt": {
                    "model": "gpt-3.5-turbo",
                    "max_tokens": 2048,
                    "temperature": 0.2,
                    "cost_per_1k_tokens": 0.0015
                },
                "standard": {
                    "model": "gpt-4o",
                    "max_tokens": 4096,
                    "temperature": 0.7,
                    "cost_per_1k_tokens": 0.01
                },
                "premium": {
                    "model": "claude-3-opus",
                    "max_tokens": 8000,
                    "temperature": 0.7,
                    "cost_per_1k_tokens": 0.03
                }
            }
            self.routing_rules = [
                {"when": "complexity == 'L'", "use": "prod_mgmt"},
                {"when": "complexity == 'M'", "use": "standard"},
                {"when": "complexity == 'H' and budget > 5.0", "use": "premium"},
                {"when": "complexity == 'H' and budget <= 5.0", "use": "standard"}
            ]
            logger.info("Using default tier configuration")
    
    async def create_task(self, task_data: Dict[str, Any]) -> str:
        """
        Create a new task
        
        Args:
            task_data: Task details including goal, complexity, budget, etc.
            
        Returns:
            Task ID
        """
        # Generate task ID if not provided
        task_id = task_data.get("id", f"task-{datetime.utcnow().timestamp()}")
        
        # Ensure required fields
        required_fields = ["goal", "complexity", "owner_team"]
        for field in required_fields:
            if field not in task_data:
                raise ValueError(f"Missing required field: {field}")
        
        # Set default values
        task_data.setdefault("budget", 2.0)  # Default budget in USD
        task_data.setdefault("dependencies", [])
        task_data.setdefault("status", "pending")
        task_data.setdefault("created_at", datetime.utcnow().isoformat())
        
        # Select tier
        tier = await self.choose_tier(task_data["complexity"], task_data["budget"])
        task_data["tier"] = tier
        task_data["model"] = self.tiers[tier]["model"]
        task_data["max_tokens"] = self.tiers[tier]["max_tokens"]
        task_data["temperature"] = self.tiers[tier]["temperature"]
        
        # Store task
        await self.redis.set(
            f"task:{task_id}", 
            json.dumps(task_data),
            expire=86400 * 7  # Keep for 7 days
        )
        
        # Add to queue if it has no dependencies or all dependencies are completed
        dependency_status = await self.check_dependencies(task_data["dependencies"])
        if dependency_status["ready"]:
            await self.add_to_queue(task_id, task_data)
        
        logger.info(f"Created task {task_id} with tier {tier}")
        return task_id
    
    async def add_to_queue(self, task_id: str, task_data: Dict[str, Any]):
        """
        Add a task to the queue
        
        Args:
            task_id: Task ID
            task_data: Task details
        """
        # Update status
        task_data["status"] = "queued"
        await self.redis.set(
            f"task:{task_id}", 
            json.dumps(task_data)
        )
        
        # Add to appropriate queue based on priority
        priority = task_data.get("priority", "normal")
        await self.redis.zadd(
            "task_queue",
            self._get_priority_score(priority),
            task_id
        )
        
        logger.info(f"Added task {task_id} to queue with priority {priority}")
    
    def _get_priority_score(self, priority: str) -> float:
        """
        Get a numeric score for a priority level (lower is higher priority)
        
        Args:
            priority: Priority level (high, normal, low)
            
        Returns:
            Numeric score
        """
        now = datetime.utcnow().timestamp()
        if priority == "high":
            return now - 1000000  # High priority tasks get a lower timestamp
        elif priority == "low":
            return now + 1000000  # Low priority tasks get a higher timestamp
        else:  # normal
            return now
    
    async def process_task_queue(self):
        """
        Process the task queue continuously
        """
        while True:
            try:
                # Get the highest priority task
                task_result = await self.redis.zpopmin("task_queue", 1)
                
                if not task_result:
                    # Queue is empty, wait and try again
                    await asyncio.sleep(1)
                    continue
                
                # Extract task ID from result
                task_id_bytes = task_result[0][0]
                task_id = task_id_bytes.decode("utf-8")
                
                # Get task data
                task_data_bytes = await self.redis.get(f"task:{task_id}")
                if not task_data_bytes:
                    logger.warning(f"Task {task_id} not found in Redis")
                    continue
                
                task_data = json.loads(task_data_bytes)
                
                # Check if dependencies are satisfied
                dependency_status = await self.check_dependencies(task_data.get("dependencies", []))
                if not dependency_status["ready"]:
                    # Re-queue with a delay
                    logger.info(f"Task {task_id} has unmet dependencies, re-queueing")
                    await asyncio.sleep(5)
                    await self.redis.zadd(
                        "task_queue",
                        self._get_priority_score(task_data.get("priority", "normal")),
                        task_id
                    )
                    continue
                
                # Assign the task to an agent
                assigned_agent = await self.assign_task(task_data)
                
                # Update task status
                task_data["status"] = "assigned"
                task_data["assigned_to"] = assigned_agent
                task_data["assigned_at"] = datetime.utcnow().isoformat()
                
                await self.redis.set(
                    f"task:{task_id}", 
                    json.dumps(task_data)
                )
                
                # Publish task assignment event
                await self.redis.publish(
                    "task_events",
                    json.dumps({
                        "event": "task_assigned",
                        "task_id": task_id,
                        "agent_id": assigned_agent,
                        "timestamp": datetime.utcnow().isoformat()
                    })
                )
                
                logger.info(f"Assigned task {task_id} to agent {assigned_agent}")
                
                # Add to active tasks
                self.active_tasks[task_id] = {
                    "agent_id": assigned_agent,
                    "started_at": datetime.utcnow().isoformat()
                }
                
            except Exception as e:
                logger.error(f"Error processing task queue: {str(e)}")
                await asyncio.sleep(5)  # Wait before retrying
    
    async def choose_tier(self, complexity: str, budget: float) -> str:
        """
        Choose the appropriate tier based on task complexity and budget
        
        Args:
            complexity: Task complexity (L, M, H)
            budget: Task budget in USD
            
        Returns:
            Tier name
        """
        # Apply routing rules
        for rule in self.routing_rules:
            when_clause = rule["when"]
            
            # Simple evaluation (in production, use a proper expression evaluator)
            try:
                # Replace variables with their values
                eval_clause = when_clause.replace("complexity", f"'{complexity}'")
                eval_clause = eval_clause.replace("budget", str(budget))
                
                if eval(eval_clause):
                    return rule["use"]
            except Exception as e:
                logger.error(f"Error evaluating rule '{when_clause}': {str(e)}")
        
        # Default to prod_mgmt tier
        return "prod_mgmt"
    
    async def check_dependencies(self, dependency_ids: List[str]) -> Dict[str, Any]:
        """
        Check if all dependencies are satisfied
        
        Args:
            dependency_ids: List of task IDs that this task depends on
            
        Returns:
            Status of dependency check
        """
        if not dependency_ids:
            return {"ready": True, "pending": []}
        
        pending_dependencies = []
        
        for dep_id in dependency_ids:
            dep_data_bytes = await self.redis.get(f"task:{dep_id}")
            if not dep_data_bytes:
                # Dependency not found, consider it pending
                pending_dependencies.append(dep_id)
                continue
            
            dep_data = json.loads(dep_data_bytes)
            if dep_data.get("status") != "completed":
                pending_dependencies.append(dep_id)
        
        return {
            "ready": len(pending_dependencies) == 0,
            "pending": pending_dependencies
        }
    
    async def update_agent_stats(self, agent_id: str, token_count: int, latency_ms: int):
        """
        Update agent statistics for load balancing
        
        Args:
            agent_id: ID of the agent
            token_count: Number of tokens processed
            latency_ms: Processing latency in milliseconds
        """
        now = datetime.utcnow().timestamp()
        
        # Store recent token usage
        await self.redis.zadd(
            f"agent:{agent_id}:tokens",
            now,
            token_count
        )
        
        # Expire old entries (keep last 5 minutes)
        five_min_ago = now - 300
        await self.redis.zremrangebyscore(
            f"agent:{agent_id}:tokens",
            0,
            five_min_ago
        )
        
        # Update latency
        await self.redis.zadd(
            f"agent:{agent_id}:latency",
            now,
            latency_ms
        )
        
        # Expire old latency entries
        await self.redis.zremrangebyscore(
            f"agent:{agent_id}:latency",
            0,
            five_min_ago
        )
    
    async def get_agent_token_rate(self, agent_id: str) -> float:
        """
        Get the recent token usage rate for an agent
        
        Args:
            agent_id: ID of the agent
            
        Returns:
            Tokens processed in the last 5 minutes
        """
        now = datetime.utcnow().timestamp()
        five_min_ago = now - 300
        
        # Get token usage in the last 5 minutes
        token_entries = await self.redis.zrangebyscore(
            f"agent:{agent_id}:tokens",
            five_min_ago,
            now,
            withscores=True
        )
        
        # Sum the token count
        return sum(entry[0] for entry in token_entries)
    
    async def assign_task(self, task_data: Dict[str, Any]) -> str:
        """
        Assign a task to the most appropriate agent
        
        Args:
            task_data: Task details
            
        Returns:
            ID of the assigned agent
        """
        team_id = task_data["owner_team"]
        tier = task_data["tier"]
        
        # Get agents for this team and tier
        agent_pool = await self.get_available_agents(team_id, tier)
        
        if not agent_pool:
            logger.warning(f"No agents available for team {team_id} and tier {tier}")
            # Fall back to any agent in this team
            agent_pool = await self.get_available_agents(team_id)
            
            if not agent_pool:
                logger.error(f"No agents available for team {team_id}")
                # Return a placeholder agent ID
                return "no_agent_available"
        
        # Get token rates for all agents
        agent_rates = {}
        for agent_id in agent_pool:
            agent_rates[agent_id] = await self.get_agent_token_rate(agent_id)
        
        # Pick agent with lowest token rate
        if agent_rates:
            return min(agent_rates.items(), key=lambda x: x[1])[0]
        else:
            # If no stats available, pick the first agent
            return agent_pool[0]
    
    async def get_available_agents(self, team_id: str, tier: Optional[str] = None) -> List[str]:
        """
        Get available agents for a team and tier
        
        Args:
            team_id: ID of the team
            tier: Optional tier to filter by
            
        Returns:
            List of agent IDs
        """
        # In a real implementation, this would query a database
        # For now, return mock data
        
        # Get agent keys from Redis
        agent_keys = await self.redis.keys("agent:*:info")
        
        agents = []
        for key in agent_keys:
            agent_data_bytes = await self.redis.get(key)
            if agent_data_bytes:
                agent_data = json.loads(agent_data_bytes)
                
                # Check if agent belongs to the team
                if agent_data.get("team_id") == team_id:
                    # Check tier if specified
                    if tier is None or agent_data.get("tier") == tier:
                        agents.append(agent_data["id"])
        
        return agents
    
    async def task_completed(self, task_id: str, result: Dict[str, Any]):
        """
        Handle task completion
        
        Args:
            task_id: ID of the completed task
            result: Task result
        """
        # Get task data
        task_data_bytes = await self.redis.get(f"task:{task_id}")
        if not task_data_bytes:
            logger.warning(f"Task {task_id} not found in Redis")
            return
        
        task_data = json.loads(task_data_bytes)
        
        # Update task status
        task_data["status"] = "completed"
        task_data["completed_at"] = datetime.utcnow().isoformat()
        task_data["result"] = result
        
        await self.redis.set(
            f"task:{task_id}", 
            json.dumps(task_data)
        )
        
        # Remove from active tasks
        if task_id in self.active_tasks:
            del self.active_tasks[task_id]
        
        logger.info(f"Task {task_id} completed")
        
        # Check for dependent tasks
        await self.process_dependent_tasks(task_id)
    
    async def process_dependent_tasks(self, completed_task_id: str):
        """
        Check and queue tasks that depend on a completed task
        
        Args:
            completed_task_id: ID of the completed task
        """
        # This would be more efficient with a proper dependency graph
        # For now, we'll scan all tasks
        
        task_keys = await self.redis.keys("task:*")
        
        for key in task_keys:
            task_id = key.decode("utf-8").split(":")[1]
            task_data_bytes = await self.redis.get(key)
            
            if task_data_bytes:
                task_data = json.loads(task_data_bytes)
                
                # Check if this task depends on the completed task
                if completed_task_id in task_data.get("dependencies", []):
                    # Check if all dependencies are now satisfied
                    dependency_status = await self.check_dependencies(task_data.get("dependencies", []))
                    
                    if dependency_status["ready"] and task_data.get("status") == "pending":
                        # All dependencies satisfied, add to queue
                        await self.add_to_queue(task_id, task_data)
                        logger.info(f"Queued dependent task {task_id}")

# Run the orchestrator
if __name__ == "__main__":
    # Load configuration from environment
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
    
    async def main():
        orchestrator = TaskOrchestrator(redis_url)
        await orchestrator.start()
        
        try:
            # Keep the main coroutine running
            while True:
                await asyncio.sleep(3600)  # Sleep for an hour
        finally:
            await orchestrator.stop()
    
    asyncio.run(main()) 