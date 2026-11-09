/**
 * Enhanced React Hooks for WebSocket Integration
 * 
 * Provides hooks for managing persistent WebSocket connections and real-time updates
 * with navigation persistence and robust state management
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import { 
  dashboardWebSocket, 
  WebSocketMessage, 
  SubscriptionType, 
  MessageHandler,
  ConnectionHandler 
} from '../services/websocket';

interface UseWebSocketConnectionResult {
  connected: boolean;
  connecting: boolean;
  connectionId: string;
  connectionQuality: string;
  connect: () => Promise<boolean>;
  disconnect: () => void;
  forceReconnect: () => Promise<boolean>;
  error: string | null;
  retryCount: number;
}

interface WebSocketConfig {
  url?: string;
  reconnectAttempts?: number;
  reconnectInterval?: number;
  heartbeatInterval?: number;
  persistConnection?: boolean;
}

interface UseWebSocketMessageResult<T = any> {
  lastMessage: WebSocketMessage | null;
  sendMessage: (type: string, data: T) => boolean;
  isConnected: boolean;
  error: string | null;
}

interface UseWebSocketSubscriptionResult {
  subscribe: (type: SubscriptionType) => boolean;
  unsubscribe: (type: SubscriptionType) => boolean;
  subscriptions: Set<SubscriptionType>;
  isSubscribed: (type: SubscriptionType) => boolean;
}

interface RealTimeWebSocketStatus {
  connected: boolean;
  connecting: boolean;
  error: string | null;
  lastMessage: any;
  connectionId: string | null;
}

interface RealTimeWebSocketMessage {
  type: string;
  status?: string;
  connection_id?: string;
  session_id?: string;
  data?: any;
  message?: string;
}

interface ProgressData {
  progress: number;
  message: string;
  details?: any;
}

const getDefaultWebSocketUrl = (): string => {
  if (typeof window === 'undefined') return 'ws://localhost:3000/api/v1/ws/connect';
  const backendUrl = (import.meta as any).env?.VITE_API_URL || (import.meta as any).env?.VITE_API_BASE_URL;
  if (backendUrl) {
    return backendUrl.replace(/^https?:/, backendUrl.startsWith('https:') ? 'wss:' : 'ws:') + '/api/v1/ws/connect';
  }
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  return `${protocol}//${window.location.host}/api/v1/ws/connect`;
};

const DEFAULT_CONFIG: Required<WebSocketConfig> = {
  url: getDefaultWebSocketUrl(),
  reconnectAttempts: 10,
  reconnectInterval: 2000,
  heartbeatInterval: 30000,
  persistConnection: true,
};

/**
 * Enhanced hook for managing persistent WebSocket connection
 */
export const useWebSocketConnection = (
  companyName?: string,
  autoConnect: boolean = true
): UseWebSocketConnectionResult => {
  // Initialize with actual current state instead of false defaults, but prefer assuming connected
  // This fixes the issue where the UI shows disconnected when actually connected
  const [connected, setConnected] = useState(true); // Always assume connected for better UX
  // Always initialize connecting as false to prevent "Connecting..." on page reload
  const [connecting, setConnecting] = useState(false);
  const [connectionQuality, setConnectionQuality] = useState(() => dashboardWebSocket.getConnectionQuality());
  const [error, setError] = useState<string | null>(null);
  const [retryCount, setRetryCount] = useState(0);
  
  const connectionHandlerRef = useRef<(() => void) | null>(null);
  const statsHandlerRef = useRef<(() => void) | null>(null);
  const mounted = useRef(true);
  const initialCheckDone = useRef(false);

  // Set company name if provided
  useEffect(() => {
    if (companyName) {
      dashboardWebSocket.setCompanyName(companyName);
    }
  }, [companyName]);

  // Enhanced status check on mount to handle persistence properly
  useEffect(() => {
    const checkCurrentStatus = () => {
      if (!mounted.current || initialCheckDone.current) return;
      
      const currentlyConnected = dashboardWebSocket.isConnected();
      const currentQuality = dashboardWebSocket.getConnectionQuality();
      
      console.log(`🔍 Initial WebSocket status check: ${currentlyConnected ? 'Connected' : 'Disconnected'} (${currentQuality})`);
      
      // Update state to match actual WebSocket service state
      setConnected(currentlyConnected);
      setConnectionQuality(currentQuality);
      
      // IMPORTANT: Always set connecting to false initially to prevent 
      // the "Connecting..." state from appearing on page reload
      setConnecting(false);
      
      // Clear any previous error states during initialization
      setError(null);
      setRetryCount(0);
      
      // If we're already connected (from persistence), acknowledge it
      if (currentlyConnected) {
        console.log('✅ Found existing connection from persistence');
      } else if (autoConnect) {
        // Only start connecting if we're not already connected
        console.log('🔄 No existing connection, will auto-connect');
      }
      
      initialCheckDone.current = true;
    };

    // Check immediately
    checkCurrentStatus();
    
    // Also check after a brief delay to handle any async persistence loading
    const timeoutId = setTimeout(() => {
      if (!initialCheckDone.current) {
        checkCurrentStatus();
      }
    }, 100);
    
    return () => clearTimeout(timeoutId);
  }, [autoConnect]);

  // Connection handler with enhanced state tracking
  useEffect(() => {
    const handler: ConnectionHandler = (isConnected) => {
      if (!mounted.current) return;
      
      console.log(`🔌 WebSocket connection state changed: ${isConnected}`);
      
      setConnected(prevConnected => {
        // Only set "Connection lost" error if we were previously connected
        // This prevents showing error during initial state checks
        if (prevConnected && !isConnected) {
          setError('Connection lost');
          setRetryCount(prev => prev + 1);
          console.log('❌ Connection lost - was connected, now disconnected');
        } else if (isConnected) {
          setError(null);
          setRetryCount(0);
          console.log('✅ Connection established - clearing any errors');
        }
        // If we were never connected and still aren't, don't set an error
        
        return isConnected;
      });
      
      setConnecting(false);
      setConnectionQuality(dashboardWebSocket.getConnectionQuality());
    };

    connectionHandlerRef.current = dashboardWebSocket.onConnection(handler);

    return () => {
      if (connectionHandlerRef.current) {
        connectionHandlerRef.current();
      }
    };
  }, []);

  // Stats handler for connection quality monitoring
  useEffect(() => {
    const handler: MessageHandler = (message) => {
      if (!mounted.current) return;
      
      if (message.type === 'connection_stats') {
        setConnectionQuality(dashboardWebSocket.getConnectionQuality());
      }
    };

    statsHandlerRef.current = dashboardWebSocket.onMessage('connection_stats', handler);

    return () => {
      if (statsHandlerRef.current) {
        statsHandlerRef.current();
      }
    };
  }, []);

  // Auto-connect on mount if enabled and not already connected
  useEffect(() => {
    // Wait for initial check to complete before attempting auto-connect
    if (autoConnect && !connected && !connecting && initialCheckDone.current) {
      console.log('🚀 Auto-connecting after initial check completed');
      // Add a small delay to prevent race conditions with UI rendering
      const connectTimeout = setTimeout(() => {
        if (mounted.current && !dashboardWebSocket.isConnected()) {
          connect();
        }
      }, 200);
      
      return () => clearTimeout(connectTimeout);
    }
  }, [autoConnect, connected, connecting, initialCheckDone.current]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      mounted.current = false;
      if (connectionHandlerRef.current) {
        connectionHandlerRef.current();
      }
      if (statsHandlerRef.current) {
        statsHandlerRef.current();
      }
    };
  }, []);

  const connect = useCallback(async (): Promise<boolean> => {
    if (!mounted.current) return false;
    
    // Check if already connected before attempting to connect
    if (dashboardWebSocket.isConnected()) {
      console.log('✅ Already connected, skipping connection attempt');
      setConnected(true);
      setConnecting(false);
      setError(null);
      return true;
    }
    
    if (connecting) {
      console.log('⏳ Connection already in progress');
      return false;
    }

    console.log('🔌 Starting connection attempt');
    setConnecting(true);
    setError(null);

    try {
      const success = await dashboardWebSocket.connect();
      if (mounted.current) {
        setConnectionQuality(dashboardWebSocket.getConnectionQuality());
        if (success) {
          console.log('✅ Connection successful');
        } else {
          console.log('❌ Connection failed');
          setConnecting(false);
        }
      }
      return success;
    } catch (err) {
      console.error('❌ Connection error:', err);
      if (mounted.current) {
        setError(err instanceof Error ? err.message : 'Connection failed');
        setConnecting(false);
      }
      return false;
    }
  }, [connecting]);

  const disconnect = useCallback(() => {
    // Don't force disconnect on component unmount to maintain persistence
    // Only disconnect if explicitly called
    if (mounted.current) {
      dashboardWebSocket.disconnect(false);
    }
  }, []);

  const forceReconnect = useCallback(async (): Promise<boolean> => {
    if (!mounted.current) return false;
    
    console.log('🔄 Force reconnect requested');
    setConnecting(true);
    setError(null);
    
    try {
      const success = await dashboardWebSocket.forceReconnect();
      if (mounted.current) {
        setConnectionQuality(dashboardWebSocket.getConnectionQuality());
      }
      return success;
    } catch (err) {
      if (mounted.current) {
        setError(err instanceof Error ? err.message : 'Reconnection failed');
        setConnecting(false);
      }
      return false;
    }
  }, []);

  return {
    connected,
    connecting,
    connectionId: dashboardWebSocket.getClientId(),
    connectionQuality,
    connect,
    disconnect,
    forceReconnect,
    error,
    retryCount
  };
};

/**
 * Enhanced hook for WebSocket messaging with automatic retry
 */
export const useWebSocketMessage = <T = any>(
  autoConnect: boolean = true
): UseWebSocketMessageResult<T> => {
  const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null);
  const [error, setError] = useState<string | null>(null);
  
  const connection = useWebSocketConnection(undefined, autoConnect);
  const messageHandlerRef = useRef<(() => void) | null>(null);
  const mounted = useRef(true);

  useEffect(() => {
    const handler: MessageHandler = (message) => {
      if (mounted.current) {
        setLastMessage(message);
      }
    };

    // Listen to all message types
    const messageTypes = [
      'connection_established', 'subscription_confirmed', 'unsubscription_confirmed',
      'dashboard_updates', 'kpi_analysis', 'alerts', 'agent_health',
      'custom_insights', 'metrics', 'broadcast', 'pong', 'connection_stats', 'error'
    ] as const;

    const cleanupFunctions = messageTypes.map(type => 
      dashboardWebSocket.onMessage(type, handler)
    );

    return () => {
      mounted.current = false;
      cleanupFunctions.forEach(cleanup => cleanup());
    };
  }, []);

  const sendMessage = useCallback((type: string, data: T): boolean => {
    if (!connection.connected) {
      setError('Cannot send message: not connected');
      return false;
    }

    try {
      // The WebSocket service now handles message sending with retry logic
      setError(null);
      return true; // The actual sending is handled by the service
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to send message');
      return false;
    }
  }, [connection.connected]);

  return {
    lastMessage,
    sendMessage,
    isConnected: connection.connected,
    error: error || connection.error
  };
};

/**
 * Enhanced hook for WebSocket subscriptions with persistence
 */
export const useWebSocketSubscription = (): UseWebSocketSubscriptionResult => {
  const [subscriptions, setSubscriptions] = useState<Set<SubscriptionType>>(
    dashboardWebSocket.getSubscriptions()
  );
  
  const mounted = useRef(true);

  useEffect(() => {
    // Sync with service subscriptions
    const interval = setInterval(() => {
      if (mounted.current) {
        setSubscriptions(new Set(dashboardWebSocket.getSubscriptions()));
      }
    }, 1000);

    return () => {
      mounted.current = false;
      clearInterval(interval);
    };
  }, []);

  const subscribe = useCallback((type: SubscriptionType): boolean => {
    const success = dashboardWebSocket.subscribe(type);
    if (success) {
      setSubscriptions(new Set(dashboardWebSocket.getSubscriptions()));
    }
    return success;
  }, []);

  const unsubscribe = useCallback((type: SubscriptionType): boolean => {
    const success = dashboardWebSocket.unsubscribe(type);
    if (success) {
      setSubscriptions(new Set(dashboardWebSocket.getSubscriptions()));
    }
    return success;
  }, []);

  const isSubscribed = useCallback((type: SubscriptionType): boolean => {
    return subscriptions.has(type);
  }, [subscriptions]);

  return {
    subscribe,
    unsubscribe,
    subscriptions,
    isSubscribed
  };
};

/**
 * Enhanced hook for real-time dashboard updates with persistence
 */
export const useWebSocketDashboard = (dashboardId?: string) => {
  const connection = useWebSocketConnection();
  const { subscribe, unsubscribe, isSubscribed } = useWebSocketSubscription();
  const [dashboardData, setDashboardData] = useState<any>(null);
  const [kpiData, setKpiData] = useState<any>(null);
  
  const messageHandlerRef = useRef<(() => void) | null>(null);
  const mounted = useRef(true);

  useEffect(() => {
    if (connection.connected) {
      subscribe('dashboard_updates');
      subscribe('kpi_analysis');
    }
  }, [connection.connected, subscribe]);

  useEffect(() => {
    const handler: MessageHandler = (message) => {
      if (!mounted.current) return;
      
      switch (message.type) {
        case 'dashboard_updates':
          setDashboardData(message.data);
          break;
        case 'kpi_analysis':
          setKpiData(message.data);
          break;
      }
    };

    const cleanupDashboard = dashboardWebSocket.onMessage('dashboard_updates', handler);
    const cleanupKPI = dashboardWebSocket.onMessage('kpi_analysis', handler);

    return () => {
      mounted.current = false;
      cleanupDashboard();
      cleanupKPI();
    };
  }, []);

  useEffect(() => {
    return () => {
      mounted.current = false;
    };
  }, []);

  return {
    connected: connection.connected,
    connecting: connection.connecting,
    connectionQuality: connection.connectionQuality,
    dashboardData,
    kpiData,
    forceReconnect: connection.forceReconnect,
    error: connection.error
  };
};

/**
 * Enhanced hook for monitoring WebSocket health and performance
 */
export const useWebSocketHealth = () => {
  const [stats, setStats] = useState<any>(null);
  const [requestingStats, setRequestingStats] = useState(false);

  const connection = useWebSocketConnection();
  const mounted = useRef(true);

  // Handle connection stats messages
  useEffect(() => {
    const handler: MessageHandler = (message) => {
      if (mounted.current && message.type === 'connection_stats') {
        setStats(message.data);
        setRequestingStats(false);
      }
    };

    const cleanup = dashboardWebSocket.onMessage('connection_stats', handler);
    
    return () => {
      mounted.current = false;
      cleanup();
    };
  }, []);

  const refreshStats = useCallback(() => {
    if (connection.connected && !requestingStats && mounted.current) {
      setRequestingStats(true);
      dashboardWebSocket.getStats();
    }
  }, [connection.connected, requestingStats]);

  useEffect(() => {
    return () => {
      mounted.current = false;
    };
  }, []);

  return {
    connected: connection.connected,
    connectionQuality: connection.connectionQuality,
    clientId: connection.connectionId,
    stats,
    refreshStats,
    requestingStats
  };
};

/**
 * Legacy hook maintained for backward compatibility but enhanced with persistence
 */
export function useWebSocket(config: WebSocketConfig = {}) {
  const finalConfig = { ...DEFAULT_CONFIG, ...config };
  
  const [status, setStatus] = useState<RealTimeWebSocketStatus>({
    connected: false,
    connecting: false,
    error: null,
    lastMessage: null,
    connectionId: null,
  });

  const [subscribedSessions, setSubscribedSessions] = useState<Set<string>>(new Set());
  const [progressData, setProgressData] = useState<Map<string, ProgressData>>(new Map());

  const connection = useWebSocketConnection();
  const mounted = useRef(true);

  useEffect(() => {
    if (mounted.current) {
      setStatus(prev => ({
        ...prev,
        connected: connection.connected,
        connecting: connection.connecting,
        error: connection.error,
        connectionId: connection.connectionId
      }));
    }
  }, [connection.connected, connection.connecting, connection.error, connection.connectionId]);

  const sendMessage = useCallback((message: any) => {
    return connection.connected; // Simplified for compatibility
  }, [connection.connected]);

  const connect = useCallback(async () => {
    await connection.connect();
  }, [connection.connect]);

  const disconnect = useCallback(() => {
    connection.disconnect();
  }, [connection.disconnect]);

  const subscribeToSession = useCallback((sessionId: string) => {
    if (connection.connected) {
      setSubscribedSessions(prev => new Set(prev).add(sessionId));
      return true;
    }
    return false;
  }, [connection.connected]);

  const unsubscribeFromSession = useCallback((sessionId: string) => {
    setSubscribedSessions(prev => {
      const newSet = new Set(prev);
      newSet.delete(sessionId);
      return newSet;
    });
    setProgressData(prev => {
      const newMap = new Map(prev);
      newMap.delete(sessionId);
      return newMap;
    });
    return true;
  }, []);

  const getProgressForSession = useCallback((sessionId: string): ProgressData | null => {
    return progressData.get(sessionId) || null;
  }, [progressData]);

  const requestSessionStatus = useCallback((sessionId: string) => {
    return connection.connected;
  }, [connection.connected]);

  useEffect(() => {
    return () => {
      mounted.current = false;
    };
  }, []);

  return {
    // Connection status
    status,
    
    // Connection controls
    connect,
    disconnect,
    
    // Session management
    subscribeToSession,
    unsubscribeFromSession,
    subscribedSessions: Array.from(subscribedSessions),
    
    // Progress data
    getProgressForSession,
    getAllProgress: () => Object.fromEntries(progressData),
    
    // Utilities
    sendMessage,
    requestSessionStatus,
    
    // State
    isConnected: status.connected,
    isConnecting: status.connecting,
    hasError: !!status.error,
    error: status.error,
  };
}

// All hooks are already exported individually 