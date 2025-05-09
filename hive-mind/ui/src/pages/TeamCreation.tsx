import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { DragDropContext, Droppable, Draggable } from 'react-beautiful-dnd';

interface AgentRole {
  id: string;
  name: string;
  description: string;
  capabilities: string[];
  isRequired: boolean;
}

interface AgentConfig {
  id: string;
  roleId: string;
  name: string;
  model: string;
  budget: number;
  maxTokens: number;
  customInstructions: string;
}

interface TeamTemplate {
  id: string;
  name: string;
  description: string;
  roles: string[];
  budgetAllocation: { [key: string]: number };
  feedbackConfig: FeedbackConfig;
}

interface FeedbackConfig {
  autoRequest: boolean;
  frequency: 'each_step' | 'milestone' | 'completion';
  reviewSteps: boolean;
  incorporationStrategy: 'immediate' | 'review' | 'manual';
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
  },
  {
    id: 'reviewer',
    name: 'Reviewer',
    description: 'Reviews code quality and provides feedback',
    capabilities: ['Code review', 'Documentation review', 'Design evaluation'],
    isRequired: false
  },
  {
    id: 'devops',
    name: 'DevOps',
    description: 'Handles deployment and infrastructure concerns',
    capabilities: ['CI/CD setup', 'Infrastructure management', 'Deployment automation'],
    isRequired: false
  }
];

const teamTemplates: TeamTemplate[] = [
  {
    id: 'minimal',
    name: 'Minimal Team',
    description: 'Basic team with essential roles for small projects',
    roles: ['manager', 'coder'],
    budgetAllocation: {
      manager: 15,
      coder: 35
    },
    feedbackConfig: {
      autoRequest: true,
      frequency: 'completion',
      reviewSteps: false,
      incorporationStrategy: 'manual'
    }
  },
  {
    id: 'balanced',
    name: 'Balanced Team',
    description: 'Well-rounded team for medium-sized projects',
    roles: ['manager', 'planner', 'coder', 'tester'],
    budgetAllocation: {
      manager: 15,
      planner: 10,
      coder: 30,
      tester: 15
    },
    feedbackConfig: {
      autoRequest: true,
      frequency: 'milestone',
      reviewSteps: true,
      incorporationStrategy: 'review'
    }
  },
  {
    id: 'full',
    name: 'Enterprise Team',
    description: 'Comprehensive team for complex projects',
    roles: ['manager', 'planner', 'architect', 'coder', 'tester', 'reviewer', 'devops'],
    budgetAllocation: {
      manager: 15,
      planner: 10,
      architect: 15,
      coder: 25,
      tester: 15,
      reviewer: 10,
      devops: 10
    },
    feedbackConfig: {
      autoRequest: true,
      frequency: 'each_step',
      reviewSteps: true,
      incorporationStrategy: 'immediate'
    }
  }
];

const defaultFeedbackConfig: FeedbackConfig = {
  autoRequest: true,
  frequency: 'milestone',
  reviewSteps: true,
  incorporationStrategy: 'review'
};

const getTooltip = (key: string): string => {
  const tooltips: { [key: string]: string } = {
    autoRequest: 'Automatically request feedback at specified intervals',
    frequency: 'How often the system should request feedback',
    reviewSteps: 'Allow reviewing individual steps before proceeding',
    incorporationStrategy: 'How feedback should be incorporated into the workflow',
    budgetAllocation: 'Distribute budget across different agents',
    maxTokens: 'Maximum tokens an agent can use per request',
    customInstructions: 'Special instructions for this agent'
  };
  
  return tooltips[key] || 'No additional information available';
};

const TeamCreation: React.FC = () => {
  const navigate = useNavigate();
  const [teamName, setTeamName] = useState('');
  const [teamDescription, setTeamDescription] = useState('');
  const [selectedRoles, setSelectedRoles] = useState<string[]>(
    availableRoles.filter(role => role.isRequired).map(role => role.id)
  );
  const [agentConfigs, setAgentConfigs] = useState<AgentConfig[]>([]);
  const [totalBudget, setTotalBudget] = useState<number>(100);
  const [modelTier, setModelTier] = useState<string>('standard');
  const [workspaceSettings, setWorkspaceSettings] = useState({
    gitIntegration: false,
    autoCommit: false,
    documentationLevel: 'standard',
    securityChecks: true
  });
  const [feedbackConfig, setFeedbackConfig] = useState<FeedbackConfig>(defaultFeedbackConfig);
  const [activeTemplate, setActiveTemplate] = useState<string | null>(null);
  const [showTooltip, setShowTooltip] = useState<string | null>(null);
  const [isConfigOpen, setIsConfigOpen] = useState<{ [key: string]: boolean }>({});
  const [validationErrors, setValidationErrors] = useState<string[]>([]);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [showPreview, setShowPreview] = useState(false);
  const [savedConfigs, setSavedConfigs] = useState<{ id: string; name: string }[]>([]);
  
  // Initialize agent configs when roles change
  useEffect(() => {
    const newConfigs = selectedRoles
      .filter(roleId => !agentConfigs.some(config => config.roleId === roleId))
      .map(roleId => {
        const role = availableRoles.find(r => r.id === roleId);
        return {
          id: `${roleId}-${Date.now()}`,
          roleId,
          name: role?.name || '',
          model: modelTier,
          budget: Math.floor(totalBudget / selectedRoles.length),
          maxTokens: 4000,
          customInstructions: ''
        };
      });
    
    setAgentConfigs(prev => [...prev.filter(config => selectedRoles.includes(config.roleId)), ...newConfigs]);
  }, [selectedRoles, modelTier]);

  // Apply template
  const applyTemplate = (templateId: string) => {
    const template = teamTemplates.find(t => t.id === templateId);
    if (!template) return;
    
    setSelectedRoles(template.roles);
    setFeedbackConfig(template.feedbackConfig);
    setActiveTemplate(templateId);
    
    // Reset configs to match template
    const newConfigs = template.roles.map(roleId => {
      const role = availableRoles.find(r => r.id === roleId);
      return {
        id: `${roleId}-${Date.now()}`,
        roleId,
        name: role?.name || '',
        model: modelTier,
        budget: template.budgetAllocation[roleId] || Math.floor(totalBudget / template.roles.length),
        maxTokens: 4000,
        customInstructions: ''
      };
    });
    
    setAgentConfigs(newConfigs);
  };

  // Handle drag and drop
  const onDragEnd = (result: any) => {
    if (!result.destination) return;
    
    const items = Array.from(selectedRoles);
    const [reorderedItem] = items.splice(result.source.index, 1);
    items.splice(result.destination.index, 0, reorderedItem);
    
    setSelectedRoles(items);
  };

  // Toggle role selection
  const handleRoleToggle = (roleId: string) => {
    const role = availableRoles.find(r => r.id === roleId);
    if (role?.isRequired) return;

    setSelectedRoles(prev => 
      prev.includes(roleId)
        ? prev.filter(id => id !== roleId)
        : [...prev, roleId]
    );
    
    // Clear active template if roles don't match anymore
    setActiveTemplate(null);
  };

  // Update agent configuration
  const updateAgentConfig = (id: string, field: keyof AgentConfig, value: any) => {
    setAgentConfigs(prev => prev.map(config => 
      config.id === id ? { ...config, [field]: value } : config
    ));
  };

  // Save current config
  const saveCurrentConfig = () => {
    const configId = `config-${Date.now()}`;
    const configToSave = {
      id: configId,
      name: teamName || `Configuration ${savedConfigs.length + 1}`,
      selectedRoles,
      agentConfigs,
      feedbackConfig,
      workspaceSettings
    };
    
    localStorage.setItem(configId, JSON.stringify(configToSave));
    setSavedConfigs(prev => [...prev, { id: configId, name: configToSave.name }]);
  };

  // Load saved config
  const loadSavedConfig = (configId: string) => {
    const savedConfig = localStorage.getItem(configId);
    if (!savedConfig) return;
    
    const config = JSON.parse(savedConfig);
    setSelectedRoles(config.selectedRoles);
    setAgentConfigs(config.agentConfigs);
    setFeedbackConfig(config.feedbackConfig);
    setWorkspaceSettings(config.workspaceSettings);
    setActiveTemplate(null);
  };

  // Validate team configuration
  const validateTeam = (): string[] => {
    const errors: string[] = [];
    
    if (teamName.trim() === '') {
      errors.push('Team name is required');
    }
    
    if (selectedRoles.length < 2) {
      errors.push('At least two roles are required (including required roles)');
    }
    
    // Check for budget allocation
    const totalAllocated = agentConfigs.reduce((sum, config) => sum + config.budget, 0);
    if (totalAllocated > totalBudget) {
      errors.push(`Budget allocation exceeds total budget (${totalAllocated} > ${totalBudget})`);
    }
    
    return errors;
  };

  // Submit form
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    const errors = validateTeam();
    if (errors.length > 0) {
      setValidationErrors(errors);
      return;
    }
    
    setValidationErrors([]);
    setIsSubmitting(true);

    try {
      const response = await axios.post('/api/teams', {
        name: teamName,
        description: teamDescription,
        roles: selectedRoles,
        agentConfigs,
        totalBudget,
        feedbackConfig,
        workspaceSettings
      });

      navigate(`/workspace/${response.data.id}`);
    } catch (err) {
      setValidationErrors(['Failed to create team. Please try again.']);
      console.error(err);
      setIsSubmitting(false);
    }
  };

  // Toggle agent configuration panel
  const toggleConfigPanel = (roleId: string) => {
    setIsConfigOpen(prev => ({
      ...prev,
      [roleId]: !prev[roleId]
    }));
  };

  return (
    <div className="team-creation-container">
      <div className="creation-header">
        <h1>Create a New Team</h1>
        <p>Configure your AI agent team with specialized roles</p>
      </div>

      {validationErrors.length > 0 && (
        <div className="validation-errors">
          <h3>Please fix the following issues:</h3>
          <ul>
            {validationErrors.map((error, index) => (
              <li key={index}>{error}</li>
            ))}
          </ul>
        </div>
      )}

      <div className="team-templates">
        <h2>Team Templates</h2>
        <p className="section-description">Start with a pre-configured team setup</p>
        
        <div className="templates-grid">
          {teamTemplates.map(template => (
            <div 
              key={template.id}
              className={`template-card ${activeTemplate === template.id ? 'active' : ''}`}
              onClick={() => applyTemplate(template.id)}
            >
              <h3>{template.name}</h3>
              <p>{template.description}</p>
              <div className="template-roles">
                {template.roles.map(roleId => {
                  const role = availableRoles.find(r => r.id === roleId);
                  return (
                    <span key={roleId} className="role-tag">
                      {role?.name}
                    </span>
                  );
                })}
              </div>
            </div>
          ))}
        </div>
      </div>

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
          
          <div className="form-group">
            <label htmlFor="totalBudget">Total Budget (USD)</label>
            <input
              type="number"
              id="totalBudget"
              min="10"
              max="1000"
              value={totalBudget}
              onChange={e => setTotalBudget(Number(e.target.value))}
              className="form-control"
            />
            <span className="form-hint">Maximum budget allowed for this team's operations</span>
          </div>
        </div>

        <div className="form-section">
          <h2>Agent Roles</h2>
          <p className="section-description">
            Select and arrange agent roles for your team 
            <span 
              className="tooltip-trigger"
              onMouseEnter={() => setShowTooltip('roles')}
              onMouseLeave={() => setShowTooltip(null)}
            >
              ℹ️
            </span>
          </p>
          {showTooltip === 'roles' && (
            <div className="tooltip">
              Drag and drop roles to change their priority. Click on a role to select/deselect it.
            </div>
          )}
          
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
          
          <h3>Team Composition</h3>
          <div className="team-composition">
            <DragDropContext onDragEnd={onDragEnd}>
              <Droppable droppableId="team-roles" direction="horizontal">
                {(provided) => (
                  <div
                    className="composition-container"
                    {...provided.droppableProps}
                    ref={provided.innerRef}
                  >
                    {selectedRoles.length === 0 ? (
                      <div className="no-roles-selected">No roles selected</div>
                    ) : (
                      selectedRoles.map((roleId, index) => {
                        const role = availableRoles.find(r => r.id === roleId);
                        const config = agentConfigs.find(c => c.roleId === roleId);
                        
                        return (
                          <Draggable key={roleId} draggableId={roleId} index={index}>
                            {(provided) => (
                              <div
                                className="composition-role"
                                ref={provided.innerRef}
                                {...provided.draggableProps}
                                {...provided.dragHandleProps}
                              >
                                <div className="composition-role-header">
                                  <span className="role-name">{role?.name}</span>
                                  <button
                                    type="button"
                                    className="config-toggle"
                                    onClick={(e) => {
                                      e.stopPropagation();
                                      toggleConfigPanel(roleId);
                                    }}
                                  >
                                    {isConfigOpen[roleId] ? '▲' : '▼'}
                                  </button>
                                </div>
                                
                                {isConfigOpen[roleId] && config && (
                                  <div className="agent-config-panel">
                                    <div className="config-group">
                                      <label htmlFor={`${roleId}-name`}>Agent Name</label>
                                      <input
                                        type="text"
                                        id={`${roleId}-name`}
                                        value={config.name}
                                        onChange={(e) => updateAgentConfig(config.id, 'name', e.target.value)}
                                        className="config-input"
                                      />
                                    </div>
                                    
                                    <div className="config-group">
                                      <label htmlFor={`${roleId}-model`}>
                                        Model
                                        <span 
                                          className="tooltip-trigger"
                                          onMouseEnter={() => setShowTooltip(`model-${roleId}`)}
                                          onMouseLeave={() => setShowTooltip(null)}
                                        >
                                          ℹ️
                                        </span>
                                      </label>
                                      {showTooltip === `model-${roleId}` && (
                                        <div className="tooltip">
                                          Select the LLM model for this agent
                                        </div>
                                      )}
                                      <select
                                        id={`${roleId}-model`}
                                        value={config.model}
                                        onChange={(e) => updateAgentConfig(config.id, 'model', e.target.value)}
                                        className="config-select"
                                      >
                                        <option value="economy">Economy (GPT-3.5-Turbo)</option>
                                        <option value="standard">Standard (GPT-4o)</option>
                                        <option value="premium">Premium (Claude-3-Opus)</option>
                                      </select>
                                    </div>
                                    
                                    <div className="config-group">
                                      <label htmlFor={`${roleId}-budget`}>
                                        Budget Allocation
                                        <span 
                                          className="tooltip-trigger"
                                          onMouseEnter={() => setShowTooltip(`budget-${roleId}`)}
                                          onMouseLeave={() => setShowTooltip(null)}
                                        >
                                          ℹ️
                                        </span>
                                      </label>
                                      {showTooltip === `budget-${roleId}` && (
                                        <div className="tooltip">
                                          {getTooltip('budgetAllocation')}
                                        </div>
                                      )}
                                      <input
                                        type="range"
                                        id={`${roleId}-budget`}
                                        min="5"
                                        max={Math.min(totalBudget, 70)}
                                        value={config.budget}
                                        onChange={(e) => updateAgentConfig(config.id, 'budget', Number(e.target.value))}
                                        className="config-slider"
                                      />
                                      <div className="slider-value">${config.budget}</div>
                                    </div>
                                    
                                    <div className="config-group">
                                      <label htmlFor={`${roleId}-tokens`}>Max Tokens</label>
                                      <input
                                        type="number"
                                        id={`${roleId}-tokens`}
                                        min="1000"
                                        max="16000"
                                        step="1000"
                                        value={config.maxTokens}
                                        onChange={(e) => updateAgentConfig(config.id, 'maxTokens', Number(e.target.value))}
                                        className="config-input"
                                      />
                                    </div>
                                    
                                    <div className="config-group">
                                      <label htmlFor={`${roleId}-instructions`}>Custom Instructions</label>
                                      <textarea
                                        id={`${roleId}-instructions`}
                                        value={config.customInstructions}
                                        onChange={(e) => updateAgentConfig(config.id, 'customInstructions', e.target.value)}
                                        className="config-textarea"
                                        rows={3}
                                        placeholder="Add any special instructions for this agent..."
                                      />
                                    </div>
                                  </div>
                                )}
                              </div>
                            )}
                          </Draggable>
                        );
                      })
                    )}
                    {provided.placeholder}
                  </div>
                )}
              </Droppable>
            </DragDropContext>
          </div>
        </div>

        <div className="form-section">
          <h2>Feedback Loop Configuration</h2>
          <p className="section-description">Configure how the team handles feedback during tasks</p>
          
          <div className="feedback-config">
            <div className="config-group">
              <label className="checkbox-label">
                <input
                  type="checkbox"
                  checked={feedbackConfig.autoRequest}
                  onChange={(e) => setFeedbackConfig({...feedbackConfig, autoRequest: e.target.checked})}
                />
                <span>Automatic Feedback Requests</span>
                <span 
                  className="tooltip-trigger"
                  onMouseEnter={() => setShowTooltip('autoRequest')}
                  onMouseLeave={() => setShowTooltip(null)}
                >
                  ℹ️
                </span>
              </label>
              {showTooltip === 'autoRequest' && (
                <div className="tooltip">{getTooltip('autoRequest')}</div>
              )}
            </div>
            
            <div className="config-group">
              <label>
                Feedback Frequency
                <span 
                  className="tooltip-trigger"
                  onMouseEnter={() => setShowTooltip('frequency')}
                  onMouseLeave={() => setShowTooltip(null)}
                >
                  ℹ️
                </span>
              </label>
              {showTooltip === 'frequency' && (
                <div className="tooltip">{getTooltip('frequency')}</div>
              )}
              <div className="radio-group">
                <label className="radio-label">
                  <input
                    type="radio"
                    name="frequency"
                    value="each_step"
                    checked={feedbackConfig.frequency === 'each_step'}
                    onChange={() => setFeedbackConfig({...feedbackConfig, frequency: 'each_step'})}
                  />
                  <span>After Each Step</span>
                </label>
                
                <label className="radio-label">
                  <input
                    type="radio"
                    name="frequency"
                    value="milestone"
                    checked={feedbackConfig.frequency === 'milestone'}
                    onChange={() => setFeedbackConfig({...feedbackConfig, frequency: 'milestone'})}
                  />
                  <span>At Milestones</span>
                </label>
                
                <label className="radio-label">
                  <input
                    type="radio"
                    name="frequency"
                    value="completion"
                    checked={feedbackConfig.frequency === 'completion'}
                    onChange={() => setFeedbackConfig({...feedbackConfig, frequency: 'completion'})}
                  />
                  <span>On Completion</span>
                </label>
              </div>
            </div>
            
            <div className="config-group">
              <label className="checkbox-label">
                <input
                  type="checkbox"
                  checked={feedbackConfig.reviewSteps}
                  onChange={(e) => setFeedbackConfig({...feedbackConfig, reviewSteps: e.target.checked})}
                />
                <span>Step-by-Step Review</span>
                <span 
                  className="tooltip-trigger"
                  onMouseEnter={() => setShowTooltip('reviewSteps')}
                  onMouseLeave={() => setShowTooltip(null)}
                >
                  ℹ️
                </span>
              </label>
              {showTooltip === 'reviewSteps' && (
                <div className="tooltip">{getTooltip('reviewSteps')}</div>
              )}
            </div>
            
            <div className="config-group">
              <label>
                Feedback Incorporation Strategy
                <span 
                  className="tooltip-trigger"
                  onMouseEnter={() => setShowTooltip('incorporation')}
                  onMouseLeave={() => setShowTooltip(null)}
                >
                  ℹ️
                </span>
              </label>
              {showTooltip === 'incorporation' && (
                <div className="tooltip">{getTooltip('incorporationStrategy')}</div>
              )}
              <div className="radio-group">
                <label className="radio-label">
                  <input
                    type="radio"
                    name="incorporation"
                    value="immediate"
                    checked={feedbackConfig.incorporationStrategy === 'immediate'}
                    onChange={() => setFeedbackConfig({...feedbackConfig, incorporationStrategy: 'immediate'})}
                  />
                  <span>Immediate Integration</span>
                </label>
                
                <label className="radio-label">
                  <input
                    type="radio"
                    name="incorporation"
                    value="review"
                    checked={feedbackConfig.incorporationStrategy === 'review'}
                    onChange={() => setFeedbackConfig({...feedbackConfig, incorporationStrategy: 'review'})}
                  />
                  <span>Review Before Integration</span>
                </label>
                
                <label className="radio-label">
                  <input
                    type="radio"
                    name="incorporation"
                    value="manual"
                    checked={feedbackConfig.incorporationStrategy === 'manual'}
                    onChange={() => setFeedbackConfig({...feedbackConfig, incorporationStrategy: 'manual'})}
                  />
                  <span>Manual Integration</span>
                </label>
              </div>
            </div>
          </div>
        </div>
        
        <div className="form-section">
          <h2>Workspace Configuration</h2>
          <p className="section-description">Configure the workspace for your team</p>
          
          <div className="workspace-config">
            <div className="config-group">
              <label className="checkbox-label">
                <input
                  type="checkbox"
                  checked={workspaceSettings.gitIntegration}
                  onChange={(e) => setWorkspaceSettings({...workspaceSettings, gitIntegration: e.target.checked})}
                />
                <span>Git Integration</span>
              </label>
            </div>
            
            <div className="config-group">
              <label className="checkbox-label">
                <input
                  type="checkbox"
                  checked={workspaceSettings.autoCommit}
                  onChange={(e) => setWorkspaceSettings({...workspaceSettings, autoCommit: e.target.checked})}
                  disabled={!workspaceSettings.gitIntegration}
                />
                <span>Automatic Commits</span>
              </label>
            </div>
            
            <div className="config-group">
              <label>Documentation Level</label>
              <select
                value={workspaceSettings.documentationLevel}
                onChange={(e) => setWorkspaceSettings({...workspaceSettings, documentationLevel: e.target.value})}
                className="config-select"
              >
                <option value="minimal">Minimal</option>
                <option value="standard">Standard</option>
                <option value="extensive">Extensive</option>
              </select>
            </div>
            
            <div className="config-group">
              <label className="checkbox-label">
                <input
                  type="checkbox"
                  checked={workspaceSettings.securityChecks}
                  onChange={(e) => setWorkspaceSettings({...workspaceSettings, securityChecks: e.target.checked})}
                />
                <span>Security Checks</span>
              </label>
            </div>
          </div>
        </div>
        
        <div className="team-actions">
          <div className="save-load-actions">
            <button 
              type="button" 
              className="btn btn-secondary"
              onClick={saveCurrentConfig}
            >
              Save Configuration
            </button>
            
            {savedConfigs.length > 0 && (
              <select 
                className="load-config-select"
                onChange={(e) => {
                  if (e.target.value) loadSavedConfig(e.target.value);
                }}
                value=""
              >
                <option value="">Load Configuration</option>
                {savedConfigs.map(config => (
                  <option key={config.id} value={config.id}>{config.name}</option>
                ))}
              </select>
            )}
          </div>
          
          <div className="preview-action">
            <button 
              type="button" 
              className="btn btn-secondary"
              onClick={() => setShowPreview(!showPreview)}
            >
              {showPreview ? 'Hide Preview' : 'Preview Team'}
            </button>
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
        </div>
      </form>
      
      {showPreview && (
        <div className="team-preview">
          <h2>Team Preview</h2>
          
          <div className="preview-section">
            <h3>Team Details</h3>
            <p><strong>Name:</strong> {teamName || 'Unnamed Team'}</p>
            <p><strong>Description:</strong> {teamDescription || 'No description provided'}</p>
            <p><strong>Total Budget:</strong> ${totalBudget}</p>
          </div>
          
          <div className="preview-section">
            <h3>Team Composition</h3>
            <div className="preview-roles">
              {selectedRoles.map(roleId => {
                const role = availableRoles.find(r => r.id === roleId);
                const config = agentConfigs.find(c => c.roleId === roleId);
                
                return (
                  <div key={roleId} className="preview-role">
                    <div className="preview-role-header">
                      <h4>{role?.name}</h4>
                      <span className="preview-budget">${config?.budget}</span>
                    </div>
                    <p>{role?.description}</p>
                    {config?.customInstructions && (
                      <div className="preview-instructions">
                        <strong>Custom Instructions:</strong>
                        <p>{config.customInstructions}</p>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
          
          <div className="preview-section">
            <h3>Feedback Configuration</h3>
            <ul>
              <li><strong>Auto Request:</strong> {feedbackConfig.autoRequest ? 'Enabled' : 'Disabled'}</li>
              <li><strong>Frequency:</strong> {
                feedbackConfig.frequency === 'each_step' ? 'After Each Step' :
                feedbackConfig.frequency === 'milestone' ? 'At Milestones' : 'On Completion'
              }</li>
              <li><strong>Step Review:</strong> {feedbackConfig.reviewSteps ? 'Enabled' : 'Disabled'}</li>
              <li><strong>Incorporation:</strong> {
                feedbackConfig.incorporationStrategy === 'immediate' ? 'Immediate Integration' :
                feedbackConfig.incorporationStrategy === 'review' ? 'Review Before Integration' : 'Manual Integration'
              }</li>
            </ul>
          </div>
        </div>
      )}
    </div>
  );
};

export default TeamCreation; 