import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Box, Card, Title, Text, Paper, Group, Table, Badge, Button } from '@mantine/core';
import { IconBrain } from '../components/layout/icons';

interface Task {
  id: string;
  title: string;
  status: 'todo' | 'in-progress' | 'review' | 'done';
  assignee?: string;
  priority: 'low' | 'medium' | 'high';
}

interface Project {
  id: string;
  name: string;
  description: string;
  tasks?: Task[];
}

export default function ProjectWorkmode() {
  const { projectId } = useParams<{ projectId?: string }>();
  const [project, setProject] = useState<Project | null>(null);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    // Default project ID if none provided
    const id = projectId || 'proj-1';
    
    // Fetch project data
    fetch(`/mock-api/api/project-${id}.json`)
      .then(response => {
        if (!response.ok) {
          throw new Error('Project data not found');
        }
        return response.json();
      })
      .then(data => {
        setProject(data);
        
        // Use tasks from project data if available
        if (data && data.tasks) {
          setTasks(data.tasks);
        } else {
          // Fallback mock tasks data
          const mockTasks: Task[] = [
            { id: 'task-1', title: 'Implement authentication flow', status: 'todo', priority: 'high' },
            { id: 'task-2', title: 'Fix responsive layout issues', status: 'in-progress', assignee: 'Developer 1', priority: 'medium' },
            { id: 'task-3', title: 'Add unit tests for API', status: 'todo', priority: 'medium' },
            { id: 'task-4', title: 'Update documentation', status: 'review', assignee: 'Developer 2', priority: 'low' },
            { id: 'task-5', title: 'Optimize database queries', status: 'done', assignee: 'Developer 3', priority: 'high' },
          ];
          setTasks(mockTasks);
        }
        
        setLoading(false);
      })
      .catch(error => {
        console.error('Error fetching project data:', error);
        
        // Set fallback data on error
        const mockProject = {
          id: id,
          name: `Project ${id}`,
          description: 'Customer-facing web application'
        };
        
        setProject(mockProject);
        
        // Fallback mock tasks data
        const mockTasks: Task[] = [
          { id: 'task-1', title: 'Implement authentication flow', status: 'todo', priority: 'high' },
          { id: 'task-2', title: 'Fix responsive layout issues', status: 'in-progress', assignee: 'Developer 1', priority: 'medium' },
          { id: 'task-3', title: 'Add unit tests for API', status: 'todo', priority: 'medium' },
          { id: 'task-4', title: 'Update documentation', status: 'review', assignee: 'Developer 2', priority: 'low' },
          { id: 'task-5', title: 'Optimize database queries', status: 'done', assignee: 'Developer 3', priority: 'high' },
        ];
        
        setTasks(mockTasks);
        setLoading(false);
      });
  }, [projectId]);

  // Function to render status badge
  const renderStatus = (status: string) => {
    const statusConfig = {
      todo: { color: 'gray', label: 'To Do' },
      'in-progress': { color: 'blue', label: 'In Progress' },
      review: { color: 'yellow', label: 'Review' },
      done: { color: 'green', label: 'Done' }
    };
    
    const config = statusConfig[status as keyof typeof statusConfig];
    
    return (
      <Badge color={config.color} size="sm">
        {config.label}
      </Badge>
    );
  };
  
  // Function to render priority
  const renderPriority = (priority: string) => {
    const priorityConfig = {
      high: { color: 'red', label: 'High' },
      medium: { color: 'yellow', label: 'Medium' },
      low: { color: 'green', label: 'Low' }
    };
    
    const config = priorityConfig[priority as keyof typeof priorityConfig];
    
    return (
      <Group gap="xs">
        <Box w={8} h={8} style={{ borderRadius: '50%', backgroundColor: `var(--mantine-color-${config.color}-filled)` }}></Box>
        <Text size="sm">{config.label}</Text>
      </Group>
    );
  };

  const openWorkModeUI = () => {
    navigate('/work-mode/dashboard');
  };

  const openTaskDetail = (taskId: string) => {
    navigate(`/work-mode/task/${taskId}`);
  };

  if (loading) {
    return <Box p="xl">Loading project data...</Box>;
  }

  if (!project) {
    return <Box p="xl">Project not found</Box>;
  }

  return (
    <Box p="md">
      {/* Header */}
      <Paper p="md" mb="md" withBorder>
        <Group justify="space-between">
          <Box>
            <Group gap="xs">
              <IconBrain size={24} />
              <Title order={3}>{project.name}</Title>
            </Group>
            <Text color="dimmed">Project Workmode</Text>
          </Box>
          <Button 
            variant="filled" 
            color="blue" 
            onClick={openWorkModeUI}
          >
            Open Full Work Mode
          </Button>
        </Group>
      </Paper>

      {/* Content */}
      <Card withBorder p="md" mb="md">
        <Title order={4} mb="md">Tasks</Title>
        
        {tasks.length === 0 ? (
          <Text>No tasks found in this project.</Text>
        ) : (
          <Table>
            <Table.Thead>
              <Table.Tr>
                <Table.Th>Title</Table.Th>
                <Table.Th>Status</Table.Th>
                <Table.Th>Assignee</Table.Th>
                <Table.Th>Priority</Table.Th>
                <Table.Th>Actions</Table.Th>
              </Table.Tr>
            </Table.Thead>
            <Table.Tbody>
              {tasks.map(task => (
                <Table.Tr key={task.id}>
                  <Table.Td>{task.title}</Table.Td>
                  <Table.Td>{renderStatus(task.status)}</Table.Td>
                  <Table.Td>{task.assignee || 'Unassigned'}</Table.Td>
                  <Table.Td>{renderPriority(task.priority)}</Table.Td>
                  <Table.Td>
                    <Button 
                      variant="light" 
                      size="xs" 
                      onClick={() => openTaskDetail(task.id)}
                    >
                      View Details
                    </Button>
                  </Table.Td>
                </Table.Tr>
              ))}
            </Table.Tbody>
          </Table>
        )}
      </Card>
    </Box>
  );
} 