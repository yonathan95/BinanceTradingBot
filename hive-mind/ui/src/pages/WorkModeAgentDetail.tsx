import { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { Box, Paper, Title, Text, Card, Group, Badge, Button, Grid, Timeline, ActionIcon } from '@mantine/core';
import { IconBrain, IconChevronLeft, IconSettings, IconClipboardList, IconUser } from '../components/layout/icons';

interface Agent {
  id: string;
  name: string;
  status: 'idle' | 'working' | 'error';
  type: string;
  taskCount: number;
  workspaceId: string;
  model?: string;
  temperature?: number;
  tokenLimit?: number;
  role?: string;
  description?: string;
  createdAt?: string;
}

interface Task {
  id: string;
  title: string;
  status: 'todo' | 'in-progress' | 'review' | 'done';
  assignedAgent?: string;
  priority: 'low' | 'medium' | 'high';
  workspaceId: string;
}

export default function WorkModeAgentDetail() {
  const { workspaceId, agentId } = useParams<{ workspaceId: string, agentId: string }>();
  const navigate = useNavigate();
  
  const [agent, setAgent] = useState<Agent | null>(null);
  const [assignedTasks, setAssignedTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!workspaceId || !agentId) {
      console.error('Missing workspaceId or agentId');
      return;
    }

    // Load agent data
    fetch(`/mock-api/api/workspace-${workspaceId}-agents.json`)
      .then(response => response.json())
      .catch(error => {
        console.error('Error fetching agent data:', error);
        return [];
      })
      .then(agents => {
        const foundAgent = agents.find((a: Agent) => a.id === agentId);
        
        if (foundAgent) {
          // Add some additional mock details for the agent
          foundAgent.model = foundAgent.model || 'gpt-4o';
          foundAgent.temperature = foundAgent.temperature || 0.7;
          foundAgent.tokenLimit = foundAgent.tokenLimit || 8000;
          foundAgent.role = foundAgent.role || 'Assistant';
          foundAgent.description = foundAgent.description || 
            `This ${foundAgent.type} agent helps with ${foundAgent.type}-related tasks in the workspace.`;
          foundAgent.createdAt = foundAgent.createdAt || '2025-01-15T10:00:00Z';
          
          setAgent(foundAgent);
        }
        
        // Fetch tasks to find ones assigned to this agent
        return fetch(`/mock-api/api/workspace-${workspaceId}-tasks.json`);
      })
      .then(response => response.json())
      .catch(error => {
        console.error('Error fetching task data:', error);
        return [];
      })
      .then(tasks => {
        const agentTasks = tasks.filter((task: Task) => task.assignedAgent === agentId);
        setAssignedTasks(agentTasks);
        setLoading(false);
      })
      .catch(error => {
        console.error('Error in data loading chain:', error);
        setLoading(false);
      });
  }, [workspaceId, agentId]);

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

  if (loading) {
    return <Box p="xl">Loading agent details...</Box>;
  }

  if (!agent) {
    return (
      <Box p="xl">
        <Text>Agent not found. The requested agent may not exist or has been removed.</Text>
        <Button 
          mt="md" 
          component={Link} 
          to={`/workspaces/${workspaceId}/work-mode/dashboard`}
          leftSection={<IconChevronLeft size={16} />}
        >
          Back to Dashboard
        </Button>
      </Box>
    );
  }

  return (
    <Box p="md">
      {/* Header */}
      <Paper p="md" mb="md" withBorder>
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
              <Title order={3}>{agent.name}</Title>
              <Text color="dimmed">{agent.type.charAt(0).toUpperCase() + agent.type.slice(1)} Agent</Text>
            </Box>
          </Group>
          <Badge size="lg" color={getStatusColor(agent.status)}>
            {getStatusLabel(agent.status)}
          </Badge>
        </Group>
      </Paper>

      <Grid>
        {/* Agent Details */}
        <Grid.Col span={{ base: 12, md: 8 }}>
          <Card withBorder p="md" mb="md">
            <Title order={4} mb="md">Agent Details</Title>
            
            <Grid>
              <Grid.Col span={6}>
                <Text fw={500}>Type</Text>
                <Text>{agent.type.charAt(0).toUpperCase() + agent.type.slice(1)}</Text>
              </Grid.Col>
              
              <Grid.Col span={6}>
                <Text fw={500}>Model</Text>
                <Text>{agent.model}</Text>
              </Grid.Col>
              
              <Grid.Col span={6}>
                <Text fw={500}>Temperature</Text>
                <Text>{agent.temperature}</Text>
              </Grid.Col>
              
              <Grid.Col span={6}>
                <Text fw={500}>Token Limit</Text>
                <Text>{agent.tokenLimit?.toLocaleString()}</Text>
              </Grid.Col>
              
              <Grid.Col span={12} mt="md">
                <Text fw={500}>Description</Text>
                <Text>{agent.description}</Text>
              </Grid.Col>
            </Grid>
          </Card>
          
          {/* Assigned Tasks */}
          <Card withBorder p="md">
            <Group justify="space-between" mb="md">
              <Title order={4}>Assigned Tasks</Title>
              <Badge>{assignedTasks.length} tasks</Badge>
            </Group>
            
            {assignedTasks.length > 0 ? (
              <Timeline active={1} bulletSize={24} lineWidth={2}>
                {assignedTasks.map((task, index) => (
                  <Timeline.Item 
                    key={task.id}
                    bullet={<IconClipboardList size={16} />}
                    title={
                      <Group gap="xs">
                        <Text fw={500}>{task.title}</Text>
                        <Badge size="sm" color={getStatusColor(task.status)}>
                          {getStatusLabel(task.status)}
                        </Badge>
                      </Group>
                    }
                  >
                    <Group justify="space-between" my="xs">
                      <Badge color={getStatusColor(task.priority)} size="sm">
                        {getPriorityLabel(task.priority)}
                      </Badge>
                      <Button 
                        variant="light" 
                        size="xs"
                        onClick={() => navigate(`/workspaces/${workspaceId}/work-mode/task/${task.id}`)}
                      >
                        View Task
                      </Button>
                    </Group>
                  </Timeline.Item>
                ))}
              </Timeline>
            ) : (
              <Text ta="center" c="dimmed">No tasks currently assigned to this agent.</Text>
            )}
          </Card>
        </Grid.Col>
        
        {/* Actions Sidebar */}
        <Grid.Col span={{ base: 12, md: 4 }}>
          <Card withBorder p="md" mb="md">
            <Title order={5} mb="md">Actions</Title>
            
            <Button 
              fullWidth 
              leftSection={<IconChevronLeft size={16} />} 
              mb="sm"
              disabled={agent.status === 'working'}
            >
              Restart Agent
            </Button>
            
            <Button 
              fullWidth 
              leftSection={<IconUser size={16} />} 
              variant="light" 
              mb="sm"
            >
              View Logs
            </Button>
            
            <Button 
              fullWidth 
              leftSection={<IconSettings size={16} />} 
              variant="light"
            >
              Configure
            </Button>
          </Card>
          
          <Card withBorder p="md">
            <Title order={5} mb="md">Agent Stats</Title>
            
            <Text fw={500} size="sm">Created</Text>
            <Text mb="md" size="sm">
              {new Date(agent.createdAt || '').toLocaleDateString()}
            </Text>
            
            <Text fw={500} size="sm">Tasks Completed</Text>
            <Text mb="md" size="sm">
              {Math.floor(Math.random() * 20)} tasks
            </Text>
            
            <Text fw={500} size="sm">Tokens Used</Text>
            <Text mb="md" size="sm">
              {Math.floor(Math.random() * 100000).toLocaleString()} tokens
            </Text>
          </Card>
        </Grid.Col>
      </Grid>
    </Box>
  );
} 