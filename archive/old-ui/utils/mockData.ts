// Mock data for testing UI without backend

// User data
export const mockUser = {
  id: 'user-1',
  username: 'demo_user',
  email: 'demo@example.com',
  role: 'admin'
};

// Teams data
export const mockTeams = [
  {
    id: 'team-1',
    name: 'Development Team',
    description: 'Main development team working on the Hive Mind project',
    created_at: '2023-07-15T12:00:00Z',
    member_count: 4,
    active_tasks: 3
  },
  {
    id: 'team-2',
    name: 'UI/UX Team',
    description: 'Frontend and design team for the Hive Mind project',
    created_at: '2023-07-16T10:30:00Z',
    member_count: 2,
    active_tasks: 1
  },
  {
    id: 'team-3',
    name: 'DevOps Team',
    description: 'Infrastructure and deployment team',
    created_at: '2023-07-17T09:15:00Z',
    member_count: 2,
    active_tasks: 2
  }
];

// Workspace files
export const mockWorkspaceFiles = [
  {
    id: 'file-1',
    name: 'main.py',
    path: '/project/main.py',
    type: 'file',
    size: 1024,
    last_modified: '2023-07-20T14:30:00Z',
    content: 'def main():\n    print("Hello, Hive Mind!")\n\nif __name__ == "__main__":\n    main()'
  },
  {
    id: 'file-2',
    name: 'utils',
    path: '/project/utils',
    type: 'directory',
    items: 3,
    last_modified: '2023-07-19T11:45:00Z'
  },
  {
    id: 'file-3',
    name: 'README.md',
    path: '/project/README.md',
    type: 'file',
    size: 2048,
    last_modified: '2023-07-18T09:20:00Z',
    content: '# Project Documentation\n\nThis is a sample README file for the Hive Mind project.'
  }
];

// Agent conversations
export const mockConversations = [
  {
    id: 'conv-1',
    agent: 'Manager',
    timestamp: '2023-07-21T13:20:00Z',
    message: 'We need to implement the authentication system. Let me assign tasks to the team.'
  },
  {
    id: 'conv-2',
    agent: 'Planner',
    timestamp: '2023-07-21T13:22:00Z',
    message: 'I\'ll break down the authentication system into smaller tasks: user registration, login, password reset, and session management.'
  },
  {
    id: 'conv-3',
    agent: 'Coder',
    timestamp: '2023-07-21T13:25:00Z',
    message: 'I\'ll start working on the user registration and login endpoints.'
  },
  {
    id: 'conv-4',
    agent: 'Tester',
    timestamp: '2023-07-21T13:27:00Z',
    message: 'I\'ll prepare test cases for each authentication feature.'
  }
];

// Tasks
export const mockTasks = [
  {
    id: 'task-1',
    title: 'Implement user authentication',
    description: 'Create login and registration endpoints',
    status: 'in_progress',
    priority: 'high',
    assigned_to: 'team-1',
    created_at: '2023-07-20T10:00:00Z',
    deadline: '2023-07-25T18:00:00Z',
    progress: 60
  },
  {
    id: 'task-2',
    title: 'Design user dashboard',
    description: 'Create wireframes and UI mockups for the main dashboard',
    status: 'completed',
    priority: 'medium',
    assigned_to: 'team-2',
    created_at: '2023-07-18T09:30:00Z',
    deadline: '2023-07-22T18:00:00Z',
    progress: 100
  },
  {
    id: 'task-3',
    title: 'Set up CI/CD pipeline',
    description: 'Configure GitHub Actions for automatic testing and deployment',
    status: 'todo',
    priority: 'medium',
    assigned_to: 'team-3',
    created_at: '2023-07-21T14:15:00Z',
    deadline: '2023-07-26T18:00:00Z',
    progress: 0
  }
];

// Cost data
export const mockCostData = {
  totalBudget: 1000,
  usedBudget: 320,
  remainingBudget: 680,
  budgetUtilization: 32,
  costByModel: [
    { model: 'gpt-4-turbo', cost: 150, tokens: 150000 },
    { model: 'gpt-3.5-turbo', cost: 120, tokens: 600000 },
    { model: 'claude-3-opus', cost: 50, tokens: 50000 }
  ],
  costByTeam: [
    { team: 'Development Team', cost: 180 },
    { team: 'UI/UX Team', cost: 80 },
    { team: 'DevOps Team', cost: 60 }
  ],
  costHistory: [
    { date: '2023-07-15', cost: 50 },
    { date: '2023-07-16', cost: 30 },
    { date: '2023-07-17', cost: 40 },
    { date: '2023-07-18', cost: 60 },
    { date: '2023-07-19', cost: 70 },
    { date: '2023-07-20', cost: 40 },
    { date: '2023-07-21', cost: 30 }
  ]
};

// Settings data
export const mockSettings = {
  general: {
    theme: 'light',
    language: 'en',
    notifications: true,
    autoSave: true
  },
  teams: {
    defaultTeam: 'team-1',
    autoJoinNewMembers: false
  },
  cost: {
    budgetAlertThreshold: 80,
    dailyBudgetLimit: 50,
    preferredModel: 'gpt-3.5-turbo'
  },
  agent: {
    conversationHistory: 50,
    maxConcurrentTasks: 3,
    agentVerbosity: 'medium'
  }
};

// Export all mock data as a single object
export const mockData = {
  user: mockUser,
  teams: mockTeams,
  workspaceFiles: mockWorkspaceFiles,
  conversations: mockConversations,
  tasks: mockTasks,
  costData: mockCostData,
  settings: mockSettings
}; 