import React, { useState, useEffect, useRef } from 'react';
import { Card, CardContent, CardHeader, Typography, List, ListItem, ListItemText, 
  Divider, Button, TextField, Box, Alert, CircularProgress, Chip, Stack } from '@mui/material';
import CodeIcon from '@mui/icons-material/Code';
import SendIcon from '@mui/icons-material/Send';
import DeveloperModeIcon from '@mui/icons-material/DeveloperMode';
import TerminalIcon from '@mui/icons-material/Terminal';

type FileChange = {
  path: string;
  event: string;
  timestamp: string;
  content?: string;
};

type VSCodeClient = {
  workspace_name: string;
  current_branch: string;
  current_commit: string;
  connected: boolean;
  permission: boolean;
  created_at: number;
  last_seen: number;
  changes_count: number;
};

type ClientUpdate = {
  clientId: string;
  client: VSCodeClient;
  message: string;
  timestamp: string;
  type: 'change' | 'status' | 'response';
};

const WorkMode: React.FC = () => {
  const [clients, setClients] = useState<Record<string, VSCodeClient>>({});
  const [selectedClient, setSelectedClient] = useState<string | null>(null);
  const [clientUpdates, setClientUpdates] = useState<ClientUpdate[]>([]);
  const [fileChanges, setFileChanges] = useState<FileChange[]>([]);
  const [message, setMessage] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Poll for clients and updates
  useEffect(() => {
    const fetchClients = async () => {
      try {
        const res = await fetch('/api/vscode/clients');
        const data = await res.json();
        setClients(data.clients);
        setLoading(false);
      } catch (err) {
        setError('Failed to fetch VS Code clients');
        setLoading(false);
      }
    };

    fetchClients();
    const interval = setInterval(fetchClients, 10000);

    return () => clearInterval(interval);
  }, []);

  // Get detailed information for a client
  const selectClient = async (clientId: string) => {
    setSelectedClient(clientId);
    setLoading(true);
    
    try {
      // Fetch client details
      const detailRes = await fetch(`/api/vscode/client/${clientId}`);
      const detailData = await detailRes.json();
      
      // Fetch client file changes
      const changesRes = await fetch(`/api/vscode/file-changes/${clientId}`);
      const changesData = await changesRes.json();
      
      setFileChanges(changesData.changes || []);
      
      // Add client selection to updates
      addClientUpdate({
        clientId,
        client: clients[clientId],
        message: `Selected VS Code client: ${clients[clientId].workspace_name}`,
        timestamp: new Date().toISOString(),
        type: 'status'
      });
      
      setLoading(false);
    } catch (err) {
      setError('Failed to fetch client details');
      setLoading(false);
    }
  };

  // Scroll to bottom of updates on new additions
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [clientUpdates]);

  // Add a new client update to the history
  const addClientUpdate = (update: ClientUpdate) => {
    setClientUpdates(prev => [...prev, update]);
  };

  // Send a message to the client
  const sendMessage = async () => {
    if (!selectedClient || !message.trim()) return;
    
    try {
      // Add message to updates first
      addClientUpdate({
        clientId: selectedClient,
        client: clients[selectedClient],
        message: `You: ${message}`,
        timestamp: new Date().toISOString(),
        type: 'change'
      });
      
      // Send to backend
      const res = await fetch(`/api/vscode/send-message/${selectedClient}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          message,
          actions: ['Acknowledge']
        })
      });
      
      if (res.ok) {
        // Clear message input
        setMessage('');
        
        // Simulate receiving a response from the agent system
        setTimeout(() => {
          addClientUpdate({
            clientId: selectedClient,
            client: clients[selectedClient],
            message: `Agent: I've processed your message and will analyze the changes.`,
            timestamp: new Date().toISOString(),
            type: 'response'
          });
        }, 1500);
      } else {
        throw new Error('Failed to send message');
      }
    } catch (err) {
      setError('Failed to send message to client');
    }
  };

  // Format timestamp for display
  const formatTime = (timestamp: string) => {
    return new Date(timestamp).toLocaleTimeString();
  };

  // Format file path to highlight filename
  const formatFilePath = (path: string) => {
    const parts = path.split('/');
    const fileName = parts.pop();
    
    return (
      <span>
        <span className="text-gray-500">{parts.join('/')}/</span>
        <span className="font-bold">{fileName}</span>
      </span>
    );
  };

  return (
    <Card sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <CardHeader 
        title={
          <Box display="flex" alignItems="center">
            <DeveloperModeIcon sx={{ mr: 1 }} />
            <Typography variant="h5">Work Mode</Typography>
          </Box>
        }
        subheader="Real-time collaboration with VS Code clients"
      />
      
      <Divider />
      
      <CardContent sx={{ flexGrow: 1, display: 'flex', flexDirection: 'column', p: 0 }}>
        {loading && (
          <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '200px' }}>
            <CircularProgress />
          </Box>
        )}
        
        {error && (
          <Alert severity="error" sx={{ m: 2 }}>{error}</Alert>
        )}
        
        {!loading && !error && (
          <Box sx={{ display: 'flex', height: '100%' }}>
            {/* Clients sidebar */}
            <Box sx={{ width: '250px', borderRight: '1px solid rgba(0, 0, 0, 0.12)', overflow: 'auto' }}>
              <Typography variant="subtitle1" sx={{ p: 2, fontWeight: 'bold' }}>
                Connected Clients
              </Typography>
              
              {Object.keys(clients).length === 0 ? (
                <Typography variant="body2" sx={{ p: 2, color: 'text.secondary' }}>
                  No VS Code clients connected
                </Typography>
              ) : (
                <List dense>
                  {Object.entries(clients).map(([id, client]) => (
                    <ListItem 
                      key={id}
                      button 
                      selected={id === selectedClient}
                      onClick={() => selectClient(id)}
                      sx={{ 
                        borderLeft: id === selectedClient ? '3px solid #1976d2' : 'none',
                        backgroundColor: id === selectedClient ? 'rgba(25, 118, 210, 0.08)' : 'transparent'
                      }}
                    >
                      <ListItemText
                        primary={
                          <Box display="flex" alignItems="center" justifyContent="space-between">
                            <Typography variant="body2" noWrap sx={{ maxWidth: '150px' }}>
                              {client.workspace_name}
                            </Typography>
                            <Chip 
                              size="small" 
                              label={client.connected ? 'Online' : 'Offline'} 
                              color={client.connected ? 'success' : 'default'}
                              sx={{ height: '18px', '& .MuiChip-label': { px: 0.5, fontSize: '0.6rem' } }}
                            />
                          </Box>
                        }
                        secondary={
                          <Typography variant="caption" component="div">
                            Branch: {client.current_branch}
                          </Typography>
                        }
                      />
                    </ListItem>
                  ))}
                </List>
              )}
            </Box>
            
            {/* Main content area */}
            <Box sx={{ flexGrow: 1, display: 'flex', flexDirection: 'column', height: '100%' }}>
              {!selectedClient ? (
                <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100%' }}>
                  <Typography variant="body1" color="text.secondary">
                    Select a VS Code client to view activity
                  </Typography>
                </Box>
              ) : (
                <>
                  {/* Updates and messages */}
                  <Box sx={{ flexGrow: 1, overflowY: 'auto', p: 2 }}>
                    {clientUpdates.filter(update => update.clientId === selectedClient).length === 0 ? (
                      <Typography variant="body2" sx={{ textAlign: 'center', color: 'text.secondary', my: 4 }}>
                        No activity yet with this client
                      </Typography>
                    ) : (
                      <>
                        {clientUpdates
                          .filter(update => update.clientId === selectedClient)
                          .map((update, index) => (
                            <Box 
                              key={index} 
                              sx={{ 
                                mb: 2, 
                                p: 1.5, 
                                borderRadius: 1,
                                backgroundColor: update.type === 'response' 
                                  ? 'rgba(25, 118, 210, 0.08)' 
                                  : (update.type === 'status' ? 'rgba(0, 0, 0, 0.03)' : 'transparent')
                              }}
                            >
                              <Box display="flex" alignItems="center" mb={0.5}>
                                {update.type === 'response' && <CodeIcon fontSize="small" sx={{ mr: 0.5, color: 'primary.main' }} />}
                                {update.type === 'status' && <TerminalIcon fontSize="small" sx={{ mr: 0.5, color: 'text.secondary' }} />}
                                <Typography variant="caption" color="text.secondary">
                                  {formatTime(update.timestamp)}
                                </Typography>
                              </Box>
                              <Typography variant="body2">
                                {update.message}
                              </Typography>
                            </Box>
                          ))}
                        
                        {fileChanges.length > 0 && (
                          <Box sx={{ mt: 2, p: 1.5, borderRadius: 1, backgroundColor: 'rgba(0, 0, 0, 0.03)' }}>
                            <Typography variant="subtitle2" sx={{ mb: 1 }}>
                              Recent File Changes
                            </Typography>
                            
                            <List dense sx={{ backgroundColor: 'background.paper', borderRadius: 1 }}>
                              {fileChanges.slice(-5).map((change, index) => (
                                <React.Fragment key={index}>
                                  <ListItem>
                                    <ListItemText
                                      primary={formatFilePath(change.path)}
                                      secondary={
                                        <Box display="flex" justifyContent="space-between">
                                          <Typography variant="caption" component="span">
                                            {change.event === 'change' ? 'Modified' : 'Deleted'}
                                          </Typography>
                                          <Typography variant="caption" component="span">
                                            {formatTime(change.timestamp)}
                                          </Typography>
                                        </Box>
                                      }
                                    />
                                  </ListItem>
                                  {index < fileChanges.slice(-5).length - 1 && <Divider component="li" />}
                                </React.Fragment>
                              ))}
                            </List>
                          </Box>
                        )}
                        
                        <div ref={messagesEndRef} />
                      </>
                    )}
                  </Box>
                  
                  {/* Message input */}
                  <Box sx={{ p: 2, borderTop: '1px solid rgba(0, 0, 0, 0.12)' }}>
                    <Box sx={{ display: 'flex' }}>
                      <TextField
                        fullWidth
                        size="small"
                        placeholder="Send a message to the team..."
                        value={message}
                        onChange={(e) => setMessage(e.target.value)}
                        onKeyDown={(e) => e.key === 'Enter' && sendMessage()}
                      />
                      <Button 
                        variant="contained" 
                        color="primary" 
                        sx={{ ml: 1 }}
                        endIcon={<SendIcon />}
                        onClick={sendMessage}
                        disabled={!message.trim()}
                      >
                        Send
                      </Button>
                    </Box>
                    <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
                      Messages will be processed by the manager agent
                    </Typography>
                  </Box>
                </>
              )}
            </Box>
          </Box>
        )}
      </CardContent>
    </Card>
  );
};

export default WorkMode; 