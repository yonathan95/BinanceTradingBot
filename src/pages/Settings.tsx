import React, { useState, useEffect } from 'react';
import { useAuth } from '../hooks/useAuth';
import axios from 'axios';

interface UserSettings {
  notifications_enabled: boolean;
  default_model_tier: string;
  theme: 'light' | 'dark' | 'system';
  auto_save: boolean;
  token_warning_threshold: number;
}

interface SystemInfo {
  version: string;
  api_status: 'operational' | 'degraded' | 'maintenance';
  llm_services: {
    name: string;
    status: 'operational' | 'degraded' | 'down';
  }[];
}

const Settings: React.FC = () => {
  const { user } = useAuth();
  const [settings, setSettings] = useState<UserSettings>({
    notifications_enabled: true,
    default_model_tier: 'standard',
    theme: 'system',
    auto_save: true,
    token_warning_threshold: 80
  });
  const [systemInfo, setSystemInfo] = useState<SystemInfo | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState('');
  const [saveMessage, setSaveMessage] = useState('');

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [settingsResponse, systemResponse] = await Promise.all([
          axios.get('/api/user/settings'),
          axios.get('/api/system/info')
        ]);
        
        setSettings(settingsResponse.data);
        setSystemInfo(systemResponse.data);
      } catch (err) {
        setError('Failed to load settings');
        console.error(err);
      } finally {
        setIsLoading(false);
      }
    };

    fetchData();
  }, []);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value, type } = e.target as HTMLInputElement;
    
    setSettings(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? (e.target as HTMLInputElement).checked : value
    }));
  };

  const handleSaveSettings = async () => {
    setIsSaving(true);
    setSaveMessage('');
    setError('');
    
    try {
      await axios.put('/api/user/settings', settings);
      setSaveMessage('Settings saved successfully');
      
      // Clear success message after 3 seconds
      setTimeout(() => {
        setSaveMessage('');
      }, 3000);
    } catch (err) {
      setError('Failed to save settings');
      console.error(err);
    } finally {
      setIsSaving(false);
    }
  };

  if (isLoading) {
    return (
      <div className="loading-container">
        <div className="spinner"></div>
        <p>Loading settings...</p>
      </div>
    );
  }

  return (
    <div className="settings-container">
      <div className="settings-header">
        <h1>Settings</h1>
      </div>
      
      {error && (
        <div className="error-message">{error}</div>
      )}
      
      {saveMessage && (
        <div className="success-message">{saveMessage}</div>
      )}

      <div className="settings-layout">
        <div className="settings-section">
          <h2>User Settings</h2>
          
          <div className="settings-card">
            <h3>Account Information</h3>
            <div className="form-group">
              <label>Username</label>
              <div className="static-field">{user?.username}</div>
            </div>
            <div className="form-group">
              <label>Email</label>
              <div className="static-field">{user?.email}</div>
            </div>
            <div className="form-group">
              <label>Role</label>
              <div className="static-field">{user?.role}</div>
            </div>
          </div>

          <div className="settings-card">
            <h3>Preferences</h3>
            <div className="form-group">
              <label htmlFor="theme">Theme</label>
              <select
                id="theme"
                name="theme"
                value={settings.theme}
                onChange={handleInputChange}
                className="form-control"
              >
                <option value="light">Light</option>
                <option value="dark">Dark</option>
                <option value="system">System Default</option>
              </select>
            </div>
            
            <div className="form-group">
              <label htmlFor="default_model_tier">Default Model Tier</label>
              <select
                id="default_model_tier"
                name="default_model_tier"
                value={settings.default_model_tier}
                onChange={handleInputChange}
                className="form-control"
              >
                <option value="prod_mgmt">Economy (GPT-3.5-Turbo)</option>
                <option value="standard">Standard (GPT-4o)</option>
                <option value="premium">Premium (Claude-3-Opus)</option>
              </select>
            </div>
            
            <div className="form-group checkbox-group">
              <label htmlFor="auto_save">
                <input
                  type="checkbox"
                  id="auto_save"
                  name="auto_save"
                  checked={settings.auto_save}
                  onChange={handleInputChange}
                />
                <span>Enable auto-save in workspace</span>
              </label>
            </div>
          </div>

          <div className="settings-card">
            <h3>Notifications</h3>
            <div className="form-group checkbox-group">
              <label htmlFor="notifications_enabled">
                <input
                  type="checkbox"
                  id="notifications_enabled"
                  name="notifications_enabled"
                  checked={settings.notifications_enabled}
                  onChange={handleInputChange}
                />
                <span>Enable notifications</span>
              </label>
            </div>
            
            <div className="form-group">
              <label htmlFor="token_warning_threshold">Token Warning Threshold (%)</label>
              <input
                type="number"
                id="token_warning_threshold"
                name="token_warning_threshold"
                value={settings.token_warning_threshold}
                onChange={handleInputChange}
                min="10"
                max="100"
                className="form-control"
              />
              <span className="form-hint">Show warning when token usage reaches this percentage of the budget</span>
            </div>
          </div>
          
          <div className="form-actions">
            <button
              className="btn btn-primary"
              onClick={handleSaveSettings}
              disabled={isSaving}
            >
              {isSaving ? 'Saving...' : 'Save Settings'}
            </button>
          </div>
        </div>

        <div className="settings-section">
          <h2>System Information</h2>
          
          <div className="settings-card">
            <h3>About</h3>
            <div className="info-row">
              <span className="info-label">Version</span>
              <span className="info-value">{systemInfo?.version || 'Unknown'}</span>
            </div>
            <div className="info-row">
              <span className="info-label">API Status</span>
              <span className={`status-badge ${systemInfo?.api_status || 'unknown'}`}>
                {systemInfo?.api_status || 'Unknown'}
              </span>
            </div>
          </div>
          
          <div className="settings-card">
            <h3>LLM Services</h3>
            {systemInfo?.llm_services.map((service, index) => (
              <div key={index} className="info-row">
                <span className="info-label">{service.name}</span>
                <span className={`status-badge ${service.status}`}>
                  {service.status}
                </span>
              </div>
            ))}
          </div>
          
          <div className="settings-card">
            <h3>Resources</h3>
            <ul className="resource-links">
              <li>
                <a href="/docs" target="_blank" rel="noopener noreferrer">Documentation</a>
              </li>
              <li>
                <a href="/docs/api" target="_blank" rel="noopener noreferrer">API Reference</a>
              </li>
              <li>
                <a href="https://github.com/your-org/hive-mind" target="_blank" rel="noopener noreferrer">GitHub Repository</a>
              </li>
              <li>
                <a href="/support" target="_blank" rel="noopener noreferrer">Support</a>
              </li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Settings; 