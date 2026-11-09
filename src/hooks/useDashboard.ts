/**
 * Dashboard Integration Hook
 * Provides complete dashboard functionality using our new services layer
 */

import { useState, useCallback, useEffect, useMemo } from 'react';
import { toast } from 'sonner';
import { 
  dashboardService, 
  uploadService, 
  exportService,
  analyticsService,
  DashboardConfig,
  ChartConfig,
  KPIConfig,
  DashboardGenerationRequest,
  DashboardExportRequest,
  ExportResponse,
  ChartRecommendationRequest,
  KPICalculationRequest,

  FileUploadResponse
} from '@/services';
import { useWebSocketConnection, useWebSocketDashboard } from './useWebSocket';

interface UseDashboardOptions {
  autoRefresh?: boolean;
  refreshInterval?: number;
}

interface DashboardState {
  config: DashboardConfig | null;
  charts: ChartConfig[];
  kpis: KPIConfig[];
  loading: boolean;
  error: string | null;
  lastGenerated: Date | null;
}

interface UploadState {
  uploading: boolean;
  progress: number;
  fileName: string | null;
  error: string | null;
  result: FileUploadResponse | null;
}

interface ExportState {
  exporting: boolean;
  progress: number;
  error: string | null;
  result: ExportResponse | null;
}

interface AnalyticsSummary {
  totalDashboards: number;
  avgProcessingTime: number;
  successRate: number;
  lastGenerated: Date | null;
}

export function useDashboard(options: UseDashboardOptions = {}) {
  const { autoRefresh = false, refreshInterval = 30000 } = options;
  
  // Enhanced WebSocket integration for persistent connections
  const webSocketConnection = useWebSocketConnection(undefined, true);
  const webSocketDashboard = useWebSocketDashboard();

  // Dashboard state
  const [dashboardState, setDashboardState] = useState<DashboardState>(() => {
    // Try to restore state from localStorage on initialization
    try {
      const saved = localStorage.getItem('current_dashboard_state');
      if (saved) {
        const parsed = JSON.parse(saved);
        console.log('🔄 Restored dashboard state from localStorage');
        return {
          ...parsed,
          lastGenerated: parsed.lastGenerated ? new Date(parsed.lastGenerated) : null,
          loading: false, // Always start with loading false
          error: null // Clear any previous errors
        };
      }
    } catch (error) {
      console.warn('Failed to restore dashboard state:', error);
    }
    
    return {
      config: null,
      charts: [],
      kpis: [],
      loading: false,
      error: null,
      lastGenerated: null,
    };
  });

  // Upload state
  const [uploadState, setUploadState] = useState<UploadState>({
    uploading: false,
    progress: 0,
    fileName: null,
    error: null,
    result: null,
  });

  // Export state
  const [exportState, setExportState] = useState<ExportState>({
    exporting: false,
    progress: 0,
    error: null,
    result: null,
  });

  // Analytics summary - computed from analytics service
  const analyticsSummary = useMemo((): AnalyticsSummary => {
    try {
      const metrics = analyticsService.calculateMetrics();
      return {
        totalDashboards: metrics.totalDashboards,
        avgProcessingTime: metrics.avgProcessingTime,
        successRate: metrics.successRate,
        lastGenerated: dashboardState.lastGenerated
      };
    } catch (error) {
      console.error('Failed to calculate analytics summary:', error);
      return {
        totalDashboards: 0,
        avgProcessingTime: 0,
        successRate: 0,
        lastGenerated: null
      };
    }
  }, [dashboardState.lastGenerated]);

  // Persist dashboard state to localStorage whenever it changes
  useEffect(() => {
    if (dashboardState.config) {
      try {
        const stateToSave = {
          ...dashboardState,
          lastGenerated: dashboardState.lastGenerated?.toISOString()
        };
        localStorage.setItem('current_dashboard_state', JSON.stringify(stateToSave));
        console.log('💾 Dashboard state saved to localStorage');
      } catch (error) {
        console.warn('Failed to save dashboard state:', error);
      }
    }
  }, [dashboardState]);

  // Monitor WebSocket connection for real-time updates
  useEffect(() => {
    if (webSocketDashboard.connected) {
      console.log('🔌 WebSocket connected - dashboard ready for real-time updates');
      
      // Handle real-time dashboard updates
      if (webSocketDashboard.dashboardData) {
        console.log('📊 Received real-time dashboard update');
        // Update dashboard state with real-time data if appropriate
        // This could include KPI updates, alert notifications, etc.
      }
      
      if (webSocketDashboard.kpiData) {
        console.log('📈 Received real-time KPI update');
        // Update KPI state with real-time data
      }
    }
  }, [
    webSocketDashboard.connected, 
    webSocketDashboard.dashboardData, 
    webSocketDashboard.kpiData
  ]);

  // Connection quality monitoring and auto-reconnection
  useEffect(() => {
    if (webSocketConnection.connectionQuality === 'poor' || webSocketConnection.connectionQuality === 'critical') {
      console.warn(`⚠️ WebSocket connection quality is ${webSocketConnection.connectionQuality}`);
    }
    
    // Auto-reconnect if connection is lost and we have dashboard data
    if (!webSocketConnection.connected && dashboardState.config && webSocketConnection.retryCount < 5) {
      console.log('🔄 Attempting to restore WebSocket connection for dashboard');
      webSocketConnection.connect();
    }
  }, [
    webSocketConnection.connected, 
    webSocketConnection.connectionQuality, 
    webSocketConnection.retryCount,
    dashboardState.config
  ]);

  /**
   * Enhanced file upload with persistent connection handling
   */
  const uploadFile = useCallback(async (file: File) => {
    setUploadState(prev => ({ ...prev, uploading: true, progress: 0, error: null }));
    
    try {
      // Ensure WebSocket connection is available for real-time updates
      if (!webSocketConnection.connected) {
        console.log('🔌 Establishing WebSocket connection for file upload tracking...');
        await webSocketConnection.connect();
      }

      const result = await uploadService.uploadFile(file, {
        onProgress: (progress) => {
          setUploadState(prev => ({ ...prev, progress }));
        }
      });

      setUploadState(prev => ({
        ...prev,
        uploading: false,
        progress: 100,
        result,
      }));

      return result;
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Upload failed';
      setUploadState(prev => ({
        ...prev,
        uploading: false,
        error: errorMessage,
      }));
      throw error;
    }
  }, [webSocketConnection, dashboardService]);

  /**
   * Enhanced dashboard generation with WebSocket integration
   */
  const generateDashboard = useCallback(async (
    request: DashboardGenerationRequest
  ) => {
    setDashboardState(prev => ({ ...prev, loading: true, error: null }));
    
    try {
      // Ensure WebSocket connection for real-time updates
      if (!webSocketConnection.connected) {
        console.log('🔌 Establishing WebSocket connection for dashboard generation...');
        await webSocketConnection.connect();
      }

      const dashboard = await dashboardService.generateDashboardFromFile(request);

      const newState = {
        config: dashboard,
        charts: dashboard.charts || [],
        kpis: dashboard.kpis || [],
        loading: false,
        error: null,
        lastGenerated: new Date(),
      };

      setDashboardState(newState);
      
      console.log('✅ Dashboard generated successfully with WebSocket support');
      return dashboard;
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Dashboard generation failed';
      setDashboardState(prev => ({
        ...prev,
        loading: false,
        error: errorMessage,
      }));
      throw error;
    }
  }, [dashboardService, webSocketConnection]);

  /**
   * Upload file and generate AI-powered dashboard in one step
   */
  const uploadAndGenerateDashboard = useCallback(async (
    file: File, 
    options?: {
      chartPreferences?: Record<string, any>;
      kpiRequirements?: string[];
      layoutType?: string;
      theme?: string;
    }
  ) => {
    try {
      console.log('🔄 Starting upload and AI dashboard generation workflow...');
      
      // Generate dashboard directly from file using AI-powered backend
      const dashboardConfig = await generateDashboard({
        file,
        chartPreferences: options?.chartPreferences,
        kpiRequirements: options?.kpiRequirements,
        layoutType: options?.layoutType || 'responsive',
        theme: options?.theme || 'default',
      });

      console.log('✅ Upload and AI dashboard generation completed successfully');
      return { dashboardConfig };
    } catch (error) {
      console.error('❌ Upload and dashboard generation failed:', error);
      throw error;
    }
  }, [generateDashboard]);

  /**
   * Generate dashboard from already uploaded file with AI analysis
   */
  const generateDashboardFromUpload = useCallback(async (
    filePath: string,
    sessionId?: string,
    options?: {
      chartPreferences?: Record<string, any>;
      kpiRequirements?: string[];
      layoutType?: string;
      theme?: string;
    }
  ) => {
    setDashboardState(prev => ({ ...prev, loading: true, error: null }));
    
    try {
      console.log('🧠 Starting AI-powered dashboard generation from uploaded file:', filePath);
      
      const config = await dashboardService.generateDashboardFromUpload(
        filePath,
        sessionId,
        options
      );
      
      console.log('✅ AI dashboard generation from upload completed:', config);
      
      setDashboardState(prev => ({
        ...prev,
        config,
        charts: config.charts,
        kpis: config.kpis,
        loading: false,
        lastGenerated: new Date(),
      }));

      return config;
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to generate dashboard from uploaded file';
      console.error('❌ Dashboard generation from upload failed:', error);
      setDashboardState(prev => ({
        ...prev,
        loading: false,
        error: errorMessage,
      }));
      throw error;
    }
  }, []);

  /**
   * Get chart recommendations for existing data
   */
  const getChartRecommendations = useCallback(async (
    data: Record<string, any>,
    context?: string,
    priorityMetrics?: string[]
  ) => {
    setDashboardState(prev => ({ ...prev, loading: true, error: null }));
    
    try {
      const recommendations = await dashboardService.getChartRecommendations({
        data,
        context,
        priorityMetrics,
      });

      setDashboardState(prev => ({
        ...prev,
        charts: recommendations,
        loading: false,
      }));

      return recommendations;
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to get chart recommendations';
      setDashboardState(prev => ({
        ...prev,
        loading: false,
        error: errorMessage,
      }));
      throw error;
    }
  }, []);

  /**
   * Calculate KPIs for existing data
   */
  const calculateKPIs = useCallback(async (
    data: Record<string, any>,
    kpiDefinitions?: Array<Record<string, any>>
  ) => {
    setDashboardState(prev => ({ ...prev, loading: true, error: null }));
    
    try {
      const kpis = await dashboardService.calculateKPIs({
        data,
        kpiDefinitions,
      });

      setDashboardState(prev => ({
        ...prev,
        kpis,
        loading: false,
      }));

      return kpis;
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to calculate KPIs';
      setDashboardState(prev => ({
        ...prev,
        loading: false,
        error: errorMessage,
      }));
      throw error;
    }
  }, []);

  /**
   * Export dashboard
   */
  const exportDashboard = useCallback(async (request: DashboardExportRequest) => {
    setExportState({
      exporting: true,
      progress: 0,
      error: null,
      result: null,
    });

    try {
      const result = await exportService.exportDashboard(request);
      
      setExportState(prev => ({
        ...prev,
        exporting: false,
        progress: 100,
        result,
      }));

      return result;
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Export failed';
      setExportState(prev => ({
        ...prev,
        exporting: false,
        error: errorMessage,
      }));
      throw error;
    }
  }, []);

  /**
   * Download exported dashboard
   */
  const downloadExport = useCallback(async (exportId: string, filename: string) => {
    try {
      await exportService.triggerDownload(exportId, filename);
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Download failed';
      setExportState(prev => ({
        ...prev,
        error: errorMessage,
      }));
      throw error;
    }
  }, []);

  /**
   * Enhanced reset with connection preservation
   */
  const resetDashboard = useCallback(() => {
    setDashboardState({
      config: null,
      charts: [],
      kpis: [],
      loading: false,
      error: null,
      lastGenerated: null,
    });
    
    // Clear dashboard state from localStorage
    try {
      localStorage.removeItem('current_dashboard_state');
      console.log('🗑️ Dashboard state cleared from localStorage');
    } catch (error) {
      console.error('Failed to clear dashboard state:', error);
    }

    // Don't disconnect WebSocket - maintain persistent connection
    if (webSocketConnection.connected) {
      console.log('🔌 WebSocket connection maintained during dashboard reset');
    }
  }, [webSocketConnection]);

  /**
   * Reset upload state
   */
  const resetUpload = useCallback(() => {
    setUploadState({
      uploading: false,
      progress: 0,
      fileName: null,
      error: null,
      result: null,
    });
  }, []);

  /**
   * Reset export state
   */
  const resetExport = useCallback(() => {
    setExportState({
      exporting: false,
      progress: 0,
      error: null,
      result: null,
    });
  }, []);

  /**
   * Manually set dashboard state (for chat-generated dashboards)
   */
  const setDashboard = useCallback((newDashboardData: {
    config: DashboardConfig;
    charts: ChartConfig[];
    kpis: KPIConfig[];
  }) => {
    setDashboardState({
      config: newDashboardData.config,
      charts: newDashboardData.charts,
      kpis: newDashboardData.kpis,
      loading: false,
      error: null,
      lastGenerated: new Date(),
    });
  }, []);

  /**
   * Analyze file structure for Smart Metric Selector
   */
  const analyzeFileStructure = useCallback(async (file: File) => {
    try {
      console.log('🔍 Analyzing file structure for Smart Metric Selector...');
      
      const analysis = await dashboardService.analyzeFileStructure(file);
      
      console.log('✅ File structure analysis completed:', analysis);
      return analysis;
    } catch (error) {
      console.error('❌ File structure analysis failed:', error);
      throw error;
    }
  }, []);

  /**
   * Generate dashboard with user-selected metrics
   */
  const generateDashboardWithSelectedMetrics = useCallback(async (
    file: File,
    selectedMetrics: string[],
    options?: {
      chartPreferences?: Record<string, any>;
      kpiRequirements?: string[];
      layoutType?: string;
      theme?: string;
    }
  ) => {
    setDashboardState(prev => ({ ...prev, loading: true, error: null }));
    
    try {
      console.log('🎯 Starting Smart Metric Selector dashboard generation...');
      
      const config = await dashboardService.generateDashboardWithSelectedMetrics({
        file,
        selectedMetrics,
        chartPreferences: options?.chartPreferences,
        kpiRequirements: options?.kpiRequirements,
        layoutType: options?.layoutType || 'responsive',
        theme: options?.theme || 'default'
      });
      
      console.log('✅ Smart Metric Selector dashboard generation completed:', config);
      
      setDashboardState(prev => ({
        ...prev,
        config,
        charts: config.charts,
        kpis: config.kpis,
        loading: false,
        lastGenerated: new Date(),
      }));

      return config;
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to generate dashboard with selected metrics';
      console.error('❌ Smart Metric Selector dashboard generation failed:', error);
      setDashboardState(prev => ({
        ...prev,
        loading: false,
        error: errorMessage,
      }));
      throw error;
    }
  }, []);

  /**
   * Generate dashboard with user-selected metric pairs
   */
  const generateDashboardWithMetricPairs = useCallback(async (
    file: File,
    metricPairs: Array<{
      id: string;
      xAxis: any;
      yAxis: any;
      chartType: string;
      name?: string;
    }>,
    options?: {
      layoutType?: string;
      theme?: string;
    }
  ) => {
    setDashboardState(prev => ({ ...prev, loading: true, error: null }));
    
    try {
      console.log('🎯 Starting Metric Pairs dashboard generation...');
      
      const config = await dashboardService.generateDashboardWithMetricPairs({
        file,
        metricPairs,
        layoutType: options?.layoutType || 'responsive',
        theme: options?.theme || 'default'
      });
      
      console.log('✅ Metric Pairs dashboard generation completed:', config);
      
      setDashboardState(prev => ({
        ...prev,
        config,
        charts: config.charts,
        kpis: config.kpis,
        loading: false,
        lastGenerated: new Date(),
      }));

      return config;
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to generate dashboard with metric pairs';
      console.error('❌ Metric Pairs dashboard generation failed:', error);
      setDashboardState(prev => ({
        ...prev,
        loading: false,
        error: errorMessage,
      }));
      throw error;
    }
  }, []);

  // Auto-refresh functionality
  useEffect(() => {
    if (!autoRefresh || !dashboardState.config) return;

    const interval = setInterval(() => {
      // Refresh dashboard data if needed
      // This could trigger KPI recalculation or chart updates
      console.log('Auto-refreshing dashboard...');
    }, refreshInterval);

    return () => clearInterval(interval);
  }, [autoRefresh, refreshInterval, dashboardState.config]);

  return {
    // Dashboard state
    dashboard: dashboardState,
    upload: uploadState,
    export: exportState,
    
    // WebSocket connection state
    webSocket: {
      connected: webSocketConnection.connected,
      connecting: webSocketConnection.connecting,
      connectionQuality: webSocketConnection.connectionQuality,
      clientId: webSocketConnection.connectionId,
      error: webSocketConnection.error,
      retryCount: webSocketConnection.retryCount,
      forceReconnect: webSocketConnection.forceReconnect
    },
    
    // Dashboard actions
    generateDashboard,
    generateDashboardFromUpload,
    uploadFile,
    uploadAndGenerateDashboard,
    getChartRecommendations,
    calculateKPIs,
    setDashboard,
    
    // Export actions
    exportDashboard,
    downloadExport,
    
    // Reset actions
    resetDashboard,
    resetUpload,
    resetExport,
    
    // Computed values
    isReady: !!dashboardState.config,
    hasData: dashboardState.charts.length > 0 || dashboardState.kpis.length > 0,
    isLoading: dashboardState.loading || uploadState.uploading || exportState.exporting,
    
    // Connection health
    connectionHealthy: webSocketConnection.connected && webSocketConnection.connectionQuality === 'good',
    
    // Analytics summary
    analytics: analyticsSummary,

    analyzeFileStructure,
    generateDashboardWithSelectedMetrics,
    generateDashboardWithMetricPairs,
  };
}

export default useDashboard; 