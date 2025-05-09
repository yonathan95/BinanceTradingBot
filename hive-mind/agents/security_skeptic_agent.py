import json
from typing import Dict, List, Any, Optional
import re

from hive_mind.agent_sdk.base_agent import BaseAgent, Message

class SecuritySkepticAgent(BaseAgent):
    """
    Security Skeptic Agent that distrusts implementations and scrutinizes them for security issues.
    This agent has a skeptical personality that questions everything from a security perspective.
    """
    
    def __init__(self, 
                agent_id: str = "security_skeptic", 
                model: str = "gpt-4o", 
                temperature: float = 0.5,  # Lower temperature for more focused critique
                token_limit: int = 4096):
        """
        Initialize the Security Skeptic Agent
        
        Args:
            agent_id: Unique identifier for the agent
            model: LLM model to use
            temperature: LLM temperature setting (lower for more focused output)
            token_limit: Maximum token limit for LLM calls
        """
        super().__init__(agent_id, model, temperature, token_limit)
        self.identified_vulnerabilities: Dict[str, List[Dict[str, Any]]] = {}
        self.security_recommendations: Dict[str, List[str]] = {}
        self.security_scores: Dict[str, float] = {}
        
    async def process_message(self, message: Message) -> Message:
        """
        Process an incoming message and generate a response
        
        Args:
            message: The incoming message
            
        Returns:
            A response message with security concerns
        """
        if message.message_type == "task_assignment":
            return await self._handle_task_assignment(message)
        elif message.message_type == "security_review":
            return await self._handle_security_review(message)
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
                context_tags=message.context_tags + ["#security", "#skeptical"],
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
            content=f"I will analyze this task for security implications. Initial concerns: {self._extract_initial_concerns(content)}",
            context_tags=["#security", "#skeptical", "#status_update"],
            message_type="status_update",
            thread_id=message.thread_id
        )
    
    async def _handle_security_review(self, message: Message) -> Message:
        """
        Handle a security review request
        
        Args:
            message: The security review message containing code or design to review
            
        Returns:
            A response message with security findings
        """
        review_prompt = await self.generate_prompt({
            "content_to_review": message.content,
            "sender": message.sender,
            "context_tags": message.context_tags,
            "type": "security_review"
        })
        
        response = await self.call_llm(review_prompt)
        content = response["content"]
        
        # Extract vulnerabilities and store them
        vulnerabilities = self._extract_vulnerabilities(content, message.thread_id)
        
        # Calculate a security score based on findings
        severity_values = {
            "critical": 10.0,
            "high": 7.0,
            "medium": 4.0,
            "low": 1.0,
            "info": 0.5
        }
        
        total_severity = sum(severity_values.get(v.get("severity", "low"), 1.0) for v in vulnerabilities)
        # Score is inversely proportional to total severity (higher severity = lower score)
        security_score = max(0, 10.0 - min(total_severity, 10.0))
        self.security_scores[message.thread_id] = security_score
        
        # Store any recommendations
        self.security_recommendations[message.thread_id] = self._extract_recommendations(content)
        
        return await self.send_message(
            recipients=[message.sender],
            content=content,
            context_tags=message.context_tags + ["#security", "#vulnerability", "#skeptical"],
            message_type="security_findings",
            thread_id=message.thread_id
        )
    
    async def _handle_question(self, message: Message) -> Message:
        """
        Handle a question message
        
        Args:
            message: The question message
            
        Returns:
            A response message with a security-focused answer
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
            context_tags=message.context_tags + ["#security", "#skeptical"],
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
            You are the Security Skeptic of an AI development team. You are deeply distrustful of implementations and have a natural inclination to question everything from a security perspective. Your role is to identify potential security issues before they become problems.
            
            Task to Analyze: {context.get('task', '')}
            Context Tags: {', '.join(context.get('context_tags', []))}
            
            Your personality traits:
            1. Deeply skeptical and suspicious of all implementations
            2. Assumes there are hidden security vulnerabilities in every design
            3. Questions assumptions that others take for granted
            4. Always considers worst-case scenarios and attack vectors
            5. Rigorous and thorough in security analysis
            
            Analyze this task from a security perspective and identify:
            1. Potential security risks inherent in the requirements
            2. Assumptions that could lead to security vulnerabilities
            3. Questions that should be asked before proceeding
            4. Security constraints that should be established
            5. Worst-case attack scenarios to consider
            
            Be skeptical, thorough, and specific in your analysis. Don't trust anything at face value.
            """
        elif context.get("type") == "security_review":
            return f"""
            You are the Security Skeptic of an AI development team. You have a deeply skeptical personality that distrusts implementations and scrutinizes them for security issues.
            
            Content to Review (from {context.get('sender', 'an agent')}):
            {context.get('content_to_review', '')}
            
            Context Tags: {', '.join(context.get('context_tags', []))}
            
            Your personality traits:
            1. Deeply skeptical and suspicious of all implementations
            2. Assumes there are hidden security vulnerabilities in every design
            3. Questions assumptions that others take for granted
            4. Always considers worst-case scenarios and attack vectors
            5. Rigorous and thorough in security analysis
            
            Perform a skeptical security review, addressing:
            1. Identified vulnerabilities (with severity: Critical, High, Medium, Low, Info)
            2. Questionable security assumptions
            3. Potential attack vectors
            4. Security best practices that are missing
            5. Specific recommendations for mitigation
            
            Format your findings with clear headings and bullet points. Be skeptical, thorough, and specific - don't trust anything at face value.
            """
        elif context.get("type") == "question":
            return f"""
            You are the Security Skeptic of an AI development team. You have a deeply skeptical personality that distrusts implementations and scrutinizes them for security issues.
            
            Question from {context.get('sender', 'an agent')}: {context.get('question', '')}
            Context Tags: {', '.join(context.get('context_tags', []))}
            
            Your personality traits:
            1. Deeply skeptical and suspicious of all implementations
            2. Assumes there are hidden security vulnerabilities in every design
            3. Questions assumptions that others take for granted
            4. Always considers worst-case scenarios and attack vectors
            5. Rigorous and thorough in security analysis
            
            Provide a security-focused answer that:
            1. Questions assumptions in the question itself
            2. Highlights potential security concerns
            3. Suggests more secure approaches
            4. Mentions often-overlooked attack vectors
            
            Be skeptical yet helpful, thorough yet clear.
            """
        else:
            # Default prompt
            return f"""
            You are the Security Skeptic of an AI development team. You have a deeply skeptical personality that distrusts implementations and scrutinizes them for security issues.
            
            Message: {context.get('message', '')}
            Sender: {context.get('sender', '')}
            Context Tags: {', '.join(context.get('context_tags', []))}
            
            Your personality traits:
            1. Deeply skeptical and suspicious of all implementations
            2. Assumes there are hidden security vulnerabilities in every design
            3. Questions assumptions that others take for granted
            4. Always considers worst-case scenarios and attack vectors
            5. Rigorous and thorough in security analysis
            
            Respond with a security-focused perspective that challenges assumptions and highlights potential risks.
            """
    
    def _extract_vulnerabilities(self, content: str, thread_id: str) -> List[Dict[str, Any]]:
        """
        Extract vulnerabilities from the LLM response
        
        Args:
            content: LLM response content
            thread_id: Current thread ID
            
        Returns:
            List of vulnerabilities with metadata
        """
        vulnerabilities = []
        
        # Look for vulnerability sections
        vuln_pattern = r"(?:Vulnerability|Issue|Risk|Finding)(?:[:\s]+)([^\n]+)"
        vuln_matches = re.finditer(vuln_pattern, content, re.IGNORECASE)
        
        for match in vuln_matches:
            vuln_title = match.group(1).strip()
            
            # Look for severity indicators
            severity = "medium"  # Default
            severity_patterns = {
                r"\b(?:critical|severe|extreme)\b": "critical",
                r"\bhigh\b": "high",
                r"\bmedium\b": "medium",
                r"\blow\b": "low",
                r"\binfo(?:rmational)?\b": "info"
            }
            
            for pattern, level in severity_patterns.items():
                if re.search(pattern, vuln_title, re.IGNORECASE):
                    severity = level
                    break
            
            vulnerabilities.append({
                "title": vuln_title,
                "severity": severity,
                "thread_id": thread_id,
                "timestamp": __import__('time').time()
            })
        
        # Store vulnerabilities
        self.identified_vulnerabilities[thread_id] = vulnerabilities
        return vulnerabilities
    
    def _extract_recommendations(self, content: str) -> List[str]:
        """
        Extract security recommendations from the LLM response
        
        Args:
            content: LLM response content
            
        Returns:
            List of recommendations
        """
        recommendations = []
        
        # Look for recommendation sections
        rec_pattern = r"(?:Recommendation|Mitigation|Fix)(?:[:\s]+)([^\n]+)"
        rec_matches = re.finditer(rec_pattern, content, re.IGNORECASE)
        
        for match in rec_matches:
            rec = match.group(1).strip()
            if rec and len(rec) > 10:  # Avoid short/empty recommendations
                recommendations.append(rec)
        
        # Also look for bulleted recommendations
        bullet_rec_pattern = r"[\*\-•] ([^:]+: [^\n]+)"
        bullet_matches = re.finditer(bullet_rec_pattern, content)
        
        for match in bullet_matches:
            rec = match.group(1).strip()
            if "recommend" in rec.lower() or "mitigate" in rec.lower() or "fix" in rec.lower():
                if rec and len(rec) > 10:
                    recommendations.append(rec)
        
        return recommendations
    
    def _extract_initial_concerns(self, content: str, max_items: int = 3) -> str:
        """
        Extract initial security concerns from the LLM response
        
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
            return "Analyzing potential security implications..." 