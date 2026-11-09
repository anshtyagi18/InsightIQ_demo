/**
 * Service for fetching metrics data from the API.
 */
import { api } from './api';
import { DashboardMetrics, Metric, TimeSeriesMetric } from '../types/metrics';
import { PaginatedResponse } from '../types/api';

export interface GetMetricsParams {
  page?: number;
  pageSize?: number;
  type?: string;
  dateFrom?: string;
  dateTo?: string;
}

class MetricsService {
  /**
   * Fetches dashboard metrics.
   * @returns A promise that resolves to DashboardMetrics.
   */
  async getDashboardMetrics(): Promise<DashboardMetrics> {
    try {
      const response = await api.get<DashboardMetrics>('/metrics/dashboard');
      return response;
    } catch (error) {
      console.error('Failed to fetch dashboard metrics:', error);
      throw new Error('Failed to fetch dashboard metrics');
    }
  }

  /**
   * Fetches a list of all available metrics.
   * @param params - Optional query parameters for pagination and filtering.
   * @returns A promise that resolves to a paginated list of metrics.
   */
  async getAllMetrics(params?: GetMetricsParams): Promise<PaginatedResponse<Metric>> {
    try {
      const response = await api.get<PaginatedResponse<Metric>>('/metrics', { params });
      return response;
    } catch (error) {
      console.error('Failed to fetch all metrics:', error);
      throw new Error('Failed to fetch all metrics');
    }
  }

  /**
   * Fetches a specific metric by its ID.
   * @param metricId - The ID of the metric to fetch.
   * @returns A promise that resolves to the metric data.
   */
  async getMetricById(metricId: string): Promise<Metric | TimeSeriesMetric> {
    try {
      const response = await api.get<Metric | TimeSeriesMetric>(`/metrics/${metricId}`);
      return response;
    } catch (error) {
      console.error(`Failed to fetch metric ${metricId}:`, error);
      throw new Error(`Failed to fetch metric ${metricId}`);
    }
  }

  /**
   * Fetches time series data for a specific metric.
   * @param metricId - The ID of the metric.
   * @param dateFrom - Start date for the time series.
   * @param dateTo - End date for the time series.
   * @param granularity - The granularity of the data (e.g., 'hourly', 'daily').
   * @returns A promise that resolves to TimeSeriesMetric.
   */
  async getMetricTimeSeries(
    metricId: string,
    dateFrom: string,
    dateTo: string,
    granularity: string
  ): Promise<TimeSeriesMetric> {
    try {
      const response = await api.get<TimeSeriesMetric>(`/metrics/${metricId}/timeseries`, {
        params: { dateFrom, dateTo, granularity },
      });
      return response;
    } catch (error) {
      console.error(`Failed to fetch time series data for metric ${metricId}:`, error);
      throw new Error(`Failed to fetch time series data for metric ${metricId}`);
    }
  }
}

export const metricsService = new MetricsService();
export default metricsService;