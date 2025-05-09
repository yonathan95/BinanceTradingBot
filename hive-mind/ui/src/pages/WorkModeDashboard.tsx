import { useEffect, useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { Box, Card, Title, Text, Paper, Grid, Badge, Group, Button } from '@mantine/core';
import { IconBrain, IconClipboardList } from '../components/layout/icons';

interface Agent {
  id: string;
  name: string;
  status: 'idle' | 'working' | 'error';
  type: string;
  taskCount: number;
}

interface Task {
  id: string;
  title: string;
  status: 'todo' | 'in-progress' | 'review' | 'done';
  assignedAgent?: string;
  priority: 'low' | 'medium' | 'high';
}

interface Workspace {
  id: string;
  name: string;
  description: string;
}

export default function WorkModeDashboard() {
  const { workspaceId } = useParams<{ workspaceId: string }>();
  const [workspace, setWorkspace] = useState<Workspace>({ id: '', name: '', description: '' });
  const [agents, setAgents] = useState<Agent[]>([]);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    if (!workspaceId) {
      console.error('No workspace ID provided');
      return;
    }

    // Load workspace details first
    const workspaceUrl = `/mock-api/api/workspace-${workspaceId}.json`;
    
    fetch(workspaceUrl)
      .then(response => response.json())
      .catch(() => {
        // Fallback workspace data
        return {
          id: workspaceId,
          name: `Workspace ${workspaceId}`,
          description: 'Enhanced workspace for AI agents collaboration'
        };
      })
      .then(data => {
        setWorkspace(data);
        
        // Now load workspace-specific agents and tasks
        return Promise.all([
          // Try to fetch workspace-specific agents
          fetch(`/mock-api/api/workspace-${workspaceId}-agents.json`)
            .then(response => response.json())
            .catch(() => {
              // Fallback mock data
              return [
                { id: 'agent-1', name: 'Coder Agent', status: 'idle', type: 'coder', taskCount: 2, workspaceId },
                { id: 'agent-2', name: 'Tester Agent', status: 'working', type: 'tester', taskCount: 1, workspaceId },
                { id: 'agent-3', name: 'Planner Agent', status: 'idle', type: 'planner', taskCount: 0, workspaceId },
                { id: 'agent-4', name: 'Manager Agent', status: 'error', type: 'manager', taskCount: 3, workspaceId },
              ];
            }),
          // Try to fetch workspace-specific tasks
          fetch(`/mock-api/api/workspace-${workspaceId}-tasks.json`)
            .then(response => response.json())
            .catch(() => {
              // Fallback mock data
              return [
                { id: 'task-1', title: 'Implement authentication flow', status: 'todo', priority: 'high', workspaceId },
                { id: 'task-2', title: 'Fix responsive layout issues', status: 'in-progress', assignedAgent: 'agent-1', priority: 'medium', workspaceId },
                { id: 'task-3', title: 'Add unit tests for API', status: 'todo', priority: 'medium', workspaceId },
                { id: 'task-4', title: 'Update documentation', status: 'review', assignedAgent: 'agent-3', priority: 'low', workspaceId },
                { id: 'task-5', title: 'Optimize database queries', status: 'done', assignedAgent: 'agent-2', priority: 'high', workspaceId },
              ];
            })
        ]);
      })
      .then(([agentData, taskData]) => {
        setAgents(agentData);
        setTasks(taskData);
        setLoading(false);
      })
      .catch(error => {
        console.error('Error loading work mode data:', error);
        setLoading(false);
      });
  }, [workspaceId]);

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

  const getStatusLabel = (status: string) => {
    switch (status) {
      case 'in-progress': return 'In Progress';
      default: return status.charAt(0).toUpperCase() + status.slice(1);
    }
  };

  if (loading) {
    return <Box p="xl">Loading enhanced work mode data...</Box>;
  }

  if (!workspace.id) {
    return <Box p="xl">Workspace not found. Please select a valid workspace.</Box>;
  }

  return (
    <Box p="md">
      {/* Header */}
      <Paper p="md" mb="md" withBorder>
        <Group justify="space-between">
          <Box>
            <Title order={3}>{workspace.name} - Enhanced Work Mode</Title>
            <Text color="dimmed">Manage your workspace agents and tasks</Text>
          </Box>
          <Button 
            component={Link} 
            to={`/workspaces/${workspaceId}/work-mode/tasks/new`}
            variant="filled" 
            color="blue"
          >
            Create New Task
          </Button>
        </Group>
      </Paper>

      {/* Agents Section */}
      <Card withBorder p="md" mb="md">
        <Group justify="space-between" mb="md">
          <Title order={4}>Workspace Agents</Title>
        </Group>
        
        <Grid>
          {agents.length > 0 ? (
            agents.map(agent => (
              <Grid.Col key={agent.id} span={{ base: 12, sm: 6, md: 3 }}>
                <Card 
                  withBorder 
                  p="md" 
                  radius="md" 
                  style={{ cursor: 'pointer' }}
                  onClick={() => navigate(`/workspaces/${workspaceId}/work-mode/agent/${agent.id}`)}
                >
                  <Group justify="space-between" mb="xs">
                    <Group gap="xs">
                      <IconBrain size={20} />
                      <Text fw={500}>{agent.name}</Text>
                    </Group>
                    <Badge color={getStatusColor(agent.status)}>
                      {getStatusLabel(agent.status)}
                    </Badge>
                  </Group>
                  <Text size="sm" color="dimmed" mb="md">Type: {agent.type}</Text>
                  <Text size="sm">Assigned Tasks: {agent.taskCount}</Text>
                </Card>
              </Grid.Col>
            ))
          ) : (
            <Grid.Col span={12}>
              <Text ta="center" c="dimmed">No agents configured for this workspace yet.</Text>
            </Grid.Col>
          )}
        </Grid>
      </Card>

      {/* Tasks Section */}
      <Card withBorder p="md">
        <Group justify="space-between" mb="md">
          <Title order={4}>Workspace Tasks</Title>
          <Button 
            component={Link} 
            to={`/workspaces/${workspaceId}/work-mode/tasks`}
            variant="light" 
            color="blue"
          >
            View All Tasks
          </Button>
        </Group>
        
        <Grid>
          {tasks.length > 0 ? (
            tasks.slice(0, 4).map(task => (
              <Grid.Col key={task.id} span={{ base: 12, sm: 6 }}>
                <Card 
                  withBorder 
                  p="md" 
                  radius="md"
                  style={{ cursor: 'pointer' }}
                  onClick={() => navigate(`/workspaces/${workspaceId}/work-mode/task/${task.id}`)}
                >
                  <Group justify="space-between" mb="xs">
                    <Group gap="xs">
                      <IconClipboardList size={20} />
                      <Text fw={500}>{task.title}</Text>
                    </Group>
                    <Badge color={getStatusColor(task.status)}>
                      {getStatusLabel(task.status)}
                    </Badge>
                  </Group>
                  <Group justify="space-between">
                    <Text size="sm" color="dimmed">
                      {task.assignedAgent ? 
                        `Assigned to: ${agents.find(a => a.id === task.assignedAgent)?.name || 'Unknown Agent'}` : 
                        'Unassigned'
                      }
                    </Text>
                    <Badge color={getStatusColor(task.priority)} size="sm">
                      {task.priority.charAt(0).toUpperCase() + task.priority.slice(1)}
                    </Badge>
                  </Group>
                </Card>
              </Grid.Col>
            ))
          ) : (
            <Grid.Col span={12}>
              <Text ta="center" c="dimmed">No tasks created for this workspace yet.</Text>
            </Grid.Col>
          )}
        </Grid>
      </Card>
    </Box>
  );
} 