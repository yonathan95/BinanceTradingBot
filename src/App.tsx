import React from 'react';
import { Routes, Route } from 'react-router-dom';
import Dashboard from './pages/Dashboard';
import Login from './pages/Login';
import TeamCreation from './pages/TeamCreation';
import Workspace from './pages/Workspace';
import CostManagement from './pages/CostManagement';
import Settings from './pages/Settings';
import WorkspaceManagement from './pages/WorkspaceManagement';
import Workspaces from './pages/Workspaces';
import AgentProfilePage from './pages/AgentProfilePage';
import TeamManagement from './pages/TeamManagement';
import WorkspaceWorkmode from './pages/WorkspaceWorkmode';
import ProjectWorkmode from './pages/ProjectWorkmode';
import Layout from './components/Layout';
import AuthGuard from './components/AuthGuard';
import TagManagement from './components/admin/TagManagement';

const App: React.FC = () => {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      
      <Route element={<AuthGuard><Layout /></AuthGuard>}>
        <Route path="/" element={<Dashboard />} />
        <Route path="/workspaces" element={<Workspaces />} />
        <Route path="/teams/create" element={<TeamCreation />} />
        <Route path="/teams/:teamId" element={<TeamManagement />} />
        <Route path="/workspace/:teamId" element={<Workspace />} />
        <Route path="/cost-management" element={<CostManagement />} />
        <Route path="/settings" element={<Settings />} />
        <Route path="/agents/:agentId" element={<AgentProfilePage />} />
        
        {/* Workspace Management Routes */}
        <Route path="/workspaces/:workspaceId" element={<WorkspaceManagement />} />
        <Route path="/workspaces/:workspaceId/projects/:projectId" element={<WorkspaceManagement />} />
        
        {/* Workmode Routes */}
        <Route path="/workspace-workmode/:workspaceId" element={<WorkspaceWorkmode />} />
        <Route path="/project-workmode/:projectId" element={<ProjectWorkmode />} />
        
        {/* New nested Work Mode Routes */}
        <Route path="/workspaces/:workspaceId/work-mode/dashboard" element={<WorkspaceWorkmode />} />
        <Route path="/workspaces/:workspaceId/work-mode/projects/:projectId" element={<ProjectWorkmode />} />
        
        {/* Admin Routes */}
        <Route path="/admin/tags" element={<TagManagement />} />
      </Route>
    </Routes>
  );
};

export default App; 