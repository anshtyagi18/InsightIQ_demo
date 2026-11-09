/**
 * Types related to Metrics API
 */

export interface Metric {
  id: string;
  name: string;
  value: number | string;
  unit?: string;
  timestamp: string;
  trend?: 'up' | 'down' | 'stable';
  description?: string;
}

export interface TimeSeriesDataPoint {
  timestamp: string;
  value: number;
}

export interface TimeSeriesMetric extends Metric {
  data: TimeSeriesDataPoint[];
}

export interface KPIData {
  title: string;
  value: string;
  change: string;
  changeType: 'positive' | 'negative' | 'neutral';
  description?: string;
}

export interface DashboardMetrics {
  kpis: KPIData[];
  charts: {
    [chartName: string]: TimeSeriesMetric;
  };
}