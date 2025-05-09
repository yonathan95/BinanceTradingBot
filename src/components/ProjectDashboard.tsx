import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';

interface Project {
  id: string;
  name: string;
  description: string;
  template: string;
  created_at: string;
  last_updated: string;
  team_members: number;
  progress: number;
}

interface ProjectDashboardProps {
  workspaceId: string;
}

const ProjectDashboard: React.FC<ProjectDashboardProps> = ({ workspaceId }) => {
  const [projects, setProjects] = useState<Project[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  const [searchTerm, setSearchTerm] = useState('');
  const [sortBy, setSortBy] = useState<'name' | 'last_updated' | 'progress'>('last_updated');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');
  const navigate = useNavigate();

  useEffect(() => {
    const fetchProjects = async () => {
      try {
        setIsLoading(true);
        
        // Use mock data
        // First try to get workspace-specific data
        const response = await axios.get(`/mock-api/api/workspace-${workspaceId}.json`);
        
        // Transform the project data to match the expected format
        const projectsData = response.data.projects.map((project: any) => ({
          id: project.id,
          name: project.name,
          description: project.description,
          template: project.status || 'Default',
          created_at: project.created_at,
          last_updated: project.updated_at,
          team_members: 3,
          progress: Math.floor(Math.random() * 100) // Random progress value for demo
        }));
        
        setProjects(projectsData);
        setError('');
      } catch (err) {
        setError('Failed to load projects');
        console.error(err);
      } finally {
        setIsLoading(false);
      }
    };

    fetchProjects();
  }, [workspaceId]);

  const handleCreateProject = () => {
    navigate(`/workspaces/${workspaceId}/projects/new`);
  };

  const handleProjectClick = (projectId: string) => {
    navigate(`/workspaces/${workspaceId}/projects/${projectId}`);
  };

  const filteredProjects = projects.filter(project => 
    project.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    project.description.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const sortedProjects = [...filteredProjects].sort((a, b) => {
    if (sortBy === 'name') {
      return sortOrder === 'asc' 
        ? a.name.localeCompare(b.name) 
        : b.name.localeCompare(a.name);
    } else if (sortBy === 'progress') {
      return sortOrder === 'asc' 
        ? a.progress - b.progress 
        : b.progress - a.progress;
    } else {
      return sortOrder === 'asc' 
        ? new Date(a.last_updated).getTime() - new Date(b.last_updated).getTime() 
        : new Date(b.last_updated).getTime() - new Date(a.last_updated).getTime();
    }
  });

  const handleSort = (column: 'name' | 'last_updated' | 'progress') => {
    if (sortBy === column) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortBy(column);
      setSortOrder('desc');
    }
  };

  if (isLoading) {
    return (
      <div className="loading-container">
        <div className="spinner"></div>
        <p>Loading projects...</p>
      </div>
    );
  }

  return (
    <div className="project-dashboard">
      <div className="dashboard-header">
        <h2>Projects</h2>
        <div className="dashboard-actions">
          <div className="search-container">
            <input
              type="text"
              placeholder="Search projects..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="search-input"
            />
          </div>
          <button className="btn btn-primary" onClick={handleCreateProject}>
            Create New Project
          </button>
        </div>
      </div>

      {error && (
        <div className="error-message">
          {error}
        </div>
      )}

      {!isLoading && sortedProjects.length === 0 && (
        <div className="empty-state">
          <h3>No projects yet</h3>
          <p>Create your first project to get started</p>
          <button className="btn btn-primary" onClick={handleCreateProject}>
            Create Project
          </button>
        </div>
      )}

      {sortedProjects.length > 0 && (
        <div className="projects-grid">
          <div className="projects-header">
            <div 
              className={`header-cell ${sortBy === 'name' ? 'active' : ''}`} 
              onClick={() => handleSort('name')}
            >
              Name {sortBy === 'name' && (sortOrder === 'asc' ? '↑' : '↓')}
            </div>
            <div className="header-cell">Template</div>
            <div className="header-cell">Team Size</div>
            <div 
              className={`header-cell ${sortBy === 'progress' ? 'active' : ''}`}
              onClick={() => handleSort('progress')}
            >
              Progress {sortBy === 'progress' && (sortOrder === 'asc' ? '↑' : '↓')}
            </div>
            <div 
              className={`header-cell ${sortBy === 'last_updated' ? 'active' : ''}`}
              onClick={() => handleSort('last_updated')}
            >
              Last Updated {sortBy === 'last_updated' && (sortOrder === 'asc' ? '↑' : '↓')}
            </div>
          </div>

          {sortedProjects.map((project) => (
            <div 
              key={project.id} 
              className="project-card" 
              onClick={() => handleProjectClick(project.id)}
            >
              <div className="project-cell project-name">{project.name}</div>
              <div className="project-cell project-template">{project.template}</div>
              <div className="project-cell project-team-size">{project.team_members}</div>
              <div className="project-cell project-progress">
                <div className="progress-bar">
                  <div 
                    className="progress-fill" 
                    style={{ width: `${project.progress}%` }}
                  ></div>
                </div>
                <span>{project.progress}%</span>
              </div>
              <div className="project-cell project-updated">
                {new Date(project.last_updated).toLocaleDateString()}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default ProjectDashboard; 