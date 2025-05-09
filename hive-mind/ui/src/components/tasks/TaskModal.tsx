import React, { useState, useEffect } from 'react';
import { 
  Modal, 
  TextInput, 
  Textarea, 
  Button, 
  Group, 
  Select, 
  MultiSelect, 
  Box, 
  Text, 
  Avatar, 
  ActionIcon,
  Divider,
  Stack,
  NumberInput
} from '@mantine/core';
import { IconCalendarDue, IconPriority, IconTag } from '../layout/icons';

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

interface Member {
  id: string;
  name: string;
  type: 'human' | 'agent';
  role?: string;
  value: string;
  label: string;
}

interface TaskModalProps {
  opened: boolean;
  onClose: () => void;
  task?: Task;
  onSave: (task: Partial<Task>) => void;
  statusOptions: { value: string; label: string }[];
  tagOptions: { value: string; label: string }[];
  members: Member[];
}

const TaskModal: React.FC<TaskModalProps> = ({ 
  opened, 
  onClose, 
  task, 
  onSave, 
  statusOptions,
  tagOptions,
  members
}) => {
  // Ensure task has all required properties before using it
  const safeTask = task ? {
    ...task,
    title: task.title || '',
    description: task.description || '',
    priority: task.priority || 'Medium',
    status: task.status || '',
    assignee: task.assignee || { id: '', name: '', type: 'human' },
    dueDate: task.dueDate || '',
    timeEstimate: task.timeEstimate || 0,
    tags: task.tags || [],
    comments: task.comments || []
  } : undefined;
  
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [priority, setPriority] = useState('Medium');
  const [status, setStatus] = useState('');
  const [assigneeId, setAssigneeId] = useState('');
  const [dueDate, setDueDate] = useState('');
  const [timeEstimate, setTimeEstimate] = useState(0);
  const [selectedTags, setSelectedTags] = useState<string[]>([]);
  const [newComment, setNewComment] = useState('');

  // Load task data into form when task changes
  useEffect(() => {
    if (safeTask) {
      setTitle(safeTask.title);
      setDescription(safeTask.description);
      setPriority(safeTask.priority);
      setStatus(safeTask.status || statusOptions[0]?.value || 'To Do');
      setAssigneeId(safeTask.assignee?.id || '');
      setDueDate(safeTask.dueDate ? new Date(safeTask.dueDate).toISOString().split('T')[0] : '');
      setTimeEstimate(safeTask.timeEstimate);
      setSelectedTags(safeTask.tags);
    } else {
      // Default values for new task
      setTitle('');
      setDescription('');
      setPriority('Medium');
      setStatus(statusOptions[0]?.value || 'To Do');
      setAssigneeId('');
      setDueDate('');
      setTimeEstimate(0);
      setSelectedTags([]);
    }
    setNewComment('');
  }, [safeTask, statusOptions]);

  const handleSubmit = () => {
    const updatedTask: Partial<Task> = {
      title,
      description,
      priority,
      status,
      dueDate: dueDate ? new Date(dueDate).toISOString() : undefined,
      timeEstimate,
      tags: selectedTags,
      ...(assigneeId && {
        assignee: members.find(m => m.id === assigneeId)
      }),
    };

    if (safeTask?.id) {
      updatedTask.id = safeTask.id;
    }

    onSave(updatedTask);
    onClose();
  };

  const isFormValid = title.trim().length > 0;

  return (
    <Modal 
      opened={opened} 
      onClose={onClose} 
      title={safeTask ? "Edit Task" : "Create New Task"} 
      size="lg"
      radius="md"
    >
      <Stack>
        <TextInput
          label="Title"
          placeholder="Task title"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          required
          radius="md"
        />

        <Textarea
          label="Description"
          placeholder="Task description"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          minRows={3}
          radius="md"
        />

        <Group grow>
          <Select
            label="Priority"
            placeholder="Select priority"
            value={priority}
            onChange={(value) => setPriority(value || 'Medium')}
            data={[
              { value: 'High', label: 'High' },
              { value: 'Medium', label: 'Medium' },
              { value: 'Low', label: 'Low' },
            ]}
            leftSection={<IconPriority size={16} />}
            radius="md"
          />

          <Select
            label="Status"
            placeholder="Select status"
            value={status}
            onChange={(value) => setStatus(value || statusOptions[0]?.value || 'To Do')}
            data={statusOptions}
            radius="md"
          />
        </Group>

        <Group grow>
          <Select
            label="Assignee"
            placeholder="Assign to"
            value={assigneeId}
            onChange={(value) => setAssigneeId(value || '')}
            data={(members || []).map(member => ({
              value: member.id,
              label: member.name,
              group: member.type === 'human' ? 'Team Members' : 'Agents'
            }))}
            clearable
            radius="md"
          />

          <NumberInput
            label="Time Estimate (hours)"
            placeholder="Time estimate"
            value={timeEstimate}
            onChange={(value) => setTimeEstimate(value || 0)}
            min={0}
            radius="md"
          />
        </Group>

        <TextInput
          label="Due Date"
          placeholder="YYYY-MM-DD"
          type="date"
          value={dueDate}
          onChange={(e) => setDueDate(e.target.value)}
          leftSection={<IconCalendarDue size={16} />}
          radius="md"
        />

        <MultiSelect
          label="Tags"
          placeholder="Select tags"
          value={selectedTags}
          onChange={setSelectedTags}
          data={tagOptions}
          searchable
          creatable
          leftSection={<IconTag size={16} />}
          getCreateLabel={(query) => `+ Create "${query}"`}
          onCreate={(query) => {
            const item = { value: query, label: query };
            return item;
          }}
          radius="md"
        />

        {safeTask && safeTask.comments && safeTask.comments.length > 0 && (
          <>
            <Divider my="md" label="Comments" labelPosition="center" />
            
            <Stack>
              {safeTask.comments.map((comment) => (
                <Box key={comment.id} p="xs" style={{ backgroundColor: '#f8f9fa', borderRadius: '8px' }}>
                  <Group mb="xs">
                    <Avatar 
                      size="sm" 
                      radius="xl"
                      color={comment.author.type === 'agent' ? 'indigo' : 'blue'}
                    >
                      {comment.author.name.charAt(0).toUpperCase()}
                    </Avatar>
                    <Box>
                      <Text size="sm" fw={500}>{comment.author.name}</Text>
                      <Text size="xs" c="dimmed">
                        {new Date(comment.timestamp).toLocaleString()}
                      </Text>
                    </Box>
                  </Group>
                  <Text size="sm">{comment.content}</Text>
                </Box>
              ))}

              <Textarea
                placeholder="Add a comment..."
                value={newComment}
                onChange={(e) => setNewComment(e.target.value)}
                minRows={2}
                radius="md"
              />
            </Stack>
          </>
        )}

        <Group justify="flex-end" mt="md">
          <Button variant="outline" onClick={onClose} radius="md">Cancel</Button>
          <Button 
            onClick={handleSubmit} 
            disabled={!isFormValid}
            radius="md"
            style={{ backgroundColor: '#1a73e8' }}
          >
            {safeTask ? 'Update Task' : 'Create Task'}
          </Button>
        </Group>
      </Stack>
    </Modal>
  );
};

export default TaskModal; 