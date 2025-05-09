import os
import json
from typing import Dict, Any, List, Optional
import aiofiles
from pathlib import Path

from hive_mind.agent_sdk.base_agent import AgentTool

class FileTool(AgentTool):
    """
    Tool for working with files in the agent workspace
    """
    
    def __init__(self, workspace_path: str):
        """
        Initialize the FileTool with a workspace path
        
        Args:
            workspace_path: Base directory for file operations
        """
        super().__init__(
            name="file_tool",
            description="Read, write, and manipulate files in the workspace",
            parameters={
                "action": "The action to perform (read, write, list, exists, delete)",
                "path": "The path to the file or directory, relative to the workspace",
                "content": "The content to write (for write action only)",
                "overwrite": "Whether to overwrite existing files (for write action only)"
            }
        )
        self.workspace_path = Path(workspace_path)
        
        # Ensure workspace directory exists
        os.makedirs(self.workspace_path, exist_ok=True)
    
    async def execute(self, 
                    action: str, 
                    path: str, 
                    content: Optional[str] = None,
                    overwrite: bool = False) -> Dict[str, Any]:
        """
        Execute file operations
        
        Args:
            action: The action to perform (read, write, list, exists, delete)
            path: The path to the file or directory
            content: The content to write (for write action only)
            overwrite: Whether to overwrite existing files (for write action only)
            
        Returns:
            A dictionary with the operation result
        """
        # Ensure the path doesn't try to escape the workspace
        full_path = self._get_safe_path(path)
        
        try:
            if action == "read":
                return await self._read_file(full_path)
            elif action == "write":
                return await self._write_file(full_path, content, overwrite)
            elif action == "list":
                return await self._list_files(full_path)
            elif action == "exists":
                return self._file_exists(full_path)
            elif action == "delete":
                return await self._delete_file(full_path)
            else:
                return {
                    "success": False,
                    "error": f"Unknown action: {action}"
                }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def _get_safe_path(self, path: str) -> Path:
        """
        Ensure the path doesn't escape the workspace
        
        Args:
            path: The requested path
            
        Returns:
            A safe Path object
        
        Raises:
            ValueError: If the path attempts to escape the workspace
        """
        # Normalize the path and resolve any symlinks
        full_path = (self.workspace_path / path).resolve()
        
        # Check if it's within the workspace
        if not str(full_path).startswith(str(self.workspace_path.resolve())):
            raise ValueError(f"Path {path} attempts to escape the workspace")
            
        return full_path
    
    async def _read_file(self, path: Path) -> Dict[str, Any]:
        """
        Read a file
        
        Args:
            path: Path to the file
            
        Returns:
            Dictionary with the file content
        """
        if not path.exists():
            return {
                "success": False,
                "error": f"File {path} does not exist"
            }
            
        if not path.is_file():
            return {
                "success": False,
                "error": f"{path} is a directory, not a file"
            }
            
        try:
            async with aiofiles.open(path, 'r', encoding='utf-8') as f:
                content = await f.read()
                
            return {
                "success": True,
                "content": content
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Error reading file: {str(e)}"
            }
    
    async def _write_file(self, path: Path, content: str, overwrite: bool) -> Dict[str, Any]:
        """
        Write content to a file
        
        Args:
            path: Path to the file
            content: Content to write
            overwrite: Whether to overwrite existing files
            
        Returns:
            Status of the operation
        """
        if path.exists() and not overwrite:
            return {
                "success": False,
                "error": f"File {path} already exists and overwrite is False"
            }
            
        # Ensure parent directory exists
        os.makedirs(path.parent, exist_ok=True)
            
        try:
            async with aiofiles.open(path, 'w', encoding='utf-8') as f:
                await f.write(content)
                
            return {
                "success": True,
                "path": str(path.relative_to(self.workspace_path))
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Error writing file: {str(e)}"
            }
    
    async def _list_files(self, path: Path) -> Dict[str, Any]:
        """
        List files in a directory
        
        Args:
            path: Path to the directory
            
        Returns:
            Dictionary with list of files and directories
        """
        if not path.exists():
            return {
                "success": False,
                "error": f"Directory {path} does not exist"
            }
            
        if not path.is_dir():
            return {
                "success": False,
                "error": f"{path} is a file, not a directory"
            }
            
        try:
            files = []
            directories = []
            
            for item in path.iterdir():
                rel_path = str(item.relative_to(self.workspace_path))
                if item.is_file():
                    files.append(rel_path)
                elif item.is_dir():
                    directories.append(rel_path)
                    
            return {
                "success": True,
                "files": files,
                "directories": directories
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Error listing directory: {str(e)}"
            }
    
    def _file_exists(self, path: Path) -> Dict[str, Any]:
        """
        Check if a file or directory exists
        
        Args:
            path: Path to check
            
        Returns:
            Dictionary with existence information
        """
        exists = path.exists()
        is_file = path.is_file() if exists else False
        is_dir = path.is_dir() if exists else False
        
        return {
            "success": True,
            "exists": exists,
            "is_file": is_file,
            "is_dir": is_dir
        }
    
    async def _delete_file(self, path: Path) -> Dict[str, Any]:
        """
        Delete a file or directory
        
        Args:
            path: Path to delete
            
        Returns:
            Status of the operation
        """
        if not path.exists():
            return {
                "success": False,
                "error": f"Path {path} does not exist"
            }
            
        try:
            if path.is_file():
                path.unlink()
            elif path.is_dir():
                # This will fail if the directory is not empty
                path.rmdir()
                
            return {
                "success": True,
                "deleted": str(path.relative_to(self.workspace_path))
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Error deleting {path}: {str(e)}"
            } 