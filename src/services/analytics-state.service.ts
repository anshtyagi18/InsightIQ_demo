/**
 * Analytics State Service
 * Provides database-backed state management for analytics sessions,
 * file uploads, dashboard configurations, and comparison results.
 */

import { api } from './api';

export interface AnalyticsSession {
  id: string;
  sessionId: string;
  analysisType: string;
  fileInfo: {
    filename: string;
    fileType: string;
    size: number;
    uploadedAt: string;
    columns: string[];
    rowCount: number;
  };
  dashboardConfig?: any;
  aiInsights?: any[];
  performanceSummary?: any;
  createdAt: string;
  updatedAt: string;
}

export interface FileUpload {
  id: string;
  fileHash: string;
  filename: string;
  fileSize: number;
  mimeType: string;
  uploadPath: string;
  processed: boolean;
  metadata: {
    sessionId: string;
    userId?: string;
    columns?: string[];
    rowCount?: number;
  };
  createdAt: string;
}

export interface ComparisonResult {
  id: string;
  sessionId: string;
  estimatedFileHash: string;
  actualFileHash: string;
  comparisonData: any;
  insights: any;
  createdAt: string;
}

export interface UserSession {
  recentSessions: AnalyticsSession[];
  recentUploads: FileUpload[];
  preferences: {
    defaultChartType?: string;
    theme?: string;
    autoRefresh?: boolean;
  };
}

class AnalyticsStateService {
  private readonly CACHE_DURATION = 5 * 60 * 1000; // 5 minutes
  private cache = new Map<string, { data: any; timestamp: number }>();

  /**
   * Store analytics session in database
   */
  async storeAnalyticsSession(
    sessionId: string,
    analysisType: string,
    fileInfo: any,
    dashboardConfig: any,
    aiInsights?: any[],
    performanceMetrics?: any
  ): Promise<boolean> {
    try {
      console.log('💾 Storing analytics session in database...');
      
      const response = await api.post('/api/v1/analytics/sessions', {
        sessionId,
        analysisType,
        fileInfo,
        dashboardConfig,
        aiInsights: aiInsights || [],
        performanceMetrics: performanceMetrics || {}
      });

      // Clear cache for this session
      this.cache.delete(`session:${sessionId}`);
      this.cache.delete('user:recent-sessions');

      console.log('✅ Analytics session stored successfully');
      return true;
    } catch (error) {
      console.error('❌ Failed to store analytics session:', error);
      return false;
    }
  }

  /**
   * Get analytics session from database
   */
  async getAnalyticsSession(sessionId: string): Promise<AnalyticsSession | null> {
    try {
      const cacheKey = `session:${sessionId}`;
      const cached = this.getFromCache(cacheKey);
      if (cached) {
        console.log('📋 Retrieved session from cache');
        return cached;
      }

      console.log('🔍 Fetching analytics session from database...');
      
      const session = await api.get<AnalyticsSession>(`/api/v1/analytics/sessions/${sessionId}`);
      
      // Cache the result
      this.setCache(cacheKey, session);
      
      console.log('✅ Analytics session retrieved');
      return session;
    } catch (error) {
      console.error('❌ Failed to get analytics session:', error);
      return null;
    }
  }

  /**
   * Store file upload information
   */
  async storeFileUpload(
    sessionId: string,
    fileInfo: any,
    previewData?: any
  ): Promise<boolean> {
    try {
      console.log('📂 Storing file upload in database...');
      
      await api.post('/api/v1/files/store', {
        sessionId,
        fileInfo,
        previewData
      });

      // Clear relevant caches
      this.cache.delete(`upload:${sessionId}`);
      this.cache.delete('user:recent-uploads');

      console.log('✅ File upload stored successfully');
      return true;
    } catch (error) {
      console.error('❌ Failed to store file upload:', error);
      return false;
    }
  }

  /**
   * Get file upload information
   */
  async getFileUpload(sessionId: string): Promise<FileUpload | null> {
    try {
      const cacheKey = `upload:${sessionId}`;
      const cached = this.getFromCache(cacheKey);
      if (cached) {
        console.log('📋 Retrieved file upload from cache');
        return cached;
      }

      console.log('🔍 Fetching file upload from database...');
      
      const upload = await api.get<FileUpload>(`/api/v1/files/info/${sessionId}`);
      
      // Cache the result
      this.setCache(cacheKey, upload);
      
      console.log('✅ File upload retrieved');
      return upload;
    } catch (error) {
      console.error('❌ Failed to get file upload:', error);
      return null;
    }
  }

  /**
   * Store comparison result
   */
  async storeComparisonResult(
    sessionId: string,
    comparisonData: any,
    insights: any
  ): Promise<boolean> {
    try {
      console.log('🔬 Storing comparison result in database...');
      
      await api.post('/api/v1/comparison/store', {
        sessionId,
        comparisonData,
        insights
      });

      // Clear cache
      this.cache.delete(`comparison:${sessionId}`);

      console.log('✅ Comparison result stored successfully');
      return true;
    } catch (error) {
      console.error('❌ Failed to store comparison result:', error);
      return false;
    }
  }

  /**
   * Get comparison result
   */
  async getComparisonResult(sessionId: string): Promise<ComparisonResult | null> {
    try {
      const cacheKey = `comparison:${sessionId}`;
      const cached = this.getFromCache(cacheKey);
      if (cached) {
        console.log('📋 Retrieved comparison result from cache');
        return cached;
      }

      console.log('🔍 Fetching comparison result from database...');
      
      const result = await api.get<ComparisonResult>(`/api/v1/comparison/result/${sessionId}`);
      
      // Cache the result
      this.setCache(cacheKey, result);
      
      console.log('✅ Comparison result retrieved');
      return result;
    } catch (error) {
      console.error('❌ Failed to get comparison result:', error);
      return null;
    }
  }

  /**
   * Get user's recent sessions and uploads
   */
  async getUserSession(): Promise<UserSession> {
    try {
      const cacheKey = 'user:recent-sessions';
      const cached = this.getFromCache(cacheKey);
      if (cached) {
        console.log('📋 Retrieved user session from cache');
        return cached;
      }

      console.log('👤 Fetching user session data from database...');
      
      const [recentSessions, recentUploads] = await Promise.all([
        api.get<AnalyticsSession[]>('/api/v1/analytics/sessions/recent'),
        api.get<FileUpload[]>('/api/v1/files/recent')
      ]);

      const userSession: UserSession = {
        recentSessions,
        recentUploads,
        preferences: this.getUserPreferences()
      };

      // Cache the result
      this.setCache(cacheKey, userSession);
      
      console.log('✅ User session data retrieved');
      return userSession;
    } catch (error) {
      console.error('❌ Failed to get user session:', error);
      return {
        recentSessions: [],
        recentUploads: [],
        preferences: this.getUserPreferences()
      };
    }
  }

  /**
   * Update user preferences
   */
  async updateUserPreferences(preferences: Partial<UserSession['preferences']>): Promise<boolean> {
    try {
      console.log('⚙️ Updating user preferences...');
      
      // Store in localStorage and optionally backend
      const currentPrefs = this.getUserPreferences();
      const updatedPrefs = { ...currentPrefs, ...preferences };
      
      localStorage.setItem('user-preferences', JSON.stringify(updatedPrefs));
      
      // Clear relevant cache
      this.cache.delete('user:recent-sessions');
      
      console.log('✅ User preferences updated');
      return true;
    } catch (error) {
      console.error('❌ Failed to update user preferences:', error);
      return false;
    }
  }

  /**
   * Get user preferences from localStorage
   */
  private getUserPreferences(): UserSession['preferences'] {
    try {
      const stored = localStorage.getItem('user-preferences');
      return stored ? JSON.parse(stored) : {};
    } catch {
      return {};
    }
  }

  /**
   * Clear all cached data
   */
  clearCache(): void {
    console.log('🧹 Clearing analytics state cache');
    this.cache.clear();
  }

  /**
   * Clear specific session data from cache
   */
  clearSessionCache(sessionId: string): void {
    console.log(`🧹 Clearing cache for session: ${sessionId}`);
    this.cache.delete(`session:${sessionId}`);
    this.cache.delete(`upload:${sessionId}`);
    this.cache.delete(`comparison:${sessionId}`);
  }

  /**
   * Get data from cache if not expired
   */
  private getFromCache(key: string): any | null {
    const cached = this.cache.get(key);
    if (!cached) return null;

    const isExpired = Date.now() - cached.timestamp > this.CACHE_DURATION;
    if (isExpired) {
      this.cache.delete(key);
      return null;
    }

    return cached.data;
  }

  /**
   * Set data in cache with timestamp
   */
  private setCache(key: string, data: any): void {
    this.cache.set(key, {
      data,
      timestamp: Date.now()
    });
  }

  /**
   * Get current session ID or generate new one
   */
  getCurrentSessionId(): string {
    let sessionId = localStorage.getItem('current-session-id');
    if (!sessionId) {
      sessionId = `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
      localStorage.setItem('current-session-id', sessionId);
    }
    return sessionId;
  }

  /**
   * Start new analytics session
   */
  startNewSession(): string {
    const sessionId = `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    localStorage.setItem('current-session-id', sessionId);
    console.log('🚀 Started new analytics session:', sessionId);
    return sessionId;
  }

  /**
   * End current session
   */
  endCurrentSession(): void {
    const sessionId = localStorage.getItem('current-session-id');
    if (sessionId) {
      localStorage.removeItem('current-session-id');
      this.clearSessionCache(sessionId);
      console.log('🏁 Ended analytics session:', sessionId);
    }
  }
}

// Export singleton instance
export const analyticsStateService = new AnalyticsStateService();
export default analyticsStateService; 