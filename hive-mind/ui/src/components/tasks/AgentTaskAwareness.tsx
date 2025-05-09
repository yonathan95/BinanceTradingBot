import React, { useState } from 'react';
import { 
  Box, 
  Title, 
  Text, 
  Group, 
  Paper, 
  Badge, 
  Progress, 
  Card, 
  Avatar, 
  Button, 
  Textarea, 
  Modal,
  Divider,
  Grid,
  Select,
  ActionIcon
} from '@mantine/core';
import { 
  IconBrain, 
  IconMessage, 
  IconCalendarDue,
  IconClipboardList,
  IconArrowMoveHorizontal
} from '../layout/icons';

interface TaskComment {
  id: string;
  author: {
    id: string;
    name: string;
    type: 'human' | 'agent';
  };
  content: string;
  timestamp: string;
}

interface Task {
  id: string;
  title: string;
  description: string;
  assignee: {
    id: string;
    name: string;
    type: 'human' | 'agent';
  };
  priority: string;
  status: string;
  dueDate: string;
  timeEstimate: number;
  progress: number;
  tags: string[];
  comments: TaskComment[];
  createdAt: string;
  updatedAt: string;
}

interface AgentTaskAwarenessProps {
  agentId: string;
  agentName: string;
  agentType: 'human' | 'agent';
  managerRole: boolean;
  assignedTasks: Task[];
  statusOptions: string[];
  onStatusChange: (taskId: string, newStatus: string) => void;
  onProgressUpdate: (taskId: string, progress: number) => void;
  onAddComment: (taskId: string, comment: string) => void;
}

const AgentTaskAwareness: React.FC<AgentTaskAwarenessProps> = ({ 
  agentId,
  agentName,
  agentType,
  managerRole,
  assignedTasks,
  statusOptions,
  onStatusChange,
  onProgressUpdate,
  onAddComment
}) => {
  const [selectedTask, setSelectedTask] = useState<Task | null>(null);
  const [updateModalOpened, setUpdateModalOpened] = useState(false);
  const [progressValue, setProgressValue] = useState(0);
  const [statusValue, setStatusValue] = useState('');
  const [commentValue, setCommentValue] = useState('');

  const handleOpenUpdateModal = (task: Task) => {
    setSelectedTask(task);
    setProgressValue(task.progress);
    setStatusValue(task.status);
    setCommentValue('');
    setUpdateModalOpened(true);
  };

  const handleSubmitUpdate = () => {
    if (!selectedTask) return;

    if (progressValue !== selectedTask.progress) {
      onProgressUpdate(selectedTask.id, progressValue);
    }

    if (statusValue !== selectedTask.status) {
      onStatusChange(selectedTask.id, statusValue);
    }

    if (commentValue.trim()) {
      onAddComment(selectedTask.id, commentValue);
    }

    setUpdateModalOpened(false);
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString();
  };

  const getDueStatus = (dueDate: string) => {
    const now = new Date();
    const due = new Date(dueDate);
    const diffTime = due.getTime() - now.getTime();
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));

    if (diffDays < 0) return 'overdue';
    if (diffDays <= 2) return 'due-soon';
    return 'on-track';
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'High': return '#ea4335';
      case 'Medium': return '#fbbc05';
      case 'Low': return '#4285f4';
      default: return '#1a73e8';
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'To Do': return '#4285f4';
      case 'In Progress': return '#fbbc05';
      case 'Testing': return '#9c27b0';
      case 'Done': return '#34a853';
      default: return '#1a73e8';
    }
  };

  const getProgressColor = (progress: number) => {
    if (progress < 25) return '#ea4335';
    if (progress < 50) return '#fbbc05';
    if (progress < 75) return '#4285f4';
    return '#34a853';
  };

  return (
    <Box>
      <Paper p="md" radius="md" style={{ backgroundColor: '#202124', border: '1px solid #333', marginBottom: '20px' }}>
        <Group justify="apart" mb="md">
          <Group>
            {agentType === 'agent' ? (
              <IconBrain size={24} color="#9c27b0" />
            ) : (
              <Avatar radius="xl" size="sm">{agentName.charAt(0).toUpperCase()}</Avatar>
            )}
            <Title order={4} style={{ color: 'white' }}>
              {agentName}'s Tasks {managerRole && '(Manager)'}
            </Title>
          </Group>
          
          <Badge size="lg" style={{ backgroundColor: agentType === 'agent' ? '#9c27b0' : '#4285f4', color: 'white' }}>
            {agentType === 'agent' ? 'AI Agent' : 'Human'}
          </Badge>
        </Group>
        
        <Box>
          <Text fw={500} size="lg" style={{ color: 'white', marginBottom: '16px' }}>
            <IconClipboardList size={18} style={{ marginRight: '8px', verticalAlign: 'middle' }} />
            Assigned Tasks ({assignedTasks.length})
          </Text>
          
          <Grid>
            {assignedTasks.length > 0 ? (
              assignedTasks.map(task => (
                <Grid.Col span={6} key={task.id}>
                  <Card 
                    padding="md" 
                    radius="md"
                    style={{ 
                      backgroundColor: '#2d2d2d', 
                      border: '1px solid #444',
                      height: '100%',
                      position: 'relative',
                      overflow: 'visible'
                    }}
                  >
                    <div style={{
                      position: 'absolute',
                      top: 0,
                      left: 0,
                      width: '4px',
                      height: '100%',
                      backgroundColor: getPriorityColor(task.priority),
                      borderTopLeftRadius: '8px',
                      borderBottomLeftRadius: '8px'
                    }} />
                    
                    <Box mb="md">
                      <Group justify="apart">
                        <Badge style={{ backgroundColor: getStatusColor(task.status), color: 'white' }}>
                          {task.status}
                        </Badge>
                        <Badge 
                          style={{ 
                            backgroundColor: 
                              getDueStatus(task.dueDate) === 'overdue' ? '#ea4335' : 
                              getDueStatus(task.dueDate) === 'due-soon' ? '#fbbc05' : '#34a853',
                            color: 'white'
                          }}
                        >
                          {getDueStatus(task.dueDate) === 'overdue' ? 'Overdue' : 
                           getDueStatus(task.dueDate) === 'due-soon' ? 'Due Soon' : 'On Track'}
                        </Badge>
                      </Group>
                      
                      <Text fw={600} size="md" style={{ color: 'white', margin: '12px 0' }}>
                        {task.title}
                      </Text>
                      
                      <Text size="sm" lineClamp={2} style={{ color: '#aaa', marginBottom: '12px' }}>
                        {task.description}
                      </Text>
                      
                      <Group mt="md" mb="md">
                        {task.tags.slice(0, 3).map(tag => (
                          <Badge key={tag} size="sm" style={{ backgroundColor: '#1a3464', color: '#a8c7fa' }}>
                            {tag}
                          </Badge>
                        ))}
                        {task.tags.length > 3 && (
                          <Badge size="sm" style={{ backgroundColor: '#3c3c3c', color: '#b0b0b0' }}>
                            +{task.tags.length - 3}
                          </Badge>
                        )}
                      </Group>
                    </Box>
                    
                    <Divider my="sm" color="#444" />
                    
                    <Box my="md">
                      <Group mb="xs">
                        <Text size="sm" style={{ color: '#aaa' }}>Progress:</Text>
                        <Text size="sm" style={{ color: 'white', fontWeight: 500 }}>{task.progress}%</Text>
                      </Group>
                      <Progress 
                        value={task.progress} 
                        size="md"
                        radius="xl"
                        color={getProgressColor(task.progress)}
                      />
                    </Box>
                    
                    <Group justify="apart" mt="md">
                      <Group>
                        <IconCalendarDue size={16} color="#aaa" />
                        <Text size="xs" style={{ color: '#aaa' }}>
                          Due: {formatDate(task.dueDate)}
                        </Text>
                      </Group>
                      
                      <Group>
                        <IconMessage size={16} color="#aaa" />
                        <Text size="xs" style={{ color: '#aaa' }}>
                          {task.comments.length} comment{task.comments.length !== 1 ? 's' : ''}
                        </Text>
                      </Group>
                    </Group>
                    
                    <Button 
                      fullWidth 
                      variant="outline" 
                      mt="md"
                      onClick={() => handleOpenUpdateModal(task)}
                      style={{ borderColor: '#4285f4', color: '#4285f4' }}
                    >
                      Update Progress
                    </Button>
                  </Card>
                </Grid.Col>
              ))
            ) : (
              <Grid.Col span={12}>
                <Paper p="xl" radius="md" style={{ backgroundColor: '#2d2d2d', border: '1px solid #444', textAlign: 'center' }}>
                  <Text style={{ color: '#aaa' }}>No tasks assigned yet.</Text>
                </Paper>
              </Grid.Col>
            )}
          </Grid>
        </Box>
      </Paper>
      
      <Modal
        opened={updateModalOpened}
        onClose={() => setUpdateModalOpened(false)}
        title={selectedTask ? `Update: ${selectedTask.title}` : 'Update Task'}
        size="lg"
        styles={{
          root: {
            backgroundColor: 'rgba(0, 0, 0, 0.7)',
          },
          content: {
            backgroundColor: '#202124',
            color: 'white',
          },
          header: {
            backgroundColor: '#202124',
            color: 'white',
            borderBottom: '1px solid #333',
          },
          title: {
            color: 'white',
            fontWeight: 'bold',
          },
          close: {
            color: 'white',
            '&:hover': {
              backgroundColor: '#333',
            },
          },
        }}
      >
        {selectedTask && (
          <Box>
            <Group mb="md">
              <Text size="sm" fw={500} style={{ color: '#aaa', width: '120px' }}>
                Update Progress:
              </Text>
              <Group style={{ flex: 1 }}>
                {[0, 25, 50, 75, 100].map(value => (
                  <Button
                    key={value}
                    variant={progressValue === value ? 'filled' : 'outline'}
                    size="xs"
                    onClick={() => setProgressValue(value)}
                    style={{
                      backgroundColor: progressValue === value ? getProgressColor(value) : 'transparent',
                      borderColor: getProgressColor(value),
                      color: progressValue === value ? 'white' : getProgressColor(value),
                      flex: 1
                    }}
                  >
                    {value}%
                  </Button>
                ))}
              </Group>
            </Group>
            
            <Group mb="md">
              <Text size="sm" fw={500} style={{ color: '#aaa', width: '120px' }}>
                Update Status:
              </Text>
              <Select
                data={statusOptions.map(status => ({ value: status, label: status }))}
                value={statusValue}
                onChange={(value) => value && setStatusValue(value)}
                style={{ flex: 1 }}
                styles={{
                  input: {
                    backgroundColor: '#333',
                    color: 'white',
                    border: '1px solid #444',
                  }
                }}
              />
            </Group>
            
            <Box mb="md">
              <Text size="sm" fw={500} style={{ color: '#aaa', marginBottom: '8px' }}>
                Add Comment:
              </Text>
              <Textarea
                placeholder="Add details about your progress..."
                minRows={4}
                value={commentValue}
                onChange={(e) => setCommentValue(e.target.value)}
                styles={{
                  input: {
                    backgroundColor: '#333',
                    color: 'white',
                    border: '1px solid #444',
                  }
                }}
              />
            </Box>
            
            <Group justify="right" mt="xl">
              <Button
                variant="outline"
                onClick={() => setUpdateModalOpened(false)}
                style={{ borderColor: '#444', color: 'white' }}
              >
                Cancel
              </Button>
              <Button
                onClick={handleSubmitUpdate}
                style={{ backgroundColor: '#4285f4' }}
              >
                Submit Update
              </Button>
            </Group>
          </Box>
        )}
      </Modal>
    </Box>
  );
};

export default AgentTaskAwareness; 