# Hive Mind UI

The user interface for the Hive Mind project, built with React, TypeScript, and Tauri.

## Setup Instructions

### Prerequisites
- Node.js (v16 or later)
- npm or yarn
- Rust (for Tauri)

### Installation

1. Clone the repository
```bash
git clone https://github.com/yourusername/hive-mind.git
cd hive-mind
```

2. Install dependencies
```bash
npm install
# or
yarn
```

3. Create a `.env` file
Create a `.env` file in the root directory with the following contents:

```
# API Configuration
VITE_API_BASE_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000/ws

# Authentication
VITE_AUTH_ENABLED=true
VITE_AUTH_TOKEN_KEY=hive_mind_auth_token

# Feature Flags
VITE_ENABLE_COST_MANAGEMENT=true
VITE_ENABLE_REAL_TIME_UPDATES=true

# UI Configuration
VITE_APP_NAME=Hive Mind
VITE_DEFAULT_THEME=light

# Logging
VITE_LOG_LEVEL=info
```

## Running the Application

### Development Mode

To run the application in development mode:

```bash
npm run dev
# or
yarn dev
```

This will start the development server at http://localhost:3000.

### Building for Production

To build the application for production:

```bash
npm run build
# or
yarn build
```

### Running with Tauri

To run the application as a Tauri desktop application:

```bash
npm run tauri dev
# or
yarn tauri dev
```

To build the Tauri desktop application:

```bash
npm run tauri build
# or
yarn tauri build
```

## UI Components

The UI includes the following main components:

- **Login**: Authentication screen
- **Dashboard**: Main overview of teams and activities
- **Team Creation**: Interface for creating new teams
- **Workspace**: File browser and editor for managing workspaces
- **Cost Management**: Budget and cost visualization tools
- **Settings**: Application and user settings
- **Screenshot Tool**: Mechanism for capturing UI for LLM agent awareness

## Architecture

The UI follows a modular architecture with:

- **Pages**: Main route components
- **Components**: Reusable UI elements
- **Services**: API, WebSocket, and Authentication services
- **Hooks**: Custom React hooks for state and behavior
- **Styles**: CSS and styling utilities

## Feature Status

All components of Phase 2: UI and User Experience have been fully implemented:

- ✅ UI Foundation
- ✅ Workspace UI
- ✅ Cost Management UI
- ✅ Advanced UI Features
- ✅ Screenshot Mechanism for LLM Agent Awareness

## Troubleshooting

If you encounter any issues:

1. Make sure you have created the `.env` file with the correct configuration
2. Verify that the backend API is running at the URL specified in your `.env` file
3. Check the browser console for any error messages
4. Ensure all dependencies are installed correctly 