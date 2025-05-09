import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import { MantineProvider, createTheme } from '@mantine/core';
import '@mantine/core/styles.css';
import App from './App';
import './styles/global.css';

// Error boundary component to catch rendering errors
class ErrorBoundary extends React.Component<{ children: React.ReactNode }, { hasError: boolean, error: Error | null }> {
  constructor(props: { children: React.ReactNode }) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error) {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('React error boundary caught an error:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div style={{ 
          padding: '20px', 
          backgroundColor: '#202939', 
          color: 'white',
          borderRadius: '8px',
          margin: '20px',
          fontFamily: 'Inter, sans-serif'
        }}>
          <h1 style={{ color: '#EF4444' }}>Something went wrong</h1>
          <p>The application encountered an error:</p>
          <pre style={{ 
            backgroundColor: '#121926', 
            padding: '10px', 
            borderRadius: '4px',
            overflowX: 'auto'
          }}>
            {this.state.error?.message || 'Unknown error'}
          </pre>
          <p>Please check the console for more details.</p>
          <button 
            style={{
              backgroundColor: '#3C5CFE',
              color: 'white',
              border: 'none',
              padding: '10px 20px',
              borderRadius: '4px',
              cursor: 'pointer',
              marginTop: '10px'
            }}
            onClick={() => window.location.reload()}
          >
            Reload Application
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}

const theme = createTheme({
  primaryColor: 'indigo',
  primaryShade: 6,
  colors: {
    indigo: [
      '#E0E8FF',
      '#C0D0FF',
      '#9FB3FF',
      '#7E96FF',
      '#5D79FF',
      '#3C5CFE',
      '#1A3FE4',
      '#0029C7',
      '#0020A0',
      '#001779',
    ],
    gray: [
      '#F8FAFC',
      '#EEF2F6',
      '#E3E8EF',
      '#CDD5DF',
      '#9AA5B4',
      '#697586',
      '#4B5565',
      '#364152',
      '#202939',
      '#121926',
    ],
  },
  components: {
    Button: {
      defaultProps: {
        radius: 'md',
      },
    },
    Card: {
      defaultProps: {
        radius: 'md',
        shadow: 'sm',
      },
    },
  },
  fontFamily: 'Inter, system-ui, -apple-system, sans-serif',
  fontSizes: {
    xs: '0.75rem',
    sm: '0.875rem',
    md: '1rem',
    lg: '1.125rem',
    xl: '1.25rem',
  },
  radius: {
    xs: '0.125rem',
    sm: '0.25rem',
    md: '0.5rem',
    lg: '1rem',
    xl: '2rem',
  },
});

try {
  ReactDOM.createRoot(document.getElementById('root')!).render(
    <React.StrictMode>
      <ErrorBoundary>
        <MantineProvider theme={theme} defaultColorScheme="dark">
          <BrowserRouter>
            <App />
          </BrowserRouter>
        </MantineProvider>
      </ErrorBoundary>
    </React.StrictMode>
  );
} catch (error) {
  console.error('Failed to render the application:', error);
  document.body.innerHTML = `
    <div style="padding: 20px; background-color: #202939; color: white; border-radius: 8px; margin: 20px; font-family: sans-serif;">
      <h1 style="color: #EF4444;">Fatal Error</h1>
      <p>The application failed to start:</p>
      <pre style="background-color: #121926; padding: 10px; border-radius: 4px; overflow-x: auto;">
        ${error instanceof Error ? error.message : String(error)}
      </pre>
      <p>Please check the console for more details.</p>
      <button 
        style="background-color: #3C5CFE; color: white; border: none; padding: 10px 20px; border-radius: 4px; cursor: pointer; margin-top: 10px;"
        onclick="window.location.reload()"
      >
        Reload Application
      </button>
      <a 
        href="/debug.html" 
        style="display: inline-block; margin-left: 10px; background-color: #364152; color: white; text-decoration: none; padding: 10px 20px; border-radius: 4px;"
      >
        Go to Debug Page
      </a>
    </div>
  `;
} 