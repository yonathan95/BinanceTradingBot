import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import WorkmodeHeader from '../components/workmode/WorkmodeHeader';
import { useTagAccess } from '../hooks/useTagAccess';
import { TaggedEntity } from '../services/tags/types';

interface Project {
  id: string;
  name: string;
  description: string;
}

const WorkspaceWorkmode = () => {
  const { workspaceId } = useParams<{ workspaceId: string }>();
  const navigate = useNavigate();
  const { getAccessibleEntities, hasAccessToEntity } = useTagAccess();
  const [workspace, setWorkspace] = useState<TaggedEntity | null>(null);
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!workspaceId) return;

    // Find the workspace from tagged entities
    const workspaces = getAccessibleEntities('workspace');
    const currentWorkspace = workspaces.find(w => w.id === workspaceId) || null;
    setWorkspace(currentWorkspace);

    // TODO: Replace with actual API call to fetch projects
    // For now, we'll use mock data
    const mockProjects: Project[] = [
      { id: 'proj-1', name: 'Frontend App', description: 'User-facing application' },
      { id: 'proj-2', name: 'Backend API', description: 'RESTful API services' },
      { id: 'proj-3', name: 'Database Layer', description: 'Data persistence and access' },
      { id: 'proj-4', name: 'DevOps Pipeline', description: 'Continuous integration/deployment' },
    ];

    // Filter projects based on user access and workspace ID
    const accessibleProjects = mockProjects.filter(project => 
      hasAccessToEntity(project.id)
      // In a real implementation, you would filter projects by workspace ID
      // This is a placeholder for the actual implementation
    );

    setProjects(accessibleProjects);
    setLoading(false);
  }, [workspaceId, getAccessibleEntities, hasAccessToEntity]);

  if (loading) {
    return <div className="p-8">Loading workspace data...</div>;
  }

  if (!workspace) {
    return <div className="p-8">Workspace not found or you do not have access to view it.</div>;
  }

  // Function to handle navigation to project workmode
  const handleOpenProjectWorkmode = (projectId: string) => {
    navigate(`/workspaces/${workspaceId}/work-mode/projects/${projectId}`);
  };

  return (
    <div className="flex flex-col h-full">
      <WorkmodeHeader 
        title={workspace.name} 
        entityId={workspaceId || ''} 
        entityType="workspace" 
      />
      
      <div className="p-6">
        <h2 className="text-xl font-semibold mb-4">Projects in Workspace: {workspace.name}</h2>
        
        {projects.length === 0 ? (
          <p>No accessible projects found in this workspace.</p>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {projects.map(project => (
              <div 
                key={project.id}
                className="border rounded-lg p-4 hover:bg-gray-50 transition-colors"
              >
                <h3 className="text-lg font-medium">{project.name}</h3>
                <p className="text-gray-600 mt-1">{project.description}</p>
                <button 
                  onClick={() => handleOpenProjectWorkmode(project.id)}
                  className="text-blue-600 hover:text-blue-800 mt-3 inline-block"
                >
                  Open Project Workmode
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default WorkspaceWorkmode; 