import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useStore } from '../hooks/useStore';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { ChevronLeft, Check } from 'lucide-react';

const TaskCreator = () => {
  const navigate = useNavigate();
  const agents = useStore(state => state.agents);
  
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [selectedAgentId, setSelectedAgentId] = useState('');
  const [priority, setPriority] = useState<'low' | 'medium' | 'high'>('medium');
  
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!title.trim() || !selectedAgentId) {
      alert('Please fill in all required fields');
      return;
    }
    
    // In a real app, this would create a new task via API call
    const newTask = {
      id: `task-${Date.now()}`,
      title,
      status: 'STARTED' as const,
      agentId: selectedAgentId,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString()
    };
    
    // Add task to store
    const tasks = useStore.getState().tasks;
    useStore.getState().tasks = [...tasks, newTask];
    
    // Navigate to the new task
    navigate(`/agent/${selectedAgentId}/task/${newTask.id}`);
  };
  
  return (
    <div className="p-6 max-w-4xl mx-auto">
      <div className="flex items-center mb-6">
        <button 
          className="flex items-center text-gray-600 hover:text-gray-900"
          onClick={() => navigate(-1)}
        >
          <ChevronLeft className="h-5 w-5 mr-1" />
          <span>Back</span>
        </button>
      </div>
      
      <Card>
        <CardHeader>
          <CardTitle>Create New Task</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit}>
            <div className="space-y-6">
              {/* Task Title */}
              <div>
                <label htmlFor="title" className="block text-sm font-medium text-gray-700">
                  Task Title <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  id="title"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  placeholder="Enter a concise title for the task"
                  className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-primary focus:border-primary"
                  required
                />
              </div>
              
              {/* Task Description */}
              <div>
                <label htmlFor="description" className="block text-sm font-medium text-gray-700">
                  Task Description
                </label>
                <textarea
                  id="description"
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  rows={4}
                  placeholder="Enter a detailed description of the task, including requirements and acceptance criteria"
                  className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-primary focus:border-primary"
                />
              </div>
              
              {/* Assign Agent */}
              <div>
                <label htmlFor="agent" className="block text-sm font-medium text-gray-700">
                  Assign to Agent <span className="text-red-500">*</span>
                </label>
                <select
                  id="agent"
                  value={selectedAgentId}
                  onChange={(e) => setSelectedAgentId(e.target.value)}
                  className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-primary focus:border-primary"
                  required
                >
                  <option value="">Select an agent</option>
                  {agents.map(agent => (
                    <option 
                      key={agent.id} 
                      value={agent.id}
                      disabled={agent.status === 'error'}
                    >
                      {agent.name} ({agent.role}) - {agent.status === 'busy' ? 'Busy' : agent.status === 'idle' ? 'Available' : 'Error'}
                    </option>
                  ))}
                </select>
              </div>
              
              {/* Priority */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Priority
                </label>
                <div className="flex space-x-4">
                  <button
                    type="button"
                    className={`px-4 py-2 rounded-md ${
                      priority === 'low' 
                        ? 'bg-green-100 text-green-800 ring-2 ring-green-500'
                        : 'bg-gray-100 text-gray-800'
                    }`}
                    onClick={() => setPriority('low')}
                  >
                    Low
                  </button>
                  <button
                    type="button"
                    className={`px-4 py-2 rounded-md ${
                      priority === 'medium' 
                        ? 'bg-yellow-100 text-yellow-800 ring-2 ring-yellow-500'
                        : 'bg-gray-100 text-gray-800'
                    }`}
                    onClick={() => setPriority('medium')}
                  >
                    Medium
                  </button>
                  <button
                    type="button"
                    className={`px-4 py-2 rounded-md ${
                      priority === 'high' 
                        ? 'bg-red-100 text-red-800 ring-2 ring-red-500'
                        : 'bg-gray-100 text-gray-800'
                    }`}
                    onClick={() => setPriority('high')}
                  >
                    High
                  </button>
                </div>
              </div>
              
              {/* Submit Button */}
              <div className="pt-4">
                <button
                  type="submit"
                  className="w-full sm:w-auto px-6 py-3 bg-primary text-primary-foreground rounded-md flex items-center justify-center"
                >
                  <Check className="h-5 w-5 mr-2" />
                  Create Task
                </button>
              </div>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  );
};

export default TaskCreator; 