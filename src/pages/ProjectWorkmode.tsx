import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import WorkmodeHeader from '../components/workmode/WorkmodeHeader';
import { useTagAccess } from '../hooks/useTagAccess';
import { TaggedEntity } from '../services/tags/types';

interface Task {
  id: string;
  title: string;
  status: 'todo' | 'in-progress' | 'review' | 'done';
  assignee?: string;
  priority: 'low' | 'medium' | 'high';
}

const ProjectWorkmode = () => {
  const { projectId, workspaceId } = useParams<{ projectId: string, workspaceId: string }>();
  const navigate = useNavigate();
  const { getAccessibleEntities, hasAccessToEntity } = useTagAccess();
  const [project, setProject] = useState<TaggedEntity | null>(null);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!projectId) return;

    // Find the project from tagged entities
    const projects = getAccessibleEntities('project');
    const currentProject = projects.find(p => p.id === projectId) || null;
    setProject(currentProject);

    // TODO: Replace with actual API call to fetch tasks
    // For now, we'll use mock data
    const mockTasks: Task[] = [
      { id: 'task-1', title: 'Implement login page', status: 'todo', priority: 'high' },
      { id: 'task-2', title: 'Fix navigation bug', status: 'in-progress', assignee: 'User 1', priority: 'medium' },
      { id: 'task-3', title: 'Add unit tests', status: 'todo', priority: 'medium' },
      { id: 'task-4', title: 'Update documentation', status: 'review', assignee: 'User 2', priority: 'low' },
      { id: 'task-5', title: 'Performance optimization', status: 'done', assignee: 'User 3', priority: 'high' },
    ];

    // In a real implementation, you would filter tasks by project ID and workspace ID
    setTasks(mockTasks);
    setLoading(false);
  }, [projectId, getAccessibleEntities, hasAccessToEntity]);

  const handleBackToWorkspace = () => {
    if (workspaceId) {
      navigate(`/workspaces/${workspaceId}/work-mode/dashboard`);
    } else {
      navigate('/workspaces');
    }
  };

  if (loading) {
    return <div className="p-8">Loading project data...</div>;
  }

  if (!project) {
    return <div className="p-8">Project not found or you do not have access to view it.</div>;
  }

  return (
    <div className="flex flex-col h-full">
      <WorkmodeHeader 
        title={project.name} 
        entityId={projectId || ''} 
        entityType="project" 
      />
      
      <div className="p-6">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-semibold">Tasks in Project: {project.name}</h2>
          <button 
            onClick={handleBackToWorkspace}
            className="px-4 py-2 bg-blue-100 text-blue-700 rounded hover:bg-blue-200"
          >
            Back to Workspace
          </button>
        </div>
        
        {tasks.length === 0 ? (
          <p>No tasks found in this project.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full bg-white">
              <thead className="bg-gray-100">
                <tr>
                  <th className="py-2 px-4 text-left">Title</th>
                  <th className="py-2 px-4 text-left">Status</th>
                  <th className="py-2 px-4 text-left">Assignee</th>
                  <th className="py-2 px-4 text-left">Priority</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {tasks.map(task => (
                  <tr key={task.id} className="hover:bg-gray-50">
                    <td className="py-2 px-4">{task.title}</td>
                    <td className="py-2 px-4">
                      <span className={`inline-block px-2 py-1 text-xs rounded-full ${
                        task.status === 'todo' ? 'bg-gray-200' :
                        task.status === 'in-progress' ? 'bg-blue-200' :
                        task.status === 'review' ? 'bg-yellow-200' :
                        'bg-green-200'
                      }`}>
                        {task.status}
                      </span>
                    </td>
                    <td className="py-2 px-4">{task.assignee || 'Unassigned'}</td>
                    <td className="py-2 px-4">
                      <span className={`inline-block w-2 h-2 rounded-full mr-2 ${
                        task.priority === 'high' ? 'bg-red-500' :
                        task.priority === 'medium' ? 'bg-yellow-500' :
                        'bg-green-500'
                      }`}></span>
                      {task.priority}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};

export default ProjectWorkmode; 