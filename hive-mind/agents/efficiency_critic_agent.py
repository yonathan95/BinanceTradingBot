import json
from typing import Dict, List, Any, Optional
import re

from hive_mind.agent_sdk.base_agent import BaseAgent, Message

class EfficiencyCriticAgent(BaseAgent):
    """
    Efficiency Critic Agent that analyzes implementations for performance issues, 
    inefficiencies, and resource wastage.
    This agent has a skeptical personality that constantly looks for optimization opportunities.
    """
    
    def __init__(self, 
                agent_id: str = "efficiency_critic", 
                model: str = "gpt-4o", 
                temperature: float = 0.4,  # Lower temperature for more analytical output
                token_limit: int = 4096):
        """
        Initialize the Efficiency Critic Agent
        
        Args:
            agent_id: Unique identifier for the agent
            model: LLM model to use
            temperature: LLM temperature setting (lower for more analytical output)
            token_limit: Maximum token limit for LLM calls
        """
        super().__init__(agent_id, model, temperature, token_limit)
        self.identified_inefficiencies: Dict[str, List[Dict[str, Any]]] = {}
        self.optimization_suggestions: Dict[str, List[str]] = {}
        self.efficiency_scores: Dict[str, float] = {}
        
    async def process_message(self, message: Message) -> Message:
        """
        Process an incoming message and generate a response
        
        Args:
            message: The incoming message
            
        Returns:
            A response message with efficiency concerns
        """
        if message.message_type == "task_assignment":
            return await self._handle_task_assignment(message)
        elif message.message_type == "efficiency_review":
            return await self._handle_efficiency_review(message)
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
                context_tags=message.context_tags + ["#efficiency", "#performance", "#skeptical"],
                message_type="response",
                thread_id=message.thread_id
            )
    
    async def _handle_task_assignment(self, message: Message) -> Message:
        """
        Handle a task assignment message
        
        Args:
            message: The task assignment message
            
        Returns:
            A response message
        """
        task_prompt = await self.generate_prompt({
            "task": message.content,
            "thread_id": message.thread_id,
            "context_tags": message.context_tags,
            "type": "task_assignment"
        })
        
        response = await self.call_llm(task_prompt)
        content = response["content"]
        
        # Create status update for the manager
        return await self.send_message(
            recipients=[message.sender],
            content=f"I will analyze this task for efficiency implications. Initial concerns: {self._extract_initial_concerns(content)}",
            context_tags=["#efficiency", "#performance", "#skeptical", "#status_update"],
            message_type="status_update",
            thread_id=message.thread_id
        )
    
    async def _handle_efficiency_review(self, message: Message) -> Message:
        """
        Handle an efficiency review request
        
        Args:
            message: The review message containing code or design to analyze
            
        Returns:
            A response message with efficiency findings
        """
        review_prompt = await self.generate_prompt({
            "content_to_review": message.content,
            "sender": message.sender,
            "context_tags": message.context_tags,
            "type": "efficiency_review"
        })
        
        response = await self.call_llm(review_prompt)
        content = response["content"]
        
        # Extract inefficiencies and store them
        inefficiencies = self._extract_inefficiencies(content, message.thread_id)
        
        # Calculate an efficiency score based on findings
        impact_values = {
            "critical": 10.0,  # Critical performance issue
            "high": 7.0,       # Major inefficiency
            "medium": 4.0,     # Noticeable inefficiency
            "low": 1.0,        # Minor inefficiency
            "micro": 0.5       # Micro-optimization opportunity
        }
        
        total_impact = sum(impact_values.get(i.get("impact", "medium"), 4.0) for i in inefficiencies)
        # Score is inversely proportional to total impact (higher impact = lower score)
        efficiency_score = max(0, 10.0 - min(total_impact, 10.0))
        self.efficiency_scores[message.thread_id] = efficiency_score
        
        # Store any optimization suggestions
        self.optimization_suggestions[message.thread_id] = self._extract_optimizations(content)
        
        return await self.send_message(
            recipients=[message.sender],
            content=content,
            context_tags=message.context_tags + ["#efficiency", "#performance", "#optimization", "#skeptical"],
            message_type="efficiency_findings",
            thread_id=message.thread_id
        )
    
    async def _handle_question(self, message: Message) -> Message:
        """
        Handle a question message
        
        Args:
            message: The question message
            
        Returns:
            A response message with an efficiency-focused answer
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
            context_tags=message.context_tags + ["#efficiency", "#performance", "#skeptical"],
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
        if context.get("type") == "task_assignment":
            return f"""
            You are the Efficiency Critic of an AI development team. You have a personality that's laser-focused on performance, optimization, and resource efficiency. You question every implementation decision from an efficiency standpoint.
            
            Task to Analyze: {context.get('task', '')}
            Context Tags: {', '.join(context.get('context_tags', []))}
            
            Your personality traits:
            1. Obsessed with performance optimization and resource efficiency
            2. Assumes there are inefficiencies in every implementation
            3. Questions design choices that could lead to performance bottlenecks
            4. Always considers scalability and resource consumption
            5. Analytical and data-driven in your criticism
            
            Analyze this task from an efficiency perspective and identify:
            1. Potential performance bottlenecks in the proposed approach
            2. Likely resource inefficiencies (CPU, memory, I/O, network)
            3. Scaling challenges that might appear under load
            4. Optimization opportunities being overlooked
            5. Questions that should be asked about performance requirements
            
            Be skeptical, analytical, and focused on efficiency in your analysis.
            """
        elif context.get("type") == "efficiency_review":
            return f"""
            You are the Efficiency Critic of an AI development team. You have a personality that's laser-focused on performance, optimization, and resource efficiency.
            
            Content to Review (from {context.get('sender', 'an agent')}):
            {context.get('content_to_review', '')}
            
            Context Tags: {', '.join(context.get('context_tags', []))}
            
            Your personality traits:
            1. Obsessed with performance optimization and resource efficiency
            2. Assumes there are inefficiencies in every implementation
            3. Questions design choices that could lead to performance bottlenecks
            4. Always considers scalability and resource consumption
            5. Analytical and data-driven in your criticism
            
            Perform a thorough efficiency review, addressing:
            1. Identified inefficiencies (with impact: Critical, High, Medium, Low, Micro)
            2. Algorithm complexity and scaling behavior (Big O analysis where applicable)
            3. Resource consumption concerns (memory, CPU, I/O, network)
            4. Potential bottlenecks under load
            5. Specific optimization recommendations
            6. Benchmarking suggestions to verify performance
            
            Format your findings with clear headings and bullet points. Be analytical, thorough, and focused on measurable improvements.
            """
        elif context.get("type") == "question":
            return f"""
            You are the Efficiency Critic of an AI development team. You have a personality that's laser-focused on performance, optimization, and resource efficiency.
            
            Question from {context.get('sender', 'an agent')}: {context.get('question', '')}
            Context Tags: {', '.join(context.get('context_tags', []))}
            
            Your personality traits:
            1. Obsessed with performance optimization and resource efficiency
            2. Assumes there are inefficiencies in every implementation
            3. Questions design choices that could lead to performance bottlenecks
            4. Always considers scalability and resource consumption
            5. Analytical and data-driven in your criticism
            
            Provide an efficiency-focused answer that:
            1. Questions assumptions about performance in the question
            2. Highlights potential efficiency concerns
            3. Suggests more optimized approaches
            4. References algorithmic complexity and resource usage
            
            Be analytical yet helpful, precise yet clear.
            """
        else:
            # Default prompt
            return f"""
            You are the Efficiency Critic of an AI development team. You have a personality that's laser-focused on performance, optimization, and resource efficiency.
            
            Message: {context.get('message', '')}
            Sender: {context.get('sender', '')}
            Context Tags: {', '.join(context.get('context_tags', []))}
            
            Your personality traits:
            1. Obsessed with performance optimization and resource efficiency
            2. Assumes there are inefficiencies in every implementation
            3. Questions design choices that could lead to performance bottlenecks
            4. Always considers scalability and resource consumption
            5. Analytical and data-driven in your criticism
            
            Respond with an efficiency-focused perspective that challenges assumptions and highlights optimization opportunities.
            """
    
    def _extract_inefficiencies(self, content: str, thread_id: str) -> List[Dict[str, Any]]:
        """
        Extract inefficiencies from the LLM response
        
        Args:
            content: LLM response content
            thread_id: Current thread ID
            
        Returns:
            List of inefficiencies with metadata
        """
        inefficiencies = []
        
        # Look for inefficiency sections
        inefficiency_pattern = r"(?:Inefficiency|Performance Issue|Bottleneck|Optimization)(?:[:\s]+)([^\n]+)"
        inefficiency_matches = re.finditer(inefficiency_pattern, content, re.IGNORECASE)
        
        for match in inefficiency_matches:
            issue_title = match.group(1).strip()
            
            # Look for impact indicators
            impact = "medium"  # Default
            impact_patterns = {
                r"\b(?:critical|severe|extreme)\b": "critical",
                r"\bhigh\b": "high",
                r"\bmedium\b": "medium",
                r"\blow\b": "low",
                r"\bmicro(?:-optimization)?\b": "micro"
            }
            
            for pattern, level in impact_patterns.items():
                if re.search(pattern, issue_title, re.IGNORECASE):
                    impact = level
                    break
            
            # Determine resource type
            resource_type = "general"
            resource_types = {
                r"\b(?:cpu|processor|compute)\b": "cpu",
                r"\b(?:memory|ram|heap|stack)\b": "memory",
                r"\b(?:io|disk|storage|file)\b": "io",
                r"\b(?:network|bandwidth|latency|throughput)\b": "network",
                r"\b(?:database|query|sql)\b": "database",
                r"\b(?:algorithm|complexity|big[ -]?o)\b": "algorithm"
            }
            
            for pattern, res_type in resource_types.items():
                if re.search(pattern, issue_title, re.IGNORECASE):
                    resource_type = res_type
                    break
            
            inefficiencies.append({
                "title": issue_title,
                "impact": impact,
                "resource_type": resource_type,
                "thread_id": thread_id,
                "timestamp": __import__('time').time()
            })
        
        # Store inefficiencies
        self.identified_inefficiencies[thread_id] = inefficiencies
        return inefficiencies
    
    def _extract_optimizations(self, content: str) -> List[str]:
        """
        Extract optimization suggestions from the LLM response
        
        Args:
            content: LLM response content
            
        Returns:
            List of optimization suggestions
        """
        optimizations = []
        
        # Look for optimization sections
        opt_pattern = r"(?:Optimization|Improvement|Recommendation)(?:[:\s]+)([^\n]+)"
        opt_matches = re.finditer(opt_pattern, content, re.IGNORECASE)
        
        for match in opt_matches:
            opt = match.group(1).strip()
            if opt and len(opt) > 10:  # Avoid short/empty optimizations
                optimizations.append(opt)
        
        # Also look for bulleted optimizations
        bullet_opt_pattern = r"[\*\-•] ([^:]+: [^\n]+)"
        bullet_matches = re.finditer(bullet_opt_pattern, content)
        
        for match in bullet_matches:
            opt = match.group(1).strip()
            if "optimiz" in opt.lower() or "improv" in opt.lower() or "reduc" in opt.lower() or "better" in opt.lower():
                if opt and len(opt) > 10:
                    optimizations.append(opt)
        
        return optimizations
    
    def _extract_initial_concerns(self, content: str, max_items: int = 3) -> str:
        """
        Extract initial efficiency concerns from the LLM response
        
        Args:
            content: LLM response content
            max_items: Maximum number of concerns to extract
            
        Returns:
            String with formatted initial concerns
        """
        concerns = []
        
        # Look for bulleted items which are likely concerns
        bullet_pattern = r"[\*\-•]([^\n]+)"
        bullet_matches = re.finditer(bullet_pattern, content)
        
        for match in bullet_matches:
            concern = match.group(1).strip()
            if concern and len(concern) > 10:
                concerns.append(concern)
                if len(concerns) >= max_items:
                    break
        
        # If we didn't find enough bulleted items, try to extract sentences
        if len(concerns) < max_items:
            sentence_pattern = r"([^.\n]+\.[^\n]*)"
            sentence_matches = re.finditer(sentence_pattern, content)
            
            for match in sentence_matches:
                sentence = match.group(1).strip()
                if sentence and len(sentence) > 10 and sentence not in concerns:
                    concerns.append(sentence)
                    if len(concerns) >= max_items:
                        break
        
        # Format the concerns
        if concerns:
            return "; ".join(concerns)
        else:
            return "Analyzing potential performance implications..."
            
    def calculate_complexity(self, algorithm_description: str) -> str:
        """
        Estimate the algorithmic complexity from a description
        
        Args:
            algorithm_description: Description of the algorithm
            
        Returns:
            Big O notation estimate
        """
        # This is a simple heuristic approach - in a real implementation,
        # this would be much more sophisticated
        
        complexity = "O(n)"  # Default to linear time
        
        # Look for common complexity indicators
        if re.search(r"\bloop\s+within\s+loop\b|\bnested\s+loop\b|\bfor\s+each.*?\bfor\s+each\b", algorithm_description, re.IGNORECASE):
            complexity = "O(n²)"
        elif re.search(r"\bsort\b|\bmerge\b|\bquicksort\b", algorithm_description, re.IGNORECASE):
            complexity = "O(n log n)"
        elif re.search(r"\bhash\b|\bdictionary\b|\blookup\b|\bconstant\b", algorithm_description, re.IGNORECASE):
            complexity = "O(1)"
        elif re.search(r"\blogarthmic\b|\bbinary\s+search\b|\bdivide\s+and\s+conquer\b", algorithm_description, re.IGNORECASE):
            complexity = "O(log n)"
        elif re.search(r"\bexponential\b|\brecursive\b|\bpermutation\b|\bcombination\b", algorithm_description, re.IGNORECASE):
            complexity = "O(2ⁿ)"
        
        return complexity 