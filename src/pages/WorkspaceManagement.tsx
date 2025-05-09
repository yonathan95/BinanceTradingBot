import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import axios from 'axios';
import ProjectDashboard from '../components/ProjectDashboard';
import ProjectTemplateSelector from '../components/ProjectTemplateSelector';
import FileManager from '../components/FileManager';
import CollaborationPanel from '../components/CollaborationPanel';
import ProjectConfig from '../components/ProjectConfig';
import ProjectMetrics from '../components/ProjectMetrics';

interface Workspace {
  id: string;
  name: string;
  description: string;
  created_at: string;
  updated_at: string;
  owner: string;
}

interface Project {
  id: string;
  name: string;
  description: string;
  template: string;
  created_at: string;
  last_updated: string;
}

const WorkspaceManagement: React.FC = () => {
  const { workspaceId, projectId } = useParams<{ workspaceId: string; projectId: string }>();
  const navigate = useNavigate();
  
  const [workspace, setWorkspace] = useState<Workspace | null>(null);
  const [currentProject, setCurrentProject] = useState<Project | null>(null);
  const [view, setView] = useState<'dashboard' | 'new-project' | 'project-details'>('dashboard');
  const [projectDetailTab, setProjectDetailTab] = useState<'files' | 'collaboration' | 'config' | 'metrics'>('files');
  const [selectedTemplateId, setSelectedTemplateId] = useState<string | null>(null);
  const [newProjectName, setNewProjectName] = useState('');
  const [newProjectDescription, setNewProjectDescription] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  const [currentFile, setCurrentFile] = useState<string | null>(null);
  const [metricsTimeRange, setMetricsTimeRange] = useState<'day' | 'week' | 'month' | 'all'>('week');

  // Fetch workspace data
  useEffect(() => {
    const fetchWorkspaceData = async () => {
      if (!workspaceId) return;
      
      try {
        setIsLoading(true);
        // Use mock data from our JSON files
        const response = await axios.get(`/mock-api/api/workspace-${workspaceId}.json`);
        setWorkspace(response.data);
        setError('');
      } catch (err) {
        setError('Failed to load workspace');
        console.error(err);
      } finally {
        setIsLoading(false);
      }
    };

    fetchWorkspaceData();
  }, [workspaceId]);

  // Fetch project data if projectId is present
  useEffect(() => {
    const fetchProjectData = async () => {
      if (!projectId) {
        setView('dashboard');
        setCurrentProject(null);
        return;
      }
      
      try {
        setIsLoading(true);
        // Use mock data from our JSON files
        const response = await axios.get(`/mock-api/api/project-${projectId}.json`);
        setCurrentProject(response.data);
        setView('project-details');
        setError('');
      } catch (err) {
        setError('Failed to load project');
        console.error(err);
      } finally {
        setIsLoading(false);
      }
    };

    fetchProjectData();
  }, [projectId]);

  // Handle create new project
  const handleCreateProject = async () => {
    if (!workspaceId || !selectedTemplateId || !newProjectName.trim()) {
      setError('Please provide project name and select a template');
      return;
    }
    
    try {
      setIsLoading(true);
      
      // For mock purposes, use an existing project ID since we can't actually create new ones
      const mockProjectId = 'prj-001';
      
      // In a real implementation, this would be an actual API call
      // const response = await axios.post(`/api/workspaces/${workspaceId}/projects`, {
      //   name: newProjectName,
      //   description: newProjectDescription,
      //   template_id: selectedTemplateId
      // });
      
      // Navigate to the mock project
      navigate(`/workspaces/${workspaceId}/projects/${mockProjectId}`);
    } catch (err) {
      setError('Failed to create project');
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  // Handle file selection
  const handleFileSelect = (filePath: string, content: string) => {
    setCurrentFile(filePath);
  };

  // Render loading state
  if (isLoading && !workspace) {
    return (
      <div className="loading-container">
        <div className="spinner"></div>
        <p>Loading workspace...</p>
      </div>
    );
  }

  // Render error state
  if (error && !workspace) {
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

  return (
    <div className="workspace-management">
      <div className="workspace-header">
        <div className="workspace-title">
          <h1>{workspace?.name}</h1>
          <p>{workspace?.description}</p>
        </div>
        
        <div className="workspace-actions">
          {view === 'dashboard' && (
            <>
              <button 
                className="btn btn-primary"
                onClick={() => setView('new-project')}
              >
                Create New Project
              </button>
              <button 
                onClick={() => navigate(`/workspaces/${workspaceId}/work-mode/dashboard`)}
                className="btn btn-outline ml-2"
              >
                Enter Workmode
              </button>
            </>
          )}
          
          {view === 'new-project' && (
            <button 
              className="btn btn-secondary"
              onClick={() => setView('dashboard')}
            >
              Back to Dashboard
            </button>
          )}
          
          {view === 'project-details' && (
            <>
              <button 
                className="btn btn-secondary"
                onClick={() => navigate(`/workspaces/${workspaceId}`)}
              >
                Back to Dashboard
              </button>
              <button 
                onClick={() => navigate(`/workspaces/${workspaceId}/work-mode/projects/${projectId}`)}
                className="btn btn-outline ml-2"
              >
                Enter Project Workmode
              </button>
            </>
          )}
        </div>
      </div>

      {error && <div className="error-message">{error}</div>}

      <div className="workspace-content">
        {view === 'dashboard' && workspaceId && (
          <ProjectDashboard workspaceId={workspaceId} />
        )}

        {view === 'new-project' && (
          <div className="new-project-form">
            <h2>Create New Project</h2>
            
            <div className="form-group">
              <label>Project Name</label>
              <input 
                type="text"
                className="form-control"
                value={newProjectName}
                onChange={(e) => setNewProjectName(e.target.value)}
                placeholder="Enter project name"
              />
            </div>
            
            <div className="form-group">
              <label>Description</label>
              <textarea 
                className="form-control"
                value={newProjectDescription}
                onChange={(e) => setNewProjectDescription(e.target.value)}
                placeholder="Enter project description"
                rows={3}
              />
            </div>
            
            <ProjectTemplateSelector 
              onSelect={setSelectedTemplateId}
              selectedTemplateId={selectedTemplateId}
            />
            
            <div className="form-actions">
              <button 
                className="btn btn-secondary"
                onClick={() => setView('dashboard')}
              >
                Cancel
              </button>
              <button 
                className="btn btn-primary"
                onClick={handleCreateProject}
                disabled={!selectedTemplateId || !newProjectName.trim()}
              >
                Create Project
              </button>
            </div>
          </div>
        )}

        {view === 'project-details' && currentProject && projectId && (
          <div className="project-details">
            <div className="project-header">
              <h2>{currentProject.name}</h2>
              <p>{currentProject.description}</p>
            </div>
            
            <div className="project-tabs">
              <button 
                className={`tab ${projectDetailTab === 'files' ? 'active' : ''}`}
                onClick={() => setProjectDetailTab('files')}
              >
                Files
              </button>
              <button 
                className={`tab ${projectDetailTab === 'collaboration' ? 'active' : ''}`}
                onClick={() => setProjectDetailTab('collaboration')}
              >
                Collaboration
              </button>
              <button 
                className={`tab ${projectDetailTab === 'config' ? 'active' : ''}`}
                onClick={() => setProjectDetailTab('config')}
              >
                Configuration
              </button>
              <button 
                className={`tab ${projectDetailTab === 'metrics' ? 'active' : ''}`}
                onClick={() => setProjectDetailTab('metrics')}
              >
                Metrics
              </button>
            </div>
            
            <div className="project-content">
              {projectDetailTab === 'files' && (
                <FileManager 
                  projectId={projectId} 
                  onFileSelect={handleFileSelect}
                />
              )}
              
              {projectDetailTab === 'collaboration' && (
                <CollaborationPanel 
                  projectId={projectId}
                  currentFile={currentFile}
                />
              )}
              
              {projectDetailTab === 'config' && (
                <ProjectConfig 
                  projectId={projectId}
                  onUpdate={() => window.location.reload()}
                />
              )}
              
              {projectDetailTab === 'metrics' && (
                <div className="metrics-container">
                  <div className="metrics-time-controls">
                    <label>Time Range:</label>
                    <select 
                      value={metricsTimeRange}
                      onChange={(e) => setMetricsTimeRange(e.target.value as 'day' | 'week' | 'month' | 'all')}
                      className="form-select"
                    >
                      <option value="day">Last 24 Hours</option>
                      <option value="week">Last 7 Days</option>
                      <option value="month">Last 30 Days</option>
                      <option value="all">All Time</option>
                    </select>
                  </div>
                  
                  <ProjectMetrics 
                    projectId={projectId}
                    timeRange={metricsTimeRange}
                  />
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default WorkspaceManagement; 