#!/bin/bash

# Bash script to install the Hive Mind VS Code extension

echo -e "\e[36mInstalling Hive Mind extension to VS Code...\e[0m"

# Determine VS Code extensions directory
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    EXTENSIONS_DIR="$HOME/.vscode/extensions"
else
    # Linux
    EXTENSIONS_DIR="$HOME/.vscode/extensions"
fi

EXTENSION_NAME="vscode-hive-mind-extension"
EXTENSION_DIR="$EXTENSIONS_DIR/$EXTENSION_NAME"

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
SOURCE_DIR="$SCRIPT_DIR"

# Check if VS Code extensions directory exists
if [ ! -d "$EXTENSIONS_DIR" ]; then
    echo -e "\e[33mCreating VS Code extensions directory...\e[0m"
    mkdir -p "$EXTENSIONS_DIR"
fi

# Remove existing extension if it exists
if [ -d "$EXTENSION_DIR" ]; then
    echo -e "\e[33mRemoving existing Hive Mind extension...\e[0m"
    rm -rf "$EXTENSION_DIR"
fi

# Create extension directory
echo -e "\e[33mCreating extension directory...\e[0m"
mkdir -p "$EXTENSION_DIR"

# Copy extension files
echo -e "\e[33mCopying extension files...\e[0m"
cp -R "$SOURCE_DIR"/* "$EXTENSION_DIR"
# Remove install scripts and node_modules from destination
rm -f "$EXTENSION_DIR/install.ps1" "$EXTENSION_DIR/install.sh"
rm -rf "$EXTENSION_DIR/node_modules"

# Install dependencies
echo -e "\e[33mInstalling dependencies...\e[0m"
cd "$EXTENSION_DIR"
npm install

echo -e "\n\e[32mHive Mind extension has been installed successfully!\e[0m"
echo -e "\e[32mPlease reload VS Code to activate the extension.\e[0m"
echo -e "\e[36mYou can do this by pressing Cmd+Shift+P (macOS) or Ctrl+Shift+P (Linux) and running 'Developer: Reload Window'\e[0m"

# Return to the original directory
cd "$SCRIPT_DIR" 