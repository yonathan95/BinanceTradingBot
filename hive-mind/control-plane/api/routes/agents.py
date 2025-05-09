"""
Agents API Routes
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from datetime import datetime

from db.database import get_db
from models.database import Agent, User, AgentRole, AgentTier
from auth.auth import get_current_active_user

router = APIRouter(prefix="/agents", tags=["agents"])


class AgentCreate:
    from pydantic import BaseModel
    
    class AgentCreate(BaseModel):
        name: str
        role: AgentRole
        model: str
        tier: AgentTier = AgentTier.STANDARD
        temperature: float = 0.7
        token_limit: int = 4096
        use_prompt_engineering: bool = False
        custom_settings: Dict[str, Any] = {}


class AgentUpdate:
    from pydantic import BaseModel
    
    class AgentUpdate(BaseModel):
        name: Optional[str] = None
        role: Optional[AgentRole] = None
        model: Optional[str] = None
        tier: Optional[AgentTier] = None
        temperature: Optional[float] = None
        token_limit: Optional[int] = None
        use_prompt_engineering: Optional[bool] = None
        custom_settings: Optional[Dict[str, Any]] = None


class AgentResponse:
    from pydantic import BaseModel
    from datetime import datetime
    
    class AgentResponse(BaseModel):
        id: str
        name: str
        role: str
        model: str
        tier: str
        temperature: float
        token_limit: int
        use_prompt_engineering: bool
        custom_settings: Dict[str, Any] = {}
        created_at: datetime
        updated_at: datetime
        
        class Config:
            orm_mode = True


@router.post("", response_model=AgentResponse.AgentResponse, status_code=status.HTTP_201_CREATED)
async def create_agent(
    agent: AgentCreate.AgentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Create a new agent
    """
    # Create the agent
    db_agent = Agent(
        name=agent.name,
        role=agent.role,
        model=agent.model,
        tier=agent.tier,
        temperature=agent.temperature,
        token_limit=agent.token_limit,
        use_prompt_engineering=agent.use_prompt_engineering,
        custom_settings=agent.custom_settings
    )
    
    db.add(db_agent)
    await db.commit()
    await db.refresh(db_agent)
    
    return db_agent


@router.get("", response_model=List[AgentResponse.AgentResponse])
async def list_agents(
    role: Optional[AgentRole] = None,
    tier: Optional[AgentTier] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000)
):
    """
    List agents with optional filtering by role and tier
    """
    # Build query with filters
    query = select(Agent)
    
    # Apply role filter if provided
    if role:
        query = query.where(Agent.role == role)
    
    # Apply tier filter if provided
    if tier:
        query = query.where(Agent.tier == tier)
    
    # Apply pagination
    query = query.offset(skip).limit(limit)
    
    # Execute query
    result = await db.execute(query)
    agents = result.scalars().all()
    
    return agents


@router.get("/{agent_id}", response_model=AgentResponse.AgentResponse)
async def get_agent(
    agent_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get agent details by ID
    """
    query = select(Agent).where(Agent.id == agent_id)
    result = await db.execute(query)
    agent = result.scalars().first()
    
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    return agent


@router.put("/{agent_id}", response_model=AgentResponse.AgentResponse)
async def update_agent(
    agent_id: str,
    agent_update: AgentUpdate.AgentUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Update an agent
    """
    query = select(Agent).where(Agent.id == agent_id)
    result = await db.execute(query)
    agent = result.scalars().first()
    
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    # Update agent fields
    update_data = agent_update.dict(exclude_unset=True)
    
    # Update custom_settings specially if provided
    custom_settings = update_data.pop("custom_settings", None)
    if custom_settings is not None:
        agent.custom_settings = custom_settings
    
    # Update the agent fields
    for key, value in update_data.items():
        setattr(agent, key, value)
    
    await db.commit()
    await db.refresh(agent)
    
    return agent


@router.get("/{agent_id}/tasks", response_model=List[Dict[str, Any]])
async def get_agent_tasks(
    agent_id: str,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get tasks assigned to an agent
    """
    # Check if agent exists
    query = select(Agent).where(Agent.id == agent_id)
    result = await db.execute(query)
    agent = result.scalars().first()
    
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    # Get tasks
    from models.database import Task
    query = select(Task).where(Task.assigned_to == agent_id)
    
    # Apply status filter if provided
    if status:
        query = query.where(Task.status == status)
    
    result = await db.execute(query)
    tasks = result.scalars().all()
    
    # Convert to response format
    task_responses = []
    for task in tasks:
        # Get tag names
        tag_names = [tag.name for tag in task.tags]
        
        task_responses.append({
            "id": task.id,
            "title": task.title,
            "description": task.description,
            "assigned_to": task.assigned_to,
            "project_id": task.project_id,
            "team_id": task.team_id,
            "status": task.status,
            "priority": task.priority,
            "type": task.type,
            "requires_validation": task.requires_validation,
            "success_criteria": task.success_criteria,
            "max_iterations": task.max_iterations,
            "iterations": task.iterations,
            "progress": task.progress,
            "due_date": task.due_date,
            "time_estimate": task.time_estimate,
            "tags": tag_names,
            "created_by": task.created_by,
            "created_at": task.created_at,
            "updated_at": task.updated_at
        })
    
    return task_responses


@router.get("/{agent_id}/teams", response_model=List[Dict[str, Any]])
async def get_agent_teams(
    agent_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get teams that an agent belongs to
    """
    # Check if agent exists
    query = select(Agent).where(Agent.id == agent_id)
    result = await db.execute(query)
    agent = result.scalars().first()
    
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    # Get teams
    teams = []
    for team in agent.teams:
        teams.append({
            "id": team.id,
            "name": team.name,
            "description": team.description,
            "workspace_id": team.workspace_id,
            "budget": team.budget,
            "created_by": team.created_by,
            "created_at": team.created_at,
            "updated_at": team.updated_at
        })
    
    return teams 