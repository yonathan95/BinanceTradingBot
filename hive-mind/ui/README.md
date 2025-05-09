# Hive Mind UI

The Hive Mind UI is built with React and Tauri, providing a modern, responsive interface for the Hive Mind AI Agent Teams platform.

## Features

- Dashboard for team and task management
- Team creation with agent role selection
- Workspace file browser and agent conversation interface
- Cost management and budget visualization
- Settings and user preferences

## Prerequisites

- Node.js 16+ and npm
- Rust (for Tauri desktop app builds)

## Getting Started

### Installation

1. Install dependencies:
   ```bash
   npm install
   ```

2. Set up environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your API endpoint and other settings
   ```

### Development

1. Start the development server:
   ```bash
   npm run dev
   ```
   This will start the React application at http://localhost:3000

2. To run the Tauri desktop app in development mode:
   ```bash
   npm run tauri dev
   ```

### Building for Production

1. Build the web version:
   ```bash
   npm run build
   ```

2. Build the desktop application:
   ```bash
   npm run tauri build
   ```
   This will create platform-specific installers in the `src-tauri/target/release/bundle` directory.

## Project Structure

```
ui/
├── public/              # Static assets
├── src/                 # Source code
│   ├── components/      # Reusable UI components
│   ├── contexts/        # React context providers
│   ├── hooks/           # Custom React hooks
│   ├── pages/           # Page components
│   ├── services/        # API service layer
│   ├── styles/          # CSS and style files
│   ├── types/           # TypeScript type definitions
│   ├── App.tsx          # Main App component
│   └── main.tsx         # Entry point
├── .env.example         # Example environment variables
├── index.html           # HTML template
├── package.json         # Node.js dependencies and scripts
├── tsconfig.json        # TypeScript configuration
└── vite.config.ts       # Vite configuration
```

## API Communication

The UI communicates with the Hive Mind API endpoints for all data operations:

- REST API for CRUD operations
- WebSockets for real-time updates
- Authentication using JWT tokens

## Contributing

1. Follow the code style and conventions in the existing files
2. Use TypeScript for all new components
3. Add appropriate tests for new features
4. Update this README as needed when adding significant features

## Technologies Used

- React for UI components
- TypeScript for type safety
- Vite for fast development and building
- React Router for navigation
- Socket.io for WebSocket communication
- Tauri for desktop application wrapping 