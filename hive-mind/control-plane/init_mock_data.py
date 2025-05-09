#!/usr/bin/env python3
"""
Script to initialize the database with mock data for testing
This script will create:
1. Several teams with different agent configurations
2. A mock project with different tasks in various states
3. Tasks assigned to agents with progress tracking
"""

import asyncio
import random
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from db.database import SessionLocal
from models.database import (
    User, Agent, Team, Project, Workspace, Task, Tag, TaskComment,
    UserType, AgentRole, AgentTier, TaskStatus, TaskPriority, Budget
)
from models.agents import AgentConfig, TeamConfig
from init_db import create_default_admin, create_default_workspace, create_default_tags

# Constants for mock data generation
AGENT_MODELS = {
    AgentTier.ECONOMY: ["gpt-3.5-turbo"],
    AgentTier.STANDARD: ["gpt-3.5-turbo-16k", "claude-instant-1"],
    AgentTier.PREMIUM: ["gpt-4o", "gpt-4-turbo", "claude-3-opus"]
}

TEAM_CONFIGS = [
    {
        "name": "Web App Development",
        "description": "Team focused on creating a modern React web application",
        "agents": [
            {"role": AgentRole.MANAGER, "tier": AgentTier.PREMIUM},
            {"role": AgentRole.PLANNER, "tier": AgentTier.PREMIUM},
            {"role": AgentRole.ARCHITECT, "tier": AgentTier.PREMIUM},
            {"role": AgentRole.CODER, "tier": AgentTier.STANDARD},
            {"role": AgentRole.TESTER, "tier": AgentTier.STANDARD}
        ],
        "budget": 200.0
    },
    {
        "name": "API Backend Team",
        "description": "Building a scalable FastAPI backend service",
        "agents": [
            {"role": AgentRole.MANAGER, "tier": AgentTier.PREMIUM},
            {"role": AgentRole.ARCHITECT, "tier": AgentTier.PREMIUM},
            {"role": AgentRole.CODER, "tier": AgentTier.STANDARD}
        ],
        "budget": 150.0
    },
    {
        "name": "ML Model Training",
        "description": "Developing and training machine learning models",
        "agents": [
            {"role": AgentRole.MANAGER, "tier": AgentTier.PREMIUM},
            {"role": AgentRole.PLANNER, "tier": AgentTier.PREMIUM},
            {"role": AgentRole.ARCHITECT, "tier": AgentTier.PREMIUM},
            {"role": AgentRole.CODER, "tier": AgentTier.PREMIUM},
            {"role": AgentRole.TESTER, "tier": AgentTier.STANDARD}
        ],
        "budget": 300.0
    }
]

PROJECTS = [
    {
        "name": "E-commerce Dashboard",
        "description": "A modern dashboard for managing e-commerce operations",
        "repository_url": "https://github.com/hive-mind/ecommerce-dashboard",
        "tasks": [
            {
                "title": "Set up React project structure",
                "description": "Initialize React project with TypeScript and configure folder structure",
                "priority": TaskPriority.HIGH,
                "status": TaskStatus.COMPLETED,
                "type": "setup",
                "time_estimate": 4.0,
                "progress": 100
            },
            {
                "title": "Create responsive UI components",
                "description": "Design and implement reusable UI components following Material Design",
                "priority": TaskPriority.MEDIUM,
                "status": TaskStatus.IN_PROGRESS,
                "type": "frontend",
                "time_estimate": 8.0,
                "progress": 60
            },
            {
                "title": "Implement authentication flow",
                "description": "Create login, registration, and password recovery flows",
                "priority": TaskPriority.HIGH,
                "status": TaskStatus.ASSIGNED,
                "type": "frontend",
                "time_estimate": 6.0,
                "progress": 20
            },
            {
                "title": "Set up API integration layer",
                "description": "Create service layer for API calls with error handling and caching",
                "priority": TaskPriority.MEDIUM,
                "status": TaskStatus.CREATED,
                "type": "frontend",
                "time_estimate": 5.0,
                "progress": 0
            },
            {
                "title": "Implement product management module",
                "description": "Create product CRUD operations and inventory management",
                "priority": TaskPriority.MEDIUM,
                "status": TaskStatus.CREATED,
                "type": "frontend",
                "time_estimate": 10.0,
                "progress": 0
            }
        ]
    },
    {
        "name": "Customer API Service",
        "description": "RESTful API service for customer management",
        "repository_url": "https://github.com/hive-mind/customer-api",
        "tasks": [
            {
                "title": "Design database schema",
                "description": "Create ER diagram and SQL schema for customer data",
                "priority": TaskPriority.HIGH,
                "status": TaskStatus.COMPLETED,
                "type": "database",
                "time_estimate": 6.0,
                "progress": 100
            },
            {
                "title": "Implement authentication middleware",
                "description": "Create JWT authentication and authorization middleware",
                "priority": TaskPriority.CRITICAL,
                "status": TaskStatus.IN_PROGRESS,
                "type": "backend",
                "time_estimate": 8.0,
                "progress": 70
            },
            {
                "title": "Create customer endpoints",
                "description": "Implement CRUD endpoints for customer data",
                "priority": TaskPriority.HIGH,
                "status": TaskStatus.ASSIGNED,
                "type": "backend",
                "time_estimate": 12.0,
                "progress": 30
            }
        ]
    }
]


async def create_agent(session, role, tier, team_id=None):
    """Create an agent with the specified role and tier"""
    model = random.choice(AGENT_MODELS[tier])
    name = f"{role.value.title()} Agent"
    
    agent = Agent(
        name=name,
        role=role,
        model=model,
        tier=tier,
        temperature=0.7 if role == AgentRole.CODER else 0.5,
        token_limit=8192 if tier == AgentTier.PREMIUM else 4096,
        use_prompt_engineering=random.choice([True, False]),
        custom_settings={"system_prompt": f"You are a specialized {role.value} agent."}
    )
    
    session.add(agent)
    await session.flush()
    
    print(f"Created agent: {agent.name} ({agent.role})")
    return agent


async def create_team(session, workspace, admin_user, team_config):
    """Create a team with the specified configuration"""
    team = Team(
        name=team_config["name"],
        description=team_config["description"],
        workspace_id=workspace.id,
        budget=team_config["budget"],
        created_by=admin_user.id
    )
    
    session.add(team)
    await session.flush()
    
    # Create agents for the team
    for agent_config in team_config["agents"]:
        agent = await create_agent(
            session, 
            agent_config["role"], 
            agent_config["tier"],
            team.id
        )
        team.agents.append(agent)
    
    # Create budget for the team
    budget = Budget(
        team_id=team.id,
        total_budget=team_config["budget"],
        remaining_budget=team_config["budget"] * 0.85,  # Some budget already used
        start_date=datetime.now() - timedelta(days=30),
        end_date=datetime.now() + timedelta(days=60),
        alert_threshold=0.8
    )
    
    session.add(budget)
    
    print(f"Created team: {team.name} with {len(team.agents)} agents")
    return team


async def create_project_with_tasks(session, workspace, admin_user, project_config, team):
    """Create a project with tasks"""
    project = Project(
        name=project_config["name"],
        description=project_config["description"],
        workspace_id=workspace.id,
        repository_url=project_config["repository_url"],
        created_by=admin_user.id,
        status="active"
    )
    
    session.add(project)
    await session.flush()
    
    # Get tags
    from sqlalchemy.future import select
    result = await session.execute(select(Tag))
    tags = result.scalars().all()
    
    # Create tasks
    for task_config in project_config["tasks"]:
        # Pick random tags
        task_tags = random.sample(tags, min(3, len(tags)))
        
        # Determine assignee based on status
        assignee = None
        if task_config["status"] not in [TaskStatus.CREATED, TaskStatus.COMPLETED]:
            # Find suitable agent for the task
            role = AgentRole.CODER
            if "type" in task_config:
                if task_config["type"] == "database":
                    role = AgentRole.ARCHITECT
                elif task_config["type"] == "setup":
                    role = AgentRole.PLANNER
            
            for agent in team.agents:
                if agent.role == role:
                    assignee = agent.id
                    break
        
        task = Task(
            title=task_config["title"],
            description=task_config["description"],
            assigned_to=assignee,
            created_by=admin_user.id,
            project_id=project.id,
            team_id=team.id,
            status=task_config["status"],
            priority=task_config["priority"],
            type=task_config.get("type", "task"),
            requires_validation=random.choice([True, False]),
            time_estimate=task_config["time_estimate"],
            progress=task_config["progress"],
            due_date=datetime.now() + timedelta(days=random.randint(7, 30))
        )
        
        for tag in task_tags:
            task.tags.append(tag)
        
        session.add(task)
        
        # Add comments if task is in progress
        if task.status in [TaskStatus.IN_PROGRESS, TaskStatus.COMPLETED]:
            for _ in range(random.randint(1, 3)):
                comment = TaskComment(
                    task_id=task.id,
                    author_id=assignee if assignee and random.random() > 0.3 else admin_user.id,
                    content=f"This is a mock comment for task: {task.title}"
                )
                session.add(comment)
    
    await session.flush()
    print(f"Created project: {project.name} with {len(project_config['tasks'])} tasks")
    return project


async def init_mock_data():
    """Initialize the database with mock data"""
    print("Initializing database with mock data...")
    
    async with SessionLocal() as session:
        # Create default admin user
        admin_user = await create_default_admin(session)
        
        # Create default workspace
        workspace = await create_default_workspace(session, admin_user)
        
        # Create default tags
        tags = await create_default_tags(session)
        
        # Create teams
        teams = []
        for team_config in TEAM_CONFIGS:
            team = await create_team(session, workspace, admin_user, team_config)
            teams.append(team)
        
        # Create projects with tasks
        for i, project_config in enumerate(PROJECTS):
            # Assign to a team (cycling through teams if more projects than teams)
            team = teams[i % len(teams)]
            project = await create_project_with_tasks(session, workspace, admin_user, project_config, team)
        
        # Commit all changes
        await session.commit()
    
    print("Mock data initialization complete!")


if __name__ == "__main__":
    asyncio.run(init_mock_data()) 