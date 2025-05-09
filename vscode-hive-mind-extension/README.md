# Hive Mind VS Code Extension

This VS Code extension enables your backend system to control the Git branch and commit that the user sees in their VS Code workspace.

## Features

- Allows a backend service to remotely control which Git branch and commit is checked out in VS Code
- Real-time synchronization between backend commands and the VS Code workspace
- Status bar indicator showing connection status
- Commands to manually connect/disconnect from the backend

## Requirements

- VS Code 1.60.0 or higher
- Git extension for VS Code (built-in)
- A Git repository open in the workspace
- A running Hive Mind backend service

## Installation

1. Copy this extension to your `.vscode/extensions` directory or build and install from source
2. Reload VS Code
3. Configure the backend URL in settings

## Extension Settings

This extension contributes the following settings:

* `hivemind.backendUrl`: URL of the Hive Mind backend service (default: "http://localhost:5000")
* `hivemind.autoConnect`: Automatically connect to the backend on startup (default: false)

## Commands

* `Hive Mind: Connect to Backend`: Connect to the backend service
* `Hive Mind: Disconnect from Backend`: Disconnect from the backend service
* `Hive Mind: Show Connection Status`: Display current connection status

## Setting Up the Backend API

To use this extension, you need to implement the following API endpoints in your backend:

### 1. Registration Endpoint

```
POST /api/vscode/register
```

**Request Body:**
```json
{
  "workspaceName": "project-name",
  "workspacePath": "/path/to/workspace",
  "initialBranch": "main"
}
```

**Response:**
```json
{
  "clientId": "unique-client-id"
}
```

### 2. WebSocket Events

The backend should use Socket.IO to send events to the VS Code client:

**Checkout event:**
```javascript
socket.emit('checkout', {
  branch: "feature/new-feature",
  commit: "a1b2c3d4e5f6" // Optional, if null will checkout the latest commit
});
```

**Response from client:**
```javascript
socket.on('checkout-result', (result) => {
  // result = { success: true, branch: "feature/new-feature", commit: "a1b2c3d4e5f6" }
  // or 
  // result = { success: false, error: "Error message" }
});
```

## Security Considerations

- The extension should only be used in trusted environments
- Consider implementing authentication for the WebSocket connection
- Be aware that allowing remote control of Git operations could potentially lead to data loss if misused

## License

MIT 