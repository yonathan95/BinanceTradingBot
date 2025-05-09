import React from 'react';
import { Card, Text, Group, Badge, Avatar, Box, Tooltip, Grid } from '@mantine/core';
import { useDrag } from 'react-dnd';
import { IconCalendarDue, IconMessage, IconPriority, IconTag } from '../layout/icons';

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
  tags: string[];
  comments: {
    id: string;
    author: {
      id: string;
      name: string;
      type: 'human' | 'agent';
    };
    content: string;
    timestamp: string;
  }[];
  createdAt: string;
  updatedAt: string;
}

interface TaskCardProps {
  task: Task;
  onClick: () => void;
}

const TaskCard: React.FC<TaskCardProps> = ({ task, onClick }) => {
  const [{ isDragging }, drag] = useDrag({
    type: 'task',
    item: { id: task.id },
    collect: (monitor) => ({
      isDragging: !!monitor.isDragging(),
    }),
  });

  // Updated priority colors to match theme
  const priorityColors = {
    High: '#ea4335', // Google red
    Medium: '#fbbc05', // Google yellow
    Low: '#4285f4',   // Google blue
  };

  // Format date to display as "Jul 15" or "Yesterday" etc.
  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const isToday = date.toDateString() === now.toDateString();
    const isYesterday = new Date(now.setDate(now.getDate() - 1)).toDateString() === date.toDateString();
    
    if (isToday) return 'Today';
    if (isYesterday) return 'Yesterday';
    
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  };

  // Get status color based on task status
  const getStatusColor = () => {
    switch (task.status) {
      case 'To Do':
        return '#4285f4'; // Blue
      case 'In Progress':
        return '#fbbc05'; // Yellow/Orange
      case 'Testing':
        return '#9c27b0'; // Purple  
      case 'Done':
        return '#34a853'; // Green
      default:
        return '#1a73e8'; // Default blue
    }
  };

  return (
    <Card
      ref={drag}
      shadow="sm"
      padding="sm"
      radius="lg"
      onClick={onClick}
      withBorder
      style={{
        opacity: isDragging ? 0.5 : 1,
        cursor: 'pointer',
        transition: 'all 0.2s ease',
        backgroundColor: '#2d2d2d',
        position: 'relative',
        overflow: 'visible',
        boxShadow: '0 4px 8px rgba(0,0,0,0.2)',
        transform: 'translateY(0)',
        border: `1px solid ${getStatusColor()}50`,
        '&:hover': {
          transform: 'translateY(-2px)',
          boxShadow: '0 6px 12px rgba(0,0,0,0.3)',
          borderColor: getStatusColor(),
        }
      }}
    >
      {/* Priority indicator */}
      <div style={{
        position: 'absolute',
        top: 0,
        left: 0,
        width: '4px',
        height: '100%',
        backgroundColor: priorityColors[task.priority as keyof typeof priorityColors],
        borderTopLeftRadius: '8px',
        borderBottomLeftRadius: '8px'
      }} />

      <Grid align="center" gutter="xs">
        <Grid.Col span={8}>
          <Text fw={600} lineClamp={2} style={{ marginLeft: '8px', color: '#ffffff' }}>{task.title}</Text>
        </Grid.Col>
        
        <Grid.Col span={4} style={{ textAlign: 'right' }}>
          {task.assignee && (
            <Tooltip label={`Assigned to: ${task.assignee.name}`}>
              <Avatar 
                size="sm" 
                radius="xl" 
                color={task.assignee.type === 'agent' ? 'violet' : 'blue'}
                style={{ border: '2px solid #2d2d2d', boxShadow: '0 2px 4px rgba(0,0,0,0.2)' }}
              >
                {task.assignee.name.charAt(0).toUpperCase()}
              </Avatar>
            </Tooltip>
          )}
        </Grid.Col>
      </Grid>

      <Box mt="xs">
        {task.tags.length > 0 && (
          <Group gap="xs" mb="xs" ml="xs">
            <IconTag size={14} color="#a0a0a0" />
            {task.tags.slice(0, 2).map((tag) => (
              <Badge 
                key={tag} 
                size="xs" 
                variant="light" 
                color="blue" 
                radius="xl" 
                style={{ backgroundColor: '#1a3464', color: '#a8c7fa' }}
              >
                {tag}
              </Badge>
            ))}
            {task.tags.length > 2 && (
              <Badge 
                size="xs" 
                variant="light" 
                color="gray" 
                radius="xl"
                style={{ backgroundColor: '#3c3c3c', color: '#b0b0b0' }}
              >
                +{task.tags.length - 2}
              </Badge>
            )}
          </Group>
        )}

        <Group justify="space-between" mt="xs" style={{ padding: '0 4px' }}>
          <Group gap="xs">
            <Tooltip label={`Priority: ${task.priority}`}>
              <Box style={{ display: 'flex', alignItems: 'center' }}>
                <Text size="xs" fw={500} style={{ 
                  color: priorityColors[task.priority as keyof typeof priorityColors],
                }}>
                  {task.priority}
                </Text>
              </Box>
            </Tooltip>
            
            {task.comments && task.comments.length > 0 && (
              <Tooltip label={`${task.comments.length} comments`}>
                <Group gap={4}>
                  <IconMessage size={14} color="#a0a0a0" />
                  <Text size="xs" c="gray.4">{task.comments.length}</Text>
                </Group>
              </Tooltip>
            )}
          </Group>

          <Group gap="xs">
            {task.dueDate && (
              <Tooltip label={`Due: ${new Date(task.dueDate).toLocaleDateString()}`}>
                <Group gap={4}>
                  <IconCalendarDue size={14} color="#a0a0a0" />
                  <Text size="xs" c="gray.4">{formatDate(task.dueDate)}</Text>
                </Group>
              </Tooltip>
            )}
          </Group>
        </Group>
      </Box>
    </Card>
  );
};

export default TaskCard; 