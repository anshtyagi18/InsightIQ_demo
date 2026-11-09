/**
 * Dashboard Agent API Types
 * 
 * TypeScript interfaces for the Dashboard Agent integration
 */

// Base API response structure from FastAPI
export interface StandardResponse<T = any> {
  success: boolean;
  data: T;
  message?: string;
  timestamp: string;
}

// Dashboard data structures
export interface DashboardData {
  metrics?: Record<string, number>;
  kpis?: Record<string, any>;
  alerts?: Alert[];
  [key: string]: any;
}

export interface Alert {
  id: string;
  message: string;
  priority: 'high' | 'medium' | 'low';
  timestamp: string;
  [key: string]: any;
}

// Request types
export interface DashboardSummaryRequest {
  company_name: string;
  dashboard_data: DashboardData;
  time_period?: string;
  focus_areas?: string[];
  use_ai?: boolean;
}

export interface KPIAnalysisRequest {
  kpi_data: Record<string, any>;
  analysis_type?: string;
  use_ai?: boolean;
}

export interface AlertsRequest {
  alerts_data: Alert[];
  priority_filter?: string;
  use_ai?: boolean;
}

export interface CustomInsightRequest {
  data: Record<string, any>;
  prompt: string;
  context?: string;
}

// Response data types
export interface DashboardSummary {
  content: string;
  ai_generated: boolean;
  confidence?: number;
  kpis_analyzed: number;
  focus_areas: string[];
  time_period: string;
  generated_at: string;
  model_used?: string;
  from_cache: boolean;
  metadata?: Record<string, any>;
  fallback_reason?: string;
}

export interface KPIAnalysis {
  insights: string;
  ai_generated: boolean;
  analysis_type: string;
  kpis_count: number;
  confidence?: number;
  generated_at: string;
  model_used?: string;
  from_cache: boolean;
  raw_data: Record<string, any>;
  metadata?: Record<string, any>;
  fallback_reason?: string;
}

export interface AlertAnalysis {
  summary: string;
  ai_generated: boolean;
  total_alerts: number;
  priority_filter?: string;
  confidence?: number;
  generated_at: string;
  model_used?: string;
  from_cache: boolean;
  alerts: Alert[];
  metadata?: Record<string, any>;
  fallback_reason?: string;
}

export interface CustomInsight {
  insight: string;
  ai_generated: boolean;
  user_prompt: string;
  context?: string;
  confidence?: number;
  generated_at: string;
  model_used?: string;
  from_cache: boolean;
  data_analyzed: Record<string, any>;
  metadata?: Record<string, any>;
  error?: boolean;
}

// Bulk dashboard data response
export interface BulkDashboardData {
  summary?: DashboardSummary;
  kpi_analysis?: KPIAnalysis;
  alerts_analysis?: AlertAnalysis;
  generated_at: string;
  company_name: string;
  time_period: string;
}

// Agent information
export interface AgentInfo {
  agent_id: string;
  name: string;
  description: string;
  version: string;
  capabilities: string[];
  ai_provider: {
    available: boolean;
    total_requests: number;
    cache_hit_rate: number;
    error_rate: number;
    average_response_time: number;
  };
  configuration: {
    max_tokens: number;
    temperature: number;
    timeout: number;
    caching_enabled: boolean;
  };
  status: string;
  compatibility?: {
    adk_compatible: boolean;
    legacy_interface: boolean;
    enhanced_features: boolean;
    sync_wrapper: boolean;
  };
}

// Health check response
export interface HealthStatus {
  status: string;
  timestamp: string;
  agent_info: AgentInfo;
  ai_status: {
    available: boolean;
    total_requests?: number;
    cache_hit_rate?: number;
    error_rate?: number;
    average_response_time?: number;
  };
}

// Performance metrics
export interface AIProviderMetrics {
  total_requests: number;
  cache_hits: number;
  cache_misses: number;
  errors: number;
  average_response_time: number;
  error_rate: number;
  cache_hit_rate: number;
  total_prompt_tokens: number;
  total_completion_tokens: number;
  total_tokens: number;
  rate_limit_hits: number;
  rate_limit_remaining: number;
}

// Cache management
export interface CacheStatus {
  cache_cleared: boolean;
}

// Error types for better error handling
export interface DashboardApiError {
  success: false;
  data: null;
  message: string;
  timestamp: string;
}

// Union type for all possible responses
export type DashboardApiResponse<T> = StandardResponse<T> | DashboardApiError;

// Utility types for component props
export interface DashboardComponentProps {
  companyName: string;
  data: DashboardData;
  timePeriod?: string;
  focusAreas?: string[];
  onDataUpdate?: (data: any) => void;
  onError?: (error: string) => void;
}

export interface DashboardState {
  loading: boolean;
  data: BulkDashboardData | null;
  error: string | null;
  lastUpdated: string | null;
}

// Hook return types
export interface UseDashboardDataResult {
  data: BulkDashboardData | null;
  loading: boolean;
  error: string | null;
  refetch: () => Promise<void>;
  summary: DashboardSummary | null;
  kpiAnalysis: KPIAnalysis | null;
  alertsAnalysis: AlertAnalysis | null;
  clearCache: () => void;
}

export interface UseCustomInsightResult {
  insight: CustomInsight | null;
  loading: boolean;
  error: string | null;
  generateInsight: (data: Record<string, any>, prompt: string, context?: string) => Promise<void>;
  reset: () => void;
}

export interface UseAgentInfoResult {
  agentInfo: AgentInfo | null;
  loading: boolean;
  error: string | null;
  refresh: () => Promise<void>;
}

// Configuration types
export interface DashboardConfig {
  apiBaseUrl?: string;
  autoRefresh?: boolean;
  refreshInterval?: number;
  enableCache?: boolean;
  enableAI?: boolean;
  fallbackMode?: boolean;
} 