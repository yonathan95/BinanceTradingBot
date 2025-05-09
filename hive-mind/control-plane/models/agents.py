from enum import Enum
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class AgentTier(str, Enum):
    """Enum for agent tiers with corresponding LLM models and costs"""
    ECONOMY = "economy"
    STANDARD = "standard"
    PREMIUM = "premium"


class AgentRole(str, Enum):
    """Enum for standard agent roles"""
    MANAGER = "manager"
    PLANNER = "planner"
    ARCHITECT = "architect"
    CODER = "coder"
    TESTER = "tester"
    PRODUCT_MANAGER = "product_manager"
    DEVOPS = "devops"
    SECURITY = "security"
    UX_DESIGNER = "ux_designer"
    DATABASE_ENGINEER = "database_engineer"
    MLOPS = "mlops"
    DOCUMENTATION = "documentation"
    PROMPT_ENGINEER = "prompt_engineer"
    
    # Skeptic roles
    ARCHITECTURE_SKEPTIC = "architecture_skeptic"
    SECURITY_SKEPTIC = "security_skeptic" 
    EFFICIENCY_CRITIC = "efficiency_critic"
    CODE_QUALITY_SKEPTIC = "code_quality_skeptic"


class AgentConfig(BaseModel):
    """Configuration for an agent"""
    role: AgentRole
    agent_id: str = Field(..., description="Unique identifier for the agent")
    model: str = Field(..., description="LLM model to use")
    temperature: float = Field(0.7, description="LLM temperature setting")
    token_limit: int = Field(4096, description="Maximum token limit for LLM calls")
    tier: AgentTier = Field(AgentTier.STANDARD, description="Agent tier (economy, standard, premium)")
    tools: List[str] = Field([], description="List of tool IDs available to this agent")
    use_prompt_engineering: bool = Field(
        False, 
        description="Whether this agent should use prompts optimized by the prompt engineer"
    )
    custom_settings: Dict[str, str] = Field({}, description="Additional custom settings for this agent")


class TeamConfig(BaseModel):
    """Configuration for a team of agents"""
    team_id: str = Field(..., description="Unique identifier for the team")
    name: str = Field(..., description="Display name for the team")
    description: Optional[str] = Field(None, description="Team description")
    agents: List[AgentConfig] = Field(..., description="List of agents in the team")
    workspace_id: str = Field(..., description="ID of the workspace for this team")
    budget: Optional[float] = Field(None, description="Maximum budget for this team in USD")
    created_by: str = Field(..., description="User ID who created the team")
    
    def get_agent_by_id(self, agent_id: str) -> Optional[AgentConfig]:
        """Get an agent configuration by its ID"""
        for agent in self.agents:
            if agent.agent_id == agent_id:
                return agent
        return None
    
    def get_agent_by_role(self, role: AgentRole) -> Optional[AgentConfig]:
        """Get an agent configuration by its role"""
        for agent in self.agents:
            if agent.role == role:
                return agent
        return None
    
    def get_prompt_engineered_agents(self) -> List[AgentConfig]:
        """Get all agents using prompt engineering"""
        return [agent for agent in self.agents if agent.use_prompt_engineering]


class PromptOptimizationRequest(BaseModel):
    """Request to optimize a prompt"""
    agent_id: str = Field(..., description="ID of the agent to optimize prompt for")
    prompt: str = Field(..., description="The prompt to optimize")
    task_type: str = Field(..., description="Type of task (e.g., 'code_review', 'architecture_design')")
    context: Dict[str, str] = Field({}, description="Additional context to consider")
    optimization_goals: List[str] = Field(
        ["clarity", "effectiveness"], 
        description="Goals for optimization (e.g., clarity, effectiveness, specificity)"
    )


class PromptOptimizationResponse(BaseModel):
    """Response with an optimized prompt"""
    prompt_id: str = Field(..., description="ID of the optimized prompt")
    agent_id: str = Field(..., description="ID of the agent the prompt is for")
    task_type: str = Field(..., description="Type of task")
    optimized_prompt: str = Field(..., description="The optimized prompt")
    explanation: str = Field(..., description="Explanation of the optimizations made")
    created_at: float = Field(..., description="Timestamp of creation")
    version: int = Field(1, description="Version number of this prompt")


class AgentPromptUsageConfig(BaseModel):
    """Configuration for agent prompt usage"""
    team_id: str = Field(..., description="ID of the team")
    optimized_agents: List[str] = Field(
        [], 
        description="List of agent IDs that should use prompts from the prompt engineer"
    )
    default_optimization_goals: List[str] = Field(
        ["clarity", "effectiveness"], 
        description="Default goals for prompt optimization"
    )
    auto_optimize: bool = Field(
        False, 
        description="Whether to automatically optimize prompts for configured agents"
    )
    optimization_feedback: bool = Field(
        True, 
        description="Whether to collect feedback on optimized prompts"
    )
    
    def is_agent_optimized(self, agent_id: str) -> bool:
        """Check if an agent is configured to use optimized prompts"""
        return agent_id in self.optimized_agents
    
    def add_optimized_agent(self, agent_id: str) -> None:
        """Add an agent to the list of optimized agents"""
        if agent_id not in self.optimized_agents:
            self.optimized_agents.append(agent_id)
    
    def remove_optimized_agent(self, agent_id: str) -> None:
        """Remove an agent from the list of optimized agents"""
        if agent_id in self.optimized_agents:
            self.optimized_agents.remove(agent_id) 