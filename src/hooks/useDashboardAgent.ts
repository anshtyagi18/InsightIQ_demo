/**
 * Dashboard Agent React Hooks
 * 
 * Custom hooks for seamless integration with the Dashboard Agent API
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { dashboardAgentService } from '../services/dashboard-agent';
import {
  DashboardData,
  BulkDashboardData,
  DashboardSummary,
  KPIAnalysis,
  AlertAnalysis,
  CustomInsight,
  AgentInfo,
  Alert,
  UseDashboardDataResult,
  UseCustomInsightResult,
  UseAgentInfoResult,
  DashboardConfig
} from '../types/dashboard';

// Default configuration
const DEFAULT_CONFIG: DashboardConfig = {
  autoRefresh: false,
  refreshInterval: 300000, // 5 minutes
  enableCache: true,
  enableAI: true,
  fallbackMode: true
};

/**
 * Hook for comprehensive dashboard data management
 */
export const useDashboardData = (
  companyName: string,
  dashboardData: DashboardData,
  timePeriod: string = 'last_month',
  config: Partial<DashboardConfig> = {}
): UseDashboardDataResult => {
  const finalConfig = { ...DEFAULT_CONFIG, ...config };
  const queryClient = useQueryClient();

  const queryKey = ['dashboard-data', companyName, timePeriod, JSON.stringify(dashboardData)];

  const {
    data,
    isLoading: loading,
    error,
    refetch: queryRefetch
  } = useQuery({
    queryKey,
    queryFn: async () => {
      if (finalConfig.fallbackMode) {
        return await dashboardAgentService.getDashboardDataWithFallback(
          companyName,
          dashboardData,
          timePeriod
        );
      } else {
        return await dashboardAgentService.getBulkDashboardData({
          company_name: companyName,
          dashboard_data: dashboardData,
          time_period: timePeriod,
          use_ai: finalConfig.enableAI
        });
      }
    },
    enabled: !!companyName && !!dashboardData,
    staleTime: finalConfig.enableCache ? 60000 : 0, // 1 minute cache
    refetchInterval: finalConfig.autoRefresh ? finalConfig.refreshInterval : false,
    retry: 2,
    retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000)
  });

  const refetch = useCallback(async () => {
    await queryRefetch();
  }, [queryRefetch]);

  const clearCache = useCallback(() => {
    queryClient.removeQueries({ queryKey });
  }, [queryClient, queryKey]);

  return {
    data: data || null,
    loading,
    error: error instanceof Error ? error.message : null,
    refetch,
    summary: data?.summary || null,
    kpiAnalysis: data?.kpi_analysis || null,
    alertsAnalysis: data?.alerts_analysis || null,
    clearCache
  };
};

/**
 * Hook for dashboard summary generation
 */
export const useDashboardSummary = (
  companyName: string,
  dashboardData: DashboardData,
  timePeriod: string = 'last_month',
  focusAreas?: string[]
) => {
  const mutation = useMutation({
    mutationFn: async () => {
      return await dashboardAgentService.generateSummary({
        company_name: companyName,
        dashboard_data: dashboardData,
        time_period: timePeriod,
        focus_areas: focusAreas,
        use_ai: true
      });
    },
    retry: 1
  });

  return {
    generateSummary: mutation.mutate,
    data: mutation.data,
    loading: mutation.isPending,
    error: mutation.error instanceof Error ? mutation.error.message : null,
    reset: mutation.reset
  };
};

/**
 * Hook for KPI analysis
 */
export const useKPIAnalysis = () => {
  const mutation = useMutation({
    mutationFn: async (params: {
      kpiData: Record<string, any>;
      analysisType?: string;
    }) => {
      return await dashboardAgentService.analyzeKPIs({
        kpi_data: params.kpiData,
        analysis_type: params.analysisType || 'trend',
        use_ai: true
      });
    },
    retry: 1
  });

  return {
    analyzeKPIs: mutation.mutate,
    data: mutation.data,
    loading: mutation.isPending,
    error: mutation.error instanceof Error ? mutation.error.message : null,
    reset: mutation.reset
  };
};

/**
 * Hook for alert analysis
 */
export const useAlertAnalysis = () => {
  const mutation = useMutation({
    mutationFn: async (params: {
      alerts: Alert[];
      priorityFilter?: string;
    }) => {
      return await dashboardAgentService.processAlerts({
        alerts_data: params.alerts,
        priority_filter: params.priorityFilter,
        use_ai: true
      });
    },
    retry: 1
  });

  return {
    processAlerts: mutation.mutate,
    data: mutation.data,
    loading: mutation.isPending,
    error: mutation.error instanceof Error ? mutation.error.message : null,
    reset: mutation.reset
  };
};

/**
 * Hook for custom insights generation
 */
export const useCustomInsight = (): UseCustomInsightResult => {
  const [insight, setInsight] = useState<CustomInsight | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const generateInsight = useCallback(async (
    data: Record<string, any>,
    prompt: string,
    context?: string
  ) => {
    setLoading(true);
    setError(null);

    try {
      const result = await dashboardAgentService.generateCustomInsight({
        data,
        prompt,
        context
      });
      setInsight(result);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to generate insight';
      setError(errorMessage);
      setInsight(null);
    } finally {
      setLoading(false);
    }
  }, []);

  const reset = useCallback(() => {
    setInsight(null);
    setError(null);
    setLoading(false);
  }, []);

  return {
    insight,
    loading,
    error,
    generateInsight,
    reset
  };
};

/**
 * Hook for agent information and status
 */
export const useAgentInfo = (): UseAgentInfoResult => {
  const { data: agentInfo, isLoading: loading, error, refetch } = useQuery({
    queryKey: ['agent-info'],
    queryFn: () => dashboardAgentService.getAgentInfo(),
    staleTime: 30000, // 30 seconds
    retry: 2
  });

  const refresh = useCallback(async () => {
    await refetch();
  }, [refetch]);

  return {
    agentInfo: agentInfo || null,
    loading,
    error: error instanceof Error ? error.message : null,
    refresh
  };
};

/**
 * Hook for agent health monitoring
 */
export const useAgentHealth = (refreshInterval?: number) => {
  const { data: healthStatus, isLoading: loading, error } = useQuery({
    queryKey: ['agent-health'],
    queryFn: () => dashboardAgentService.checkHealth(),
    refetchInterval: refreshInterval || 60000, // 1 minute default
    retry: 1,
    staleTime: 30000
  });

  const isHealthy = healthStatus?.status === 'healthy';
  const aiAvailable = healthStatus?.ai_status?.available || false;

  return {
    healthStatus,
    isHealthy,
    aiAvailable,
    loading,
    error: error instanceof Error ? error.message : null
  };
};

/**
 * Hook for agent status information (lightweight)
 */
export const useAgentStatus = () => {
  const [status, setStatus] = useState<{
    available: boolean;
    aiEnabled: boolean;
    version?: string;
    error?: string;
  }>({
    available: false,
    aiEnabled: false
  });

  const [loading, setLoading] = useState(false);

  const checkStatus = useCallback(async () => {
    setLoading(true);
    try {
      const statusInfo = await dashboardAgentService.getAgentStatus();
      setStatus(statusInfo);
    } catch (error) {
      setStatus({
        available: false,
        aiEnabled: false,
        error: error instanceof Error ? error.message : 'Unknown error'
      });
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    checkStatus();
  }, [checkStatus]);

  return {
    status,
    loading,
    refresh: checkStatus
  };
};

/**
 * Hook for cache management
 */
export const useCacheManagement = () => {
  const queryClient = useQueryClient();

  const clearAllCache = useCallback(() => {
    queryClient.clear();
  }, [queryClient]);

  const clearDashboardCache = useCallback(() => {
    queryClient.removeQueries({ queryKey: ['dashboard-data'] });
  }, [queryClient]);

  const clearAgentCache = useCallback(async () => {
    try {
      await dashboardAgentService.clearCache();
      // Also clear React Query cache
      queryClient.removeQueries({ queryKey: ['dashboard-data'] });
      return true;
    } catch (error) {
      console.error('Failed to clear agent cache:', error);
      return false;
    }
  }, [queryClient]);

  return {
    clearAllCache,
    clearDashboardCache,
    clearAgentCache
  };
};

/**
 * Hook for managing dashboard configuration
 */
export const useDashboardConfig = () => {
  const [config, setConfig] = useState<DashboardConfig>(DEFAULT_CONFIG);

  const updateConfig = useCallback((updates: Partial<DashboardConfig>) => {
    setConfig(prev => ({ ...prev, ...updates }));
  }, []);

  const resetConfig = useCallback(() => {
    setConfig(DEFAULT_CONFIG);
  }, []);

  return {
    config,
    updateConfig,
    resetConfig
  };
};

/**
 * Hook for real-time dashboard updates (polling-based)
 */
export const useRealTimeDashboard = (
  companyName: string,
  dashboardData: DashboardData,
  timePeriod: string = 'last_month',
  intervalMs: number = 60000 // 1 minute default
) => {
  const intervalRef = useRef<NodeJS.Timeout>();
  const [isRealTimeEnabled, setIsRealTimeEnabled] = useState(false);

  const dashboardResult = useDashboardData(companyName, dashboardData, timePeriod, {
    autoRefresh: isRealTimeEnabled,
    refreshInterval: intervalMs
  });

  const enableRealTime = useCallback(() => {
    setIsRealTimeEnabled(true);
  }, []);

  const disableRealTime = useCallback(() => {
    setIsRealTimeEnabled(false);
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
    }
  }, []);

  const toggleRealTime = useCallback(() => {
    if (isRealTimeEnabled) {
      disableRealTime();
    } else {
      enableRealTime();
    }
  }, [isRealTimeEnabled, enableRealTime, disableRealTime]);

  useEffect(() => {
    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, []);

  return {
    ...dashboardResult,
    isRealTimeEnabled,
    enableRealTime,
    disableRealTime,
    toggleRealTime
  };
}; 