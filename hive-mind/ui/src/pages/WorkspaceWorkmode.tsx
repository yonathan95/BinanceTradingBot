import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Box, Card, Title, Text, Paper, Grid, Button, Group } from '@mantine/core';
import { IconFolders, IconBrain } from '../components/layout/icons';

interface Project {
  id: string;
  name: string;
  description: string;
}

export default function WorkspaceWorkmode() {
  const { workspaceId } = useParams<{ workspaceId?: string }>();
  const [workspace, setWorkspace] = useState({ id: '', name: '', description: '' });
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    if (!workspaceId) {
      setLoading(false);
      return;
    }

    // Fetch workspace data for the specific workspace ID
    const apiUrl = `/mock-api/api/workspace-${workspaceId}.json`;
      
    fetch(apiUrl)
      .then(response => response.json())
      .catch(error => {
        console.error('Error fetching workspace data:', error);
        // Fallback mock data
        return {
          id: workspaceId,
          name: `Workspace ${workspaceId}`,
          description: 'Workspace description',
          projects: [
            { id: 'proj-1', name: 'Frontend Application', description: 'Customer-facing web application' },
            { id: 'proj-2', name: 'Backend API', description: 'RESTful API services' },
            { id: 'proj-3', name: 'Database Layer', description: 'Data persistence and access' },
            { id: 'proj-4', name: 'DevOps Pipeline', description: 'CI/CD automation' },
          ]
        };
      })
      .then(data => {
        setWorkspace(data);
        
        // Use projects from the workspace data if available
        if (data && data.projects) {
          setProjects(data.projects);
        }
        
        setLoading(false);
      });
  }, [workspaceId]);

  const handleProjectClick = (projectId: string) => {
    // Navigate to project workmode with workspace context
    navigate(`/workspaces/${workspaceId}/work-mode/projects/${projectId}`);
  };

  const openEnhancedWorkMode = () => {
    // Navigate to the enhanced Work Mode UI with workspace context
    navigate(`/workspaces/${workspaceId}/work-mode/dashboard`);
  };

  if (loading) {
    return <Box p="xl">Loading workspace data...</Box>;
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
            <Title order={3}>{workspace.name}</Title>
            <Text color="dimmed">Workspace Work Mode</Text>
          </Box>
          <Button 
            variant="filled" 
            color="blue"
            leftSection={<IconBrain size={20} />}
            onClick={openEnhancedWorkMode}
          >
            Enhanced Work Mode
          </Button>
        </Group>
      </Paper>

      {/* Content */}
      <Card withBorder p="md" mb="md">
        <Title order={4} mb="md">Projects in {workspace.name}</Title>
        
        <Grid>
          {projects.length > 0 ? (
            projects.map(project => (
              <Grid.Col key={project.id} span={{ base: 12, sm: 6, md: 4 }}>
                <Card withBorder p="md" radius="md">
                  <Group justify="space-between" mb="xs">
                    <Text fw={500}>{project.name}</Text>
                    <IconFolders size={20} />
                  </Group>
                  <Text size="sm" color="dimmed" mb="md">{project.description}</Text>
                  <Button 
                    onClick={() => handleProjectClick(project.id)}
                    variant="light" 
                    color="blue" 
                    fullWidth
                  >
                    Open Project Work Mode
                  </Button>
                </Card>
              </Grid.Col>
            ))
          ) : (
            <Grid.Col span={12}>
              <Text ta="center" c="dimmed">No projects found in this workspace.</Text>
            </Grid.Col>
          )}
        </Grid>
      </Card>
    </Box>
  );
} 