import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
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
  Tabs, 
  AppShell, 
  ScrollArea,
  Paper,
  Divider,
  Avatar,
  ActionIcon,
  Modal,
  TextInput,
  Textarea,
  Select,
  MultiSelect,
  Flex
} from '@mantine/core';
import { 
  IconFileText, 
  IconUsers, 
  IconSettings, 
  IconChartBar, 
  IconPlus,
  IconDotsVertical,
  IconFolder,
  IconChevronLeft,
  IconChevronRight,
  IconClipboardList,
  IconBrain
} from '../components/layout/icons';
import axios from 'axios';
import WorkspaceTaskBoard from '../components/tasks/WorkspaceTaskBoard';

interface Member {
  id: string;
  name: string;
  role: string;
  email: string;
  type?: 'human' | 'agent';
}

interface AgentMember extends Member {
  type: 'agent';
  agentClass: string;
  model: string;
  temperature: number;
  tokenLimit: number;
  customInstructions?: string;
  tier: 'economy' | 'standard' | 'premium';
  tools: string[];
}

interface Project {
  id: string;
  name: string;
  description: string;
  status: string;
  created_at: string;
  updated_at: string;
}

interface Workspace {
  id: string;
  name: string;
  description: string;
  created_at: string;
  updated_at: string;
  owner: string;
  members: Member[];
  agents?: AgentMember[];
  projects: Project[];
}

// Add fallback mock data for workspace details
const getMockWorkspaceById = (workspaceId: string) => {
  if (workspaceId === 'ws-001') {
    return {
      "id": "ws-001",
      "name": "Frontend Development",
      "description": "Workspace for all frontend related projects",
      "created_at": "2023-06-15T10:30:00Z",
      "updated_at": "2023-10-22T14:45:00Z",
      "owner": "John Doe",
      "members": [
        {
          "id": "usr-001",
          "name": "John Doe",
          "role": "Owner",
          "email": "john.doe@example.com"
        },
        {
          "id": "usr-002",
          "name": "Jane Smith",
          "role": "Developer",
          "email": "jane.smith@example.com"
        }
      ],
      "projects": [
        {
          "id": "prj-001",
          "name": "Company Website",
          "description": "Corporate website redesign",
          "status": "In Progress",
          "created_at": "2023-07-10T09:30:00Z",
          "updated_at": "2023-10-20T11:15:00Z"
        },
        {
          "id": "prj-002",
          "name": "Customer Portal",
          "description": "Self-service portal for customers",
          "status": "Planning",
          "created_at": "2023-08-15T13:45:00Z",
          "updated_at": "2023-10-18T16:30:00Z"
        }
      ]
    };
  } else if (workspaceId === 'ws-002') {
    return {
      "id": "ws-002",
      "name": "Backend Systems",
      "description": "API and database infrastructure projects",
      "created_at": "2023-07-10T09:15:00Z",
      "updated_at": "2023-10-18T11:20:00Z",
      "owner": "Jane Smith",
      "members": [
        {
          "id": "usr-002",
          "name": "Jane Smith",
          "role": "Owner",
          "email": "jane.smith@example.com"
        },
        {
          "id": "usr-003",
          "name": "Alex Johnson",
          "role": "Developer",
          "email": "alex.johnson@example.com"
        }
      ],
      "projects": [
        {
          "id": "prj-003",
          "name": "API Gateway",
          "description": "Central API management service",
          "status": "In Progress",
          "created_at": "2023-07-15T10:30:00Z",
          "updated_at": "2023-10-15T11:15:00Z"
        }
      ]
    };
  } else if (workspaceId === 'ws-003') {
    return {
      "id": "ws-003",
      "name": "Mobile Applications",
      "description": "iOS and Android app development",
      "created_at": "2023-08-05T13:45:00Z",
      "updated_at": "2023-10-20T16:30:00Z",
      "owner": "Alex Johnson",
      "members": [
        {
          "id": "usr-003",
          "name": "Alex Johnson",
          "role": "Owner",
          "email": "alex.johnson@example.com"
        },
        {
          "id": "usr-004",
          "name": "Sarah Wilson",
          "role": "Developer",
          "email": "sarah.wilson@example.com"
        }
      ],
      "projects": [
        {
          "id": "prj-006",
          "name": "iOS Shopping App",
          "description": "Native iOS application for e-commerce",
          "status": "In Progress",
          "created_at": "2023-08-10T10:30:00Z",
          "updated_at": "2023-10-19T14:45:00Z"
        }
      ]
    };
  }
  
  // Default workspace if ID doesn't match
  return {
    "id": workspaceId || "ws-default",
    "name": "Demo Workspace",
    "description": "A default workspace for demonstration",
    "created_at": new Date().toISOString(),
    "updated_at": new Date().toISOString(),
    "owner": "Demo User",
    "members": [
      {
        "id": "usr-001",
        "name": "Demo User",
        "role": "Owner",
        "email": "demo@example.com"
      }
    ],
    "projects": [
      {
        "id": "prj-default",
        "name": "Demo Project",
        "description": "A sample project for demonstration",
        "status": "Planning",
        "created_at": new Date().toISOString(),
        "updated_at": new Date().toISOString()
      }
    ]
  };
};

export default function WorkspaceDetail() {
  const { workspaceId } = useParams<{ workspaceId: string }>();
  const navigate = useNavigate();

  const [workspace, setWorkspace] = useState<Workspace | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [activeSection, setActiveSection] = useState<string>('projects');
  const [createProjectModal, setCreateProjectModal] = useState(false);
  const [newProjectName, setNewProjectName] = useState('');
  const [newProjectDesc, setNewProjectDesc] = useState('');
  const [newProjectStatus, setNewProjectStatus] = useState('Planning');
  
  // Add state for sidebar minimization
  const [sidebarMinimized, setSidebarMinimized] = useState(false);
  
  // New states for member management
  const [createMemberModal, setCreateMemberModal] = useState(false);
  const [newMemberName, setNewMemberName] = useState('');
  const [newMemberEmail, setNewMemberEmail] = useState('');
  const [newMemberRole, setNewMemberRole] = useState('Member');
  
  // New states for agent management
  const [createAgentModal, setCreateAgentModal] = useState(false);
  const [newAgentName, setNewAgentName] = useState('');
  const [newAgentClass, setNewAgentClass] = useState('');
  const [newAgentModel, setNewAgentModel] = useState('gpt-4o');
  const [newAgentTemperature, setNewAgentTemperature] = useState(0.7);
  const [newAgentTokenLimit, setNewAgentTokenLimit] = useState(4096);
  const [newAgentTier, setNewAgentTier] = useState<'economy' | 'standard' | 'premium'>('standard');
  const [newAgentTools, setNewAgentTools] = useState<string[]>([]);
  const [newAgentInstructions, setNewAgentInstructions] = useState('');
  
  // Settings state
  const [budgetLimit, setBudgetLimit] = useState(1000);
  const [costPerToken, setCostPerToken] = useState(0.002);
  const [rateLimit, setRateLimit] = useState(60);
  const [rateLimitPeriod, setRateLimitPeriod] = useState('minute');
  const [enabledModules, setEnabledModules] = useState<string[]>([
    'core', 'agents', 'vectorStore', 'monitoring', 'feedback'
  ]);

  // Agent communication state
  const [commProtocol, setCommProtocol] = useState('structured-json');
  const [contextTagging, setContextTagging] = useState(true);
  const [priorityRouting, setPriorityRouting] = useState(true);
  const [threadedConversations, setThreadedConversations] = useState(true);
  const [autoSummarize, setAutoSummarize] = useState(true);
  const [dlpEnabled, setDlpEnabled] = useState(false);
  const [commRetention, setCommRetention] = useState('30');

  useEffect(() => {
    const fetchWorkspace = async () => {
      if (!workspaceId) return;
      
      try {
        setLoading(true);
        try {
          // Try to get from the mock API
          const response = await axios.get(`/mock-api/api/workspace-${workspaceId}.json`);
          setWorkspace(response.data);
        } catch (innerErr) {
          // Try alternative path
          try {
            const response = await axios.get(`/public/mock-api/api/workspace-${workspaceId}.json`);
            setWorkspace(response.data);
          } catch (anotherErr) {
            // Use fallback data
            console.log('Using fallback mock workspace data');
            setWorkspace(getMockWorkspaceById(workspaceId));
          }
        }
        setError('');
      } catch (err) {
        console.error('Error fetching workspace:', err);
        // Use fallback data
        console.log('Using fallback mock workspace data after error');
        setWorkspace(getMockWorkspaceById(workspaceId));
        setError(''); // Clear error since we're using fallback data
      } finally {
        setLoading(false);
      }
    };

    fetchWorkspace();
  }, [workspaceId]);

  const handleCreateProject = () => {
    if (!workspace) return;

    // In a real implementation, this would make an API call
    const newProject = {
      id: `prj-${Math.floor(Math.random() * 1000)}`,
      name: newProjectName,
      description: newProjectDesc,
      status: newProjectStatus,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString()
    };

    setWorkspace({
      ...workspace,
      projects: [...workspace.projects, newProject]
    });
    
    setCreateProjectModal(false);
    setNewProjectName('');
    setNewProjectDesc('');
    setNewProjectStatus('Planning');
  };

  // Add new team member
  const handleAddMember = () => {
    if (!workspace) return;

    const newMember: Member = {
      id: `usr-${Math.floor(Math.random() * 1000)}`,
      name: newMemberName,
      email: newMemberEmail,
      role: newMemberRole,
      type: 'human'
    };

    setWorkspace({
      ...workspace,
      members: [...workspace.members, newMember]
    });
    
    setCreateMemberModal(false);
    setNewMemberName('');
    setNewMemberEmail('');
    setNewMemberRole('Member');
  };

  // Add new agent
  const handleAddAgent = () => {
    if (!workspace) return;

    const newAgent: AgentMember = {
      id: `agent-${Math.floor(Math.random() * 1000)}`,
      name: newAgentName,
      email: `${newAgentName.toLowerCase().replace(/\s+/g, '.')}@ai.hivemind.com`,
      role: newAgentClass,
      type: 'agent',
      agentClass: newAgentClass,
      model: newAgentModel,
      temperature: newAgentTemperature,
      tokenLimit: newAgentTokenLimit,
      tier: newAgentTier,
      tools: newAgentTools,
      customInstructions: newAgentInstructions
    };

    // Initialize agents array if it doesn't exist
    const currentAgents = workspace.agents || [];
    
    setWorkspace({
      ...workspace,
      agents: [...currentAgents, newAgent]
    });
    
    setCreateAgentModal(false);
    setNewAgentName('');
    setNewAgentClass('');
    setNewAgentModel('gpt-4o');
    setNewAgentTemperature(0.7);
    setNewAgentTokenLimit(4096);
    setNewAgentTier('standard');
    setNewAgentTools([]);
    setNewAgentInstructions('');
  };

  // Handle sidebar navigation item click
  const handleSidebarNavClick = (section: string) => {
    setActiveSection(section);
  };

  // Add a new function to handle navigation to workspace workmode
  const handleWorkModeClick = () => {
    navigate(`/workspaces/${workspaceId}/work-mode/dashboard`);
  };

  if (loading) {
    return (
      <Flex justify="center" align="center" style={{ height: '50vh' }}>
        <Loader size="lg" />
      </Flex>
    );
  }

  if (error || !workspace) {
    return (
      <Paper p="xl" withBorder radius="md" style={{ backgroundColor: '#FEF2F2' }}>
        <Text c="red">{error || 'Workspace not found'}</Text>
        <Button onClick={() => navigate('/workspaces')} mt="md">
          Return to Workspaces
        </Button>
      </Paper>
    );
  }

  // Combine regular members and agent members for the task board
  const allMembers = [
    ...workspace.members,
    ...(workspace.agents || [])
  ].map(member => ({
    ...member,
    type: member.type || 'human' // Ensure type is never undefined
  }));

  // Render each section based on the active tab
  const renderActiveSection = () => {
    switch (activeSection) {
      case 'projects':
        return (
          <>
            <Flex justify="space-between" align="center" mb="lg">
              <Title order={3}>Projects</Title>
              <Button leftSection={<IconPlus size={16} />} onClick={() => setCreateProjectModal(true)}>
                Create Project
              </Button>
            </Flex>
            
            <Grid>
              {workspace.projects.map(project => (
                <Grid.Col span={{ base: 12, md: 6, lg: 4 }} key={project.id}>
                  <Card withBorder shadow="sm" padding="lg" radius="md">
                    <Card.Section withBorder inheritPadding py="xs">
                      <Group justify="space-between">
                        <Title order={4}>{project.name}</Title>
                        <Badge color={
                          project.status === 'In Progress' ? 'blue' :
                          project.status === 'Completed' ? 'green' :
                          project.status === 'Planning' ? 'yellow' : 'gray'
                        }>
                          {project.status}
                        </Badge>
                      </Group>
                    </Card.Section>
                    
                    <Text mt="md" mb="md" c="dimmed" lineClamp={2}>
                      {project.description}
                    </Text>
                    
                    <Group mt="md" mb="md">
                      <Text size="sm" c="dimmed">
                        Created: {new Date(project.created_at).toLocaleDateString()}
                      </Text>
                      <Text size="sm" c="dimmed">
                        Updated: {new Date(project.updated_at).toLocaleDateString()}
                      </Text>
                    </Group>
                    
                    <Button 
                      fullWidth 
                      mt="md" 
                      onClick={() => navigate(`/workspaces/${workspaceId}/projects/${project.id}`)}
                    >
                      Open Project
                    </Button>
                  </Card>
                </Grid.Col>
              ))}
            </Grid>
          </>
        );
      case 'tasks':
        return <WorkspaceTaskBoard workspaceId={workspaceId || ''} members={allMembers} />;
      case 'members':
        return (
          <>
            <Flex justify="space-between" align="center" mb="lg">
              <Title order={3}>Team Members</Title>
              <Group>
                <Button 
                  leftSection={<IconPlus size={16} />} 
                  variant="outline"
                  onClick={() => setCreateMemberModal(true)}
                >
                  Add Human
                </Button>
                <Button 
                  leftSection={<IconPlus size={16} />} 
                  onClick={() => setCreateAgentModal(true)}
                >
                  Add Agent
                </Button>
              </Group>
            </Flex>
            
            <Tabs defaultValue="humans">
              <Tabs.List mb="md">
                <Tabs.Tab value="humans">Humans</Tabs.Tab>
                <Tabs.Tab value="agents">AI Agents</Tabs.Tab>
              </Tabs.List>
              
              <Tabs.Panel value="humans">
                {workspace.members.filter(m => m.type !== 'agent').map(member => (
                  <Paper key={member.id} withBorder p="md" radius="md" mb="md">
                    <Group>
                      <Avatar size="md" color="blue">
                        {member.name.split(' ').map(n => n[0]).join('')}
                      </Avatar>
                      <Box style={{ flex: 1 }}>
                        <Text fw={500}>{member.name}</Text>
                        <Text size="sm" c="dimmed">{member.email}</Text>
                      </Box>
                      <Badge>{member.role}</Badge>
                    </Group>
                  </Paper>
                ))}
                
                {workspace.members.filter(m => m.type !== 'agent').length === 0 && (
                  <Text c="dimmed" ta="center" py="xl">No human members added yet</Text>
                )}
              </Tabs.Panel>
              
              <Tabs.Panel value="agents">
                {(workspace.agents || []).map(agent => (
                  <Paper key={agent.id} withBorder p="md" radius="md" mb="md">
                    <Group mb="sm">
                      <Avatar size="md" color="violet">
                        {agent.name.split(' ').map(n => n[0]).join('')}
                      </Avatar>
                      <Box style={{ flex: 1 }}>
                        <Text fw={500}>{agent.name}</Text>
                        <Text size="sm" c="dimmed">{agent.email}</Text>
                      </Box>
                      <Badge color="violet">{agent.agentClass}</Badge>
                    </Group>
                    
                    <Grid>
                      <Grid.Col span={6}>
                        <Text size="sm" fw={500}>Model:</Text>
                        <Text size="sm" c="dimmed">{agent.model}</Text>
                      </Grid.Col>
                      <Grid.Col span={6}>
                        <Text size="sm" fw={500}>Tier:</Text>
                        <Text size="sm" c="dimmed" tt="capitalize">{agent.tier}</Text>
                      </Grid.Col>
                      <Grid.Col span={6}>
                        <Text size="sm" fw={500}>Temperature:</Text>
                        <Text size="sm" c="dimmed">{agent.temperature}</Text>
                      </Grid.Col>
                      <Grid.Col span={6}>
                        <Text size="sm" fw={500}>Token Limit:</Text>
                        <Text size="sm" c="dimmed">{agent.tokenLimit}</Text>
                      </Grid.Col>
                      
                      {agent.tools && agent.tools.length > 0 && (
                        <Grid.Col span={12}>
                          <Text size="sm" fw={500}>Tools:</Text>
                          <Group gap="xs" mt="xs">
                            {agent.tools.map(tool => (
                              <Badge key={tool} size="sm">{tool}</Badge>
                            ))}
                          </Group>
                        </Grid.Col>
                      )}
                      
                      {agent.customInstructions && (
                        <Grid.Col span={12}>
                          <Text size="sm" fw={500}>Custom Instructions:</Text>
                          <Text size="sm" c="dimmed">{agent.customInstructions}</Text>
                        </Grid.Col>
                      )}
                    </Grid>
                  </Paper>
                ))}
                
                {(!workspace.agents || workspace.agents.length === 0) && (
                  <Text c="dimmed" ta="center" py="xl">No AI agents added yet</Text>
                )}
              </Tabs.Panel>
            </Tabs>
          </>
        );
      case 'communication':
        return (
          <>
            <Title order={3} mb="lg">Agent Communication Configuration</Title>
            
            <Paper withBorder p="lg" radius="md" mb="xl">
              <Title order={4} mb="md">Communication Protocol</Title>
              
              <Select
                label="Message Format"
                data={[
                  { value: 'structured-json', label: 'Structured JSON' },
                  { value: 'simple-text', label: 'Simple Text' },
                  { value: 'yaml', label: 'YAML' },
                  { value: 'protobuf', label: 'Protocol Buffers' },
                ]}
                value={commProtocol}
                onChange={(value) => setCommProtocol(value || 'structured-json')}
                mb="md"
              />
              
              <Grid>
                <Grid.Col span={6}>
                  <Box style={{ display: 'flex', alignItems: 'center' }}>
                    <input 
                      type="checkbox" 
                      id="contextTagging"
                      checked={contextTagging}
                      onChange={(e) => setContextTagging(e.target.checked)}
                      style={{ marginRight: '10px' }}
                    />
                    <Box>
                      <label htmlFor="contextTagging" style={{ display: 'block', fontWeight: 500 }}>Context Tagging</label>
                      <Text size="xs" c="dimmed">Route messages based on context tags</Text>
                    </Box>
                  </Box>
                </Grid.Col>
                
                <Grid.Col span={6}>
                  <Box style={{ display: 'flex', alignItems: 'center' }}>
                    <input 
                      type="checkbox" 
                      id="priorityRouting"
                      checked={priorityRouting}
                      onChange={(e) => setPriorityRouting(e.target.checked)}
                      style={{ marginRight: '10px' }}
                    />
                    <Box>
                      <label htmlFor="priorityRouting" style={{ display: 'block', fontWeight: 500 }}>Priority Routing</label>
                      <Text size="xs" c="dimmed">Process high-priority messages first</Text>
                    </Box>
                  </Box>
                </Grid.Col>
                
                <Grid.Col span={6}>
                  <Box style={{ display: 'flex', alignItems: 'center' }}>
                    <input 
                      type="checkbox" 
                      id="threadedConversations"
                      checked={threadedConversations}
                      onChange={(e) => setThreadedConversations(e.target.checked)}
                      style={{ marginRight: '10px' }}
                    />
                    <Box>
                      <label htmlFor="threadedConversations" style={{ display: 'block', fontWeight: 500 }}>Threaded Conversations</label>
                      <Text size="xs" c="dimmed">Group messages by topic thread</Text>
                    </Box>
                  </Box>
                </Grid.Col>
                
                <Grid.Col span={6}>
                  <Box style={{ display: 'flex', alignItems: 'center' }}>
                    <input 
                      type="checkbox" 
                      id="autoSummarize"
                      checked={autoSummarize}
                      onChange={(e) => setAutoSummarize(e.target.checked)}
                      style={{ marginRight: '10px' }}
                    />
                    <Box>
                      <label htmlFor="autoSummarize" style={{ display: 'block', fontWeight: 500 }}>Auto-Summarize</label>
                      <Text size="xs" c="dimmed">Summarize conversations to save tokens</Text>
                    </Box>
                  </Box>
                </Grid.Col>
                
                <Grid.Col span={6}>
                  <Box style={{ display: 'flex', alignItems: 'center' }}>
                    <input 
                      type="checkbox" 
                      id="dlpEnabled"
                      checked={dlpEnabled}
                      onChange={(e) => setDlpEnabled(e.target.checked)}
                      style={{ marginRight: '10px' }}
                    />
                    <Box>
                      <label htmlFor="dlpEnabled" style={{ display: 'block', fontWeight: 500 }}>DLP Filtering</label>
                      <Text size="xs" c="dimmed">Filter sensitive information</Text>
                    </Box>
                  </Box>
                </Grid.Col>
                
                <Grid.Col span={6}>
                  <Select
                    label="Message Retention"
                    data={[
                      { value: '7', label: '7 days' },
                      { value: '30', label: '30 days' },
                      { value: '90', label: '90 days' },
                      { value: '365', label: '1 year' },
                      { value: 'forever', label: 'Forever' },
                    ]}
                    value={commRetention}
                    onChange={(value) => setCommRetention(value || '30')}
                  />
                </Grid.Col>
              </Grid>
            </Paper>
            
            <Paper withBorder p="lg" radius="md" mb="xl">
              <Title order={4} mb="md">Message Templates</Title>
              
              <Textarea
                label="Standard Message Template"
                minRows={5}
                defaultValue={`{
  "sender": "{{sender}}",
  "recipients": ["{{recipients}}"],
  "context_tags": ["{{tags}}"],
  "message_type": "{{type}}",
  "content": "{{message}}",
  "priority": "normal",
  "requires_response": true,
  "thread_id": "{{thread}}"
}`}
                mb="lg"
              />
              
              <Textarea
                label="Task Message Template"
                minRows={5}
                defaultValue={`{
  "sender": "{{sender}}",
  "recipients": ["{{recipients}}"],
  "context_tags": ["{{tags}}"],
  "message_type": "task",
  "task": {
    "title": "{{title}}",
    "description": "{{description}}",
    "deadline": "{{deadline}}",
    "priority": "{{priority}}"
  },
  "requires_response": true,
  "thread_id": "{{thread}}"
}`}
                mb="lg"
              />
            </Paper>
            
            <Paper withBorder p="lg" radius="md">
              <Title order={4} mb="md">Communication Flow</Title>
              
              <Grid>
                <Grid.Col span={6}>
                  <Select
                    label="Orchestration Mode"
                    data={[
                      { value: 'manager', label: 'Manager-Orchestrated' },
                      { value: 'direct', label: 'Direct P2P' },
                      { value: 'hybrid', label: 'Hybrid' },
                    ]}
                    defaultValue="manager"
                    mb="md"
                  />
                </Grid.Col>
                
                <Grid.Col span={6}>
                  <Select
                    label="Context Handling"
                    data={[
                      { value: 'full', label: 'Full Context Sharing' },
                      { value: 'summarized', label: 'Summarized Context' },
                      { value: 'minimal', label: 'Minimal Context' },
                    ]}
                    defaultValue="summarized"
                    mb="md"
                  />
                </Grid.Col>
              </Grid>
              
              <Title order={5} mt="lg" mb="md">Communication Diagram</Title>
              <Box 
                style={{ 
                  height: '200px', 
                  backgroundColor: '#f1f3f5', 
                  borderRadius: '4px',
                  display: 'flex',
                  justifyContent: 'center',
                  alignItems: 'center',
                  color: '#868e96'
                }}
              >
                Communication flow diagram would appear here
              </Box>
              
              <Text size="sm" mt="md" c="dimmed" mb="lg">
                This diagram visualizes how messages flow between agents in your workspace.
              </Text>
            </Paper>
          </>
        );
      case 'settings':
        return (
          <>
            <Title order={3} mb="lg">Workspace Settings</Title>
            
            <Paper withBorder p="lg" radius="md" mb="xl">
              <Title order={4} mb="md">General Settings</Title>
              
              <TextInput
                label="Workspace Name"
                value={workspace.name}
                mb="md"
              />
              
              <Textarea
                label="Description"
                value={workspace.description}
                minRows={3}
                mb="xl"
              />
            </Paper>

            <Paper withBorder p="lg" radius="md" mb="xl">
              <Title order={4} mb="md">Cost Management</Title>
              
              <Grid>
                <Grid.Col span={6}>
                  <TextInput
                    label="Budget Limit (USD)"
                    type="number"
                    value={budgetLimit}
                    onChange={(e) => setBudgetLimit(parseFloat(e.target.value))}
                    mb="md"
                  />
                </Grid.Col>
                <Grid.Col span={6}>
                  <TextInput
                    label="Cost Per 1K Tokens (USD)"
                    type="number"
                    step={0.0001}
                    min={0}
                    value={costPerToken}
                    onChange={(e) => setCostPerToken(parseFloat(e.target.value))}
                    mb="md"
                  />
                </Grid.Col>
              </Grid>
              
              <Text size="sm" mb="xl" fs="italic">
                Estimated daily cost at current usage: $23.45
              </Text>
              
              <Title order={5} mb="sm">Usage Alerts</Title>
              <Select
                label="Notify when budget reaches"
                data={[
                  { value: '50', label: '50% of limit' },
                  { value: '75', label: '75% of limit' },
                  { value: '90', label: '90% of limit' },
                  { value: '100', label: '100% of limit (budget exceeded)' },
                ]}
                value="75"
                mb="lg"
              />
            </Paper>
            
            <Paper withBorder p="lg" radius="md" mb="xl">
              <Title order={4} mb="md">Rate Limits</Title>
              
              <Group align="flex-end" mb="md">
                <TextInput
                  label="Maximum Requests"
                  type="number"
                  value={rateLimit}
                  onChange={(e) => setRateLimit(parseInt(e.target.value))}
                  style={{ width: '150px' }}
                />
                <Text>per</Text>
                <Select
                  data={[
                    { value: 'second', label: 'Second' },
                    { value: 'minute', label: 'Minute' },
                    { value: 'hour', label: 'Hour' },
                    { value: 'day', label: 'Day' },
                  ]}
                  value={rateLimitPeriod}
                  onChange={(value) => setRateLimitPeriod(value || 'minute')}
                  style={{ width: '120px' }}
                />
              </Group>
              
              <Text size="sm" c="dimmed" mb="lg">
                API rate limits help prevent excessive usage and cost overruns.
              </Text>
            </Paper>
            
            <Paper withBorder p="lg" radius="md" mb="xl">
              <Title order={4} mb="md">Module Configuration</Title>
              
              <MultiSelect
                label="Enabled Modules"
                data={[
                  { value: 'core', label: 'Core Platform' },
                  { value: 'agents', label: 'AI Agents' },
                  { value: 'vectorStore', label: 'Vector Database' },
                  { value: 'fileStorage', label: 'File Storage' },
                  { value: 'monitoring', label: 'Monitoring & Analytics' },
                  { value: 'feedback', label: 'Feedback Loop' },
                  { value: 'llmCaching', label: 'LLM Response Caching' },
                  { value: 'webSearch', label: 'Web Search' },
                  { value: 'codeExecution', label: 'Code Execution Environment' },
                  { value: 'teamChat', label: 'Team Chat Integration' },
                ]}
                value={enabledModules}
                onChange={setEnabledModules}
                mb="md"
              />
              
              <Text size="sm" mb="xl" c="dimmed">
                Enable or disable specific modules to customize your workspace functionality.
              </Text>
              
              <Box>
                <Title order={5} mb="sm">Module Specific Settings</Title>
                
                {enabledModules.includes('vectorStore') && (
                  <Box mb="md">
                    <Title order={6} mb="xs">Vector Database</Title>
                    <Select
                      label="Vector Store Provider"
                      data={[
                        { value: 'pinecone', label: 'Pinecone' },
                        { value: 'qdrant', label: 'Qdrant' },
                        { value: 'weaviate', label: 'Weaviate' },
                        { value: 'milvus', label: 'Milvus' },
                      ]}
                      value="qdrant"
                      mb="xs"
                    />
                    <TextInput
                      label="Embedding Model"
                      placeholder="e.g., text-embedding-3-large"
                      value="text-embedding-3-large"
                      mb="md"
                    />
                  </Box>
                )}
                
                {enabledModules.includes('monitoring') && (
                  <Box mb="md">
                    <Title order={6} mb="xs">Monitoring & Analytics</Title>
                    <MultiSelect
                      label="Tracked Metrics"
                      data={[
                        { value: 'tokenUsage', label: 'Token Usage' },
                        { value: 'responseTime', label: 'Response Time' },
                        { value: 'errorRate', label: 'Error Rate' },
                        { value: 'userFeedback', label: 'User Feedback' },
                        { value: 'costAnalysis', label: 'Cost Analysis' },
                      ]}
                      value={['tokenUsage', 'responseTime', 'costAnalysis']}
                      mb="md"
                    />
                  </Box>
                )}
                
                {enabledModules.includes('llmCaching') && (
                  <Box mb="md">
                    <Title order={6} mb="xs">LLM Response Caching</Title>
                    <TextInput
                      label="Cache TTL (seconds)"
                      type="number"
                      value="3600"
                      mb="xs"
                    />
                    <Select
                      label="Cache Storage"
                      data={[
                        { value: 'redis', label: 'Redis' },
                        { value: 'memcached', label: 'Memcached' },
                        { value: 'local', label: 'Local Memory' },
                      ]}
                      value="redis"
                      mb="md"
                    />
                  </Box>
                )}
              </Box>
            </Paper>
            
            <Paper withBorder p="lg" radius="md">
              <Title order={4} mb="md" c="red.7">Danger Zone</Title>
              
              <Text c="dimmed" mb="md">
                Once you delete a workspace, there is no going back. Please be certain.
              </Text>
              <Button color="red" variant="outline">Delete Workspace</Button>
            </Paper>
          </>
        );
      case 'analytics':
        return (
          <>
            <Title order={3} mb="lg">Workspace Analytics</Title>
            
            <Grid>
              <Grid.Col span={{ base: 12, md: 6, lg: 3 }}>
                <Paper withBorder p="md" radius="md" ta="center">
                  <Text fw={700} size="xl" mb="xs">{workspace.projects.length}</Text>
                  <Text c="dimmed">Total Projects</Text>
                </Paper>
              </Grid.Col>
              
              <Grid.Col span={{ base: 12, md: 6, lg: 3 }}>
                <Paper withBorder p="md" radius="md" ta="center">
                  <Text fw={700} size="xl" mb="xs">{workspace.members.length}</Text>
                  <Text c="dimmed">Team Members</Text>
                </Paper>
              </Grid.Col>
              
              <Grid.Col span={{ base: 12, md: 6, lg: 3 }}>
                <Paper withBorder p="md" radius="md" ta="center">
                  <Text fw={700} size="xl" mb="xs">
                    {workspace.projects.filter(p => p.status === 'In Progress').length}
                  </Text>
                  <Text c="dimmed">Active Projects</Text>
                </Paper>
              </Grid.Col>
              
              <Grid.Col span={{ base: 12, md: 6, lg: 3 }}>
                <Paper withBorder p="md" radius="md" ta="center">
                  <Text fw={700} size="xl" mb="xs">
                    {workspace.projects.filter(p => p.status === 'Completed').length}
                  </Text>
                  <Text c="dimmed">Completed Projects</Text>
                </Paper>
              </Grid.Col>
            </Grid>
            
            <Paper withBorder p="lg" radius="md" mt="xl">
              <Text>Analytics charts would appear here</Text>
            </Paper>
          </>
        );
      default:
        return <div>Select a section from the sidebar</div>;
    }
  };

  return (
    <Box style={{ display: 'flex', height: 'calc(100vh - 60px)' }}>
      {/* Workspace Navigation Sidebar */}
      <Box 
        style={{ 
          width: sidebarMinimized ? 60 : 300, 
          backgroundColor: '#202939', 
          padding: '1rem',
          overflowY: 'auto',
          borderRight: '1px solid #364152',
          transition: 'width 0.3s ease',
          position: 'relative'
        }}
      >
        <ActionIcon 
          variant="filled" 
          size="lg"
          color="blue"
          style={{
            position: 'absolute',
            right: sidebarMinimized ? '50%' : '0.5rem',
            top: '0.5rem',
            zIndex: 100,
            transform: sidebarMinimized ? 'translateX(50%)' : 'none',
            borderRadius: '50%',
            backgroundColor: '#1A3FE4',
            boxShadow: '0 2px 4px rgba(0,0,0,0.2)',
            transition: 'all 0.3s ease',
          }}
          onClick={() => setSidebarMinimized(prev => !prev)}
          title={sidebarMinimized ? "Expand workspace sidebar" : "Collapse workspace sidebar"}
        >
          {sidebarMinimized ? <IconChevronRight size={16} /> : <IconChevronLeft size={16} />}
        </ActionIcon>
        
        <Box mb="lg">
          <Group mb="md">
            {!sidebarMinimized && <Title order={4} c="white">Workspace Navigation</Title>}
          </Group>
          <Divider mb="md" color="#364152" />
          <Box>
            <Text fw={700} size={sidebarMinimized ? "sm" : "lg"} c="white" ta={sidebarMinimized ? "center" : "left"}>
              {sidebarMinimized ? workspace?.name?.substring(0, 1) : workspace?.name}
            </Text>
            {!sidebarMinimized && <Text c="dimmed" size="sm">{workspace?.description}</Text>}
          </Box>
        </Box>
        
        {/* Work Mode Button */}
        <Box mb="md">
          <Button
            leftSection={!sidebarMinimized && <IconBrain size={20} />}
            fullWidth
            size="lg"
            style={{
              backgroundColor: '#1A3FE4',
              color: 'white',
              borderRadius: '8px',
              padding: sidebarMinimized ? '8px' : '12px 20px',
              fontSize: sidebarMinimized ? '10px' : '16px',
              fontWeight: 'bold',
              boxShadow: '0 4px 12px rgba(26,63,228,0.4)',
              border: '2px solid #4169E1',
              transition: 'all 0.3s ease',
              marginBottom: '16px'
            }}
            onClick={handleWorkModeClick}
          >
            {sidebarMinimized ? <IconBrain size={24} /> : "Enter Work Mode"}
          </Button>
        </Box>
        
        <Divider mb="md" color="#364152" />
        
        {/* Navigation Items */}
        <Box mb="md">
          {!sidebarMinimized && <Text fw={600} c="white" mb="xs">Workspace</Text>}
          <Box 
            onClick={() => handleSidebarNavClick('projects')}
            style={{
              display: 'flex',
              alignItems: 'center',
              padding: '0.5rem 0.75rem',
              borderRadius: '0.25rem',
              cursor: 'pointer',
              backgroundColor: activeSection === 'projects' ? '#1A3FE4' : 'transparent',
              color: activeSection === 'projects' ? '#F8FAFC' : '#9AA5B4',
              marginBottom: '0.5rem',
              justifyContent: sidebarMinimized ? 'center' : 'flex-start',
            }}
          >
            <IconFileText size={20} />
            {!sidebarMinimized && <Text ml="xs">Projects</Text>}
          </Box>
          
          <Box 
            onClick={() => handleSidebarNavClick('tasks')}
            style={{
              display: 'flex',
              alignItems: 'center',
              padding: '0.5rem 0.75rem',
              borderRadius: '0.25rem',
              cursor: 'pointer',
              backgroundColor: activeSection === 'tasks' ? '#1A3FE4' : 'transparent',
              color: activeSection === 'tasks' ? '#F8FAFC' : '#9AA5B4',
              marginBottom: '0.5rem',
              justifyContent: sidebarMinimized ? 'center' : 'flex-start',
            }}
          >
            <IconClipboardList size={20} />
            {!sidebarMinimized && <Text ml="xs">Tasks</Text>}
          </Box>
          
          <Box 
            onClick={() => handleSidebarNavClick('members')}
            style={{
              display: 'flex',
              alignItems: 'center',
              padding: '0.5rem 0.75rem',
              borderRadius: '0.25rem',
              cursor: 'pointer',
              backgroundColor: activeSection === 'members' ? '#1A3FE4' : 'transparent',
              color: activeSection === 'members' ? '#F8FAFC' : '#9AA5B4',
              marginBottom: '0.5rem',
              justifyContent: sidebarMinimized ? 'center' : 'flex-start',
            }}
          >
            <IconUsers size={20} />
            {!sidebarMinimized && <Text ml="xs">Members</Text>}
          </Box>
          
          <Box 
            onClick={() => handleSidebarNavClick('communication')}
            style={{
              display: 'flex',
              alignItems: 'center',
              padding: '0.5rem 0.75rem',
              borderRadius: '0.25rem',
              cursor: 'pointer',
              backgroundColor: activeSection === 'communication' ? '#1A3FE4' : 'transparent',
              color: activeSection === 'communication' ? '#F8FAFC' : '#9AA5B4',
              marginBottom: '0.5rem',
              justifyContent: sidebarMinimized ? 'center' : 'flex-start',
            }}
          >
            <IconChartBar size={20} />
            {!sidebarMinimized && <Text ml="xs">Communication</Text>}
          </Box>
          
          <Box 
            onClick={() => handleSidebarNavClick('analytics')}
            style={{
              display: 'flex',
              alignItems: 'center',
              padding: '0.5rem 0.75rem',
              borderRadius: '0.25rem',
              cursor: 'pointer',
              backgroundColor: activeSection === 'analytics' ? '#1A3FE4' : 'transparent',
              color: activeSection === 'analytics' ? '#F8FAFC' : '#9AA5B4',
              marginBottom: '0.5rem',
              justifyContent: sidebarMinimized ? 'center' : 'flex-start',
            }}
          >
            <IconChartBar size={20} />
            {!sidebarMinimized && <Text ml="xs">Analytics</Text>}
          </Box>
          
          <Box 
            onClick={() => handleSidebarNavClick('settings')}
            style={{
              display: 'flex',
              alignItems: 'center',
              padding: '0.5rem 0.75rem',
              borderRadius: '0.25rem',
              cursor: 'pointer',
              backgroundColor: activeSection === 'settings' ? '#1A3FE4' : 'transparent',
              color: activeSection === 'settings' ? '#F8FAFC' : '#9AA5B4',
              marginBottom: '0.5rem',
              justifyContent: sidebarMinimized ? 'center' : 'flex-start',
            }}
          >
            <IconSettings size={20} />
            {!sidebarMinimized && <Text ml="xs">Settings</Text>}
          </Box>
        </Box>
        
        <Divider mb="md" color="#364152" />
        
        {!sidebarMinimized && <Text fw={600} mb="xs" c="white">Projects</Text>}
        <ScrollArea h="calc(100vh - 400px)">
          {workspace?.projects.map(project => (
            <Card 
              key={project.id} 
              withBorder 
              padding={sidebarMinimized ? "xs" : "sm"} 
              radius="md"
              mb="xs"
              onClick={() => navigate(`/workspaces/${workspaceId}/projects/${project.id}`)}
              style={{ cursor: 'pointer' }}
            >
              <Group>
                <IconFolder size={sidebarMinimized ? 16 : 20} />
                {!sidebarMinimized && (
                  <Box style={{ flex: 1 }}>
                    <Text fw={500} size="sm">{project.name}</Text>
                    <Badge size="xs" color={
                      project.status === 'In Progress' ? 'blue' :
                      project.status === 'Completed' ? 'green' :
                      project.status === 'Planning' ? 'yellow' : 'gray'
                    }>
                      {project.status}
                    </Badge>
                  </Box>
                )}
                {!sidebarMinimized && (
                  <ActionIcon variant="subtle">
                    <IconDotsVertical size={16} />
                  </ActionIcon>
                )}
              </Group>
            </Card>
          ))}
          
          <Button 
            leftSection={sidebarMinimized ? undefined : <IconPlus size={16} />} 
            mt="md" 
            variant="outline" 
            fullWidth
            onClick={() => setCreateProjectModal(true)}
            px={sidebarMinimized ? "xs" : "md"}
          >
            {sidebarMinimized ? "+" : "New Project"}
          </Button>
        </ScrollArea>
      </Box>

      {/* Main Content Area */}
      <Box style={{ flex: 1, padding: '1rem', overflowY: 'auto', transition: 'width 0.3s ease' }}>
        <Box mb="lg">
          <Title>{workspace.name}</Title>
          <Text c="dimmed">{workspace.description}</Text>
        </Box>

        {/* Render the active section */}
        {renderActiveSection()}
      </Box>

      <Modal
        opened={createProjectModal}
        onClose={() => setCreateProjectModal(false)}
        title="Create New Project"
        size="md"
      >
        <Box>
          <TextInput
            label="Project Name"
            placeholder="Enter project name"
            value={newProjectName}
            onChange={(e) => setNewProjectName(e.target.value)}
            required
            mb="md"
          />
          
          <Textarea
            label="Description"
            placeholder="Describe the project"
            value={newProjectDesc}
            onChange={(e) => setNewProjectDesc(e.target.value)}
            minRows={3}
            mb="md"
          />
          
          <Select
            label="Status"
            value={newProjectStatus}
            onChange={(value) => setNewProjectStatus(value || 'Planning')}
            data={[
              { value: 'Planning', label: 'Planning' },
              { value: 'In Progress', label: 'In Progress' },
              { value: 'Completed', label: 'Completed' },
              { value: 'On Hold', label: 'On Hold' }
            ]}
            mb="xl"
          />
          
          <Group justify="flex-end">
            <Button variant="outline" onClick={() => setCreateProjectModal(false)}>Cancel</Button>
            <Button 
              onClick={handleCreateProject}
              disabled={!newProjectName.trim()}
            >
              Create
            </Button>
          </Group>
        </Box>
      </Modal>

      {/* Add Member Modal */}
      <Modal
        opened={createMemberModal}
        onClose={() => setCreateMemberModal(false)}
        title="Add Team Member"
        size="md"
      >
        <Box>
          <TextInput
            label="Name"
            placeholder="Enter member name"
            value={newMemberName}
            onChange={(e) => setNewMemberName(e.target.value)}
            required
            mb="md"
          />
          
          <TextInput
            label="Email"
            placeholder="Enter member email"
            value={newMemberEmail}
            onChange={(e) => setNewMemberEmail(e.target.value)}
            required
            mb="md"
          />
          
          <Select
            label="Role"
            value={newMemberRole}
            onChange={(value) => setNewMemberRole(value || 'Member')}
            data={[
              { value: 'Owner', label: 'Owner' },
              { value: 'Admin', label: 'Admin' },
              { value: 'Member', label: 'Member' },
              { value: 'Viewer', label: 'Viewer' }
            ]}
            mb="xl"
          />
          
          <Group justify="flex-end">
            <Button variant="outline" onClick={() => setCreateMemberModal(false)}>Cancel</Button>
            <Button 
              onClick={handleAddMember}
              disabled={!newMemberName.trim() || !newMemberEmail.trim()}
            >
              Add Member
            </Button>
          </Group>
        </Box>
      </Modal>

      {/* Add Agent Modal */}
      <Modal
        opened={createAgentModal}
        onClose={() => setCreateAgentModal(false)}
        title="Add AI Agent"
        size="lg"
      >
        <Box>
          <TextInput
            label="Agent Name"
            placeholder="Enter agent name"
            value={newAgentName}
            onChange={(e) => setNewAgentName(e.target.value)}
            required
            mb="md"
          />
          
          <Select
            label="Agent Class"
            placeholder="Select agent class"
            value={newAgentClass}
            onChange={(value) => setNewAgentClass(value || '')}
            data={[
              { value: 'Manager', label: 'Manager Agent' },
              { value: 'Planner', label: 'Planner Agent' },
              { value: 'Coder', label: 'Coder Agent' },
              { value: 'Reviewer', label: 'Reviewer Agent' },
              { value: 'Tester', label: 'Tester Agent' },
              { value: 'DevOps', label: 'DevOps Agent' },
              { value: 'Writer', label: 'Writer Agent' },
              { value: 'Designer', label: 'Designer Agent' }
            ]}
            mb="md"
          />
          
          <Grid>
            <Grid.Col span={6}>
              <Select
                label="Model"
                value={newAgentModel}
                onChange={(value) => setNewAgentModel(value || 'gpt-4o')}
                data={[
                  { value: 'gpt-4o', label: 'GPT-4o' },
                  { value: 'gpt-4-turbo', label: 'GPT-4 Turbo' },
                  { value: 'gpt-3.5-turbo', label: 'GPT-3.5 Turbo' },
                  { value: 'claude-3-opus', label: 'Claude 3 Opus' },
                  { value: 'claude-3-sonnet', label: 'Claude 3 Sonnet' },
                  { value: 'claude-3-haiku', label: 'Claude 3 Haiku' },
                ]}
                mb="md"
              />
            </Grid.Col>
            <Grid.Col span={6}>
              <Select
                label="Tier"
                value={newAgentTier}
                onChange={(value: any) => setNewAgentTier(value || 'standard')}
                data={[
                  { value: 'economy', label: 'Economy' },
                  { value: 'standard', label: 'Standard' },
                  { value: 'premium', label: 'Premium' }
                ]}
                mb="md"
              />
            </Grid.Col>
            <Grid.Col span={6}>
              <TextInput
                label="Temperature"
                type="number"
                min={0}
                max={1}
                step={0.1}
                value={newAgentTemperature}
                onChange={(e) => setNewAgentTemperature(parseFloat(e.target.value))}
                mb="md"
              />
            </Grid.Col>
            <Grid.Col span={6}>
              <TextInput
                label="Token Limit"
                type="number"
                min={1000}
                max={128000}
                step={1}
                value={newAgentTokenLimit}
                onChange={(e) => setNewAgentTokenLimit(parseInt(e.target.value))}
                mb="md"
              />
            </Grid.Col>
          </Grid>
          
          <MultiSelect
            label="Tools"
            placeholder="Select tools"
            value={newAgentTools}
            onChange={(value: string[]) => setNewAgentTools(value || [])}
            data={[
              { value: 'WebSearch', label: 'Web Search' },
              { value: 'CodeInterpreter', label: 'Code Interpreter' },
              { value: 'FileTool', label: 'File Tool' },
              { value: 'DatabaseTool', label: 'Database Tool' },
              { value: 'APICaller', label: 'API Caller' },
              { value: 'AgentCommunicator', label: 'Agent Communicator' },
            ]}
            mb="md"
            multiple
          />
          
          <Textarea
            label="Custom Instructions"
            placeholder="Enter any custom instructions for this agent"
            value={newAgentInstructions}
            onChange={(e) => setNewAgentInstructions(e.target.value)}
            minRows={3}
            mb="xl"
          />
          
          <Group justify="flex-end">
            <Button variant="outline" onClick={() => setCreateAgentModal(false)}>Cancel</Button>
            <Button 
              onClick={handleAddAgent}
              disabled={!newAgentName.trim() || !newAgentClass}
            >
              Add Agent
            </Button>
          </Group>
        </Box>
      </Modal>
    </Box>
  );
} 