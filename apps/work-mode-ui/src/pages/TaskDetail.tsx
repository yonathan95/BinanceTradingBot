import { useParams, useNavigate } from 'react-router-dom';
import { useStore } from '../hooks/useStore';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { ChevronLeft, Clock, CheckCircle, AlertCircle, Activity } from 'lucide-react';

const TaskDetail = () => {
  const { id: agentId, taskId } = useParams<{ id: string; taskId: string }>();
  const navigate = useNavigate();
  
  const { agents, tasks } = useStore(state => ({
    agents: state.agents,
    tasks: state.tasks
  }));
  
  // Find the task by id
  const task = tasks.find(t => t.id === taskId);
  
  // Find the agent by id
  const agent = agents.find(a => a.id === agentId);
  
  if (!task || !agent) {
    return (
      <div className="p-6">
        <div className="flex items-center mb-6">
          <button 
            className="flex items-center text-gray-600 hover:text-gray-900"
            onClick={() => navigate(-1)}
          >
            <ChevronLeft className="h-5 w-5 mr-1" />
            <span>Back</span>
          </button>
        </div>
        <div className="flex items-center justify-center h-64">
          <p className="text-gray-500">Task not found</p>
        </div>
      </div>
    );
  }
  
  // Format the dates
  const createdAt = new Date(task.createdAt).toLocaleString();
  const updatedAt = new Date(task.updatedAt).toLocaleString();
  
  // Status icon
  const StatusIcon = 
    task.status === 'COMPLETE' ? CheckCircle :
    task.status === 'ERROR' ? AlertCircle :
    Activity;
  
  // Status color
  const statusColor = 
    task.status === 'COMPLETE' ? 'text-green-500' :
    task.status === 'ERROR' ? 'text-red-500' :
    'text-yellow-500';
  
  const statusBgColor = 
    task.status === 'COMPLETE' ? 'bg-green-100' :
    task.status === 'ERROR' ? 'bg-red-100' :
    'bg-yellow-100';
  
  const statusTextColor = 
    task.status === 'COMPLETE' ? 'text-green-800' :
    task.status === 'ERROR' ? 'text-red-800' :
    'text-yellow-800';
  
  return (
    <div className="p-6">
      <div className="flex items-center mb-6">
        <button 
          className="flex items-center text-gray-600 hover:text-gray-900"
          onClick={() => navigate(-1)}
        >
          <ChevronLeft className="h-5 w-5 mr-1" />
          <span>Back</span>
        </button>
      </div>
      
      {/* Task Header */}
      <div className="mb-8">
        <div className="flex items-center justify-between mb-2">
          <h1 className="text-2xl font-bold">{task.title}</h1>
          <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${statusBgColor} ${statusTextColor}`}>
            <StatusIcon className={`h-4 w-4 mr-1 ${statusColor}`} />
            {task.status}
          </span>
        </div>
        <div className="flex items-center text-gray-500">
          <span className="flex items-center mr-4">
            <Clock className="h-4 w-4 mr-1" />
            Created: {createdAt}
          </span>
          <span className="flex items-center">
            <Clock className="h-4 w-4 mr-1" />
            Updated: {updatedAt}
          </span>
        </div>
      </div>
      
      {/* Task Details */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
        <div className="lg:col-span-2">
          <Card>
            <CardHeader>
              <CardTitle>Task Description</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-gray-700">
                {/* In a real app, this would be the actual task description */}
                This is a detailed description of the task. It includes requirements, expected outcomes, and any relevant context that would help the agent complete the task successfully.
              </p>
              
              <div className="mt-6 border-t border-gray-200 pt-4">
                <h3 className="font-medium mb-2">Requirements</h3>
                <ul className="list-disc pl-5 space-y-1 text-gray-700">
                  <li>Implement feature according to specifications</li>
                  <li>Write unit tests for new functionality</li>
                  <li>Ensure code meets project style guidelines</li>
                  <li>Update documentation as needed</li>
                </ul>
              </div>
              
              <div className="mt-6 border-t border-gray-200 pt-4">
                <h3 className="font-medium mb-2">Acceptance Criteria</h3>
                <ul className="list-disc pl-5 space-y-1 text-gray-700">
                  <li>All tests must pass</li>
                  <li>Code review approval required</li>
                  <li>Documentation updated</li>
                  <li>Performance benchmarks met</li>
                </ul>
              </div>
            </CardContent>
          </Card>
        </div>
        
        <div>
          <Card className="mb-6">
            <CardHeader>
              <CardTitle>Assigned Agent</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center">
                <div className="w-10 h-10 rounded-full bg-gray-300 flex items-center justify-center mr-3 overflow-hidden">
                  {agent.avatarUrl ? (
                    <img 
                      src={agent.avatarUrl} 
                      alt={agent.name} 
                      className="w-full h-full object-cover"
                    />
                  ) : (
                    <div className="text-lg font-bold text-gray-700">
                      {agent.name.charAt(0)}
                    </div>
                  )}
                </div>
                <div>
                  <p className="font-medium">{agent.name}</p>
                  <p className="text-sm text-gray-500">{agent.role}</p>
                </div>
              </div>
              
              <div className="mt-4 pt-4 border-t border-gray-200">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-500">Status</span>
                  <span className={`capitalize ${
                    agent.status === 'idle' ? 'text-green-500' :
                    agent.status === 'busy' ? 'text-yellow-500' :
                    'text-red-500'
                  }`}>
                    {agent.status}
                  </span>
                </div>
              </div>
            </CardContent>
          </Card>
          
          <Card>
            <CardHeader>
              <CardTitle>Task Actions</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                <button 
                  className="w-full py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-primary hover:bg-primary/90 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary"
                  onClick={() => {
                    // In a real app, this would open a chat with the agent about this task
                    useStore.getState().setActiveAgent(agentId || null);
                  }}
                >
                  Discuss with Agent
                </button>
                
                <button 
                  className="w-full py-2 px-4 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary"
                  onClick={() => {
                    // In a real app, this would allow changing task priority or reassigning
                    alert('This would open task settings in a real app');
                  }}
                >
                  Task Settings
                </button>
                
                {task.status !== 'COMPLETE' && (
                  <button 
                    className="w-full py-2 px-4 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary"
                    onClick={() => {
                      // In a real app, this would mark the task as complete
                      useStore.getState().setTaskStatus({
                        taskId: task.id,
                        status: 'COMPLETE'
                      });
                    }}
                  >
                    Mark as Complete
                  </button>
                )}
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default TaskDetail; 