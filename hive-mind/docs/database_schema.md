# Hive Mind Database Schema and API Documentation

This document provides an overview of the Hive Mind database schema and API endpoints.

## Database Schema

The database schema is designed to support the Hive Mind multi-agent system with the following primary entities:

### Users

Users represent human users and AI agents in the system.

**Table: `users`**
- `id` (PK): Unique identifier (UUID)
- `username`: Unique username
- `email`: Unique email address
- `password_hash`: Hashed password (for human users)
- `first_name`: User's first name
- `last_name`: User's last name
- `user_type`: Type of user (human or agent)
- `avatar_url`: URL to user's avatar
- `created_at`: Timestamp when the user was created
- `updated_at`: Timestamp when the user was last updated
- `last_login`: Timestamp of the last login
- `is_active`: Whether the user is active

### Agents

Agents represent AI agents in the system with specific roles and capabilities.

**Table: `agents`**
- `id` (PK): Unique identifier (UUID)
- `name`: Agent name
- `role`: Agent role (manager, planner, architect, coder, etc.)
- `model`: LLM model used by the agent
- `tier`: Agent tier (economy, standard, premium)
- `temperature`: LLM temperature setting
- `token_limit`: Maximum token limit for LLM calls
- `use_prompt_engineering`: Whether the agent uses prompt engineering
- `custom_settings`: JSON with custom settings
- `created_at`: Timestamp when the agent was created
- `updated_at`: Timestamp when the agent was last updated

### Teams

Teams represent groups of agents and/or human users working together.

**Table: `teams`**
- `id` (PK): Unique identifier (UUID)
- `name`: Team name
- `description`: Team description
- `workspace_id` (FK): ID of the workspace the team belongs to
- `budget`: Team budget
- `created_by` (FK): ID of the user who created the team
- `created_at`: Timestamp when the team was created
- `updated_at`: Timestamp when the team was last updated

### Workspaces

Workspaces are containers for teams and projects.

**Table: `workspaces`**
- `id` (PK): Unique identifier (UUID)
- `name`: Workspace name
- `description`: Workspace description
- `created_by` (FK): ID of the user who created the workspace
- `created_at`: Timestamp when the workspace was created
- `updated_at`: Timestamp when the workspace was last updated

### Projects

Projects represent units of work within a workspace.

**Table: `projects`**
- `id` (PK): Unique identifier (UUID)
- `name`: Project name
- `description`: Project description
- `workspace_id` (FK): ID of the workspace the project belongs to
- `repository_url`: URL to the project repository
- `created_by` (FK): ID of the user who created the project
- `created_at`: Timestamp when the project was created
- `updated_at`: Timestamp when the project was last updated
- `status`: Project status (active, completed, archived, etc.)

### Tasks

Tasks represent units of work assigned to users or agents.

**Table: `tasks`**
- `id` (PK): Unique identifier (UUID)
- `title`: Task title
- `description`: Task description
- `assigned_to` (FK): ID of the user or agent the task is assigned to
- `created_by` (FK): ID of the user who created the task
- `project_id` (FK): ID of the project the task belongs to
- `team_id` (FK): ID of the team the task belongs to
- `status`: Task status (created, assigned, in_progress, etc.)
- `priority`: Task priority (low, medium, high, critical)
- `type`: Task type
- `requires_validation`: Whether the task requires validation
- `success_criteria`: JSON with success criteria
- `max_iterations`: Maximum number of iterations
- `iterations`: Current number of iterations
- `progress`: Task progress (0-100%)
- `due_date`: Task due date
- `time_estimate`: Estimated time to complete the task (in hours)
- `created_at`: Timestamp when the task was created
- `updated_at`: Timestamp when the task was last updated

### Task Comments

Comments on tasks from users or agents.

**Table: `task_comments`**
- `id` (PK): Unique identifier (UUID)
- `task_id` (FK): ID of the task the comment belongs to
- `author_id` (FK): ID of the user or agent who created the comment
- `content`: Comment content
- `created_at`: Timestamp when the comment was created
- `updated_at`: Timestamp when the comment was last updated

### Tags

Tags for categorizing tasks.

**Table: `tags`**
- `id` (PK): Unique identifier (UUID)
- `name`: Tag name
- `color`: Tag color
- `created_at`: Timestamp when the tag was created

### Budgets

Budgets for tracking spending by teams.

**Table: `budgets`**
- `id` (PK): Unique identifier (UUID)
- `team_id` (FK): ID of the team the budget belongs to
- `total_budget`: Total budget amount
- `remaining_budget`: Remaining budget amount
- `start_date`: Budget start date
- `end_date`: Budget end date
- `alert_threshold`: Threshold for alerts (0.0-1.0)
- `tier_constraints`: JSON with tier constraints
- `created_at`: Timestamp when the budget was created

### Spending Alerts

Alerts for budget spending.

**Table: `spending_alerts`**
- `id` (PK): Unique identifier (UUID)
- `team_id` (FK): ID of the team the alert belongs to
- `budget_id` (FK): ID of the budget the alert belongs to
- `alert_type`: Type of alert
- `message`: Alert message
- `current_spending`: Current spending
- `budget_limit`: Budget limit
- `percentage_used`: Percentage of budget used
- `topic_name`: Topic name (optional)
- `created_at`: Timestamp when the alert was created

### Topic Budgets

Budgets for specific topics within a team.

**Table: `topic_budgets`**
- `id` (PK): Unique identifier (UUID)
- `team_id` (FK): ID of the team the topic budget belongs to
- `topic_name`: Topic name
- `total_budget`: Total budget amount
- `remaining_budget`: Remaining budget amount
- `start_date`: Budget start date
- `end_date`: Budget end date
- `alert_threshold`: Threshold for alerts (0.0-1.0)
- `status`: Status (active, paused, completed)
- `created_at`: Timestamp when the topic budget was created

## Association Tables

### Team Agent Association

**Table: `team_agent_association`**
- `team_id` (PK, FK): ID of the team
- `agent_id` (PK, FK): ID of the agent

### Project User Association

**Table: `project_user_association`**
- `project_id` (PK, FK): ID of the project
- `user_id` (PK, FK): ID of the user
- `role`: Role of the user in the project (owner, editor, viewer, etc.)

### Task Tag Association

**Table: `task_tag_association`**
- `task_id` (PK, FK): ID of the task
- `tag_id` (PK, FK): ID of the tag

## API Endpoints

### Authentication

- **POST /api/auth/token**: Authenticate a user and get an access token
- **POST /api/auth/agent/token**: Authenticate an agent and get an access token
- **POST /api/auth/register**: Register a new user
- **GET /api/auth/me**: Get information about the current user

### Tasks

- **POST /api/tasks**: Create a new task
- **GET /api/tasks**: List tasks (with optional filtering)
- **GET /api/tasks/{task_id}**: Get task details by ID
- **PUT /api/tasks/{task_id}**: Update a task
- **PUT /api/tasks/{task_id}/status**: Update the status of a task
- **POST /api/tasks/{task_id}/comments**: Add a comment to a task
- **GET /api/tasks/{task_id}/comments**: Get comments for a task

### Teams

- **POST /api/teams**: Create a new team
- **GET /api/teams**: List teams (with optional filtering)
- **GET /api/teams/{team_id}**: Get team details by ID
- **PUT /api/teams/{team_id}**: Update a team
- **GET /api/teams/{team_id}/agents**: Get agents in a team
- **POST /api/teams/{team_id}/agents**: Add an agent to a team
- **DELETE /api/teams/{team_id}/agents/{agent_id}**: Remove an agent from a team
- **POST /api/teams/{team_id}/budget**: Create a budget for a team
- **GET /api/teams/{team_id}/budget**: Get a team's budget

### Agents

- **POST /api/agents**: Create a new agent
- **GET /api/agents**: List agents (with optional filtering)
- **GET /api/agents/{agent_id}**: Get agent details by ID
- **PUT /api/agents/{agent_id}**: Update an agent
- **GET /api/agents/{agent_id}/tasks**: Get tasks assigned to an agent
- **GET /api/agents/{agent_id}/teams**: Get teams that an agent belongs to

### WebSockets

- **WS /ws/events**: WebSocket endpoint for real-time events

## Entity Relationships

![Entity Relationship Diagram](./database_diagram.png)

## How to Use

### Setup the Database

Run the following script to set up the database:

```bash
cd hive-mind/control-plane
python setup_db.py
```

This will:
1. Create the database if it doesn't exist
2. Create the migrations
3. Apply the migrations to create all tables
4. Seed the database with initial data

### Start the API Server

Run the following command to start the API server:

```bash
cd hive-mind/control-plane
uvicorn app:app --reload --port 8000
```

### Access the API Documentation

Open your browser and navigate to:

```
http://localhost:8000/docs
```

This will open the Swagger UI where you can explore and test the API endpoints. 