import React from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';

const Navbar: React.FC = () => {
  const { user, logout } = useAuth();

  return (
    <nav className="navbar">
      <div className="container flex justify-between items-center">
        <div className="flex items-center gap-4">
          <span className="project-title">Hive Mind</span>
          <div className="breadcrumbs">Dashboard</div>
        </div>
        <div className="flex items-center gap-3">
          <button className="notifications-btn">
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"></path>
              <path d="M13.73 21a2 2 0 0 1-3.46 0"></path>
            </svg>
          </button>
          <div className="user-menu">
            <div className="user-info">
              <span className="user-name">{user?.username}</span>
              <span className="user-role">{user?.role}</span>
            </div>
            <div className="avatar">
              {user?.username.charAt(0).toUpperCase()}
            </div>
            <div className="dropdown-menu">
              <Link to="/settings" className="dropdown-item">Settings</Link>
              <button onClick={logout} className="dropdown-item">Logout</button>
            </div>
          </div>
        </div>
      </div>
    </nav>
  );
};

export default Navbar; 