import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import axios from 'axios';

interface Agent {
  id: string;
  name: string;
  role: string;
  avatar?: string;
  description: string;
  model: string;
  capabilities: string[];
  active: boolean;
  performance?: {
    tasksCompleted: number;
    successRate: number;
  };
}

interface Team {
  id: string;
  name: string;
  description: string;
  model_tier: string;
  budget_limit: number;
  budget_used: number;
  created_at: string;
  updated_at: string;
  agents: Agent[];
}

const TeamManagement: React.FC = () => {
  const { teamId } = useParams<{ teamId: string }>();
  const navigate = useNavigate();
  const [team, setTeam] = useState<Team | null>(null);
  const [activeTab, setActiveTab] = useState<'overview' | 'agents' | 'settings'>('agents');
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchTeamData = async () => {
      if (!teamId) return;
      
      try {
        setIsLoading(true);
        // In a real implementation, this would be a real API call
        // For now, using mock data
        const response = await axios.get(`/api/teams/${teamId}`);
        setTeam(response.data);
        setError('');
      } catch (err) {
        setError('Failed to load team data');
        console.error(err);
      } finally {
        setIsLoading(false);
      }
    };

    fetchTeamData();
  }, [teamId]);

  const handleBack = () => {
    navigate(-1);
  };

  if (isLoading) {
    return (
      <div className="loading-container">
        <div className="spinner"></div>
        <p>Loading team data...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="error-container">
        <h2>Error</h2>
        <p>{error}</p>
        <button onClick={handleBack} className="back-button">
          Go Back
        </button>
      </div>
    );
  }

  return (
    <div className="team-management-page">
      <div className="page-header">
        <button onClick={handleBack} className="back-button">
          &larr; Back
        </button>
        <h1>Team Management</h1>
      </div>

      {team ? (
        <>
          <div className="team-info">
            <h2>{team.name}</h2>
            <p>{team.description}</p>

            <div className="team-stats">
              <div className="stat-card">
                <h3>Model Tier</h3>
                <div className="stat-value">{team.model_tier}</div>
              </div>
              <div className="stat-card">
                <h3>Budget</h3>
                <div className="stat-value">
                  ${team.budget_used.toFixed(2)} / ${team.budget_limit.toFixed(2)}
                </div>
                <div className="progress-container">
                  <div className="progress-bar">
                    <div 
                      className="progress-fill" 
                      style={{ width: `${Math.min(100, (team.budget_used / team.budget_limit) * 100)}%` }}
                    ></div>
                  </div>
                </div>
              </div>
              <div className="stat-card">
                <h3>Agents</h3>
                <div className="stat-value">{team.agents.length}</div>
              </div>
            </div>
          </div>

          <div className="tabs">
            <button 
              className={`tab ${activeTab === 'overview' ? 'active' : ''}`}
              onClick={() => setActiveTab('overview')}
            >
              Overview
            </button>
            <button 
              className={`tab ${activeTab === 'agents' ? 'active' : ''}`}
              onClick={() => setActiveTab('agents')}
            >
              AI Agents
            </button>
            <button 
              className={`tab ${activeTab === 'settings' ? 'active' : ''}`}
              onClick={() => setActiveTab('settings')}
            >
              Settings
            </button>
          </div>

          <div className="tab-content">
            {activeTab === 'overview' && (
              <div className="overview-content">
                <h3>Team Overview</h3>
                <p>Created: {new Date(team.created_at).toLocaleDateString()}</p>
                <p>Last updated: {new Date(team.updated_at).toLocaleDateString()}</p>
                {/* Additional team overview information would go here */}
              </div>
            )}

            {activeTab === 'agents' && (
              <div className="agents-content">
                <h3>Team AI Agents</h3>
                <div className="agent-cards">
                  {team.agents.map(agent => (
                    <div key={agent.id} className="agent-card" onClick={() => navigate(`/agents/${agent.id}`)}>
                      <div className="agent-avatar">
                        {agent.avatar ? (
                          <img src={agent.avatar} alt={agent.name} className="agent-avatar-img" />
                        ) : (
                          <div className="avatar-placeholder">
                            {agent.name.charAt(0).toUpperCase()}
                          </div>
                        )}
                      </div>
                      <div className="agent-info">
                        <h3>{agent.name}</h3>
                        <span className="agent-role">{agent.role}</span>
                        {agent.performance && (
                          <div className="agent-stats">
                            <div className="stat">
                              <span className="stat-label">Tasks</span>
                              <span className="stat-value">{agent.performance.tasksCompleted}</span>
                            </div>
                            <div className="stat">
                              <span className="stat-label">Success</span>
                              <span className="stat-value">{(agent.performance.successRate * 100).toFixed(0)}%</span>
                            </div>
                          </div>
                        )}
                        <div className="agent-status">
                          <span className={`status-indicator ${agent.active ? 'active' : 'inactive'}`}></span>
                          <span>{agent.active ? 'Active' : 'Inactive'}</span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {activeTab === 'settings' && (
              <div className="settings-content">
                <h3>Team Settings</h3>
                <div className="form-container">
                  <div className="form-group">
                    <label htmlFor="team-name">Team Name</label>
                    <input type="text" id="team-name" value={team.name} readOnly />
                  </div>
                  <div className="form-group">
                    <label htmlFor="team-description">Description</label>
                    <textarea id="team-description" value={team.description} readOnly rows={3}></textarea>
                  </div>
                  <div className="form-group">
                    <label htmlFor="model-tier">Model Tier</label>
                    <select id="model-tier" value={team.model_tier} disabled>
                      <option value="basic">Basic</option>
                      <option value="standard">Standard</option>
                      <option value="premium">Premium</option>
                      <option value="enterprise">Enterprise</option>
                    </select>
                  </div>
                  <div className="form-group">
                    <label htmlFor="budget-limit">Budget Limit</label>
                    <input type="number" id="budget-limit" value={team.budget_limit} readOnly />
                  </div>
                  <button className="btn btn-primary">Edit Team</button>
                </div>
              </div>
            )}
          </div>
        </>
      ) : (
        <div className="empty-state">
          <p>Team not found</p>
        </div>
      )}
    </div>
  );
};

export default TeamManagement; 