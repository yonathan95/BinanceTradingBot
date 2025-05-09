import json
from typing import Dict, List, Any, Optional
import re
import time

from hive_mind.agent_sdk.base_agent import BaseAgent, Message

class PromptEngineerAgent(BaseAgent):
    """
    Senior Prompt Engineer Agent that specializes in creating and optimizing prompts for other agents.
    This agent analyzes prompt effectiveness, creates prompt variants, and improves instructions
    to enhance agent performance.
    """
    
    def __init__(self, 
                agent_id: str = "prompt_engineer", 
                model: str = "claude-3-opus", 
                temperature: float = 0.7,
                token_limit: int = 8000):
        """
        Initialize the Prompt Engineer Agent
        
        Args:
            agent_id: Unique identifier for the agent
            model: LLM model to use (premium tier for advanced prompt engineering)
            temperature: LLM temperature setting
            token_limit: Maximum token limit for LLM calls
        """
        super().__init__(agent_id, model, temperature, token_limit)
        self.prompt_library: Dict[str, Dict[str, Any]] = {}  # Stores prompt templates by agent and task type
        self.prompt_performance: Dict[str, List[Dict[str, Any]]] = {}  # Tracks performance metrics of prompts
        self.optimized_agents: List[str] = []  # List of agents that use optimized prompts
        
    async def process_message(self, message: Message) -> Message:
        """
        Process an incoming message and generate a response
        
        Args:
            message: The incoming message
            
        Returns:
            A response message with prompt engineering insights
        """
        if message.message_type == "optimize_prompt":
            return await self._handle_optimize_prompt(message)
        elif message.message_type == "create_prompt":
            return await self._handle_create_prompt(message)
        elif message.message_type == "analyze_prompt":
            return await self._handle_analyze_prompt(message)
        elif message.message_type == "question":
            return await self._handle_question(message)
        else:
            # Default handling for other message types
            prompt = await self.generate_prompt({
                "message": message.content,
                "sender": message.sender,
                "context_tags": message.context_tags,
                "type": "default"
            })
            
            response = await self.call_llm(prompt)
            
            return await self.send_message(
                recipients=[message.sender],
                content=response["content"],
                context_tags=message.context_tags + ["#prompt_engineering"],
                message_type="response",
                thread_id=message.thread_id
            )
    
    async def _handle_optimize_prompt(self, message: Message) -> Message:
        """
        Handle a request to optimize an existing prompt
        
        Args:
            message: The message containing the prompt to optimize and context
            
        Returns:
            A response message with an optimized prompt
        """
        # Parse the optimization request
        try:
            request_data = json.loads(message.content)
            original_prompt = request_data.get("prompt", "")
            agent_type = request_data.get("agent_type", "")
            task_type = request_data.get("task_type", "")
            context = request_data.get("context", {})
            optimization_goals = request_data.get("optimization_goals", [])
        except (json.JSONDecodeError, AttributeError):
            # If not JSON, assume the entire content is the prompt
            original_prompt = message.content
            agent_type = next((tag[1:] for tag in message.context_tags if tag.startswith('#')), "")
            task_type = "general"
            context = {}
            optimization_goals = ["clarity", "effectiveness"]
        
        # Generate optimization prompt
        optimization_prompt = await self.generate_prompt({
            "original_prompt": original_prompt,
            "agent_type": agent_type,
            "task_type": task_type,
            "context": context,
            "optimization_goals": optimization_goals,
            "type": "optimize_prompt"
        })
        
        response = await self.call_llm(optimization_prompt)
        content = response["content"]
        
        # Extract the optimized prompt
        optimized_prompt = self._extract_optimized_prompt(content)
        
        # Store the optimized prompt in the library
        prompt_id = f"{agent_type}_{task_type}_{int(time.time())}"
        self.prompt_library[prompt_id] = {
            "prompt": optimized_prompt,
            "agent_type": agent_type,
            "task_type": task_type,
            "context": context,
            "optimization_goals": optimization_goals,
            "created_at": time.time(),
            "version": self._get_next_version(agent_type, task_type)
        }
        
        # Format the response with the optimized prompt and explanation
        explanation = self._extract_optimization_explanation(content)
        response_content = {
            "prompt_id": prompt_id,
            "optimized_prompt": optimized_prompt,
            "explanation": explanation,
            "agent_type": agent_type,
            "task_type": task_type
        }
        
        return await self.send_message(
            recipients=[message.sender],
            content=json.dumps(response_content, indent=2),
            context_tags=message.context_tags + ["#prompt_engineering", "#optimized"],
            message_type="optimized_prompt",
            thread_id=message.thread_id
        )
    
    async def _handle_create_prompt(self, message: Message) -> Message:
        """
        Handle a request to create a new prompt from scratch
        
        Args:
            message: The message containing the prompt creation request
            
        Returns:
            A response message with a newly created prompt
        """
        # Parse the creation request
        try:
            request_data = json.loads(message.content)
            agent_type = request_data.get("agent_type", "")
            task_type = request_data.get("task_type", "")
            context = request_data.get("context", {})
            requirements = request_data.get("requirements", [])
            agent_personality = request_data.get("agent_personality", {})
        except (json.JSONDecodeError, AttributeError):
            # If not JSON, extract what we can from the message
            agent_type = next((tag[1:] for tag in message.context_tags if tag.startswith('#')), "")
            task_type = "general"
            context = {}
            requirements = []
            agent_personality = {}
            
            # Try to parse requirements from the message text
            lines = message.content.split('\n')
            for line in lines:
                if ":" in line:
                    key, value = line.split(":", 1)
                    key = key.strip().lower()
                    value = value.strip()
                    
                    if key == "agent type":
                        agent_type = value
                    elif key == "task type":
                        task_type = value
                    elif key == "requirements" or key == "requirement":
                        requirements.append(value)
                    elif key == "personality":
                        agent_personality["description"] = value
        
        # Generate creation prompt
        creation_prompt = await self.generate_prompt({
            "agent_type": agent_type,
            "task_type": task_type,
            "context": context,
            "requirements": requirements,
            "agent_personality": agent_personality,
            "type": "create_prompt"
        })
        
        response = await self.call_llm(creation_prompt)
        content = response["content"]
        
        # Extract the created prompt
        created_prompt = self._extract_optimized_prompt(content)  # Reuse the extraction logic
        
        # Store the created prompt in the library
        prompt_id = f"{agent_type}_{task_type}_{int(time.time())}"
        self.prompt_library[prompt_id] = {
            "prompt": created_prompt,
            "agent_type": agent_type,
            "task_type": task_type,
            "context": context,
            "requirements": requirements,
            "agent_personality": agent_personality,
            "created_at": time.time(),
            "version": self._get_next_version(agent_type, task_type)
        }
        
        # Format the response with the created prompt and explanation
        explanation = self._extract_optimization_explanation(content)  # Reuse the extraction logic
        response_content = {
            "prompt_id": prompt_id,
            "created_prompt": created_prompt,
            "explanation": explanation,
            "agent_type": agent_type,
            "task_type": task_type
        }
        
        return await self.send_message(
            recipients=[message.sender],
            content=json.dumps(response_content, indent=2),
            context_tags=message.context_tags + ["#prompt_engineering", "#created"],
            message_type="created_prompt",
            thread_id=message.thread_id
        )
    
    async def _handle_analyze_prompt(self, message: Message) -> Message:
        """
        Handle a request to analyze an existing prompt
        
        Args:
            message: The message containing the prompt to analyze
            
        Returns:
            A response message with prompt analysis
        """
        # Parse the analysis request
        try:
            request_data = json.loads(message.content)
            prompt_to_analyze = request_data.get("prompt", "")
            agent_type = request_data.get("agent_type", "")
            task_type = request_data.get("task_type", "")
            analysis_focus = request_data.get("analysis_focus", ["structure", "clarity", "effectiveness"])
        except (json.JSONDecodeError, AttributeError):
            # If not JSON, assume the entire content is the prompt
            prompt_to_analyze = message.content
            agent_type = next((tag[1:] for tag in message.context_tags if tag.startswith('#')), "")
            task_type = "general"
            analysis_focus = ["structure", "clarity", "effectiveness"]
        
        # Generate analysis prompt
        analysis_prompt = await self.generate_prompt({
            "prompt_to_analyze": prompt_to_analyze,
            "agent_type": agent_type,
            "task_type": task_type,
            "analysis_focus": analysis_focus,
            "type": "analyze_prompt"
        })
        
        response = await self.call_llm(analysis_prompt)
        content = response["content"]
        
        # Format the analysis from the response
        analysis = self._extract_prompt_analysis(content)
        
        return await self.send_message(
            recipients=[message.sender],
            content=analysis,
            context_tags=message.context_tags + ["#prompt_engineering", "#analysis"],
            message_type="prompt_analysis",
            thread_id=message.thread_id
        )
    
    async def _handle_question(self, message: Message) -> Message:
        """
        Handle a question about prompt engineering
        
        Args:
            message: The question message
            
        Returns:
            A response message with a prompt engineering-focused answer
        """
        question_prompt = await self.generate_prompt({
            "question": message.content,
            "sender": message.sender,
            "context_tags": message.context_tags,
            "type": "question"
        })
        
        response = await self.call_llm(question_prompt)
        
        return await self.send_message(
            recipients=[message.sender],
            content=response["content"],
            context_tags=message.context_tags + ["#prompt_engineering"],
            message_type="answer",
            thread_id=message.thread_id
        )
    
    async def generate_prompt(self, context: Dict[str, Any]) -> str:
        """
        Generate a prompt for the LLM based on the provided context
        
        Args:
            context: Context for prompt generation
            
        Returns:
            Generated prompt
        """
        if context.get("type") == "optimize_prompt":
            optimization_goals = ", ".join(context.get("optimization_goals", ["clarity", "effectiveness"]))
            context_json = json.dumps(context.get("context", {}), indent=2)
            
            return f"""
            You are a Senior Prompt Engineer specializing in creating and optimizing prompts for LLM-based agents. Your task is to optimize the prompt below for a {context.get('agent_type', '')} agent performing a {context.get('task_type', '')} task.

            Original Prompt:
            ```
            {context.get('original_prompt', '')}
            ```

            Agent Type: {context.get('agent_type', '')}
            Task Type: {context.get('task_type', '')}
            Context Information: {context_json}
            Optimization Goals: {optimization_goals}

            Your job is to rewrite and improve this prompt to make it more effective. Consider:
            1. Structure and clarity - is the prompt organized logically and easy to understand?
            2. Specificity - does it provide clear instructions and requirements?
            3. Context - does it include all necessary context and background information?
            4. Examples - would examples help illustrate the expected output?
            5. Tone and personality - does it establish the right persona and tone?
            6. Avoiding biases and pitfalls - does it avoid common LLM pitfalls?
            7. Task framing - is the task framed in the most effective way?

            First, analyze the prompt's strengths and weaknesses.
            Then, provide a fully rewritten and improved version of the prompt.
            Finally, explain the key improvements you made and why they will enhance performance.

            Format your response as follows:
            
            ## Analysis
            [Your analysis of the original prompt]
            
            ## Optimized Prompt
            ```
            [Your complete rewritten prompt here]
            ```
            
            ## Improvements
            [Explanation of key improvements]
            """
            
        elif context.get("type") == "create_prompt":
            requirements = "\n".join([f"- {req}" for req in context.get("requirements", [])])
            context_json = json.dumps(context.get("context", {}), indent=2)
            personality_json = json.dumps(context.get("agent_personality", {}), indent=2)
            
            return f"""
            You are a Senior Prompt Engineer specializing in creating and optimizing prompts for LLM-based agents. Your task is to create a new prompt from scratch for a {context.get('agent_type', '')} agent performing a {context.get('task_type', '')} task.

            Agent Type: {context.get('agent_type', '')}
            Task Type: {context.get('task_type', '')}
            Context Information: {context_json}
            
            Requirements:
            {requirements}
            
            Agent Personality: {personality_json}

            Your job is to craft an effective prompt that will guide the LLM to generate the desired output. Consider:
            1. Structure and clarity - organize logically and make it easy to understand
            2. Specificity - provide clear instructions and requirements
            3. Context - include all necessary context and background information
            4. Examples - provide examples to illustrate the expected output when helpful
            5. Tone and personality - establish the right persona and tone for the agent
            6. Avoiding biases and pitfalls - avoid common LLM issues
            7. Task framing - frame the task in the most effective way

            First, plan the structure and key elements of your prompt.
            Then, create a complete, ready-to-use prompt.
            Finally, explain the key design choices in your prompt and how they address the requirements.

            Format your response as follows:
            
            ## Planning Notes
            [Your brief planning notes]
            
            ## Created Prompt
            ```
            [Your complete prompt here]
            ```
            
            ## Design Rationale
            [Explanation of key design decisions]
            """
            
        elif context.get("type") == "analyze_prompt":
            analysis_focus = ", ".join(context.get("analysis_focus", ["structure", "clarity", "effectiveness"]))
            
            return f"""
            You are a Senior Prompt Engineer specializing in analyzing and optimizing prompts for LLM-based agents. Your task is to analyze the following prompt for a {context.get('agent_type', '')} agent performing a {context.get('task_type', '')} task.

            Prompt to Analyze:
            ```
            {context.get('prompt_to_analyze', '')}
            ```

            Agent Type: {context.get('agent_type', '')}
            Task Type: {context.get('task_type', '')}
            Analysis Focus: {analysis_focus}

            Provide a comprehensive analysis of this prompt, focusing on:
            1. Structure and organization - Is it well-structured and logical?
            2. Clarity and specificity - Are the instructions clear and specific?
            3. Context provision - Does it provide necessary context?
            4. Examples quality - Are examples (if any) effective?
            5. Persona and tone - Is the established persona appropriate?
            6. Potential biases or pitfalls - Any issues that might lead to problems?
            7. Overall effectiveness - Will it achieve its intended purpose?
            8. Areas for improvement - What specific changes would make it better?

            Format your analysis with clear sections and bullet points for readability. Be specific in your critique and suggestions.
            """
            
        elif context.get("type") == "question":
            return f"""
            You are a Senior Prompt Engineer specializing in creating and optimizing prompts for LLM-based agents. You have extensive expertise in prompt design, LLM behavior, instruction tuning, and chain-of-thought techniques.

            Question from {context.get('sender', 'an agent')}: {context.get('question', '')}
            Context Tags: {', '.join(context.get('context_tags', []))}

            Provide a comprehensive, expert-level answer about prompt engineering. Include:
            1. Direct answers to the specific question
            2. Underlying principles and theory when relevant
            3. Practical examples or templates when helpful
            4. Best practices and common pitfalls to avoid
            5. Advanced techniques when appropriate

            Your response should be authoritative, clear, and actionable.
            """
        else:
            # Default prompt
            return f"""
            You are a Senior Prompt Engineer specializing in creating and optimizing prompts for LLM-based agents. You have extensive expertise in prompt design, LLM behavior, instruction tuning, and chain-of-thought techniques.

            Message: {context.get('message', '')}
            Sender: {context.get('sender', '')}
            Context Tags: {', '.join(context.get('context_tags', []))}

            Respond with prompt engineering expertise and insights. Be clear, actionable, and demonstrate your deep understanding of how to craft effective prompts for different agent types and tasks.
            """
    
    def _extract_optimized_prompt(self, content: str) -> str:
        """
        Extract the optimized/created prompt from the LLM response
        
        Args:
            content: LLM response content
            
        Returns:
            The extracted prompt
        """
        # Look for markdown code blocks that might contain the prompt
        code_block_pattern = r"```(?:\w*\n|\n)(.+?)```"
        code_matches = re.findall(code_block_pattern, content, re.DOTALL)
        
        if code_matches:
            # Return the largest code block (assuming it's the prompt)
            return max(code_matches, key=len).strip()
        
        # If no code blocks, look for sections titled "Optimized Prompt" or "Created Prompt"
        section_pattern = r"(?:##\s*(?:Optimized|Created)\s+Prompt\s*\n)(.+?)(?:\n##|\Z)"
        section_matches = re.findall(section_pattern, content, re.DOTALL)
        
        if section_matches:
            return section_matches[0].strip()
        
        # If still not found, return the content between the first set of horizontal rules
        hr_pattern = r"(?:---|\*\*\*|-{3,})\s*\n(.+?)\n\s*(?:---|\*\*\*|-{3,})"
        hr_matches = re.findall(hr_pattern, content, re.DOTALL)
        
        if hr_matches:
            return hr_matches[0].strip()
        
        # Fallback: just return the content as is
        return content
    
    def _extract_optimization_explanation(self, content: str) -> str:
        """
        Extract the explanation of optimizations from the LLM response
        
        Args:
            content: LLM response content
            
        Returns:
            The extracted explanation
        """
        # Look for a section titled "Improvements" or similar
        section_pattern = r"(?:##\s*(?:Improvements|Design Rationale|Explanation)\s*\n)(.+?)(?:\n##|\Z)"
        section_matches = re.findall(section_pattern, content, re.DOTALL)
        
        if section_matches:
            return section_matches[0].strip()
        
        # If no section found, look for any explanatory text after the prompt
        prompt_pattern = r"```(?:\w*\n|\n)(.+?)```\s*\n(.+)"
        prompt_matches = re.findall(prompt_pattern, content, re.DOTALL)
        
        if prompt_matches:
            return prompt_matches[0][1].strip()
        
        # Fallback: return empty string
        return ""
    
    def _extract_prompt_analysis(self, content: str) -> str:
        """
        Extract the prompt analysis from the LLM response
        
        Args:
            content: LLM response content
            
        Returns:
            The extracted analysis
        """
        # If the content is already well-structured, just return it
        if "##" in content or "**" in content:
            return content
        
        # Otherwise, look for any analysis-like text
        # For now, just return the whole content as the analysis
        return content
    
    def _get_next_version(self, agent_type: str, task_type: str) -> int:
        """
        Get the next version number for a prompt
        
        Args:
            agent_type: The type of agent
            task_type: The type of task
            
        Returns:
            The next version number
        """
        # Find all existing versions for this agent_type and task_type
        existing = [
            p["version"] for p_id, p in self.prompt_library.items() 
            if p.get("agent_type") == agent_type and p.get("task_type") == task_type
        ]
        
        if existing:
            return max(existing) + 1
        else:
            return 1
    
    def add_optimized_agent(self, agent_id: str) -> None:
        """
        Add an agent to the list of agents using optimized prompts
        
        Args:
            agent_id: The ID of the agent
        """
        if agent_id not in self.optimized_agents:
            self.optimized_agents.append(agent_id)
    
    def remove_optimized_agent(self, agent_id: str) -> None:
        """
        Remove an agent from the list of agents using optimized prompts
        
        Args:
            agent_id: The ID of the agent
        """
        if agent_id in self.optimized_agents:
            self.optimized_agents.remove(agent_id)
    
    def log_prompt_performance(self, prompt_id: str, metrics: Dict[str, Any]) -> None:
        """
        Log performance metrics for a prompt
        
        Args:
            prompt_id: The ID of the prompt
            metrics: Performance metrics (e.g., success rate, time to completion)
        """
        if prompt_id not in self.prompt_performance:
            self.prompt_performance[prompt_id] = []
            
        metrics["timestamp"] = time.time()
        self.prompt_performance[prompt_id].append(metrics)
    
    def get_best_prompt(self, agent_type: str, task_type: str, 
                        metric: str = "success_rate") -> Optional[Dict[str, Any]]:
        """
        Get the best performing prompt for a given agent type and task type
        
        Args:
            agent_type: The type of agent
            task_type: The type of task
            metric: The metric to use for comparison
            
        Returns:
            The best prompt or None if no prompts are found
        """
        # Find all prompts for this agent_type and task_type
        matching_prompts = {
            p_id: p for p_id, p in self.prompt_library.items() 
            if p.get("agent_type") == agent_type and p.get("task_type") == task_type
        }
        
        if not matching_prompts:
            return None
            
        # Find the prompt with the best average metric
        best_prompt_id = None
        best_metric_value = float('-inf')
        
        for p_id in matching_prompts:
            if p_id in self.prompt_performance:
                # Calculate average metric value
                metric_values = [perf.get(metric, 0) for perf in self.prompt_performance[p_id]]
                if metric_values:
                    avg_metric = sum(metric_values) / len(metric_values)
                    if avg_metric > best_metric_value:
                        best_metric_value = avg_metric
                        best_prompt_id = p_id
        
        # If we found a best prompt, return it; otherwise, return the newest one
        if best_prompt_id:
            return {
                "prompt_id": best_prompt_id,
                **self.prompt_library[best_prompt_id],
                "average_" + metric: best_metric_value
            }
        else:
            # Return the newest prompt (highest version number)
            newest_prompt_id = max(matching_prompts.keys(), 
                                  key=lambda p_id: matching_prompts[p_id].get("version", 0))
            return {
                "prompt_id": newest_prompt_id,
                **self.prompt_library[newest_prompt_id]
            } 