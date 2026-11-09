/**
 * Data Intelligence API Service for Insightia.
 * Connects frontend workspace with FastAPI Python backend engine.
 */

import axios from 'axios';

export interface ColumnStats {
  min?: number;
  max?: number;
  mean?: number;
  median?: number;
  std?: number;
  q25?: number;
  q75?: number;
  iqr?: number;
  skewness?: number;
  outliers_iqr?: number;
  outliers_zscore?: number;
  lower_bound?: number;
  upper_bound?: number;
}

export interface ValueFrequency {
  name: string;
  count: number;
  percentage: number;
}

export interface ColumnProfile {
  name: string;
  type: 'numeric' | 'categorical' | 'datetime' | 'boolean' | 'text';
  missing_count: number;
  missing_pct: number;
  unique_count: number;
  stats?: ColumnStats;
  top_values?: ValueFrequency[];
  outliers_count: number;
}

export interface CorrelationItem {
  col1: string;
  col2: string;
  correlation: number;
  strength: string;
}

export interface DataInsight {
  type: 'health' | 'anomaly' | 'trend' | 'distribution';
  level: 'success' | 'warning' | 'alert' | 'info';
  title: string;
  description: string;
}

export interface AuditLogEntry {
  timestamp: string;
  message: string;
  rows?: number;
  cols?: number;
}

export interface DatasetProfile {
  session_id: string;
  dataset_name: string;
  total_rows: number;
  total_cols: number;
  total_cells: number;
  missing_cells: number;
  missing_rate: number;
  duplicate_rows: number;
  duplicate_rate: number;
  outlier_count: number;
  health_score: number;
  columns: ColumnProfile[];
  correlations: Record<string, Record<string, number>>;
  strong_correlations: CorrelationItem[];
  insights: DataInsight[];
  preview: Record<string, any>[];
  audit_entry?: string;
  health_score_delta?: number;
  audit_log?: AuditLogEntry[];
}

export interface ChartPayload {
  chartType: 'bar' | 'line' | 'scatter' | 'pie' | 'histogram' | 'area';
  xAxis: string;
  yAxis: string;
  data: Record<string, any>[];
  title: string;
  insights?: string[];
}

export interface CopilotResponse {
  session_id: string;
  explanation: string;
  verified_figures: Record<string, any>;
  chart_payload: ChartPayload | null;
  executed_code: string;
  status: string;
  is_hinglish: boolean;
}

const API_BASE = '/api/data';

export const dataIntelligenceService = {
  /**
   * Ingest CSV, Excel (.xlsx, .xls) or JSON file
   */
  async uploadDataset(file: File): Promise<DatasetProfile> {
    const formData = new FormData();
    formData.append('file', file);

    const response = await axios.post<DatasetProfile>(`${API_BASE}/upload`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      timeout: 60000,
    });
    return response.data;
  },

  /**
   * Load curated 1-click sample business datasets
   */
  async loadSampleDataset(sampleId: 'ecommerce_sales' | 'customer_churn' | 'financial_kpi'): Promise<DatasetProfile> {
    const response = await axios.get<DatasetProfile>(`${API_BASE}/sample/${sampleId}`, {
      timeout: 30000,
    });
    return response.data;
  },

  /**
   * Execute deterministic cleaning operations
   */
  async cleanDataset(
    sessionId: string,
    action: 'impute' | 'drop_na' | 'remove_duplicates' | 'remove_outliers' | 'coerce_types' | 'auto_clean',
    params?: Record<string, any>
  ): Promise<DatasetProfile> {
    const response = await axios.post<DatasetProfile>(`${API_BASE}/clean`, {
      session_id: sessionId,
      action,
      params,
    }, {
      timeout: 45000,
    });
    return response.data;
  },

  /**
   * Send Multilingual or Hinglish query to Copilot
   */
  async chatCopilot(sessionId: string, query: string): Promise<CopilotResponse> {
    const response = await axios.post<CopilotResponse>(`${API_BASE}/chat`, {
      session_id: sessionId,
      query,
    }, {
      timeout: 60000,
    });
    return response.data;
  },

  /**
   * Download export file (CSV, Excel, JSON, Executive PDF)
   */
  getExportUrl(sessionId: string, format: 'csv' | 'xlsx' | 'json' | 'pdf'): string {
    return `${API_BASE}/export/${format}?session_id=${encodeURIComponent(sessionId)}`;
  },

  /**
   * Trigger direct browser download
   */
  triggerDownload(sessionId: string, format: 'csv' | 'xlsx' | 'json' | 'pdf', filename?: string) {
    const url = this.getExportUrl(sessionId, format);
    const link = document.createElement('a');
    link.href = url;
    if (filename) {
      link.download = filename;
    }
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  },
};

