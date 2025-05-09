# Work Mode - VS Code Integration

This document describes the Work Mode feature, which enables real-time collaboration between the Hive Mind system and VS Code users.

## Overview

Work Mode is a new feature that allows the Hive Mind agents to:
1. Track file changes made by users in VS Code
2. Process these changes and determine if they're related to ongoing tasks
3. Automatically create new tasks when appropriate
4. Send feedback and messages directly to VS Code users
5. Provide a dedicated UI in the Hive Mind dashboard for monitoring and communicating with VS Code clients

## Components

The system consists of several integrated components:

### VS Code Extension
- Requests permission from the user at the beginning of each session
- Tracks file changes and sends them to the backend
- Receives messages and instructions from the agent system
- Provides a UI for granting/denying permissions

### Backend VS Code Controller
- Manages VS Code client connections via Socket.IO
- Stores permission status for each client
- Forwards file changes to the agent system
- Sends messages from the agent system to VS Code clients

### VS Code Change Handler
- Processes file changes from VS Code clients
- Determines if changes are related to ongoing tasks
- Creates summaries of changes for agent processing
- Manages task-client relationships

### Manager Agent Integration
- Evaluates file changes to determine if a new task should be created
- Provides context about changes to other agents
- Manages communication between agents and VS Code clients

### Work Mode UI
- Displays connected VS Code clients
- Shows real-time file changes
- Allows sending messages to VS Code clients
- Provides an interface for monitoring agent-VS Code interactions

## Features

### Permission Management
VS Code users are prompted to grant permission at the beginning of each session. This permission allows the backend to:
- Receive file change events
- Send messages to the user
- Change Git branches and commits (with additional confirmation)

Permissions can be managed through:
- The initial dialog prompt
- VS Code commands (`hivemind.grantPermission`, `hivemind.denyPermission`)
- The backend API

### File Change Tracking
When a user makes changes to files in VS Code:
1. Changes are batched and sent to the backend
2. The VS Code change handler processes these changes
3. Changes are analyzed to determine if they're related to an existing task
4. If related to a task, they're forwarded to the appropriate agents
5. If not related, they may trigger the creation of a new task

### Real-time Communication
Work Mode enables real-time communication between agents and VS Code users:
- Agents can send messages directly to VS Code
- Users see these messages as notifications
- The Work Mode UI shows the communication history
- Users can send messages to the agent system via the UI

## Getting Started

### VS Code Extension Setup
1. Install the VS Code extension
2. Connect to the backend (will happen automatically by default)
3. Grant permission when prompted
4. Begin working normally - your changes will be tracked

### Using Work Mode UI
1. Navigate to the "Work Mode" tab in the dashboard
2. Select a connected VS Code client
3. View file changes and communication history
4. Send messages to the client

## How It Works

### Change Detection Flow
```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│ VS Code     │     │ Backend     │     │ VS Code     │     │ Manager     │
│ Extension   │────▶│ Controller  │────▶│ Change      │────▶│ Agent       │
│             │     │             │     │ Handler     │     │             │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
                                                                   │
                                                                   ▼
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│ VS Code     │     │ Backend     │     │ Agent       │     │ Other       │
│ User        │◀────│ Controller  │◀────│ Response    │◀────│ Agents      │
│             │     │             │     │             │     │             │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
```

### File Change Lifecycle
1. User edits a file in VS Code
2. Changes are detected and batched (to avoid sending too many events)
3. Changes are sent to the backend
4. Backend forwards changes to the VS Code change handler
5. Handler determines if changes relate to an existing task
6. Changes are processed by appropriate agents
7. Feedback is sent back to the VS Code client

## Configuration

### VS Code Extension Settings
- `hivemind.backendUrl`: URL of the Hive Mind backend (default: `http://localhost:5000`)
- `hivemind.autoConnect`: Automatically connect on startup (default: `true`)
- `hivemind.trackFileChanges`: Track file changes and send to backend (default: `true`)

### Backend Configuration
The backend maintains several data structures:
- `vscode_clients`: Map of connected VS Code clients
- `vscode_permissions`: Permission status for each client
- `vscode_file_changes`: History of file changes per client

## API Reference

### VS Code Controller Endpoints
- `POST /api/vscode/register`: Register a new VS Code client
- `GET /api/vscode/clients`: List all registered clients
- `GET /api/vscode/client/{client_id}`: Get details about a specific client
- `POST /api/vscode/permission`: Update permission for a client
- `POST /api/vscode/checkout`: Change Git branch/commit for a client
- `POST /api/vscode/send-message/{client_id}`: Send a message to a client
- `GET /api/vscode/file-changes/{client_id}`: Get file changes for a client

### Socket.IO Events
- `checkout`: Command to checkout a branch/commit
- `checkout-result`: Result of a checkout operation
- `request-permission`: Request permission from the client
- `permission-response`: Client's response to a permission request
- `file-changes`: File changes sent from VS Code
- `user-message`: Message sent to the VS Code client

## Contributing

To extend the Work Mode functionality:
1. Add new message types in the VS Code extension
2. Update the change handler to process these messages
3. Enhance the manager agent to make more intelligent decisions
4. Extend the UI to display more information

## Troubleshooting

Common issues:
- Permission denied: Use the VS Code command `hivemind.grantPermission`
- Connection issues: Check the backend URL in VS Code settings
- Changes not being processed: Ensure the manager agent is running
- UI not showing changes: Check network connections and refresh the page 