"""
Common utilities and extensions for Hive Mind agents.
"""

from .git_integration import GitIntegration
from .agent_git_extension import AgentGitExtension
from .git_enabled_agent import GitEnabledAgent

__all__ = ['GitIntegration', 'AgentGitExtension', 'GitEnabledAgent'] 