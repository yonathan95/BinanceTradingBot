import React, { useState, useEffect, useRef } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import axios from 'axios';
import websocketService from '../services/websocket';
import WorkMode from '../components/WorkMode';

// Types
interface Team {
  id: string;
  name: string;
  description: string;
  agents: number;
  tasks: number;
  lastActive: string;
  status: 'active' | 'idle' | 'stopped';
  config?: {
    budgetLimit: number;
    budgetUsed: number;
  };
}

interface Task {
  id: string;
  goal: string;
  team: string;
  teamId: string;
  status: 'pending' | 'in_progress' | 'completed' | 'failed';
  complexity: 'L' | 'M' | 'H';
  budget: number;
  progress: number;
  created_at: string;
  updated_at: string;
  feedback?: {
    status: 'pending' | 'received' | 'implemented';
    lastUpdate: string;
  };
}

interface Workspace {
  id: string;
  name: string;
  description: string;
  projects: number;
  created_at: string;
  updated_at: string;
}

interface AgentInteraction {
  id: string;
  taskId: string;
  source: string;
  target: string;
  type: 'request' | 'response' | 'error';
  content: string;
  timestamp: string;
}

interface TimelineEvent {
  id: string;
  type: 'task_created' | 'task_updated' | 'agent_interaction' | 'feedback_received' | 'budget_alert';
  entityId: string;
  title: string;
  description: string;
  timestamp: string;
}

// Dashboard Component
const Dashboard: React.FC = () => {
  // State
  const [teams, setTeams] = useState<Team[]>([]);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [workspaces, setWorkspaces] = useState<Workspace[]>([]);
  const [agentInteractions, setAgentInteractions] = useState<AgentInteraction[]>([]);
  const [timelineEvents, setTimelineEvents] = useState<TimelineEvent[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  const [darkMode, setDarkMode] = useState(() => {
    return localStorage.getItem('darkMode') === 'true';
  });
  const [filterOptions, setFilterOptions] = useState({
    status: 'all',
    team: 'all',
    dateRange: '7d'
  });
  const [sortOptions, setSortOptions] = useState({
    field: 'updated_at',
    direction: 'desc'
  });
  const [activeTab, setActiveTab] = useState('dashboard');

  // Refs
  const wsConnected = useRef(false);

  // Add navigate hook at the beginning of the Dashboard function
  const navigate = useNavigate();

  // Effects
  useEffect(() => {
    document.body.classList.toggle('dark-mode', darkMode);
    localStorage.setItem('darkMode', darkMode.toString());
  }, [darkMode]);

  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        setIsLoading(true);
        
        // Fetch all required data
        const [teamsResponse, tasksResponse, workspacesResponse, interactionsResponse, timelineResponse] = await Promise.all([
          axios.get('/api/teams'),
          axios.get('/api/tasks/recent'),
          axios.get('/api/workspaces'),
          axios.get('/api/agent-interactions/recent'),
          axios.get('/api/timeline/recent')
        ]);
        
        setTeams(teamsResponse.data);
        setTasks(tasksResponse.data);
        setWorkspaces(workspacesResponse.data);
        setAgentInteractions(interactionsResponse.data);
        setTimelineEvents(timelineResponse.data);
      } catch (err) {
        setError('Failed to load dashboard data');
        console.error(err);
      } finally {
        setIsLoading(false);
      }
    };

    fetchDashboardData();
    
    // Setup WebSocket
    if (!wsConnected.current) {
      websocketService.connect();
      
      websocketService.onConnect(() => {
        wsConnected.current = true;
        console.log('WebSocket connected');
      });
      
      // Handle real-time updates
      websocketService.onMessage('team_updated', (data) => {
        setTeams(prev => prev.map(team => 
          team.id === data.id ? { ...team, ...data } : team
        ));
      });
      
      websocketService.onMessage('task_updated', (data) => {
        setTasks(prev => prev.map(task => 
          task.id === data.id ? { ...task, ...data } : task
        ));
      });
      
      websocketService.onMessage('workspace_updated', (data) => {
        setWorkspaces(prev => prev.map(workspace => 
          workspace.id === data.id ? { ...workspace, ...data } : workspace
        ));
      });
      
      websocketService.onMessage('new_interaction', (data) => {
        setAgentInteractions(prev => [data, ...prev].slice(0, 50));
      });
      
      websocketService.onMessage('new_timeline_event', (data) => {
        setTimelineEvents(prev => [data, ...prev].slice(0, 50));
      });
      
      websocketService.onMessage('budget_alert', (data) => {
        // Add budget alert to timeline
        const newEvent: TimelineEvent = {
          id: `budget-alert-${Date.now()}`,
          type: 'budget_alert',
          entityId: data.teamId,
          title: 'Budget Alert',
          description: `Team ${data.teamName} has reached ${data.percentage}% of budget limit`,
          timestamp: new Date().toISOString()
        };
        
        setTimelineEvents(prev => [newEvent, ...prev].slice(0, 50));
      });
    }
    
    return () => {
      // No need to disconnect on component unmount to maintain real-time updates
    };
  }, []);

  // Filter tasks based on current filter options
  const filteredTasks = tasks.filter(task => {
    // Filter by status
    if (filterOptions.status !== 'all' && task.status !== filterOptions.status) {
      return false;
    }
    
    // Filter by team
    if (filterOptions.team !== 'all' && task.teamId !== filterOptions.team) {
      return false;
    }
    
    // Filter by date range
    const taskDate = new Date(task.updated_at).getTime();
    const now = new Date().getTime();
    const dayInMs = 24 * 60 * 60 * 1000;
    
    switch (filterOptions.dateRange) {
      case '1d':
        return (now - taskDate) <= dayInMs;
      case '7d':
        return (now - taskDate) <= 7 * dayInMs;
      case '30d':
        return (now - taskDate) <= 30 * dayInMs;
      default:
        return true;
    }
  });
  
  // Sort tasks based on current sort options
  const sortedTasks = [...filteredTasks].sort((a, b) => {
    let aValue = a[sortOptions.field as keyof Task];
    let bValue = b[sortOptions.field as keyof Task];
    
    if (typeof aValue === 'string' && typeof bValue === 'string') {
      if (sortOptions.direction === 'asc') {
        return aValue.localeCompare(bValue as string);
      } else {
        return bValue.localeCompare(aValue as string);
      }
    } else if (typeof aValue === 'number' && typeof bValue === 'number') {
      if (sortOptions.direction === 'asc') {
        return aValue - bValue;
      } else {
        return bValue - aValue;
      }
    }
    
    return 0;
  });

  // Handler for theme toggle
  const toggleDarkMode = () => {
    setDarkMode(prev => !prev);
  };

  // Loading and error states
  if (isLoading) {
    return (
      <div className="loading-container">
        <div className="spinner"></div>
        <p>Loading dashboard...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="error-container">
        <h2>Error</h2>
        <p>{error}</p>
        <button 
          className="btn btn-primary" 
          onClick={() => window.location.reload()}
        >
          Retry
        </button>
      </div>
    );
  }

  // Calculate dashboard metrics
  const totalBudget = teams.reduce((sum, team) => sum + (team.config?.budgetLimit || 0), 0);
  const usedBudget = teams.reduce((sum, team) => sum + (team.config?.budgetUsed || 0), 0);
  const budgetPercentage = totalBudget > 0 ? Math.round((usedBudget / totalBudget) * 100) : 0;
  const activeTasks = tasks.filter(task => task.status === 'in_progress').length;
  const completedTasks = tasks.filter(task => task.status === 'completed').length;
  const pendingFeedback = tasks.filter(task => task.feedback?.status === 'pending').length;

  // Dashboard render
  return (
    <div className={`dashboard-container ${darkMode ? 'dark-mode' : ''}`}>
      <header className="dashboard-header">
        <h1>Hive Mind Dashboard</h1>
        <button 
          className="dark-mode-toggle" 
          onClick={toggleDarkMode}
          aria-label={darkMode ? "Switch to light mode" : "Switch to dark mode"}
        >
          {darkMode ? "☀️" : "🌙"}
        </button>
      </header>

      <nav className="dashboard-nav">
        <ul>
          <li className={activeTab === 'dashboard' ? 'active' : ''}>
            <button onClick={() => setActiveTab('dashboard')}>Dashboard</button>
          </li>
          <li className={activeTab === 'teams' ? 'active' : ''}>
            <button onClick={() => setActiveTab('teams')}>Teams</button>
          </li>
          <li className={activeTab === 'tasks' ? 'active' : ''}>
            <button onClick={() => setActiveTab('tasks')}>Tasks</button>
          </li>
          <li className={activeTab === 'workspaces' ? 'active' : ''}>
            <button onClick={() => setActiveTab('workspaces')}>Workspaces</button>
          </li>
          <li className={activeTab === 'workmode' ? 'active' : ''}>
            <button onClick={() => setActiveTab('workmode')}>Work Mode</button>
          </li>
        </ul>
      </nav>

      {error && (
        <div className="dashboard-error">
          <p>{error}</p>
          <button onClick={() => window.location.reload()}>Retry</button>
        </div>
      )}

      {isLoading ? (
        <div className="dashboard-loading">
          <p>Loading dashboard data...</p>
          <div className="spinner"></div>
        </div>
      ) : (
        <main className="dashboard-content">
          {activeTab === 'dashboard' && (
            <div className="dashboard-overview">
              <section className="dashboard-stats">
                <div className="stat-card">
                  <h3>Active Teams</h3>
                  <p className="stat-value">{teams.filter(t => t.status === 'active').length}</p>
                </div>
                <div className="stat-card">
                  <h3>Active Tasks</h3>
                  <p className="stat-value">{tasks.filter(t => t.status === 'in_progress').length}</p>
                </div>
                <div className="stat-card">
                  <h3>Workspaces</h3>
                  <p className="stat-value">{workspaces.length}</p>
                </div>
                <div className="stat-card">
                  <h3>Total Agents</h3>
                  <p className="stat-value">{teams.reduce((sum, team) => sum + team.agents, 0)}</p>
                </div>
              </section>

              <div className="dashboard-grid">
                <div className="dashboard-column">
                  <section className="dashboard-recent-tasks">
                    <div className="section-header">
                      <h2>Recent Tasks</h2>
                      <Link to="/tasks" className="view-all">View All</Link>
                    </div>
                    {renderTasks()}
                  </section>
                  
                  <section className="dashboard-workspaces">
                    <div className="section-header">
                      <h2>Workspaces</h2>
                      <Link to="/workspaces" className="view-all">View All</Link>
                    </div>
                    {renderWorkspaces()}
                  </section>
                </div>
                
                <div className="dashboard-column">
                  <section className="dashboard-teams">
                    <div className="section-header">
                      <h2>Teams</h2>
                      <Link to="/teams" className="view-all">View All</Link>
                    </div>
                    {renderTeams()}
                  </section>
                  
                  <section className="dashboard-timeline">
                    <div className="section-header">
                      <h2>Activity Timeline</h2>
                    </div>
                    {renderTimeline()}
                  </section>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'teams' && (
            <div className="teams-section full-width">
              <div className="section-header">
                <h2>Teams</h2>
                <Link to="/team/create" className="create-btn">Create Team</Link>
              </div>
              {renderTeams(true)}
            </div>
          )}

          {activeTab === 'tasks' && (
            <div className="tasks-section full-width">
              <div className="section-header">
                <h2>Tasks</h2>
                {renderFilterControls()}
              </div>
              {renderTasks(true)}
            </div>
          )}

          {activeTab === 'workspaces' && (
            <div className="workspaces-section full-width">
              <div className="section-header">
                <h2>Workspaces</h2>
                <Link to="/workspaces/create" className="create-btn">Create Workspace</Link>
              </div>
              {renderWorkspaces(true)}
            </div>
          )}
          
          {activeTab === 'workmode' && (
            <div className="workmode-section full-width">
              <WorkMode />
            </div>
          )}
        </main>
      )}
    </div>
  );

  // Render workspaces list
  function renderWorkspaces(fullWidth?: boolean) {
    if (workspaces.length === 0) {
      return (
        <div className="empty-state">
          <p>No workspaces yet</p>
          <Link to="/workspaces" className="btn btn-primary">
            Manage Workspaces
          </Link>
        </div>
      );
    }

    // Show just the top 3 most recently updated workspaces
    const recentWorkspaces = [...workspaces]
      .sort((a, b) => new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime())
      .slice(0, 3);

    return (
      <div className={`workspaces-list ${fullWidth ? 'full-width' : ''}`}>
        {recentWorkspaces.map(workspace => (
          <div key={workspace.id} className="workspace-item">
            <div className="workspace-info">
              <h3>{workspace.name}</h3>
              <p>{workspace.description}</p>
            </div>
            <div className="workspace-stats">
              <div className="stat">
                <span className="stat-value">{workspace.projects}</span>
                <span className="stat-label">Projects</span>
              </div>
              <div className="stat">
                <span className="stat-value">
                  {new Date(workspace.updated_at).toLocaleDateString()}
                </span>
                <span className="stat-label">Last Updated</span>
              </div>
            </div>
            <div className="workspace-actions">
              <Link 
                to={`/workspaces/${workspace.id}`} 
                className="btn btn-primary btn-sm"
              >
                Open Workspace
              </Link>
            </div>
          </div>
        ))}

        {workspaces.length > 3 && (
          <div className="view-all-link">
            <Link to="/workspaces">
              View all workspaces ({workspaces.length})
            </Link>
          </div>
        )}
      </div>
    );
  }

  // Render teams list
  function renderTeams(fullWidth?: boolean) {
    if (teams.length === 0) {
      return (
        <div className="empty-state">
          <p>No teams yet</p>
          <button 
            className="btn btn-primary"
            onClick={() => {/* Create new team logic */}}
          >
            Create Team
          </button>
        </div>
      );
    }

    return (
      <div className={`teams-list ${fullWidth ? 'full-width' : ''}`}>
        {teams.map(team => (
          <div key={team.id} className="team-item">
            <div className="team-info">
              <h3>{team.name}</h3>
              <p>{team.description}</p>
            </div>
            <div className="team-stats">
              <div className="stat">
                <span className="stat-value">{team.agents}</span>
                <span className="stat-label">Agents</span>
              </div>
              <div className="stat">
                <span className="stat-value">{team.tasks}</span>
                <span className="stat-label">Tasks</span>
              </div>
            </div>
            <div className="team-actions">
              <Link 
                to={`/workspace/${team.id}`} 
                className="btn btn-secondary btn-sm"
              >
                View Workspace
              </Link>
              <Link 
                to={`/teams/${team.id}`} 
                className="btn btn-primary btn-sm"
              >
                Manage Team
              </Link>
            </div>
          </div>
        ))}
      </div>
    );
  }

  // Render filter controls
  function renderFilterControls() {
    return (
      <>
        <select 
          value={filterOptions.status} 
          onChange={(e) => setFilterOptions({...filterOptions, status: e.target.value})}
        >
          <option value="all">All Statuses</option>
          <option value="pending">Pending</option>
          <option value="in_progress">In Progress</option>
          <option value="completed">Completed</option>
          <option value="failed">Failed</option>
        </select>
        
        <select 
          value={filterOptions.team} 
          onChange={(e) => setFilterOptions({...filterOptions, team: e.target.value})}
        >
          <option value="all">All Teams</option>
          {teams.map(team => (
            <option key={team.id} value={team.id}>{team.name}</option>
          ))}
        </select>
        
        <select 
          value={filterOptions.dateRange} 
          onChange={(e) => setFilterOptions({...filterOptions, dateRange: e.target.value})}
        >
          <option value="all">All Time</option>
          <option value="1d">Last 24 Hours</option>
          <option value="7d">Last 7 Days</option>
          <option value="30d">Last 30 Days</option>
        </select>
      </>
    );
  }

  // Render tasks list
  function renderTasks(fullWidth?: boolean) {
    if (sortedTasks.length === 0) {
      return (
        <div className="empty-state">
          <p>No tasks match your current filters.</p>
        </div>
      );
    }

    return (
      <div className={`tasks-table-container ${fullWidth ? 'full-width' : ''}`}>
        <table className="tasks-table">
          <thead>
            <tr>
              <th>Task</th>
              <th>Team</th>
              <th>Status</th>
              <th>Progress</th>
              <th>Budget</th>
              <th>Feedback</th>
              <th>Last Updated</th>
            </tr>
          </thead>
          <tbody>
            {sortedTasks.map(task => (
              <tr key={task.id} className="task-row" onClick={() => window.location.href = `/workspace/${task.teamId}?task=${task.id}`}>
                <td>{task.goal}</td>
                <td>{task.team}</td>
                <td>
                  <span className={`status-badge ${task.status}`}>
                    {task.status.replace('_', ' ')}
                  </span>
                </td>
                <td>
                  <div className="progress-container">
                    <div className="progress-bar">
                      <div 
                        className="progress-fill" 
                        style={{ width: `${task.progress}%` }}
                      ></div>
                    </div>
                    <span className="progress-text">{task.progress}%</span>
                  </div>
                </td>
                <td>${task.budget.toFixed(2)}</td>
                <td>
                  {task.feedback ? (
                    <span className={`feedback-status ${task.feedback.status}`}>
                      {task.feedback.status}
                    </span>
                  ) : (
                    <span className="feedback-status none">None</span>
                  )}
                </td>
                <td>{new Date(task.updated_at).toLocaleString()}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
  }

  // Render timeline
  function renderTimeline() {
    if (timelineEvents.length === 0) {
      return (
        <div className="empty-state">
          <p>No activities to display.</p>
        </div>
      );
    }

    return (
      <div className="timeline">
        {timelineEvents.map((event) => (
          <div key={event.id} className={`timeline-event ${event.type}`}>
            <div className="timeline-marker"></div>
            <div className="timeline-content">
              <div className="timeline-header">
                <h4>{event.title}</h4>
                <span className="timeline-time">
                  {new Date(event.timestamp).toLocaleString()}
                </span>
              </div>
              <p>{event.description}</p>
              {event.type === 'task_updated' && (
                <Link to={`/workspace/${event.entityId.split('-')[0]}?task=${event.entityId}`}>
                  View Task
                </Link>
              )}
              {event.type === 'budget_alert' && (
                <Link to="/cost-management">
                  Manage Budget
                </Link>
              )}
            </div>
          </div>
        ))}
      </div>
    );
  }
};

export default Dashboard; 