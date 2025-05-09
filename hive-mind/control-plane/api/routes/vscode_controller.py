"""
VS Code Controller - Manages the interface between backend and VS Code clients
"""

import logging
import uuid
import time
import json
from typing import Dict, List, Any, Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel
from socketio import AsyncServer

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Models
class VSCodeClientRegistration(BaseModel):
    workspaceName: str
    workspacePath: str
    initialBranch: str

class BranchCheckout(BaseModel):
    branch: str
    commit: Optional[str] = None
    clientId: str
    message: Optional[str] = None

class ClientPermission(BaseModel):
    clientId: str
    allowed: bool
    reason: Optional[str] = None

class FileChange(BaseModel):
    path: str
    content: Optional[str]
    timestamp: str
    event: str  # 'change' or 'delete'

class FileChangeBatch(BaseModel):
    clientId: str
    changes: List[FileChange]
    timestamp: str

# Router
router = APIRouter(
    prefix="/api/vscode",
    tags=["vscode"],
    responses={404: {"description": "Not found"}},
)

# Store connected clients
vscode_clients = {}

# Store permission status for clients
# Key: client_id, Value: permission_status (True=allowed, False=denied)
vscode_permissions = {}

# Store file changes history
# Key: client_id, Value: List of file changes
vscode_file_changes = {}

# Mock clients for testing when actual clients aren't connected
def initialize_mock_clients():
    """Initialize mock clients for testing purposes"""
    mock_client_id = "mock-client-123"
    vscode_clients[mock_client_id] = {
        "workspace_name": "Mock Workspace",
        "workspace_path": "C:/projects/mock-workspace",
        "initial_branch": "main",
        "current_branch": "main",
        "current_commit": "abcdef1234567890",
        "connected": True,
        "sid": "mock-socket-id",
        "created_at": time.time(),
        "last_seen": time.time()
    }
    vscode_permissions[mock_client_id] = {
        "allowed": True,
        "last_updated": time.time(),
        "reason": "Mock client for testing"
    }
    logger.info(f"Initialized mock client: {mock_client_id}")
    return mock_client_id

# Socket.IO server instance (to be initialized by main app)
sio: Optional[AsyncServer] = None

# Reference to an agent message queue or service
agent_service = None

def initialize_sio(socketio_server: AsyncServer):
    """Initialize the Socket.IO server instance"""
    global sio
    sio = socketio_server
    
    @sio.event
    async def connect(sid, environ, auth):
        """Handle client connection"""
        client_id = environ.get('HTTP_X_CLIENT_ID') or environ.get('QUERY_STRING', '').split('clientId=')[-1].split('&')[0]
        logger.info(f"Socket.IO connection attempt from client ID: {client_id}")
        
        if client_id in vscode_clients:
            vscode_clients[client_id]['sid'] = sid
            vscode_clients[client_id]['connected'] = True
            vscode_clients[client_id]['last_seen'] = time.time()
            logger.info(f"VS Code client {client_id} connected with Socket.IO (sid: {sid})")
        else:
            logger.warning(f"Unknown VS Code client attempted to connect: {client_id}")
    
    @sio.event
    async def disconnect(sid):
        """Handle client disconnection"""
        disconnected_client_id = None
        for client_id, client in vscode_clients.items():
            if client.get('sid') == sid:
                client['connected'] = False
                client['last_seen'] = time.time()
                disconnected_client_id = client_id
                logger.info(f"VS Code client {client_id} disconnected (sid: {sid})")
                break
        
        if not disconnected_client_id:
            logger.warning(f"Unknown Socket.IO client disconnected (sid: {sid})")
    
    @sio.on('checkout-result')
    async def on_checkout_result(sid, data):
        """Handle checkout result from client"""
        client_found = False
        for client_id, client in vscode_clients.items():
            if client.get('sid') == sid:
                client_found = True
                logger.info(f"Checkout result from {client_id}: {data}")
                # Update stored state
                if data.get('success'):
                    client['current_branch'] = data.get('branch')
                    client['current_commit'] = data.get('commit')
                    client['last_seen'] = time.time()
                break
        
        if not client_found:
            logger.warning(f"Received checkout-result from unknown client (sid: {sid})")
    
    @sio.on('permission-response')
    async def on_permission_response(sid, data):
        """Handle permission response from client"""
        client_found = False
        for client_id, client in vscode_clients.items():
            if client.get('sid') == sid:
                client_found = True
                granted = data.get('granted', False)
                logger.info(f"Permission response from {client_id}: {granted}")
                
                # Update permissions
                vscode_permissions[client_id] = {
                    "allowed": granted,
                    "last_updated": time.time(),
                    "reason": data.get('reason')
                }
                break
        
        if not client_found:
            logger.warning(f"Received permission-response from unknown client (sid: {sid})")
    
    @sio.on('file-changes')
    async def on_file_changes(sid, data):
        """Handle file changes from client"""
        client_found = False
        client_id = data.get('clientId')
        
        for cid, client in vscode_clients.items():
            if client.get('sid') == sid:
                client_found = True
                logger.info(f"Received file changes from {cid}: {len(data.get('changes', []))} changes")
                
                # Store the changes in history
                if cid not in vscode_file_changes:
                    vscode_file_changes[cid] = []
                
                changes = data.get('changes', [])
                vscode_file_changes[cid].extend(changes)
                
                # Limit history size to prevent memory issues
                if len(vscode_file_changes[cid]) > 1000:
                    vscode_file_changes[cid] = vscode_file_changes[cid][-1000:]
                
                # Process changes through agent system
                await process_file_changes(cid, changes)
                break
        
        if not client_found:
            logger.warning(f"Received file-changes from unknown client (sid: {sid})")

async def process_file_changes(client_id, changes):
    """Process file changes through the agent system"""
    try:
        # Get client information
        client = vscode_clients.get(client_id)
        if not client:
            logger.warning(f"Client {client_id} not found for processing file changes")
            return
        
        # Create a message for the agent system
        message = {
            "type": "vscode_file_changes",
            "client_id": client_id,
            "workspace_name": client.get("workspace_name"),
            "workspace_path": client.get("workspace_path"),
            "branch": client.get("current_branch"),
            "commit": client.get("current_commit"),
            "timestamp": time.time(),
            "changes": changes
        }
        
        # If we have an agent service, forward the message
        if agent_service:
            await agent_service.process_message(message)
        else:
            # Log that we would send this to agents if configured
            logger.info(f"Would send file changes to agent system: {json.dumps(message, indent=2)}")
        
        logger.info(f"Processed {len(changes)} file changes from client {client_id}")
    except Exception as e:
        logger.error(f"Error processing file changes: {str(e)}")

@router.post("/register", status_code=201)
async def register_vscode_client(registration: VSCodeClientRegistration) -> Dict[str, Any]:
    """
    Register a new VS Code client
    """
    client_id = str(uuid.uuid4())
    
    vscode_clients[client_id] = {
        "workspace_name": registration.workspaceName,
        "workspace_path": registration.workspacePath,
        "initial_branch": registration.initialBranch,
        "current_branch": registration.initialBranch,
        "current_commit": None,
        "connected": False,
        "sid": None,
        "created_at": time.time(),
        "last_seen": time.time()
    }
    
    # Initialize with no permission (require explicit grant)
    vscode_permissions[client_id] = {
        "allowed": False,
        "last_updated": time.time(),
        "reason": "New registration - needs permission"
    }
    
    # Initialize empty file changes history
    vscode_file_changes[client_id] = []
    
    logger.info(f"Registered new VS Code client: {client_id} for workspace: {registration.workspaceName}")
    
    return {
        "clientId": client_id,
        "status": "registered"
    }

@router.get("/clients")
async def get_vscode_clients() -> Dict[str, Any]:
    """
    Get all registered VS Code clients
    """
    # If no clients exist, create a mock client for testing
    if not vscode_clients:
        mock_id = initialize_mock_clients()
        logger.info(f"No clients found, created mock client: {mock_id}")
    
    clients_info = {}
    for client_id, client in vscode_clients.items():
        permission = vscode_permissions.get(client_id, {"allowed": False})
        clients_info[client_id] = {
            "workspace_name": client["workspace_name"],
            "current_branch": client["current_branch"],
            "current_commit": client["current_commit"],
            "connected": client["connected"],
            "permission": permission.get("allowed"),
            "created_at": client.get("created_at"),
            "last_seen": client.get("last_seen"),
            "changes_count": len(vscode_file_changes.get(client_id, []))
        }
    
    return {
        "clients": clients_info,
        "count": len(clients_info)
    }

@router.post("/checkout")
async def checkout_branch(checkout: BranchCheckout) -> Dict[str, Any]:
    """
    Send command to checkout a specific branch and commit
    """
    client_id = checkout.clientId
    
    # If client doesn't exist and we're in development, create a mock client
    if client_id not in vscode_clients:
        logger.warning(f"VS Code client {client_id} not found. Creating mock client.")
        mock_id = initialize_mock_clients()
        if mock_id != client_id:
            raise HTTPException(status_code=404, detail=f"VS Code client {client_id} not found")
    
    client = vscode_clients[client_id]
    
    # Check permission
    permission = vscode_permissions.get(client_id, {"allowed": False})
    if not permission.get("allowed"):
        logger.warning(f"Permission denied for client {client_id}")
        # If no permission, request it through the Socket.IO connection if client is connected
        if client["connected"] and client["sid"] and sio:
            try:
                await sio.emit(
                    'request-permission',
                    {
                        'requestType': 'branch-checkout',
                        'details': {
                            'branch': checkout.branch,
                            'commit': checkout.commit,
                            'message': checkout.message or "Backend requested permission to change your branch"
                        }
                    },
                    room=client["sid"]
                )
                logger.info(f"Permission request sent to client {client_id}")
                return {
                    "status": "permission_requested",
                    "client_id": client_id,
                    "message": "Permission request sent to VS Code client"
                }
            except Exception as e:
                logger.error(f"Error sending permission request: {str(e)}")
                raise HTTPException(status_code=500, detail=f"Error sending permission request: {str(e)}")
        else:
            raise HTTPException(status_code=403, detail="Permission denied")
    
    # Check if client is connected
    if not client["connected"] or not client["sid"] or not sio:
        raise HTTPException(status_code=400, detail="Client not connected")
    
    # Send checkout command
    try:
        await sio.emit(
            'checkout',
            {
                'branch': checkout.branch,
                'commit': checkout.commit,
                'message': checkout.message
            },
            room=client["sid"]
        )
        logger.info(f"Checkout command sent to client {client_id}: branch={checkout.branch}, commit={checkout.commit}")
        return {
            "status": "checkout_sent",
            "client_id": client_id,
            "branch": checkout.branch,
            "commit": checkout.commit
        }
    except Exception as e:
        logger.error(f"Error sending checkout command: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error sending checkout command: {str(e)}")

@router.get("/client/{client_id}")
async def get_vscode_client(client_id: str) -> Dict[str, Any]:
    """
    Get information about a specific VS Code client
    """
    if client_id not in vscode_clients:
        raise HTTPException(status_code=404, detail=f"VS Code client {client_id} not found")
    
    client = vscode_clients[client_id]
    permission = vscode_permissions.get(client_id, {"allowed": False})
    
    return {
        "client_id": client_id,
        "workspace_name": client["workspace_name"],
        "workspace_path": client["workspace_path"],
        "initial_branch": client["initial_branch"],
        "current_branch": client["current_branch"],
        "current_commit": client["current_commit"],
        "connected": client["connected"],
        "created_at": client.get("created_at"),
        "last_seen": client.get("last_seen"),
        "permission": {
            "allowed": permission.get("allowed", False),
            "last_updated": permission.get("last_updated"),
            "reason": permission.get("reason")
        },
        "changes_count": len(vscode_file_changes.get(client_id, []))
    }

@router.post("/permission")
async def set_client_permission(permission: ClientPermission) -> Dict[str, Any]:
    """
    Set permission for a VS Code client
    """
    client_id = permission.clientId
    
    if client_id not in vscode_clients:
        raise HTTPException(status_code=404, detail=f"VS Code client {client_id} not found")
    
    vscode_permissions[client_id] = {
        "allowed": permission.allowed,
        "last_updated": time.time(),
        "reason": permission.reason or "Set via API"
    }
    
    logger.info(f"Permission set for client {client_id}: {permission.allowed}")
    
    return {
        "client_id": client_id,
        "allowed": permission.allowed,
        "status": "updated"
    }

async def send_message_to_client(client_id: str, message: str, actions: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Send a message to a specific VS Code client
    
    Args:
        client_id: ID of the client to send the message to
        message: The message content
        actions: Optional list of action buttons to display
        
    Returns:
        Status of the message send operation
    """
    if client_id not in vscode_clients:
        logger.warning(f"Cannot send message to unknown client: {client_id}")
        return {"status": "error", "message": "Unknown client ID"}
    
    client = vscode_clients[client_id]
    
    if not client["connected"] or not client["sid"] or not sio:
        logger.warning(f"Cannot send message to disconnected client: {client_id}")
        return {"status": "error", "message": "Client not connected"}
    
    try:
        await sio.emit(
            'user-message',
            {
                'message': message,
                'actions': actions or []
            },
            room=client["sid"]
        )
        logger.info(f"Sent message to client {client_id}: {message}")
        return {"status": "sent", "client_id": client_id}
    except Exception as e:
        logger.error(f"Error sending message to client {client_id}: {str(e)}")
        return {"status": "error", "message": str(e)}

@router.post("/send-message/{client_id}")
async def send_message_to_client_api(client_id: str, message: str, actions: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Send a message to a VS Code client via API
    """
    return await send_message_to_client(client_id, message, actions)

@router.get("/file-changes/{client_id}")
async def get_client_file_changes(client_id: str, limit: int = 100) -> Dict[str, Any]:
    """
    Get file changes for a specific VS Code client
    """
    if client_id not in vscode_clients:
        raise HTTPException(status_code=404, detail=f"VS Code client {client_id} not found")
    
    changes = vscode_file_changes.get(client_id, [])
    
    # Return the most recent changes up to the limit
    return {
        "client_id": client_id,
        "count": len(changes),
        "changes": changes[-limit:] if limit > 0 else changes
    }

@router.post("/mock")
async def create_mock_client() -> Dict[str, Any]:
    """
    Create a mock client for testing
    """
    mock_id = initialize_mock_clients()
    
    return {
        "client_id": mock_id,
        "status": "created"
    }

def initialize_agent_service(service):
    """Initialize the agent service for processing messages"""
    global agent_service
    agent_service = service
    logger.info("Agent service initialized for VS Code controller") 