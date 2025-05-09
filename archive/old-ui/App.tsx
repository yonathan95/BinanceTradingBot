import React from 'react';
import { Routes, Route } from 'react-router-dom';
import Dashboard from './pages/Dashboard';
import Login from './pages/Login';
import TeamCreation from './pages/TeamCreation';
import Workspace from './pages/Workspace';
import CostManagement from './pages/CostManagement';
import Settings from './pages/Settings';
import Layout from './components/Layout';
import AuthGuard from './components/AuthGuard';

const App: React.FC = () => {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      
      <Route element={<AuthGuard><Layout /></AuthGuard>}>
        <Route path="/" element={<Dashboard />} />
        <Route path="/teams/create" element={<TeamCreation />} />
        <Route path="/workspace/:teamId" element={<Workspace />} />
        <Route path="/cost-management" element={<CostManagement />} />
        <Route path="/settings" element={<Settings />} />
      </Route>
    </Routes>
  );
};

export default App; 