"""
Teams API routes
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query, Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, and_, or_
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

from db.database import get_db
from models.database import Team, Agent, Task, User, Budget, UserType, TaskStatus, AgentRole, AgentTier
from models.agents import TeamConfig, AgentConfig

router = APIRouter(
    prefix="/teams",
    tags=["teams"],
    responses={404: {"description": "Not found"}},
)

@router.get("/")
async def get_teams(
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = 10,
    search: Optional[str] = None,
    status: Optional[str] = None,
    workspace_id: Optional[str] = None,
):
    """
    Get a list of teams.
    Optionally filter by search term, status, or workspace.
    """
    query = select(Team)
    
    # Apply filters
    if workspace_id:
        query = query.where(Team.workspace_id == workspace_id)
    
    if search:
        query = query.where(
            or_(
                Team.name.ilike(f"%{search}%"),
                Team.description.ilike(f"%{search}%"),
            )
        )
    
    # Count total items for pagination
    count_query = select(func.count()).select_from(query.subquery())
    total = await db.execute(count_query)
    total_count = total.scalar() or 0
    
    # Apply pagination
    query = query.offset(skip).limit(limit)
    
    # Execute query
    result = await db.execute(query)
    teams = result.scalars().all()
    
    # Fetch additional data for each team
    team_data = []
    for team in teams:
        # Count agents
        agent_count_query = select(func.count())\
            .select_from(Team.__table__.join(Team.agents))\
            .where(Team.id == team.id)
        agent_result = await db.execute(agent_count_query)
        agent_count = agent_result.scalar() or 0
        
        # Count tasks
        task_count_query = select(func.count())\
            .select_from(Task)\
            .where(Task.team_id == team.id)
        task_result = await db.execute(task_count_query)
        task_count = task_result.scalar() or 0
        
        # Get budget info
        budget_query = select(Budget).where(Budget.team_id == team.id)
        budget_result = await db.execute(budget_query)
        budget = budget_result.scalars().first()
        
        # Get last active task timestamp
        last_active_query = select(func.max(Task.updated_at))\
            .where(Task.team_id == team.id)
        last_active_result = await db.execute(last_active_query)
        last_active = last_active_result.scalar()
        
        # Get agent roles
        roles_query = select(Agent.role)\
            .join(Team.agents)\
            .where(Team.id == team.id)\
            .distinct()
        roles_result = await db.execute(roles_query)
        roles = [role[0].value for role in roles_result.all()]
        
        # Determine team status based on active tasks
        active_tasks_query = select(func.count())\
            .select_from(Task)\
            .where(
                Task.team_id == team.id,
                Task.status.in_([
                    TaskStatus.ASSIGNED,
                    TaskStatus.IN_PROGRESS,
                    TaskStatus.WAITING_FOR_REVIEW,
                    TaskStatus.REVISION_NEEDED
                ])
            )
        active_tasks_result = await db.execute(active_tasks_query)
        active_tasks_count = active_tasks_result.scalar() or 0
        
        team_status = "active" if active_tasks_count > 0 else "idle"
        
        # Determine model tier based on agents
        tier_query = select(func.max(Agent.tier))\
            .join(Team.agents)\
            .where(Team.id == team.id)
        tier_result = await db.execute(tier_query)
        tier = tier_result.scalar() or AgentTier.STANDARD
        
        # Add to result
        team_data.append({
            "id": team.id,
            "name": team.name,
            "description": team.description,
            "agents": agent_count,
            "tasks": task_count,
            "lastActive": last_active.isoformat() if last_active else None,
            "status": team_status,
            "roles": roles,
            "model_tier": tier.value,
            "budget_limit": budget.total_budget if budget else 0,
            "budget_used": budget.total_budget - budget.remaining_budget if budget else 0
        })
    
    return {
        "items": team_data,
        "total": total_count,
        "page": skip // limit + 1,
        "size": limit,
        "pages": (total_count + limit - 1) // limit
    }

@router.get("/{team_id}")
async def get_team(
    team_id: str = Path(..., description="The ID of the team to get"),
    db: AsyncSession = Depends(get_db),
):
    """
    Get details for a specific team.
    """
    # Get team
    team_query = select(Team).where(Team.id == team_id)
    team_result = await db.execute(team_query)
    team = team_result.scalars().first()
    
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    
    # Get budget info
    budget_query = select(Budget).where(Budget.team_id == team_id)
    budget_result = await db.execute(budget_query)
    budget = budget_result.scalars().first()
    
    # Get agents
    agents_query = select(Agent).join(Team.agents).where(Team.id == team_id)
    agents_result = await db.execute(agents_query)
    agents = agents_result.scalars().all()
    
    # Get agent roles and tiers
    roles = [agent.role.value for agent in agents]
    tiers = set(agent.tier.value for agent in agents)
    
    # Get task data
    task_status_query = select(Task.status, func.count())\
        .where(Task.team_id == team_id)\
        .group_by(Task.status)
    task_status_result = await db.execute(task_status_query)
    task_status_counts = {status.value: count for status, count in task_status_result.all()}
    
    # Get total tasks
    task_count_query = select(func.count())\
        .select_from(Task)\
        .where(Task.team_id == team_id)
    task_count_result = await db.execute(task_count_query)
    task_count = task_count_result.scalar() or 0
    
    # Get last active task timestamp
    last_active_query = select(func.max(Task.updated_at))\
        .where(Task.team_id == team_id)
    last_active_result = await db.execute(last_active_query)
    last_active = last_active_result.scalar()
    
    # Determine team status based on active tasks
    active_tasks_query = select(func.count())\
        .select_from(Task)\
        .where(
            Task.team_id == team_id,
            Task.status.in_([
                TaskStatus.ASSIGNED,
                TaskStatus.IN_PROGRESS,
                TaskStatus.WAITING_FOR_REVIEW,
                TaskStatus.REVISION_NEEDED
            ])
        )
    active_tasks_result = await db.execute(active_tasks_query)
    active_tasks_count = active_tasks_result.scalar() or 0
    
    team_status = "active" if active_tasks_count > 0 else "idle"
    
    # Build response
    team_data = {
        "id": team.id,
        "name": team.name,
        "description": team.description,
        "workspace_id": team.workspace_id,
        "created_at": team.created_at.isoformat() if team.created_at else None,
        "updated_at": team.updated_at.isoformat() if team.updated_at else None,
        "agents": {
            "count": len(agents),
            "roles": roles,
            "items": [
                {
                    "id": agent.id,
                    "name": agent.name,
                    "role": agent.role.value,
                    "model": agent.model,
                    "tier": agent.tier.value
                }
                for agent in agents
            ]
        },
        "tasks": {
            "count": task_count,
            "status": task_status_counts,
            "active": active_tasks_count
        },
        "status": team_status,
        "lastActive": last_active.isoformat() if last_active else None,
        "budget": {
            "total": budget.total_budget if budget else 0,
            "remaining": budget.remaining_budget if budget else 0,
            "used": budget.total_budget - budget.remaining_budget if budget else 0,
            "percentage_used": (
                (budget.total_budget - budget.remaining_budget) / budget.total_budget * 100
                if budget and budget.total_budget > 0 else 0
            )
        },
        "model_tier": max(tiers) if tiers else AgentTier.STANDARD.value
    }
    
    return team_data

@router.post("/")
async def create_team(
    team_config: TeamConfig,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new team with agent configurations.
    """
    # Create team record
    team = Team(
        name=team_config.name,
        description=team_config.description,
        workspace_id=team_config.workspace_id,
        budget=team_config.budget,
        created_by=team_config.created_by
    )
    
    db.add(team)
    await db.flush()
    
    # Create budget for the team
    if team_config.budget:
        budget = Budget(
            team_id=team.id,
            total_budget=team_config.budget,
            remaining_budget=team_config.budget,
            start_date=datetime.now(),
            end_date=datetime.now() + timedelta(days=90),  # Default 90-day budget period
            alert_threshold=0.8
        )
        db.add(budget)
    
    # Create agents
    for agent_config in team_config.agents:
        agent = Agent(
            name=f"{agent_config.role.value.title()} Agent",
            role=agent_config.role,
            model=agent_config.model,
            tier=agent_config.tier,
            temperature=agent_config.temperature,
            token_limit=agent_config.token_limit,
            use_prompt_engineering=agent_config.use_prompt_engineering,
            custom_settings=agent_config.custom_settings
        )
        db.add(agent)
        await db.flush()
        
        # Add to team
        team.agents.append(agent)
    
    await db.commit()
    
    # Start any background processing needed
    background_tasks.add_task(
        initialize_team_resources, 
        team_id=team.id, 
        workspace_id=team_config.workspace_id
    )
    
    return {
        "id": team.id,
        "name": team.name,
        "agent_count": len(team_config.agents),
        "created_at": team.created_at.isoformat() if team.created_at else None
    }

async def initialize_team_resources(team_id: str, workspace_id: str):
    """Background task to initialize team resources"""
    # This would be implemented to set up any additional resources needed
    # such as code repositories, communication channels, etc.
    pass

@router.put("/{team_id}")
async def update_team(
    team_update: Dict[str, Any],
    team_id: str = Path(..., description="The ID of the team to update"),
    db: AsyncSession = Depends(get_db),
):
    """
    Update a team's details.
    """
    # Get team
    team_query = select(Team).where(Team.id == team_id)
    team_result = await db.execute(team_query)
    team = team_result.scalars().first()
    
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    
    # Update fields
    if "name" in team_update:
        team.name = team_update["name"]
    
    if "description" in team_update:
        team.description = team_update["description"]
    
    if "budget" in team_update:
        team.budget = team_update["budget"]
        
        # Update or create budget record
        budget_query = select(Budget).where(Budget.team_id == team_id)
        budget_result = await db.execute(budget_query)
        budget = budget_result.scalars().first()
        
        if budget:
            # If budget is increasing, add to remaining
            if team_update["budget"] > budget.total_budget:
                budget.remaining_budget += (team_update["budget"] - budget.total_budget)
            budget.total_budget = team_update["budget"]
        else:
            # Create new budget
            budget = Budget(
                team_id=team.id,
                total_budget=team_update["budget"],
                remaining_budget=team_update["budget"],
                start_date=datetime.now(),
                end_date=datetime.now() + timedelta(days=90),
                alert_threshold=0.8
            )
            db.add(budget)
    
    # Update agent configurations if provided
    if "agents" in team_update:
        # Handle agent updates - this would need more complex logic in a real implementation
        # For example, checking which agents to add, update, or remove
        pass
    
    await db.commit()
    
    return {
        "id": team.id,
        "name": team.name,
        "updated_at": team.updated_at.isoformat()
    }

@router.delete("/{team_id}")
async def delete_team(
    team_id: str = Path(..., description="The ID of the team to delete"),
    db: AsyncSession = Depends(get_db),
):
    """
    Delete a team.
    """
    # Get team
    team_query = select(Team).where(Team.id == team_id)
    team_result = await db.execute(team_query)
    team = team_result.scalars().first()
    
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    
    # Check if there are active tasks
    active_tasks_query = select(func.count())\
        .select_from(Task)\
        .where(
            Task.team_id == team_id,
            Task.status.in_([
                TaskStatus.ASSIGNED,
                TaskStatus.IN_PROGRESS,
                TaskStatus.WAITING_FOR_REVIEW,
                TaskStatus.REVISION_NEEDED
            ])
        )
    active_tasks_result = await db.execute(active_tasks_query)
    active_tasks_count = active_tasks_result.scalar() or 0
    
    if active_tasks_count > 0:
        raise HTTPException(
            status_code=400, 
            detail=f"Cannot delete team with {active_tasks_count} active tasks"
        )
    
    # Delete budget records
    budget_query = select(Budget).where(Budget.team_id == team_id)
    budget_result = await db.execute(budget_query)
    budget = budget_result.scalars().first()
    
    if budget:
        await db.delete(budget)
    
    # Delete team (will cascade to agent associations)
    await db.delete(team)
    await db.commit()
    
    return {"status": "success", "message": f"Team {team_id} deleted"}

@router.get("/{team_id}/agents")
async def get_team_agents(
    team_id: str = Path(..., description="The ID of the team"),
    db: AsyncSession = Depends(get_db),
):
    """
    Get all agents for a specific team.
    """
    # Verify team exists
    team_query = select(Team).where(Team.id == team_id)
    team_result = await db.execute(team_query)
    team = team_result.scalars().first()
    
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    
    # Get agents
    agents_query = select(Agent).join(Team.agents).where(Team.id == team_id)
    agents_result = await db.execute(agents_query)
    agents = agents_result.scalars().all()
    
    return {
        "team_id": team_id,
        "team_name": team.name,
        "agents": [
            {
                "id": agent.id,
                "name": agent.name,
                "role": agent.role.value,
                "model": agent.model,
                "tier": agent.tier.value,
                "temperature": agent.temperature,
                "token_limit": agent.token_limit,
                "use_prompt_engineering": agent.use_prompt_engineering
            }
            for agent in agents
        ]
    } 