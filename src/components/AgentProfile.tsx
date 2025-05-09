import React, { useState, useEffect } from 'react';
import { Line, Bar, Radar, Pie } from 'react-chartjs-2';
import { Chart, registerables } from 'chart.js';

// Register Chart.js components
Chart.register(...registerables);

// TypeScript interfaces
interface Agent {
  id: string;
  name: string;
  role: string;
  avatar: string;
  capabilities: string[];
  specializations: string[];
  personality: {
    traits: string[];
    communicationStyle: string;
  };
  performance: {
    tasksCompleted: number;
    successRate: number;
    averageCompletionTime: number;
  };
  feedbackLoop: {
    averageIterations: number;
    improvementRate: number;
    successfulFeedbackCycles: number;
  };
  resourceUsage: {
    tokens: number;
    computationTime: number;
    costToDate: number;
  };
  skills: {
    category: string;
    level: number;
  }[];
  integrations: string[];
  recentActivities: {
    id: string;
    timestamp: string;
    action: string;
    description: string;
    associatedTask?: string;
  }[];
  communicationAnalytics: {
    messageFrequency: {
      dates: string[];
      counts: number[];
    };
    responseTime: {
      averageMs: number;
      distribution: {
        range: string;
        count: number;
      }[];
    };
    sentiment: {
      positive: number;
      neutral: number;
      negative: number;
    };
    topicsByFrequency: {
      topic: string;
      count: number;
    }[];
    collaborationByAgent: {
      agentId: string;
      agentName: string;
      messageCount: number;
      collaborationScore: number;
    }[];
    communicationEfficiency: number;
  };
}

interface AgentProfileProps {
  agentId: string;
}

const AgentProfile: React.FC<AgentProfileProps> = ({ agentId }) => {
  const [agent, setAgent] = useState<Agent | null>(null);
  const [activeTab, setActiveTab] = useState('overview');
  const [isEditing, setIsEditing] = useState(false);
  const [editableAgent, setEditableAgent] = useState<Partial<Agent> | null>(null);

  useEffect(() => {
    // Fetch agent data from API
    const fetchAgentData = async () => {
      try {
        // In a real implementation, this would be an API call
        // For now, using mock data
        const response = await fetch(`/mock-api/api/agents/${agentId}`);
        const data = await response.json();
        setAgent(data);
        setEditableAgent(data);
      } catch (error) {
        console.error('Error fetching agent data:', error);
      }
    };

    fetchAgentData();
  }, [agentId]);

  const handleSaveChanges = async () => {
    try {
      // In a real implementation, this would be an API call
      // PUT /api/agents/${agentId}
      console.log('Saving changes:', editableAgent);
      
      // Update local state
      setAgent(editableAgent as Agent);
      setIsEditing(false);
    } catch (error) {
      console.error('Error saving agent data:', error);
    }
  };

  const handleCancelEdit = () => {
    setEditableAgent(agent);
    setIsEditing(false);
  };

  if (!agent) {
    return <div className="loading">Loading agent profile...</div>;
  }

  const messageFrequencyChartData = {
    labels: agent.communicationAnalytics.messageFrequency.dates,
    datasets: [
      {
        label: 'Message Volume',
        data: agent.communicationAnalytics.messageFrequency.counts,
        borderColor: 'rgba(75, 192, 192, 1)',
        backgroundColor: 'rgba(75, 192, 192, 0.2)',
        fill: true,
      },
    ],
  };

  const responseTimeChartData = {
    labels: agent.communicationAnalytics.responseTime.distribution.map(d => d.range),
    datasets: [
      {
        label: 'Response Time Distribution',
        data: agent.communicationAnalytics.responseTime.distribution.map(d => d.count),
        backgroundColor: 'rgba(153, 102, 255, 0.6)',
      },
    ],
  };

  const sentimentChartData = {
    labels: ['Positive', 'Neutral', 'Negative'],
    datasets: [
      {
        data: [
          agent.communicationAnalytics.sentiment.positive,
          agent.communicationAnalytics.sentiment.neutral,
          agent.communicationAnalytics.sentiment.negative,
        ],
        backgroundColor: [
          'rgba(75, 192, 192, 0.6)',
          'rgba(255, 206, 86, 0.6)',
          'rgba(255, 99, 132, 0.6)',
        ],
      },
    ],
  };

  const collaborationChartData = {
    labels: agent.communicationAnalytics.collaborationByAgent.map(a => a.agentName),
    datasets: [
      {
        label: 'Message Count',
        data: agent.communicationAnalytics.collaborationByAgent.map(a => a.messageCount),
        backgroundColor: 'rgba(54, 162, 235, 0.6)',
      },
      {
        label: 'Collaboration Score',
        data: agent.communicationAnalytics.collaborationByAgent.map(a => a.collaborationScore),
        backgroundColor: 'rgba(255, 159, 64, 0.6)',
      },
    ],
  };

  const skillsChartData = {
    labels: agent.skills.map(s => s.category),
    datasets: [
      {
        label: 'Skill Level',
        data: agent.skills.map(s => s.level),
        backgroundColor: 'rgba(255, 99, 132, 0.2)',
        borderColor: 'rgba(255, 99, 132, 1)',
        pointBackgroundColor: 'rgba(255, 99, 132, 1)',
        pointBorderColor: '#fff',
        pointHoverBackgroundColor: '#fff',
        pointHoverBorderColor: 'rgba(255, 99, 132, 1)',
      },
    ],
  };

  return (
    <div className="agent-profile">
      <div className="profile-header">
        <div className="avatar-container">
          {agent.avatar ? (
            <img src={agent.avatar} alt={`${agent.name} avatar`} className="agent-avatar" />
          ) : (
            <div className="avatar-placeholder">
              {agent.name.charAt(0).toUpperCase()}
            </div>
          )}
          {isEditing && (
            <button className="edit-avatar-btn">
              Change Avatar
            </button>
          )}
        </div>
        <div className="agent-info">
          <h1>{agent.name}</h1>
          <span className="agent-role">{agent.role}</span>
          {!isEditing ? (
            <button 
              className="edit-profile-btn"
              onClick={() => setIsEditing(true)}
            >
              Edit Profile
            </button>
          ) : (
            <div className="edit-actions">
              <button 
                className="save-btn"
                onClick={handleSaveChanges}
              >
                Save Changes
              </button>
              <button 
                className="cancel-btn"
                onClick={handleCancelEdit}
              >
                Cancel
              </button>
            </div>
          )}
        </div>
      </div>

      <div className="profile-tabs">
        <button 
          className={`tab-btn ${activeTab === 'overview' ? 'active' : ''}`}
          onClick={() => setActiveTab('overview')}
        >
          Overview
        </button>
        <button 
          className={`tab-btn ${activeTab === 'communication' ? 'active' : ''}`}
          onClick={() => setActiveTab('communication')}
        >
          Communication Analysis
        </button>
        <button 
          className={`tab-btn ${activeTab === 'performance' ? 'active' : ''}`}
          onClick={() => setActiveTab('performance')}
        >
          Performance
        </button>
        <button 
          className={`tab-btn ${activeTab === 'activities' ? 'active' : ''}`}
          onClick={() => setActiveTab('activities')}
        >
          Recent Activities
        </button>
        <button 
          className={`tab-btn ${activeTab === 'settings' ? 'active' : ''}`}
          onClick={() => setActiveTab('settings')}
        >
          Settings
        </button>
      </div>

      <div className="profile-content">
        {activeTab === 'overview' && (
          <div className="overview-tab">
            <div className="section">
              <h2>Capabilities & Specializations</h2>
              <div className="tags-container">
                {agent.capabilities.map((capability, index) => (
                  <span key={`capability-${index}`} className="tag capability-tag">
                    {capability}
                  </span>
                ))}
                {agent.specializations.map((specialization, index) => (
                  <span key={`specialization-${index}`} className="tag specialization-tag">
                    {specialization}
                  </span>
                ))}
              </div>
            </div>

            <div className="section">
              <h2>Personality</h2>
              <p className="communication-style">
                <strong>Communication Style:</strong> {agent.personality.communicationStyle}
              </p>
              <div className="tags-container">
                {agent.personality.traits.map((trait, index) => (
                  <span key={`trait-${index}`} className="tag personality-tag">
                    {trait}
                  </span>
                ))}
              </div>
            </div>

            <div className="section">
              <h2>Skills & Knowledge</h2>
              <div className="chart-container">
                <Radar data={skillsChartData} />
              </div>
            </div>

            <div className="section">
              <h2>Resource Usage</h2>
              <div className="stats-grid">
                <div className="stat-card">
                  <h3>Tokens Used</h3>
                  <div className="stat-value">{agent.resourceUsage.tokens.toLocaleString()}</div>
                </div>
                <div className="stat-card">
                  <h3>Computation Time</h3>
                  <div className="stat-value">{agent.resourceUsage.computationTime.toFixed(2)}s</div>
                </div>
                <div className="stat-card">
                  <h3>Cost to Date</h3>
                  <div className="stat-value">${agent.resourceUsage.costToDate.toFixed(2)}</div>
                </div>
              </div>
            </div>

            <div className="section">
              <h2>Integrations</h2>
              <div className="integrations-list">
                {agent.integrations.map((integration, index) => (
                  <div key={`integration-${index}`} className="integration-item">
                    {integration}
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {activeTab === 'communication' && (
          <div className="communication-tab">
            <div className="section">
              <h2>Message Frequency & Volume</h2>
              <div className="chart-container">
                <Line data={messageFrequencyChartData} />
              </div>
            </div>

            <div className="section">
              <h2>Response Time Analysis</h2>
              <div className="stats-grid">
                <div className="stat-card">
                  <h3>Average Response Time</h3>
                  <div className="stat-value">
                    {(agent.communicationAnalytics.responseTime.averageMs / 1000).toFixed(2)}s
                  </div>
                </div>
              </div>
              <div className="chart-container">
                <Bar data={responseTimeChartData} />
              </div>
            </div>

            <div className="section">
              <h2>Sentiment Analysis</h2>
              <div className="chart-container pie-chart">
                <Pie data={sentimentChartData} />
              </div>
            </div>

            <div className="section">
              <h2>Common Topics</h2>
              <div className="topics-list">
                {agent.communicationAnalytics.topicsByFrequency.map((topic, index) => (
                  <div key={`topic-${index}`} className="topic-item">
                    <span className="topic-name">{topic.topic}</span>
                    <span className="topic-count">{topic.count}</span>
                  </div>
                ))}
              </div>
            </div>

            <div className="section">
              <h2>Collaboration Metrics</h2>
              <div className="chart-container">
                <Bar data={collaborationChartData} />
              </div>
            </div>

            <div className="section">
              <h2>Communication Efficiency</h2>
              <div className="efficiency-meter">
                <div 
                  className="efficiency-fill" 
                  style={{ width: `${agent.communicationAnalytics.communicationEfficiency * 100}%` }}
                ></div>
                <span className="efficiency-value">
                  {(agent.communicationAnalytics.communicationEfficiency * 100).toFixed(1)}%
                </span>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'performance' && (
          <div className="performance-tab">
            <div className="section">
              <h2>Task Performance</h2>
              <div className="stats-grid">
                <div className="stat-card">
                  <h3>Tasks Completed</h3>
                  <div className="stat-value">{agent.performance.tasksCompleted}</div>
                </div>
                <div className="stat-card">
                  <h3>Success Rate</h3>
                  <div className="stat-value">{(agent.performance.successRate * 100).toFixed(1)}%</div>
                </div>
                <div className="stat-card">
                  <h3>Avg. Completion Time</h3>
                  <div className="stat-value">{agent.performance.averageCompletionTime.toFixed(1)}s</div>
                </div>
              </div>
            </div>

            <div className="section">
              <h2>Feedback Loop Statistics</h2>
              <div className="stats-grid">
                <div className="stat-card">
                  <h3>Avg. Iterations</h3>
                  <div className="stat-value">{agent.feedbackLoop.averageIterations.toFixed(1)}</div>
                </div>
                <div className="stat-card">
                  <h3>Improvement Rate</h3>
                  <div className="stat-value">{(agent.feedbackLoop.improvementRate * 100).toFixed(1)}%</div>
                </div>
                <div className="stat-card">
                  <h3>Successful Feedback Cycles</h3>
                  <div className="stat-value">{agent.feedbackLoop.successfulFeedbackCycles}</div>
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'activities' && (
          <div className="activities-tab">
            <div className="section">
              <h2>Recent Activities</h2>
              <div className="activity-timeline">
                {agent.recentActivities.map((activity) => (
                  <div key={activity.id} className="activity-item">
                    <div className="activity-time">
                      {new Date(activity.timestamp).toLocaleString()}
                    </div>
                    <div className="activity-info">
                      <h3>{activity.action}</h3>
                      <p>{activity.description}</p>
                      {activity.associatedTask && (
                        <div className="associated-task">
                          Task ID: {activity.associatedTask}
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {activeTab === 'settings' && (
          <div className="settings-tab">
            <div className="section">
              <h2>Agent Configuration</h2>
              {isEditing ? (
                <div className="form-container">
                  <div className="form-group">
                    <label htmlFor="agent-name">Name</label>
                    <input 
                      id="agent-name"
                      type="text" 
                      value={editableAgent?.name || ''} 
                      onChange={(e) => setEditableAgent({...editableAgent, name: e.target.value})}
                    />
                  </div>
                  <div className="form-group">
                    <label htmlFor="communication-style">Communication Style</label>
                    <select 
                      id="communication-style"
                      value={editableAgent?.personality?.communicationStyle || ''}
                      onChange={(e) => {
                        const updatedPersonality = {...editableAgent?.personality, communicationStyle: e.target.value};
                        setEditableAgent({...editableAgent, personality: updatedPersonality});
                      }}
                    >
                      <option value="Formal">Formal</option>
                      <option value="Casual">Casual</option>
                      <option value="Technical">Technical</option>
                      <option value="Collaborative">Collaborative</option>
                      <option value="Direct">Direct</option>
                    </select>
                  </div>
                  {/* More configuration options would go here */}
                </div>
              ) : (
                <div className="view-only-settings">
                  <p>Switch to edit mode to modify agent configuration.</p>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default AgentProfile; 