"""
Common utility functions for agents
"""
import os
import json
import logging
from typing import Dict, Any, List

# Configure logging
logging.basicConfig(
    level=os.environ.get("LOG_LEVEL", "INFO"),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def get_logger(name: str) -> logging.Logger:
    """Get a logger with the given name"""
    return logging.getLogger(name)

def load_json(file_path: str) -> Dict[str, Any]:
    """Load a JSON file"""
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger = get_logger("utils")
        logger.error(f"Error loading JSON file {file_path}: {e}")
        return {}

def save_json(file_path: str, data: Dict[str, Any]) -> None:
    """Save data to a JSON file"""
    try:
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        logger = get_logger("utils")
        logger.error(f"Error saving JSON file {file_path}: {e}")

def format_message(agent_type: str, content: str) -> Dict[str, Any]:
    """Format a message from an agent"""
    return {
        "agent_type": agent_type,
        "content": content,
        "timestamp": None  # Will be added by message handler
    } 