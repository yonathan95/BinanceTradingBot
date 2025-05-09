# Hive Mind Implementation Prompts

This document contains all the prompts needed to implement the Hive Mind project with feedback loops and local development capabilities. These prompts are organized by phase and component, following the project planning documentation.

## 1. Setup and Local Development Environment

### Local Development Docker Setup Prompt

```
Create a docker-compose.yml file to enable local development and testing of the Hive Mind project. The file should:

1. Set up containers for all core services (Control Plane, Agent Workers, Cost Domain Manager, Task Orchestrator)
2. Configure a local database (PostgreSQL)
3. Set up RabbitMQ for local message queuing
4. Add Qdrant for vector storage
5. Include minimal configuration for running the system offline
6. Expose appropriate ports for each service
7. Set up volume mounts for local development
8. Include environment variables for configuration
9. Enable hot-reloading for development

The goal is to allow developers to run the entire system locally without GCP dependencies for testing and development purposes.
```

### Local Development Environment Configuration Prompt

```
Create a .env.example file for local development of the Hive Mind project. The file should include:

1. API keys for OpenAI, Anthropic, and other LLM providers
2. Configuration for local database connection
3. Default agent tier settings (token limits, temperature, etc.)
4. Local storage paths
5. Development feature flags
6. Logging level configuration
7. Test environment settings
8. Mock service configurations

Include inline comments explaining each configuration option and its possible values.
```

## 2. Base Agent Framework Implementation

### BaseAgent Class Implementation Prompt

```
Implement the BaseAgent class that will serve as the foundation for all Hive Mind agents. The class should:

1. Support configurable LLM models (OpenAI, Anthropic, etc.)
2. Include context management
3. Implement token tracking and budget awareness
4. Support tool registration and execution
5. Include message handling for agent communication
6. Implement proper error handling and retry logic
7. Support streaming responses
8. Include methods for prompt generation and parsing
9. Support persona configuration
10. Include feedback loop capability that allows agents to:
    - Submit work for review
    - Receive feedback
    - Iterate on solutions until they meet defined success criteria
    - Track iteration count and status

Follow the Python class structure from the taskBreakdown.md file, but extend it to include the feedback loop capability.
```

### Agent Communication Protocol Implementation Prompt

```
Implement the agent communication protocol for Hive Mind, enabling structured message passing between agents. The implementation should:

1. Create a Message class with properties according to the agentRoles.md specification
2. Implement message routing based on context tags
3. Support priority levels for urgent messages
4. Add thread IDs for conversation tracking
5. Include sender and recipient information
6. Add support for requiring responses
7. Implement message serialization/deserialization for network transport
8. Add support for feedback loop messages with special handling
9. Include validation to ensure messages are well-formed

The protocol should be compatible with both local development and cloud deployment modes.
```

## 3. Feedback Loop Implementation

### Feedback Loop Framework Prompt

```
Implement a comprehensive feedback loop framework for the Hive Mind system. The framework should:

1. Allow tasks to be submitted for validation with success criteria
2. Provide a validation mechanism that checks outputs against criteria
3. Support multiple iteration cycles until success criteria are met
4. Track iteration count and prevent infinite loops
5. Provide detailed feedback for failed validations
6. Include task status tracking (not_started, in_progress, review, completed, failed)
7. Support configurable maximum iteration counts
8. Allow different validators to be plugged in for different types of tasks
9. Include proper error handling
10. Provide metrics on success rates and iteration counts
11. Support both automated and human-in-the-loop validation

The framework should be usable by any agent in the system, with the Tester agent as the primary user for code validation.
```

### Tester Agent With Feedback Loop Prompt

```
Implement a Tester agent for the Hive Mind system that uses the feedback loop framework. The agent should:

1. Extend the BaseAgent class with testing-specific functionality
2. Implement prompt engineering focused on identifying code issues
3. Create validation functions for different types of tests (unit, integration, etc.)
4. Parse LLM responses to extract structured test results
5. Provide detailed, constructive feedback for failed tests
6. Track test coverage and success metrics
7. Support test case generation
8. Implement iterative testing with the feedback loop
9. Prioritize testing based on code complexity and risk
10. Add support for regression testing
11. Include mocking capabilities for dependencies

The agent should use the feedback loop to work with the Coder agent, submitting feedback until code meets all test criteria or the maximum iteration count is reached.
```

## 4. Manager Agent Implementation

### Manager Agent Implementation Prompt

```
Implement the Manager Agent that will orchestrate the Hive Mind team's activities. The agent should:

1. Extend the BaseAgent class with management-specific functionality
2. Implement task creation and assignment logic
3. Add message routing between team members based on context tags
4. Include task monitoring and progress tracking
5. Add support for generating status updates for the user
6. Implement conversation summarization to minimize token usage
7. Add enforcement of project guard rails and security policies
8. Coordinate the feedback loop process between agents
9. Manage task dependencies and execution order
10. Handle error recovery when agents encounter issues
11. Implement the prompt template from agentRoles.md with appropriate customization

The Manager Agent should serve as the central coordinator for the team, ensuring effective communication and task completion with the feedback loop integrated into the workflow.
```

### Task Orchestrator Implementation Prompt

```
Implement the Task Orchestrator and Tier Router for the Hive Mind system. The component should:

1. Create a task queue with priority management
2. Implement tier selection based on task complexity and budget
3. Add dependency resolution to sequence task execution
4. Implement agent load balancing
5. Integrate with the feedback loop to track task status
6. Provide task assignment logic that matches tasks to appropriate agents
7. Add support for task splitting and merging
8. Implement retry logic for failed tasks
9. Add budget awareness to prevent cost overruns
10. Include task execution metrics collection
11. Provide an API for the Manager Agent to interact with

The Task Orchestrator should work closely with the Manager Agent to ensure tasks are assigned efficiently and completed through the feedback loop process.
```

## 5. Agent Implementation Prompts

### Planner Agent Implementation Prompt

```
Implement the Planner Agent for the Hive Mind system. The agent should:

1. Extend the BaseAgent class with planning-specific functionality
2. Parse high-level project requirements into tasks
3. Estimate task complexity and dependencies
4. Create project plans with structured task breakdowns
5. Identify risks and suggest mitigation strategies
6. Integrate with the feedback loop to refine plans based on feedback
7. Use the Claude Sonnet model as specified in agentRoles.md
8. Implement the prompt template from agentRoles.md with appropriate customization
9. Add support for updating plans as project requirements change
10. Include project scope management
11. Generate structured output for the Task Orchestrator to consume

The Planner Agent should work with the Manager Agent to break down user requests into actionable tasks for the team.
```

### Coder Agent Implementation Prompt

```
Implement the Coder Agent for the Hive Mind system. The agent should:

1. Extend the BaseAgent class with coding-specific functionality
2. Write clean, efficient, and maintainable code based on specifications
3. Integrate with the feedback loop to receive and address test feedback
4. Implement iterative code improvement based on feedback
5. Follow coding standards and patterns
6. Use the Claude Opus model as specified in agentRoles.md
7. Implement the prompt template from agentRoles.md with appropriate customization
8. Add support for different programming languages
9. Include error handling and debugging capabilities
10. Support refactoring existing code
11. Generate appropriate tests for the code

The Coder Agent should work closely with the Tester Agent through the feedback loop to iteratively improve code until it meets all requirements.
```

## 6. Testing and Evaluation Framework Prompts

### Unit Testing Framework Prompt

```
Implement a comprehensive unit testing framework for the Hive Mind system. The framework should:

1. Create test cases for all core components (BaseAgent, Message, FeedbackLoop, etc.)
2. Implement mock LLM responses for deterministic testing
3. Add test fixtures for common testing scenarios
4. Include property-based testing for critical components
5. Support both synchronous and asynchronous testing
6. Provide code coverage reporting
7. Implement test parameterization for edge cases
8. Add support for testing the feedback loop mechanism
9. Include integration with a CI pipeline
10. Generate test reports for quality tracking

The unit testing framework should ensure that all components work correctly individually and through the feedback loop mechanism.
```

### Integration Testing Framework Prompt

```
Implement an integration testing framework for the Hive Mind system. The framework should:

1. Create test scenarios that exercise multiple components together
2. Implement end-to-end workflow tests
3. Add performance testing for scaling validation
4. Include security testing
5. Support testing the feedback loop across multiple agents
6. Implement test orchestration for complex scenarios
7. Add support for testing network interfaces
8. Include test data generation
9. Provide metrics on system behavior
10. Support testing both locally and in a cloud environment

The integration testing framework should validate that the system works correctly as a whole, with particular focus on the feedback loop interactions between agents.
```

## 7. FastAPI Control Plane Implementation

### FastAPI Control Plane Implementation Prompt

```
Implement the FastAPI Control Plane for the Hive Mind system. The API should:

1. Create RESTful endpoints for team and agent management
2. Implement GraphQL for complex queries
3. Add WebSocket support for real-time logs
4. Implement authentication middleware
5. Add rate limiting and request validation
6. Create team provisioning logic
7. Implement task creation and management
8. Add integration with the Task Orchestrator
9. Implement feedback loop status tracking and reporting
10. Include budget management interfaces
11. Add comprehensive API documentation with examples

The Control Plane should provide both API and WebSocket interfaces for managing the Hive Mind system, including visibility into the feedback loop process.
```

### WebSocket Implementation for Real-time Feedback Prompt

```
Implement WebSocket support in the Control Plane to provide real-time feedback on agent activities. The implementation should:

1. Create WebSocket endpoints for subscribing to team events
2. Implement connection authentication and validation
3. Add message filtering based on user permissions
4. Create a pub/sub model for distributing events
5. Implement heartbeat mechanism for connection health
6. Add reconnection logic for clients
7. Create structured event formats for different event types
8. Include support for feedback loop status updates
9. Implement rate limiting to prevent flooding
10. Add logging and monitoring for WebSocket connections

The WebSocket implementation should allow clients to monitor the feedback loop process in real-time, seeing agent interactions and task progress.
```

## 8. Cost Domain Manager Implementation

### Cost Domain Manager Implementation Prompt

```
Implement the Cost Domain Manager for the Hive Mind system. The component should:

1. Create a Budget model according to taskBreakdown.md
2. Implement token tracking middleware
3. Create integration with LLM provider billing APIs
4. Add budget enforcement mechanisms
5. Implement alerts for budget thresholds
6. Create forecasting for spend projections
7. Add support for budget adjustments
8. Implement tiering recommendations based on budget constraints
9. Create comprehensive reporting
10. Add integration with the feedback loop to track iteration costs
11. Include cost optimization recommendations

The Cost Domain Manager should ensure that the system operates within budget constraints, even when the feedback loop requires multiple iterations.
```

## 9. UI Implementation Prompts

### React UI Dashboard Implementation Prompt

```
Implement the main dashboard for the Hive Mind UI. The dashboard should:

1. Display team configuration and status
2. Show task progress and status
3. Visualize agent interactions
4. Display budget information and alerts
5. Show feedback loop status for tasks
6. Implement real-time updates using WebSocket
7. Add filtering and sorting capabilities
8. Include a timeline view of activities
9. Provide drill-down capabilities for detailed information
10. Implement responsive design for different screen sizes
11. Add dark/light mode support

The dashboard should provide a clear visualization of the system's status, with particular focus on the feedback loop process for tasks.
```

### Team Creation Interface Implementation Prompt

```
Implement the team creation interface for the Hive Mind UI. The interface should:

1. Allow users to select agent roles from available options
2. Implement drag-and-drop for team composition
3. Add configuration options for each agent
4. Create budget allocation interface
5. Implement workspace configuration
6. Add validation for team composition
7. Include templates for common team configurations
8. Provide tooltips and help text for options
9. Implement preview functionality
10. Add save and load capabilities for team configurations
11. Include feedback loop configuration options

The team creation interface should allow users to create and configure teams with appropriate agent roles and feedback loop settings.
```

## 10. Local Execution and Testing

## Robust Workspace and Project Management System Prompt

Implement a robust workspace and project management system for Hive Mind. The system should:

1. Create a central dashboard for managing multiple projects within a workspace
2. Implement project templating for quick setup of common project types
3. Add file management with version history and diff viewing
4. Support code review workflows with feedback loops
5. Implement real-time collaboration features
6. Add project-specific agent configuration and team composition
7. Include project metrics and progress tracking
8. Support resource allocation across projects
9. Implement project-specific knowledge bases and context
10. Add integration with version control systems
11. Include permission management for team members
12. Support custom workflow definitions for different project types

The workspace should serve as the main entry point for users, allowing them to manage all aspects of their Hive Mind projects from a single interface.

## Agent Profile Page Implementation Prompt

Implement a comprehensive agent profile page for the Hive Mind system. The profile page should:

1. Display a customizable avatar/profile picture for the agent
2. Show the agent's role, capabilities, and specializations
3. Include a configurable personality section with traits and communication style
4. Implement an advanced communication analysis dashboard showing:
   - Communication patterns with other agents
   - Message frequency and volume over time
   - Response time analysis
   - Sentiment analysis of communications
   - Common topics and keywords in messages
   - Collaboration metrics with each team member
   - Communication efficiency scores
5. Add performance metrics for tasks completed
6. Show feedback loop statistics (iterations required, improvement rate)
7. Include a configuration panel for customizing the agent's parameters
8. Add a log of recent activities and contributions
9. Implement a skills/knowledge visualization
10. Show integration capabilities with other systems
11. Add resource usage statistics (tokens, computation time)

The profile page should provide deep insights into how each agent operates and interacts within the team ecosystem.



## Agent Profile Page Implementation Prompt

Implement a comprehensive communication analytics system for Hive Mind agents. The system should:

1. Create a messaging middleware that captures all inter-agent communications
2. Implement message metadata tagging for:
   - Message intent (question, response, suggestion, critique, etc.)
   - Topic classification
   - Urgency/priority
   - Referenced entities (code files, tasks, concepts)
   - Sentiment and tone
   - Complexity level (using readability metrics)
3. Add timestamps for delivery and response times
4. Track message size and token usage
5. Implement conversation threading with relationship mapping
6. Add outcome tracking for message chains (resolved/unresolved)
7. Create agent relationship graphs based on communication patterns
8. Implement feedback loop interaction tracking
9. Add natural language processing for content analysis
10. Track iteration counts for task resolution
11. Implement communication efficiency metrics
12. Add integration with the cost domain for communication cost analysis

The analytics system should collect and process data throughout the project lifecycle, providing the necessary inputs for the advanced communication analysis displayed on agent profiles.




### Local Testing Script Implementation Prompt

```
Implement a comprehensive local testing script for the Hive Mind system. The script should:

1. Start the local development environment using Docker Compose
2. Run a series of test scenarios
3. Exercise all core components
4. Test the feedback loop mechanism with various scenarios
5. Validate that agents can communicate effectively
6. Verify budget tracking functionality
7. Test error handling and recovery
8. Include performance benchmarking
9. Generate a test report
10. Clean up resources after testing

The script should provide a quick way to validate that the system is functioning correctly locally, with particular attention to the feedback loop mechanism.
```

### Demo Project Generator Prompt

```
Implement a demo project generator for the Hive Mind system. The generator should:

1. Create a simple project specification (e.g., a TODO app)
2. Generate the initial request to the system
3. Configure a team with appropriate roles
4. Set up success criteria for the feedback loop
5. Monitor the system as it processes the request
6. Record agent interactions and feedback cycles
7. Collect metrics on the process
8. Generate a report on the system's performance
9. Include visualizations of the feedback loop process
10. Provide examples of the feedback given between iterations

The demo project generator should showcase the system's capabilities, particularly the feedback loop mechanism that allows agents to iteratively improve their outputs.
```

## 11. Deployment and Documentation

### Deployment Script Implementation Prompt

```
Implement deployment scripts for the Hive Mind system. The scripts should:

1. Support local deployment with Docker Compose
2. Include GCP deployment with Terraform
3. Add Kubernetes deployment with Helm
4. Implement CI/CD pipeline configuration
5. Create environment-specific configurations
6. Support multi-environment deployment
7. Include rollback capabilities
8. Add monitoring setup
9. Implement secret management
10. Include documentation on deployment options

The deployment scripts should support both local and cloud deployment, with appropriate configuration for each environment.
```

### User Documentation Generation Prompt

```
Create comprehensive user documentation for the Hive Mind system. The documentation should:

1. Include a getting started guide
2. Provide detailed explanations of system components
3. Include tutorials for common tasks
4. Add reference documentation for APIs
5. Explain the feedback loop mechanism and its benefits
6. Include troubleshooting guides
7. Add best practices and examples
8. Provide guidance on budget management
9. Include security considerations
10. Add a glossary of terms
11. Provide downloadable resources

The documentation should make it easy for users to understand and use the system, with particular focus on explaining the feedback loop mechanism and its value.
``` 