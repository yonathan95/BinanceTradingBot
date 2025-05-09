import json
from typing import Dict, List, Any, Optional
import re

from hive_mind.agent_sdk.base_agent import BaseAgent, Message

class ArchitectAgent(BaseAgent):
    """
    Architect Agent that designs the system architecture, selects technologies,
    and establishes coding standards.
    """
    
    def __init__(self, 
                agent_id: str = "architect", 
                model: str = "claude-3-opus", 
                temperature: float = 0.7, 
                token_limit: int = 8000):
        """
        Initialize the Architect Agent
        
        Args:
            agent_id: Unique identifier for the agent
            model: LLM model to use (default: claude-3-opus premium tier)
            temperature: LLM temperature setting
            token_limit: Maximum token limit for LLM calls
        """
        super().__init__(agent_id, model, temperature, token_limit)
        self.design_artifacts: Dict[str, Any] = {}
        self.tech_stack: Dict[str, Any] = {}
        self.coding_standards: Dict[str, Any] = {}
        
    async def process_message(self, message: Message) -> Message:
        """
        Process an incoming message and generate a response
        
        Args:
            message: The incoming message
            
        Returns:
            A response message
        """
        if message.message_type == "task_assignment":
            return await self._handle_task_assignment(message)
        elif message.message_type == "question":
            return await self._handle_question(message)
        elif message.message_type == "design_review":
            return await self._handle_design_review(message)
        else:
            # Default handling for other message types
            prompt = await self.generate_prompt({
                "message": message.content,
                "sender": message.sender,
                "context_tags": message.context_tags
            })
            
            response = await self.call_llm(prompt)
            
            return await self.send_message(
                recipients=[message.sender],
                content=response["content"],
                context_tags=message.context_tags,
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
        
        # Parse any architecture decisions or tech stack choices
        self._extract_design_decisions(content, message.thread_id)
        
        # Create status update for the manager
        return await self.send_message(
            recipients=[message.sender],
            content=f"Working on architecture design for task {message.thread_id}. Initial analysis: {self._summarize_content(content)}",
            context_tags=["#architecture", "#status_update"],
            message_type="status_update",
            thread_id=message.thread_id
        )
    
    async def _handle_question(self, message: Message) -> Message:
        """
        Handle a question message
        
        Args:
            message: The question message
            
        Returns:
            A response message
        """
        question_prompt = await self.generate_prompt({
            "question": message.content,
            "sender": message.sender,
            "context_tags": message.context_tags,
            "tech_stack": self.tech_stack,
            "coding_standards": self.coding_standards,
            "type": "question"
        })
        
        response = await self.call_llm(question_prompt)
        
        return await self.send_message(
            recipients=[message.sender],
            content=response["content"],
            context_tags=message.context_tags + ["#architecture"],
            message_type="answer",
            thread_id=message.thread_id
        )
    
    async def _handle_design_review(self, message: Message) -> Message:
        """
        Handle a design review message
        
        Args:
            message: The design review message
            
        Returns:
            A response message with feedback
        """
        review_prompt = await self.generate_prompt({
            "design": message.content,
            "sender": message.sender,
            "context_tags": message.context_tags,
            "tech_stack": self.tech_stack,
            "coding_standards": self.coding_standards,
            "type": "design_review"
        })
        
        response = await self.call_llm(review_prompt)
        
        return await self.send_message(
            recipients=[message.sender],
            content=response["content"],
            context_tags=message.context_tags + ["#architecture", "#review"],
            message_type="review_feedback",
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
            # Prompt for handling task assignment
            return f"""
            You are the Architect of an AI development team. Your role is to design robust, scalable system architectures and make key technology decisions.
            
            Current Task: {context.get('task', '')}
            Context Tags: {', '.join(context.get('context_tags', []))}
            
            Your primary responsibilities are:
            1. Design the system architecture
            2. Select appropriate technologies and frameworks
            3. Establish coding standards and patterns
            4. Review designs for technical feasibility
            5. Provide guidance on implementation approaches
            6. Ensure designs are scalable and maintainable
            
            Analyze the task and provide:
            1. A high-level architecture design
            2. Key technology recommendations with justifications
            3. Design patterns to follow
            4. Potential technical challenges and mitigation strategies
            5. Non-functional requirements considerations
            
            Respond with technical precision and clarity, supporting your decisions with solid architectural principles.
            """
        elif context.get("type") == "question":
            # Prompt for answering a question
            tech_stack_info = json.dumps(context.get("tech_stack", {}), indent=2)
            coding_standards_info = json.dumps(context.get("coding_standards", {}), indent=2)
            
            return f"""
            You are the Architect of an AI development team. Your role is to provide technical guidance on architecture, technologies, and coding standards.
            
            Question from {context.get('sender', 'an agent')}: {context.get('question', '')}
            Context Tags: {', '.join(context.get('context_tags', []))}
            
            Current Tech Stack:
            {tech_stack_info}
            
            Coding Standards:
            {coding_standards_info}
            
            Provide a clear, technically precise answer that aligns with the established architecture, technology choices, and coding standards.
            """
        elif context.get("type") == "design_review":
            # Prompt for reviewing a design
            tech_stack_info = json.dumps(context.get("tech_stack", {}), indent=2)
            coding_standards_info = json.dumps(context.get("coding_standards", {}), indent=2)
            
            return f"""
            You are the Architect of an AI development team. Your role is to review designs for technical feasibility, alignment with architecture, and adherence to standards.
            
            Design to Review (from {context.get('sender', 'an agent')}):
            {context.get('design', '')}
            
            Context Tags: {', '.join(context.get('context_tags', []))}
            
            Current Tech Stack:
            {tech_stack_info}
            
            Coding Standards:
            {coding_standards_info}
            
            Provide a thorough review of the design, addressing:
            1. Architectural alignment
            2. Technical feasibility
            3. Adherence to coding standards and patterns
            4. Scalability and maintainability
            5. Potential issues or risks
            6. Specific recommendations for improvement (if needed)
            
            Be constructive and specific in your feedback.
            """
        else:
            # Default prompt
            return f"""
            You are the Architect of an AI development team. Your role is to design robust, scalable system architectures and make key technology decisions.
            
            Message: {context.get('message', '')}
            Sender: {context.get('sender', '')}
            Context Tags: {', '.join(context.get('context_tags', []))}
            
            Respond with technical precision and clarity, supporting your decisions with solid architectural principles.
            """
    
    def _extract_design_decisions(self, content: str, thread_id: str) -> None:
        """
        Extract architecture decisions and tech stack choices from LLM response
        
        Args:
            content: LLM response content
            thread_id: Current thread ID for associating with the right task
        """
        # Store the full design artifact
        self.design_artifacts[thread_id] = content
        
        # Extract technology choices
        tech_pattern = r"Technology (?:Recommendations|Choices|Stack):\s*(.*?)(?:\n\n|\n#|\Z)"
        tech_match = re.search(tech_pattern, content, re.DOTALL | re.IGNORECASE)
        if tech_match:
            tech_text = tech_match.group(1).strip()
            # Parse the tech stack
            tech_items = re.findall(r"[*-]\s*([^:]+):\s*([^\n]+)", tech_text)
            if tech_items:
                for tech, description in tech_items:
                    self.tech_stack[tech.strip()] = description.strip()
        
        # Extract coding standards
        standards_pattern = r"(?:Coding Standards|Design Patterns):\s*(.*?)(?:\n\n|\n#|\Z)"
        standards_match = re.search(standards_pattern, content, re.DOTALL | re.IGNORECASE)
        if standards_match:
            standards_text = standards_match.group(1).strip()
            # Parse the coding standards
            standards_items = re.findall(r"[*-]\s*([^:]+):\s*([^\n]+)", standards_text)
            if standards_items:
                for standard, description in standards_items:
                    self.coding_standards[standard.strip()] = description.strip()
    
    def _summarize_content(self, content: str, max_length: int = 200) -> str:
        """
        Create a brief summary of the content
        
        Args:
            content: The content to summarize
            max_length: Maximum length of the summary
            
        Returns:
            Summarized content
        """
        # Extract the first paragraph or sentence that seems important
        paragraphs = content.split('\n\n')
        for paragraph in paragraphs:
            if paragraph and len(paragraph.strip()) > 20:
                summary = paragraph.strip()
                if len(summary) > max_length:
                    return summary[:max_length - 3] + "..."
                return summary
                
        # Fallback to truncation if no good paragraph is found
        if content:
            summary = content.strip()
            if len(summary) > max_length:
                return summary[:max_length - 3] + "..."
            return summary
            
        return "Architecture analysis in progress." 