from fastapi import APIRouter, Depends, HTTPException, Body
from typing import List, Dict, Any, Optional
import json
import time

from ..auth import get_current_user
from ...models.agents import AgentPromptUsageConfig, PromptOptimizationRequest, PromptOptimizationResponse
from ...models.users import User
from ...services.agent_service import AgentService, get_agent_service
from ...services.team_service import TeamService, get_team_service

router = APIRouter(
    prefix="/prompt-engineering",
    tags=["prompt-engineering"],
)


@router.post("/optimize", response_model=PromptOptimizationResponse)
async def optimize_prompt(
    request: PromptOptimizationRequest,
    current_user: User = Depends(get_current_user),
    agent_service: AgentService = Depends(get_agent_service),
    team_service: TeamService = Depends(get_team_service)
):
    """
    Optimize a prompt for an agent using the prompt engineer
    """
    # Verify the agent exists and user has access to it
    agent_config = await agent_service.get_agent(request.agent_id)
    if not agent_config:
        raise HTTPException(status_code=404, detail=f"Agent {request.agent_id} not found")
    
    # Verify user has access to the team containing this agent
    team = await team_service.get_team_by_agent(request.agent_id)
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    
    if team.created_by != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized to access this team")
    
    # Get the prompt engineer agent for this team
    prompt_engineer = team.get_agent_by_role("prompt_engineer")
    if not prompt_engineer:
        raise HTTPException(status_code=404, detail="No prompt engineer agent found in this team")
    
    # Format the optimization request
    optimization_request = {
        "prompt": request.prompt,
        "agent_type": agent_config.role,
        "task_type": request.task_type,
        "context": request.context,
        "optimization_goals": request.optimization_goals
    }
    
    # Send the request to the prompt engineer agent
    try:
        # In a real implementation, this would communicate with the agent through
        # a message queue or API call. We're mocking the response for now.
        # result = await agent_service.send_message_to_agent(
        #     prompt_engineer.agent_id, 
        #     "optimize_prompt", 
        #     json.dumps(optimization_request)
        # )
        
        # Mock response
        mock_result = {
            "prompt_id": f"{agent_config.role}_{request.task_type}_{int(time.time())}",
            "optimized_prompt": f"Optimized version of: {request.prompt[:50]}...",
            "explanation": "This prompt was optimized for clarity and effectiveness.",
            "agent_type": agent_config.role,
            "task_type": request.task_type
        }
        
        # Create the response
        response = PromptOptimizationResponse(
            prompt_id=mock_result["prompt_id"],
            agent_id=request.agent_id,
            task_type=request.task_type,
            optimized_prompt=mock_result["optimized_prompt"],
            explanation=mock_result["explanation"],
            created_at=time.time(),
            version=1
        )
        
        return response
        
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Error optimizing prompt: {str(e)}"
        )


@router.get("/config/{team_id}", response_model=AgentPromptUsageConfig)
async def get_prompt_usage_config(
    team_id: str,
    current_user: User = Depends(get_current_user),
    team_service: TeamService = Depends(get_team_service)
):
    """
    Get the prompt usage configuration for a team
    """
    # Verify user has access to the team
    team = await team_service.get_team(team_id)
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    
    if team.created_by != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized to access this team")
    
    # Get the prompt usage configuration
    try:
        # In a real implementation, this would fetch from a database
        # config = await team_service.get_prompt_usage_config(team_id)
        
        # Mock response
        optimized_agents = [
            agent.agent_id for agent in team.agents
            if agent.use_prompt_engineering
        ]
        
        config = AgentPromptUsageConfig(
            team_id=team_id,
            optimized_agents=optimized_agents,
            default_optimization_goals=["clarity", "effectiveness"],
            auto_optimize=False,
            optimization_feedback=True
        )
        
        return config
        
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Error getting prompt usage configuration: {str(e)}"
        )


@router.post("/config/{team_id}", response_model=AgentPromptUsageConfig)
async def update_prompt_usage_config(
    team_id: str,
    config: AgentPromptUsageConfig,
    current_user: User = Depends(get_current_user),
    team_service: TeamService = Depends(get_team_service)
):
    """
    Update the prompt usage configuration for a team
    """
    # Verify team_id matches the config
    if team_id != config.team_id:
        raise HTTPException(
            status_code=400, 
            detail="Team ID in path does not match team ID in configuration"
        )
    
    # Verify user has access to the team
    team = await team_service.get_team(team_id)
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    
    if team.created_by != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized to access this team")
    
    # Verify all optimized_agents exist in the team
    for agent_id in config.optimized_agents:
        if not team.get_agent_by_id(agent_id):
            raise HTTPException(
                status_code=400, 
                detail=f"Agent {agent_id} not found in team {team_id}"
            )
    
    # Update the prompt usage configuration
    try:
        # In a real implementation, this would update the database
        # updated_config = await team_service.update_prompt_usage_config(config)
        
        # Update agent configs to reflect prompt usage
        for agent in team.agents:
            agent.use_prompt_engineering = agent.agent_id in config.optimized_agents
        
        # Mock response (just return the input config)
        return config
        
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Error updating prompt usage configuration: {str(e)}"
        )


@router.post("/toggle-agent/{agent_id}")
async def toggle_agent_prompt_engineering(
    agent_id: str,
    enable: bool = Body(..., embed=True),
    current_user: User = Depends(get_current_user),
    agent_service: AgentService = Depends(get_agent_service),
    team_service: TeamService = Depends(get_team_service)
):
    """
    Enable or disable prompt engineering for a specific agent
    """
    # Verify the agent exists
    agent_config = await agent_service.get_agent(agent_id)
    if not agent_config:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")
    
    # Verify user has access to the team containing this agent
    team = await team_service.get_team_by_agent(agent_id)
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    
    if team.created_by != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized to access this team")
    
    # Update the agent's prompt engineering setting
    try:
        # In a real implementation, this would update the database
        # await agent_service.set_agent_prompt_engineering(agent_id, enable)
        
        # Get the prompt usage configuration
        # config = await team_service.get_prompt_usage_config(team.team_id)
        
        # Mock implementation
        # Create a default config if none exists
        config = AgentPromptUsageConfig(
            team_id=team.team_id,
            optimized_agents=[],
            default_optimization_goals=["clarity", "effectiveness"],
            auto_optimize=False,
            optimization_feedback=True
        )
        
        # Update the configuration
        if enable:
            config.add_optimized_agent(agent_id)
        else:
            config.remove_optimized_agent(agent_id)
        
        # Update the agent configuration
        agent_config.use_prompt_engineering = enable
        
        return {
            "agent_id": agent_id,
            "use_prompt_engineering": enable,
            "message": f"Prompt engineering {'enabled' if enable else 'disabled'} for agent {agent_id}"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Error toggling prompt engineering: {str(e)}"
        )


@router.get("/library/{team_id}", response_model=List[Dict[str, Any]])
async def get_prompt_library(
    team_id: str,
    agent_id: Optional[str] = None,
    task_type: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    team_service: TeamService = Depends(get_team_service)
):
    """
    Get prompts from the prompt library for a team, optionally filtered by agent and task type
    """
    # Verify user has access to the team
    team = await team_service.get_team(team_id)
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    
    if team.created_by != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized to access this team")
    
    # Get the prompt engineer agent for this team
    prompt_engineer = team.get_agent_by_role("prompt_engineer")
    if not prompt_engineer:
        raise HTTPException(status_code=404, detail="No prompt engineer agent found in this team")
    
    # Get prompts from the library
    try:
        # In a real implementation, this would fetch from the prompt engineer agent's library
        # prompts = await agent_service.get_prompt_library(prompt_engineer.agent_id, agent_id, task_type)
        
        # Mock response
        mock_prompts = [
            {
                "prompt_id": "architect_system_design_1234567890",
                "agent_id": "architect-1",
                "task_type": "system_design",
                "prompt": "You are an Architect tasked with designing a system...",
                "created_at": time.time() - 86400,  # 1 day ago
                "version": 1
            },
            {
                "prompt_id": "coder_implementation_1234567890",
                "agent_id": "coder-1",
                "task_type": "implementation",
                "prompt": "You are a Coder tasked with implementing...",
                "created_at": time.time() - 43200,  # 12 hours ago
                "version": 2
            },
            {
                "prompt_id": "tester_unit_testing_1234567890",
                "agent_id": "tester-1",
                "task_type": "unit_testing",
                "prompt": "You are a Tester tasked with creating unit tests...",
                "created_at": time.time() - 21600,  # 6 hours ago
                "version": 1
            }
        ]
        
        # Filter by agent_id if provided
        if agent_id:
            mock_prompts = [p for p in mock_prompts if p["agent_id"] == agent_id]
            
        # Filter by task_type if provided
        if task_type:
            mock_prompts = [p for p in mock_prompts if p["task_type"] == task_type]
        
        return mock_prompts
        
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Error retrieving prompt library: {str(e)}"
        ) 