import { useParams, useNavigate } from 'react-router-dom';
import { useState, useEffect } from 'react';
import { useStore } from '../hooks/useStore';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { ChevronLeft, MessageSquare, GitBranch, AlertTriangle, Clock, Zap } from 'lucide-react';

const AgentDetail = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { agents, timelines, tokenBurnForecasts, setActiveAgent } = useStore(state => ({
    agents: state.agents,
    timelines: state.timelines,
    tokenBurnForecasts: state.tokenBurnForecasts,
    setActiveAgent: state.setActiveAgent
  }));
  
  const [selectedTab, setSelectedTab] = useState<'timeline' | 'tasks'>('timeline');
  
  // Find the agent by id
  const agent = agents.find(a => a.id === id);
  // Get agent timeline events
  const agentTimeline = timelines[id || ''] || [];
  // Get agent tasks
  const agentTasks = useStore(state => 
    state.tasks.filter(task => task.agentId === id)
  );
  
  // Open chat drawer when page loads
  useEffect(() => {
    if (id) {
      setActiveAgent(id);
    }
    
    return () => {
      // Close drawer when navigating away
      setActiveAgent(null);
    };
  }, [id, setActiveAgent]);
  
  if (!agent) {
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
          <p className="text-gray-500">Agent not found</p>
        </div>
      </div>
    );
  }
  
  // Format the token burn rate
  const tokenBurn = tokenBurnForecasts[id || ''];
  const formattedTokenBurn = tokenBurn 
    ? `$${tokenBurn.perHourUsd.toFixed(2)}/hr`
    : 'N/A';
  
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
      
      {/* Agent Header */}
      <div className="flex items-start justify-between mb-8">
        <div>
          <div className="flex items-center">
            <div className="w-12 h-12 rounded-full bg-gray-300 flex items-center justify-center mr-4 overflow-hidden">
              {agent.avatarUrl ? (
                <img 
                  src={agent.avatarUrl} 
                  alt={agent.name} 
                  className="w-full h-full object-cover"
                />
              ) : (
                <div className="text-2xl font-bold text-gray-700">
                  {agent.name.charAt(0)}
                </div>
              )}
            </div>
            <div>
              <h1 className="text-2xl font-bold flex items-center">
                {agent.name}
                <div className={`ml-2 w-3 h-3 rounded-full ${
                  agent.status === 'idle' ? 'bg-green-500' :
                  agent.status === 'busy' ? 'bg-yellow-500' :
                  'bg-red-500'
                }`} />
              </h1>
              <p className="text-gray-500">{agent.role}</p>
            </div>
          </div>
        </div>
        
        <div className="flex items-center">
          <button 
            className="px-4 py-2 rounded-md border border-gray-300 flex items-center mr-2"
            onClick={() => setActiveAgent(id || null)}
          >
            <MessageSquare className="h-4 w-4 mr-2" />
            <span>Chat</span>
          </button>
        </div>
      </div>
      
      {/* Agent Stats */}
      <div className="grid grid-cols-4 gap-4 mb-8">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">Status</p>
                <p className="text-lg font-medium capitalize">{agent.status}</p>
              </div>
              <div className={`p-2 rounded-full ${
                agent.status === 'idle' ? 'bg-green-100' :
                agent.status === 'busy' ? 'bg-yellow-100' :
                'bg-red-100'
              }`}>
                <div className={`w-5 h-5 ${
                  agent.status === 'idle' ? 'text-green-500' :
                  agent.status === 'busy' ? 'text-yellow-500' :
                  'text-red-500'
                }`}>
                  {agent.status === 'error' ? <AlertTriangle /> : <Clock />}
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">Token Burn Rate</p>
                <p className="text-lg font-medium">{formattedTokenBurn}</p>
              </div>
              <div className="p-2 rounded-full bg-blue-100">
                <Zap className="w-5 h-5 text-blue-500" />
              </div>
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">Tasks Completed</p>
                <p className="text-lg font-medium">
                  {agentTasks.filter(task => task.status === 'COMPLETE').length}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">Current Task</p>
                <p className="text-lg font-medium truncate">
                  {agent.currentTask || 'None'}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
      
      {/* Tabs for Timeline and Tasks */}
      <div className="mb-4">
        <div className="flex border-b border-gray-200">
          <button
            className={`px-4 py-2 text-sm font-medium border-b-2 ${
              selectedTab === 'timeline' 
                ? 'border-primary text-primary' 
                : 'border-transparent text-gray-500 hover:text-gray-900'
            }`}
            onClick={() => setSelectedTab('timeline')}
          >
            Timeline
          </button>
          <button
            className={`px-4 py-2 text-sm font-medium border-b-2 ${
              selectedTab === 'tasks' 
                ? 'border-primary text-primary' 
                : 'border-transparent text-gray-500 hover:text-gray-900'
            }`}
            onClick={() => setSelectedTab('tasks')}
          >
            Tasks
          </button>
        </div>
      </div>
      
      {/* Tab Content */}
      {selectedTab === 'timeline' && (
        <Card>
          <CardHeader>
            <CardTitle>Activity Timeline</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-6">
              {agentTimeline.length > 0 ? (
                agentTimeline.map((event, index) => (
                  <div key={event.commitSha} className="flex relative">
                    <div className="mr-4 relative">
                      <div className="w-8 h-8 rounded-full bg-gray-100 flex items-center justify-center">
                        <GitBranch className="w-4 h-4 text-gray-600" />
                      </div>
                      {index < agentTimeline.length - 1 && (
                        <div className="absolute w-0.5 bg-gray-200 h-full top-8 left-4 -translate-x-1/2" />
                      )}
                    </div>
                    <div>
                      <p className="font-medium">{event.message}</p>
                      <p className="text-sm text-gray-500">
                        {new Date(event.timestamp).toLocaleString()}
                      </p>
                      <p className="text-sm mt-1">
                        {event.diffSize > 0
                          ? `Modified ${event.diffSize} lines of code`
                          : 'No code changes'
                        }
                      </p>
                    </div>
                  </div>
                ))
              ) : (
                <p className="text-center text-gray-500 py-8">No activity recorded yet</p>
              )}
            </div>
          </CardContent>
        </Card>
      )}
      
      {selectedTab === 'tasks' && (
        <Card>
          <CardHeader>
            <CardTitle>Tasks</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full border-collapse">
                <thead>
                  <tr className="border-b">
                    <th className="text-left py-3 px-4 font-medium text-gray-500">Task</th>
                    <th className="text-left py-3 px-4 font-medium text-gray-500">Status</th>
                    <th className="text-left py-3 px-4 font-medium text-gray-500">Created</th>
                    <th className="text-left py-3 px-4 font-medium text-gray-500">Last Updated</th>
                  </tr>
                </thead>
                <tbody>
                  {agentTasks.length > 0 ? agentTasks.map(task => (
                    <tr 
                      key={task.id} 
                      className="border-b cursor-pointer hover:bg-gray-50"
                      onClick={() => navigate(`/agent/${id}/task/${task.id}`)}
                    >
                      <td className="py-3 px-4">{task.title}</td>
                      <td className="py-3 px-4">
                        <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                          task.status === 'COMPLETE' ? 'bg-green-100 text-green-800' :
                          task.status === 'ERROR' ? 'bg-red-100 text-red-800' :
                          'bg-yellow-100 text-yellow-800'
                        }`}>
                          {task.status}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-gray-600 text-sm">
                        {new Date(task.createdAt).toLocaleString()}
                      </td>
                      <td className="py-3 px-4 text-gray-600 text-sm">
                        {new Date(task.updatedAt).toLocaleString()}
                      </td>
                    </tr>
                  )) : (
                    <tr>
                      <td colSpan={4} className="py-8 text-center text-gray-500">
                        No tasks assigned to this agent
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default AgentDetail; 