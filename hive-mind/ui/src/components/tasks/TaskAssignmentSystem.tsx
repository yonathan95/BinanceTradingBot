import React, { useState, useEffect } from 'react';
import { 
  Box, 
  Title, 
  Text, 
  Paper, 
  Group, 
  Badge, 
  Button, 
  Select, 
  MultiSelect, 
  Table, 
  Avatar, 
  Tooltip,
  ActionIcon,
  Modal,
  Stack,
  ScrollArea,
  Switch,
  Card,
  Divider
} from '@mantine/core';
import { IconUsers, IconTag, IconCheck, IconX, IconBrain, IconUserSearch } from '../layout/icons';
import { tasks as tasksApi, agents as agentsApi } from '../../services/api';

interface Agent {
  id: string;
  name: string;
  type: 'human' | 'agent';
  skills: string[];
  availability: number; // 0-100%
  role: string;
  assignedTasks: number;
}

interface Task {
  id: string;
  title: string;
  description: string;
  assigned_to: string | null;
  assignee_name: string | null;
  assignee_type: string | null;
  priority: string;
  status: string;
  due_date: string | null;
  time_estimate: number | null;
  progress: number;
  tags: string[];
  created_by: string;
  created_at: string;
  updated_at: string;
}

interface TaskAssignmentSystemProps {
  workspaceId: string;
  teamId?: string;
  projectId?: string;
}

const TaskAssignmentSystem: React.FC<TaskAssignmentSystemProps> = ({ 
  workspaceId, 
  teamId,
  projectId
}) => {
  // State
  const [tasks, setTasks] = useState<Task[]>([]);
  const [agents, setAgents] = useState<Agent[]>([]);
  const [selectedTask, setSelectedTask] = useState<string | null>(null);
  const [selectedAgent, setSelectedAgent] = useState<string | null>(null);
  const [useAI, setUseAI] = useState(true);
  const [tagFilter, setTagFilter] = useState<string[]>([]);
  const [statusFilter, setStatusFilter] = useState<string | null>(null);
  const [priorityFilter, setPriorityFilter] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [assignmentModalOpen, setAssignmentModalOpen] = useState(false);
  const [suggestedAgents, setSuggestedAgents] = useState<Agent[]>([]);

  // Load data
  useEffect(() => {
    loadTasks();
    loadAgents();
  }, [workspaceId, teamId, projectId]);

  const loadTasks = async () => {
    try {
      setIsLoading(true);
      const filters: any = {
        status: 'created', // Only get unassigned tasks by default
      };
      
      if (teamId) filters.team_id = teamId;
      if (projectId) filters.project_id = projectId;
      
      const response = await tasksApi.getTasks(filters);
      setTasks(response.data);
    } catch (error) {
      console.error('Error loading tasks:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const loadAgents = async () => {
    try {
      const response = await agentsApi.getAgents();
      // Transform agent data to match the component's Agent interface
      const formattedAgents: Agent[] = response.data.map((agent: any) => ({
        id: agent.id,
        name: agent.name,
        type: 'agent',
        skills: agent.role ? [agent.role] : [],
        availability: 100, // Default value, could be calculated from current task load
        role: agent.role || 'agent',
        assignedTasks: 0 // This would be calculated from assigned tasks
      }));
      setAgents(formattedAgents);
    } catch (error) {
      console.error('Error loading agents:', error);
    }
  };

  // Apply filters to tasks
  const filteredTasks = tasks
    .filter(task => !statusFilter || task.status === statusFilter)
    .filter(task => !priorityFilter || task.priority === priorityFilter)
    .filter(task => tagFilter.length === 0 || tagFilter.some(tag => task.tags.includes(tag)));

  // Get all unique tags from tasks
  const allTags = [...new Set(tasks.flatMap(task => task.tags))].map(tag => ({
    value: tag,
    label: tag
  }));

  // Get all unique statuses from tasks
  const allStatuses = [...new Set(tasks.map(task => task.status))].map(status => ({
    value: status,
    label: status
  }));

  // Get all unique priorities from tasks
  const allPriorities = [...new Set(tasks.map(task => task.priority))].map(priority => ({
    value: priority,
    label: priority
  }));

  // Handle task assignment
  const handleAssignTask = async () => {
    if (!selectedTask || !selectedAgent) return;
    
    try {
      setIsLoading(true);
      await tasksApi.updateTask(selectedTask, {
        assigned_to: selectedAgent,
        status: 'assigned'
      });
      
      // Refresh task list
      await loadTasks();
      
      // Reset selection
      setSelectedTask(null);
      setSelectedAgent(null);
      setAssignmentModalOpen(false);
    } catch (error) {
      console.error('Error assigning task:', error);
    } finally {
      setIsLoading(false);
    }
  };

  // Suggest agents for a task
  const suggestAgentsForTask = async () => {
    if (!selectedTask) return;
    
    const task = tasks.find(t => t.id === selectedTask);
    if (!task) return;
    
    // In a real-world scenario, this would call an AI-powered endpoint
    // For now, we'll just suggest agents based on skills (tags) match
    const taskTags = task.tags || [];
    
    // Sort agents by skill match
    const rankedAgents = [...agents].sort((a, b) => {
      const aSkillMatch = a.skills.filter(skill => 
        taskTags.some(tag => tag.toLowerCase().includes(skill.toLowerCase()))
      ).length;
      
      const bSkillMatch = b.skills.filter(skill => 
        taskTags.some(tag => tag.toLowerCase().includes(skill.toLowerCase()))
      ).length;
      
      // Sort by skill match, then by availability
      return bSkillMatch - aSkillMatch || b.availability - a.availability;
    });
    
    setSuggestedAgents(rankedAgents);
  };

  // Open assignment modal and suggest agents if AI is enabled
  const handleOpenAssignmentModal = () => {
    setAssignmentModalOpen(true);
    if (useAI) {
      suggestAgentsForTask();
    }
  };

  return (
    <Box p="md">
      <Title order={2} mb="md" style={{ color: '#f8f9fa' }}>
        Task Assignment System
      </Title>
      
      {/* Filters */}
      <Paper p="md" mb="lg" style={{ backgroundColor: '#2c2e33', border: '1px solid #444' }}>
        <Title order={4} mb="sm" style={{ color: '#e9ecef' }}>
          Filters
        </Title>
        <Group position="apart">
          <Box style={{ flex: 1 }}>
            <Text size="sm" fw={500} style={{ color: '#aaa', marginBottom: '8px' }}>
              Tags
            </Text>
            <MultiSelect
              data={allTags}
              value={tagFilter}
              onChange={setTagFilter}
              placeholder="Filter by tags"
              clearable
              styles={{
                input: {
                  backgroundColor: '#333',
                  color: 'white',
                  border: '1px solid #444',
                }
              }}
            />
          </Box>
          
          <Box style={{ flex: 1 }}>
            <Text size="sm" fw={500} style={{ color: '#aaa', marginBottom: '8px' }}>
              Status
            </Text>
            <Select
              data={allStatuses}
              value={statusFilter}
              onChange={setStatusFilter}
              placeholder="Filter by status"
              clearable
              styles={{
                input: {
                  backgroundColor: '#333',
                  color: 'white',
                  border: '1px solid #444',
                }
              }}
            />
          </Box>
          
          <Box style={{ flex: 1 }}>
            <Text size="sm" fw={500} style={{ color: '#aaa', marginBottom: '8px' }}>
              Priority
            </Text>
            <Select
              data={allPriorities}
              value={priorityFilter}
              onChange={setPriorityFilter}
              placeholder="Filter by priority"
              clearable
              styles={{
                input: {
                  backgroundColor: '#333',
                  color: 'white',
                  border: '1px solid #444',
                }
              }}
            />
          </Box>
        </Group>
      </Paper>
      
      {/* Tasks Table */}
      <Paper p="md" mb="lg" style={{ backgroundColor: '#2c2e33', border: '1px solid #444' }}>
        <Group position="apart" mb="md">
          <Title order={4} style={{ color: '#e9ecef' }}>
            Available Tasks ({filteredTasks.length})
          </Title>
          <Button 
            variant="filled" 
            color="blue" 
            disabled={!selectedTask}
            onClick={handleOpenAssignmentModal}
            loading={isLoading}
          >
            Assign Task
          </Button>
        </Group>
        
        <ScrollArea style={{ height: 400 }}>
          <Table style={{ minWidth: 800 }}>
            <thead>
              <tr>
                <th style={{ color: '#aaa' }}>Select</th>
                <th style={{ color: '#aaa' }}>Title</th>
                <th style={{ color: '#aaa' }}>Priority</th>
                <th style={{ color: '#aaa' }}>Status</th>
                <th style={{ color: '#aaa' }}>Tags</th>
                <th style={{ color: '#aaa' }}>Created</th>
              </tr>
            </thead>
            <tbody>
              {filteredTasks.map((task) => (
                <tr key={task.id} style={{ 
                  backgroundColor: selectedTask === task.id ? '#304060' : 'transparent',
                  cursor: 'pointer'
                }}>
                  <td>
                    <ActionIcon 
                      color={selectedTask === task.id ? 'blue' : 'gray'} 
                      variant="filled"
                      onClick={() => setSelectedTask(selectedTask === task.id ? null : task.id)}
                    >
                      {selectedTask === task.id ? <IconCheck size={16} /> : <IconX size={16} />}
                    </ActionIcon>
                  </td>
                  <td style={{ color: 'white' }}>{task.title}</td>
                  <td>
                    <Badge 
                      color={
                        task.priority === 'high' ? 'red' : 
                        task.priority === 'medium' ? 'yellow' : 'blue'
                      }
                    >
                      {task.priority}
                    </Badge>
                  </td>
                  <td>
                    <Badge color="gray">{task.status}</Badge>
                  </td>
                  <td>
                    <Group spacing={4}>
                      {task.tags.slice(0, 2).map((tag, i) => (
                        <Badge key={i} size="sm" color="cyan" variant="filled">{tag}</Badge>
                      ))}
                      {task.tags.length > 2 && (
                        <Tooltip label={task.tags.slice(2).join(', ')}>
                          <Badge size="sm" color="dark">+{task.tags.length - 2}</Badge>
                        </Tooltip>
                      )}
                    </Group>
                  </td>
                  <td style={{ color: '#aaa' }}>
                    {new Date(task.created_at).toLocaleDateString()}
                  </td>
                </tr>
              ))}
              {filteredTasks.length === 0 && (
                <tr>
                  <td colSpan={6} style={{ textAlign: 'center', padding: '20px', color: '#aaa' }}>
                    No tasks match your filters
                  </td>
                </tr>
              )}
            </tbody>
          </Table>
        </ScrollArea>
      </Paper>
      
      {/* Assignment Modal */}
      <Modal
        opened={assignmentModalOpen}
        onClose={() => setAssignmentModalOpen(false)}
        title="Assign Task"
        size="lg"
        styles={{
          modal: {
            backgroundColor: '#202124',
            color: 'white'
          },
          title: {
            color: 'white',
            fontWeight: 'bold'
          }
        }}
      >
        {selectedTask && (
          <Stack spacing="lg">
            <Box>
              <Text size="sm" fw={500} style={{ color: '#aaa', marginBottom: '8px' }}>
                Selected Task
              </Text>
              <Card p="sm" style={{ backgroundColor: '#333', border: '1px solid #444' }}>
                <Text fw={500} style={{ color: 'white' }}>
                  {tasks.find(t => t.id === selectedTask)?.title}
                </Text>
                <Text size="sm" style={{ color: '#aaa' }}>
                  {tasks.find(t => t.id === selectedTask)?.description}
                </Text>
              </Card>
            </Box>
            
            <Divider />
            
            <Box>
              <Text size="sm" fw={500} style={{ color: '#aaa', marginBottom: '8px' }}>
                Select Agent
              </Text>
              <Select
                data={agents.map(agent => ({ 
                  value: agent.id, 
                  label: `${agent.name} (${agent.role})`,
                  group: agent.type
                }))}
                value={selectedAgent}
                onChange={setSelectedAgent}
                placeholder="Select an agent to assign"
                searchable
                clearable
                styles={{
                  input: {
                    backgroundColor: '#333',
                    color: 'white',
                    border: '1px solid #444',
                  }
                }}
              />
            </Box>
            
            <Group>
              <Switch
                checked={useAI}
                onChange={(event) => setUseAI(event.currentTarget.checked)}
                label="Use AI to suggest agents"
                styles={{
                  label: {
                    color: 'white'
                  }
                }}
              />
            </Group>
            
            {useAI && suggestedAgents.length > 0 && (
              <Box>
                <Text size="sm" fw={500} style={{ color: '#aaa', marginBottom: '8px' }}>
                  AI Suggestions
                </Text>
                <Stack spacing="xs">
                  {suggestedAgents.slice(0, 3).map((agent) => (
                    <Card 
                      key={agent.id} 
                      p="sm" 
                      style={{ 
                        backgroundColor: selectedAgent === agent.id ? '#304060' : '#333',
                        border: '1px solid #444',
                        cursor: 'pointer'
                      }}
                      onClick={() => setSelectedAgent(agent.id)}
                    >
                      <Group position="apart">
                        <Group>
                          <Avatar color="blue" radius="xl">
                            <IconBrain size={20} />
                          </Avatar>
                          <div>
                            <Text fw={500} style={{ color: 'white' }}>
                              {agent.name}
                            </Text>
                            <Text size="xs" style={{ color: '#aaa' }}>
                              {agent.role}
                            </Text>
                          </div>
                        </Group>
                        <Badge color="blue">{agent.availability}% Available</Badge>
                      </Group>
                    </Card>
                  ))}
                </Stack>
              </Box>
            )}
            
            <Group position="right" mt="md">
              <Button variant="outline" color="gray" onClick={() => setAssignmentModalOpen(false)}>
                Cancel
              </Button>
              <Button 
                variant="filled" 
                color="blue" 
                onClick={handleAssignTask} 
                disabled={!selectedAgent}
                loading={isLoading}
              >
                Assign Task
              </Button>
            </Group>
          </Stack>
        )}
      </Modal>
    </Box>
  );
};

export default TaskAssignmentSystem; 