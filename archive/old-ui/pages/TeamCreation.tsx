import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';

interface AgentRole {
  id: string;
  name: string;
  description: string;
  capabilities: string[];
  isRequired: boolean;
}

const availableRoles: AgentRole[] = [
  {
    id: 'manager',
    name: 'Manager',
    description: 'Orchestrates the team and handles communication',
    capabilities: ['Task coordination', 'Progress tracking', 'Team supervision'],
    isRequired: true
  },
  {
    id: 'planner',
    name: 'Planner',
    description: 'Breaks down projects into tasks and creates strategic plans',
    capabilities: ['Project breakdown', 'Task prioritization', 'Timeline planning'],
    isRequired: false
  },
  {
    id: 'architect',
    name: 'Architect',
    description: 'Designs system architecture and makes technology decisions',
    capabilities: ['System design', 'Technology selection', 'Architecture planning'],
    isRequired: false
  },
  {
    id: 'coder',
    name: 'Coder',
    description: 'Implements features according to specifications',
    capabilities: ['Code implementation', 'Bug fixing', 'Code optimization'],
    isRequired: true
  },
  {
    id: 'tester',
    name: 'Tester',
    description: 'Verifies code quality and tests implementations',
    capabilities: ['Test creation', 'Quality assurance', 'Bug reporting'],
    isRequired: false
  }
];

const TeamCreation: React.FC = () => {
  const navigate = useNavigate();
  const [teamName, setTeamName] = useState('');
  const [teamDescription, setTeamDescription] = useState('');
  const [selectedRoles, setSelectedRoles] = useState<string[]>(
    availableRoles.filter(role => role.isRequired).map(role => role.id)
  );
  const [budgetLimit, setBudgetLimit] = useState<number>(50);
  const [modelTier, setModelTier] = useState<string>('standard');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState('');

  const handleRoleToggle = (roleId: string) => {
    const role = availableRoles.find(r => r.id === roleId);
    if (role?.isRequired) return;

    setSelectedRoles(prev => 
      prev.includes(roleId)
        ? prev.filter(id => id !== roleId)
        : [...prev, roleId]
    );
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setIsSubmitting(true);

    if (teamName.trim() === '') {
      setError('Team name is required');
      setIsSubmitting(false);
      return;
    }

    if (selectedRoles.length < 2) {
      setError('Please select at least one role in addition to the required roles');
      setIsSubmitting(false);
      return;
    }

    try {
      const response = await axios.post('/api/teams', {
        name: teamName,
        description: teamDescription,
        roles: selectedRoles,
        budget_limit: budgetLimit,
        model_tier: modelTier
      });

      navigate(`/workspace/${response.data.id}`);
    } catch (err) {
      setError('Failed to create team. Please try again.');
      console.error(err);
      setIsSubmitting(false);
    }
  };

  return (
    <div className="team-creation-container">
      <div className="creation-header">
        <h1>Create a New Team</h1>
        <p>Configure your AI agent team with specialized roles</p>
      </div>

      {error && (
        <div className="error-message">{error}</div>
      )}

      <form onSubmit={handleSubmit} className="creation-form">
        <div className="form-section">
          <h2>Team Details</h2>
          <div className="form-group">
            <label htmlFor="teamName">Team Name</label>
            <input
              type="text"
              id="teamName"
              value={teamName}
              onChange={e => setTeamName(e.target.value)}
              placeholder="Enter a name for your team"
              className="form-control"
              required
            />
          </div>

          <div className="form-group">
            <label htmlFor="teamDescription">Team Description</label>
            <textarea
              id="teamDescription"
              value={teamDescription}
              onChange={e => setTeamDescription(e.target.value)}
              placeholder="Describe what this team will be working on"
              className="form-control"
              rows={3}
            />
          </div>
        </div>

        <div className="form-section">
          <h2>Agent Roles</h2>
          <p className="section-description">Select which agent roles to include in your team</p>
          
          <div className="roles-grid">
            {availableRoles.map(role => (
              <div 
                key={role.id}
                className={`role-card ${selectedRoles.includes(role.id) ? 'selected' : ''} ${role.isRequired ? 'required' : ''}`}
                onClick={() => handleRoleToggle(role.id)}
              >
                <div className="role-header">
                  <h3>{role.name}</h3>
                  {role.isRequired && <span className="required-badge">Required</span>}
                </div>
                <p className="role-description">{role.description}</p>
                <div className="role-capabilities">
                  <h4>Capabilities:</h4>
                  <ul>
                    {role.capabilities.map((capability, index) => (
                      <li key={index}>{capability}</li>
                    ))}
                  </ul>
                </div>
                <div className="selection-indicator">
                  {selectedRoles.includes(role.id) ? '✓' : '+'}
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="form-section">
          <h2>Resource Configuration</h2>
          
          <div className="form-group">
            <label htmlFor="budgetLimit">Budget Limit (USD)</label>
            <input
              type="number"
              id="budgetLimit"
              min="10"
              max="1000"
              value={budgetLimit}
              onChange={e => setBudgetLimit(Number(e.target.value))}
              className="form-control"
            />
            <span className="form-hint">Maximum budget allowed for this team's operations</span>
          </div>

          <div className="form-group">
            <label>Model Tier</label>
            <div className="radio-group">
              <label className="radio-label">
                <input
                  type="radio"
                  name="modelTier"
                  value="prod_mgmt"
                  checked={modelTier === 'prod_mgmt'}
                  onChange={() => setModelTier('prod_mgmt')}
                />
                <span>Economy (GPT-3.5-Turbo)</span>
              </label>
              
              <label className="radio-label">
                <input
                  type="radio"
                  name="modelTier"
                  value="standard"
                  checked={modelTier === 'standard'}
                  onChange={() => setModelTier('standard')}
                />
                <span>Standard (GPT-4o)</span>
              </label>
              
              <label className="radio-label">
                <input
                  type="radio"
                  name="modelTier"
                  value="premium"
                  checked={modelTier === 'premium'}
                  onChange={() => setModelTier('premium')}
                />
                <span>Premium (Claude-3-Opus)</span>
              </label>
            </div>
          </div>
        </div>

        <div className="form-actions">
          <button 
            type="button" 
            className="btn btn-secondary"
            onClick={() => navigate('/')}
          >
            Cancel
          </button>
          <button 
            type="submit" 
            className="btn btn-primary"
            disabled={isSubmitting}
          >
            {isSubmitting ? 'Creating Team...' : 'Create Team'}
          </button>
        </div>
      </form>
    </div>
  );
};

export default TeamCreation; 