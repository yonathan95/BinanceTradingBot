import { useStore } from '../hooks/useStore';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { useNavigate } from 'react-router-dom';
import { Plus, Activity, CheckCircle, AlertCircle } from 'lucide-react';

const Dashboard = () => {
  const navigate = useNavigate();
  const { agents, tasks } = useStore(state => ({
    agents: state.agents,
    tasks: state.tasks
  }));
  
  // Calculate statistics
  const completedTasks = tasks.filter(task => task.status === 'COMPLETE').length;
  const activeTasks = tasks.filter(task => task.status === 'STARTED').length;
  const errorTasks = tasks.filter(task => task.status === 'ERROR').length;
  
  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold">Work Mode Dashboard</h1>
        <button
          className="px-4 py-2 bg-primary text-primary-foreground rounded-md flex items-center"
          onClick={() => navigate('/tasks/new')}
        >
          <Plus className="h-4 w-4 mr-2" />
          <span>New Task</span>
        </button>
      </div>
      
      {/* Stats overview */}
      <div className="grid grid-cols-3 gap-6 mb-8">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-gray-500">Active Tasks</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center">
              <Activity className="h-8 w-8 text-yellow-500 mr-2" />
              <span className="text-3xl font-bold">{activeTasks}</span>
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-gray-500">Completed Tasks</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center">
              <CheckCircle className="h-8 w-8 text-green-500 mr-2" />
              <span className="text-3xl font-bold">{completedTasks}</span>
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-gray-500">Issues</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center">
              <AlertCircle className="h-8 w-8 text-red-500 mr-2" />
              <span className="text-3xl font-bold">{errorTasks}</span>
            </div>
          </CardContent>
        </Card>
      </div>
      
      {/* Main content tabs */}
      <Tabs defaultValue="agents">
        <TabsList className="mb-4">
          <TabsTrigger value="agents">Active Agents</TabsTrigger>
          <TabsTrigger value="tasks">Recent Tasks</TabsTrigger>
          <TabsTrigger value="activity">Activity Feed</TabsTrigger>
        </TabsList>
        
        <TabsContent value="agents">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {agents.map(agent => (
              <Card key={agent.id} className="cursor-pointer hover:shadow-md transition-shadow" onClick={() => navigate(`/agent/${agent.id}`)}>
                <CardHeader className="pb-2">
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-lg font-medium">{agent.name}</CardTitle>
                    <div className={`w-3 h-3 rounded-full ${
                      agent.status === 'idle' ? 'bg-green-500' :
                      agent.status === 'busy' ? 'bg-yellow-500' :
                      'bg-red-500'
                    }`} />
                  </div>
                  <p className="text-sm text-gray-500">{agent.role}</p>
                </CardHeader>
                <CardContent>
                  <div className="text-sm">
                    {agent.currentTask ? (
                      <div>
                        <p className="font-medium">Current task:</p>
                        <p className="text-gray-600 truncate">{agent.currentTask}</p>
                      </div>
                    ) : (
                      <p className="text-gray-600">Idle - No current task</p>
                    )}
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>
        
        <TabsContent value="tasks">
          <div className="overflow-x-auto">
            <table className="w-full border-collapse">
              <thead>
                <tr className="border-b">
                  <th className="text-left py-3 px-4 font-medium text-gray-500">Task</th>
                  <th className="text-left py-3 px-4 font-medium text-gray-500">Agent</th>
                  <th className="text-left py-3 px-4 font-medium text-gray-500">Status</th>
                  <th className="text-left py-3 px-4 font-medium text-gray-500">Created</th>
                  <th className="text-left py-3 px-4 font-medium text-gray-500">Last Updated</th>
                </tr>
              </thead>
              <tbody>
                {tasks.length > 0 ? tasks.map(task => {
                  const agent = agents.find(a => a.id === task.agentId);
                  return (
                    <tr 
                      key={task.id} 
                      className="border-b cursor-pointer hover:bg-gray-50"
                      onClick={() => navigate(`/agent/${task.agentId}/task/${task.id}`)}
                    >
                      <td className="py-3 px-4">{task.title}</td>
                      <td className="py-3 px-4">{agent?.name || 'Unknown'}</td>
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
                  );
                }) : (
                  <tr>
                    <td colSpan={5} className="py-8 text-center text-gray-500">
                      No tasks found
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </TabsContent>
        
        <TabsContent value="activity">
          <Card>
            <CardContent className="p-6">
              <div className="space-y-8">
                {Object.entries(useStore.getState().timelines).map(([agentId, events]) => {
                  const agent = agents.find(a => a.id === agentId);
                  if (!agent || events.length === 0) return null;
                  
                  return (
                    <div key={agentId} className="border-l-2 border-gray-200 pl-4">
                      <h3 className="font-medium mb-2">{agent.name} Activity</h3>
                      <div className="space-y-4">
                        {events.slice(0, 5).map(event => (
                          <div key={event.commitSha} className="relative">
                            <div className="absolute -left-6 w-2 h-2 rounded-full bg-primary" />
                            <div className="text-sm">
                              <p className="font-medium">{event.message}</p>
                              <p className="text-gray-500 text-xs">
                                {new Date(event.timestamp).toLocaleString()} • 
                                {event.diffSize > 0 ? ` ${event.diffSize} changes` : ' No changes'}
                              </p>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  );
                })}
                
                {Object.keys(useStore.getState().timelines).length === 0 && (
                  <div className="text-center py-8 text-gray-500">
                    No recent activity
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default Dashboard; 