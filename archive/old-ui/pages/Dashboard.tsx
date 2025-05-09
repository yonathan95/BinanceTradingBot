import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import axios from 'axios';

interface Team {
  id: string;
  name: string;
  description: string;
  agents: number;
  tasks: number;
  lastActive: string;
  status: 'active' | 'idle' | 'stopped';
}

interface Task {
  id: string;
  goal: string;
  team: string;
  status: 'pending' | 'in_progress' | 'completed' | 'failed';
  complexity: 'L' | 'M' | 'H';
  budget: number;
  progress: number;
  created_at: string;
}

const Dashboard: React.FC = () => {
  const [teams, setTeams] = useState<Team[]>([]);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [teamsResponse, tasksResponse] = await Promise.all([
          axios.get('/api/teams'),
          axios.get('/api/tasks/recent')
        ]);
        setTeams(teamsResponse.data);
        setTasks(tasksResponse.data);
      } catch (err) {
        setError('Failed to load dashboard data');
        console.error(err);
      } finally {
        setIsLoading(false);
      }
    };

    fetchData();
  }, []);

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

  return (
    <div className="dashboard-container">
      <div className="dashboard-header">
        <h1>Dashboard</h1>
        <Link to="/teams/create" className="btn btn-primary">
          Create New Team
        </Link>
      </div>

      <div className="dashboard-metrics">
        <div className="metric-card">
          <h3>Teams</h3>
          <div className="metric-value">{teams.length}</div>
        </div>
        <div className="metric-card">
          <h3>Active Tasks</h3>
          <div className="metric-value">
            {tasks.filter(task => task.status === 'in_progress').length}
          </div>
        </div>
        <div className="metric-card">
          <h3>Completed Tasks</h3>
          <div className="metric-value">
            {tasks.filter(task => task.status === 'completed').length}
          </div>
        </div>
        <div className="metric-card">
          <h3>Budget Usage</h3>
          <div className="metric-value">
            ${tasks.reduce((sum, task) => sum + task.budget, 0).toFixed(2)}
          </div>
        </div>
      </div>

      <div className="teams-section">
        <h2>Your Teams</h2>
        {teams.length === 0 ? (
          <div className="empty-state">
            <p>You don't have any teams yet.</p>
            <Link to="/teams/create" className="btn btn-primary">
              Create Your First Team
            </Link>
          </div>
        ) : (
          <div className="teams-grid">
            {teams.map(team => (
              <div key={team.id} className="team-card">
                <div className="team-header">
                  <h3>{team.name}</h3>
                  <span className={`status-badge ${team.status}`}>{team.status}</span>
                </div>
                <p className="team-description">{team.description}</p>
                <div className="team-stats">
                  <div className="stat">
                    <span className="stat-label">Agents</span>
                    <span className="stat-value">{team.agents}</span>
                  </div>
                  <div className="stat">
                    <span className="stat-label">Tasks</span>
                    <span className="stat-value">{team.tasks}</span>
                  </div>
                  <div className="stat">
                    <span className="stat-label">Last Active</span>
                    <span className="stat-value">{new Date(team.lastActive).toLocaleDateString()}</span>
                  </div>
                </div>
                <div className="team-actions">
                  <Link to={`/workspace/${team.id}`} className="btn btn-primary">
                    Open Workspace
                  </Link>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="recent-tasks-section">
        <h2>Recent Tasks</h2>
        {tasks.length === 0 ? (
          <div className="empty-state">
            <p>No tasks have been created yet.</p>
          </div>
        ) : (
          <div className="tasks-table-container">
            <table className="tasks-table">
              <thead>
                <tr>
                  <th>Task</th>
                  <th>Team</th>
                  <th>Status</th>
                  <th>Complexity</th>
                  <th>Budget</th>
                  <th>Progress</th>
                  <th>Created</th>
                </tr>
              </thead>
              <tbody>
                {tasks.map(task => (
                  <tr key={task.id}>
                    <td>{task.goal}</td>
                    <td>{task.team}</td>
                    <td>
                      <span className={`status-badge ${task.status}`}>
                        {task.status.replace('_', ' ')}
                      </span>
                    </td>
                    <td>{task.complexity}</td>
                    <td>${task.budget.toFixed(2)}</td>
                    <td>
                      <div className="progress-bar">
                        <div 
                          className="progress-fill" 
                          style={{ width: `${task.progress}%` }}
                        ></div>
                      </div>
                      <span className="progress-text">{task.progress}%</span>
                    </td>
                    <td>{new Date(task.created_at).toLocaleDateString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};

export default Dashboard; 