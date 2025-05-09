import api from './api';
import { AUTH_TOKEN_KEY } from '../config';
import { AxiosError } from 'axios';

interface LoginCredentials {
  username: string;
  password: string;
}

interface LoginResponse {
  token: string;
  user: {
    id: string;
    username: string;
    email: string;
    role: string;
  };
}

interface ErrorResponse {
  response?: {
    status: number;
  };
}

const AuthService = {
  /**
   * Login user with credentials
   */
  async login(credentials: LoginCredentials): Promise<LoginResponse> {
    try {
      const response = await api.post<LoginResponse>('/auth/login', credentials);
      const { token, user } = response.data;
      
      // Store token in localStorage
      localStorage.setItem(AUTH_TOKEN_KEY, token);
      
      return response.data;
    } catch (error) {
      throw error;
    }
  },
  
  /**
   * Logout current user
   */
  logout(): void {
    localStorage.removeItem(AUTH_TOKEN_KEY);
    // Optionally, notify the server about logout
    api.post('/auth/logout').catch((error: AxiosError) => {
      console.error('Logout error:', error);
    });
  },
  
  /**
   * Check if user is authenticated
   */
  isAuthenticated(): boolean {
    return !!localStorage.getItem(AUTH_TOKEN_KEY);
  },
  
  /**
   * Get current user profile
   */
  async getCurrentUser() {
    if (!this.isAuthenticated()) {
      return null;
    }
    
    try {
      const response = await api.get('/auth/me');
      return response.data;
    } catch (error: unknown) {
      // If profile fetch fails, user might not be authenticated
      const err = error as ErrorResponse;
      if (err.response && err.response.status === 401) {
        this.logout();
      }
      return null;
    }
  }
};

export default AuthService; 