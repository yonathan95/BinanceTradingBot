import api from './api';
import AuthService from './auth';
import websocketService from './websocket';
import mockService from './mockService';
import { screenshotService } from './screenshot';

// Initialize mock service if needed
mockService();

export {
  api,
  AuthService,
  websocketService,
  screenshotService
}; 