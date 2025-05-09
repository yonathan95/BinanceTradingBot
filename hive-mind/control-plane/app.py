from fastapi import FastAPI, Depends, HTTPException, WebSocket, WebSocketDisconnect, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from typing import Dict, List, Any, Optional
import uuid
import json
import asyncio
from datetime import datetime
from pydantic import BaseModel, Field
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import API routes
from api.routes import researcher, auth, tasks, teams, agents

# Database initialization
from db.database import Base, engine

# API Models
class TeamCreate(BaseModel):
    name: str
    description: Optional[str] = None
    agent_ids: List[str]

class TeamResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    agent_ids: List[str]
    created_at: datetime

class TaskCreate(BaseModel):
    description: str
    assigned_to: str
    type: str
    requires_validation: bool = False
    success_criteria: Dict[str, Any] = {}
    max_iterations: int = 5

class TaskResponse(BaseModel):
    id: str
    description: str
    assigned_to: str
    type: str
    status: str
    requires_validation: bool
    success_criteria: Dict[str, Any] = {}
    max_iterations: int
    iterations: int
    created_at: datetime
    updated_at: datetime

# Initialize FastAPI app
app = FastAPI(title="Hive Mind Control Plane API")

# Setup CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api")
app.include_router(tasks.router, prefix="/api")
app.include_router(teams.router, prefix="/api")
app.include_router(agents.router, prefix="/api")
app.include_router(researcher.router)

# OAuth2 for authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# In-memory storage for demonstration (replace with database in production)
teams: Dict[str, Dict[str, Any]] = {}
tasks: Dict[str, Dict[str, Any]] = {}
active_connections: Dict[str, List[WebSocket]] = {}

# Helper function for mock authentication (replace with proper auth in production)
async def get_current_user(token: str = Depends(oauth2_scheme)):
    # Mock implementation - replace with actual auth logic
    return {"id": "user-1", "username": "admin"}

# Team management endpoints
@app.post("/teams", response_model=TeamResponse)
async def create_team(
    team: TeamCreate, 
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Create a new team with the specified configuration
    """
    team_id = f"team-{str(uuid.uuid4())}"
    team_data = {
        "id": team_id,
        "name": team.name,
        "description": team.description,
        "agent_ids": team.agent_ids,
        "created_at": datetime.utcnow(),
        "created_by": current_user["id"]
    }
    teams[team_id] = team_data
    
    # Broadcast team creation to connected clients
    await broadcast_event("team_created", team_data)
    
    return team_data

@app.get("/teams", response_model=List[TeamResponse])
async def list_teams(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    List all teams
    """
    return list(teams.values())

@app.get("/teams/{team_id}", response_model=TeamResponse)
async def get_team(
    team_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get team details by ID
    """
    if team_id not in teams:
        raise HTTPException(status_code=404, detail="Team not found")
    return teams[team_id]

# Task management endpoints
@app.post("/tasks", response_model=TaskResponse)
async def create_task(
    task: TaskCreate, 
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Create a new task
    """
    task_id = f"task-{str(uuid.uuid4())}"
    now = datetime.utcnow()
    task_data = {
        "id": task_id,
        "description": task.description,
        "assigned_to": task.assigned_to,
        "type": task.type,
        "status": "assigned",
        "requires_validation": task.requires_validation,
        "success_criteria": task.success_criteria,
        "max_iterations": task.max_iterations,
        "iterations": 0,
        "created_at": now,
        "updated_at": now,
        "created_by": current_user["id"]
    }
    tasks[task_id] = task_data
    
    # Broadcast task creation to connected clients
    await broadcast_event("task_created", task_data)
    
    return task_data

@app.get("/tasks", response_model=List[TaskResponse])
async def list_tasks(
    team_id: Optional[str] = None,
    status: Optional[str] = None,
    assigned_to: Optional[str] = None,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    List tasks with optional filtering
    """
    filtered_tasks = tasks.values()
    
    # Apply filters
    if team_id:
        filtered_tasks = [task for task in filtered_tasks if task.get("team_id") == team_id]
    if status:
        filtered_tasks = [task for task in filtered_tasks if task["status"] == status]
    if assigned_to:
        filtered_tasks = [task for task in filtered_tasks if task["assigned_to"] == assigned_to]
    
    return list(filtered_tasks)

@app.get("/tasks/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get task details by ID
    """
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    return tasks[task_id]

@app.put("/tasks/{task_id}/status", response_model=TaskResponse)
async def update_task_status(
    task_id: str,
    status: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Update the status of a task
    """
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task = tasks[task_id]
    task["status"] = status
    task["updated_at"] = datetime.utcnow()
    
    # Broadcast task update to connected clients
    await broadcast_event("task_updated", task)
    
    return task

@app.post("/tasks/{task_id}/feedback", response_model=TaskResponse)
async def submit_task_feedback(
    task_id: str,
    feedback: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Submit feedback for a task
    """
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task = tasks[task_id]
    task["feedback"] = task.get("feedback", []) + [feedback]
    task["iterations"] += 1
    task["updated_at"] = datetime.utcnow()
    
    # Update status based on iterations
    if task["iterations"] >= task["max_iterations"]:
        task["status"] = "failed"
    else:
        task["status"] = "revision_needed"
    
    # Broadcast task update to connected clients
    await broadcast_event("task_feedback", {
        "task_id": task_id,
        "feedback": feedback,
        "iterations": task["iterations"],
        "status": task["status"]
    })
    
    return task

# WebSocket connections
@app.websocket("/ws/events")
async def events_websocket(websocket: WebSocket):
    """
    WebSocket endpoint for real-time events
    """
    await websocket.accept()
    
    # Assign a connection ID
    connection_id = str(uuid.uuid4())
    
    # Initialize connection in active_connections if not exists
    if "events" not in active_connections:
        active_connections["events"] = []
    
    # Add connection to active connections
    active_connections["events"].append(websocket)
    
    try:
        # Keep connection alive
        while True:
            # Wait for message (keeps connection open)
            data = await websocket.receive_text()
            
            # Echo received data (optional)
            await websocket.send_text(f"Echo: {data}")
    except WebSocketDisconnect:
        # Remove connection when disconnected
        active_connections["events"].remove(websocket)

# Function to broadcast events to connected clients
async def broadcast_event(event_type: str, data: Any):
    """
    Broadcast event to all connected WebSocket clients
    """
    if "events" not in active_connections:
        return
    
    # Create event message
    event_message = {
        "type": event_type,
        "data": data,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    # Convert to JSON
    message = json.dumps(event_message)
    
    # Send to all connected clients
    for connection in active_connections["events"]:
        try:
            await connection.send_text(message)
        except:
            # Remove failed connections
            active_connections["events"].remove(connection)

# Health check endpoint
@app.get("/health")
async def health_check():
    """
    Health check endpoint
    """
    return {"status": "healthy", "timestamp": datetime.utcnow()}

# Setup database on startup
@app.on_event("startup")
async def startup_db():
    """
    Create database tables on startup
    """
    from sqlalchemy.ext.asyncio import AsyncEngine
    
    # Create tables
    async with engine.begin() as conn:
        # Import all models to ensure they're registered with Base.metadata
        from models.database import User, Agent, Team, Task, TaskComment, Project, Workspace, Tag, Budget, SpendingAlert, TopicBudget
        
        # Create tables
        # In production, use Alembic migrations instead
        await conn.run_sync(Base.metadata.create_all)
    
    print("Database tables created!")

# IMPORTANT: In a production environment, use Alembic for database migrations instead of
# creating tables directly. This approach is used here for simplicity.

# Run the application
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 