import React from 'react';
import { NavLink, useNavigate } from 'react-router-dom';

const Sidebar: React.FC = () => {
  const navigate = useNavigate();

  const handleWorkModeClick = () => {
    navigate('/workspaces/ws-001/work-mode/dashboard');
  };

  return (
    <aside className="sidebar">
      <div className="sidebar-header">
        <div className="logo">
          <svg width="32" height="32" viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M16 2L29.9 26H2.1L16 2Z" fill="#FFD700"/>
            <path d="M16 6L25.9 24H6.1L16 6Z" fill="#FFA500"/>
            <path d="M16 10L21.9 22H10.1L16 10Z" fill="#FF8C00"/>
            <circle cx="16" cy="18" r="3" fill="#000"/>
          </svg>
          <span className="logo-text">Hive Mind</span>
        </div>
      </div>
      
      {/* Work Mode Button */}
      <div className="work-mode-button-container" style={{ padding: '12px', textAlign: 'center' }}>
        <button 
          onClick={handleWorkModeClick}
          className="work-mode-button"
          style={{
            backgroundColor: '#1A3FE4',
            color: 'white',
            border: 'none',
            borderRadius: '8px',
            padding: '10px 16px',
            fontSize: '14px',
            fontWeight: 'bold',
            cursor: 'pointer',
            width: '100%',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            boxShadow: '0 2px 4px rgba(0,0,0,0.2)'
          }}
        >
          <span style={{ marginRight: '8px' }}>💼</span>
          Work Mode
        </button>
      </div>
      
      <nav className="sidebar-nav">
        <ul className="nav-list">
          <li className="nav-item">
            <NavLink to="/" className={({isActive}) => isActive ? 'nav-link active' : 'nav-link'}>
              <span className="nav-icon">📊</span>
              <span className="nav-text">Dashboard</span>
            </NavLink>
          </li>
          
          {/* Projects Section */}
          <li className="nav-section">
            <div className="section-header">
              <span className="section-icon">📁</span>
              <span className="section-title">Projects</span>
            </div>
            <ul className="section-items">
              <li className="nav-item">
                <NavLink to="/workspaces" className={({isActive}) => isActive ? 'nav-link active' : 'nav-link'}>
                  <span className="nav-icon">🏢</span>
                  <span className="nav-text">Workspaces</span>
                </NavLink>
              </li>
            </ul>
          </li>
          
          <li className="nav-item">
            <NavLink to="/teams/create" className={({isActive}) => isActive ? 'nav-link active' : 'nav-link'}>
              <span className="nav-icon">👥</span>
              <span className="nav-text">Create Team</span>
            </NavLink>
          </li>
          <li className="nav-item">
            <NavLink to="/cost-management" className={({isActive}) => isActive ? 'nav-link active' : 'nav-link'}>
              <span className="nav-icon">💰</span>
              <span className="nav-text">Cost Management</span>
            </NavLink>
          </li>
          <li className="nav-item">
            <NavLink to="/settings" className={({isActive}) => isActive ? 'nav-link active' : 'nav-link'}>
              <span className="nav-icon">⚙️</span>
              <span className="nav-text">Settings</span>
            </NavLink>
          </li>
        </ul>
      </nav>
      
      <div className="sidebar-footer">
        <div className="version">v0.1.0</div>
      </div>
    </aside>
  );
};

export default Sidebar; 