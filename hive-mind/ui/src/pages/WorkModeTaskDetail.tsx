import { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { Box, Paper, Title, Text, Card, Group, Badge, Button, Grid, Timeline, ActionIcon, Textarea } from '@mantine/core';
import { IconBrain, IconChevronLeft, IconSettings, IconClipboardList, IconUser } from '../components/layout/icons';

interface Task {
  id: string;
  title: string;
  status: 'todo' | 'in-progress' | 'review' | 'done';
  assignedAgent?: string;
  priority: 'low' | 'medium' | 'high';
  workspaceId: string;
  description?: string;
  createdAt?: string;
  updatedAt?: string;
}

interface Agent {
  id: string;
  name: string;
  status: 'idle' | 'working' | 'error';
  type: string;
  taskCount: number;
  workspaceId: string;
}

export default function WorkModeTaskDetail() {
  const { workspaceId, taskId } = useParams<{ workspaceId: string, taskId: string }>();
  const navigate = useNavigate();
  
  // Add console logs to debug the component rendering
  console.log('WorkModeTaskDetail rendering with params:', { workspaceId, taskId });
  
  const [task, setTask] = useState<Task | null>(null);
  const [assignedAgent, setAssignedAgent] = useState<Agent | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [comment, setComment] = useState('');

  useEffect(() => {
    if (!workspaceId || !taskId) {
      console.error('Missing workspaceId or taskId');
      setError('Missing workspace or task information');
      setLoading(false);
      return;
    }

    console.log('Fetching task data for workspaceId:', workspaceId, 'taskId:', taskId);

    // Determine the actual taskId to use for fetching
    // This will handle both formats: "task-1" (when passed directly in URL) and "1" (when using :taskId param)
    const actualTaskId = taskId.startsWith('task-') ? taskId : `task-${taskId}`;
    
    console.log('Using actualTaskId for fetch:', actualTaskId);

    // Load task data with explicit error handling
    fetch(`/mock-api/api/workspace-${workspaceId}-tasks.json`)
      .then(response => {
        console.log('Task data response status:', response.status);
        if (!response.ok) {
          throw new Error(`Server responded with status: ${response.status}`);
        }
        return response.json();
      })
      .then(tasks => {
        console.log('Fetched tasks:', tasks);
        if (!Array.isArray(tasks)) {
          throw new Error('Invalid task data format: expected array');
        }
        
        // Look for the task by the actual task ID format
        const foundTask = tasks.find((t: Task) => t.id === actualTaskId);
        console.log('Found task:', foundTask);
        
        if (foundTask) {
          // Add some additional mock details for the task
          foundTask.description = foundTask.description || 
            `This is a ${foundTask.priority} priority task related to the project.`;
          foundTask.createdAt = foundTask.createdAt || '2025-02-15T10:00:00Z';
          foundTask.updatedAt = foundTask.updatedAt || '2025-02-18T14:30:00Z';
          
          setTask(foundTask);
          
          // If task has an assigned agent, fetch agent details
          if (foundTask.assignedAgent) {
            return fetch(`/mock-api/api/workspace-${workspaceId}-agents.json`)
              .then(response => {
                if (!response.ok) {
                  throw new Error(`Agent data error: ${response.status}`);
                }
                return response.json();
              })
              .then(agents => {
                const agent = agents.find((a: Agent) => a.id === foundTask.assignedAgent);
                if (agent) {
                  setAssignedAgent(agent);
                }
                return null;
              })
              .catch(error => {
                console.error('Error fetching agent data:', error);
                // Don't fail the whole component if just agent data fails
              });
          }
        } else {
          setError(`Task ${actualTaskId} not found in workspace ${workspaceId}`);
        }
        
        return null;
      })
      .catch(error => {
        console.error('Error in task fetching process:', error);
        setError(error.message || 'Error loading task data');
        // Create a fallback task as a last resort for UI debugging
        const fallbackTask: Task = {
          id: actualTaskId,
          title: `Fallback Task (${actualTaskId})`,
          status: 'todo',
          priority: 'medium',
          workspaceId,
          description: 'This is a fallback task created when the actual task data could not be loaded.',
          createdAt: new Date().toISOString(),
          updatedAt: new Date().toISOString()
        };
        setTask(fallbackTask);
      })
      .finally(() => {
        setLoading(false);
      });
  }, [workspaceId, taskId]);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'idle': return 'blue';
      case 'working': return 'green';
      case 'error': return 'red';
      case 'todo': return 'gray';
      case 'in-progress': return 'blue';
      case 'review': return 'yellow';
      case 'done': return 'green';
      default: return 'gray';
    }
  };

  const getPriorityLabel = (priority: string) => {
    return priority.charAt(0).toUpperCase() + priority.slice(1);
  };

  const getStatusLabel = (status: string) => {
    switch (status) {
      case 'in-progress': return 'In Progress';
      default: return status.charAt(0).toUpperCase() + status.slice(1);
    }
  };

  const handleAddComment = () => {
    if (!comment.trim()) return;
    
    // In a real app, this would send the comment to an API
    alert('Comment added: ' + comment);
    setComment('');
  };

  const handleChangeStatus = (newStatus: string) => {
    // In a real app, this would update the task status via API
    alert(`Task status changed to: ${newStatus}`);
  };

  if (loading) {
    return (
      <Box p="xl" style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <Text size="xl" c="gray.3">Loading task details...</Text>
      </Box>
    );
  }

  if (error && !task) {
    return (
      <Box p="xl" style={{ minHeight: '100vh' }}>
        <Paper p="md" mb="md" withBorder style={{ backgroundColor: '#2c2e33', borderColor: '#e03131' }}>
          <Title order={3} c="red.5">Error Loading Task</Title>
          <Text c="red.3">{error}</Text>
        </Paper>
        <Button 
          mt="md" 
          component={Link} 
          to={`/workspaces/${workspaceId}/work-mode/dashboard`}
          leftSection={<IconChevronLeft size={16} />}
          color="blue"
        >
          Back to Dashboard
        </Button>
      </Box>
    );
  }

  if (!task) {
    return (
      <Box p="xl" style={{ minHeight: '100vh' }}>
        <Paper p="md" mb="md" withBorder style={{ backgroundColor: '#2c2e33' }}>
          <Title order={3} c="gray.3">Task Not Found</Title>
          <Text c="gray.5">The requested task may not exist or has been removed.</Text>
        </Paper>
        <Button 
          mt="md" 
          component={Link} 
          to={`/workspaces/${workspaceId}/work-mode/dashboard`}
          leftSection={<IconChevronLeft size={16} />}
          color="blue"
        >
          Back to Dashboard
        </Button>
      </Box>
    );
  }

  return (
    <Box p="md">
      {/* Header */}
      <Paper p="md" mb="md" withBorder style={{ backgroundColor: '#2c2e33' }}>
        <Group justify="space-between">
          <Group>
            <ActionIcon 
              variant="subtle" 
              onClick={() => navigate(`/workspaces/${workspaceId}/work-mode/dashboard`)}
              size="lg"
            >
              <IconChevronLeft size={20} />
            </ActionIcon>
            <Box>
              <Title order={3}>{task.title}</Title>
              <Text color="dimmed">Task ID: {task.id}</Text>
            </Box>
          </Group>
          <Badge size="lg" color={getStatusColor(task.status)}>
            {getStatusLabel(task.status)}
          </Badge>
        </Group>
      </Paper>

      <Grid>
        {/* Task Details */}
        <Grid.Col span={{ base: 12, md: 8 }}>
          <Card withBorder p="md" mb="md" style={{ backgroundColor: '#2c2e33' }}>
            <Title order={4} mb="md" c="gray.3">Task Details</Title>
            
            <Grid>
              <Grid.Col span={6}>
                <Text fw={500} c="gray.4">Priority</Text>
                <Badge color={getStatusColor(task.priority)}>
                  {getPriorityLabel(task.priority)}
                </Badge>
              </Grid.Col>
              
              <Grid.Col span={6}>
                <Text fw={500} c="gray.4">Status</Text>
                <Badge color={getStatusColor(task.status)}>
                  {getStatusLabel(task.status)}
                </Badge>
              </Grid.Col>
              
              <Grid.Col span={6}>
                <Text fw={500} c="gray.4">Created</Text>
                <Text c="gray.5">{new Date(task.createdAt || '').toLocaleDateString()}</Text>
              </Grid.Col>
              
              <Grid.Col span={6}>
                <Text fw={500} c="gray.4">Last Updated</Text>
                <Text c="gray.5">{new Date(task.updatedAt || '').toLocaleDateString()}</Text>
              </Grid.Col>
              
              <Grid.Col span={12} mt="md">
                <Text fw={500} c="gray.4">Description</Text>
                <Text c="gray.5">{task.description}</Text>
              </Grid.Col>
            </Grid>
          </Card>
          
          {/* Comments Section */}
          <Card withBorder p="md" style={{ backgroundColor: '#2c2e33' }}>
            <Title order={4} mb="md" c="gray.3">Comments</Title>
            
            <Box mb="md">
              <Textarea
                placeholder="Add a comment..."
                minRows={3}
                value={comment}
                onChange={(e) => setComment(e.currentTarget.value)}
                styles={{ input: { backgroundColor: '#25262b' } }}
              />
              <Button mt="sm" onClick={handleAddComment} color="blue">
                Add Comment
              </Button>
            </Box>
            
            <Text ta="center" c="dimmed">No comments yet.</Text>
          </Card>
        </Grid.Col>
        
        {/* Task Actions Sidebar */}
        <Grid.Col span={{ base: 12, md: 4 }}>
          <Card withBorder p="md" mb="md" style={{ backgroundColor: '#2c2e33' }}>
            <Title order={5} mb="md" c="gray.3">Assigned To</Title>
            
            {assignedAgent ? (
              <Box>
                <Group mb="md">
                  <IconBrain size={20} />
                  <Box>
                    <Text fw={500} c="gray.3">{assignedAgent.name}</Text>
                    <Text size="sm" color="dimmed">
                      {assignedAgent.type.charAt(0).toUpperCase() + assignedAgent.type.slice(1)} Agent
                    </Text>
                  </Box>
                  <Badge color={getStatusColor(assignedAgent.status)}>
                    {getStatusLabel(assignedAgent.status)}
                  </Badge>
                </Group>
                <Button 
                  fullWidth 
                  variant="light"
                  onClick={() => navigate(`/workspaces/${workspaceId}/work-mode/agent/${assignedAgent.id}`)}
                  color="blue"
                >
                  View Agent
                </Button>
              </Box>
            ) : (
              <Box>
                <Text ta="center" c="dimmed" mb="md">No agent assigned</Text>
                <Button fullWidth color="blue">
                  Assign Agent
                </Button>
              </Box>
            )}
          </Card>
          
          <Card withBorder p="md" mb="md" style={{ backgroundColor: '#2c2e33' }}>
            <Title order={5} mb="md" c="gray.3">Change Status</Title>
            
            <Button 
              fullWidth 
              mb="sm"
              color={task.status === 'todo' ? 'blue' : 'gray'}
              variant={task.status === 'todo' ? 'filled' : 'light'}
              onClick={() => handleChangeStatus('todo')}
            >
              To Do
            </Button>
            
            <Button 
              fullWidth 
              mb="sm"
              color={task.status === 'in-progress' ? 'blue' : 'gray'}
              variant={task.status === 'in-progress' ? 'filled' : 'light'}
              onClick={() => handleChangeStatus('in-progress')}
            >
              In Progress
            </Button>
            
            <Button 
              fullWidth 
              mb="sm"
              color={task.status === 'review' ? 'yellow' : 'gray'}
              variant={task.status === 'review' ? 'filled' : 'light'}
              onClick={() => handleChangeStatus('review')}
            >
              Review
            </Button>
            
            <Button 
              fullWidth 
              color={task.status === 'done' ? 'green' : 'gray'}
              variant={task.status === 'done' ? 'filled' : 'light'}
              onClick={() => handleChangeStatus('done')}
            >
              Done
            </Button>
          </Card>
          
          <Card withBorder p="md" style={{ backgroundColor: '#2c2e33' }}>
            <Title order={5} mb="md" c="gray.3">Actions</Title>
            
            <Button 
              fullWidth 
              leftSection={<IconSettings size={16} />} 
              variant="light"
              mb="sm"
              color="blue"
            >
              Edit Task
            </Button>
            
            <Button 
              fullWidth 
              color="red"
              variant="light"
            >
              Delete Task
            </Button>
          </Card>
        </Grid.Col>
      </Grid>
    </Box>
  );
} 