import { WS_URL, AUTH_TOKEN_KEY } from '../config';
import MockWebSocket from './mockWebSocket';

type MessageHandler = (data: any) => void;
type ConnectionHandler = () => void;

class WebSocketService {
  private socket: WebSocket | null = null;
  private mockSocket: MockWebSocket | null = null;
  private messageHandlers: Map<string, MessageHandler[]> = new Map();
  private onConnectHandlers: ConnectionHandler[] = [];
  private onDisconnectHandlers: ConnectionHandler[] = [];
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  private isConnecting = false;
  private useMockSocket = process.env.NODE_ENV === 'development' || window.location.search.includes('mock=true');

  constructor() {
    this.connect = this.connect.bind(this);
    this.disconnect = this.disconnect.bind(this);
    this.send = this.send.bind(this);
    this.onMessage = this.onMessage.bind(this);
    this.onConnect = this.onConnect.bind(this);
    this.onDisconnect = this.onDisconnect.bind(this);
    this.handleMessage = this.handleMessage.bind(this);
    this.joinTeam = this.joinTeam.bind(this);
  }

  connect(): void {
    if (this.useMockSocket) {
      console.log('Using mock WebSocket');
      this.connectMock();
      return;
    }

    if (this.socket && (this.socket.readyState === WebSocket.OPEN || this.socket.readyState === WebSocket.CONNECTING)) {
      return;
    }

    if (this.isConnecting) {
      return;
    }

    this.isConnecting = true;

    const token = localStorage.getItem(AUTH_TOKEN_KEY);
    const url = token ? `${WS_URL}?token=${token}` : WS_URL;
    
    this.socket = new WebSocket(url);
    
    this.socket.onopen = () => {
      this.isConnecting = false;
      this.onConnectHandlers.forEach(handler => handler());
      
      if (this.reconnectTimer) {
        clearTimeout(this.reconnectTimer);
        this.reconnectTimer = null;
      }
    };
    
    this.socket.onclose = () => {
      this.isConnecting = false;
      this.onDisconnectHandlers.forEach(handler => handler());
      
      if (!this.reconnectTimer) {
        this.reconnectTimer = setTimeout(() => {
          this.connect();
        }, 3000);
      }
    };
    
    this.socket.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        this.handleMessage(data);
      } catch (error) {
        console.error('Error parsing WebSocket message:', error);
      }
    };
    
    this.socket.onerror = (error) => {
      console.error('WebSocket error:', error);
      this.isConnecting = false;
    };
  }
  
  private connectMock(): void {
    if (this.mockSocket) {
      return;
    }
    
    this.mockSocket = new MockWebSocket();
    
    this.mockSocket.on('connect', () => {
      this.onConnectHandlers.forEach(handler => handler());
    });
    
    this.mockSocket.on('message', (message) => {
      this.handleMessage({ type: 'message', payload: message });
    });
    
    this.mockSocket.connect(WS_URL);
  }
  
  joinTeam(teamId: string): void {
    if (this.useMockSocket && this.mockSocket) {
      this.mockSocket.joinTeam(teamId);
      return;
    }
    
    this.send('join_team', { team_id: teamId });
  }
  
  disconnect(): void {
    if (this.useMockSocket && this.mockSocket) {
      this.mockSocket.disconnect();
      this.mockSocket = null;
      return;
    }
    
    if (this.socket) {
      this.socket.close();
      this.socket = null;
    }
    
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
  }
  
  send(type: string, payload: any): boolean {
    if (this.useMockSocket && this.mockSocket) {
      this.mockSocket.emit(type, payload);
      return true;
    }
    
    if (!this.socket || this.socket.readyState !== WebSocket.OPEN) {
      return false;
    }
    
    this.socket.send(JSON.stringify({ type, payload }));
    return true;
  }
  
  onMessage(type: string, handler: MessageHandler): () => void {
    if (!this.messageHandlers.has(type)) {
      this.messageHandlers.set(type, []);
    }
    
    const handlers = this.messageHandlers.get(type)!;
    handlers.push(handler);
    
    return () => {
      const index = handlers.indexOf(handler);
      if (index !== -1) {
        handlers.splice(index, 1);
      }
    };
  }
  
  onConnect(handler: ConnectionHandler): () => void {
    this.onConnectHandlers.push(handler);
    
    return () => {
      const index = this.onConnectHandlers.indexOf(handler);
      if (index !== -1) {
        this.onConnectHandlers.splice(index, 1);
      }
    };
  }
  
  onDisconnect(handler: ConnectionHandler): () => void {
    this.onDisconnectHandlers.push(handler);
    
    return () => {
      const index = this.onDisconnectHandlers.indexOf(handler);
      if (index !== -1) {
        this.onDisconnectHandlers.splice(index, 1);
      }
    };
  }
  
  private handleMessage(data: { type: string; payload: any }): void {
    if (!data || !data.type) {
      return;
    }
    
    const handlers = this.messageHandlers.get(data.type);
    if (handlers) {
      handlers.forEach(handler => handler(data.payload));
    }
  }
}

// Create singleton instance
const websocketService = new WebSocketService();

export default websocketService; 