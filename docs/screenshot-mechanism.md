# UI Screenshot Mechanism for LLM Agent Awareness

## Overview

This feature allows LLM agents to "see" the UI they've created through screenshot capture capabilities. It enables agents to capture the current state of the user interface and share it with other agents, promoting a more comprehensive understanding of the UI's visual representation.

## Implementation Details

The screenshot mechanism consists of the following components:

### 1. Screenshot Service (`src/services/screenshot.ts`)

A service that handles the core screenshot functionality:
- Captures full-screen screenshots of the current UI
- Captures specific DOM elements using selectors
- Manages screenshot storage and metadata
- Provides access to the latest screenshots for agents

### 2. React Hook (`src/hooks/useScreenshot.ts`)

A custom React hook that wraps the screenshot service functionality:
- Manages state related to capturing screenshots
- Handles capturing, errors, and loading states
- Provides a clean interface for React components

### 3. UI Component (`src/components/ScreenshotTool.tsx`)

A reusable React component that provides UI controls for:
- Capturing full-screen screenshots
- Capturing specific elements using CSS selectors
- Displaying the latest screenshot path

### 4. Integration with Agent Communication

- Screenshots are shared through the WebSocket communication system
- System messages inform users when screenshots are captured
- A dedicated API endpoint for recording and retrieving screenshots

## How It Works

1. **Capture**: When a user triggers a screenshot through the UI, the `html2canvas` library captures the current UI state.
2. **Storage**: The screenshot is saved to the filesystem with metadata about when and where it was captured.
3. **Sharing**: The screenshot path is shared with agents, notifying them that a new visual representation is available.
4. **Access**: Agents can access the screenshot to gain visual understanding of the UI state.

## Usage for Agents

Agents can use the screenshot mechanism to:
- Verify that UI changes have been applied correctly
- Understand the current visual layout of components
- Identify potential UI issues or improvements
- Reference specific UI elements in their communications

## Technical Requirements

- **Client-side**: 
  - html2canvas library for DOM capturing
  - React for UI components
  - Tauri's filesystem API for storage

- **Server-side**:
  - API endpoints for screenshot metadata
  - WebSocket for real-time notifications

## Future Improvements

- Add automated screenshot capture on significant UI changes
- Implement visual diffing to highlight UI changes between screenshots
- Create AI-specific image analysis to enhance agent understanding of UI elements
- Add annotation capabilities for agents to highlight specific elements 