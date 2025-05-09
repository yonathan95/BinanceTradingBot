"""
Planner Agent - Responsible for defining project scope, breaking down tasks,
and creating strategic implementation plans.
"""

import logging
import json
from typing import List, Dict, Any, Optional
import asyncio

from hive_mind.agent_sdk.base_agent import BaseAgent, Message

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PlannerAgent(BaseAgent):
    """
    Planner Agent that defines project scope, breaks it down into tasks,
    and creates a strategic plan for implementation.
    """
    
    def __init__(self, 
                agent_id: str = "planner", 
                model: str = "gpt-4o", 
                temperature: float = 0.7, 
                token_limit: int = 4096,
                memory_enabled: bool = True,
                embedding_model: str = "text-embedding-ada-002",
                vector_db_url: Optional[str] = None):
        """Initialize the Planner Agent"""
        super().__init__(
            agent_id=agent_id, 
            model=model, 
            temperature=temperature, 
            token_limit=token_limit,
            memory_enabled=memory_enabled,
            embedding_model=embedding_model,
            vector_db_url=vector_db_url
        )
        self.current_plans: Dict[str, Dict[str, Any]] = {}
        
    async def process_message(self, message: Message) -> Message:
        """Process an incoming message and generate a response"""
        logger.info(f"Planner received message: {message.content[:50]}...")
        
        # First, retrieve relevant memories to provide context
        context = await self.build_context_with_memory(
            query=message.content,
            max_memories=5,
            recent_message_count=5
        )
        
        # Add message-specific context
        context["current_message"] = message
        context["sender"] = message.sender
        context["thread_id"] = message.thread_id
        context["context_tags"] = message.context_tags
        
        # Generate a prompt based on the context
        prompt = await self.generate_prompt(context)
        
        # Call LLM to generate a response
        response_data = await self.call_llm(prompt)
        response_content = response_data["content"]
        
        # Check for plan creation or task breakdown requests
        if any(keyword in message.content.lower() for keyword in 
              ["plan", "breakdown", "break down", "tasks", "split up", "divide", "strategy"]):
            try:
                # Try to extract structured plan data
                plan_data = self._extract_plan_data(response_content)
                
                # If we have a project name in the plan, store it
                if "project_name" in plan_data:
                    project_id = plan_data.get("project_id", message.thread_id)
                    self.current_plans[project_id] = plan_data
                    
                    # Store the plan in memory with high importance
                    if self.memory_enabled:
                        await self.memory.add_memory(
                            content=f"PROJECT PLAN: {json.dumps(plan_data, indent=2)}",
                            metadata={
                                "type": "project_plan",
                                "project_id": project_id,
                                "project_name": plan_data.get("project_name", "Unnamed Project"),
                                "timestamp": plan_data.get("timestamp", 0),
                                "thread_id": message.thread_id
                            },
                            importance=4.0  # High importance for plans
                        )
            except Exception as e:
                logger.error(f"Error extracting plan data: {str(e)}")
        
        # Create and return response message
        return await self.send_message(
            recipients=[message.sender],
            content=response_content,
            context_tags=message.context_tags,
            message_type="response",
            thread_id=message.thread_id
        )
    
    async def generate_prompt(self, context: Dict[str, Any]) -> str:
        """Generate a prompt for the LLM based on the provided context"""
        
        # Build prompt with relevant memories for context
        memories_context = ""
        if "relevant_memories" in context and context["relevant_memories"]:
            memories_context = "Previous relevant information:\n"
            for i, memory in enumerate(context["relevant_memories"]):
                memories_context += f"{i+1}. {memory}\n"
        
        # Include recent message history
        message_history = ""
        if "recent_messages" in context and context["recent_messages"]:
            message_history = "Recent conversation:\n"
            for msg in context["recent_messages"]:
                message_history += f"{msg.sender}: {msg.content}\n"
        
        # Get the current message
        current_message = context.get("current_message")
        
        # Build the complete prompt
        prompt = f"""
You are the Planner of an AI development team. Your role is to create well-structured plans and break down projects into manageable tasks.

{memories_context}

{message_history}

User Request: {current_message.content if current_message else ""}

Your primary responsibilities are:
1. Understand project requirements
2. Break down projects into specific tasks
3. Define dependencies between tasks
4. Estimate complexity (Low/Medium/High) for each task
5. Recommend appropriate budget allocation
6. Identify potential risks

When creating a plan, follow this structure:
- Project Name: [Name]
- Project Description: [Brief description]
- Objectives: [Bullet points of key objectives]
- Tasks:
  - Task 1: 
    - Description: [Description]
    - Complexity: [Low/Medium/High]
    - Dependencies: [List of task IDs or "None"]
    - Estimated time: [Duration]
  - Task 2: [...]
- Risks:
  - Risk 1: [Description and mitigation strategy]
  - Risk 2: [...]
- Timeline: [Overall project timeline]

Respond in a structured, analytical manner focusing on creating an achievable plan.
"""
        return prompt
    
    def _extract_plan_data(self, text: str) -> Dict[str, Any]:
        """
        Extract structured plan data from the text response.
        This is a simple implementation - in a real system, you might use
        a more sophisticated approach or have the LLM return structured data.
        """
        lines = text.split('\n')
        plan_data = {
            "project_name": "Unnamed Project",
            "project_description": "",
            "objectives": [],
            "tasks": [],
            "risks": [],
            "timeline": "",
            "timestamp": int(asyncio.get_event_loop().time()),
            "project_id": f"project-{asyncio.get_event_loop().time()}"
        }
        
        current_section = None
        current_task = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Extract project name
            if line.startswith("Project Name:") or line.startswith("- Project Name:"):
                plan_data["project_name"] = line.split(":", 1)[1].strip()
                
            # Extract project description
            elif line.startswith("Project Description:") or line.startswith("- Project Description:"):
                plan_data["project_description"] = line.split(":", 1)[1].strip()
                
            # Handle section markers
            elif line.startswith("Objectives:") or line.startswith("- Objectives:"):
                current_section = "objectives"
            elif line.startswith("Tasks:") or line.startswith("- Tasks:"):
                current_section = "tasks"
            elif line.startswith("Risks:") or line.startswith("- Risks:"):
                current_section = "risks"
            elif line.startswith("Timeline:") or line.startswith("- Timeline:"):
                current_section = "timeline"
                plan_data["timeline"] = line.split(":", 1)[1].strip() if ":" in line else ""
                
            # Handle task entries
            elif current_section == "tasks" and (line.startswith("- Task") or line.startswith("  - Task")):
                task_name = line.split(":", 1)[1].strip() if ":" in line else line
                current_task = {
                    "name": task_name,
                    "description": "",
                    "complexity": "Medium",
                    "dependencies": [],
                    "estimated_time": ""
                }
                plan_data["tasks"].append(current_task)
                
            elif current_section == "tasks" and current_task and line.startswith("    - Description:"):
                current_task["description"] = line.split(":", 1)[1].strip()
            elif current_section == "tasks" and current_task and line.startswith("    - Complexity:"):
                current_task["complexity"] = line.split(":", 1)[1].strip()
            elif current_section == "tasks" and current_task and line.startswith("    - Dependencies:"):
                deps = line.split(":", 1)[1].strip()
                current_task["dependencies"] = [d.strip() for d in deps.split(",")] if deps.lower() != "none" else []
            elif current_section == "tasks" and current_task and line.startswith("    - Estimated time:"):
                current_task["estimated_time"] = line.split(":", 1)[1].strip()
                
            # Handle bullet points
            elif current_section == "objectives" and (line.startswith("- ") or line.startswith("  - ")):
                plan_data["objectives"].append(line.strip("- ").strip())
            elif current_section == "risks" and (line.startswith("- ") or line.startswith("  - ")):
                plan_data["risks"].append(line.strip("- ").strip())
        
        return plan_data
    
    async def create_project_plan(self, 
                           project_description: str, 
                           project_constraints: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Create a new project plan based on the description and constraints.
        
        Args:
            project_description: Detailed description of the project
            project_constraints: Dictionary of constraints (budget, timeline, etc.)
            
        Returns:
            Dictionary containing the project plan
        """
        if project_constraints is None:
            project_constraints = {}
            
        # Prepare context for prompt generation
        context = {
            "project_description": project_description,
            "project_constraints": project_constraints
        }
        
        # Try to retrieve relevant memories about similar projects
        if self.memory_enabled:
            context["relevant_memories"] = await self.retrieve_relevant_memories(
                query=project_description,
                max_memories=5
            )
        
        # Generate custom prompt for plan creation
        prompt = f"""
You are the Planner of an AI development team. Your task is to create a detailed project plan based on the following description and constraints.

Project Description:
{project_description}

Project Constraints:
{json.dumps(project_constraints, indent=2) if project_constraints else "No specific constraints provided."}

Please create a structured project plan that includes:
1. Project name
2. Project description (summary)
3. Key objectives (3-5 bullet points)
4. Tasks breakdown (with description, complexity, dependencies, and time estimates)
5. Potential risks and mitigation strategies
6. Overall timeline

Format the plan in a clear, structured manner that can be easily parsed.
"""
        
        # Call LLM to generate the plan
        response_data = await self.call_llm(prompt)
        response_content = response_data["content"]
        
        # Extract structured plan data
        plan_data = self._extract_plan_data(response_content)
        
        # Store the plan
        project_id = plan_data["project_id"]
        self.current_plans[project_id] = plan_data
        
        # Store in memory
        if self.memory_enabled:
            await self.memory.add_memory(
                content=f"PROJECT PLAN:\n{response_content}",
                metadata={
                    "type": "project_plan",
                    "project_id": project_id,
                    "project_name": plan_data.get("project_name", "Unnamed Project"),
                    "timestamp": plan_data.get("timestamp", 0)
                },
                importance=4.0  # High importance for plans
            )
        
        return plan_data
    
    async def update_project_plan(self, 
                           project_id: str, 
                           updates: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update an existing project plan.
        
        Args:
            project_id: ID of the project to update
            updates: Dictionary of updates to apply to the plan
            
        Returns:
            Updated project plan
        """
        if project_id not in self.current_plans:
            raise ValueError(f"Project {project_id} not found")
            
        plan = self.current_plans[project_id]
        
        # Apply updates
        for key, value in updates.items():
            if key in plan:
                plan[key] = value
        
        # Update timestamp
        plan["last_updated"] = int(asyncio.get_event_loop().time())
        
        # Store updated plan in memory
        if self.memory_enabled:
            await self.memory.add_memory(
                content=f"UPDATED PROJECT PLAN: {json.dumps(plan, indent=2)}",
                metadata={
                    "type": "project_plan_update",
                    "project_id": project_id,
                    "project_name": plan.get("project_name", "Unnamed Project"),
                    "timestamp": plan.get("last_updated", 0)
                },
                importance=3.5  # Slightly lower than initial plan
            )
        
        return plan 