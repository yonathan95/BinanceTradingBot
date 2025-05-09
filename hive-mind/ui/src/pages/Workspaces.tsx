import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  Box, 
  Title, 
  Text, 
  Card, 
  Group, 
  Button, 
  Grid, 
  Badge, 
  Loader, 
  ActionIcon,
  Flex,
  Paper,
  Modal,
  TextInput,
  Textarea
} from '@mantine/core';
import axios from 'axios';

interface Workspace {
  id: string;
  name: string;
  description: string;
  projects: number;
  created_at: string;
  updated_at: string;
  owner: string;
}

// Fallback mock data in case the API fails
const mockWorkspaces: Workspace[] = [
  {
    "id": "ws-001",
    "name": "Frontend Development",
    "description": "Workspace for all frontend related projects",
    "projects": 5,
    "created_at": "2023-06-15T10:30:00Z",
    "updated_at": "2023-10-22T14:45:00Z",
    "owner": "John Doe"
  },
  {
    "id": "ws-002",
    "name": "Backend Systems",
    "description": "API and database infrastructure projects",
    "projects": 3,
    "created_at": "2023-07-10T09:15:00Z",
    "updated_at": "2023-10-18T11:20:00Z",
    "owner": "Jane Smith"
  },
  {
    "id": "ws-003",
    "name": "Mobile Applications",
    "description": "iOS and Android app development",
    "projects": 2,
    "created_at": "2023-08-05T13:45:00Z",
    "updated_at": "2023-10-20T16:30:00Z",
    "owner": "Alex Johnson"
  }
];

export default function Workspaces() {
  const [workspaces, setWorkspaces] = useState<Workspace[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [createModalOpen, setCreateModalOpen] = useState(false);
  const [newWorkspaceName, setNewWorkspaceName] = useState('');
  const [newWorkspaceDesc, setNewWorkspaceDesc] = useState('');
  
  const navigate = useNavigate();

  useEffect(() => {
    const fetchWorkspaces = async () => {
      try {
        setLoading(true);
        // Try multiple paths to find the mock data
        try {
          const response = await axios.get('/mock-api/api/workspaces.json');
          setWorkspaces(response.data);
        } catch (innerErr) {
          // Try another common path
          try {
            const response = await axios.get('/public/mock-api/api/workspaces.json');
            setWorkspaces(response.data);
          } catch (anotherErr) {
            // Use the hardcoded fallback data
            console.log('Using fallback mock workspaces data');
            setWorkspaces(mockWorkspaces);
          }
        }
        setError('');
      } catch (err) {
        console.error('Error fetching workspaces:', err);
        // Use the hardcoded fallback data
        console.log('Using fallback mock workspaces data after error');
        setWorkspaces(mockWorkspaces);
        setError(''); // Clear error since we're using fallback data
      } finally {
        setLoading(false);
      }
    };

    fetchWorkspaces();
  }, []);

  const handleCreateWorkspace = () => {
    // In a real implementation, this would make an API call
    const newWorkspace = {
      id: `ws-${Math.floor(Math.random() * 1000)}`,
      name: newWorkspaceName,
      description: newWorkspaceDesc,
      projects: 0,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      owner: 'Current User'
    };

    setWorkspaces([...workspaces, newWorkspace]);
    setCreateModalOpen(false);
    setNewWorkspaceName('');
    setNewWorkspaceDesc('');
  };

  return (
    <Box p="md">
      <Flex justify="space-between" align="center" mb="xl">
        <Title>Workspaces</Title>
        <Button onClick={() => setCreateModalOpen(true)}>Create Workspace</Button>
      </Flex>

      {loading ? (
        <Flex justify="center" align="center" style={{ height: '200px' }}>
          <Loader size="lg" />
        </Flex>
      ) : error ? (
        <Paper p="xl" withBorder radius="md" style={{ backgroundColor: '#FEF2F2' }}>
          <Text c="red">{error}</Text>
        </Paper>
      ) : workspaces.length === 0 ? (
        <Paper p="xl" withBorder radius="md" ta="center">
          <Text size="lg" fw={500} mb="md">No workspaces found</Text>
          <Text mb="lg">Get started by creating your first workspace</Text>
          <Button onClick={() => setCreateModalOpen(true)}>Create Workspace</Button>
        </Paper>
      ) : (
        <Grid>
          {workspaces.map((workspace) => (
            <Grid.Col span={{ base: 12, md: 6, lg: 4 }} key={workspace.id}>
              <Card withBorder shadow="sm" radius="md" padding="lg">
                <Card.Section withBorder inheritPadding py="xs">
                  <Title order={3}>{workspace.name}</Title>
                </Card.Section>
                
                <Text mt="md" mb="md" c="dimmed" lineClamp={2}>
                  {workspace.description}
                </Text>
                
                <Group mt="md" mb="md">
                  <Badge color="blue">{workspace.projects} Projects</Badge>
                  <Badge color="gray">Updated: {new Date(workspace.updated_at).toLocaleDateString()}</Badge>
                </Group>
                
                <Text size="sm" c="dimmed">
                  Owner: {workspace.owner}
                </Text>
                
                <Button 
                  fullWidth 
                  mt="md" 
                  onClick={() => navigate(`/workspaces/${workspace.id}`)}
                >
                  Open Workspace
                </Button>
              </Card>
            </Grid.Col>
          ))}
        </Grid>
      )}

      <Modal
        opened={createModalOpen}
        onClose={() => setCreateModalOpen(false)}
        title="Create New Workspace"
        size="md"
      >
        <Box>
          <TextInput
            label="Workspace Name"
            placeholder="Enter workspace name"
            value={newWorkspaceName}
            onChange={(e) => setNewWorkspaceName(e.target.value)}
            required
            mb="md"
          />
          
          <Textarea
            label="Description"
            placeholder="Describe the purpose of this workspace"
            value={newWorkspaceDesc}
            onChange={(e) => setNewWorkspaceDesc(e.target.value)}
            minRows={3}
            mb="xl"
          />
          
          <Group justify="flex-end">
            <Button variant="outline" onClick={() => setCreateModalOpen(false)}>Cancel</Button>
            <Button 
              onClick={handleCreateWorkspace}
              disabled={!newWorkspaceName.trim()}
            >
              Create
            </Button>
          </Group>
        </Box>
      </Modal>
    </Box>
  );
} 