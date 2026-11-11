/**
 * WebSocket Service for InsightIQ
 * Handles real-time connections for dashboard updates, agent status, and live data
 * Connects to /api/v1/ws/* endpoints
 */

export interface WebSocketMessage {
  type: string;
  data: any;
  timestamp: string;
  sender?: string;
}

export interface WebSocketConfig {
  url: string;
  reconnectInterval?: number;
  maxReconnectAttempts?: number;
  protocols?: string[];
}

export interface ConnectionStatus {
  connected: boolean;
  connecting: boolean;
  lastConnected?: Date;
  reconnectAttempts: number;
  error?: string;
}

class WebSocketService {
  private connections: Map<string, WebSocket> = new Map();
  private connectionStatus: Map<string, ConnectionStatus> = new Map();
  private messageHandlers: Map<string, Set<(message: WebSocketMessage) => void>> = new Map();
  private statusHandlers: Map<string, Set<(status: ConnectionStatus) => void>> = new Map();
  private reconnectTimers: Map<string, NodeJS.Timeout> = new Map();
  
  private readonly baseUrl = import.meta.env.VITE_WS_BASE_URL || (
    typeof window !== 'undefined'
      ? `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}`
      : 'ws://localhost:8000'
  );

  /**
   * Connect to a dashboard WebSocket for real-time updates
   */
  connectToDashboard(dashboardId: string): string {
    const connectionId = `dashboard_${dashboardId}`;
    const url = `${this.baseUrl}/api/v1/ws/dashboard/${dashboardId}`;
    
    return this.connect(connectionId, { url });
  }

  /**
   * Connect to an agent WebSocket for status updates
   */
  connectToAgent(agentId: string): string {
    const connectionId = `agent_${agentId}`;
    const url = `${this.baseUrl}/api/v1/ws/agent/${agentId}`;
    
    return this.connect(connectionId, { url });
  }

  /**
   * Connect to the direct test WebSocket
   */
  connectToDirectTest(): string {
    const connectionId = 'direct_test';
    const url = `${this.baseUrl}/api/v1/ws/direct-test`;
    
    return this.connect(connectionId, { url });
  }

  /**
   * Generic WebSocket connection method
   */
  connect(connectionId: string, config: WebSocketConfig): string {
    // Close existing connection if any
    this.disconnect(connectionId);

    const { url, protocols, reconnectInterval = 5000, maxReconnectAttempts = 5 } = config;
    
    // Initialize connection status
    const status: ConnectionStatus = {
      connected: false,
      connecting: true,
      reconnectAttempts: 0
    };
    this.connectionStatus.set(connectionId, status);
    this.notifyStatusHandlers(connectionId, status);

    try {
      const ws = new WebSocket(url, protocols);
      this.connections.set(connectionId, ws);

      ws.onopen = () => {
        console.log(`WebSocket connected: ${connectionId}`);
        const newStatus: ConnectionStatus = {
          connected: true,
          connecting: false,
          lastConnected: new Date(),
          reconnectAttempts: 0
        };
        this.connectionStatus.set(connectionId, newStatus);
        this.notifyStatusHandlers(connectionId, newStatus);
      };

      ws.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data);
          this.notifyMessageHandlers(connectionId, message);
        } catch (error) {
          console.error(`Failed to parse WebSocket message for ${connectionId}:`, error);
        }
      };

      ws.onclose = (event) => {
        console.log(`WebSocket closed: ${connectionId}`, event.code, event.reason);
        const currentStatus = this.connectionStatus.get(connectionId);
        
        if (currentStatus && currentStatus.reconnectAttempts < maxReconnectAttempts) {
          // Attempt reconnection
          const newStatus: ConnectionStatus = {
            connected: false,
            connecting: true,
            lastConnected: currentStatus.lastConnected,
            reconnectAttempts: currentStatus.reconnectAttempts + 1
          };
          this.connectionStatus.set(connectionId, newStatus);
          this.notifyStatusHandlers(connectionId, newStatus);

          const timer = setTimeout(() => {
            console.log(`Attempting to reconnect ${connectionId} (attempt ${newStatus.reconnectAttempts})`);
            this.connect(connectionId, config);
          }, reconnectInterval);
          
          this.reconnectTimers.set(connectionId, timer);
        } else {
          // Max reconnect attempts reached
          const finalStatus: ConnectionStatus = {
            connected: false,
            connecting: false,
            lastConnected: currentStatus?.lastConnected,
            reconnectAttempts: currentStatus?.reconnectAttempts || 0,
            error: 'Max reconnection attempts reached'
          };
          this.connectionStatus.set(connectionId, finalStatus);
          this.notifyStatusHandlers(connectionId, finalStatus);
        }
      };

      ws.onerror = (error) => {
        console.error(`WebSocket error for ${connectionId}:`, error);
        const currentStatus = this.connectionStatus.get(connectionId);
        const errorStatus: ConnectionStatus = {
          connected: false,
          connecting: false,
          lastConnected: currentStatus?.lastConnected,
          reconnectAttempts: currentStatus?.reconnectAttempts || 0,
          error: 'Connection error'
        };
        this.connectionStatus.set(connectionId, errorStatus);
        this.notifyStatusHandlers(connectionId, errorStatus);
      };

    } catch (error) {
      console.error(`Failed to create WebSocket connection for ${connectionId}:`, error);
      const errorStatus: ConnectionStatus = {
        connected: false,
        connecting: false,
        reconnectAttempts: 0,
        error: error instanceof Error ? error.message : 'Unknown error'
      };
      this.connectionStatus.set(connectionId, errorStatus);
      this.notifyStatusHandlers(connectionId, errorStatus);
    }

    return connectionId;
  }

  /**
   * Disconnect from a WebSocket
   */
  disconnect(connectionId: string): void {
    const ws = this.connections.get(connectionId);
    if (ws) {
      ws.close();
      this.connections.delete(connectionId);
    }

    const timer = this.reconnectTimers.get(connectionId);
    if (timer) {
      clearTimeout(timer);
      this.reconnectTimers.delete(connectionId);
    }

    const status: ConnectionStatus = {
      connected: false,
      connecting: false,
      reconnectAttempts: 0
    };
    this.connectionStatus.set(connectionId, status);
    this.notifyStatusHandlers(connectionId, status);
  }

  /**
   * Send a message through a WebSocket connection
   */
  send(connectionId: string, message: any): boolean {
    const ws = this.connections.get(connectionId);
    if (ws && ws.readyState === WebSocket.OPEN) {
      try {
        const wsMessage: WebSocketMessage = {
          type: message.type || 'message',
          data: message.data || message,
          timestamp: new Date().toISOString(),
          sender: 'client'
        };
        ws.send(JSON.stringify(wsMessage));
        return true;
      } catch (error) {
        console.error(`Failed to send message to ${connectionId}:`, error);
        return false;
      }
    }
    return false;
  }

  /**
   * Subscribe to messages from a specific connection
   */
  onMessage(connectionId: string, handler: (message: WebSocketMessage) => void): () => void {
    if (!this.messageHandlers.has(connectionId)) {
      this.messageHandlers.set(connectionId, new Set());
    }
    
    const handlers = this.messageHandlers.get(connectionId)!;
    handlers.add(handler);
    
    // Return unsubscribe function
    return () => {
      handlers.delete(handler);
    };
  }

  /**
   * Subscribe to connection status changes
   */
  onStatusChange(connectionId: string, handler: (status: ConnectionStatus) => void): () => void {
    if (!this.statusHandlers.has(connectionId)) {
      this.statusHandlers.set(connectionId, new Set());
    }
    
    const handlers = this.statusHandlers.get(connectionId)!;
    handlers.add(handler);
    
    // Return unsubscribe function
    return () => {
      handlers.delete(handler);
    };
  }

  /**
   * Get connection status
   */
  getStatus(connectionId: string): ConnectionStatus {
    return this.connectionStatus.get(connectionId) || {
      connected: false,
      connecting: false,
      reconnectAttempts: 0
    };
  }

  /**
   * Get all active connections
   */
  getActiveConnections(): string[] {
    return Array.from(this.connections.keys()).filter(
      connectionId => this.getStatus(connectionId).connected
    );
  }

  /**
   * Disconnect all connections
   */
  disconnectAll(): void {
    const connectionIds = Array.from(this.connections.keys());
    connectionIds.forEach(connectionId => this.disconnect(connectionId));
  }

  private notifyMessageHandlers(connectionId: string, message: WebSocketMessage): void {
    const handlers = this.messageHandlers.get(connectionId);
    if (handlers) {
      handlers.forEach(handler => {
        try {
          handler(message);
        } catch (error) {
          console.error(`Error in message handler for ${connectionId}:`, error);
        }
      });
    }
  }

  private notifyStatusHandlers(connectionId: string, status: ConnectionStatus): void {
    const handlers = this.statusHandlers.get(connectionId);
    if (handlers) {
      handlers.forEach(handler => {
        try {
          handler(status);
        } catch (error) {
          console.error(`Error in status handler for ${connectionId}:`, error);
        }
      });
    }
  }
}

// Export singleton instance
export const webSocketService = new WebSocketService();
export default webSocketService; 