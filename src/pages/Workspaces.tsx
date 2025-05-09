import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import axios from 'axios';

interface Workspace {
  id: string;
  name: string;
  description: string;
  projects: number;
  created_at: string;
  updated_at: string;
}

const Workspaces: React.FC = () => {
  const [workspaces, setWorkspaces] = useState<Workspace[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  const navigate = useNavigate();

  useEffect(() => {
    const fetchWorkspaces = async () => {
      try {
        setIsLoading(true);
        const response = await axios.get('/mock-api/api/workspaces.json');
        setWorkspaces(response.data);
        setError('');
      } catch (err) {
        setError('Failed to load workspaces');
        console.error(err);
      } finally {
        setIsLoading(false);
      }
    };

    fetchWorkspaces();
  }, []);

  const handleCreateWorkspace = () => {
    // Navigate to workspace creation page or open modal
    // For now, we'll just implement a placeholder
    console.log('Create workspace clicked');
  };

  if (isLoading) {
    return (
      <div className="loading-container">
        <div className="spinner"></div>
        <p>Loading workspaces...</p>
      </div>
    );
  }

  return (
    <div className="workspaces-page">
      <div className="workspaces-header">
        <h1>My Workspaces</h1>
        <button 
          className="btn btn-primary"
          onClick={handleCreateWorkspace}
        >
          Create New Workspace
        </button>
      </div>

      {error && <div className="error-message">{error}</div>}

      <div className="workspaces-grid">
        {workspaces.length === 0 ? (
          <div className="empty-state">
            <h3>No workspaces yet</h3>
            <p>Create your first workspace to get started</p>
            <button 
              className="btn btn-primary"
              onClick={handleCreateWorkspace}
            >
              Create Workspace
            </button>
          </div>
        ) : (
          workspaces.map(workspace => (
            <div key={workspace.id} className="workspace-card">
              <div className="workspace-info">
                <h3>{workspace.name}</h3>
                <p>{workspace.description}</p>
              </div>
              <div className="workspace-stats">
                <div className="stat">
                  <span className="stat-value">{workspace.projects}</span>
                  <span className="stat-label">Projects</span>
                </div>
                <div className="stat">
                  <span className="stat-value">
                    {new Date(workspace.updated_at).toLocaleDateString()}
                  </span>
                  <span className="stat-label">Last Updated</span>
                </div>
              </div>
              <div className="workspace-actions">
                <button 
                  className="btn btn-primary"
                  onClick={() => navigate(`/workspaces/${workspace.id}`)}
                >
                  Open Workspace
                </button>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};

export default Workspaces; 