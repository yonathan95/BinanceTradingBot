import { Route, Routes } from 'react-router-dom';
import { AppShell, Burger, Group, useMantineTheme, Box, Text, Button } from '@mantine/core';
import { useState, useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';

import AppHeader from './components/layout/AppHeader';
import AppSidebar from './components/layout/AppSidebar';
import Dashboard from './pages/Dashboard';
import Teams from './pages/Teams';
import Settings from './pages/Settings';
import CostManagement from './pages/CostManagement';
import Analytics from './pages/Analytics';
import TeamCreation from './pages/TeamCreation';
import Workspaces from './pages/Workspaces';
import WorkspaceDetail from './pages/WorkspaceDetail';
import WorkspaceWorkmode from './pages/WorkspaceWorkmode';
import ProjectWorkmode from './pages/ProjectWorkmode';
import WorkModeDashboard from './pages/WorkModeDashboard';
import WorkModeAgentDetail from './pages/WorkModeAgentDetail';
import WorkModeTaskDetail from './pages/WorkModeTaskDetail';

// Import additional Work Mode UI pages when they're created
// import WorkModeTaskCreator from './pages/WorkModeTaskCreator';

// Create a component for the 404 Not Found page
function NotFound() {
  const location = useLocation();
  
  return (
    <Box p="xl" style={{ minHeight: '70vh', display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center' }}>
      <Text size="xl" fw={700} mb="md" c="blue.3">Page Not Found</Text>
      <Text mb="lg" c="gray.3">The requested path <strong>{location.pathname}</strong> could not be found.</Text>
      <Button component={Link} to="/" variant="filled" color="blue">
        Go to Dashboard
      </Button>
    </Box>
  );
}

export default function App() {
  const theme = useMantineTheme();
  const [opened, setOpened] = useState(false);
  const [sidebarMinimized, setSidebarMinimized] = useState(false);

  const handleSidebarMinimizeChange = (minimized: boolean) => {
    setSidebarMinimized(minimized);
  };

  // Add console log for debugging route rendering
  console.log('App component rendering');

  return (
    <AppShell
      padding="md"
      navbar={{
        width: sidebarMinimized ? 60 : 260,
        breakpoint: 'sm',
        collapsed: { mobile: !opened },
      }}
      header={{ height: 60 }}
      styles={{
        main: {
          transition: 'padding-left 0.3s ease, width 0.3s ease',
          backgroundColor: '#1a1b1e', // Change to dark theme background color
          color: '#c1c2c5', // Add text color for dark theme
          overflow: 'auto', // Change overflow to auto to show scrollbars when needed
          paddingLeft: sidebarMinimized ? 'calc(60px + 1rem)' : undefined,
          minHeight: '100vh', // Ensure the main content fills the viewport height
        },
        navbar: {
          transition: 'width 0.3s ease',
          backgroundColor: '#141517', // Make navbar darker than main content
        },
        header: {
          backgroundColor: '#141517', // Match header to navbar
        }
      }}
    >
      <AppShell.Header>
        <Group p="md">
          <Burger
            opened={opened}
            onClick={() => setOpened((o) => !o)}
            hiddenFrom="sm"
            size="sm"
          />
          <AppHeader />
        </Group>
      </AppShell.Header>

      <AppShell.Navbar p={0}>
        <AppSidebar onMinimizeChange={handleSidebarMinimizeChange} />
      </AppShell.Navbar>
      
      <AppShell.Main className="animate-fade">
        <Box style={{ padding: '1rem' }}>
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/teams" element={<Teams />} />
            <Route path="/create-team" element={<TeamCreation />} />
            <Route path="/workspaces" element={<Workspaces />} />
            <Route path="/workspaces/:workspaceId" element={<WorkspaceDetail />} />
            <Route path="/analytics" element={<Analytics />} />
            <Route path="/cost-management" element={<CostManagement />} />
            <Route path="/settings" element={<Settings />} />
            
            {/* Workmode Routes */}
            <Route path="/workspace-workmode" element={<WorkspaceWorkmode />} />
            <Route path="/workspace-workmode/:workspaceId" element={<WorkspaceWorkmode />} />
            <Route path="/project-workmode" element={<ProjectWorkmode />} />
            <Route path="/project-workmode/:projectId" element={<ProjectWorkmode />} />
            
            {/* Enhanced Work Mode UI Routes */}
            <Route path="/work-mode/dashboard" element={<WorkModeDashboard />} />
            {/* Add route for workspace-specific work mode */}
            <Route path="/workspaces/:workspaceId/work-mode/dashboard" element={<WorkModeDashboard />} />
            {/* Workspace-specific agent routes */}
            <Route path="/workspaces/:workspaceId/work-mode/agent/:agentId" element={<WorkModeAgentDetail />} />
            {/* Workspace-specific task routes - updated to match the actual URL structure used */}
            <Route path="/workspaces/:workspaceId/work-mode/task/:taskId" element={<WorkModeTaskDetail />} />
            
            {/* Add the exact route patterns that are causing issues */}
            <Route path="/workspaces/ws-001/work-mode/task/task-1" element={<WorkModeTaskDetail />} />
            <Route path="/workspaces/ws-001/work-mode/task/task-3" element={<WorkModeTaskDetail />} />
            
            {/* Grafana dashboard routes */}
            <Route path="/d/:dashboardId/*" element={<Analytics />} />
            {/* Add these routes when the components are created
            <Route path="/work-mode/agent/:id" element={<WorkModeAgentDetail />} />
            <Route path="/work-mode/task/:id" element={<WorkModeTaskDetail />} />
            <Route path="/work-mode/tasks/new" element={<WorkModeTaskCreator />} />
            */}
            
            {/* Catch-all route for 404 Not Found */}
            <Route path="*" element={<NotFound />} />
          </Routes>
        </Box>
      </AppShell.Main>
    </AppShell>
  );
} 