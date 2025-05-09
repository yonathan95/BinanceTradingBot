import { Routes, Route } from 'react-router-dom';
import { useEffect } from 'react';
import { useStore } from './hooks/useStore';
import { initializeWebSocket } from './hooks/useWebSocket';

// Import pages
import Dashboard from './pages/Dashboard';
import AgentDetail from './pages/AgentDetail';
import TaskDetail from './pages/TaskDetail';
import TaskCreator from './pages/TaskCreator';

// Import components
import Layout from './components/Layout';

const App = () => {
  const { setAgents, addTimelineEvent, setTaskStatus } = useStore((state) => ({
    setAgents: state.setAgents,
    addTimelineEvent: state.addTimelineEvent,
    setTaskStatus: state.setTaskStatus,
  }));

  useEffect(() => {
    const wsUrl = import.meta.env.VITE_WS_URL || 'ws://localhost:8080';
    
    const handleEvents = (event: any) => {
      const { type, payload } = event;
      
      switch (type) {
        case 'AGENT_STATUS':
          setAgents(payload);
          break;
        case 'TIMELINE_UPDATE':
          addTimelineEvent(payload);
          break;
        case 'TASK_STATUS':
          setTaskStatus(payload);
          break;
        default:
          console.log('Unhandled event type:', type);
      }
    };
    
    initializeWebSocket(wsUrl, handleEvents);
  }, [setAgents, addTimelineEvent, setTaskStatus]);

  return (
    <Routes>
      <Route path="/" element={<Layout />}>
        <Route index element={<Dashboard />} />
        <Route path="dashboard" element={<Dashboard />} />
        <Route path="agent/:id" element={<AgentDetail />} />
        <Route path="agent/:id/task/:taskId" element={<TaskDetail />} />
        <Route path="tasks/new" element={<TaskCreator />} />
      </Route>
    </Routes>
  );
};

export default App; 