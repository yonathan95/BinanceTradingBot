// This file simulates WebSocket behavior for local development
class MockWebSocket {
  private listeners: Record<string, ((data: any) => void)[]> = {};
  private teamId: string | null = null;
  private connected: boolean = false;
  private mockMessages = [
    {
      id: "auto-msg-1",
      agent: "Manager",
      content: "I'm analyzing the current task...",
      timestamp: "",
      type: "text"
    },
    {
      id: "auto-msg-2",
      agent: "Planner",
      content: "Based on our current progress, I recommend we focus on implementing the shopping cart functionality next.",
      timestamp: "",
      type: "text"
    },
    {
      id: "auto-msg-3",
      agent: "Coder",
      content: "I'll start working on the ShoppingCart component. It will need to handle adding/removing items and updating quantities.",
      timestamp: "",
      type: "text"
    },
    {
      id: "auto-msg-4",
      agent: "Tester",
      content: "I'll prepare test cases for the shopping cart, focusing on edge cases like empty cart, item quantity limits, and price calculations.",
      timestamp: "",
      type: "text"
    }
  ];
  private messageInterval: NodeJS.Timeout | null = null;
  
  constructor() {
    console.log("Mock WebSocket initialized");
  }
  
  public connect(url: string): void {
    setTimeout(() => {
      this.connected = true;
      this.emit('connect', {});
      console.log("Mock WebSocket connected");
    }, 500);
  }
  
  public on(event: string, callback: (data: any) => void): void {
    if (!this.listeners[event]) {
      this.listeners[event] = [];
    }
    this.listeners[event].push(callback);
  }
  
  public emit(event: string, data: any): void {
    if (this.listeners[event]) {
      this.listeners[event].forEach(callback => callback(data));
    }
  }
  
  public joinTeam(teamId: string): void {
    this.teamId = teamId;
    console.log(`Joined team: ${teamId}`);
    this.startMockMessageStream();
  }
  
  private startMockMessageStream(): void {
    if (this.messageInterval) {
      clearInterval(this.messageInterval);
    }
    
    let messageIndex = 0;
    
    // Send a message every 10-20 seconds
    this.messageInterval = setInterval(() => {
      if (!this.connected || !this.teamId) return;
      
      const message = {...this.mockMessages[messageIndex]};
      message.timestamp = new Date().toISOString();
      message.id = `auto-msg-${Date.now()}`;
      
      this.emit('message', message);
      
      messageIndex = (messageIndex + 1) % this.mockMessages.length;
    }, Math.random() * 10000 + 10000); // Between 10 and 20 seconds
  }
  
  public disconnect(): void {
    this.connected = false;
    if (this.messageInterval) {
      clearInterval(this.messageInterval);
      this.messageInterval = null;
    }
    console.log("Mock WebSocket disconnected");
  }
  
  public isConnected(): boolean {
    return this.connected;
  }
}

export default MockWebSocket; 