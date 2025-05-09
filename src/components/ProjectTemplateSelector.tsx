import React, { useState, useEffect } from 'react';
import axios from 'axios';

interface Template {
  id: string;
  name: string;
  description: string;
  icon: string;
  default_roles: string[];
  files_structure: any[];
  workflow: string;
}

interface ProjectTemplateSelectorProps {
  onSelect: (templateId: string) => void;
  selectedTemplateId: string | null;
}

const ProjectTemplateSelector: React.FC<ProjectTemplateSelectorProps> = ({
  onSelect,
  selectedTemplateId
}) => {
  const [templates, setTemplates] = useState<Template[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchTemplates = async () => {
      try {
        setIsLoading(true);
        const response = await axios.get('/api/project-templates');
        setTemplates(response.data);
        setError('');
      } catch (err) {
        setError('Failed to load project templates');
        console.error(err);
      } finally {
        setIsLoading(false);
      }
    };

    fetchTemplates();
  }, []);

  if (isLoading) {
    return (
      <div className="loading-container">
        <div className="spinner"></div>
        <p>Loading templates...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="error-container">
        <p>{error}</p>
        <button 
          className="btn btn-secondary" 
          onClick={() => window.location.reload()}
        >
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="template-selector">
      <h3>Select a Project Template</h3>
      <p className="template-help-text">
        Templates provide pre-defined structures for common project types
      </p>
      
      <div className="templates-grid">
        {templates.map((template) => (
          <div 
            key={template.id}
            className={`template-card ${selectedTemplateId === template.id ? 'selected' : ''}`}
            onClick={() => onSelect(template.id)}
          >
            <div className="template-icon">
              <img src={template.icon} alt={template.name} />
            </div>
            <div className="template-info">
              <h4>{template.name}</h4>
              <p>{template.description}</p>
              <div className="template-details">
                <div className="detail-item">
                  <span className="detail-label">Default Roles:</span>
                  <span className="detail-value">{template.default_roles.join(', ')}</span>
                </div>
                <div className="detail-item">
                  <span className="detail-label">Workflow:</span>
                  <span className="detail-value">{template.workflow}</span>
                </div>
              </div>
            </div>
            {selectedTemplateId === template.id && (
              <div className="selected-indicator">✓</div>
            )}
          </div>
        ))}
      </div>

      {templates.length === 0 && (
        <div className="empty-state">
          <p>No templates available</p>
        </div>
      )}
    </div>
  );
};

export default ProjectTemplateSelector; 