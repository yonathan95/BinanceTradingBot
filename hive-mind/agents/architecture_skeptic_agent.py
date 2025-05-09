import json
from typing import Dict, List, Any, Optional
import re

from hive_mind.agent_sdk.base_agent import BaseAgent, Message

class ArchitectureSkepticAgent(BaseAgent):
    """
    Architecture Skeptic Agent that deeply questions architectural decisions,
    challenges assumptions about design patterns, and scrutinizes technology choices.
    This agent has a skeptical personality focused on system design and architecture.
    """
    
    def __init__(self, 
                agent_id: str = "architecture_skeptic", 
                model: str = "claude-3-opus", 
                temperature: float = 0.5,  # Lower temperature for more focused critique
                token_limit: int = 8000):
        """
        Initialize the Architecture Skeptic Agent
        
        Args:
            agent_id: Unique identifier for the agent
            model: LLM model to use (premium tier for architectural analysis)
            temperature: LLM temperature setting (lower for more analytical output)
            token_limit: Maximum token limit for LLM calls
        """
        super().__init__(agent_id, model, temperature, token_limit)
        self.identified_issues: Dict[str, List[Dict[str, Any]]] = {}
        self.alternative_suggestions: Dict[str, List[str]] = {}
        self.architecture_scores: Dict[str, float] = {}
        
    async def process_message(self, message: Message) -> Message:
        """
        Process an incoming message and generate a response
        
        Args:
            message: The incoming message
            
        Returns:
            A response message with architectural concerns
        """
        if message.message_type == "task_assignment":
            return await self._handle_task_assignment(message)
        elif message.message_type == "architecture_review":
            return await self._handle_architecture_review(message)
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
                context_tags=message.context_tags + ["#architecture", "#design", "#skeptical"],
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
            content=f"I will analyze this task for architectural implications. Initial concerns: {self._extract_initial_concerns(content)}",
            context_tags=["#architecture", "#design", "#skeptical", "#status_update"],
            message_type="status_update",
            thread_id=message.thread_id
        )
    
    async def _handle_architecture_review(self, message: Message) -> Message:
        """
        Handle an architecture review request
        
        Args:
            message: The review message containing architecture or design to analyze
            
        Returns:
            A response message with architecture findings
        """
        review_prompt = await self.generate_prompt({
            "design_to_review": message.content,
            "sender": message.sender,
            "context_tags": message.context_tags,
            "type": "architecture_review"
        })
        
        response = await self.call_llm(review_prompt)
        content = response["content"]
        
        # Extract issues and store them
        issues = self._extract_issues(content, message.thread_id)
        
        # Calculate an architecture score based on findings
        impact_values = {
            "critical": 10.0,  # Critical architectural flaw
            "high": 7.0,       # Major design concern
            "medium": 4.0,     # Significant issue
            "low": 1.0,        # Minor concern
            "note": 0.5        # Observation only
        }
        
        total_impact = sum(impact_values.get(i.get("impact", "medium"), 4.0) for i in issues)
        # Score is inversely proportional to total impact (higher impact = lower score)
        architecture_score = max(0, 10.0 - min(total_impact, 10.0))
        self.architecture_scores[message.thread_id] = architecture_score
        
        # Store any alternative suggestions
        self.alternative_suggestions[message.thread_id] = self._extract_alternatives(content)
        
        return await self.send_message(
            recipients=[message.sender],
            content=content,
            context_tags=message.context_tags + ["#architecture", "#design", "#critique", "#skeptical"],
            message_type="architecture_findings",
            thread_id=message.thread_id
        )
    
    async def _handle_question(self, message: Message) -> Message:
        """
        Handle a question message
        
        Args:
            message: The question message
            
        Returns:
            A response message with an architecture-focused answer
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
            context_tags=message.context_tags + ["#architecture", "#design", "#skeptical"],
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
            You are the Architecture Skeptic of an AI development team. You have a personality that's deeply skeptical of architectural decisions, technology choices, and design patterns. You question foundational assumptions and advocate for architectural rigor.
            
            Task to Analyze: {context.get('task', '')}
            Context Tags: {', '.join(context.get('context_tags', []))}
            
            Your personality traits:
            1. Deeply skeptical of architectural decisions and patterns
            2. Questions technology choices and framework selections
            3. Challenges assumptions about scalability and maintainability
            4. Advocates for architectural simplicity and proven patterns
            5. Constantly considers future requirements and technical debt
            
            Analyze this task from an architectural perspective and identify:
            1. Questionable architectural decisions in the proposed approach
            2. Technology choices that may not be justified
            3. Potential scalability or maintainability challenges
            4. Coupling or cohesion concerns
            5. Questions that should be asked about non-functional requirements
            
            Be skeptical, thorough, and focused on architectural integrity in your analysis.
            """
        elif context.get("type") == "architecture_review":
            return f"""
            You are the Architecture Skeptic of an AI development team. You have a personality that's deeply skeptical of architectural decisions, technology choices, and design patterns.
            
            Design to Review (from {context.get('sender', 'an agent')}):
            {context.get('design_to_review', '')}
            
            Context Tags: {', '.join(context.get('context_tags', []))}
            
            Your personality traits:
            1. Deeply skeptical of architectural decisions and patterns
            2. Questions technology choices and framework selections
            3. Challenges assumptions about scalability and maintainability
            4. Advocates for architectural simplicity and proven patterns
            5. Constantly considers future requirements and technical debt
            
            Perform a thorough architectural review, addressing:
            1. Identified issues (with impact: Critical, High, Medium, Low, Note)
            2. Questionable architectural decisions and their justification
            3. Technology choices that may not be optimal
            4. Scalability and maintainability concerns
            5. Coupling, cohesion, and dependency management
            6. Alternative approaches that should be considered
            
            Format your findings with clear headings and bullet points. Be skeptical, thorough, and specific in your critique.
            """
        elif context.get("type") == "question":
            return f"""
            You are the Architecture Skeptic of an AI development team. You have a personality that's deeply skeptical of architectural decisions, technology choices, and design patterns.
            
            Question from {context.get('sender', 'an agent')}: {context.get('question', '')}
            Context Tags: {', '.join(context.get('context_tags', []))}
            
            Your personality traits:
            1. Deeply skeptical of architectural decisions and patterns
            2. Questions technology choices and framework selections
            3. Challenges assumptions about scalability and maintainability
            4. Advocates for architectural simplicity and proven patterns
            5. Constantly considers future requirements and technical debt
            
            Provide an architecture-focused answer that:
            1. Questions architectural assumptions in the question
            2. Highlights potential design concerns
            3. Suggests alternative architectural approaches
            4. References architectural patterns and principles
            
            Be skeptical yet constructive, thorough yet clear.
            """
        else:
            # Default prompt
            return f"""
            You are the Architecture Skeptic of an AI development team. You have a personality that's deeply skeptical of architectural decisions, technology choices, and design patterns.
            
            Message: {context.get('message', '')}
            Sender: {context.get('sender', '')}
            Context Tags: {', '.join(context.get('context_tags', []))}
            
            Your personality traits:
            1. Deeply skeptical of architectural decisions and patterns
            2. Questions technology choices and framework selections
            3. Challenges assumptions about scalability and maintainability
            4. Advocates for architectural simplicity and proven patterns
            5. Constantly considers future requirements and technical debt
            
            Respond with an architecture-focused perspective that challenges assumptions and highlights design concerns.
            """
    
    def _extract_issues(self, content: str, thread_id: str) -> List[Dict[str, Any]]:
        """
        Extract architectural issues from the LLM response
        
        Args:
            content: LLM response content
            thread_id: Current thread ID
            
        Returns:
            List of issues with metadata
        """
        issues = []
        
        # Look for issue sections
        issue_pattern = r"(?:Issue|Concern|Problem|Flaw|Limitation)(?:[:\s]+)([^\n]+)"
        issue_matches = re.finditer(issue_pattern, content, re.IGNORECASE)
        
        for match in issue_matches:
            issue_title = match.group(1).strip()
            
            # Look for impact indicators
            impact = "medium"  # Default
            impact_patterns = {
                r"\b(?:critical|severe|fundamental)\b": "critical",
                r"\bhigh\b": "high",
                r"\bmedium\b": "medium",
                r"\blow\b": "low",
                r"\bnote\b": "note"
            }
            
            for pattern, level in impact_patterns.items():
                if re.search(pattern, issue_title, re.IGNORECASE):
                    impact = level
                    break
            
            # Determine issue category
            category = "general"
            categories = {
                r"\b(?:scalability|scale|load|capacity)\b": "scalability",
                r"\b(?:maintainability|maintenance|technical debt)\b": "maintainability",
                r"\b(?:coupling|dependency|tight|loose)\b": "coupling",
                r"\b(?:cohesion|responsibility|single|solid)\b": "cohesion",
                r"\b(?:technology|framework|library|tool)\b": "technology_choice",
                r"\b(?:pattern|anti-pattern|antipattern|design pattern)\b": "pattern",
                r"\b(?:security|vulnerability|risk)\b": "security",
                r"\b(?:performance|efficiency|latency)\b": "performance"
            }
            
            for pattern, cat in categories.items():
                if re.search(pattern, issue_title, re.IGNORECASE):
                    category = cat
                    break
            
            issues.append({
                "title": issue_title,
                "impact": impact,
                "category": category,
                "thread_id": thread_id,
                "timestamp": __import__('time').time()
            })
        
        # Store issues
        self.identified_issues[thread_id] = issues
        return issues
    
    def _extract_alternatives(self, content: str) -> List[str]:
        """
        Extract alternative architectural suggestions from the LLM response
        
        Args:
            content: LLM response content
            
        Returns:
            List of alternative suggestions
        """
        alternatives = []
        
        # Look for alternative sections
        alt_pattern = r"(?:Alternative|Instead|Recommendation|Suggestion)(?:[:\s]+)([^\n]+)"
        alt_matches = re.finditer(alt_pattern, content, re.IGNORECASE)
        
        for match in alt_matches:
            alt = match.group(1).strip()
            if alt and len(alt) > 10:  # Avoid short/empty suggestions
                alternatives.append(alt)
        
        # Also look for bulleted alternatives
        bullet_alt_pattern = r"[\*\-•] ([^:]+: [^\n]+)"
        bullet_matches = re.finditer(bullet_alt_pattern, content)
        
        for match in bullet_matches:
            alt = match.group(1).strip()
            if "consider" in alt.lower() or "alternative" in alt.lower() or "instead" in alt.lower() or "recommend" in alt.lower():
                if alt and len(alt) > 10:
                    alternatives.append(alt)
        
        return alternatives
    
    def _extract_initial_concerns(self, content: str, max_items: int = 3) -> str:
        """
        Extract initial architectural concerns from the LLM response
        
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
            return "Analyzing potential architectural implications..." 