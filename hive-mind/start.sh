#!/bin/bash

# Hive Mind Startup Script
# This script starts all the necessary components of the Hive Mind system

# Exit on any error
set -e

# Set directories
SCRIPT_DIR=$(dirname "$(readlink -f "$0")")
CONTROL_PLANE_DIR="$SCRIPT_DIR/control-plane"
UI_DIR="$SCRIPT_DIR/ui"

# Terminal colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Helper function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Print banner
echo -e "${BLUE}"
echo "  _    _ _           __  __ _           _ "
echo " | |  | (_)         |  \/  (_)         | |"
echo " | |__| |___   _____| \  / |_ _ __   __| |"
echo " |  __  | \ \ / / _ \ |\/| | | '_ \ / _\` |"
echo " | |  | | |\ V /  __/ |  | | | | | | (_| |"
echo " |_|  |_|_| \_/ \___|_|  |_|_|_| |_|\__,_|"
echo -e "${NC}"
echo -e "${YELLOW}Multi-Agent Engineering Platform${NC}"
echo

# Check prerequisites
echo -e "${BLUE}Checking prerequisites...${NC}"

if ! command_exists python; then
    echo -e "${RED}Error: Python is not installed. Please install Python 3.9 or higher.${NC}"
    exit 1
fi

if ! command_exists npm; then
    echo -e "${RED}Error: npm is not installed. Please install Node.js and npm.${NC}"
    exit 1
fi

if ! command_exists docker; then
    echo -e "${YELLOW}Warning: Docker is not installed. Database services will not be available.${NC}"
fi

# Check Python version
PYTHON_VERSION=$(python --version 2>&1 | awk '{print $2}')
PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 9 ]); then
    echo -e "${RED}Error: Python 3.9 or higher is required. Current version: $PYTHON_VERSION${NC}"
    exit 1
fi

echo -e "${GREEN}Prerequisites check passed.${NC}"
echo

# Setup virtual environment
echo -e "${BLUE}Setting up Python virtual environment...${NC}"
if [ ! -d "$SCRIPT_DIR/venv" ]; then
    python -m venv "$SCRIPT_DIR/venv"
fi

# Activate virtual environment
if [ -f "$SCRIPT_DIR/venv/bin/activate" ]; then
    source "$SCRIPT_DIR/venv/bin/activate"
elif [ -f "$SCRIPT_DIR/venv/Scripts/activate" ]; then
    source "$SCRIPT_DIR/venv/Scripts/activate"
else
    echo -e "${RED}Error: Could not find activation script for virtual environment.${NC}"
    exit 1
fi

# Install Python dependencies
echo -e "${BLUE}Installing Python dependencies...${NC}"
if [ -f "$SCRIPT_DIR/requirements.txt" ]; then
    pip install -r "$SCRIPT_DIR/requirements.txt"
elif [ -f "$CONTROL_PLANE_DIR/requirements.txt" ]; then
    pip install -r "$CONTROL_PLANE_DIR/requirements.txt"
else
    echo -e "${RED}Error: Could not find requirements.txt${NC}"
    exit 1
fi

# Start PostgreSQL database if Docker is available
if command_exists docker; then
    echo -e "${BLUE}Starting PostgreSQL database...${NC}"
    
    # Check if container is already running
    if ! docker ps | grep -q "hivemind-postgres"; then
        docker run --name hivemind-postgres -e POSTGRES_USER=postgres -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=hivemind -p 5432:5432 -d postgres:14-alpine
        echo -e "${GREEN}PostgreSQL database started.${NC}"
    else
        echo -e "${GREEN}PostgreSQL database is already running.${NC}"
    fi
else
    echo -e "${YELLOW}Warning: Docker is not available. Please ensure PostgreSQL is running and accessible.${NC}"
fi

# Setup database
echo -e "${BLUE}Setting up database...${NC}"
cd "$CONTROL_PLANE_DIR"
python setup_db.py

# Install UI dependencies
echo -e "${BLUE}Installing UI dependencies...${NC}"
cd "$UI_DIR"
npm install

# Start API server in the background
echo -e "${BLUE}Starting API server...${NC}"
cd "$CONTROL_PLANE_DIR"
uvicorn app:app --reload --host 0.0.0.0 --port 8000 &
API_PID=$!

# Start UI in the background
echo -e "${BLUE}Starting UI...${NC}"
cd "$UI_DIR"
npm run dev &
UI_PID=$!

# Print startup information
echo
echo -e "${GREEN}Hive Mind system started successfully!${NC}"
echo -e "${YELLOW}API server running at:${NC} http://localhost:8000"
echo -e "${YELLOW}API documentation:${NC} http://localhost:8000/docs"
echo -e "${YELLOW}UI running at:${NC} http://localhost:3000"
echo
echo -e "${BLUE}Press Ctrl+C to stop all services${NC}"

# Setup trap to catch Ctrl+C and kill background processes
trap 'kill $API_PID $UI_PID; echo -e "\n${GREEN}Hive Mind services stopped.${NC}"; exit 0' INT

# Wait for children
wait 