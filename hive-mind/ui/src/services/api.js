import axios from 'axios';

// Configure axios with baseURL from environment or default
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api';

// Create axios instance with common configuration
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  // Add a timeout to detect if the API is unreachable
  timeout: 2000,
});

// Flag to track if we should use mock data
let useMockData = false;

// Helper function to get mock data path
const getMockPath = (path) => {
  // Remove leading slash if present
  const cleanPath = path.startsWith('/') ? path.substring(1) : path;
  return `/mock-api/${cleanPath}`;
};

// Request interceptor to add auth token to requests
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    
    // If we've detected the real API is down, use mock data
    if (useMockData && !config.url.includes('/mock-api/')) {
      config.url = getMockPath(config.url);
      // Reset baseURL to avoid doubling up the paths
      config.baseURL = '';
    }
    
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor to handle common errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    // Handle 401 Unauthorized errors (e.g., token expired)
    if (error.response && error.response.status === 401) {
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      window.location.href = '/login';
    }
    
    // Network error or connection refused - fall back to mock data
    if (error.code === 'ECONNABORTED' || error.message.includes('Network Error') || 
       (error.response && error.response.status === 0)) {
      console.log('API server unreachable, falling back to mock data');
      useMockData = true;
      
      // Retry the request with mock data
      const originalRequest = error.config;
      originalRequest.url = getMockPath(originalRequest.url);
      originalRequest.baseURL = '';
      return axios(originalRequest);
    }
    
    return Promise.reject(error);
  }
);

// Authentication
export const auth = {
  login: (username, password) => 
    api.post('/auth/token', `username=${username}&password=${password}`, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
    }),
  
  register: (userData) => 
    api.post('/auth/register', userData),
  
  getCurrentUser: () => 
    api.get('/auth/me'),
  
  agentLogin: (agentId, apiKey) => 
    api.post('/auth/agent/token', { agent_id: agentId, api_key: apiKey }),
};

// Tasks
export const tasks = {
  getTasks: (filters = {}) => 
    api.get('/tasks', { params: filters }),
  
  getTask: (taskId) => 
    api.get(`/tasks/${taskId}`),
  
  createTask: (taskData) => 
    api.post('/tasks', taskData),
  
  updateTask: (taskId, taskData) => 
    api.put(`/tasks/${taskId}`, taskData),
  
  updateTaskStatus: (taskId, status) => 
    api.put(`/tasks/${taskId}/status`, { status }),
  
  getTaskComments: (taskId) => 
    api.get(`/tasks/${taskId}/comments`),
  
  addTaskComment: (taskId, content) => 
    api.post(`/tasks/${taskId}/comments`, { content }),
};

// Teams
export const teams = {
  getTeams: () => 
    api.get('/teams'),
  
  getTeam: (teamId) => 
    api.get(`/teams/${teamId}`),
  
  createTeam: (teamData) => 
    api.post('/teams', teamData),
  
  updateTeam: (teamId, teamData) => 
    api.put(`/teams/${teamId}`, teamData),
  
  getTeamAgents: (teamId) => 
    api.get(`/teams/${teamId}/agents`),
  
  addAgentToTeam: (teamId, agentId) => 
    api.post(`/teams/${teamId}/agents`, { agent_id: agentId }),
  
  removeAgentFromTeam: (teamId, agentId) => 
    api.delete(`/teams/${teamId}/agents/${agentId}`),
};

// Agents
export const agents = {
  getAgents: () => 
    api.get('/agents'),
  
  getAgent: (agentId) => 
    api.get(`/agents/${agentId}`),
  
  createAgent: (agentData) => 
    api.post('/agents', agentData),
  
  updateAgent: (agentId, agentData) => 
    api.put(`/agents/${agentId}`, agentData),
};

// Projects
export const projects = {
  getProjects: () => 
    api.get('/projects'),
  
  getProject: (projectId) => 
    api.get(`/projects/${projectId}`),
  
  createProject: (projectData) => 
    api.post('/projects', projectData),
  
  updateProject: (projectId, projectData) => 
    api.put(`/projects/${projectId}`, projectData),
  
  getProjectTasks: (projectId) => 
    api.get('/tasks', { params: { project_id: projectId } }),
};

// Workspaces
export const workspaces = {
  getWorkspaces: () => 
    api.get('/workspaces'),
  
  getWorkspace: (workspaceId) => 
    api.get(`/workspaces/${workspaceId}`),
  
  createWorkspace: (workspaceData) => 
    api.post('/workspaces', workspaceData),
  
  updateWorkspace: (workspaceId, workspaceData) => 
    api.put(`/workspaces/${workspaceId}`, workspaceData),
  
  getWorkspaceTeams: (workspaceId) => 
    api.get(`/workspaces/${workspaceId}/teams`),
  
  getWorkspaceProjects: (workspaceId) => 
    api.get(`/workspaces/${workspaceId}/projects`),
};

// Tags
export const tags = {
  getTags: () => 
    api.get('/tags'),
  
  createTag: (tagData) => 
    api.post('/tags', tagData),
};

// Budgets
export const budgets = {
  getTeamBudget: (teamId) => 
    api.get(`/teams/${teamId}/budget`),
  
  createTeamBudget: (teamId, budgetData) => 
    api.post(`/teams/${teamId}/budget`, budgetData),
  
  updateTeamBudget: (teamId, budgetData) => 
    api.put(`/teams/${teamId}/budget`, budgetData),
  
  getTeamSpendingAlerts: (teamId) => 
    api.get(`/teams/${teamId}/spending-alerts`),
};

// Users
export const users = {
  getUsers: () => 
    api.get('/users'),
  
  getUser: (userId) => 
    api.get(`/users/${userId}`),
  
  updateUser: (userId, userData) => 
    api.put(`/users/${userId}`, userData),
};

export default {
  auth,
  tasks,
  teams,
  agents,
  projects,
  workspaces,
  tags,
  budgets,
  users,
}; 