"""
VS Code Git Control Example - Shows how to control VS Code clients from an agent.
"""

import asyncio
import logging
import os
import sys

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.common.git_enabled_agent import GitEnabledAgent

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    """Main function to demonstrate VS Code client control"""
    # Create an agent with VS Code integration enabled
    agent = GitEnabledAgent(
        agent_id="vscode-controller",
        model="gpt-4",
        workspace_path="./example-repo",
        repository_url="https://github.com/example/repo.git",
        control_plane_url="http://localhost:5000",
        vscode_integration_enabled=True
    )
    
    try:
        # Get list of connected VS Code clients
        clients = await agent.get_vscode_clients()
        logger.info(f"Connected VS Code clients: {clients}")
        
        if "clients" in clients and clients["clients"]:
            # For demonstration purposes, use the first client
            workspace_name = list(clients["clients"].keys())[0]
            
            # Change the branch in VS Code
            result = await agent.set_vscode_client_branch(
                workspace_name=workspace_name,
                branch="feature/new-feature"
            )
            logger.info(f"Set branch result: {result}")
            
            # Wait a moment
            await asyncio.sleep(5)
            
            # Change to a different branch
            result = await agent.set_vscode_client_branch(
                workspace_name=workspace_name,
                branch="main"
            )
            logger.info(f"Set branch result: {result}")
        else:
            logger.warning("No VS Code clients connected")
            
    except Exception as e:
        logger.error(f"Error: {str(e)}")
    finally:
        # Close the VS Code service
        if hasattr(agent, 'vscode_service'):
            await agent.vscode_service.close()

if __name__ == "__main__":
    asyncio.run(main()) 