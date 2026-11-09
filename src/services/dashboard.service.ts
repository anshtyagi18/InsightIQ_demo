/**
 * Dashboard Service for InsightIQ
 * Handles dashboard generation, chart recommendations, KPI calculations, and layouts
 * Connects to /api/v1/dashboard/* endpoints
 */

import { api } from './api';
import { WorkflowResult } from './enhanced-dashboard.service';
import { 
  parseDatasetFile, 
  profileDataset, 
  cleanDataset, 
  generateBIDashboard 
} from './bi-engine';

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

export interface DashboardConfig {
  dashboard_id: string;
  layout: Record<string, any>;
  charts: ChartConfig[];
  kpis: KPIConfig[];
  metadata: Record<string, any>;
  generated_at: string;
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

interface ColumnClassification {
  column_name: string;
  column_type: 'numeric' | 'categorical' | 'date' | 'other';
  business_context: string;
  is_key_metric: boolean;
  sample_values: string[];
  null_count: number;
  unique_count: number;
  recommended: boolean;
}

interface FileAnalysisResponse {
  file_metadata: {
    filename: string;
    total_rows: number;
    total_columns: number;
    sheet_name: string;
    file_size_mb: number;
  };
  column_classifications: ColumnClassification[];
  summary: {
    total_analyzable_columns: number;
    key_metrics_count: number;
    recommended_count: number;
    numeric_columns: number;
    categorical_columns: number;
    date_columns: number;
  };
}

interface MetricSelectionDashboardRequest {
  file: File;
  selectedMetrics: string[];
  chartPreferences?: Record<string, any>;
  kpiRequirements?: string[];
  layoutType?: string;
  theme?: string;
}

interface MetricPairsDashboardRequest {
  file: File;
  metricPairs: Array<{
    id: string;
    xAxis: any;
    yAxis: any;
    chartType: string;
    name?: string;
  }>;
  layoutType?: string;
  theme?: string;
}

class DashboardService {
  private readonly STORAGE_KEY = 'dashboard_results';

  /**
   * Check if the AI-powered backend is available
   */
  async checkAIBackendHealth(): Promise<{
    isAvailable: boolean;
    aiServicesEnabled: boolean;
    message: string;
  }> {
    try {
      const response = await api.get('/api/v1/dashboard/health');
      return {
        isAvailable: true,
        aiServicesEnabled: response.ai_enabled || false,
        message: response.message || 'Backend connected',
      };
    } catch (error) {
      console.warn('⚠️ AI backend health check failed:', error);
      return {
        isAvailable: false,
        aiServicesEnabled: false,
        message: 'Backend unavailable - using fallback mode',
      };
    }
  }

  /**
   * Save dashboard result to localStorage for analytics
   */
  private saveDashboardResult(config: DashboardConfig, processingTime: number = 0, fileName?: string, fileSize?: number): void {
    try {
      const existingResults = this.getDashboardResults();
      
      const workflowResult: WorkflowResult = {
        workflow_id: config.dashboard_id || `dashboard_${Date.now()}`,
        dashboard_config: config,
        metadata: config.metadata || {},
        quality_metrics: {
          charts_generated: config.charts?.length || 0,
          kpis_generated: config.kpis?.length || 0,
          confidence_score: this.calculateConfidenceScore(config)
        },
        processing_time: processingTime,
        completed_at: config.generated_at || new Date().toISOString()
      };

      const updatedResults = [...existingResults, workflowResult];
      
      // Keep only the last 50 results to prevent localStorage bloat
      if (updatedResults.length > 50) {
        updatedResults.splice(0, updatedResults.length - 50);
      }
      
      localStorage.setItem(this.STORAGE_KEY, JSON.stringify(updatedResults));
      console.log('✅ Dashboard result saved to localStorage for analytics');

      // Track the generation event in real-time analytics
      this.trackGenerationEvent({
        dashboard_id: config.dashboard_id || `dashboard_${Date.now()}`,
        file_name: fileName || 'Unknown File',
        file_size: fileSize || 0,
        processing_time: processingTime,
        charts_generated: config.charts?.length || 0,
        kpis_generated: config.kpis?.length || 0,
        success: true
      });
      
    } catch (error) {
      console.error('Failed to save dashboard result:', error);
      
      // Track failed generation
      this.trackGenerationEvent({
        dashboard_id: `failed_${Date.now()}`,
        file_name: fileName || 'Unknown File',
        file_size: fileSize || 0,
        processing_time: processingTime,
        charts_generated: 0,
        kpis_generated: 0,
        success: false,
        error_message: error instanceof Error ? error.message : 'Unknown error'
      });
    }
  }

  /**
   * Track dashboard generation event for real-time analytics
   */
  private trackGenerationEvent(event: {
    dashboard_id: string;
    file_name: string;
    file_size: number;
    processing_time: number;
    charts_generated: number;
    kpis_generated: number;
    success: boolean;
    error_message?: string;
  }): void {
    try {
      // Dynamically import analytics service to avoid circular dependencies
      import('./analytics.service').then(({ analyticsService }) => {
        analyticsService.trackDashboardGeneration(event);
      });
    } catch (error) {
      console.error('Failed to track generation event:', error);
    }
  }

  /**
   * Get all dashboard results from localStorage
   */
  private getDashboardResults(): WorkflowResult[] {
    try {
      const saved = localStorage.getItem(this.STORAGE_KEY);
      return saved ? JSON.parse(saved) : [];
    } catch (error) {
      console.error('Failed to load dashboard results:', error);
      return [];
    }
  }

  /**
   * Calculate confidence score based on charts and KPIs generated
   */
  private calculateConfidenceScore(config: DashboardConfig): number {
    const chartsScore = Math.min((config.charts?.length || 0) * 0.2, 0.6);
    const kpisScore = Math.min((config.kpis?.length || 0) * 0.1, 0.4);
    return Math.min(chartsScore + kpisScore, 1.0);
  }

  /**
   * Generate a complete dashboard from uploaded file
   */
  async generateDashboardFromFile(request: DashboardGenerationRequest): Promise<DashboardConfig> {
    const startTime = Date.now();
    
    try {
      console.log('🧠 Attempting backend dashboard generation for file:', request.file.name);
      
      const formData = new FormData();
      formData.append('file', request.file);
      
      if (request.chartPreferences) {
        formData.append('chart_preferences', JSON.stringify(request.chartPreferences));
      }
      
      if (request.kpiRequirements) {
        formData.append('kpi_requirements', JSON.stringify(request.kpiRequirements));
      }
      
      if (request.layoutType) {
        formData.append('layout_type', request.layoutType);
      }
      
      if (request.theme) {
        formData.append('theme', request.theme);
      }

      const response = await api.postDashboard<DashboardConfig>(
        '/api/v1/dashboard/generate',
        formData,
        {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
          timeout: 10000,
        }
      );
      
      console.log('✅ Backend dashboard generation successful:', response);
      
      const processingTime = (Date.now() - startTime) / 1000;
      this.saveDashboardResult(response, processingTime, request.file.name, request.file.size);
      
      return response;
    } catch (error) {
      console.warn('⚠️ Backend endpoint failed or offline. Running client-side BI Engine:', error);
      const parsed = await parseDatasetFile(request.file);
      const cleaned = cleanDataset(parsed.data);
      const biDashboard = generateBIDashboard(cleaned.cleanedData, request.file.name);
      
      const processingTime = (Date.now() - startTime) / 1000;
      this.saveDashboardResult(biDashboard as any, processingTime, request.file.name, request.file.size);
      
      return biDashboard as any;
    }
  }

  /**
   * Generate a dashboard from an already uploaded file using AI analysis
   */
  async generateDashboardFromUpload(filePath: string, sessionId?: string, options?: {
    chartPreferences?: Record<string, any>;
    kpiRequirements?: string[];
    layoutType?: string;
    theme?: string;
  }): Promise<DashboardConfig> {
    const startTime = Date.now();
    
    try {
      console.log('🚀 Starting AI dashboard generation from uploaded file:', filePath);
      
      const request = {
        file_path: filePath,
        session_id: sessionId,
        chart_preferences: options?.chartPreferences,
        kpi_requirements: options?.kpiRequirements,
        layout_type: options?.layoutType || 'responsive',
        theme: options?.theme || 'default'
      };

      // Use the AI-powered generation endpoint that includes:
      // - Intelligent column analysis and detection
      // - Business context recognition (revenue, categories, locations, etc.)
      // - Automatic pivot table creation where beneficial
      // - Smart chart type selection based on data patterns
      // - AI-generated KPIs based on detected business metrics
      const response = await api.postDashboard<DashboardConfig>(
        '/api/v1/dashboard/generate-from-upload',
        request,
        {
          timeout: 120000, // 2 minutes timeout for AI processing
        }
      );
      
      console.log('✅ AI dashboard generation from upload completed:', response);
      
      // Calculate processing time and save result
      const processingTime = (Date.now() - startTime) / 1000;
      this.saveDashboardResult(response, processingTime, filePath, 0);
      
      return response;
    } catch (error) {
      console.error('❌ AI dashboard generation from upload failed:', error);
      throw new Error(`Failed to generate dashboard from uploaded file: ${error instanceof Error ? error.message : 'Unknown error'}`);
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
   * Generate interactive features for dashboard
   */
  async generateInteractiveFeatures(data: Record<string, any>, chartsConfig?: Record<string, any>, userPreferences?: Record<string, any>) {
    try {
      const response = await api.post(
        '/api/v1/dashboard/interactive-features',
        {
          data,
          charts_config: chartsConfig,
          user_preferences: userPreferences
        }
      );
      
      return response;
    } catch (error) {
      console.error('Interactive features generation failed:', error);
      throw new Error(`Failed to generate interactive features: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  /**
   * Get bulk dashboard data
   */
  async getBulkDashboardData(request: Record<string, any>) {
    try {
      const response = await api.post(
        '/api/v1/dashboard/bulk-data',
        request
      );
      
      return response;
    } catch (error) {
      console.error('Bulk dashboard data retrieval failed:', error);
      throw new Error(`Failed to get bulk dashboard data: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  /**
   * Analyze file structure for Smart Metric Selector
   */
  async analyzeFileStructure(file: File): Promise<FileAnalysisResponse> {
    const startTime = Date.now();
    
    try {
      console.log('🔍 Analyzing file structure for metric selection:', file.name);
      
      const formData = new FormData();
      formData.append('file', file);

      const response = await api.postDashboard<FileAnalysisResponse>(
        '/api/v1/dashboard/analyze-file',
        formData,
        {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
          timeout: 10000,
        }
      );
      
      console.log('✅ File analysis completed:', response);
      return response;
    } catch (error) {
      console.warn('⚠️ Backend analysis endpoint offline. Profiling dataset locally:', error);
      const parsed = await parseDatasetFile(file);
      const prof = profileDataset(parsed.data);

      const columnClassifications: ColumnClassification[] = prof.columns.map(c => ({
        column_name: c.name,
        column_type: c.type === 'id' ? 'categorical' : c.type,
        business_context: `${c.type.toUpperCase()} Field`,
        business_context_display: `${c.type.toUpperCase()} (${c.uniqueCount} unique values)`,
        is_key_metric: c.type === 'numeric' && (c.name === prof.primaryMetric || c.name === prof.secondaryMetric),
        sample_values: c.sampleValues.map(v => String(v)),
        null_count: c.nullCount,
        unique_count: c.uniqueCount,
        recommended: c.name === prof.primaryMetric || c.name === prof.primaryDimension || c.name === prof.primaryDate,
        data_quality: c.quality === 'good' ? 'good' : 'issues',
      }));

      return {
        file_metadata: {
          filename: file.name,
          total_rows: prof.rowCount,
          total_columns: prof.columnCount,
          sheet_name: parsed.sheetNames?.[0] || 'Sheet1',
          file_size_mb: Number((file.size / (1024 * 1024)).toFixed(2)),
        },
        column_classifications: columnClassifications,
        summary: {
          total_analyzable_columns: prof.columnCount,
          key_metrics_count: prof.numericColumns.length,
          recommended_count: columnClassifications.filter(c => c.recommended).length,
          numeric_columns: prof.numericColumns.length,
          categorical_columns: prof.categoricalColumns.length,
          date_columns: prof.dateColumns.length,
        }
      };
    }
  }

  /**
   * Generate dashboard with selected metrics only
   */
  async generateDashboardWithSelectedMetrics(request: MetricSelectionDashboardRequest): Promise<DashboardConfig> {
    const startTime = Date.now();
    
    try {
      console.log('🎯 Generating dashboard with selected metrics:', request.selectedMetrics);
      
      const formData = new FormData();
      formData.append('file', request.file);
      formData.append('selected_metrics', JSON.stringify(request.selectedMetrics));
      
      if (request.chartPreferences) {
        formData.append('chart_preferences', JSON.stringify(request.chartPreferences));
      }
      
      if (request.kpiRequirements) {
        formData.append('kpi_requirements', JSON.stringify(request.kpiRequirements));
      }
      
      if (request.layoutType) {
        formData.append('layout_type', request.layoutType);
      }
      
      if (request.theme) {
        formData.append('theme', request.theme);
      }

      const response = await api.postDashboard<DashboardConfig>(
        '/api/v1/dashboard/generate-with-metrics',
        formData,
        {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
          timeout: 10000,
        }
      );
      
      const processingTime = (Date.now() - startTime) / 1000;
      this.saveDashboardResult(response, processingTime, request.file.name, request.file.size);
      return response;
    } catch (error) {
      console.warn('⚠️ Backend endpoint offline. Generating local dashboard with selected metrics:', error);
      const parsed = await parseDatasetFile(request.file);
      const cleaned = cleanDataset(parsed.data);
      const biDashboard = generateBIDashboard(cleaned.cleanedData, request.file.name);
      
      const processingTime = (Date.now() - startTime) / 1000;
      this.saveDashboardResult(biDashboard as any, processingTime, request.file.name, request.file.size);
      return biDashboard as any;
    }
  }

  /**
   * Generate dashboard with metric pairs (X/Y axis relationships)
   */
  async generateDashboardWithMetricPairs(request: MetricPairsDashboardRequest): Promise<DashboardConfig> {
    const startTime = Date.now();
    
    try {
      console.log('🎯 Generating dashboard with metric pairs:', request.metricPairs);
      
      const formData = new FormData();
      formData.append('file', request.file);
      formData.append('metric_pairs', JSON.stringify(request.metricPairs));
      
      if (request.layoutType) {
        formData.append('layout_type', request.layoutType);
      }
      
      if (request.theme) {
        formData.append('theme', request.theme);
      }

      const response = await api.postDashboard<DashboardConfig>(
        '/api/v1/dashboard/generate-with-pairs',
        formData,
        {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
          timeout: 10000,
        }
      );
      
      const processingTime = (Date.now() - startTime) / 1000;
      this.saveDashboardResult(response, processingTime, request.file.name, request.file.size);
      return response;
    } catch (error) {
      console.warn('⚠️ Backend endpoint offline. Generating local dashboard with metric pairs:', error);
      const parsed = await parseDatasetFile(request.file);
      const cleaned = cleanDataset(parsed.data);
      const biDashboard = generateBIDashboard(cleaned.cleanedData, request.file.name);
      
      const processingTime = (Date.now() - startTime) / 1000;
      this.saveDashboardResult(biDashboard as any, processingTime, request.file.name, request.file.size);
      return biDashboard as any;
    }
  }
}

// Export singleton instance
export const dashboardService = new DashboardService();
export default dashboardService; 