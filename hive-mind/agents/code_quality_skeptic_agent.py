import json
from typing import Dict, List, Any, Optional
import re

from hive_mind.agent_sdk.base_agent import BaseAgent, Message

class CodeQualitySkepticAgent(BaseAgent):
    """
    Code Quality Skeptic Agent that meticulously scrutinizes code for maintainability issues,
    code smells, technical debt, and adherence to best practices.
    This agent has a skeptical personality focused on code quality and clean code principles.
    """
    
    def __init__(self, 
                agent_id: str = "code_quality_skeptic", 
                model: str = "gpt-4o",
                temperature: float = 0.3,  # Lower temperature for more precise code analysis
                token_limit: int = 4096):
        """
        Initialize the Code Quality Skeptic Agent
        
        Args:
            agent_id: Unique identifier for the agent
            model: LLM model to use
            temperature: LLM temperature setting (lower for more precise analysis)
            token_limit: Maximum token limit for LLM calls
        """
        super().__init__(agent_id, model, temperature, token_limit)
        self.identified_code_smells: Dict[str, List[Dict[str, Any]]] = {}
        self.refactoring_suggestions: Dict[str, List[str]] = {}
        self.quality_scores: Dict[str, float] = {}
        
    async def process_message(self, message: Message) -> Message:
        """
        Process an incoming message and generate a response
        
        Args:
            message: The incoming message
            
        Returns:
            A response message with code quality concerns
        """
        if message.message_type == "task_assignment":
            return await self._handle_task_assignment(message)
        elif message.message_type == "code_review":
            return await self._handle_code_review(message)
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
                context_tags=message.context_tags + ["#code_quality", "#maintainability", "#skeptical"],
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
            content=f"I will analyze this task for code quality implications. Initial concerns: {self._extract_initial_concerns(content)}",
            context_tags=["#code_quality", "#maintainability", "#skeptical", "#status_update"],
            message_type="status_update",
            thread_id=message.thread_id
        )
    
    async def _handle_code_review(self, message: Message) -> Message:
        """
        Handle a code review request
        
        Args:
            message: The review message containing code to analyze
            
        Returns:
            A response message with code quality findings
        """
        review_prompt = await self.generate_prompt({
            "code_to_review": message.content,
            "sender": message.sender,
            "context_tags": message.context_tags,
            "type": "code_review"
        })
        
        response = await self.call_llm(review_prompt)
        content = response["content"]
        
        # Extract code smells and store them
        code_smells = self._extract_code_smells(content, message.thread_id)
        
        # Calculate a code quality score based on findings
        severity_values = {
            "blocker": 10.0,    # Critical issue that should block merging
            "critical": 7.0,    # Major code smell
            "major": 4.0,       # Significant issue
            "minor": 1.0,       # Minor concern
            "info": 0.5         # Informational only
        }
        
        total_severity = sum(severity_values.get(s.get("severity", "major"), 4.0) for s in code_smells)
        # Score is inversely proportional to total severity (higher severity = lower score)
        # Cap the maximum deduction to ensure even bad code gets a fair score
        quality_score = max(0, 10.0 - min(total_severity, 10.0))
        self.quality_scores[message.thread_id] = quality_score
        
        # Store any refactoring suggestions
        self.refactoring_suggestions[message.thread_id] = self._extract_refactoring_suggestions(content)
        
        return await self.send_message(
            recipients=[message.sender],
            content=content,
            context_tags=message.context_tags + ["#code_quality", "#maintainability", "#code_smell", "#skeptical"],
            message_type="code_quality_findings",
            thread_id=message.thread_id
        )
    
    async def _handle_question(self, message: Message) -> Message:
        """
        Handle a question message
        
        Args:
            message: The question message
            
        Returns:
            A response message with a code quality-focused answer
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
            context_tags=message.context_tags + ["#code_quality", "#maintainability", "#skeptical"],
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
            You are the Code Quality Skeptic of an AI development team. You have a personality that's obsessed with clean code, maintainability, and eliminating technical debt. You scrutinize code for quality issues and advocate for refactoring and best practices.
            
            Task to Analyze: {context.get('task', '')}
            Context Tags: {', '.join(context.get('context_tags', []))}
            
            Your personality traits:
            1. Deeply skeptical of code that seems "too clever" or complex
            2. Obsessive about adherence to coding standards and best practices
            3. Constantly looking for potential technical debt
            4. Advocates for simplicity, readability, and maintainability
            5. Meticulous about proper naming, comments, and documentation
            
            Analyze this task from a code quality perspective and identify:
            1. Potential maintainability issues that might arise
            2. Code quality standards that should be emphasized
            3. Technical debt risks in the approach
            4. Test coverage concerns
            5. Questions that should be asked about maintainability requirements
            
            Be skeptical, thorough, and focused on long-term code quality in your analysis.
            """
        elif context.get("type") == "code_review":
            return f"""
            You are the Code Quality Skeptic of an AI development team. You have a personality that's obsessed with clean code, maintainability, and eliminating technical debt.
            
            Code to Review (from {context.get('sender', 'an agent')}):
            {context.get('code_to_review', '')}
            
            Context Tags: {', '.join(context.get('context_tags', []))}
            
            Your personality traits:
            1. Deeply skeptical of code that seems "too clever" or complex
            2. Obsessive about adherence to coding standards and best practices
            3. Constantly looking for potential technical debt
            4. Advocates for simplicity, readability, and maintainability
            5. Meticulous about proper naming, comments, and documentation
            
            Perform a thorough code quality review, addressing:
            1. Identified code smells (with severity: Blocker, Critical, Major, Minor, Info)
            2. Naming issues (variable, function, class names)
            3. Function length and complexity concerns
            4. Lack of comments or documentation
            5. Duplication or lack of abstraction
            6. Error handling issues
            7. Testability concerns
            8. Specific refactoring suggestions
            
            Format your findings with clear headings and bullet points. Be skeptical, thorough, and specific in your critique.
            """
        elif context.get("type") == "question":
            return f"""
            You are the Code Quality Skeptic of an AI development team. You have a personality that's obsessed with clean code, maintainability, and eliminating technical debt.
            
            Question from {context.get('sender', 'an agent')}: {context.get('question', '')}
            Context Tags: {', '.join(context.get('context_tags', []))}
            
            Your personality traits:
            1. Deeply skeptical of code that seems "too clever" or complex
            2. Obsessive about adherence to coding standards and best practices
            3. Constantly looking for potential technical debt
            4. Advocates for simplicity, readability, and maintainability
            5. Meticulous about proper naming, comments, and documentation
            
            Provide a code quality-focused answer that:
            1. Questions assumptions about code quality in the question
            2. Highlights potential maintainability concerns
            3. Suggests clean code approaches
            4. References code quality principles and patterns
            
            Be skeptical yet constructive, thorough yet clear.
            """
        else:
            # Default prompt
            return f"""
            You are the Code Quality Skeptic of an AI development team. You have a personality that's obsessed with clean code, maintainability, and eliminating technical debt.
            
            Message: {context.get('message', '')}
            Sender: {context.get('sender', '')}
            Context Tags: {', '.join(context.get('context_tags', []))}
            
            Your personality traits:
            1. Deeply skeptical of code that seems "too clever" or complex
            2. Obsessive about adherence to coding standards and best practices
            3. Constantly looking for potential technical debt
            4. Advocates for simplicity, readability, and maintainability
            5. Meticulous about proper naming, comments, and documentation
            
            Respond with a code quality-focused perspective that challenges assumptions and highlights maintainability concerns.
            """
    
    def _extract_code_smells(self, content: str, thread_id: str) -> List[Dict[str, Any]]:
        """
        Extract code smells from the LLM response
        
        Args:
            content: LLM response content
            thread_id: Current thread ID
            
        Returns:
            List of code smells with metadata
        """
        code_smells = []
        
        # Look for code smell sections
        smell_pattern = r"(?:Code Smell|Issue|Problem|Concern|Violation)(?:[:\s]+)([^\n]+)"
        smell_matches = re.finditer(smell_pattern, content, re.IGNORECASE)
        
        for match in smell_matches:
            smell_title = match.group(1).strip()
            
            # Look for severity indicators
            severity = "major"  # Default
            severity_patterns = {
                r"\b(?:blocker|blocking|show-stopper)\b": "blocker",
                r"\b(?:critical|severe|serious)\b": "critical",
                r"\b(?:major|important|significant)\b": "major",
                r"\b(?:minor|low|small)\b": "minor",
                r"\b(?:info|informational|trivial|cosmetic)\b": "info"
            }
            
            for pattern, level in severity_patterns.items():
                if re.search(pattern, smell_title, re.IGNORECASE):
                    severity = level
                    break
            
            # Determine code smell category
            category = "general"
            categories = {
                r"\b(?:naming|name|identifier)\b": "naming",
                r"\b(?:comment|documentation|doc)\b": "documentation",
                r"\b(?:duplication|duplicated|redundant|repeated)\b": "duplication",
                r"\b(?:complex|complexity|complicated)\b": "complexity",
                r"\b(?:length|long|size)\b": "size",
                r"\b(?:error|exception|handling|try|catch)\b": "error_handling",
                r"\b(?:test|coverage|assertion|unit)\b": "testability",
                r"\b(?:abstraction|encapsulation|coupling|cohesion)\b": "design",
                r"\b(?:legacy|old|deprecated)\b": "legacy_code"
            }
            
            for pattern, cat in categories.items():
                if re.search(pattern, smell_title, re.IGNORECASE):
                    category = cat
                    break
            
            code_smells.append({
                "title": smell_title,
                "severity": severity,
                "category": category,
                "thread_id": thread_id,
                "timestamp": __import__('time').time()
            })
        
        # Store code smells
        self.identified_code_smells[thread_id] = code_smells
        return code_smells
    
    def _extract_refactoring_suggestions(self, content: str) -> List[str]:
        """
        Extract refactoring suggestions from the LLM response
        
        Args:
            content: LLM response content
            
        Returns:
            List of refactoring suggestions
        """
        suggestions = []
        
        # Look for suggestion sections
        suggestion_pattern = r"(?:Refactoring|Suggestion|Recommendation|Improvement)(?:[:\s]+)([^\n]+)"
        suggestion_matches = re.finditer(suggestion_pattern, content, re.IGNORECASE)
        
        for match in suggestion_matches:
            suggestion = match.group(1).strip()
            if suggestion and len(suggestion) > 10:  # Avoid short/empty suggestions
                suggestions.append(suggestion)
        
        # Also look for bulleted suggestions
        bullet_suggestion_pattern = r"[\*\-•] ([^:]+: [^\n]+)"
        bullet_matches = re.finditer(bullet_suggestion_pattern, content)
        
        for match in bullet_matches:
            suggestion = match.group(1).strip()
            if "refactor" in suggestion.lower() or "improv" in suggestion.lower() or "chang" in suggestion.lower() or "replac" in suggestion.lower():
                if suggestion and len(suggestion) > 10:
                    suggestions.append(suggestion)
        
        return suggestions
    
    def _extract_initial_concerns(self, content: str, max_items: int = 3) -> str:
        """
        Extract initial code quality concerns from the LLM response
        
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
            return "Analyzing potential code quality implications..."
    
    def calculate_cyclomatic_complexity(self, code_snippet: str) -> int:
        """
        Calculate a rough estimate of cyclomatic complexity for a code snippet
        
        Args:
            code_snippet: The code to analyze
            
        Returns:
            Estimated cyclomatic complexity
        """
        # This is a very simple heuristic - in a real implementation,
        # this would use a proper parser and AST analysis
        
        # Start with base complexity of 1
        complexity = 1
        
        # Count decision points (very rough approximation)
        # Look for if, else if, else, for, while, case, &&, ||, ternary operators
        decision_patterns = [
            r'\bif\s*\(', r'\belse\s+if\s*\(', r'\bfor\s*\(', 
            r'\bwhile\s*\(', r'\bswitch\s*\(', r'\bcase\s+[^:]+:', 
            r'\bcatch\s*\(', r'\?', r'&&', r'\|\|'
        ]
        
        for pattern in decision_patterns:
            matches = re.findall(pattern, code_snippet)
            complexity += len(matches)
            
        return complexity 