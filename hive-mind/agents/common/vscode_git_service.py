"""
VS Code Git Service - Allows agents to control VS Code workspaces via the backend API.
"""

import logging
import aiohttp
import json
from typing import Dict, List, Any, Optional, Union

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VSCodeGitService:
    """
    Service to control VS Code Git workspaces from agents.
    
    This service integrates with the Hive Mind backend API to control
    which branches and commits are displayed in connected VS Code clients.
    """
    
    def __init__(self, 
                control_plane_url: str = "http://localhost:5000",
                api_key: Optional[str] = None):
        """
        Initialize VS Code Git Service
        
        Args:
            control_plane_url: URL of the Hive Mind control plane
            api_key: Optional API key for authentication
        """
        self.control_plane_url = control_plane_url
        self.api_key = api_key
        self.session = None
        
    async def _ensure_session(self):
        """Ensure HTTP session is created"""
        if self.session is None:
            self.session = aiohttp.ClientSession()
            
    async def close(self):
        """Close HTTP session"""
        if self.session:
            await self.session.close()
            self.session = None
    
    async def get_connected_clients(self) -> Dict[str, Any]:
        """
        Get all connected VS Code clients
        
        Returns:
            List of connected clients
        """
        await self._ensure_session()
        
        headers = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
            
        async with self.session.get(
            f"{self.control_plane_url}/api/vscode/clients",
            headers=headers
        ) as response:
            if response.status == 200:
                return await response.json()
            else:
                error = await response.text()
                logger.error(f"Error getting VS Code clients: {error}")
                return {"error": error, "status": response.status}
    
    async def get_client_info(self, client_id: str) -> Dict[str, Any]:
        """
        Get information about a specific VS Code client
        
        Args:
            client_id: ID of the client
            
        Returns:
            Client information
        """
        await self._ensure_session()
        
        headers = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
            
        async with self.session.get(
            f"{self.control_plane_url}/api/vscode/client/{client_id}",
            headers=headers
        ) as response:
            if response.status == 200:
                return await response.json()
            else:
                error = await response.text()
                logger.error(f"Error getting VS Code client {client_id}: {error}")
                return {"error": error, "status": response.status}
    
    async def checkout_branch(self, 
                            client_id: str, 
                            branch: str, 
                            commit: Optional[str] = None,
                            message: Optional[str] = None) -> Dict[str, Any]:
        """
        Send command to checkout a specific branch and commit in a VS Code client
        
        Args:
            client_id: ID of the VS Code client
            branch: Name of the branch to checkout
            commit: Optional commit hash to checkout
            message: Optional message to display to the user
            
        Returns:
            Command result
        """
        await self._ensure_session()
        
        headers = {
            "Content-Type": "application/json"
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
            
        payload = {
            "clientId": client_id,
            "branch": branch,
            "commit": commit,
            "message": message
        }
        
        async with self.session.post(
            f"{self.control_plane_url}/api/vscode/checkout",
            headers=headers,
            json=payload
        ) as response:
            if response.status in (200, 201):
                return await response.json()
            else:
                error = await response.text()
                logger.error(f"Error sending checkout command: {error}")
                return {"error": error, "status": response.status}
                
    async def find_client_by_workspace_name(self, workspace_name: str) -> Optional[str]:
        """
        Find a client ID by workspace name
        
        Args:
            workspace_name: Name of the workspace
            
        Returns:
            Client ID if found, None otherwise
        """
        clients = await self.get_connected_clients()
        
        if "clients" in clients:
            for client_id, client in clients["clients"].items():
                if client["workspace_name"] == workspace_name:
                    return client_id
                    
        return None 