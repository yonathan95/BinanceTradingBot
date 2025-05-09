"""
Hive Mind Control Plane - Main Application
"""

import logging
import os
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
import socketio
import asyncio

# Import API routes
from api.routes import tasks, agents, teams
from api.routes.vscode_controller import router as vscode_router, initialize_sio, initialize_agent_service

# Import agent modules
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from agents.manager.manager_agent import ManagerAgent

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Hive Mind Control Plane",
    description="API for controlling and coordinating Hive Mind agents and tasks",
    version="0.1.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create Socket.IO instance
sio = socketio.AsyncServer(
    async_mode='asgi',
    cors_allowed_origins=["*"]  # In production, replace with specific origins
)
socket_app = socketio.ASGIApp(sio)

# Mount Socket.IO app
app.mount("/socket.io", socket_app)

# Include API routes
app.include_router(tasks.router)
app.include_router(agents.router)
app.include_router(teams.router)
app.include_router(vscode_router)

# Agent system components
manager_agent = None

class AgentController:
    """Controller for agent communication"""
    
    async def send_vscode_message(self, client_id, message):
        """Send message to VS Code client"""
        from api.routes.vscode_controller import send_message_to_client
        await send_message_to_client(client_id, message)

@app.on_event("startup")
async def startup_event():
    """Initialize components on startup"""
    global manager_agent
    
    # Initialize the agent controller
    agent_controller = AgentController()
    
    # Initialize the manager agent
    manager_agent = ManagerAgent(agent_controller)
    
    # Connect manager agent to VS Code controller
    initialize_agent_service(manager_agent)
    
    # Start the manager agent
    await manager_agent.start()
    
    logger.info("Started Hive Mind manager agent")

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up on shutdown"""
    global manager_agent
    
    if manager_agent:
        await manager_agent.stop()
        logger.info("Stopped Hive Mind manager agent")

# Initialize Socket.IO handlers for VS Code controller
initialize_sio(sio)

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": "Hive Mind Control Plane",
        "version": "0.1.0",
        "status": "running"
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 5000))
    host = os.environ.get("HOST", "0.0.0.0")  # Listen on all network interfaces
    logger.info(f"Starting server on {host}:{port}")
    uvicorn.run("main:app", host=host, port=port, reload=True) 