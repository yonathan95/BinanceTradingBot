import React, { useState, useEffect } from 'react';
import { Box, Title, Group, Button, ActionIcon, TextInput, Select, Paper, ScrollArea } from '@mantine/core';
import { DndProvider } from 'react-dnd';
import { HTML5Backend } from 'react-dnd-html5-backend';
import { IconClipboardList, IconPlus, IconSearch } from '../components/layout/icons';
import axios from 'axios';
import BoardColumn from '../components/tasks/BoardColumn';
import TaskModal from '../components/tasks/TaskModal';

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

interface Column {
  id: string;
  title: string;
  tasks: Task[];
}

const TaskBoard: React.FC = () => {
  const [columns, setColumns] = useState<Column[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [createTaskModalOpen, setCreateTaskModalOpen] = useState(false);
  const [editTaskModalOpen, setEditTaskModalOpen] = useState(false);
  const [currentTask, setCurrentTask] = useState<Task | undefined>(undefined);
  const [searchQuery, setSearchQuery] = useState('');
  const [filterPriority, setFilterPriority] = useState<string | null>(null);
  const [filterAssignee, setFilterAssignee] = useState<string | null>(null);
  const [filterTag, setFilterTag] = useState<string | null>(null);

  // Mock members for development
  const members = [
    { id: 'usr-001', name: 'John Doe', type: 'human', value: 'usr-001', label: 'John Doe' },
    { id: 'usr-002', name: 'Jane Smith', type: 'human', value: 'usr-002', label: 'Jane Smith' },
    { id: 'usr-003', name: 'Alex Johnson', type: 'human', value: 'usr-003', label: 'Alex Johnson' },
    { id: 'agent-001', name: 'Code Agent', type: 'agent', value: 'agent-001', label: 'Code Agent' },
    { id: 'agent-002', name: 'UI Helper', type: 'agent', value: 'agent-002', label: 'UI Helper' },
    { id: 'agent-003', name: 'API Tester', type: 'agent', value: 'agent-003', label: 'API Tester' },
  ];

  const statusOptions = columns.map(column => ({
    value: column.title,
    label: column.title
  }));

  const tagOptions = Array.from(
    new Set(
      columns
        .flatMap(column => column.tasks)
        .flatMap(task => task.tags)
    )
  ).map(tag => ({
    value: tag,
    label: tag
  }));

  useEffect(() => {
    const fetchTasks = async () => {
      try {
        setLoading(true);
        const response = await axios.get('/mock-api/api/tasks/board.json');
        setColumns(response.data);
        setError('');
      } catch (err) {
        console.error('Error fetching task board data:', err);
        setError('Failed to load tasks. Please try again later.');
      } finally {
        setLoading(false);
      }
    };

    fetchTasks();
  }, []);

  const handleCreateTask = (newTask: Partial<Task>) => {
    // In a real app, this would call an API to create the task
    const taskId = `task-${Date.now()}`;
    const now = new Date().toISOString();
    
    const fullTask: Task = {
      id: taskId,
      title: newTask.title || '',
      description: newTask.description || '',
      assignee: newTask.assignee || {
        id: '',
        name: '',
        type: 'human'
      },
      priority: newTask.priority || 'Medium',
      status: newTask.status || 'To Do',
      dueDate: newTask.dueDate || now,
      timeEstimate: newTask.timeEstimate || 0,
      tags: newTask.tags || [],
      comments: [],
      createdAt: now,
      updatedAt: now
    };

    // Find the column that matches the task status
    const targetColumnIndex = columns.findIndex(column => column.title === fullTask.status);
    if (targetColumnIndex >= 0) {
      const newColumns = [...columns];
      newColumns[targetColumnIndex].tasks.push(fullTask);
      setColumns(newColumns);
    }
  };

  const handleUpdateTask = (updatedTask: Partial<Task>) => {
    if (!updatedTask.id) return;

    // Find the task in the columns
    let found = false;
    const newColumns = columns.map(column => {
      const taskIndex = column.tasks.findIndex(task => task.id === updatedTask.id);
      if (taskIndex >= 0) {
        found = true;
        
        // Create updated task
        const updatedTaskFull = {
          ...column.tasks[taskIndex],
          ...updatedTask,
          updatedAt: new Date().toISOString()
        };
        
        // If status has changed, we need to move the task to a different column
        if (updatedTask.status && updatedTask.status !== column.tasks[taskIndex].status) {
          // Remove from current column
          const newTasks = [...column.tasks];
          newTasks.splice(taskIndex, 1);
          
          return {
            ...column,
            tasks: newTasks
          };
        }
        
        // Update in current column
        const newTasks = [...column.tasks];
        newTasks[taskIndex] = updatedTaskFull;
        
        return {
          ...column,
          tasks: newTasks
        };
      }
      return column;
    });
    
    // If status has changed, add the task to the new column
    if (found && updatedTask.status) {
      const targetColumnIndex = newColumns.findIndex(column => column.title === updatedTask.status);
      if (targetColumnIndex >= 0) {
        // Find the original task
        const originalTask = columns
          .flatMap(column => column.tasks)
          .find(task => task.id === updatedTask.id);
        
        if (originalTask) {
          // Create the updated task
          const updatedTaskFull = {
            ...originalTask,
            ...updatedTask,
            updatedAt: new Date().toISOString()
          };
          
          // Add to new column
          newColumns[targetColumnIndex].tasks.push(updatedTaskFull);
        }
      }
    }
    
    setColumns(newColumns);
  };

  const handleDragDrop = (taskId: string, targetColumnId: string) => {
    // Find the task
    let taskToMove: Task | undefined;
    let sourceColumnIndex = -1;
    let sourceTaskIndex = -1;

    columns.forEach((column, colIndex) => {
      const taskIndex = column.tasks.findIndex(task => task.id === taskId);
      if (taskIndex >= 0) {
        taskToMove = column.tasks[taskIndex];
        sourceColumnIndex = colIndex;
        sourceTaskIndex = taskIndex;
      }
    });

    if (!taskToMove) return;

    // Find the target column
    const targetColumnIndex = columns.findIndex(column => column.id === targetColumnId);
    if (targetColumnIndex < 0) return;

    // Update task status
    const updatedTask = {
      ...taskToMove,
      status: columns[targetColumnIndex].title,
      updatedAt: new Date().toISOString()
    };

    // Remove from source column
    const newColumns = [...columns];
    newColumns[sourceColumnIndex].tasks.splice(sourceTaskIndex, 1);

    // Add to target column
    newColumns[targetColumnIndex].tasks.push(updatedTask);

    setColumns(newColumns);
  };

  const handleTaskClick = (task: Task) => {
    setCurrentTask(task);
    setEditTaskModalOpen(true);
  };

  const handleCreateTaskClick = () => {
    setCurrentTask(undefined);
    setCreateTaskModalOpen(true);
  };

  const getFilteredColumns = () => {
    return columns.map(column => {
      const filteredTasks = column.tasks.filter(task => {
        // Apply search filter
        const matchesSearch = searchQuery === '' || 
          task.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
          task.description.toLowerCase().includes(searchQuery.toLowerCase());

        // Apply priority filter
        const matchesPriority = !filterPriority || 
          task.priority === filterPriority;

        // Apply assignee filter
        const matchesAssignee = !filterAssignee || 
          task.assignee?.id === filterAssignee;

        // Apply tag filter
        const matchesTag = !filterTag || 
          task.tags.includes(filterTag);

        return matchesSearch && matchesPriority && matchesAssignee && matchesTag;
      });

      return {
        ...column,
        tasks: filteredTasks
      };
    });
  };

  const filteredColumns = getFilteredColumns();

  return (
    <Box p="md">
      <Group position="apart" mb="lg">
        <Group>
          <IconClipboardList size={24} />
          <Title order={2}>Task Board</Title>
        </Group>
        
        <Button
          leftIcon={<IconPlus size={16} />}
          onClick={handleCreateTaskClick}
        >
          New Task
        </Button>
      </Group>
      
      <Paper p="md" mb="md" shadow="xs">
        <Group>
          <TextInput
            placeholder="Search tasks..."
            icon={<IconSearch size={16} />}
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            style={{ flex: 1 }}
          />
          
          <Select
            placeholder="Priority"
            clearable
            data={[
              { value: 'High', label: 'High' },
              { value: 'Medium', label: 'Medium' },
              { value: 'Low', label: 'Low' },
            ]}
            value={filterPriority}
            onChange={setFilterPriority}
            style={{ width: 150 }}
          />
          
          <Select
            placeholder="Assignee"
            clearable
            data={members.map(member => ({
              value: member.id,
              label: member.name
            }))}
            value={filterAssignee}
            onChange={setFilterAssignee}
            style={{ width: 150 }}
          />
          
          <Select
            placeholder="Tag"
            clearable
            data={tagOptions}
            value={filterTag}
            onChange={setFilterTag}
            style={{ width: 150 }}
          />
        </Group>
      </Paper>
      
      <ScrollArea h="calc(100vh - 220px)" type="auto">
        <DndProvider backend={HTML5Backend}>
          <Group align="flex-start" spacing="md" noWrap>
            {filteredColumns.map(column => (
              <BoardColumn
                key={column.id}
                id={column.id}
                title={column.title}
                tasks={column.tasks}
                onDrop={handleDragDrop}
                onTaskClick={handleTaskClick}
              />
            ))}
          </Group>
        </DndProvider>
      </ScrollArea>
      
      {/* Create Task Modal */}
      <TaskModal
        opened={createTaskModalOpen}
        onClose={() => setCreateTaskModalOpen(false)}
        onSave={handleCreateTask}
        statusOptions={statusOptions}
        tagOptions={tagOptions}
        members={members}
      />
      
      {/* Edit Task Modal */}
      {currentTask && (
        <TaskModal
          opened={editTaskModalOpen}
          onClose={() => setEditTaskModalOpen(false)}
          task={currentTask}
          onSave={handleUpdateTask}
          statusOptions={statusOptions}
          tagOptions={tagOptions}
          members={members}
        />
      )}
    </Box>
  );
};

export default TaskBoard; 