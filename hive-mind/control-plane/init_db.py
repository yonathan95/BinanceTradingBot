#!/usr/bin/env python3
"""
Script to initialize the database with some default data

This script will:
1. Create a default admin user
2. Create default agent types
3. Create default tags
4. Create a default workspace
"""

import asyncio
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import database models and utilities
from sqlalchemy.ext.asyncio import AsyncSession
from db.database import SessionLocal, engine, Base
from models.database import (
    User, Agent, Team, Project, Workspace, Tag, 
    UserType, AgentRole, AgentTier, TaskStatus, TaskPriority
)
from auth.auth import get_password_hash


async def init_db():
    """
    Initialize the database with default data
    """
    print("Initializing database with default data...")
    
    # Create a database session
    async with SessionLocal() as session:
        # Create default admin user if it doesn't exist
        admin_user = await create_default_admin(session)
        
        # Create default workspace if it doesn't exist
        workspace = await create_default_workspace(session, admin_user)
        
        # Create default agents if they don't exist
        agents = await create_default_agents(session)
        
        # Create default tags if they don't exist
        tags = await create_default_tags(session)
        
        # Create default team if it doesn't exist
        team = await create_default_team(session, workspace, admin_user, agents)
        
        # Create default project if it doesn't exist
        project = await create_default_project(session, workspace, admin_user)
        
        # Commit all changes
        await session.commit()
    
    print("Database initialization complete!")


async def create_default_admin(session: AsyncSession):
    """
    Create a default admin user if it doesn't exist
    """
    # Check if admin user exists
    from sqlalchemy.future import select
    result = await session.execute(select(User).where(User.username == "admin"))
    admin = result.scalars().first()
    
    if admin:
        print("Default admin user already exists")
        return admin
    
    # Create admin user
    admin = User(
        username="admin",
        email="admin@hivemind.ai",
        password_hash=get_password_hash("admin"),  # In production, use a secure password
        first_name="Admin",
        last_name="User",
        user_type=UserType.HUMAN,
        is_active=True
    )
    
    session.add(admin)
    await session.flush()
    
    print(f"Created default admin user: {admin.username}")
    return admin


async def create_default_workspace(session: AsyncSession, admin_user: User):
    """
    Create a default workspace if it doesn't exist
    """
    # Check if default workspace exists
    from sqlalchemy.future import select
    result = await session.execute(select(Workspace).where(Workspace.name == "Default Workspace"))
    workspace = result.scalars().first()
    
    if workspace:
        print("Default workspace already exists")
        return workspace
    
    # Create default workspace
    workspace = Workspace(
        name="Default Workspace",
        description="Default workspace for Hive Mind",
        created_by=admin_user.id
    )
    
    session.add(workspace)
    await session.flush()
    
    print(f"Created default workspace: {workspace.name}")
    return workspace


async def create_default_agents(session: AsyncSession):
    """
    Create default agents for each role if they don't exist
    """
    agents = []
    
    # Define agent configurations
    agent_configs = [
        {
            "name": "Manager Agent",
            "role": AgentRole.MANAGER,
            "model": "gpt-4o",
            "tier": AgentTier.PREMIUM
        },
        {
            "name": "Planner Agent",
            "role": AgentRole.PLANNER,
            "model": "gpt-4-turbo-preview",
            "tier": AgentTier.PREMIUM
        },
        {
            "name": "Architect Agent",
            "role": AgentRole.ARCHITECT,
            "model": "gpt-4-turbo-preview",
            "tier": AgentTier.PREMIUM
        },
        {
            "name": "Coder Agent",
            "role": AgentRole.CODER,
            "model": "gpt-4-turbo-preview",
            "tier": AgentTier.STANDARD
        },
        {
            "name": "Tester Agent",
            "role": AgentRole.TESTER,
            "model": "gpt-3.5-turbo",
            "tier": AgentTier.STANDARD
        },
        {
            "name": "Documentation Agent",
            "role": AgentRole.DOCUMENTATION,
            "model": "gpt-3.5-turbo",
            "tier": AgentTier.ECONOMY
        }
    ]
    
    # Create agents
    for config in agent_configs:
        # Check if agent exists
        from sqlalchemy.future import select
        result = await session.execute(
            select(Agent).where(
                Agent.name == config["name"], 
                Agent.role == config["role"]
            )
        )
        agent = result.scalars().first()
        
        if agent:
            print(f"Agent already exists: {agent.name}")
            agents.append(agent)
            continue
        
        # Create agent
        agent = Agent(
            name=config["name"],
            role=config["role"],
            model=config["model"],
            tier=config["tier"],
            temperature=0.7,
            token_limit=4096,
            use_prompt_engineering=False,
            custom_settings={}
        )
        
        session.add(agent)
        await session.flush()
        
        print(f"Created agent: {agent.name} ({agent.role})")
        agents.append(agent)
    
    return agents


async def create_default_tags(session: AsyncSession):
    """
    Create default tags if they don't exist
    """
    tags = []
    
    # Define tag configurations
    tag_configs = [
        {"name": "High Priority", "color": "#ff4d4f"},
        {"name": "Bug", "color": "#ff7a45"},
        {"name": "Feature", "color": "#73d13d"},
        {"name": "Enhancement", "color": "#40a9ff"},
        {"name": "Documentation", "color": "#9254de"},
        {"name": "Frontend", "color": "#ffa940"},
        {"name": "Backend", "color": "#36cfc9"},
        {"name": "Database", "color": "#597ef7"},
        {"name": "Security", "color": "#f759ab"},
        {"name": "Testing", "color": "#bae637"}
    ]
    
    # Create tags
    for config in tag_configs:
        # Check if tag exists
        from sqlalchemy.future import select
        result = await session.execute(select(Tag).where(Tag.name == config["name"]))
        tag = result.scalars().first()
        
        if tag:
            print(f"Tag already exists: {tag.name}")
            tags.append(tag)
            continue
        
        # Create tag
        tag = Tag(
            name=config["name"],
            color=config["color"]
        )
        
        session.add(tag)
        await session.flush()
        
        print(f"Created tag: {tag.name}")
        tags.append(tag)
    
    return tags


async def create_default_team(
    session: AsyncSession, 
    workspace: Workspace, 
    admin_user: User, 
    agents: list
):
    """
    Create a default team if it doesn't exist
    """
    # Check if default team exists
    from sqlalchemy.future import select
    result = await session.execute(select(Team).where(Team.name == "Core Team"))
    team = result.scalars().first()
    
    if team:
        print("Default team already exists")
        return team
    
    # Create default team
    team = Team(
        name="Core Team",
        description="Core engineering team with AI agents",
        workspace_id=workspace.id,
        budget=1000.0,  # Default budget
        created_by=admin_user.id
    )
    
    session.add(team)
    await session.flush()
    
    # Add agents to team
    for agent in agents:
        team.agents.append(agent)
    
    await session.flush()
    
    print(f"Created default team: {team.name} with {len(agents)} agents")
    return team


async def create_default_project(
    session: AsyncSession, 
    workspace: Workspace, 
    admin_user: User
):
    """
    Create a default project if it doesn't exist
    """
    # Check if default project exists
    from sqlalchemy.future import select
    result = await session.execute(select(Project).where(Project.name == "Hive Mind"))
    project = result.scalars().first()
    
    if project:
        print("Default project already exists")
        return project
    
    # Create default project
    project = Project(
        name="Hive Mind",
        description="Multi-agent AI engineering platform",
        workspace_id=workspace.id,
        repository_url="https://github.com/hivemind/hivemind",
        created_by=admin_user.id,
        status="active"
    )
    
    session.add(project)
    await session.flush()
    
    # Add admin user to project
    from sqlalchemy import insert
    from models.database import project_user_association
    
    await session.execute(
        insert(project_user_association).values(
            project_id=project.id,
            user_id=admin_user.id,
            role="owner"
        )
    )
    
    print(f"Created default project: {project.name}")
    return project


if __name__ == "__main__":
    asyncio.run(init_db()) 