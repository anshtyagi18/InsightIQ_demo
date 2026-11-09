/**
 * Enhanced WebSocket Service for Dashboard Real-time Updates
 * Provides persistent connections across navigation and robust state management
 */

// Types for WebSocket messaging
type WebSocketMessageType = 
  | 'connection_established'
  | 'subscription_confirmed'
  | 'unsubscription_confirmed'
  | 'dashboard_updates'
  | 'kpi_analysis'
  | 'alerts'
  | 'agent_health'
  | 'custom_insights'
  | 'metrics'
  | 'broadcast'
  | 'pong'
  | 'connection_stats'
  | 'error';

// Types for subscription management
type SubscriptionType = 
  | 'dashboard_updates'
  | 'kpi_analysis'
  | 'alerts'
  | 'agent_health'
  | 'custom_insights'
  | 'metrics';

interface WebSocketMessage {
  type: WebSocketMessageType;
  data: any;
  timestamp: string;
  client_id?: string;
}

interface ConnectionOptions {
  clientId?: string;
  companyName?: string;
  autoReconnect?: boolean;
  maxReconnectAttempts?: number;
  reconnectDelay?: number;
  persistConnection?: boolean; // New option for navigation persistence
}

type MessageHandler = (message: WebSocketMessage) => void;
type ConnectionHandler = (connected: boolean) => void;

class DashboardWebSocketService {
  private websocket: WebSocket | null = null;
  private clientId: string;
  private companyName?: string;
  private baseUrl: string;
  
  // Enhanced connection state management
  private connected = false;
  private connecting = false;
  private connectionAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 2000;
  private autoReconnect = true;
  private persistConnection = true; // Enable persistence by default
  private reconnectTimeout: NodeJS.Timeout | null = null;
  
  // Subscriptions and handlers with persistent storage
  private subscriptions = new Set<SubscriptionType>();
  private messageHandlers = new Map<WebSocketMessageType, Set<MessageHandler>>();
  private connectionHandlers = new Set<ConnectionHandler>();
  
  // Heartbeat with enhanced monitoring
  private heartbeatInterval: NodeJS.Timeout | null = null;
  private lastPong = Date.now();
  private connectionQuality = 'good'; // 'good', 'poor', 'critical'
  
  // Navigation persistence
  private navigationTimeout: NodeJS.Timeout | null = null;
  private isNavigating = false;
  
  // Connection state persistence keys
  private readonly STORAGE_KEYS = {
    CLIENT_ID: 'dashboard_ws_client_id',
    SUBSCRIPTIONS: 'dashboard_ws_subscriptions',
    CONNECTION_STATE: 'dashboard_ws_connection_state',
    COMPANY_NAME: 'dashboard_ws_company_name'
  };

  constructor(options: ConnectionOptions = {}) {
    this.clientId = options.clientId || this.loadOrGenerateClientId();
    this.companyName = options.companyName || this.loadCompanyName();
    this.autoReconnect = options.autoReconnect ?? true;
    this.persistConnection = options.persistConnection ?? true;
    this.maxReconnectAttempts = options.maxReconnectAttempts ?? 2;
    this.reconnectDelay = options.reconnectDelay ?? 2000;
    
    // Determine WebSocket URL - use backend URL if provided, otherwise derive from current location
    const backendUrl = import.meta.env.VITE_API_URL || import.meta.env.VITE_API_BASE_URL;
    if (backendUrl) {
      this.baseUrl = backendUrl.replace(/^https?:/, backendUrl.startsWith('https:') ? 'wss:' : 'ws:');
    } else {
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const host = window.location.host;
      this.baseUrl = `${protocol}//${host}`;
    }
    
    console.log(`🔌 WebSocket service initialized with baseUrl: ${this.baseUrl}`);
    
    // Load persisted state if persistence is enabled
    if (this.persistConnection) {
      this.loadPersistedState();
      this.setupNavigationHandlers();
    }
  }

  /**
   * Load or generate client ID with persistence
   */
  private loadOrGenerateClientId(): string {
    if (this.persistConnection) {
      const stored = localStorage.getItem(this.STORAGE_KEYS.CLIENT_ID);
      if (stored) return stored;
    }
    
    const newId = this.generateClientId();
    if (this.persistConnection) {
      localStorage.setItem(this.STORAGE_KEYS.CLIENT_ID, newId);
    }
    return newId;
  }

  /**
   * Load company name from storage
   */
  private loadCompanyName(): string | undefined {
    if (this.persistConnection) {
      const stored = localStorage.getItem(this.STORAGE_KEYS.COMPANY_NAME);
      return stored || undefined;
    }
    return undefined;
  }

  /**
   * Generate unique client ID
   */
  private generateClientId(): string {
    return `client_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  /**
   * Setup navigation event handlers for connection persistence
   */
  private setupNavigationHandlers(): void {
    // Handle browser navigation
    window.addEventListener('beforeunload', this.handleBeforeUnload.bind(this));
    window.addEventListener('visibilitychange', this.handleVisibilityChange.bind(this));
    
    // Handle programmatic navigation (React Router)
    window.addEventListener('popstate', this.handleNavigation.bind(this));
    
    // Override history methods to detect navigation
    const originalPushState = window.history.pushState;
    const originalReplaceState = window.history.replaceState;
    
    window.history.pushState = (...args) => {
      this.handleNavigation();
      return originalPushState.apply(window.history, args);
    };
    
    window.history.replaceState = (...args) => {
      this.handleNavigation();
      return originalReplaceState.apply(window.history, args);
    };
  }

  /**
   * Handle page navigation to maintain connection
   */
  private handleNavigation(): void {
    console.log('🧭 Navigation detected, preserving WebSocket connection');
    this.isNavigating = true;
    
    // Clear any existing navigation timeout
    if (this.navigationTimeout) {
      clearTimeout(this.navigationTimeout);
    }
    
    // Set a timeout to detect navigation completion
    this.navigationTimeout = setTimeout(() => {
      this.isNavigating = false;
      // Ensure connection is restored after navigation
      if (!this.connected && this.autoReconnect) {
        console.log('🔄 Restoring connection after navigation');
        this.connect();
      }
    }, 1000);
  }

  /**
   * Handle page visibility changes
   */
  private handleVisibilityChange(): void {
    if (document.hidden) {
      console.log('👁️ Page hidden, reducing connection activity');
      // Reduce heartbeat frequency when page is hidden
      this.stopHeartbeat();
    } else {
      console.log('👁️ Page visible, resuming normal connection activity');
      if (this.connected) {
        this.startHeartbeat();
      } else if (this.autoReconnect) {
        this.connect();
      }
    }
  }

  /**
   * Handle before page unload
   */
  private handleBeforeUnload(): void {
    if (this.persistConnection) {
      this.saveConnectionState();
    }
  }

  /**
   * Load persisted connection state
   */
  private loadPersistedState(): void {
    try {
      const state = localStorage.getItem(this.STORAGE_KEYS.CONNECTION_STATE);
      if (state) {
        const parsed = JSON.parse(state);
        this.connectionAttempts = parsed.connectionAttempts || 0;
        
        // Check if we had a recent connection and should auto-reconnect
        if (parsed.lastConnected) {
          const lastConnected = new Date(parsed.lastConnected);
          const now = new Date();
          const timeDiff = now.getTime() - lastConnected.getTime();
          const fiveMinutes = 5 * 60 * 1000; // 5 minutes in milliseconds
          
          if (timeDiff < fiveMinutes) {
            console.log('🔄 Found recent connection, will auto-reconnect');
            // Schedule auto-reconnect after a brief delay to allow page to initialize
            setTimeout(() => {
              if (!this.connected && !this.connecting && this.autoReconnect) {
                console.log('🚀 Auto-reconnecting from persisted state');
                this.connect();
              }
            }, 1000);
          } else {
            console.log('⏰ Last connection too old, not auto-reconnecting');
          }
        }
      }
      
      const subscriptions = localStorage.getItem(this.STORAGE_KEYS.SUBSCRIPTIONS);
      if (subscriptions) {
        const parsed = JSON.parse(subscriptions);
        this.subscriptions = new Set(parsed);
      }
    } catch (error) {
      console.warn('Failed to load persisted WebSocket state:', error);
    }
  }

  /**
   * Save connection state to localStorage
   */
  private saveConnectionState(): void {
    if (!this.persistConnection) return;
    
    try {
      localStorage.setItem(this.STORAGE_KEYS.CONNECTION_STATE, JSON.stringify({
        connectionAttempts: this.connectionAttempts,
        lastConnected: new Date().toISOString(),
        clientId: this.clientId
      }));
      
      localStorage.setItem(this.STORAGE_KEYS.SUBSCRIPTIONS, 
        JSON.stringify(Array.from(this.subscriptions)));
        
      if (this.companyName) {
        localStorage.setItem(this.STORAGE_KEYS.COMPANY_NAME, this.companyName);
      }
    } catch (error) {
      console.warn('Failed to save WebSocket state:', error);
    }
  }
  
  /**
   * Enhanced connect method with persistence support
   */
  connect(): Promise<boolean> {
    return new Promise((resolve, reject) => {
      if (this.connected) {
        console.log('✅ Already connected, returning true');
        resolve(true);
        return;
      }
      
      if (this.connecting) {
        console.log('⏳ Connection already in progress');
        resolve(false);
        return;
      }
      
      // Don't attempt connection during navigation
      if (this.isNavigating) {
        console.log('🧭 Navigation in progress, delaying connection');
        setTimeout(() => this.connect().then(resolve).catch(reject), 500);
        return;
      }
      
      console.log('🔌 Starting connection process');
      this.connecting = true;
      
      try {
        const params = new URLSearchParams({
          client_id: this.clientId,
          ...(this.companyName && { company_name: this.companyName })
        });
        
        const url = `${this.baseUrl}/api/v1/ws/connect${params.toString() ? `?${params}` : ''}`;
        console.log('🔌 Connecting to WebSocket:', url);
        
        this.websocket = new WebSocket(url);
        
        this.websocket.onopen = () => {
          console.log('✅ WebSocket connected:', this.clientId);
          
          // Force the connected state to true
          this.connected = true;
          this.connecting = false;
          this.connectionAttempts = 0;
          this.connectionQuality = 'good';
          
          // Force update all connection handlers with a small delay to ensure state propagation
          setTimeout(() => {
            console.log('🔄 Force updating all connection handlers with connected=true');
            this.notifyConnectionHandlers(true);
          }, 100);
          
          this.startHeartbeat();
          this.restoreSubscriptions();
          this.saveConnectionState();
          resolve(true);
        };
        
        this.websocket.onmessage = (event) => {
          try {
            const message: WebSocketMessage = JSON.parse(event.data);
            this.handleMessage(message);
          } catch (error) {
            console.error('Failed to parse WebSocket message:', error);
          }
        };
        
        this.websocket.onclose = (event) => {
          console.log('🔌 WebSocket closed:', event.code, event.reason);
          this.handleDisconnection();
          
          if (this.connecting) {
            reject(new Error(`Connection failed: ${event.reason}`));
          }
        };
        
        this.websocket.onerror = (error) => {
          console.debug('WebSocket connection unavailable, operating in local state mode');
          this.handleDisconnection();
          
          if (this.connecting) {
            reject(error);
          }
        };
        
      } catch (error) {
        this.connecting = false;
        reject(error);
      }
    });
  }

  /**
   * Restore subscriptions after reconnection
   */
  private restoreSubscriptions(): void {
    console.log('🔄 Restoring subscriptions:', Array.from(this.subscriptions));
    for (const subscription of this.subscriptions) {
      this.send({
        type: 'subscribe',
        data: { subscription_type: subscription }
      });
    }
  }
  
  /**
   * Enhanced disconnect method
   */
  disconnect(force: boolean = false): void {
    if (force || !this.persistConnection) {
      this.autoReconnect = false;
      this.persistConnection = false;
      this.clearPersistedState();
    }
    
    if (this.reconnectTimeout) {
      clearTimeout(this.reconnectTimeout);
      this.reconnectTimeout = null;
    }
    
    if (this.navigationTimeout) {
      clearTimeout(this.navigationTimeout);
      this.navigationTimeout = null;
    }
    
    this.stopHeartbeat();
    
    if (this.websocket) {
      this.websocket.close(1000, force ? 'Force disconnect' : 'Client disconnect');
      this.websocket = null;
    }
    
    this.handleDisconnection();
  }

  /**
   * Clear persisted state
   */
  private clearPersistedState(): void {
    Object.values(this.STORAGE_KEYS).forEach(key => {
      localStorage.removeItem(key);
    });
  }
  
  /**
   * Enhanced disconnection handling with smarter reconnection
   */
  private handleDisconnection(): void {
    this.connected = false;
    this.connecting = false;
    this.stopHeartbeat();
    this.notifyConnectionHandlers(false);
    
    // Update connection quality based on attempts
    if (this.connectionAttempts > 3) {
      this.connectionQuality = 'poor';
    }
    if (this.connectionAttempts > 7) {
      this.connectionQuality = 'critical';
    }
    
    if (this.autoReconnect && this.connectionAttempts < this.maxReconnectAttempts && !this.isNavigating) {
      this.scheduleReconnect();
    } else if (this.connectionAttempts >= this.maxReconnectAttempts) {
      console.info('WebSocket reconnect attempts finished, client operating in standalone mode.');
      this.connectionQuality = 'critical';
    }
  }
  
  /**
   * Enhanced reconnection scheduling with adaptive delays
   */
  private scheduleReconnect(): void {
    if (this.reconnectTimeout || this.isNavigating) {
      return;
    }
    
    // Adaptive delay based on connection quality and attempts
    const baseDelay = this.reconnectDelay;
    const multiplier = Math.min(Math.pow(1.5, this.connectionAttempts), 10);
    const jitter = Math.random() * 1000; // Add jitter to prevent thundering herd
    const delay = baseDelay * multiplier + jitter;
    
    console.log(`🔄 Scheduling reconnect in ${Math.round(delay)}ms (attempt ${this.connectionAttempts + 1}/${this.maxReconnectAttempts})`);
    
    this.reconnectTimeout = setTimeout(async () => {
      this.reconnectTimeout = null;
      this.connectionAttempts++;
      
      try {
        await this.connect();
      } catch (error) {
        console.error('Reconnection failed:', error);
      }
    }, delay);
  }
  
  /**
   * Enhanced heartbeat with connection quality monitoring
   */
  private startHeartbeat(): void {
    this.stopHeartbeat();
    this.lastPong = Date.now();
    
    this.heartbeatInterval = setInterval(() => {
      // Make timeout more lenient to avoid false positives on slow networks
      // Default: (2000 * 4) + 2000 = 10000ms (10 seconds)
      if (Date.now() - this.lastPong > (this.reconnectDelay * 4) + 2000) {
        console.warn('❤️‍🩹 Heartbeat: Pong not received in time, reconnecting');
        this.connectionQuality = 'poor';
        this.websocket?.close(); // This will trigger onclose and reconnection logic
        return;
      }
      
      this.send({ type: 'ping', data: { timestamp: Date.now() } });
    }, this.reconnectDelay);
  }
  
  /**
   * Stop heartbeat monitoring
   */
  private stopHeartbeat(): void {
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval);
      this.heartbeatInterval = null;
    }
  }
  
  /**
   * Enhanced message sending with retry logic
   */
  private send(message: { type: string; data: any }, retries: number = 2): boolean {
    if (!this.connected || !this.websocket) {
      if (retries > 0 && this.autoReconnect) {
        console.log('🔄 Connection lost, attempting to reconnect and resend message');
        this.connect().then(() => {
          setTimeout(() => this.send(message, retries - 1), 1000);
        }).catch(error => {
          console.error('Failed to reconnect for message sending:', error);
        });
      } else {
        console.warn('Cannot send message: WebSocket not connected');
      }
      return false;
    }
    
    try {
      this.websocket.send(JSON.stringify({
        ...message,
        client_id: this.clientId,
        timestamp: new Date().toISOString()
      }));
      return true;
    } catch (error) {
      console.error('Failed to send WebSocket message:', error);
      return false;
    }
  }
  
  /**
   * Enhanced message handling
   */
  private handleMessage(message: WebSocketMessage): void {
    // Update last pong time for heartbeat
    if (message.type === 'pong') {
      this.lastPong = Date.now();
      this.connectionQuality = 'good';
    }
    
    // Handle connection statistics
    if (message.type === 'connection_stats') {
      console.log('📊 Connection stats received:', message.data);
    }
    
    // Notify specific handlers
    const handlers = this.messageHandlers.get(message.type);
    if (handlers) {
      handlers.forEach(handler => {
        try {
          handler(message);
        } catch (error) {
          console.error('Error in message handler:', error);
        }
      });
    }
  }
  
  /**
   * Notify connection handlers
   */
  private notifyConnectionHandlers(connected: boolean): void {
    this.connectionHandlers.forEach(handler => {
      try {
        handler(connected);
      } catch (error) {
        console.error('Error in connection handler:', error);
      }
    });
  }
  
  /**
   * Enhanced subscription management
   */
  subscribe(subscriptionType: SubscriptionType): boolean {
    this.subscriptions.add(subscriptionType);
    this.saveConnectionState(); // Persist subscription
    
    return this.send({
      type: 'subscribe',
      data: { subscription_type: subscriptionType }
    });
  }
  
  /**
   * Enhanced unsubscription
   */
  unsubscribe(subscriptionType: SubscriptionType): boolean {
    this.subscriptions.delete(subscriptionType);
    this.saveConnectionState(); // Persist subscription change
    
    return this.send({
      type: 'unsubscribe',
      data: { subscription_type: subscriptionType }
    });
  }
  
  /**
   * Add message handler with cleanup
   */
  onMessage(messageType: WebSocketMessageType, handler: MessageHandler): () => void {
    if (!this.messageHandlers.has(messageType)) {
      this.messageHandlers.set(messageType, new Set());
    }
    
    this.messageHandlers.get(messageType)!.add(handler);
    
    // Return cleanup function
    return () => {
      const handlers = this.messageHandlers.get(messageType);
      if (handlers) {
        handlers.delete(handler);
        if (handlers.size === 0) {
          this.messageHandlers.delete(messageType);
        }
      }
    };
  }
  
  /**
   * Add connection handler with cleanup
   */
  onConnection(handler: ConnectionHandler): () => void {
    this.connectionHandlers.add(handler);
    
    // Immediately notify of current state
    handler(this.connected);
    
    // Return cleanup function
    return () => {
      this.connectionHandlers.delete(handler);
    };
  }
  
  /**
   * Get connection statistics
   */
  getStats(): void {
    this.send({
      type: 'get_stats',
      data: { 
        request_id: `stats_${Date.now()}`,
        connection_quality: this.connectionQuality,
        connection_attempts: this.connectionAttempts
      }
    });
  }
  
  /**
   * Check if connected - with enhanced websocket readyState check
   */
  isConnected(): boolean {
    // First check if our internal flag says we're connected
    if (this.connected) {
      // Double-check the actual WebSocket object's state
      // WebSocket.OPEN = 1
      if (this.websocket && this.websocket.readyState === 1) {
        return true;
      } else {
        // Our internal state is wrong, we're not actually connected
        // This could happen if the connection was closed without properly updating our state
        console.warn('⚠️ WebSocket connection state mismatch: internal=connected, actual=disconnected');
        // Fix our internal state
        this.connected = false;
      }
    }
    return false;
  }
  
  /**
   * Get client ID
   */
  getClientId(): string {
    return this.clientId;
  }
  
  /**
   * Get current subscriptions
   */
  getSubscriptions(): Set<SubscriptionType> {
    return new Set(this.subscriptions);
  }
  
  /**
   * Set company name with persistence
   */
  setCompanyName(companyName: string): void {
    this.companyName = companyName;
    if (this.persistConnection) {
      localStorage.setItem(this.STORAGE_KEYS.COMPANY_NAME, companyName);
    }
  }

  /**
   * Get connection quality
   */
  getConnectionQuality(): string {
    return this.connectionQuality;
  }

  /**
   * Force reconnection
   */
  forceReconnect(): Promise<boolean> {
    console.log('🔄 Force reconnecting WebSocket');
    this.disconnect(false);
    this.connectionAttempts = 0;
    return this.connect();
  }

  /**
   * Enable/disable connection persistence
   */
  setPersistence(enabled: boolean): void {
    this.persistConnection = enabled;
    if (!enabled) {
      this.clearPersistedState();
    } else {
      this.saveConnectionState();
    }
  }
}

// Create and export singleton instance
export const dashboardWebSocket = new DashboardWebSocketService({
  autoReconnect: true,
  maxReconnectAttempts: 2,
  reconnectDelay: 2000,
  persistConnection: true
});

// Export types for external use
export type {
  WebSocketMessage,
  WebSocketMessageType,
  SubscriptionType,
  MessageHandler,
  ConnectionHandler,
  ConnectionOptions
}; 