let socket: WebSocket | null = null;
let reconnectTimeout: number | null = null;

export const initializeWebSocket = (
  url: string,
  onMessage: (data: any) => void,
) => {
  // Clear any existing reconnect timeouts
  if (reconnectTimeout) {
    window.clearTimeout(reconnectTimeout);
    reconnectTimeout = null;
  }

  // Close existing socket if any
  if (socket) {
    socket.close();
  }

  socket = new WebSocket(url);

  socket.onopen = () => {
    console.log('WebSocket connection established');
  };

  socket.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      onMessage(data);
    } catch (error) {
      console.error('Error parsing WebSocket message:', error);
    }
  };

  socket.onclose = (event) => {
    console.log('WebSocket connection closed', event.code, event.reason);
    
    // Reconnect after 5 seconds
    reconnectTimeout = window.setTimeout(() => {
      console.log('Attempting to reconnect WebSocket...');
      initializeWebSocket(url, onMessage);
    }, 5000);
  };

  socket.onerror = (error) => {
    console.error('WebSocket error:', error);
  };

  return () => {
    if (socket) {
      socket.close();
    }
    
    if (reconnectTimeout) {
      window.clearTimeout(reconnectTimeout);
    }
  };
};

export const sendWebSocketMessage = (message: any) => {
  if (socket && socket.readyState === WebSocket.OPEN) {
    socket.send(JSON.stringify(message));
    return true;
  }
  return false;
}; 