import React, { useState, useEffect } from 'react';
import axios from 'axios';

interface Agent {
  id: string;
  name: string;
  role: string;
  description: string;
  model: string;
  capabilities: string[];
  active: boolean;
}

interface TeamMember {
  id: string;
  name: string;
  email: string;
  role: 'admin' | 'editor' | 'viewer';
  avatar: string;
}

interface ProjectConfigProps {
  projectId: string;
  onUpdate?: () => void;
}

const ProjectConfig: React.FC<ProjectConfigProps> = ({ projectId, onUpdate }) => {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [teamMembers, setTeamMembers] = useState<TeamMember[]>([]);
  const [availableAgents, setAvailableAgents] = useState<Agent[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  const [newMemberEmail, setNewMemberEmail] = useState('');
  const [newMemberRole, setNewMemberRole] = useState<'editor' | 'viewer'>('editor');
  const [activeTab, setActiveTab] = useState<'agents' | 'team'>('agents');
  const [modelTier, setModelTier] = useState('standard');
  const [budgetLimit, setBudgetLimit] = useState(100);

  // Fetch project configuration data
  useEffect(() => {
    const fetchProjectConfig = async () => {
      try {
        setIsLoading(true);
        const [
          agentsResponse, 
          teamResponse, 
          availableAgentsResponse,
          projectResponse
        ] = await Promise.all([
          axios.get(`/api/projects/${projectId}/agents`),
          axios.get(`/api/projects/${projectId}/team`),
          axios.get('/api/available-agents'),
          axios.get(`/api/projects/${projectId}`)
        ]);
        
        setAgents(agentsResponse.data);
        setTeamMembers(teamResponse.data);
        setAvailableAgents(availableAgentsResponse.data);
        setModelTier(projectResponse.data.model_tier);
        setBudgetLimit(projectResponse.data.budget_limit);
        setError('');
      } catch (err) {
        setError('Failed to load project configuration');
        console.error(err);
      } finally {
        setIsLoading(false);
      }
    };

    fetchProjectConfig();
  }, [projectId]);

  // Toggle agent activation
  const handleToggleAgent = async (agentId: string, currentlyActive: boolean) => {
    try {
      const response = await axios.patch(`/api/projects/${projectId}/agents/${agentId}`, {
        active: !currentlyActive
      });
      
      setAgents(prevAgents => 
        prevAgents.map(agent => 
          agent.id === agentId ? response.data : agent
        )
      );
      
      if (onUpdate) {
        onUpdate();
      }
    } catch (err) {
      setError('Failed to update agent configuration');
      console.error(err);
    }
  };

  // Add a new agent to the project
  const handleAddAgent = async (agentId: string) => {
    try {
      const response = await axios.post(`/api/projects/${projectId}/agents`, {
        agent_id: agentId
      });
      
      setAgents(prevAgents => [...prevAgents, response.data]);
      
      if (onUpdate) {
        onUpdate();
      }
    } catch (err) {
      setError('Failed to add agent to project');
      console.error(err);
    }
  };

  // Remove an agent from the project
  const handleRemoveAgent = async (agentId: string) => {
    try {
      await axios.delete(`/api/projects/${projectId}/agents/${agentId}`);
      
      setAgents(prevAgents => 
        prevAgents.filter(agent => agent.id !== agentId)
      );
      
      if (onUpdate) {
        onUpdate();
      }
    } catch (err) {
      setError('Failed to remove agent from project');
      console.error(err);
    }
  };

  // Invite a new team member
  const handleInviteTeamMember = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!newMemberEmail.trim()) return;
    
    try {
      const response = await axios.post(`/api/projects/${projectId}/team/invite`, {
        email: newMemberEmail,
        role: newMemberRole
      });
      
      setTeamMembers(prevMembers => [...prevMembers, response.data]);
      setNewMemberEmail('');
      
      if (onUpdate) {
        onUpdate();
      }
    } catch (err) {
      setError('Failed to invite team member');
      console.error(err);
    }
  };

  // Update team member role
  const handleUpdateMemberRole = async (memberId: string, newRole: 'admin' | 'editor' | 'viewer') => {
    try {
      const response = await axios.patch(`/api/projects/${projectId}/team/${memberId}`, {
        role: newRole
      });
      
      setTeamMembers(prevMembers => 
        prevMembers.map(member => 
          member.id === memberId ? response.data : member
        )
      );
      
      if (onUpdate) {
        onUpdate();
      }
    } catch (err) {
      setError('Failed to update team member role');
      console.error(err);
    }
  };

  // Remove team member
  const handleRemoveTeamMember = async (memberId: string) => {
    try {
      await axios.delete(`/api/projects/${projectId}/team/${memberId}`);
      
      setTeamMembers(prevMembers => 
        prevMembers.filter(member => member.id !== memberId)
      );
      
      if (onUpdate) {
        onUpdate();
      }
    } catch (err) {
      setError('Failed to remove team member');
      console.error(err);
    }
  };

  // Update project settings
  const handleUpdateProjectSettings = async () => {
    try {
      await axios.patch(`/api/projects/${projectId}`, {
        model_tier: modelTier,
        budget_limit: budgetLimit
      });
      
      if (onUpdate) {
        onUpdate();
      }
    } catch (err) {
      setError('Failed to update project settings');
      console.error(err);
    }
  };

  if (isLoading) {
    return (
      <div className="loading-container">
        <div className="spinner"></div>
        <p>Loading project configuration...</p>
      </div>
    );
  }

  return (
    <div className="project-config">
      <div className="tabs">
        <button 
          className={`tab ${activeTab === 'agents' ? 'active' : ''}`}
          onClick={() => setActiveTab('agents')}
        >
          AI Agents
        </button>
        <button 
          className={`tab ${activeTab === 'team' ? 'active' : ''}`}
          onClick={() => setActiveTab('team')}
        >
          Team Members
        </button>
      </div>

      {error && <div className="error-message">{error}</div>}

      <div className="project-settings">
        <h3>Project Settings</h3>
        <div className="settings-form">
          <div className="form-group">
            <label>Model Tier</label>
            <select 
              value={modelTier} 
              onChange={(e) => setModelTier(e.target.value)}
              className="form-select"
            >
              <option value="basic">Basic</option>
              <option value="standard">Standard</option>
              <option value="premium">Premium</option>
              <option value="enterprise">Enterprise</option>
            </select>
          </div>
          
          <div className="form-group">
            <label>Budget Limit ($)</label>
            <input 
              type="number" 
              value={budgetLimit} 
              onChange={(e) => setBudgetLimit(parseInt(e.target.value))}
              min="0"
              className="form-control"
            />
          </div>
          
          <button 
            className="btn btn-primary"
            onClick={handleUpdateProjectSettings}
          >
            Update Settings
          </button>
        </div>
      </div>

      {activeTab === 'agents' && (
        <div className="agents-config">
          <div className="active-agents">
            <h3>Project Agents</h3>
            {agents.length === 0 ? (
              <p className="empty-message">No agents configured for this project</p>
            ) : (
              <div className="agents-list">
                {agents.map(agent => (
                  <div key={agent.id} className="agent-card" onClick={() => window.location.href = `/agents/${agent.id}`} style={{ cursor: 'pointer' }}>
                    <div className="agent-header">
                      <h4>{agent.name}</h4>
                      <div className="agent-actions">
                        <label className="switch">
                          <input 
                            type="checkbox" 
                            checked={agent.active}
                            onChange={() => handleToggleAgent(agent.id, agent.active)}
                          />
                          <span className="slider round"></span>
                        </label>
                        <button 
                          className="btn btn-danger btn-sm"
                          onClick={(e) => {
                            e.stopPropagation();
                            handleRemoveAgent(agent.id);
                          }}
                        >
                          Remove
                        </button>
                      </div>
                    </div>
                    <div className="agent-role">{agent.role}</div>
                    <div className="agent-description">{agent.description}</div>
                    <div className="agent-details">
                      <div className="detail-item">
                        <span className="detail-label">Model:</span>
                        <span className="detail-value">{agent.model}</span>
                      </div>
                      <div className="detail-item">
                        <span className="detail-label">Capabilities:</span>
                        <div className="capabilities-list">
                          {agent.capabilities.map((capability, index) => (
                            <span key={index} className="capability-tag">{capability}</span>
                          ))}
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          <div className="available-agents">
            <h3>Available Agents</h3>
            <div className="available-agents-list">
              {availableAgents
                .filter(availableAgent => !agents.some(agent => agent.id === availableAgent.id))
                .map(agent => (
                  <div key={agent.id} className="available-agent-card">
                    <div className="agent-info">
                      <h4>{agent.name}</h4>
                      <div className="agent-role">{agent.role}</div>
                      <div className="agent-description">{agent.description}</div>
                    </div>
                    <button 
                      className="btn btn-primary"
                      onClick={(e) => {
                        e.stopPropagation();
                        handleAddAgent(agent.id);
                      }}
                    >
                      Add to Project
                    </button>
                  </div>
                ))
              }
              
              {availableAgents.length === 0 && (
                <p className="empty-message">No additional agents available</p>
              )}
            </div>
          </div>
        </div>
      )}

      {activeTab === 'team' && (
        <div className="team-config">
          <div className="team-members">
            <h3>Team Members</h3>
            {teamMembers.length === 0 ? (
              <p className="empty-message">No team members in this project</p>
            ) : (
              <div className="members-list">
                {teamMembers.map(member => (
                  <div key={member.id} className="member-card">
                    <div className="member-avatar">
                      <img src={member.avatar} alt={member.name} />
                    </div>
                    <div className="member-info">
                      <div className="member-name">{member.name}</div>
                      <div className="member-email">{member.email}</div>
                    </div>
                    <div className="member-role">
                      <select 
                        value={member.role} 
                        onChange={(e) => handleUpdateMemberRole(
                          member.id, 
                          e.target.value as 'admin' | 'editor' | 'viewer'
                        )}
                        disabled={member.role === 'admin'}
                        className="role-select"
                      >
                        <option value="admin">Admin</option>
                        <option value="editor">Editor</option>
                        <option value="viewer">Viewer</option>
                      </select>
                    </div>
                    <div className="member-actions">
                      {member.role !== 'admin' && (
                        <button 
                          className="btn btn-danger btn-sm"
                          onClick={(e) => {
                            e.stopPropagation();
                            handleRemoveTeamMember(member.id);
                          }}
                        >
                          Remove
                        </button>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          <div className="invite-member">
            <h3>Invite Team Member</h3>
            <form onSubmit={handleInviteTeamMember} className="invite-form">
              <div className="form-group">
                <label>Email</label>
                <input 
                  type="email" 
                  value={newMemberEmail}
                  onChange={(e) => setNewMemberEmail(e.target.value)}
                  placeholder="Enter email address"
                  required
                  className="form-control"
                />
              </div>
              
              <div className="form-group">
                <label>Role</label>
                <select 
                  value={newMemberRole}
                  onChange={(e) => setNewMemberRole(e.target.value as 'editor' | 'viewer')}
                  className="form-select"
                >
                  <option value="editor">Editor</option>
                  <option value="viewer">Viewer</option>
                </select>
              </div>
              
              <button 
                type="submit"
                className="btn btn-primary"
                disabled={!newMemberEmail.trim()}
              >
                Send Invitation
              </button>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default ProjectConfig; 