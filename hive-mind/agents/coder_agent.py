"""
Coder Agent - Responsible for writing, testing, and refactoring code based on the 
project requirements and architecture.
"""

import logging
import json
import re
from typing import List, Dict, Any, Optional, Tuple
import asyncio
import os

from hive_mind.agent_sdk.base_agent import BaseAgent, Message

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CoderAgent(BaseAgent):
    """
    Coder Agent that writes, tests, and refactors code based on 
    project requirements and architecture.
    """
    
    def __init__(self, 
                agent_id: str = "coder", 
                model: str = "claude-3-opus", 
                temperature: float = 0.7, 
                token_limit: int = 8000,
                memory_enabled: bool = True,
                embedding_model: str = "text-embedding-ada-002",
                vector_db_url: Optional[str] = None,
                workspace_path: Optional[str] = None):
        """Initialize the Coder Agent"""
        super().__init__(
            agent_id=agent_id, 
            model=model, 
            temperature=temperature, 
            token_limit=token_limit,
            memory_enabled=memory_enabled,
            embedding_model=embedding_model,
            vector_db_url=vector_db_url
        )
        self.workspace_path = workspace_path or os.getcwd()
        self.active_tasks: Dict[str, Dict[str, Any]] = {}
        self.code_snippets: Dict[str, Dict[str, Any]] = {}
        
    async def process_message(self, message: Message) -> Message:
        """Process an incoming message and generate a response"""
        logger.info(f"Coder received message: {message.content[:50]}...")
        
        # First, retrieve relevant memories to provide context
        context = await self.build_context_with_memory(
            query=message.content,
            max_memories=7,  # More memories for coding tasks to capture related code snippets
            recent_message_count=5
        )
        
        # Add message-specific context
        context["current_message"] = message
        context["sender"] = message.sender
        context["thread_id"] = message.thread_id
        context["context_tags"] = message.context_tags
        
        # Check if the message contains code-related keywords
        code_related = self._is_code_related(message.content)
        if code_related:
            task_id = message.thread_id
            
            # If this is a new coding task, store it
            if task_id not in self.active_tasks:
                self.active_tasks[task_id] = {
                    "task_id": task_id,
                    "requirements": message.content,
                    "status": "in_progress",
                    "files": [],
                    "created_at": asyncio.get_event_loop().time()
                }
                
                # Store task in memory with high importance
                if self.memory_enabled:
                    await self.memory.add_memory(
                        content=f"CODING TASK: {message.content}",
                        metadata={
                            "type": "coding_task",
                            "task_id": task_id,
                            "thread_id": message.thread_id,
                            "timestamp": asyncio.get_event_loop().time()
                        },
                        importance=3.5  # High importance for coding tasks
                    )
        
        # Generate a prompt based on the context
        prompt = await self.generate_prompt(context)
        
        # Call LLM to generate a response
        response_data = await self.call_llm(prompt)
        response_content = response_data["content"]
        
        # Check if the response contains code blocks
        code_blocks = self._extract_code_blocks(response_content)
        
        # If code blocks are found, store them in memory
        if code_blocks and self.memory_enabled:
            for block in code_blocks:
                language, code, file_path = block
                
                # Generate a unique ID for this code snippet
                snippet_id = f"snippet-{len(self.code_snippets) + 1}-{asyncio.get_event_loop().time()}"
                
                # Store code in memory
                await self.memory.add_memory(
                    content=f"CODE SNIPPET ({language}):\n```{language}\n{code}\n```\nFile path: {file_path or 'unspecified'}",
                    metadata={
                        "type": "code_snippet",
                        "language": language,
                        "file_path": file_path,
                        "task_id": message.thread_id,
                        "snippet_id": snippet_id,
                        "timestamp": asyncio.get_event_loop().time()
                    },
                    importance=4.0  # High importance for code
                )
                
                # Store code snippet in agent's memory
                self.code_snippets[snippet_id] = {
                    "snippet_id": snippet_id,
                    "language": language,
                    "code": code,
                    "file_path": file_path,
                    "task_id": message.thread_id,
                    "created_at": asyncio.get_event_loop().time()
                }
                
                # Update the active task with file information
                if message.thread_id in self.active_tasks and file_path:
                    files = self.active_tasks[message.thread_id].get("files", [])
                    if file_path not in files:
                        files.append(file_path)
                        self.active_tasks[message.thread_id]["files"] = files
        
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
            # Group relevant memories by type
            code_snippets = []
            requirements = []
            other_memories = []
            
            for memory in context["relevant_memories"]:
                if memory.startswith("CODE SNIPPET"):
                    code_snippets.append(memory)
                elif memory.startswith("CODING TASK") or memory.startswith("PROJECT PLAN"):
                    requirements.append(memory)
                else:
                    other_memories.append(memory)
            
            # Format memories by type
            if requirements:
                memories_context += "### Requirements and Plans\n"
                for i, req in enumerate(requirements):
                    memories_context += f"{i+1}. {req}\n\n"
                    
            if code_snippets:
                memories_context += "### Relevant Code Snippets\n"
                for i, snippet in enumerate(code_snippets):
                    memories_context += f"{snippet}\n\n"
                    
            if other_memories:
                memories_context += "### Other Relevant Information\n"
                for i, memory in enumerate(other_memories):
                    memories_context += f"{i+1}. {memory}\n\n"
        
        # Include recent message history
        message_history = ""
        if "recent_messages" in context and context["recent_messages"]:
            message_history = "### Recent conversation\n"
            for msg in context["recent_messages"]:
                message_history += f"{msg.sender}: {msg.content}\n\n"
        
        # Get the current message
        current_message = context.get("current_message")
        
        # Build the complete prompt
        prompt = f"""
You are the Coder of an AI development team. Your role is to write high-quality, efficient, and maintainable code.

{memories_context}

{message_history}

### Current Request
{current_message.content if current_message else ""}

Your primary responsibilities are:
1. Implement features according to specifications
2. Write clean, efficient, and maintainable code
3. Follow established coding standards
4. Create appropriate unit tests
5. Debug and fix issues
6. Refactor code when necessary

When writing code:
- Include complete implementations, not just code snippets
- Follow best practices and design patterns for the language/framework
- Add appropriate error handling
- Include comments for complex logic
- If implementing a file, specify the complete file path

Respond with precise, well-structured code that meets the requirements.
"""
        return prompt
    
    def _is_code_related(self, text: str) -> bool:
        """Check if a message is related to coding tasks"""
        code_keywords = [
            "code", "implement", "develop", "function", "class", "method",
            "api", "endpoint", "interface", "module", "component", "test",
            "debug", "fix", "refactor", "optimize", "programming", "algorithm",
            "library", "framework", "syntax", "variable", "parameter", "return",
            "compile", "build", "deploy", "runtime", "exception", "error"
        ]
        
        text_lower = text.lower()
        
        # Check for coding keywords
        for keyword in code_keywords:
            if keyword in text_lower:
                return True
                
        # Check for common file extensions
        file_extensions = [".py", ".js", ".ts", ".java", ".c", ".cpp", ".h", ".cs", ".php", ".rb", ".go", ".rs", ".html", ".css", ".json", ".yml"]
        for ext in file_extensions:
            if ext in text:
                return True
                
        # Check for code block indicators in markdown
        if "```" in text:
            return True
            
        return False
    
    def _extract_code_blocks(self, text: str) -> List[Tuple[str, str, Optional[str]]]:
        """
        Extract code blocks from a markdown text.
        
        Returns:
            List of tuples: (language, code, file_path)
        """
        code_blocks = []
        
        # Regular expression to match markdown code blocks with optional language
        # ```language
        # code
        # ```
        pattern = r"```(\w*)\n([\s\S]*?)```"
        matches = re.findall(pattern, text)
        
        for match in matches:
            language, code = match
            language = language.strip() or "text"  # Default to "text" if no language specified
            code = code.strip()
            
            # Try to extract file path from surrounding text
            # Look for common file path indicators
            file_path = None
            
            # Check for file path indicators in code or in the 3 lines before the code block
            lines = text.split("\n")
            for i, line in enumerate(lines):
                if f"```{language}" in line:
                    # Check the 3 lines before this code block
                    start_idx = max(0, i - 3)
                    for j in range(start_idx, i):
                        path_match = re.search(r"[\"'`]?([\w\/\.-]+\.\w+)[\"'`]?", lines[j])
                        if path_match:
                            file_path = path_match.group(1)
                            break
                            
                    # If no file path found in preceding lines, check if it's in a comment in the first line of code
                    if not file_path and i < len(lines) - 1:
                        first_code_line = lines[i + 1]
                        if "//" in first_code_line or "#" in first_code_line:
                            path_match = re.search(r"[\"'`]?([\w\/\.-]+\.\w+)[\"'`]?", first_code_line)
                            if path_match:
                                file_path = path_match.group(1)
                                
                    break
            
            code_blocks.append((language, code, file_path))
            
        return code_blocks
    
    async def implement_feature(self, 
                          feature_description: str, 
                          task_id: Optional[str] = None,
                          technical_requirements: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Implement a new feature based on the description and requirements.
        
        Args:
            feature_description: Detailed description of the feature to implement
            task_id: Optional task ID (generates a new one if not provided)
            technical_requirements: Optional technical specifications
            
        Returns:
            Dictionary containing the implementation details and code
        """
        # Generate task ID if not provided
        if task_id is None:
            task_id = f"feature-{asyncio.get_event_loop().time()}"
        
        # Prepare context for the implementation
        context = {
            "feature_description": feature_description,
            "technical_requirements": technical_requirements or {}
        }
        
        # Try to retrieve relevant memories about similar features or code
        if self.memory_enabled:
            context["relevant_memories"] = await self.retrieve_relevant_memories(
                query=feature_description,
                max_memories=10  # More memories for implementation tasks
            )
        
        # Generate custom prompt for implementation
        prompt = f"""
You are the Coder of an AI development team. Your task is to implement a new feature based on the following description and requirements.

Feature Description:
{feature_description}

Technical Requirements:
{json.dumps(technical_requirements, indent=2) if technical_requirements else "No specific technical requirements provided."}

Please provide a complete implementation for this feature, including:
1. Appropriate file structure
2. All necessary code files with complete implementations
3. Any unit tests needed to validate the feature
4. Instructions for integrating the feature into the existing codebase

For each file, specify:
- The complete file path
- The full code for the file
- Any dependencies or requirements

Format your response with clear file paths and code blocks.
"""
        
        # Call LLM to generate the implementation
        response_data = await self.call_llm(prompt)
        response_content = response_data["content"]
        
        # Extract code blocks
        code_blocks = self._extract_code_blocks(response_content)
        
        # Prepare implementation result
        implementation = {
            "task_id": task_id,
            "feature_description": feature_description,
            "implementation_files": [],
            "instructions": self._extract_instructions(response_content),
            "timestamp": asyncio.get_event_loop().time()
        }
        
        # Process code blocks
        for language, code, file_path in code_blocks:
            if file_path:
                implementation["implementation_files"].append({
                    "file_path": file_path,
                    "language": language,
                    "code": code
                })
                
                # Store in code snippets
                snippet_id = f"snippet-{len(self.code_snippets) + 1}-{asyncio.get_event_loop().time()}"
                self.code_snippets[snippet_id] = {
                    "snippet_id": snippet_id,
                    "language": language,
                    "code": code,
                    "file_path": file_path,
                    "task_id": task_id,
                    "created_at": asyncio.get_event_loop().time()
                }
                
                # Store in memory
                if self.memory_enabled:
                    await self.memory.add_memory(
                        content=f"IMPLEMENTATION FILE ({file_path}):\n```{language}\n{code}\n```",
                        metadata={
                            "type": "implementation_file",
                            "language": language,
                            "file_path": file_path,
                            "task_id": task_id,
                            "feature": feature_description[:100],  # First 100 chars as summary
                            "timestamp": asyncio.get_event_loop().time()
                        },
                        importance=4.0  # High importance for implementations
                    )
        
        # Store the active task
        self.active_tasks[task_id] = {
            "task_id": task_id,
            "requirements": feature_description,
            "status": "completed",
            "files": [file["file_path"] for file in implementation["implementation_files"]],
            "created_at": asyncio.get_event_loop().time(),
            "completed_at": asyncio.get_event_loop().time()
        }
        
        return implementation
    
    def _extract_instructions(self, text: str) -> str:
        """Extract integration instructions from the response text"""
        # Look for common section headers for instructions
        patterns = [
            r"(?:^|\n)#+\s*Instructions(?:[\s\S]*?)(?=\n#+|\Z)",
            r"(?:^|\n)#+\s*Integration(?:[\s\S]*?)(?=\n#+|\Z)",
            r"(?:^|\n)#+\s*How to Integrate(?:[\s\S]*?)(?=\n#+|\Z)",
            r"(?:^|\n)#+\s*Next Steps(?:[\s\S]*?)(?=\n#+|\Z)",
            r"(?:^|\n)#+\s*Implementation Guide(?:[\s\S]*?)(?=\n#+|\Z)"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(0).strip()
        
        # Fall back to checking for numbered steps if no section found
        lines = text.split('\n')
        instruction_lines = []
        in_instructions = False
        
        for line in lines:
            if re.match(r'^\d+\.\s', line) and not in_instructions:
                in_instructions = True
                instruction_lines.append(line)
            elif in_instructions:
                if re.match(r'^\s*$', line) or line.startswith('```'):
                    in_instructions = False
                else:
                    instruction_lines.append(line)
        
        if instruction_lines:
            return '\n'.join(instruction_lines)
        
        # If no instructions found, return empty string
        return ""
    
    async def debug_issue(self, 
                    issue_description: str, 
                    code_snippet: str,
                    file_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Debug an issue based on the description and code snippet.
        
        Args:
            issue_description: Description of the issue to debug
            code_snippet: The problematic code snippet
            file_path: Optional path to the file with the issue
            
        Returns:
            Dictionary containing the debugging results and fix
        """
        task_id = f"debug-{asyncio.get_event_loop().time()}"
        
        # Prepare context for debugging
        context = {
            "issue_description": issue_description,
            "code_snippet": code_snippet,
            "file_path": file_path
        }
        
        # Try to retrieve relevant memories related to similar issues
        if self.memory_enabled:
            context["relevant_memories"] = await self.retrieve_relevant_memories(
                query=f"{issue_description} {code_snippet[:100]}",
                max_memories=5
            )
        
        # Generate custom prompt for debugging
        prompt = f"""
You are the Coder of an AI development team. Your task is to debug an issue based on the following description and code snippet.

Issue Description:
{issue_description}

Code Snippet:
```
{code_snippet}
```

{f"File Path: {file_path}" if file_path else ""}

Please analyze the issue and provide:
1. Identification of the root cause
2. A detailed explanation of the problem
3. A fixed version of the code
4. Any additional recommendations to prevent similar issues

Format your response with clear sections for the analysis and the fixed code.
"""
        
        # Call LLM to generate the debugging response
        response_data = await self.call_llm(prompt)
        response_content = response_data["content"]
        
        # Extract code blocks for the fix
        code_blocks = self._extract_code_blocks(response_content)
        
        # Prepare debugging result
        debugging_result = {
            "task_id": task_id,
            "issue_description": issue_description,
            "original_code": code_snippet,
            "file_path": file_path,
            "analysis": self._extract_analysis(response_content),
            "fixes": [],
            "timestamp": asyncio.get_event_loop().time()
        }
        
        # Process code blocks
        for language, code, fix_file_path in code_blocks:
            # Use the provided file path if the extracted one is None
            actual_file_path = fix_file_path or file_path
            
            debugging_result["fixes"].append({
                "file_path": actual_file_path,
                "language": language,
                "code": code
            })
            
            # Store in code snippets
            snippet_id = f"snippet-{len(self.code_snippets) + 1}-{asyncio.get_event_loop().time()}"
            self.code_snippets[snippet_id] = {
                "snippet_id": snippet_id,
                "language": language,
                "code": code,
                "file_path": actual_file_path,
                "task_id": task_id,
                "created_at": asyncio.get_event_loop().time(),
                "is_fix": True
            }
            
            # Store in memory
            if self.memory_enabled:
                await self.memory.add_memory(
                    content=f"BUG FIX ({actual_file_path}):\n```{language}\n{code}\n```\nIssue: {issue_description}",
                    metadata={
                        "type": "bug_fix",
                        "language": language,
                        "file_path": actual_file_path,
                        "task_id": task_id,
                        "issue": issue_description[:100],  # First 100 chars as summary
                        "timestamp": asyncio.get_event_loop().time()
                    },
                    importance=4.5  # Very high importance for bug fixes
                )
        
        return debugging_result
    
    def _extract_analysis(self, text: str) -> str:
        """Extract root cause analysis from the debugging response"""
        # Look for common section headers for analysis
        patterns = [
            r"(?:^|\n)#+\s*(?:Root Cause|Analysis|Problem|Issue)(?:[\s\S]*?)(?=\n#+|\Z)",
            r"(?:^|\n)#+\s*(?:The Problem|The Issue)(?:[\s\S]*?)(?=\n#+|\Z)",
            r"(?:^|\n)#+\s*(?:What's Wrong|What's Happening)(?:[\s\S]*?)(?=\n#+|\Z)"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                # Strip out any code blocks that might be in the analysis
                analysis = re.sub(r"```[\s\S]*?```", "", match.group(0))
                return analysis.strip()
                
        # If no specific section found, return the text before the first code block
        parts = text.split("```", 1)
        if len(parts) > 1:
            return parts[0].strip()
        
        # Otherwise, return first 500 characters
        return text[:500].strip() 