import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter as Router } from 'react-router-dom';
import App from './App';
import './styles/global.css';
import { showApiWarningIfNeeded } from './utils/apiChecker';
import { AuthProvider } from './hooks/useAuth';
import { TagAccessProvider } from './hooks/useTagAccess';

// Use the new UI by default
window.localStorage.setItem('USE_MOCK_API', 'false');
(window as any).USE_MOCK_API = false;

// Check API connectivity and show warning if needed
showApiWarningIfNeeded().catch(error => {
  console.error('Error checking API connection:', error);
});

ReactDOM.createRoot(document.getElementById('root') as HTMLElement).render(
  <React.StrictMode>
    <Router>
      <AuthProvider>
        <TagAccessProvider>
          <App />
        </TagAccessProvider>
      </AuthProvider>
    </Router>
  </React.StrictMode>,
); 