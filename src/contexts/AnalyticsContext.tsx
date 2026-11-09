import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { analyticsStateService, AnalyticsSession, FileUpload, UserSession, ComparisonResult } from '../services/analytics-state.service';

interface FileInfo {
  name: string;
  size: number;
  type: string;
  lastModified: number;
}

interface AnalysisData {
  analysisType: string;
  fileInfo: FileInfo;
  dashboardConfig: DashboardConfig;
  aiInsights?: AIInsight[];
  performanceMetrics?: PerformanceMetrics;
}

interface AIInsight {
  type: string;
  content: string;
  confidence?: number;
}

interface PerformanceMetrics {
  processingTime: number;
  memoryUsage?: number;
  accuracy?: number;
}

interface DashboardConfig {
  charts: ChartConfig[];
  layout: string;
  theme?: string;
}

interface ChartConfig {
  id: string;
  type: string;
  title: string;
  data: unknown;
  options?: Record<string, unknown>;
}

interface ComparisonData {
  estimated: unknown[];
  actual: unknown[];
  analysis: ComparisonAnalysis;
}

interface ComparisonAnalysis {
  variance: number;
  correlation: number;
  insights: string[];
}

interface ComparisonInsights {
  summary: string;
  recommendations: string[];
  riskLevel: 'low' | 'medium' | 'high';
}

interface PreviewData {
  headers: string[];
  rows: unknown[][];
  totalRows: number;
}

interface AnalyticsContextType {
  // Current session
  currentSessionId: string | null;
  currentSession: AnalyticsSession | null;
  isLoading: boolean;
  
  // Session management
  startNewSession: () => string;
  endCurrentSession: () => void;
  getCurrentSession: () => Promise<AnalyticsSession | null>;
  
  // Data persistence
  storeAnalyticsSession: (
    analysisType: string,
    fileInfo: FileInfo,
    dashboardConfig: DashboardConfig,
    aiInsights?: AIInsight[],
    performanceMetrics?: PerformanceMetrics
  ) => Promise<boolean>;
  
  storeFileUpload: (fileInfo: FileInfo, previewData?: PreviewData) => Promise<boolean>;
  storeComparisonResult: (comparisonData: ComparisonData, insights: ComparisonInsights) => Promise<boolean>;
  
  // Data retrieval
  getFileUpload: (sessionId?: string) => Promise<FileUpload | null>;
  getComparisonResult: (sessionId?: string) => Promise<ComparisonResult | null>;
  getUserSessionData: () => Promise<UserSession>;
  
  // User preferences
  userPreferences: UserSession['preferences'];
  updateUserPreferences: (preferences: Partial<UserSession['preferences']>) => Promise<boolean>;
  
  // Cache management
  clearCache: () => void;
  refreshSession: () => Promise<void>;
}

const AnalyticsContext = createContext<AnalyticsContextType | undefined>(undefined);

export function useAnalytics() {
  const context = useContext(AnalyticsContext);
  if (context === undefined) {
    throw new Error('useAnalytics must be used within an AnalyticsProvider');
  }
  return context;
}

interface AnalyticsProviderProps {
  children: ReactNode;
}

export function AnalyticsProvider({ children }: AnalyticsProviderProps) {
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);
  const [currentSession, setCurrentSession] = useState<AnalyticsSession | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [userPreferences, setUserPreferences] = useState<UserSession['preferences']>({});

  // Initialize on mount
  useEffect(() => {
    initializeAnalytics();
  }, []);

  const initializeAnalytics = async () => {
    try {
      console.log('🚀 Initializing analytics context...');
      
      // Get or create current session
      const sessionId = analyticsStateService.getCurrentSessionId();
      setCurrentSessionId(sessionId);
      
      // Load user preferences and recent data
      const userSessionData = await analyticsStateService.getUserSession();
      setUserPreferences(userSessionData.preferences);
      
      console.log('✅ Analytics context initialized');
    } catch (error) {
      console.error('❌ Failed to initialize analytics context:', error);
    }
  };

  const startNewSession = (): string => {
    console.log('🆕 Starting new analytics session...');
    
    const sessionId = analyticsStateService.startNewSession();
    setCurrentSessionId(sessionId);
    setCurrentSession(null);
    
    console.log('✅ New session started:', sessionId);
    return sessionId;
  };

  const endCurrentSession = (): void => {
    console.log('🏁 Ending current analytics session...');
    
    if (currentSessionId) {
      analyticsStateService.endCurrentSession();
      setCurrentSessionId(null);
      setCurrentSession(null);
    }
    
    console.log('✅ Session ended');
  };

  const getCurrentSession = async (): Promise<AnalyticsSession | null> => {
    if (!currentSessionId) return null;
    
    try {
      if (currentSession && currentSession.sessionId === currentSessionId) {
        return currentSession;
      }
      
      console.log('🔍 Fetching current session from database...');
      const session = await analyticsStateService.getAnalyticsSession(currentSessionId);
      setCurrentSession(session);
      return session;
    } catch (error) {
      console.error('❌ Failed to get current session:', error);
      return null;
    }
  };

  const storeAnalyticsSession = async (
    analysisType: string,
    fileInfo: FileInfo,
    dashboardConfig: DashboardConfig,
    aiInsights?: AIInsight[],
    performanceMetrics?: PerformanceMetrics
  ): Promise<boolean> => {
    if (!currentSessionId) {
      console.warn('⚠️ No current session to store analytics data');
      return false;
    }

    try {
      setIsLoading(true);
      console.log('💾 Storing analytics session...');
      
      const success = await analyticsStateService.storeAnalyticsSession(
        currentSessionId,
        analysisType,
        fileInfo,
        dashboardConfig,
        aiInsights,
        performanceMetrics
      );
      
      if (success) {
        // Refresh current session data
        await getCurrentSession();
        console.log('✅ Analytics session stored successfully');
      }
      
      return success;
    } catch (error) {
      console.error('❌ Failed to store analytics session:', error);
      return false;
    } finally {
      setIsLoading(false);
    }
  };

  const storeFileUpload = async (fileInfo: FileInfo, previewData?: PreviewData): Promise<boolean> => {
    if (!currentSessionId) {
      console.warn('⚠️ No current session to store file upload');
      return false;
    }

    try {
      setIsLoading(true);
      console.log('📂 Storing file upload...');
      
      const success = await analyticsStateService.storeFileUpload(
        currentSessionId,
        fileInfo,
        previewData
      );
      
      if (success) {
        console.log('✅ File upload stored successfully');
      }
      
      return success;
    } catch (error) {
      console.error('❌ Failed to store file upload:', error);
      return false;
    } finally {
      setIsLoading(false);
    }
  };

  const storeComparisonResult = async (comparisonData: ComparisonData, insights: ComparisonInsights): Promise<boolean> => {
    if (!currentSessionId) {
      console.warn('⚠️ No current session to store comparison result');
      return false;
    }

    try {
      setIsLoading(true);
      console.log('🔬 Storing comparison result...');
      
      const success = await analyticsStateService.storeComparisonResult(
        currentSessionId,
        comparisonData,
        insights
      );
      
      if (success) {
        console.log('✅ Comparison result stored successfully');
      }
      
      return success;
    } catch (error) {
      console.error('❌ Failed to store comparison result:', error);
      return false;
    } finally {
      setIsLoading(false);
    }
  };

  const getFileUpload = async (sessionId?: string): Promise<FileUpload | null> => {
    const targetSessionId = sessionId || currentSessionId;
    if (!targetSessionId) return null;

    try {
      console.log('🔍 Fetching file upload...');
      const fileUpload = await analyticsStateService.getFileUpload(targetSessionId);
      
      if (fileUpload) {
        console.log('✅ File upload retrieved');
      }
      
      return fileUpload;
    } catch (error) {
      console.error('❌ Failed to get file upload:', error);
      return null;
    }
  };

  const getComparisonResult = async (sessionId?: string): Promise<ComparisonResult | null> => {
    const targetSessionId = sessionId || currentSessionId;
    if (!targetSessionId) return null;

    try {
      console.log('🔍 Fetching comparison result...');
      const result = await analyticsStateService.getComparisonResult(targetSessionId);
      
      if (result) {
        console.log('✅ Comparison result retrieved');
      }
      
      return result;
    } catch (error) {
      console.error('❌ Failed to get comparison result:', error);
      return null;
    }
  };

  const getUserSessionData = async (): Promise<UserSession> => {
    try {
      console.log('👤 Fetching user session data...');
      const userSession = await analyticsStateService.getUserSession();
      
      // Update local preferences
      setUserPreferences(userSession.preferences);
      
      console.log('✅ User session data retrieved');
      return userSession;
    } catch (error) {
      console.error('❌ Failed to get user session data:', error);
      return {
        recentSessions: [],
        recentUploads: [],
        preferences: {}
      };
    }
  };

  const updateUserPreferences = async (preferences: Partial<UserSession['preferences']>): Promise<boolean> => {
    try {
      console.log('⚙️ Updating user preferences...');
      
      const success = await analyticsStateService.updateUserPreferences(preferences);
      
      if (success) {
        // Update local state
        setUserPreferences(prev => ({ ...prev, ...preferences }));
        console.log('✅ User preferences updated');
      }
      
      return success;
    } catch (error) {
      console.error('❌ Failed to update user preferences:', error);
      return false;
    }
  };

  const clearCache = (): void => {
    console.log('🧹 Clearing analytics cache...');
    analyticsStateService.clearCache();
    setCurrentSession(null);
  };

  const refreshSession = async (): Promise<void> => {
    if (!currentSessionId) return;

    try {
      console.log('🔄 Refreshing current session...');
      
      // Clear local session and refetch from database
      setCurrentSession(null);
      analyticsStateService.clearSessionCache(currentSessionId);
      
      await getCurrentSession();
      
      console.log('✅ Session refreshed');
    } catch (error) {
      console.error('❌ Failed to refresh session:', error);
    }
  };

  const value: AnalyticsContextType = {
    // Current session
    currentSessionId,
    currentSession,
    isLoading,
    
    // Session management
    startNewSession,
    endCurrentSession,
    getCurrentSession,
    
    // Data persistence
    storeAnalyticsSession,
    storeFileUpload,
    storeComparisonResult,
    
    // Data retrieval
    getFileUpload,
    getComparisonResult,
    getUserSessionData,
    
    // User preferences
    userPreferences,
    updateUserPreferences,
    
    // Cache management
    clearCache,
    refreshSession,
  };

  return <AnalyticsContext.Provider value={value}>{children}</AnalyticsContext.Provider>;
} 