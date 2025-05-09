import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import axios from 'axios';
import { websocketService, screenshotService } from '../services';
import { ScreenshotTool } from '../components/ScreenshotTool';

interface Team {
  id: string;
  name: string;
  description: string;
  roles: string[];
  model_tier: string;
  budget_limit: number;
}

interface File {
  id: string;
  name: string;
  type: 'file' | 'directory';
  path: string;
  children?: File[];
}

interface Message {
  id: string;
  agent: string;
  content: string;
  timestamp: string;
  type: 'text' | 'code' | 'system';
}

const Workspace: React.FC = () => {
  const { teamId } = useParams<{ teamId: string }>();
  const [team, setTeam] = useState<Team | null>(null);
  const [files, setFiles] = useState<File[]>([]);
  const [activeFile, setActiveFile] = useState<string | null>(null);
  const [fileContent, setFileContent] = useState<string>('');
  const [messages, setMessages] = useState<Message[]>([]);
  const [taskInput, setTaskInput] = useState('');
  const [isTaskSubmitting, setIsTaskSubmitting] = useState(false);
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [latestScreenshotPath, setLatestScreenshotPath] = useState<string | null>(null);

  useEffect(() => {
    const fetchTeamData = async () => {
      try {
        const [teamResponse, filesResponse] = await Promise.all([
          axios.get(`/api/teams/${teamId}`),
          axios.get(`/api/teams/${teamId}/files`)
        ]);
        
        setTeam(teamResponse.data);
        setFiles(filesResponse.data);
        
        // Also fetch recent messages
        const messagesResponse = await axios.get(`/api/teams/${teamId}/messages`);
        setMessages(messagesResponse.data);
      } catch (err) {
        setError('Failed to load workspace data');
        console.error(err);
      } finally {
        setIsLoading(false);
      }
    };

    if (!teamId) return;

    fetchTeamData();

    // Set up real-time message updates using WebSocket
    websocketService.connect();
    
    websocketService.onConnect(() => {
      console.log('WebSocket connected');
      if (teamId) {
        websocketService.joinTeam(teamId);
      }
    });

    websocketService.onMessage('message', (message: Message) => {
      setMessages(prev => [...prev, message]);
    });

    websocketService.onMessage('file_updated', (data: { path: string, content: string }) => {
      if (data.path === activeFile) {
        setFileContent(data.content);
      }
    });

    return () => {
      websocketService.disconnect();
    };
  }, [teamId, activeFile]);

  const handleFileSelect = async (filePath: string) => {
    try {
      const response = await axios.get(`/api/teams/${teamId}/files/${encodeURIComponent(filePath)}/content`);
      setActiveFile(filePath);
      setFileContent(response.data.content);
    } catch (err) {
      console.error('Failed to load file content', err);
    }
  };

  const handleTaskSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (taskInput.trim() === '') return;
    
    setIsTaskSubmitting(true);
    
    try {
      await axios.post(`/api/teams/${teamId}/tasks`, {
        goal: taskInput,
        complexity: 'M', // Default complexity
        budget: team?.budget_limit || 10
      });
      
      setTaskInput('');
      
      // Add a system message showing the task was submitted
      const newMessage: Message = {
        id: `system-${Date.now()}`,
        agent: 'System',
        content: `Task submitted: ${taskInput}`,
        timestamp: new Date().toISOString(),
        type: 'system'
      };
      
      setMessages(prev => [...prev, newMessage]);
    } catch (err) {
      setError('Failed to submit task');
      console.error(err);
    } finally {
      setIsTaskSubmitting(false);
    }
  };

  const handleScreenshotTaken = async (path: string) => {
    setLatestScreenshotPath(path);
    
    // Add a system message showing a screenshot was captured
    const newMessage: Message = {
      id: `screenshot-${Date.now()}`,
      agent: 'System',
      content: `UI Screenshot captured: ${path}`,
      timestamp: new Date().toISOString(),
      type: 'system'
    };
    
    setMessages(prev => [...prev, newMessage]);
    
    // Notify agents about the screenshot
    try {
      await axios.post(`/api/screenshots`, {
        path,
        teamId,
        timestamp: new Date().toISOString(),
        context: {
          url: window.location.href,
          viewport: {
            width: window.innerWidth,
            height: window.innerHeight
          }
        }
      });
      
      console.log('Screenshot shared with agents:', path);
    } catch (err) {
      console.error('Failed to share screenshot with agents:', err);
    }
  };

  if (isLoading) {
    return (
      <div className="loading-container">
        <div className="spinner"></div>
        <p>Loading workspace...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="error-container">
        <h2>Error</h2>
        <p>{error}</p>
        <button 
          className="btn btn-primary" 
          onClick={() => window.location.reload()}
        >
          Retry
        </button>
      </div>
    );
  }

  const renderFileTree = (files: File[], depth = 0) => {
    return files.map(file => (
      <div key={file.id} style={{ marginLeft: `${depth * 16}px` }}>
        <div 
          className={`file-item ${file.type} ${activeFile === file.path ? 'active' : ''}`}
          onClick={() => file.type === 'file' ? handleFileSelect(file.path) : null}
        >
          {file.type === 'directory' ? '📁' : '📄'} {file.name}
        </div>
        {file.children && file.children.length > 0 && renderFileTree(file.children, depth + 1)}
      </div>
    ));
  };

  return (
    <div className="workspace-container">
      <div className="workspace-header">
        <h1>{team?.name} Workspace</h1>
        <div className="team-stats">
          <div className="stat">
            <span className="stat-label">Model Tier</span>
            <span className="stat-value">{team?.model_tier}</span>
          </div>
          <div className="stat">
            <span className="stat-label">Budget</span>
            <span className="stat-value">${team?.budget_limit}</span>
          </div>
          <div className="stat">
            <span className="stat-label">Agents</span>
            <span className="stat-value">{team?.roles.length}</span>
          </div>
        </div>
      </div>

      <div className="workspace-layout">
        <div className="files-panel">
          <div className="panel-header">
            <h2>Files</h2>
          </div>
          <div className="file-tree">
            {files.length === 0 ? (
              <p className="empty-message">No files yet</p>
            ) : (
              renderFileTree(files)
            )}
          </div>
        </div>

        <div className="editor-panel">
          <div className="panel-header">
            <h2>{activeFile || 'Select a file'}</h2>
          </div>
          <div className="file-content">
            {activeFile ? (
              <pre>{fileContent}</pre>
            ) : (
              <div className="empty-state">
                <p>Select a file to view its content</p>
              </div>
            )}
          </div>
        </div>

        <div className="conversation-panel">
          <div className="panel-header">
            <h2>Agent Conversation</h2>
          </div>
          <div className="messages-container">
            {messages.length === 0 ? (
              <div className="empty-state">
                <p>No messages yet. Submit a task to get started.</p>
              </div>
            ) : (
              messages.map(message => (
                <div key={message.id} className={`message ${message.type} ${message.agent.toLowerCase()}`}>
                  <div className="message-header">
                    <span className="agent-name">{message.agent}</span>
                    <span className="timestamp">{new Date(message.timestamp).toLocaleTimeString()}</span>
                  </div>
                  <div className="message-content">
                    {message.type === 'code' ? (
                      <pre><code>{message.content}</code></pre>
                    ) : (
                      <p>{message.content}</p>
                    )}
                  </div>
                </div>
              ))
            )}
          </div>
          <form onSubmit={handleTaskSubmit} className="task-input-form">
            <textarea
              value={taskInput}
              onChange={e => setTaskInput(e.target.value)}
              placeholder="Describe your task here..."
              className="task-input"
              rows={3}
            />
            <button 
              type="submit" 
              className="btn btn-primary"
              disabled={isTaskSubmitting}
            >
              {isTaskSubmitting ? 'Submitting...' : 'Submit Task'}
            </button>
          </form>
          
          {/* UI Screenshot Tool */}
          <div className="mt-4">
            <ScreenshotTool onScreenshotTaken={handleScreenshotTaken} />
          </div>
        </div>
      </div>
    </div>
  );
};

export default Workspace; 