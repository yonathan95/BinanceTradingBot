"""
Tester Agent - Responsible for verifying code quality through comprehensive testing,
identifying bugs, and ensuring the software meets requirements.
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

class TesterAgent(BaseAgent):
    """
    Tester Agent that verifies code quality, creates and runs tests,
    reports bugs, and ensures software meets requirements.
    """
    
    def __init__(self, 
                agent_id: str = "tester", 
                model: str = "gpt-3.5-turbo", 
                temperature: float = 0.2,  # Lower temperature for more deterministic testing
                token_limit: int = 2048,
                memory_enabled: bool = True,
                embedding_model: str = "text-embedding-ada-002",
                vector_db_url: Optional[str] = None,
                workspace_path: Optional[str] = None):
        """Initialize the Tester Agent"""
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
        self.test_runs: Dict[str, Dict[str, Any]] = {}
        self.bugs_found: Dict[str, Dict[str, Any]] = {}
        
    async def process_message(self, message: Message) -> Message:
        """Process an incoming message and generate a response"""
        logger.info(f"Tester received message: {message.content[:50]}...")
        
        # First, retrieve relevant memories to provide context
        context = await self.build_context_with_memory(
            query=message.content,
            max_memories=7,
            recent_message_count=5
        )
        
        # Add message-specific context
        context["current_message"] = message
        context["sender"] = message.sender
        context["thread_id"] = message.thread_id
        context["context_tags"] = message.context_tags
        
        # Check if the message contains testing-related keywords
        test_related = self._is_test_related(message.content)
        if test_related:
            test_id = message.thread_id
            
            # If this is a new testing task, store it
            if test_id not in self.test_runs:
                self.test_runs[test_id] = {
                    "test_id": test_id,
                    "requirements": message.content,
                    "status": "in_progress",
                    "test_cases": [],
                    "results": None,
                    "created_at": asyncio.get_event_loop().time()
                }
                
                # Store task in memory with high importance
                if self.memory_enabled:
                    await self.memory.add_memory(
                        content=f"TESTING TASK: {message.content}",
                        metadata={
                            "type": "testing_task",
                            "test_id": test_id,
                            "thread_id": message.thread_id,
                            "timestamp": asyncio.get_event_loop().time()
                        },
                        importance=3.5  # High importance for testing tasks
                    )
        
        # Generate a prompt based on the context
        prompt = await self.generate_prompt(context)
        
        # Call LLM to generate a response
        response_data = await self.call_llm(prompt)
        response_content = response_data["content"]
        
        # Check if the response contains test code blocks
        test_blocks = self._extract_test_blocks(response_content)
        
        # If test blocks are found, store them in memory
        if test_blocks and self.memory_enabled:
            for block in test_blocks:
                language, code, file_path = block
                
                # Store test code in memory
                await self.memory.add_memory(
                    content=f"TEST CODE ({language}):\n```{language}\n{code}\n```\nFile path: {file_path or 'unspecified'}",
                    metadata={
                        "type": "test_code",
                        "language": language,
                        "file_path": file_path,
                        "test_id": message.thread_id,
                        "timestamp": asyncio.get_event_loop().time()
                    },
                    importance=3.8  # High importance for test code
                )
                
                # Update the test run with test case information
                if message.thread_id in self.test_runs:
                    test_cases = self.test_runs[message.thread_id].get("test_cases", [])
                    test_cases.append({
                        "language": language,
                        "code": code,
                        "file_path": file_path,
                        "created_at": asyncio.get_event_loop().time()
                    })
                    self.test_runs[message.thread_id]["test_cases"] = test_cases
        
        # Check if the response contains bug reports
        bugs = self._extract_bug_reports(response_content)
        
        # If bugs are found, store them in memory
        if bugs and self.memory_enabled:
            for bug in bugs:
                bug_id = f"bug-{len(self.bugs_found) + 1}-{asyncio.get_event_loop().time()}"
                
                # Store bug in memory
                await self.memory.add_memory(
                    content=f"BUG REPORT: {bug['description']}\nSeverity: {bug['severity']}\nReproduction Steps: {bug['reproduction_steps']}",
                    metadata={
                        "type": "bug_report",
                        "bug_id": bug_id,
                        "severity": bug['severity'],
                        "test_id": message.thread_id,
                        "file_path": bug.get('file_path'),
                        "timestamp": asyncio.get_event_loop().time()
                    },
                    importance=4.0  # High importance for bugs
                )
                
                # Store bug in agent's records
                self.bugs_found[bug_id] = {
                    "bug_id": bug_id,
                    "description": bug['description'],
                    "severity": bug['severity'],
                    "reproduction_steps": bug['reproduction_steps'],
                    "file_path": bug.get('file_path'),
                    "status": "open",
                    "test_id": message.thread_id,
                    "created_at": asyncio.get_event_loop().time()
                }
        
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
            test_code = []
            code_snippets = []
            requirements = []
            bug_reports = []
            other_memories = []
            
            for memory in context["relevant_memories"]:
                if memory.startswith("TEST CODE"):
                    test_code.append(memory)
                elif memory.startswith("CODE SNIPPET"):
                    code_snippets.append(memory)
                elif memory.startswith("TESTING TASK") or memory.startswith("CODING TASK"):
                    requirements.append(memory)
                elif memory.startswith("BUG REPORT"):
                    bug_reports.append(memory)
                else:
                    other_memories.append(memory)
            
            # Format memories by type
            if requirements:
                memories_context += "### Requirements and Tasks\n"
                for i, req in enumerate(requirements):
                    memories_context += f"{i+1}. {req}\n\n"
                    
            if code_snippets:
                memories_context += "### Code to Test\n"
                for i, snippet in enumerate(code_snippets):
                    memories_context += f"{snippet}\n\n"
                    
            if test_code:
                memories_context += "### Existing Test Code\n"
                for i, test in enumerate(test_code):
                    memories_context += f"{test}\n\n"
                    
            if bug_reports:
                memories_context += "### Known Bugs\n"
                for i, bug in enumerate(bug_reports):
                    memories_context += f"{i+1}. {bug}\n\n"
                    
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
You are the Tester of an AI development team. Your role is to ensure code quality through comprehensive testing and validation.

{memories_context}

{message_history}

### Current Request
{current_message.content if current_message else ""}

Your primary responsibilities are:
1. Create test plans and cases
2. Implement automated tests
3. Perform necessary manual testing
4. Report bugs with clear reproduction steps
5. Verify fixes and regression test
6. Monitor test coverage

When writing test code:
- Include appropriate assertions and error messages
- Cover happy paths, edge cases, and error conditions
- Follow testing best practices for the language/framework
- If implementing a test file, specify the complete file path

When reporting bugs:
- Provide a clear description of the issue
- Include detailed reproduction steps
- Assign a severity level (Critical, High, Medium, Low)
- Specify the affected component or file path

Respond with a focus on quality assurance, being thorough and precise in identifying potential issues and validating functionality.
"""
        return prompt
    
    def _is_test_related(self, text: str) -> bool:
        """Check if a message is related to testing tasks"""
        test_keywords = [
            "test", "verify", "validate", "check", "assert", "coverage",
            "bug", "defect", "issue", "failure", "error", "crash",
            "unit test", "integration test", "e2e test", "end-to-end",
            "qa", "quality assurance", "regression", "automated test",
            "test plan", "test case", "test suite", "test runner",
            "jest", "pytest", "junit", "mocha", "cypress", "selenium"
        ]
        
        text_lower = text.lower()
        
        # Check for testing keywords
        for keyword in test_keywords:
            if keyword in text_lower:
                return True
                
        # Check for common test file patterns
        test_file_patterns = ["test_", "_test", "spec.", ".spec", "Test.java", "Tests.cs"]
        for pattern in test_file_patterns:
            if pattern in text:
                return True
                
        return False
    
    def _extract_test_blocks(self, text: str) -> List[Tuple[str, str, Optional[str]]]:
        """
        Extract test code blocks from a markdown text.
        
        Returns:
            List of tuples: (language, code, file_path)
        """
        code_blocks = []
        
        # Regular expression to match markdown code blocks with optional language
        pattern = r"```(\w*)\n([\s\S]*?)```"
        matches = re.findall(pattern, text)
        
        for match in matches:
            language, code = match
            language = language.strip() or "text"  # Default to "text" if no language specified
            code = code.strip()
            
            # Try to extract file path from surrounding text
            file_path = None
            
            # Check for file path indicators
            lines = text.split("\n")
            for i, line in enumerate(lines):
                if f"```{language}" in line:
                    # Check a few lines before this code block
                    start_idx = max(0, i - 3)
                    for j in range(start_idx, i):
                        # Look for common test file patterns
                        path_match = re.search(r"[\"'`]?([\w\/\.-]+(?:test|spec|Test|Spec)[\w\/\.-]*\.\w+)[\"'`]?", lines[j])
                        if path_match:
                            file_path = path_match.group(1)
                            break
                            
                        # Look for any file path
                        general_path_match = re.search(r"[\"'`]?([\w\/\.-]+\.\w+)[\"'`]?", lines[j])
                        if general_path_match:
                            file_path = general_path_match.group(1)
                            break
                    
                    break
            
            # Check if this is actually test code
            is_test_code = self._is_test_code(code, language)
            if is_test_code:
                code_blocks.append((language, code, file_path))
            
        return code_blocks
    
    def _is_test_code(self, code: str, language: str) -> bool:
        """
        Determine if code is likely to be test code.
        
        Args:
            code: The code to check
            language: The programming language
            
        Returns:
            Boolean indicating if this is test code
        """
        # Look for test-related patterns based on language
        test_patterns = {
            "python": [
                r"(?:import|from)\s+(?:unittest|pytest|nose)",
                r"class\s+\w+(?:Test|TestCase)",
                r"def\s+test_\w+",
                r"@pytest\.(?:mark|fixture)",
                r"assert\s+"
            ],
            "javascript": [
                r"(?:describe|it|test)\s*\(",
                r"expect\s*\(",
                r"assert\.",
                r"(?:import|require)\s+(?:['\"]\w*test|jest|mocha)",
                r"\.toBe\(|\.toEqual\("
            ],
            "typescript": [
                r"(?:describe|it|test)\s*\(",
                r"expect\s*\(",
                r"assert\.",
                r"(?:import|require)\s+(?:['\"]\w*test|jest|mocha)",
                r"\.toBe\(|\.toEqual\("
            ],
            "java": [
                r"import\s+(?:org\.junit|org\.testng)",
                r"@Test",
                r"Assert\.",
                r"class\s+\w+Test",
                r"void\s+test\w+"
            ],
            "csharp": [
                r"using\s+(?:Microsoft\.VisualStudio\.TestTools|NUnit|Xunit)",
                r"\[Test(?:Method|Case|Fixture)?\]",
                r"Assert\.",
                r"class\s+\w+Tests"
            ]
        }
        
        # Get patterns for this language, or use a generic set
        patterns = test_patterns.get(language.lower(), [
            r"test", r"assert", r"expect", r"should", r"mock", r"stub", r"spy"
        ])
        
        # Check if any patterns match
        for pattern in patterns:
            if re.search(pattern, code, re.IGNORECASE):
                return True
                
        return False
    
    def _extract_bug_reports(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract bug reports from text.
        
        Returns:
            List of dictionaries with bug information
        """
        bugs = []
        
        # Look for bug report sections
        bug_section_patterns = [
            r"#+\s*Bug(?:\s+Report)?(?:[\s\S]*?)(?=\n#+|\Z)",
            r"#+\s*Issue(?:\s+Report)?(?:[\s\S]*?)(?=\n#+|\Z)",
            r"#+\s*Defect(?:\s+Report)?(?:[\s\S]*?)(?=\n#+|\Z)"
        ]
        
        for pattern in bug_section_patterns:
            sections = re.findall(pattern, text, re.IGNORECASE)
            for section in sections:
                bug = self._parse_bug_section(section)
                if bug:
                    bugs.append(bug)
        
        # If no structured bug sections found, look for bullet points with bug descriptions
        if not bugs:
            lines = text.split('\n')
            bug_points = []
            current_bug = []
            in_bug = False
            
            for line in lines:
                # New bug starts with a bullet or number
                if re.match(r'^\s*[\*\-\d]+\.?\s+(?:bug|issue|defect):', line, re.IGNORECASE):
                    if in_bug and current_bug:
                        bug_points.append('\n'.join(current_bug))
                        current_bug = []
                    in_bug = True
                    current_bug.append(line)
                # Continue collecting lines for the current bug
                elif in_bug and line.strip() and not line.startswith('#'):
                    current_bug.append(line)
                # End of a bug section (blank line or new heading)
                elif in_bug and (not line.strip() or line.startswith('#')):
                    if current_bug:
                        bug_points.append('\n'.join(current_bug))
                        current_bug = []
                    in_bug = False
            
            # Add the last bug if there is one
            if in_bug and current_bug:
                bug_points.append('\n'.join(current_bug))
            
            # Process each bug point
            for point in bug_points:
                bug = self._parse_bug_point(point)
                if bug:
                    bugs.append(bug)
        
        return bugs
    
    def _parse_bug_section(self, section: str) -> Optional[Dict[str, Any]]:
        """
        Parse a bug report section to extract structured information.
        
        Args:
            section: Text of the bug section
            
        Returns:
            Dictionary with bug information or None if parsing failed
        """
        # Initialize bug structure
        bug = {
            "description": "",
            "severity": "Medium",  # Default severity
            "reproduction_steps": "",
            "file_path": None
        }
        
        # Extract description (usually the first line after the heading)
        description_match = re.search(r"#+\s*(?:Bug|Issue|Defect)(?:\s+Report)?.*?\n+(.+)", section, re.IGNORECASE)
        if description_match:
            bug["description"] = description_match.group(1).strip()
        
        # Extract severity
        severity_match = re.search(r"(?:^|\n)(?:\*\*)?Severity(?:\*\*)?\s*:?\s*(\w+)", section, re.IGNORECASE)
        if severity_match:
            severity = severity_match.group(1).strip().capitalize()
            # Normalize severity to one of the standard levels
            if severity in ["Critical", "High", "Medium", "Low"]:
                bug["severity"] = severity
            elif "critical" in severity.lower() or "blocker" in severity.lower():
                bug["severity"] = "Critical"
            elif "high" in severity.lower() or "major" in severity.lower():
                bug["severity"] = "High"
            elif "medium" in severity.lower() or "normal" in severity.lower():
                bug["severity"] = "Medium"
            elif "low" in severity.lower() or "minor" in severity.lower():
                bug["severity"] = "Low"
        
        # Extract reproduction steps
        repro_match = re.search(r"(?:^|\n)(?:\*\*)?(?:Reproduction Steps|Steps to Reproduce|Repro Steps)(?:\*\*)?\s*:?\s*([\s\S]*?)(?=\n(?:\*\*)?[A-Za-z]+(?:\*\*)?\s*:|\Z)", section, re.IGNORECASE)
        if repro_match:
            bug["reproduction_steps"] = repro_match.group(1).strip()
        
        # Extract file path
        file_match = re.search(r"(?:^|\n)(?:\*\*)?(?:File|File Path|Location)(?:\*\*)?\s*:?\s*[\"'`]?([\w\/\.-]+\.\w+)[\"'`]?", section, re.IGNORECASE)
        if file_match:
            bug["file_path"] = file_match.group(1).strip()
        
        # Only return the bug if we have at least a description
        if bug["description"]:
            return bug
        return None
    
    def _parse_bug_point(self, point: str) -> Optional[Dict[str, Any]]:
        """
        Parse a bullet point containing a bug description.
        
        Args:
            point: Text of the bullet point
            
        Returns:
            Dictionary with bug information or None if parsing failed
        """
        # Initialize bug structure
        bug = {
            "description": "",
            "severity": "Medium",  # Default severity
            "reproduction_steps": "",
            "file_path": None
        }
        
        # Extract description (first line after the bullet)
        description_match = re.search(r'^\s*[\*\-\d]+\.?\s+(?:bug|issue|defect):?\s*(.+?)(?:\n|$)', point, re.IGNORECASE)
        if not description_match:
            description_match = re.search(r'^\s*[\*\-\d]+\.?\s+(.+?)(?:\n|$)', point)
        
        if description_match:
            bug["description"] = description_match.group(1).strip()
        
        # Check for severity indicators in the description
        severity_keywords = {
            "Critical": ["critical", "blocker", "crash", "security", "data loss", "urgent"],
            "High": ["high", "major", "significant", "important"],
            "Medium": ["medium", "moderate", "normal"],
            "Low": ["low", "minor", "cosmetic", "trivial"]
        }
        
        for severity, keywords in severity_keywords.items():
            if any(keyword in bug["description"].lower() for keyword in keywords):
                bug["severity"] = severity
                break
        
        # Extract explicit severity if mentioned
        severity_match = re.search(r'severity:?\s*(\w+)', point, re.IGNORECASE)
        if severity_match:
            severity = severity_match.group(1).strip().capitalize()
            if severity in ["Critical", "High", "Medium", "Low"]:
                bug["severity"] = severity
        
        # Extract reproduction steps (all lines after the first line)
        lines = point.split('\n')
        if len(lines) > 1:
            # Skip the first line (already used for description) and join the rest
            repro_steps = '\n'.join(lines[1:]).strip()
            bug["reproduction_steps"] = repro_steps
        
        # Extract file path
        file_match = re.search(r'[\"\'`]?([\w\/\.-]+\.\w+)[\"\'`]?', point)
        if file_match:
            bug["file_path"] = file_match.group(1).strip()
        
        # Only return the bug if we have at least a description
        if bug["description"]:
            return bug
        return None
    
    async def create_test_plan(self, 
                         feature_description: str, 
                         code_to_test: Dict[str, str],
                         test_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Create a comprehensive test plan for a feature.
        
        Args:
            feature_description: Description of the feature to test
            code_to_test: Dictionary mapping file paths to code content
            test_id: Optional test ID (generates a new one if not provided)
            
        Returns:
            Dictionary containing the test plan and test cases
        """
        # Generate test ID if not provided
        if test_id is None:
            test_id = f"test-plan-{asyncio.get_event_loop().time()}"
        
        # Prepare context for the test plan
        context = {
            "feature_description": feature_description,
            "code_to_test": code_to_test
        }
        
        # Try to retrieve relevant memories about similar features or tests
        if self.memory_enabled:
            context["relevant_memories"] = await self.retrieve_relevant_memories(
                query=feature_description,
                max_memories=7
            )
        
        # Generate custom prompt for test plan creation
        prompt = f"""
You are the Tester of an AI development team. Your task is to create a comprehensive test plan for the following feature:

Feature Description:
{feature_description}

Code to Test:
"""
        
        # Add code to the prompt
        for file_path, code in code_to_test.items():
            prompt += f"\n\nFile: {file_path}\n```\n{code}\n```"
            
        prompt += """

Please create a detailed test plan including:
1. Test objectives and scope
2. Test approach (unit, integration, end-to-end, etc.)
3. Test environment requirements
4. A comprehensive set of test cases covering:
   - Happy paths
   - Edge cases
   - Error conditions
   - Performance considerations (if applicable)
5. For each test case, provide:
   - ID and description
   - Preconditions
   - Test steps
   - Expected results
   - Pass/fail criteria
6. Actual test code implementations for key test cases

Format your response with clear headings and structured content.
"""
        
        # Call LLM to generate the test plan
        response_data = await self.call_llm(prompt)
        response_content = response_data["content"]
        
        # Extract test plan sections
        test_plan = {
            "test_id": test_id,
            "feature_description": feature_description,
            "objectives": self._extract_test_objectives(response_content),
            "approach": self._extract_test_approach(response_content),
            "environment": self._extract_test_environment(response_content),
            "test_cases": self._extract_test_cases(response_content),
            "implementation": [],
            "timestamp": asyncio.get_event_loop().time()
        }
        
        # Extract test code blocks
        test_blocks = self._extract_test_blocks(response_content)
        for language, code, file_path in test_blocks:
            test_plan["implementation"].append({
                "language": language,
                "code": code,
                "file_path": file_path
            })
            
            # Store in memory
            if self.memory_enabled:
                await self.memory.add_memory(
                    content=f"TEST IMPLEMENTATION ({file_path or 'unnamed'}):\n```{language}\n{code}\n```",
                    metadata={
                        "type": "test_implementation",
                        "language": language,
                        "file_path": file_path,
                        "test_id": test_id,
                        "timestamp": asyncio.get_event_loop().time()
                    },
                    importance=3.8  # High importance for test implementations
                )
        
        # Store the test plan in memory
        if self.memory_enabled:
            await self.memory.add_memory(
                content=f"TEST PLAN: {feature_description}\nObjectives: {test_plan['objectives']}\nApproach: {test_plan['approach']}\nTest Cases: {len(test_plan['test_cases'])} cases defined",
                metadata={
                    "type": "test_plan",
                    "test_id": test_id,
                    "timestamp": asyncio.get_event_loop().time()
                },
                importance=4.0  # High importance for test plans
            )
        
        # Store the test run
        self.test_runs[test_id] = {
            "test_id": test_id,
            "requirements": feature_description,
            "status": "planned",
            "test_cases": test_plan["test_cases"],
            "implementations": test_plan["implementation"],
            "created_at": asyncio.get_event_loop().time()
        }
        
        return test_plan
    
    def _extract_test_objectives(self, text: str) -> str:
        """Extract test objectives from the test plan"""
        patterns = [
            r"#+\s*(?:Test )?Objectives(?:[\s\S]*?)(?=\n#+|\Z)",
            r"#+\s*(?:Test )?Goals(?:[\s\S]*?)(?=\n#+|\Z)",
            r"#+\s*(?:Test )?Purpose(?:[\s\S]*?)(?=\n#+|\Z)"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                # Remove the heading itself
                content = re.sub(r"#+\s*(?:Test )?(?:Objectives|Goals|Purpose).*?\n", "", match.group(0), 1)
                return content.strip()
        
        return "General functional testing"  # Default if not found
    
    def _extract_test_approach(self, text: str) -> str:
        """Extract test approach from the test plan"""
        patterns = [
            r"#+\s*(?:Test )?Approach(?:[\s\S]*?)(?=\n#+|\Z)",
            r"#+\s*(?:Test )?Strategy(?:[\s\S]*?)(?=\n#+|\Z)",
            r"#+\s*(?:Test )?Methodology(?:[\s\S]*?)(?=\n#+|\Z)"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                # Remove the heading itself
                content = re.sub(r"#+\s*(?:Test )?(?:Approach|Strategy|Methodology).*?\n", "", match.group(0), 1)
                return content.strip()
        
        return "Unit testing and integration testing"  # Default if not found
    
    def _extract_test_environment(self, text: str) -> str:
        """Extract test environment requirements from the test plan"""
        patterns = [
            r"#+\s*(?:Test )?Environment(?:[\s\S]*?)(?=\n#+|\Z)",
            r"#+\s*(?:Test )?Requirements(?:[\s\S]*?)(?=\n#+|\Z)",
            r"#+\s*(?:Test )?Setup(?:[\s\S]*?)(?=\n#+|\Z)"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                # Remove the heading itself
                content = re.sub(r"#+\s*(?:Test )?(?:Environment|Requirements|Setup).*?\n", "", match.group(0), 1)
                return content.strip()
        
        return "Standard development environment"  # Default if not found
    
    def _extract_test_cases(self, text: str) -> List[Dict[str, Any]]:
        """Extract test cases from the test plan"""
        test_cases = []
        
        # Look for Test Cases section
        test_cases_section = ""
        section_patterns = [
            r"#+\s*Test Cases(?:[\s\S]*?)(?=\n#+|\Z)",
            r"#+\s*Test Scenarios(?:[\s\S]*?)(?=\n#+|\Z)",
            r"#+\s*Test Suite(?:[\s\S]*?)(?=\n#+|\Z)"
        ]
        
        for pattern in section_patterns:
            match = re.search(pattern, text)
            if match:
                test_cases_section = match.group(0)
                break
        
        if not test_cases_section:
            return test_cases
        
        # Look for individual test cases in the section
        # First check for well-structured test cases with their own headings
        individual_case_pattern = r"#+\s*(?:Test Case|TC)[^\n]*:?[^\n]*\n([\s\S]*?)(?=\n#+|\Z)"
        cases = re.findall(individual_case_pattern, test_cases_section)
        
        if cases:
            for case_content in cases:
                test_case = self._parse_test_case(case_content)
                if test_case:
                    test_cases.append(test_case)
        else:
            # Fall back to looking for numbered or bulleted lists
            lines = test_cases_section.split('\n')
            current_case = []
            in_case = False
            
            for line in lines:
                # Skip the heading line
                if "Test Cases" in line or "Test Scenarios" in line or "Test Suite" in line:
                    continue
                    
                # New test case starts with a bullet or number
                if re.match(r'^\s*[\*\-\d]+\.?\s+', line):
                    if in_case and current_case:
                        test_case = self._parse_test_case('\n'.join(current_case))
                        if test_case:
                            test_cases.append(test_case)
                        current_case = []
                    in_case = True
                    current_case.append(line)
                # Continue collecting lines for the current test case
                elif in_case and line.strip():
                    current_case.append(line)
                # End of a test case (blank line)
                elif in_case and not line.strip():
                    if current_case:
                        test_case = self._parse_test_case('\n'.join(current_case))
                        if test_case:
                            test_cases.append(test_case)
                        current_case = []
                    in_case = False
            
            # Add the last test case if there is one
            if in_case and current_case:
                test_case = self._parse_test_case('\n'.join(current_case))
                if test_case:
                    test_cases.append(test_case)
        
        return test_cases
    
    def _parse_test_case(self, text: str) -> Optional[Dict[str, Any]]:
        """Parse a test case section to extract structured information"""
        test_case = {
            "id": f"TC-{len(self.test_runs) + 1}-{len(self.test_runs.get('test_cases', [])) + 1}",
            "description": "",
            "preconditions": "",
            "steps": [],
            "expected_results": "",
            "pass_criteria": ""
        }
        
        # Extract description (first line)
        lines = text.split('\n')
        if lines:
            # Clean up the first line (remove bullets, numbers, etc.)
            first_line = re.sub(r'^\s*[\*\-\d]+\.?\s+', '', lines[0]).strip()
            test_case["description"] = first_line
            
            # Try to extract an ID if present
            id_match = re.search(r'(TC-\d+|Test Case \d+)', first_line)
            if id_match:
                test_case["id"] = id_match.group(1)
                # Remove the ID from the description
                test_case["description"] = re.sub(r'(TC-\d+|Test Case \d+)[:\s]*', '', first_line).strip()
        
        # Extract other components
        # Preconditions
        precond_match = re.search(r'(?:Preconditions?|Pre-conditions?|Setup)[:\s]+([\s\S]*?)(?=(?:Steps?|Test Steps?|Procedure|Expected|Pass\/Fail)[:\s]|$)', text, re.IGNORECASE)
        if precond_match:
            test_case["preconditions"] = precond_match.group(1).strip()
        
        # Test steps
        steps_match = re.search(r'(?:Steps?|Test Steps?|Procedure)[:\s]+([\s\S]*?)(?=(?:Expected|Result|Pass\/Fail)[:\s]|$)', text, re.IGNORECASE)
        if steps_match:
            steps_text = steps_match.group(1).strip()
            # Split into individual steps
            step_lines = steps_text.split('\n')
            steps = []
            for line in step_lines:
                # Clean up each step (remove bullets, numbers, etc.)
                cleaned = re.sub(r'^\s*[\*\-\d]+\.?\s+', '', line).strip()
                if cleaned:
                    steps.append(cleaned)
            test_case["steps"] = steps
        
        # Expected results
        results_match = re.search(r'(?:Expected Results?|Expected Output|Results?)[:\s]+([\s\S]*?)(?=(?:Pass\/Fail|Criteria)[:\s]|$)', text, re.IGNORECASE)
        if results_match:
            test_case["expected_results"] = results_match.group(1).strip()
        
        # Pass criteria
        criteria_match = re.search(r'(?:Pass\/Fail Criteria|Pass Criteria|Success Criteria)[:\s]+([\s\S]*?)(?=$)', text, re.IGNORECASE)
        if criteria_match:
            test_case["pass_criteria"] = criteria_match.group(1).strip()
        
        # Only return if we have at least a description and some steps
        if test_case["description"] and (test_case["steps"] or test_case["expected_results"]):
            return test_case
        return None
    
    async def report_bugs(self, 
                    test_results: Dict[str, Any], 
                    code_tested: Dict[str, str]) -> Dict[str, Any]:
        """
        Generate bug reports based on test results.
        
        Args:
            test_results: Dictionary containing test results
            code_tested: Dictionary mapping file paths to code content
            
        Returns:
            Dictionary containing bug reports
        """
        # Generate a unique ID for this bug report set
        report_id = f"bug-report-{asyncio.get_event_loop().time()}"
        
        # Prepare context for bug reporting
        context = {
            "test_results": test_results,
            "code_tested": code_tested
        }
        
        # Try to retrieve relevant memories about similar bugs
        if self.memory_enabled:
            context["relevant_memories"] = await self.retrieve_relevant_memories(
                query="bugs in " + " ".join(code_tested.keys()),
                max_memories=5
            )
        
        # Generate custom prompt for bug reporting
        prompt = f"""
You are the Tester of an AI development team. Your task is to analyze test results and generate detailed bug reports.

Test Results:
{json.dumps(test_results, indent=2)}

Code Tested:
"""
        
        # Add code to the prompt
        for file_path, code in code_tested.items():
            prompt += f"\n\nFile: {file_path}\n```\n{code}\n```"
            
        prompt += """

Please analyze the test results and generate detailed bug reports for any failures, including:
1. Bug description
2. Severity (Critical, High, Medium, Low)
3. Steps to reproduce
4. Expected vs. actual behavior
5. Affected component/file
6. Potential root cause
7. Suggested fix if applicable

Format each bug report with proper headings and structure.
"""
        
        # Call LLM to generate bug reports
        response_data = await self.call_llm(prompt)
        response_content = response_data["content"]
        
        # Extract bug reports
        bugs = self._extract_bug_reports(response_content)
        
        # Prepare bug report result
        bug_report = {
            "report_id": report_id,
            "test_id": test_results.get("test_id"),
            "bugs_found": bugs,
            "analysis": self._extract_analysis_from_bug_report(response_content),
            "timestamp": asyncio.get_event_loop().time()
        }
        
        # Store bug reports in memory
        if self.memory_enabled and bugs:
            for i, bug in enumerate(bugs):
                bug_id = f"bug-{report_id}-{i+1}"
                
                # Store bug in memory
                await self.memory.add_memory(
                    content=f"BUG REPORT: {bug['description']}\nSeverity: {bug['severity']}\nReproduction Steps: {bug['reproduction_steps']}",
                    metadata={
                        "type": "bug_report",
                        "bug_id": bug_id,
                        "severity": bug['severity'],
                        "report_id": report_id,
                        "test_id": test_results.get("test_id"),
                        "file_path": bug.get('file_path'),
                        "timestamp": asyncio.get_event_loop().time()
                    },
                    importance=4.0  # High importance for bugs
                )
                
                # Store bug in agent's records
                self.bugs_found[bug_id] = {
                    "bug_id": bug_id,
                    "description": bug['description'],
                    "severity": bug['severity'],
                    "reproduction_steps": bug['reproduction_steps'],
                    "file_path": bug.get('file_path'),
                    "status": "open",
                    "report_id": report_id,
                    "test_id": test_results.get("test_id"),
                    "created_at": asyncio.get_event_loop().time()
                }
        
        return bug_report
    
    def _extract_analysis_from_bug_report(self, text: str) -> str:
        """Extract overall analysis from bug report text"""
        patterns = [
            r"#+\s*(?:Analysis|Summary|Overview)(?:[\s\S]*?)(?=\n#+|\Z)",
            r"#+\s*(?:Test Results|Test Analysis)(?:[\s\S]*?)(?=\n#+|\Z)",
            r"#+\s*(?:Findings|Conclusion)(?:[\s\S]*?)(?=\n#+|\Z)"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                # Remove the heading itself
                content = re.sub(r"#+\s*(?:Analysis|Summary|Overview|Test Results|Test Analysis|Findings|Conclusion).*?\n", "", match.group(0), 1)
                return content.strip()
        
        # If no specific section found, return the text before the first heading or bug report
        parts = re.split(r"\n#+\s*(?:Bug|Issue|Defect)", text, 1)
        if len(parts) > 1:
            return parts[0].strip()
        
        # Otherwise, return first 500 characters
        return text[:500].strip() 