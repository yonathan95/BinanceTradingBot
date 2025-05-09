import React, { useState, useEffect } from 'react';
import { Box, Title, Group, Button, TextInput, Select, Paper, ScrollArea } from '@mantine/core';
import { DndProvider } from 'react-dnd';
import { HTML5Backend } from 'react-dnd-html5-backend';
import { IconClipboardList, IconPlus, IconSearch } from '../layout/icons';
import axios from 'axios';
import BoardColumn from './BoardColumn';
import TaskModal from './TaskModal';
import TaskDetailView from './TaskDetailView';
import TaskAssignmentSystem from './TaskAssignmentSystem';
import AgentTaskAwareness from './AgentTaskAwareness';

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
  progress?: number;
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

interface Member {
  id: string;
  name: string;
  type: 'human' | 'agent';
  role?: string;
  skills?: string[];
  availability?: number;
  assignedTasks?: number;
  value?: string;
  label?: string;
}

interface Agent {
  id: string;
  name: string;
  type: 'human' | 'agent';
  role: string;
  skills: string[];
  availability: number;
  assignedTasks: number;
}

interface WorkspaceTaskBoardProps {
  workspaceId: string;
  members: Member[];
}

const WorkspaceTaskBoard: React.FC<WorkspaceTaskBoardProps> = ({ workspaceId, members }) => {
  const [columns, setColumns] = useState<Column[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [createTaskModalOpen, setCreateTaskModalOpen] = useState(false);
  const [editTaskModalOpen, setEditTaskModalOpen] = useState(false);
  const [viewTaskModalOpen, setViewTaskModalOpen] = useState(false);
  const [currentTask, setCurrentTask] = useState<Task | undefined>(undefined);
  const [searchQuery, setSearchQuery] = useState('');
  const [filterPriority, setFilterPriority] = useState<string | null>(null);
  const [filterAssignee, setFilterAssignee] = useState<string | null>(null);
  const [filterTag, setFilterTag] = useState<string | null>(null);
  const [currentUserId, setCurrentUserId] = useState("usr-001"); // Simulated current user
  const [currentUserIsManager, setCurrentUserIsManager] = useState(true); // Simulated manager role
  const [showAgentView, setShowAgentView] = useState(false);
  const [selectedAgent, setSelectedAgent] = useState<string | null>(null);

  const statusOptions = columns.map(column => ({
    value: column.title,
    label: column.title
  }));

  const tagOptions = Array.from(
    new Set(
      columns
        .flatMap(column => column.tasks)
        .flatMap(task => task.tags || [])
    )
  ).map(tag => ({
    value: tag,
    label: tag
  }));

  // Format members for the task modal
  const formattedMembers = (members || []).map(member => ({
    ...member,
    value: member.id,
    label: member.name
  }));

  // Add progress to tasks
  const enhancedMembers: Agent[] = members.map(member => ({
    ...member,
    role: member.role || 'Team Member',
    skills: ['UI', 'Frontend', 'Backend', 'API', 'Security', 'UX', 'Filtering', 'Testing'].slice(0, Math.floor(Math.random() * 5) + 1),
    availability: Math.floor(Math.random() * 60) + 40, // 40-100% availability
    assignedTasks: Math.floor(Math.random() * 5)
  }));

  useEffect(() => {
    const fetchTasks = async () => {
      try {
        setLoading(true);
        // In a real implementation, this would fetch tasks for the specific workspace
        // e.g. `/api/workspaces/${workspaceId}/tasks/board`
        try {
          const response = await axios.get('/mock-api/api/tasks/board.json');
          // Process tasks to ensure all required properties exist
          const processedData = response.data.map((column: any) => ({
            ...column,
            tasks: column.tasks.map((task: any) => ({
              ...task,
              // Ensure all tasks have these properties to prevent undefined errors
              tags: task.tags || [],
              comments: task.comments || [],
              assignee: task.assignee || { id: '', name: '', type: 'human' },
              timeEstimate: task.timeEstimate || 0
            }))
          }));
          setColumns(processedData);
          setError('');
        } catch (mainErr) {
          // If the main path fails, use inline mock data
          console.error('Error fetching task board data, using inline mock data:', mainErr);
          setColumns([
            {
              id: "column-1",
              title: "To Do",
              tasks: [
                {
                  id: "task-1",
                  title: "Create responsive product card component",
                  description: "Design and implement a responsive product card component that works well on all screen sizes.",
                  assignee: { id: "usr-001", name: "John Doe", type: "human" },
                  priority: "Medium",
                  status: "To Do",
                  dueDate: "2023-07-15T00:00:00Z",
                  timeEstimate: 8,
                  tags: ["UI", "Frontend"],
                  comments: [],
                  createdAt: "2023-06-28T14:00:00Z",
                  updatedAt: "2023-07-01T10:30:00Z"
                },
                {
                  id: "task-3",
                  title: "Design and implement shopping cart functionality",
                  description: "Create a shopping cart that allows users to add, remove, and update quantities of products.",
                  assignee: { id: "usr-002", name: "Jane Smith", type: "human" },
                  priority: "High",
                  status: "To Do",
                  dueDate: "2023-07-20T00:00:00Z",
                  timeEstimate: 16,
                  tags: ["UI", "Frontend", "UX"],
                  comments: [],
                  createdAt: "2023-06-29T18:00:00Z",
                  updatedAt: "2023-06-29T18:00:00Z"
                }
              ]
            },
            {
              id: "column-2", 
              title: "In Progress",
              tasks: [
                {
                  id: "task-2",
                  title: "Implement product list page with filtering",
                  description: "Create the product listing page with filtering options for categories, price range, and other attributes.",
                  assignee: { id: "agent-002", name: "UI Helper", type: "agent" },
                  priority: "High",
                  status: "In Progress",
                  dueDate: "2023-07-10T00:00:00Z",
                  timeEstimate: 12,
                  tags: ["UI", "Frontend", "Filtering"],
                  comments: [],
                  createdAt: "2023-06-28T16:00:00Z",
                  updatedAt: "2023-07-02T10:15:00Z"
                }
              ]
            },
            {
              id: "column-3", 
              title: "Testing",
              tasks: [
                {
                  id: "task-4",
                  title: "Create RESTful API endpoints for products",
                  description: "Implement API endpoints for products including listing, detail, create, update, and delete operations.",
                  assignee: { id: "usr-004", name: "Sarah Wilson", type: "human" },
                  priority: "Medium",
                  status: "Testing",
                  dueDate: "2023-07-12T00:00:00Z",
                  timeEstimate: 10,
                  tags: ["API", "Backend"],
                  comments: [],
                  createdAt: "2023-06-30T11:00:00Z",
                  updatedAt: "2023-07-05T09:20:00Z"
                }
              ]
            },
            {
              id: "column-4",
              title: "Done",
              tasks: [
                {
                  id: "task-5",
                  title: "Implement user authentication API",
                  description: "Create APIs for user registration, login, and authentication.",
                  assignee: { id: "usr-003", name: "Alex Johnson", type: "human" },
                  priority: "High",
                  status: "Done",
                  dueDate: "2023-06-25T00:00:00Z",
                  timeEstimate: 20,
                  tags: ["API", "Backend", "Security"],
                  comments: [],
                  createdAt: "2023-06-15T09:00:00Z",
                  updatedAt: "2023-06-24T15:45:00Z"
                }
              ]
            }
          ]);
        }
      } catch (err) {
        console.error('Error in task board data handling:', err);
        setError('Failed to load tasks. Please try again later.');
      } finally {
        setLoading(false);
      }
    };

    fetchTasks();
  }, [workspaceId]);

  // Enhance tasks with progress value
  useEffect(() => {
    const newColumns = columns.map(column => {
      const newTasks = column.tasks.map(task => ({
        ...task,
        progress: task.status === 'Done' ? 100 : 
                 task.status === 'Testing' ? Math.floor(Math.random() * 30) + 70 : 
                 task.status === 'In Progress' ? Math.floor(Math.random() * 40) + 30 : 
                 Math.floor(Math.random() * 20)
      }));
      return { ...column, tasks: newTasks };
    });
    
    if (columns.length > 0 && newColumns[0].tasks.length > 0 && !('progress' in newColumns[0].tasks[0])) {
      setColumns(newColumns);
    }
  }, [columns]);

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
    setViewTaskModalOpen(true);
  };

  const handleEditTaskClick = () => {
    setViewTaskModalOpen(false);
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

  // Get all tasks (flattened from columns)
  const allTasks = columns.flatMap(column => column.tasks);
  
  // Get tasks assigned to selected agent
  const getAssignedTasks = (agentId: string) => {
    return allTasks.filter(task => task.assignee && task.assignee.id === agentId);
  };

  // Handle task status change
  const handleStatusChange = (taskId: string, newStatus: string) => {
    const task = allTasks.find(t => t.id === taskId);
    if (task) {
      handleUpdateTask({
        ...task,
        status: newStatus,
        updatedAt: new Date().toISOString()
      });
    }
  };

  // Handle task progress update
  const handleProgressUpdate = (taskId: string, progress: number) => {
    const task = allTasks.find(t => t.id === taskId);
    if (task) {
      handleUpdateTask({
        ...task,
        progress,
        updatedAt: new Date().toISOString()
      });
    }
  };

  // Handle adding comment to task
  const handleAddComment = (taskId: string, comment: string) => {
    const task = allTasks.find(t => t.id === taskId);
    if (task) {
      const now = new Date().toISOString();
      const newComment = {
        id: `comment-${Date.now()}`,
        author: {
          id: currentUserId,
          name: enhancedMembers.find(m => m.id === currentUserId)?.name || 'Current User',
          type: enhancedMembers.find(m => m.id === currentUserId)?.type || 'human'
        },
        content: comment,
        timestamp: now
      };
      
      handleUpdateTask({
        ...task,
        comments: [...task.comments, newComment],
        updatedAt: now
      });
    }
  };

  // Handle task assignment
  const handleAssignTask = (taskId: string, agentId: string) => {
    const task = allTasks.find(t => t.id === taskId);
    const agent = enhancedMembers.find(m => m.id === agentId);
    
    if (task && agent) {
      handleUpdateTask({
        ...task,
        assignee: {
          id: agent.id,
          name: agent.name,
          type: agent.type
        },
        updatedAt: new Date().toISOString()
      });
    }
  };

  // Get status options
  const taskStatusOptions = columns.map(column => column.title);

  if (loading) {
    return <div>Loading task board...</div>;
  }

  if (error) {
    return <div>{error}</div>;
  }

  return (
    <Box>
      <Group mb="lg" style={{ justifyContent: 'space-between' }}>
        <Group>
          <IconClipboardList size={24} />
          <Title order={3}>Tasks</Title>
        </Group>
        
        <Group>
          {currentUserIsManager && (
            <Button
              variant="outline"
              onClick={() => setShowAgentView(!showAgentView)}
              style={{ 
                borderColor: showAgentView ? '#34a853' : '#1a73e8',
                color: showAgentView ? '#34a853' : '#1a73e8',
                borderRadius: '20px',
                padding: '0 20px'
              }}
            >
              {showAgentView ? 'Show Task Board' : 'Show Agent Tasks'}
            </Button>
          )}
          
          <Button
            leftSection={<IconPlus size={16} />}
            onClick={handleCreateTaskClick}
            style={{ 
              backgroundColor: '#1a73e8',
              color: 'white',
              borderRadius: '20px',
              padding: '0 20px'
            }}
          >
            New Task
          </Button>
        </Group>
      </Group>
      
      {!showAgentView ? (
        <>
          <Paper p="md" mb="md" shadow="xs" style={{ borderRadius: '12px', backgroundColor: '#202124', border: '1px solid #333' }}>
            <Group>
              <TextInput
                placeholder="Search tasks..."
                leftSection={<IconSearch size={16} />}
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                style={{ flex: 1 }}
                radius="xl"
                styles={{
                  input: {
                    backgroundColor: '#333',
                    color: 'white',
                    '&::placeholder': {
                      color: '#aaa'
                    }
                  }
                }}
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
                radius="xl"
                styles={{
                  input: {
                    backgroundColor: '#333',
                    color: 'white'
                  },
                  dropdown: {
                    backgroundColor: '#333',
                    color: 'white'
                  }
                }}
              />
              
              <Select
                placeholder="Assignee"
                clearable
                data={formattedMembers.map(member => ({
                  value: member.id,
                  label: member.name
                }))}
                value={filterAssignee}
                onChange={setFilterAssignee}
                style={{ width: 150 }}
                radius="xl"
                styles={{
                  input: {
                    backgroundColor: '#333',
                    color: 'white'
                  },
                  dropdown: {
                    backgroundColor: '#333',
                    color: 'white'
                  }
                }}
              />
              
              <Select
                placeholder="Tag"
                clearable
                data={tagOptions}
                value={filterTag}
                onChange={setFilterTag}
                style={{ width: 150 }}
                radius="xl"
                styles={{
                  input: {
                    backgroundColor: '#333',
                    color: 'white'
                  },
                  dropdown: {
                    backgroundColor: '#333',
                    color: 'white'
                  }
                }}
              />
            </Group>
          </Paper>

          {currentUserIsManager && (
            <TaskAssignmentSystem 
              workspaceId={workspaceId}
              onAssignTask={handleAssignTask}
              availableTasks={allTasks}
              availableAgents={enhancedMembers}
            />
          )}
          
          <ScrollArea.Autosize mah={600} offsetScrollbars>
            <DndProvider backend={HTML5Backend}>
              <Group align="flex-start" style={{ gap: '1rem', flexWrap: 'nowrap' }}>
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
          </ScrollArea.Autosize>
        </>
      ) : (
        <>
          <Paper p="md" mb="md" shadow="xs" style={{ borderRadius: '12px', backgroundColor: '#202124', border: '1px solid #333' }}>
            <Group>
              <Select
                placeholder="Select Agent"
                data={enhancedMembers.map(member => ({
                  value: member.id,
                  label: member.name,
                  group: member.type === 'human' ? 'Human Team Members' : 'AI Agents'
                }))}
                value={selectedAgent}
                onChange={setSelectedAgent}
                style={{ flex: 1 }}
                searchable
                clearable
                radius="xl"
                styles={{
                  input: {
                    backgroundColor: '#333',
                    color: 'white'
                  },
                  dropdown: {
                    backgroundColor: '#333',
                    color: 'white'
                  }
                }}
              />
            </Group>
          </Paper>
          
          {selectedAgent ? (
            <AgentTaskAwareness
              agentId={selectedAgent}
              agentName={enhancedMembers.find(m => m.id === selectedAgent)?.name || 'Agent'}
              agentType={enhancedMembers.find(m => m.id === selectedAgent)?.type || 'agent'}
              managerRole={false}
              assignedTasks={getAssignedTasks(selectedAgent)}
              statusOptions={taskStatusOptions}
              onStatusChange={handleStatusChange}
              onProgressUpdate={handleProgressUpdate}
              onAddComment={handleAddComment}
            />
          ) : (
            <Paper p="xl" radius="md" style={{ backgroundColor: '#202124', border: '1px solid #333', textAlign: 'center' }}>
              <Text style={{ color: '#aaa' }}>Select an agent to view their tasks</Text>
            </Paper>
          )}
        </>
      )}
      
      {/* Create Task Modal */}
      <TaskModal
        opened={createTaskModalOpen}
        onClose={() => setCreateTaskModalOpen(false)}
        onSave={handleCreateTask}
        statusOptions={statusOptions}
        tagOptions={tagOptions}
        members={formattedMembers}
      />
      
      {/* View Task Detail Modal */}
      {currentTask && (
        <TaskDetailView
          task={currentTask}
          opened={viewTaskModalOpen}
          onClose={() => setViewTaskModalOpen(false)}
          onEditClick={handleEditTaskClick}
        />
      )}
      
      {/* Edit Task Modal */}
      {currentTask && (
        <TaskModal
          opened={editTaskModalOpen}
          onClose={() => setEditTaskModalOpen(false)}
          task={currentTask}
          onSave={handleUpdateTask}
          statusOptions={statusOptions}
          tagOptions={tagOptions}
          members={formattedMembers}
        />
      )}
    </Box>
  );
};

export default WorkspaceTaskBoard; 