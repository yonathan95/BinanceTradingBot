import React, { useState } from 'react';
import { 
  Modal, 
  Box, 
  Text, 
  Divider, 
  Group, 
  Badge, 
  Avatar, 
  Textarea,
  Button,
  Stack,
  Paper,
  ScrollArea
} from '@mantine/core';
import { IconCalendarDue, IconPriority, IconTag, IconClock } from '../layout/icons';

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
  tags: string[];
  comments: TaskComment[];
  createdAt: string;
  updatedAt: string;
}

interface TaskDetailViewProps {
  task: Task;
  opened: boolean;
  onClose: () => void;
  onEditClick: () => void;
}

const TaskDetailView: React.FC<TaskDetailViewProps> = ({ task, opened, onClose, onEditClick }) => {
  const [newComment, setNewComment] = useState('');

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString();
  };

  // Priority colors
  const priorityColors = {
    High: '#ea4335',
    Medium: '#fbbc05',
    Low: '#4285f4',
  };

  // Get status color based on task status
  const getStatusColor = () => {
    switch (task.status) {
      case 'To Do':
        return '#4285f4';
      case 'In Progress':
        return '#fbbc05';
      case 'Testing':
        return '#9c27b0';
      case 'Done':
        return '#34a853';
      default:
        return '#1a73e8';
    }
  };

  const handleAddComment = () => {
    // In a real app, this would save the comment to the backend
    console.log("Adding comment:", newComment);
    setNewComment('');
  };

  return (
    <Modal 
      opened={opened} 
      onClose={onClose} 
      title={`Task: ${task.title}`}
      size="xl"
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
      <ScrollArea h="calc(100vh - 200px)">
        <Box p="md">
          <Paper p="md" radius="md" style={{ backgroundColor: '#2d2d2d', border: '1px solid #333' }}>
            <Group justify="apart" mb="md">
              <Badge color="blue" size="lg" style={{ backgroundColor: getStatusColor(), color: 'white' }}>
                {task.status}
              </Badge>
              <Badge color="red" size="lg" style={{ backgroundColor: priorityColors[task.priority as keyof typeof priorityColors], color: 'white' }}>
                {task.priority} Priority
              </Badge>
            </Group>

            <Text size="lg" fw={500} mb="xs" style={{ color: 'white' }}>{task.title}</Text>
            <Text style={{ color: '#ccc', whiteSpace: 'pre-wrap' }}>{task.description}</Text>

            <Divider my="md" color="#444" />

            <Group mb="md">
              <Box>
                <Text size="sm" fw={500} style={{ color: '#aaa' }}>Assignee</Text>
                <Group mt={5}>
                  <Avatar 
                    size="sm" 
                    radius="xl" 
                    color={task.assignee?.type === 'agent' ? 'violet' : 'blue'}
                  >
                    {task.assignee?.name.charAt(0).toUpperCase()}
                  </Avatar>
                  <Text style={{ color: 'white' }}>{task.assignee?.name}</Text>
                </Group>
              </Box>

              <Box>
                <Text size="sm" fw={500} style={{ color: '#aaa' }}>Due Date</Text>
                <Group mt={5}>
                  <IconCalendarDue size={16} color="#ddd" />
                  <Text style={{ color: 'white' }}>{task.dueDate ? formatDate(task.dueDate) : 'No due date'}</Text>
                </Group>
              </Box>

              <Box>
                <Text size="sm" fw={500} style={{ color: '#aaa' }}>Time Estimate</Text>
                <Group mt={5}>
                  <IconClock size={16} color="#ddd" />
                  <Text style={{ color: 'white' }}>{task.timeEstimate} hours</Text>
                </Group>
              </Box>
            </Group>

            {task.tags.length > 0 && (
              <Box mb="md">
                <Text size="sm" fw={500} mb={5} style={{ color: '#aaa' }}>Tags</Text>
                <Group>
                  {task.tags.map(tag => (
                    <Badge 
                      key={tag} 
                      style={{ backgroundColor: '#1a3464', color: '#a8c7fa' }}
                    >
                      {tag}
                    </Badge>
                  ))}
                </Group>
              </Box>
            )}

            <Group justify="apart" mt="lg">
              <Text size="sm" style={{ color: '#aaa' }}>
                Created: {formatDate(task.createdAt)}
              </Text>
              <Text size="sm" style={{ color: '#aaa' }}>
                Last Updated: {formatDate(task.updatedAt)}
              </Text>
            </Group>
          </Paper>

          <Divider my="lg" color="#444" label="Comments" labelPosition="center" />

          <Stack gap="md">
            {task.comments && task.comments.length > 0 ? (
              task.comments.map(comment => (
                <Paper key={comment.id} p="md" radius="md" style={{ backgroundColor: '#2d2d2d', border: '1px solid #333' }}>
                  <Group justify="apart" mb="xs">
                    <Group>
                      <Avatar 
                        size="sm" 
                        radius="xl" 
                        color={comment.author.type === 'agent' ? 'violet' : 'blue'}
                      >
                        {comment.author.name.charAt(0).toUpperCase()}
                      </Avatar>
                      <Text style={{ color: 'white' }}>{comment.author.name}</Text>
                    </Group>
                    <Text size="sm" style={{ color: '#aaa' }}>{formatDate(comment.timestamp)}</Text>
                  </Group>
                  <Text style={{ color: '#ccc', whiteSpace: 'pre-wrap' }}>{comment.content}</Text>
                </Paper>
              ))
            ) : (
              <Text ta="center" style={{ color: '#aaa' }}>No comments yet</Text>
            )}
          </Stack>

          <Paper p="md" mt="lg" radius="md" style={{ backgroundColor: '#2d2d2d', border: '1px solid #333' }}>
            <Textarea
              placeholder="Add a comment..."
              minRows={3}
              value={newComment}
              onChange={(e) => setNewComment(e.target.value)}
              mb="md"
              styles={{
                input: {
                  backgroundColor: '#333',
                  color: 'white',
                  border: '1px solid #444',
                }
              }}
            />
            <Group justify="right">
              <Button 
                onClick={handleAddComment}
                disabled={!newComment.trim()}
                style={{ backgroundColor: '#1a73e8' }}
              >
                Add Comment
              </Button>
            </Group>
          </Paper>

          <Group justify="right" mt="xl">
            <Button variant="outline" onClick={onClose} style={{ borderColor: '#444', color: 'white' }}>
              Close
            </Button>
            <Button onClick={onEditClick} style={{ backgroundColor: '#1a73e8' }}>
              Edit Task
            </Button>
          </Group>
        </Box>
      </ScrollArea>
    </Modal>
  );
};

export default TaskDetailView; 