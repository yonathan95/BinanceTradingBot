import { useState, useEffect, createContext, useContext } from 'react';
import axios from 'axios';
import { mockUser } from '../utils/mockData';
import { AUTH_ENABLED } from '../config';

interface User {
  id: string;
  username: string;
  email: string;
  role: string;
}

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<boolean>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // Check if user is already logged in
    const checkAuthStatus = async () => {
      // For demo purposes, automatically log in with mock user if auth is disabled
      if (!AUTH_ENABLED || window.localStorage.getItem('USE_MOCK_API') === 'true') {
        setUser(mockUser);
        setIsLoading(false);
        return;
      }
      
      const token = localStorage.getItem('token');
      
      if (token) {
        try {
          const response = await axios.get('/api/auth/me', {
            headers: {
              Authorization: `Bearer ${token}`
            }
          });
          
          setUser(response.data);
        } catch (error) {
          localStorage.removeItem('token');
          setUser(null);
        }
      }
      
      setIsLoading(false);
    };
    
    checkAuthStatus();
  }, []);

  const login = async (email: string, password: string): Promise<boolean> => {
    // For demo purposes, bypass real authentication if using mock data
    if (!AUTH_ENABLED || window.localStorage.getItem('USE_MOCK_API') === 'true') {
      // Simple validation for demo
      if (email && password) {
        setUser(mockUser);
        return true;
      }
      return false;
    }
    
    try {
      const response = await axios.post('/api/auth/login', { email, password });
      const { token, user } = response.data;
      
      localStorage.setItem('token', token);
      setUser(user);
      return true;
    } catch (error) {
      return false;
    }
  };

  const logout = () => {
    localStorage.removeItem('token');
    setUser(null);
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated: !!user,
        isLoading,
        login,
        logout
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  
  return context;
}; 