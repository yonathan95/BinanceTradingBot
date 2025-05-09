# VS Code Git Branch Control System

This guide explains how to use the Hive Mind VS Code extension to control the Git branch context from your backend.

## Setup Steps

1. **Install the VS Code Extension:**
   ```powershell
   # Navigate to the extension directory
   cd vscode-hive-mind-extension
   
   # Run the installation script
   .\install.ps1
   ```

2. **Start the Backend Service:**
   ```powershell
   # Navigate to the hive-mind directory
   cd hive-mind
   
   # Start the backend service
   docker-compose up -d hive-mind-backend
   ```

3. **Reload VS Code:**
   - In VS Code, press `Ctrl+Shift+P` and run "Developer: Reload Window"
   - Make sure you have a Git repository open in VS Code

## Connecting to the Backend

The extension will attempt to auto-connect to the default backend URL (http://localhost:5000) when VS Code starts. You have two ways to manually control the connection:

1. **Standard Connection:**
   - Press `Ctrl+Shift+P` to open the Command Palette
   - Type "Hive Mind: Connect to Backend" and press Enter
   - This connects to the default backend URL or the last saved URL

2. **Custom Connection:**
   - Press `Ctrl+Shift+P` to open the Command Palette
   - Type "Hive Mind: Connect to Custom Backend URL" and press Enter
   - Enter the backend URL (e.g., http://192.168.1.100:5000)
   - This URL will be saved for future connections

3. **Disconnecting:**
   - Press `Ctrl+Shift+P` to open the Command Palette
   - Type "Hive Mind: Disconnect from Backend" and press Enter

4. **Checking Status:**
   - Click on the Hive Mind indicator in the status bar, or
   - Press `Ctrl+Shift+P` and type "Hive Mind: Show Connection Status"

## Testing the Connection

1. **Check if VS Code is connected:**
   ```powershell
   # Navigate to the hive-mind directory
   cd hive-mind
   
   # List connected VS Code clients
   .\change-vscode-branch.ps1 -List
   ```

   If you see "No VS Code clients connected", try the following:
   - Make sure VS Code is open with a Git repository
   - Use the Command Palette to connect manually (as described above)
   - Check the VS Code extension is installed (look for "Hive Mind" in the status bar)
   - Try connecting to a custom URL if your backend is running on a different machine

2. **Change Branch in VS Code:**
   - Once your client is connected, note the client ID from the list
   - Run the following command to change the branch:
   ```powershell
   .\change-vscode-branch.ps1 -Client "your-client-id" -Branch "main"
   ```

   Replace `your-client-id` with the actual client ID from the list, and `main` with the branch you want to switch to.

## Using in Your Backend Code

To control VS Code from your backend code, use the following:

```python
import requests

def change_vs_code_branch(client_id, branch, commit=None):
    """Change the branch in a connected VS Code client."""
    checkout_data = {
        "branch": branch,
        "clientId": client_id,
        "commit": commit,
        "message": f"Switching to {branch}"
    }
    
    response = requests.post(
        "http://localhost:5000/api/vscode/checkout", 
        json=checkout_data
    )
    
    return response.json()

# Example usage
client_id = "get-this-from-listing-clients"
change_vs_code_branch(client_id, "develop")
```

## Troubleshooting

1. **VS Code doesn't connect to backend:**
   - Make sure the backend is running: `docker ps | findstr hive-mind-backend`
   - Check backend logs: `docker logs hive-mind-hive-mind-backend-1`
   - Try connecting to a custom URL using the Command Palette
   - Check your network firewall if connecting to a remote machine

2. **Branch change doesn't work:**
   - Make sure the branch exists in your Git repository
   - Check if you have uncommitted changes that prevent branch switching
   - Look at the VS Code Git panel for any error messages

3. **Extension doesn't show in VS Code:**
   - Verify extension installation path: `%USERPROFILE%\.vscode\extensions\vscode-hive-mind-extension`
   - Check VS Code extensions panel to see if it's listed
   - Try reinstalling: `.\vscode-hive-mind-extension\install.ps1`

## Connection Across Machines

If your backend runs on a different machine than VS Code:

1. **On the backend machine:**
   - Make sure the backend listens on all interfaces (0.0.0.0) not just localhost
   - Ensure your firewall allows connections on port 5000
   - Find your machine's IP address using `ipconfig` (Windows) or `ifconfig` (Linux/macOS)

2. **In VS Code:**
   - Use the "Connect to Custom Backend URL" command
   - Enter the IP address of the backend machine (e.g., http://192.168.1.100:5000)

## Branch Control API

The backend API provides these endpoints:

- `GET /api/vscode/clients` - List all connected VS Code clients
- `GET /api/vscode/client/{client_id}` - Get information about a specific client
- `POST /api/vscode/checkout` - Change branch for a specific client
- `POST /api/vscode/register` - Register a new VS Code client (used by the extension) 