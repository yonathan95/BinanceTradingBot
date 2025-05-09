# VS Code Permissions System

This document describes the permissions system for controlling VS Code clients from the Hive Mind backend.

## Overview

The Hive Mind system can control VS Code clients by changing their Git branches and commits. To ensure this is done securely and with user consent, a permissions system has been implemented.

## How Permissions Work

1. When a VS Code client registers with the backend, it starts with permissions disabled by default
2. Before performing operations like changing branches, the backend checks if the client has granted permission
3. If permission has not been granted, the backend will request it from the client
4. The user can grant or deny permission via a dialog in VS Code
5. Permission status is stored on the backend and persists until explicitly changed

## Permission Workflows

### Automatic Permission Request

When the backend attempts to change a branch for a client without permission:

1. The backend sends a `request-permission` event to the client
2. VS Code shows a dialog asking the user to grant or deny permission
3. The user's choice is sent back to the backend via a `permission-response` event
4. If granted, the backend will automatically retry the operation

### Manual Permission Management

Permissions can be managed manually using the following methods:

1. **VS Code Extension Commands**:
   - `hivemind.grantPermission` - Grant permission to the backend
   - `hivemind.denyPermission` - Deny permission to the backend

2. **Backend API Endpoints**:
   - `POST /api/vscode/permission` - Set permission for a specific client

## API Reference

### Backend API Endpoints

#### List VS Code Clients

```
GET /api/vscode/clients
```

Returns a list of all registered VS Code clients, including their permission status.

#### Get Client Information

```
GET /api/vscode/client/{client_id}
```

Returns detailed information about a specific client, including permission status.

#### Set Permission

```
POST /api/vscode/permission
```

Body:
```json
{
  "clientId": "client-id-here",
  "allowed": true,
  "reason": "Optional reason for the permission change"
}
```

#### Change Branch

```
POST /api/vscode/checkout
```

Body:
```json
{
  "clientId": "client-id-here",
  "branch": "branch-name",
  "commit": "optional-commit-hash",
  "message": "Optional message explaining the change"
}
```

Response codes:
- 200: Command sent successfully
- 403: Permission denied
- 404: Client not found
- 400: Client not connected
- 500: Server error

### Socket.IO Events

#### request-permission (Server to Client)

Sent when the backend needs permission to perform an operation.

```javascript
{
  "requestType": "branch-checkout",
  "details": {
    "branch": "main",
    "commit": "commit-hash",
    "message": "Reason for the checkout"
  }
}
```

#### permission-response (Client to Server)

Sent by the client in response to a permission request.

```javascript
{
  "granted": true,
  "requestType": "branch-checkout",
  "reason": "User granted permission via VS Code UI"
}
```

## Testing with Mock Clients

For testing purposes, you can create mock clients using:

```
POST /api/vscode/mock
```

This creates a mock client with permission already granted.

## Debugging Permission Issues

If a branch change fails due to permission issues, check:

1. The client's current permission status using the `/api/vscode/client/{client_id}` endpoint
2. The VS Code extension logs for any permission request events
3. The backend logs for permission-related messages

You can use the `test-vscode-api.ps1` script to test and debug permission functionality:

```powershell
# Create a mock client
.\test-vscode-api.ps1 -CreateMockClient

# List all clients and their permission status
.\test-vscode-api.ps1 -ListClients

# Grant permission to a specific client
.\test-vscode-api.ps1 -ClientId "client-id-here" -GrantPermission

# Deny permission to a specific client
.\test-vscode-api.ps1 -ClientId "client-id-here" -DenyPermission
``` 