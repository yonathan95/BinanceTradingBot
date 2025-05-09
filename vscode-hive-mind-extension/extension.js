const vscode = require('vscode');
const axios = require('axios');
const io = require('socket.io-client');
const path = require('path');
const fs = require('fs');

const autoConnect = true;

let socket = null;
let statusBarItem = null;
let backendUrl = 'http://localhost:5000';
let connectionStatus = 'Disconnected';
let clientId = null;
let fileChangeTimeout = null;
let pendingChanges = new Map();
let currentContext = {
  branch: null,
  commit: null
};

/**
 * Activate the extension
 * @param {vscode.ExtensionContext} context
 */
function activate(context) {
  console.log('Hive Mind extension is now active');

  // Create status bar item
  statusBarItem = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Left, 100);
  statusBarItem.text = '$(cloud) Hive Mind: Disconnected';
  statusBarItem.tooltip = 'Click to show Hive Mind status';
  statusBarItem.command = 'hivemind.showStatus';
  statusBarItem.show();
  
  // Register commands
  const connectCmd = vscode.commands.registerCommand('hivemind.connect', connectToBackend);
  const disconnectCmd = vscode.commands.registerCommand('hivemind.disconnect', disconnectFromBackend);
  const statusCmd = vscode.commands.registerCommand('hivemind.showStatus', showStatus);
  const connectCustomCmd = vscode.commands.registerCommand('hivemind.connectCustom', connectToCustomBackend);
  const grantPermissionCmd = vscode.commands.registerCommand('hivemind.grantPermission', grantPermission);
  const denyPermissionCmd = vscode.commands.registerCommand('hivemind.denyPermission', denyPermission);
  
  context.subscriptions.push(connectCmd);
  context.subscriptions.push(disconnectCmd);
  context.subscriptions.push(statusCmd);
  context.subscriptions.push(connectCustomCmd);
  context.subscriptions.push(grantPermissionCmd);
  context.subscriptions.push(denyPermissionCmd);
  context.subscriptions.push(statusBarItem);
  
  // Register file change listeners
  const fileWatcher = vscode.workspace.createFileSystemWatcher('**/*');
  fileWatcher.onDidChange(handleFileChange);
  fileWatcher.onDidCreate(handleFileChange);
  fileWatcher.onDidDelete(handleFileDelete);
  context.subscriptions.push(fileWatcher);
  
  // Auto-connect if enabled in settings or by default
  const config = vscode.workspace.getConfiguration('hivemind');
  if ((config && config.get('autoConnect')) || autoConnect) {
    // Connect with a slight delay to ensure VS Code is fully loaded
    setTimeout(connectToBackend, 3000);
  }
}

/**
 * Handle file changes by sending to backend
 * @param {vscode.Uri} uri 
 */
async function handleFileChange(uri) {
  // Skip if not connected
  if (!socket || !clientId) return;
  
  try {
    const filePath = uri.fsPath;
    const workspaceFolder = vscode.workspace.getWorkspaceFolder(uri);
    if (!workspaceFolder) return;
    
    const relativePath = path.relative(workspaceFolder.uri.fsPath, filePath);
    
    // Skip node_modules, .git, and other standard ignore patterns
    if (
      relativePath.includes('node_modules') || 
      relativePath.includes('.git') ||
      relativePath.startsWith('dist/') ||
      relativePath.startsWith('build/')
    ) {
      return;
    }
    
    // Read file content
    const content = await fs.promises.readFile(filePath, 'utf8').catch(err => null);
    if (content === null) return; // File might have been deleted or is binary
    
    // Add to pending changes
    pendingChanges.set(relativePath, {
      path: relativePath,
      content,
      timestamp: new Date().toISOString(),
      event: 'change'
    });
    
    // Debounce sending changes
    if (fileChangeTimeout) {
      clearTimeout(fileChangeTimeout);
    }
    
    fileChangeTimeout = setTimeout(() => {
      sendPendingChanges();
    }, 3000); // Wait 3 seconds to batch changes
    
  } catch (error) {
    console.error('Error handling file change:', error);
  }
}

/**
 * Handle file deletion
 * @param {vscode.Uri} uri 
 */
function handleFileDelete(uri) {
  // Skip if not connected
  if (!socket || !clientId) return;
  
  try {
    const filePath = uri.fsPath;
    const workspaceFolder = vscode.workspace.getWorkspaceFolder(uri);
    if (!workspaceFolder) return;
    
    const relativePath = path.relative(workspaceFolder.uri.fsPath, filePath);
    
    // Skip node_modules, .git, and other standard ignore patterns
    if (
      relativePath.includes('node_modules') || 
      relativePath.includes('.git') ||
      relativePath.startsWith('dist/') ||
      relativePath.startsWith('build/')
    ) {
      return;
    }
    
    // Add to pending changes
    pendingChanges.set(relativePath, {
      path: relativePath,
      content: null,
      timestamp: new Date().toISOString(),
      event: 'delete'
    });
    
    // Debounce sending changes
    if (fileChangeTimeout) {
      clearTimeout(fileChangeTimeout);
    }
    
    fileChangeTimeout = setTimeout(() => {
      sendPendingChanges();
    }, 3000); // Wait 3 seconds to batch changes
    
  } catch (error) {
    console.error('Error handling file deletion:', error);
  }
}

/**
 * Send pending changes to backend
 */
async function sendPendingChanges() {
  if (pendingChanges.size === 0 || !socket || !clientId) return;
  
  try {
    const changes = Array.from(pendingChanges.values());
    pendingChanges.clear();
    
    console.log(`Sending ${changes.length} file changes to backend`);
    
    socket.emit('file-changes', {
      clientId,
      changes,
      timestamp: new Date().toISOString()
    });
    
  } catch (error) {
    console.error('Error sending file changes:', error);
  }
}

/**
 * Grant permission to the backend
 */
async function grantPermission() {
  if (!clientId) {
    vscode.window.showErrorMessage('Not connected to Hive Mind backend');
    return;
  }
  
  try {
    const response = await axios.post(`${backendUrl}/api/vscode/permission`, {
      clientId,
      allowed: true,
      reason: 'User manually granted permission'
    });
    
    vscode.window.showInformationMessage('Permission granted to Hive Mind backend');
  } catch (error) {
    console.error('Error granting permission:', error);
    vscode.window.showErrorMessage(`Failed to grant permission: ${error.message}`);
  }
}

/**
 * Deny permission to the backend
 */
async function denyPermission() {
  if (!clientId) {
    vscode.window.showErrorMessage('Not connected to Hive Mind backend');
    return;
  }
  
  try {
    const response = await axios.post(`${backendUrl}/api/vscode/permission`, {
      clientId,
      allowed: false,
      reason: 'User manually denied permission'
    });
    
    vscode.window.showInformationMessage('Permission denied to Hive Mind backend');
  } catch (error) {
    console.error('Error denying permission:', error);
    vscode.window.showErrorMessage(`Failed to deny permission: ${error.message}`);
  }
}

/**
 * Connect to a custom backend URL specified by the user
 */
async function connectToCustomBackend() {
  try {
    // First disconnect if already connected
    if (socket) {
      await disconnectFromBackend();
    }
    
    // Prompt user for backend URL
    const inputUrl = await vscode.window.showInputBox({
      prompt: 'Enter the Hive Mind backend URL',
      placeHolder: 'http://localhost:5000',
      value: backendUrl
    });
    
    if (!inputUrl) {
      return; // User cancelled
    }
    
    // Update the backend URL
    backendUrl = inputUrl;
    
    // Save the URL to user settings
    const config = vscode.workspace.getConfiguration('hivemind');
    await config.update('backendUrl', backendUrl, vscode.ConfigurationTarget.Global);
    
    // Connect to the specified backend
    await connectToBackend();
    
  } catch (error) {
    console.error('Error connecting to custom backend:', error);
    vscode.window.showErrorMessage(`Failed to connect to custom backend: ${error.message}`);
  }
}

/**
 * Connect to the backend server
 */
async function connectToBackend() {
  try {
    console.log('Connecting to Hive Mind backend at ' + backendUrl);
    
    // Check if there's a Git repository in the workspace
    const gitExtension = vscode.extensions.getExtension('vscode.git')?.exports;
    const api = gitExtension?.getAPI(1);
    
    if (!api || api.repositories.length === 0) {
      vscode.window.showErrorMessage('No Git repository found in the current workspace.');
      return;
    }
    
    // Register with backend
    const workspaceFolders = vscode.workspace.workspaceFolders;
    const workspaceName = workspaceFolders && workspaceFolders.length > 0 
      ? workspaceFolders[0].name 
      : 'unknown';
    
    console.log('Registering with backend...');
    console.log('Workspace name: ' + workspaceName);
    console.log('Current branch: ' + (api.repositories[0].state.HEAD?.name || 'unknown'));
    
    try {
      const registration = await axios.post(`${backendUrl}/api/vscode/register`, {
        workspaceName,
        workspacePath: workspaceFolders[0].uri.fsPath,
        initialBranch: api.repositories[0].state.HEAD?.name || 'unknown'
      });
      
      clientId = registration.data.clientId;
      console.log('Registered with clientId: ' + clientId);
      
      // Connect to WebSocket
      console.log('Connecting to WebSocket...');
      socket = io(backendUrl, {
        query: {
          clientId
        }
      });
      
      // Listen for Git commands
      socket.on('connect', () => {
        console.log('WebSocket connected!');
        connectionStatus = 'Connected';
        statusBarItem.text = `$(cloud) Hive Mind: Connected`;
        vscode.window.showInformationMessage(`Connected to Hive Mind backend at ${backendUrl}`);
        
        // Prompt for permission at the start of the session
        promptForPermission();
      });
      
      socket.on('disconnect', () => {
        console.log('WebSocket disconnected!');
        connectionStatus = 'Disconnected';
        statusBarItem.text = `$(cloud) Hive Mind: Disconnected`;
      });
      
      socket.on('checkout', async (data) => {
        try {
          console.log('Received checkout command:', data);
          // Handle branch & commit checkout command
          await executeGitCommand(data.branch, data.commit);
          
          // Update current context
          currentContext.branch = data.branch;
          currentContext.commit = data.commit;
          
          // Send acknowledgment back to server
          socket.emit('checkout-result', {
            success: true,
            branch: data.branch,
            commit: data.commit
          });
        } catch (error) {
          console.error('Error during checkout:', error);
          socket.emit('checkout-result', {
            success: false,
            error: error.message
          });
        }
      });
      
      // Message from backend for the user
      socket.on('user-message', (data) => {
        try {
          console.log('Received user message:', data);
          vscode.window.showInformationMessage(data.message, ...(data.actions || []));
        } catch (error) {
          console.error('Error showing user message:', error);
        }
      });
      
      // Handle permission requests from the backend
      socket.on('request-permission', async (data) => {
        try {
          console.log('Received permission request:', data);
          
          // Extract request details
          const requestType = data.requestType;
          const details = data.details;
          
          let message = 'The Hive Mind backend is requesting permission to control this VS Code instance.';
          
          // Customize message based on request type
          if (requestType === 'branch-checkout') {
            message = `The Hive Mind backend wants to change your branch to "${details.branch}"`;
            if (details.commit) {
              message += ` at commit "${details.commit.substring(0, 7)}..."`;
            }
            if (details.message) {
              message += `\n\nReason: ${details.message}`;
            }
          }
          
          // Add warning about what this means
          message += '\n\nGranting permission allows the backend to control your Git branches.';
          
          // Show confirmation dialog
          const response = await vscode.window.showInformationMessage(
            message,
            { modal: true },
            'Allow',
            'Deny'
          );
          
          if (response === 'Allow') {
            // User granted permission
            socket.emit('permission-response', {
              granted: true,
              requestType: requestType,
              reason: 'User granted permission via VS Code UI'
            });
            
            vscode.window.showInformationMessage('Permission granted. The backend can now control this VS Code instance.');
            
            // If this was a checkout request, the backend will send a separate checkout command
          } else {
            // User denied or dismissed the dialog
            socket.emit('permission-response', {
              granted: false,
              requestType: requestType,
              reason: 'User denied permission via VS Code UI'
            });
            
            vscode.window.showInformationMessage('Permission denied. The backend cannot control this VS Code instance.');
          }
        } catch (error) {
          console.error('Error handling permission request:', error);
          socket.emit('permission-response', {
            granted: false,
            requestType: data.requestType,
            reason: `Error: ${error.message}`
          });
        }
      });
      
      socket.on('error', (error) => {
        console.error('Socket error:', error);
        vscode.window.showErrorMessage(`Hive Mind connection error: ${error}`);
      });
    } catch (error) {
      console.error('Registration error:', error);
      vscode.window.showErrorMessage(`Failed to register with Hive Mind backend: ${error.message}`);
    }
    
  } catch (error) {
    console.error('Connection error:', error);
    vscode.window.showErrorMessage(`Failed to connect to Hive Mind backend: ${error.message}`);
    connectionStatus = 'Error';
    statusBarItem.text = `$(cloud) Hive Mind: Error`;
  }
}

/**
 * Prompt the user for permission at the start of a session
 */
async function promptForPermission() {
  if (!clientId) return;
  
  try {
    // Get the client info from the backend
    const clientInfo = await axios.get(`${backendUrl}/api/vscode/client/${clientId}`);
    
    // Only show prompt if permission not yet granted
    if (!clientInfo.data.permission.allowed) {
      const message = 'Allow Hive Mind to control your VS Code instance? This includes changing Git branches and receiving your code changes for AI assistance.';
      
      const response = await vscode.window.showInformationMessage(
        message,
        { modal: true },
        'Allow',
        'Deny'
      );
      
      if (response === 'Allow') {
        await grantPermission();
      } else {
        await denyPermission();
      }
    }
  } catch (error) {
    console.error('Error prompting for permission:', error);
  }
}

/**
 * Execute a Git command to change branch and/or commit
 */
async function executeGitCommand(branch, commit) {
  const gitExtension = vscode.extensions.getExtension('vscode.git')?.exports;
  const api = gitExtension?.getAPI(1);
  
  if (!api || api.repositories.length === 0) {
    throw new Error('No Git repository found in the current workspace');
  }
  
  const repo = api.repositories[0];
  
  // Check if there are unsaved changes
  const hasChanges = await vscode.workspace.saveAll();
  
  if (repo.state.workingTreeChanges.length > 0) {
    const stashChoice = await vscode.window.showWarningMessage(
      'You have uncommitted changes. Stash them before checkout?',
      { modal: true },
      'Stash Changes',
      'Force Checkout (Discard Changes)',
      'Cancel'
    );
    
    if (stashChoice === 'Stash Changes') {
      await repo.clean();
    } else if (stashChoice === 'Force Checkout (Discard Changes)') {
      // Continue with checkout (will force)
    } else {
      throw new Error('Checkout canceled due to uncommitted changes');
    }
  }
  
  // First checkout the branch
  await repo.checkout(branch);
  
  // Then checkout specific commit if provided
  if (commit) {
    await repo.checkout(commit);
  }
  
  vscode.window.showInformationMessage(`Switched to: ${branch}${commit ? ` at commit ${commit.substring(0, 7)}...` : ''}`);
}

/**
 * Disconnect from the backend
 */
function disconnectFromBackend() {
  if (socket) {
    socket.disconnect();
    socket = null;
  }
  
  connectionStatus = 'Disconnected';
  statusBarItem.text = `$(cloud) Hive Mind: Disconnected`;
  vscode.window.showInformationMessage('Disconnected from Hive Mind backend');
  
  return Promise.resolve();
}

/**
 * Show the extension status
 */
function showStatus() {
  vscode.window.showInformationMessage(
    `Hive Mind Extension Status\n` +
    `Connection: ${connectionStatus}\n` +
    `Backend URL: ${backendUrl}\n` +
    `Client ID: ${clientId || 'Not registered'}`
  );
}

/**
 * Deactivate the extension
 */
function deactivate() {
  if (socket) {
    socket.disconnect();
    socket = null;
  }
}

module.exports = {
  activate,
  deactivate
} 