import os
import re
import asyncio
import shlex
from typing import Dict, Any, List, Optional, Set
import subprocess
from pathlib import Path

from hive_mind.agent_sdk.base_agent import AgentTool

class ExecTool(AgentTool):
    """
    Tool for executing shell commands in a sandboxed environment
    """
    
    # Set of potentially dangerous commands that are blocked
    # This is not exhaustive and should be expanded based on security needs
    BLOCKED_COMMANDS = {
        "rm", "rmdir", "del", "format", "mkfs", 
        "dd", "chmod", "chown", "sudo", "su", 
        "passwd", "mount", "umount", "shutdown", "reboot"
    }
    
    # Command pattern blocklist (regex patterns)
    BLOCKED_PATTERNS = [
        r">(.*)",         # Output redirection
        r">>(.*)",        # Append redirection
        r"<(.*)",         # Input redirection
        r"\|(.*)",        # Pipe (can be allowed for specific commands)
        r"&$",            # Background execution
        r";(.*)",         # Command chaining
        r"`(.*)`",        # Command substitution
        r"\$\((.*)\)"     # Command substitution
    ]
    
    def __init__(self, workspace_path: str, allowed_commands: Optional[Set[str]] = None):
        """
        Initialize the ExecTool with a workspace path and allowed commands
        
        Args:
            workspace_path: Base directory for command execution
            allowed_commands: Set of commands that are explicitly allowed
        """
        super().__init__(
            name="exec_tool",
            description="Execute shell commands in the workspace",
            parameters={
                "command": "The command to execute",
                "timeout": "Timeout in seconds (default: 30)"
            }
        )
        self.workspace_path = Path(workspace_path)
        self.allowed_commands = allowed_commands or {
            "ls", "dir", "cd", "pwd", "echo", "cat", "more", 
            "head", "tail", "find", "grep", "mkdir", "touch", 
            "python", "pip", "git", "npm", "node"
        }
        
        # Ensure workspace directory exists
        os.makedirs(self.workspace_path, exist_ok=True)
    
    async def execute(self, command: str, timeout: int = 30) -> Dict[str, Any]:
        """
        Execute a shell command
        
        Args:
            command: Command to execute
            timeout: Maximum execution time in seconds
            
        Returns:
            A dictionary with the command output
        """
        # Verify the command is safe to execute
        validation_result = self._validate_command(command)
        if not validation_result["valid"]:
            return {
                "success": False,
                "error": validation_result["reason"]
            }
            
        try:
            # Create a process to execute the command
            proc = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(self.workspace_path)
            )
            
            # Wait for the process to complete with timeout
            try:
                stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout)
                
                # Decode output
                stdout_str = stdout.decode('utf-8', errors='replace')
                stderr_str = stderr.decode('utf-8', errors='replace')
                
                return {
                    "success": proc.returncode == 0,
                    "exit_code": proc.returncode,
                    "stdout": stdout_str,
                    "stderr": stderr_str
                }
            except asyncio.TimeoutError:
                # Kill the process if it times out
                try:
                    proc.kill()
                except:
                    pass
                    
                return {
                    "success": False,
                    "error": f"Command timed out after {timeout} seconds"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Error executing command: {str(e)}"
            }
    
    def _validate_command(self, command: str) -> Dict[str, Any]:
        """
        Validate that a command is safe to execute
        
        Args:
            command: The command to validate
            
        Returns:
            Dictionary with validation result
        """
        # Split the command to get the base command
        try:
            # Get the base command
            base_command = shlex.split(command)[0]
            
            # Check if it's in the blocked commands list
            if base_command in self.BLOCKED_COMMANDS:
                return {
                    "valid": False,
                    "reason": f"Command '{base_command}' is not allowed for security reasons"
                }
                
            # Check if it's not in the allowed commands list
            if base_command not in self.allowed_commands:
                return {
                    "valid": False,
                    "reason": f"Command '{base_command}' is not in the allowed commands list"
                }
                
            # Check for blocked patterns
            for pattern in self.BLOCKED_PATTERNS:
                if re.search(pattern, command):
                    return {
                        "valid": False,
                        "reason": f"Command contains blocked pattern: {pattern}"
                    }
                    
            # If all checks pass, the command is valid
            return {
                "valid": True
            }
        except Exception as e:
            return {
                "valid": False,
                "reason": f"Error parsing command: {str(e)}"
            } 