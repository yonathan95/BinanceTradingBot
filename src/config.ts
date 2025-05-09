// Configuration constants for the Hive Mind UI

// API Configuration
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
export const WS_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000/ws';

// Authentication
export const AUTH_ENABLED = import.meta.env.VITE_AUTH_ENABLED === 'true';
export const AUTH_TOKEN_KEY = import.meta.env.VITE_AUTH_TOKEN_KEY || 'hive_mind_auth_token';

// Feature Flags
export const ENABLE_COST_MANAGEMENT = import.meta.env.VITE_ENABLE_COST_MANAGEMENT !== 'false';
export const ENABLE_REAL_TIME_UPDATES = import.meta.env.VITE_ENABLE_REAL_TIME_UPDATES !== 'false';

// UI Configuration
export const APP_NAME = import.meta.env.VITE_APP_NAME || 'HiveMind';
export const DEFAULT_THEME = import.meta.env.VITE_DEFAULT_THEME || 'light';

// Logging
export const LOG_LEVEL = import.meta.env.VITE_LOG_LEVEL || 'info'; 