# Hive Mind Mock API

This directory contains mock data for testing the Hive Mind UI without requiring a backend server.

## Structure

```
mock-api/
  ├── api/
  │   ├── teams.json - List of all teams
  │   ├── cost-domain/
  │   │   └── usage.json - Cost usage data for all teams
  │   ├── tasks/
  │   │   └── recent.json - List of recent tasks
  │   └── teams/
  │       ├── team-1/ - Web App Development team
  │       │   ├── messages.json - Team conversation history
  │       │   ├── files.json - Team file structure
  │       │   └── files/ - Actual file contents
  │       ├── team-2/ - API Backend Team
  │       │   ├── messages.json - Team conversation history
  │       │   ├── files.json - Team file structure
  │       │   └── files/ - Actual file contents
  │       └── team-3/ - ML Model Training
  │           ├── messages.json - Team conversation history
  │           ├── files.json - Team file structure
  │           └── files/ - Actual file contents
```

## How It Works

The application is configured to automatically use mock data in development mode. This is handled by the `mockService.ts` file, which intercepts API requests and redirects them to these static JSON files.

For real-time message simulation, the application uses `mockWebSocket.ts` which simulates WebSocket communication and periodically sends mock agent messages.

## Adding New Mock Data

1. Create a new JSON file in the appropriate directory
2. The file name should match the API endpoint path (e.g., for `/api/teams/team-4`, create `teams/team-4.json`)
3. Follow the existing data structure format for consistency

## File Structure

Each team has a `files.json` that defines the directory structure, and a `files/` directory that contains the actual file contents. File contents are stored in a structure where:

- Each file has its own directory named after the file (e.g., `Button.tsx/`)
- Inside that directory is a `content.json` file with the following structure:
  ```json
  {
    "path": "/path/to/file.tsx",
    "content": "// The actual file content as a string"
  }
  ```

## Testing with Mock Data

1. Run the application in development mode: `npm run dev`
2. The mock service will automatically intercept API requests
3. If you want to force using mock data in any environment, add `?mock=true` to the URL

## WebSocket Simulation

The mock WebSocket service automatically sends periodic messages to simulate agent communication. These messages are defined in the `mockWebSocket.ts` file and are sent at random intervals between 10 and 20 seconds. 