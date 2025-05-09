import React, { useState, useEffect } from 'react';
import axios from 'axios';

interface Team {
  id: string;
  name: string;
  budget_limit: number;
  model_tier: string;
  budget_used: number;
}

interface ModelTier {
  id: string;
  name: string;
  model: string;
  max_tokens: number;
  cost_per_1k_tokens: number;
}

interface TokenUsage {
  team_id: string;
  team_name: string;
  date: string;
  token_count: number;
  cost: number;
}

const modelTiers: ModelTier[] = [
  {
    id: 'prod_mgmt',
    name: 'Economy',
    model: 'gpt-3.5-turbo',
    max_tokens: 2048,
    cost_per_1k_tokens: 0.0015
  },
  {
    id: 'standard',
    name: 'Standard',
    model: 'gpt-4o',
    max_tokens: 4096,
    cost_per_1k_tokens: 0.01
  },
  {
    id: 'premium',
    name: 'Premium',
    model: 'claude-3-opus',
    max_tokens: 8000,
    cost_per_1k_tokens: 0.03
  }
];

const CostManagement: React.FC = () => {
  const [teams, setTeams] = useState<Team[]>([]);
  const [tokenUsage, setTokenUsage] = useState<TokenUsage[]>([]);
  const [selectedTeam, setSelectedTeam] = useState<string>('');
  const [editBudget, setEditBudget] = useState<number | null>(null);
  const [editModelTier, setEditModelTier] = useState<string | null>(null);
  const [isUpdating, setIsUpdating] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  const [timeRange, setTimeRange] = useState<'day' | 'week' | 'month'>('week');

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [teamsResponse, usageResponse] = await Promise.all([
          axios.get('/api/teams'),
          axios.get(`/api/cost-domain/usage?range=${timeRange}`)
        ]);
        
        setTeams(teamsResponse.data);
        setTokenUsage(usageResponse.data);
      } catch (err) {
        setError('Failed to load cost management data');
        console.error(err);
      } finally {
        setIsLoading(false);
      }
    };

    fetchData();
  }, [timeRange]);

  const totalBudget = teams.reduce((sum, team) => sum + team.budget_limit, 0);
  const totalUsed = teams.reduce((sum, team) => sum + team.budget_used, 0);
  const percentUsed = totalBudget > 0 ? (totalUsed / totalBudget) * 100 : 0;

  const handleTeamSelect = (teamId: string) => {
    setSelectedTeam(teamId);
    const team = teams.find(t => t.id === teamId);
    
    if (team) {
      setEditBudget(team.budget_limit);
      setEditModelTier(team.model_tier);
    }
  };

  const handleBudgetChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setEditBudget(Number(e.target.value));
  };

  const handleModelTierChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setEditModelTier(e.target.value);
  };

  const handleUpdateSettings = async () => {
    if (!selectedTeam || editBudget === null || !editModelTier) return;
    
    setIsUpdating(true);
    
    try {
      await axios.patch(`/api/teams/${selectedTeam}/cost-settings`, {
        budget_limit: editBudget,
        model_tier: editModelTier
      });
      
      // Update the local state
      setTeams(teams.map(team => 
        team.id === selectedTeam 
          ? { ...team, budget_limit: editBudget, model_tier: editModelTier }
          : team
      ));
      
      setError('');
    } catch (err) {
      setError('Failed to update cost settings');
      console.error(err);
    } finally {
      setIsUpdating(false);
    }
  };

  const getTeamTokenUsage = (teamId: string) => {
    return tokenUsage.filter(usage => usage.team_id === teamId);
  };

  const getModelTierDetails = (tierId: string) => {
    return modelTiers.find(tier => tier.id === tierId) || modelTiers[1]; // Default to standard
  };

  if (isLoading) {
    return (
      <div className="loading-container">
        <div className="spinner"></div>
        <p>Loading cost data...</p>
      </div>
    );
  }

  return (
    <div className="cost-management-container">
      <div className="cost-header">
        <h1>Cost Management</h1>
        <div className="time-range-selector">
          <button 
            className={`btn ${timeRange === 'day' ? 'btn-primary' : 'btn-secondary'}`}
            onClick={() => setTimeRange('day')}
          >
            Day
          </button>
          <button 
            className={`btn ${timeRange === 'week' ? 'btn-primary' : 'btn-secondary'}`}
            onClick={() => setTimeRange('week')}
          >
            Week
          </button>
          <button 
            className={`btn ${timeRange === 'month' ? 'btn-primary' : 'btn-secondary'}`}
            onClick={() => setTimeRange('month')}
          >
            Month
          </button>
        </div>
      </div>

      {error && (
        <div className="error-message">{error}</div>
      )}

      <div className="overview-section">
        <h2>Budget Overview</h2>
        <div className="stats-cards">
          <div className="stat-card">
            <h3>Total Budget</h3>
            <div className="stat-value">${totalBudget.toFixed(2)}</div>
          </div>
          <div className="stat-card">
            <h3>Total Used</h3>
            <div className="stat-value">${totalUsed.toFixed(2)}</div>
          </div>
          <div className="stat-card">
            <h3>Remaining</h3>
            <div className="stat-value">${(totalBudget - totalUsed).toFixed(2)}</div>
          </div>
        </div>

        <div className="budget-progress">
          <div className="progress-bar">
            <div 
              className="progress-fill" 
              style={{ width: `${Math.min(percentUsed, 100)}%` }}
            ></div>
          </div>
          <div className="progress-label">
            {percentUsed.toFixed(1)}% Used
          </div>
        </div>
      </div>

      <div className="team-config-section">
        <div className="team-list">
          <h2>Teams</h2>
          <div className="teams-table-container">
            <table className="teams-table">
              <thead>
                <tr>
                  <th>Team</th>
                  <th>Budget</th>
                  <th>Used</th>
                  <th>Model Tier</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {teams.map(team => (
                  <tr 
                    key={team.id} 
                    className={team.id === selectedTeam ? 'selected' : ''}
                    onClick={() => handleTeamSelect(team.id)}
                  >
                    <td>{team.name}</td>
                    <td>${team.budget_limit.toFixed(2)}</td>
                    <td>${team.budget_used.toFixed(2)}</td>
                    <td>{getModelTierDetails(team.model_tier).name}</td>
                    <td>
                      <span className={`status-badge ${team.budget_used < team.budget_limit ? 'active' : 'warning'}`}>
                        {team.budget_used < team.budget_limit ? 'Active' : 'Over Budget'}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        <div className="team-settings">
          <h2>Team Cost Settings</h2>
          {selectedTeam ? (
            <div className="settings-form">
              <div className="form-group">
                <label htmlFor="budgetLimit">Budget Limit (USD)</label>
                <input
                  type="number"
                  id="budgetLimit"
                  value={editBudget || 0}
                  onChange={handleBudgetChange}
                  min="10"
                  max="1000"
                  step="5"
                  className="form-control"
                />
              </div>

              <div className="form-group">
                <label htmlFor="modelTier">Model Tier</label>
                <select
                  id="modelTier"
                  value={editModelTier || ''}
                  onChange={handleModelTierChange}
                  className="form-control"
                >
                  {modelTiers.map(tier => (
                    <option key={tier.id} value={tier.id}>
                      {tier.name} ({tier.model}) - ${tier.cost_per_1k_tokens} per 1k tokens
                    </option>
                  ))}
                </select>
              </div>

              <button
                className="btn btn-primary"
                onClick={handleUpdateSettings}
                disabled={isUpdating}
              >
                {isUpdating ? 'Updating...' : 'Update Settings'}
              </button>
            </div>
          ) : (
            <div className="empty-state">
              <p>Select a team to modify its cost settings</p>
            </div>
          )}
        </div>
      </div>

      <div className="usage-section">
        <h2>Token Usage History</h2>
        {selectedTeam ? (
          <div className="usage-details">
            <h3>{teams.find(t => t.id === selectedTeam)?.name}</h3>
            {getTeamTokenUsage(selectedTeam).length === 0 ? (
              <p>No usage data available for selected time range</p>
            ) : (
              <table className="usage-table">
                <thead>
                  <tr>
                    <th>Date</th>
                    <th>Tokens</th>
                    <th>Cost</th>
                  </tr>
                </thead>
                <tbody>
                  {getTeamTokenUsage(selectedTeam).map((usage, index) => (
                    <tr key={index}>
                      <td>{new Date(usage.date).toLocaleDateString()}</td>
                      <td>{usage.token_count.toLocaleString()}</td>
                      <td>${usage.cost.toFixed(4)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        ) : (
          <div className="empty-state">
            <p>Select a team to view token usage history</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default CostManagement; 