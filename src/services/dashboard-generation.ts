/**
 * @deprecated This file is deprecated as of Phase 2 frontend restructuring.
 * Use @/services/dashboard.service.ts instead for all dashboard functionality.
 * This file will be removed in a future version.
 * 
 * Migration Guide:
 * - Replace imports from './dashboard-generation' with './dashboard.service'
 * - Use dashboardService.generateDashboardFromFile() instead of generateDashboard()
 * - Use dashboardService.getChartRecommendations() for chart suggestions
 * - Use dashboardService.calculateKPIs() for KPI calculations
 */

/**
 * Dashboard Generation Service
 * Connects frontend to backend dashboard generation pipeline
 */

import { api } from './api';

// Types for dashboard generation
export interface DashboardGenerationRequest {
  file: File;
  chartPreferences?: Record<string, any>;
  kpiRequirements?: string[];
  layoutType?: string;
  theme?: string;
}

export interface ChartRecommendationRequest {
  data: Record<string, any>;
  context?: string;
  priorityMetrics?: string[];
}

export interface KPICalculationRequest {
  data: Record<string, any>;
  kpiDefinitions?: Array<Record<string, any>>;
}

export interface ChartConfig {
  chart_type: string;
  data_columns: string[];
  title: string;
  description: string;
  confidence: number;
  recharts_config: Record<string, any>;
  data?: Record<string, any>[];
}

export interface KPIConfig {
  name: string;
  value: number;
  unit: string;
  trend: 'up' | 'down' | 'neutral';
  trend_percentage: number;
  description: string;
  format_type: 'number' | 'currency' | 'percentage';
}

export interface DashboardConfig {
  dashboard_id: string;
  layout: Record<string, any>;
  charts: ChartConfig[];
  kpis: KPIConfig[];
  metadata: Record<string, any>;
  generated_at: string;
}

export interface LayoutTemplate {
  type: string;
  grid_columns: number;
  sections: Array<{
    id: string;
    title: string;
    position: {
      row: number;
      col: number;
      span: number;
    };
    component_type: string;
    max_items: number;
    actual_items?: number;
  }>;
}

export interface ThemeConfig {
  name: string;
  colors: {
    primary: string;
    secondary: string;
    accent: string;
    background: string;
    surface: string;
    text: string;
  };
  chart_palette: string[];
  typography: {
    font_family: string;
    heading_size: string;
    body_size: string;
  };
}

class DashboardGenerationService {
  /**
   * Generate a complete dashboard from an uploaded file
   */
  async generateDashboardFromFile(request: DashboardGenerationRequest): Promise<DashboardConfig> {
    const formData = new FormData();
    formData.append('file', request.file);
    
    if (request.chartPreferences) {
      formData.append('chart_preferences', JSON.stringify(request.chartPreferences));
    }
    
    if (request.kpiRequirements) {
      formData.append('kpi_requirements', JSON.stringify(request.kpiRequirements));
    }
    
    formData.append('layout_type', request.layoutType || 'responsive');
    formData.append('theme', request.theme || 'default');

    try {
      const response = await api.postDashboard<DashboardConfig>(
        '/api/v1/dashboard/generate',
        formData,
        {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        }
      );
      
      return response;
    } catch (error) {
      console.error('Dashboard generation failed:', error);
      throw new Error(`Failed to generate dashboard: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  /**
   * Unified Python+Gemini chart pipeline
   */
  async getChartRecommendations(request: ChartRecommendationRequest): Promise<ChartConfig[]> {
    try {
      const rows = Array.isArray(request.data) ? request.data : (request.data?.rows || []);
      const response = await fetch('/api/v1/charts/unified', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          data: rows,
          dataset_name: request.context || 'Dataset',
        }),
      });
      if (response.ok) {
        const json = await response.json();
        if (json && Array.isArray(json.charts)) {
          return json.charts;
        }
      }
      return [];
    } catch (error) {
      console.error('Unified chart pipeline failed:', error);
      return [];
    }
  }

  /**
   * Calculate KPIs from data
   */
  async calculateKPIs(request: KPICalculationRequest): Promise<KPIConfig[]> {
    try {
      const response = await api.post<{ status: string; kpis: KPIConfig[] }>(
        '/api/v1/dashboard/calculate-kpis',
        request
      );
      
      return response.kpis;
    } catch (error) {
      console.error('KPI calculation failed:', error);
      throw new Error(`Failed to calculate KPIs: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  /**
   * Get layout template by type
   */
  async getLayoutTemplate(layoutType: string): Promise<LayoutTemplate> {
    try {
      const response = await api.get<{ status: string; layout: LayoutTemplate }>(
        `/api/v1/dashboard/layouts/${layoutType}`
      );
      
      return response.layout;
    } catch (error) {
      console.error('Layout template retrieval failed:', error);
      throw new Error(`Failed to get layout template: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  /**
   * Get theme configuration by name
   */
  async getThemeConfig(themeName: string): Promise<ThemeConfig> {
    try {
      const response = await api.get<{ status: string; theme: ThemeConfig }>(
        `/api/v1/dashboard/themes/${themeName}`
      );
      
      return response.theme;
    } catch (error) {
      console.error('Theme configuration retrieval failed:', error);
      throw new Error(`Failed to get theme configuration: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  /**
   * Utility method to format KPI values based on their type
   */
  formatKPIValue(kpi: KPIConfig): string {
    const { value, format_type, unit } = kpi;
    
    switch (format_type) {
      case 'currency':
        return new Intl.NumberFormat('en-US', {
          style: 'currency',
          currency: 'USD',
        }).format(value);
      
      case 'percentage':
        return `${value.toFixed(1)}%`;
      
      case 'number':
      default:
        const formatted = new Intl.NumberFormat('en-US').format(value);
        return unit ? `${formatted} ${unit}` : formatted;
    }
  }

  /**
   * Get trend icon/indicator for KPI
   */
  getTrendIndicator(kpi: KPIConfig): { icon: string; color: string; text: string } {
    const { trend, trend_percentage } = kpi;
    
    switch (trend) {
      case 'up':
        return {
          icon: '↗️',
          color: 'text-green-500',
          text: `+${trend_percentage.toFixed(1)}%`
        };
      
      case 'down':
        return {
          icon: '↘️',
          color: 'text-red-500',
          text: `-${trend_percentage.toFixed(1)}%`
        };
      
      case 'neutral':
      default:
        return {
          icon: '→',
          color: 'text-gray-500',
          text: 'No change'
        };
    }
  }

  /**
   * Convert backend chart config to Recharts component props
   */
  convertToRechartsProps(chartConfig: ChartConfig, data: any[]): Record<string, any> {
    const { recharts_config, data_columns } = chartConfig;
    
    // Base props from backend config
    const props = {
      data,
      width: recharts_config.width || '100%',
      height: recharts_config.height || 300,
      margin: recharts_config.margin || { top: 5, right: 30, left: 20, bottom: 5 },
    };

    // Add specific props based on chart type
    if (recharts_config.dataKey) {
      props.dataKey = recharts_config.dataKey;
    }

    if (recharts_config.xAxisKey) {
      props.xAxisDataKey = recharts_config.xAxisKey;
    }

    return props;
  }
}

// Export singleton instance
export const dashboardGenerationService = new DashboardGenerationService();
export default dashboardGenerationService; 