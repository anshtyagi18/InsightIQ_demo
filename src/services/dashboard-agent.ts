/**
 * Dashboard Agent Service
 * 
 * Service for integrating with the Dashboard Agent API backend
 */

import { api } from './api';
import {
  DashboardSummaryRequest,
  KPIAnalysisRequest,
  AlertsRequest,
  CustomInsightRequest,
  DashboardSummary,
  KPIAnalysis,
  AlertAnalysis,
  CustomInsight,
  BulkDashboardData,
  AgentInfo,
  HealthStatus,
  AIProviderMetrics,
  CacheStatus,
  StandardResponse,
  DashboardData,
  Alert
} from '../types/dashboard';

class DashboardAgentService {
  private readonly baseUrl = '/api/v1/dashboard';

  /**
   * Check the health status of the Dashboard Agent API
   */
  async checkHealth(): Promise<HealthStatus> {
    try {
      const response = await api.get<HealthStatus>('/health');
      return response;
    } catch (error) {
      console.error('Failed to check Dashboard Agent health:', error);
      throw new Error('Dashboard Agent health check failed');
    }
  }

  /**
   * Generate an AI-powered dashboard summary
   */
  async generateSummary(request: DashboardSummaryRequest): Promise<DashboardSummary> {
    try {
      const response = await api.postDashboard<StandardResponse<DashboardSummary>>(
        `${this.baseUrl}/summary`,
        request
      );
      
      if (!response.success) {
        throw new Error(response.message || 'Failed to generate summary');
      }
      
      return response.data;
    } catch (error) {
      console.error('Failed to generate dashboard summary:', error);
      throw new Error('Failed to generate dashboard summary');
    }
  }

  /**
   * Analyze KPIs with AI insights
   */
  async analyzeKPIs(request: KPIAnalysisRequest): Promise<KPIAnalysis> {
    try {
      const response = await api.postDashboard<StandardResponse<KPIAnalysis>>(
        `${this.baseUrl}/kpis/analyze`,
        request
      );
      
      if (!response.success) {
        throw new Error(response.message || 'Failed to analyze KPIs');
      }
      
      return response.data;
    } catch (error) {
      console.error('Failed to analyze KPIs:', error);
      throw new Error('Failed to analyze KPIs');
    }
  }

  /**
   * Process and analyze alerts with AI prioritization
   */
  async processAlerts(request: AlertsRequest): Promise<AlertAnalysis> {
    try {
      const response = await api.postDashboard<StandardResponse<AlertAnalysis>>(
        `${this.baseUrl}/alerts`,
        request
      );
      
      if (!response.success) {
        throw new Error(response.message || 'Failed to process alerts');
      }
      
      return response.data;
    } catch (error) {
      console.error('Failed to process alerts:', error);
      throw new Error('Failed to process alerts');
    }
  }

  /**
   * Generate custom insights using AI
   */
  async generateCustomInsight(request: CustomInsightRequest): Promise<CustomInsight> {
    try {
      const response = await api.postDashboard<StandardResponse<CustomInsight>>(
        `${this.baseUrl}/insights/custom`,
        request
      );
      
      if (!response.success) {
        throw new Error(response.message || 'Failed to generate custom insight');
      }
      
      return response.data;
    } catch (error) {
      console.error('Failed to generate custom insight:', error);
      throw new Error('Failed to generate custom insight');
    }
  }

  /**
   * Get comprehensive dashboard data in one request
   */
  async getBulkDashboardData(request: DashboardSummaryRequest): Promise<BulkDashboardData> {
    try {
      const response = await api.postDashboard<StandardResponse<BulkDashboardData>>(
        `${this.baseUrl}/bulk-data`,
        request
      );
      
      if (!response.success) {
        throw new Error(response.message || 'Failed to get bulk dashboard data');
      }
      
      return response.data;
    } catch (error) {
      console.error('Failed to get bulk dashboard data:', error);
      throw new Error('Failed to get bulk dashboard data');
    }
  }

  /**
   * Get Dashboard Agent information and capabilities
   */
  async getAgentInfo(): Promise<AgentInfo> {
    try {
      const response = await api.get<StandardResponse<AgentInfo>>(
        `${this.baseUrl}/agent-info`
      );
      
      if (!response.success) {
        throw new Error(response.message || 'Failed to get agent info');
      }
      
      return response.data;
    } catch (error) {
      console.error('Failed to get agent info:', error);
      throw new Error('Failed to get agent info');
    }
  }

  /**
   * Get AI provider performance metrics
   */
  async getMetrics(): Promise<AIProviderMetrics> {
    try {
      const response = await api.get<StandardResponse<AIProviderMetrics>>(
        `${this.baseUrl}/metrics`
      );
      
      if (!response.success) {
        throw new Error(response.message || 'Failed to get metrics');
      }
      
      return response.data;
    } catch (error) {
      console.error('Failed to get metrics:', error);
      throw new Error('Failed to get metrics');
    }
  }

  /**
   * Clear the AI provider cache
   */
  async clearCache(): Promise<boolean> {
    try {
      const response = await api.post<StandardResponse<CacheStatus>>(
        `${this.baseUrl}/cache/clear`
      );
      
      if (!response.success) {
        throw new Error(response.message || 'Failed to clear cache');
      }
      
      return response.data.cache_cleared;
    } catch (error) {
      console.error('Failed to clear cache:', error);
      throw new Error('Failed to clear cache');
    }
  }

  // Convenience methods for common use cases

  /**
   * Generate a quick summary for a company with minimal configuration
   */
  async quickSummary(
    companyName: string,
    dashboardData: DashboardData,
    timePeriod: string = 'last_month'
  ): Promise<DashboardSummary> {
    return this.generateSummary({
      company_name: companyName,
      dashboard_data: dashboardData,
      time_period: timePeriod,
      use_ai: true
    });
  }

  /**
   * Get high-priority alerts analysis
   */
  async getHighPriorityAlerts(alerts: Alert[]): Promise<AlertAnalysis> {
    return this.processAlerts({
      alerts_data: alerts,
      priority_filter: 'high',
      use_ai: true
    });
  }

  /**
   * Analyze revenue KPIs specifically
   */
  async analyzeRevenue(revenueData: Record<string, any>): Promise<KPIAnalysis> {
    return this.analyzeKPIs({
      kpi_data: revenueData,
      analysis_type: 'revenue',
      use_ai: true
    });
  }

  /**
   * Get dashboard data with fallback to non-AI mode
   */
  async getDashboardDataWithFallback(
    companyName: string,
    dashboardData: DashboardData,
    timePeriod: string = 'last_month'
  ): Promise<BulkDashboardData> {
    try {
      // Try with AI first
      return await this.getBulkDashboardData({
        company_name: companyName,
        dashboard_data: dashboardData,
        time_period: timePeriod,
        use_ai: true
      });
    } catch (error) {
      console.warn('AI-powered dashboard failed, falling back to basic mode:', error);
      
      // Fallback to non-AI mode
      return await this.getBulkDashboardData({
        company_name: companyName,
        dashboard_data: dashboardData,
        time_period: timePeriod,
        use_ai: false
      });
    }
  }

  /**
   * Check if the Dashboard Agent is available and ready
   */
  async isAgentReady(): Promise<boolean> {
    try {
      const health = await this.checkHealth();
      return health.status === 'healthy';
    } catch (error) {
      return false;
    }
  }

  /**
   * Get agent status information for UI display
   */
  async getAgentStatus(): Promise<{
    available: boolean;
    aiEnabled: boolean;
    version?: string;
    error?: string;
  }> {
    try {
      const health = await this.checkHealth();
      const agentInfo = health.agent_info;
      
      return {
        available: true,
        aiEnabled: health.ai_status.available,
        version: agentInfo.version,
      };
    } catch (error) {
      return {
        available: false,
        aiEnabled: false,
        error: error instanceof Error ? error.message : 'Unknown error'
      };
    }
  }
}

// Export singleton instance
export const dashboardAgentService = new DashboardAgentService();
export default dashboardAgentService; 