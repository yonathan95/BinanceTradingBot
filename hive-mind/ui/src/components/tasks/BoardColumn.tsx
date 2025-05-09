import React from 'react';
import { Box, Text, Stack, ScrollArea, Table } from '@mantine/core';
import { useDrop } from 'react-dnd';
import TaskCard from './TaskCard';

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

interface BoardColumnProps {
  id: string;
  title: string;
  tasks: Task[];
  onDrop: (taskId: string, columnId: string) => void;
  onTaskClick: (task: Task) => void;
}

const BoardColumn: React.FC<BoardColumnProps> = ({ id, title, tasks, onDrop, onTaskClick }) => {
  const [{ isOver }, drop] = useDrop({
    accept: 'task',
    drop: (item: { id: string }) => {
      onDrop(item.id, id);
    },
    collect: (monitor) => ({
      isOver: !!monitor.isOver(),
    }),
  });

  // Get column header color based on status
  const getColumnHeaderColor = () => {
    switch (title) {
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
    <Box
      ref={drop}
      style={{
        width: 300,
        minWidth: 300,
        backgroundColor: isOver 
          ? '#2c2c2c'
          : '#202124',
        padding: '16px',
        borderRadius: '8px',
        border: '1px solid #333',
        transition: 'background-color 200ms ease, transform 200ms ease, box-shadow 200ms ease',
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        boxShadow: '0 2px 8px rgba(0,0,0,0.3)',
        margin: '0 10px',
      }}
    >
      <Box 
        mb="md" 
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          backgroundColor: getColumnHeaderColor(),
          color: 'white',
          padding: '10px 16px',
          borderRadius: '10px',
          boxShadow: '0 2px 4px rgba(0,0,0,0.2)',
        }}
      >
        <Text fw={600} size="md" c="white">{title}</Text>
        <Text size="sm" c="white" fw={500}>{tasks.length}</Text>
      </Box>

      <ScrollArea h="calc(100vh - 180px)" type="auto" offsetScrollbars>
        <Table 
          style={{ 
            border: 'none', 
            borderCollapse: 'separate', 
            borderSpacing: '0 10px' 
          }}
        >
          <Table.Tbody>
            {tasks.map((task) => (
              <Table.Tr key={task.id} style={{ background: 'transparent', border: 'none' }}>
                <Table.Td style={{ padding: '4px 0', border: 'none' }}>
                  <TaskCard 
                    task={task} 
                    onClick={() => onTaskClick(task)}
                  />
                </Table.Td>
              </Table.Tr>
            ))}
          </Table.Tbody>
        </Table>
      </ScrollArea>
    </Box>
  );
};

export default BoardColumn; 