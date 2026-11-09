/**
 * Service for fetching insights data from the API.
 */
import { api } from './api';
import { Insight, InsightsResponse, InsightFilterOptions } from '../types/insights';
import { PaginatedResponse, SuccessResponse } from '../types/api';

export interface GetInsightsParams {
  page?: number;
  pageSize?: number;
  sortBy?: string;
  sortOrder?: 'asc' | 'desc';
  filters?: InsightFilterOptions;
}

class InsightsService {
  /**
   * Fetches a list of insights.
   * @param params - Optional query parameters for pagination, sorting, and filtering.
   * @returns A promise that resolves to a paginated list of insights.
   */
  async getInsights(params?: GetInsightsParams): Promise<InsightsResponse> {
    try {
      const response = await api.get<InsightsResponse>('/insights', { params });
      return response;
    } catch (error) {
      console.error('Failed to fetch insights:', error);
      throw new Error('Failed to fetch insights');
    }
  }

  /**
   * Fetches a specific insight by its ID.
   * @param insightId - The ID of the insight to fetch.
   * @returns A promise that resolves to the insight data.
   */
  async getInsightById(insightId: string): Promise<Insight> {
    try {
      const response = await api.get<Insight>(`/insights/${insightId}`);
      return response;
    } catch (error) {
      console.error(`Failed to fetch insight ${insightId}:`, error);
      throw new Error(`Failed to fetch insight ${insightId}`);
    }
  }

  /**
   * Creates a new insight.
   * @param insightData - The data for the new insight.
   * @returns A promise that resolves to the created insight.
   */
  async createInsight(insightData: Partial<Insight>): Promise<Insight> {
    try {
      const response = await api.post<Insight>('/insights', insightData);
      return response;
    } catch (error) {
      console.error('Failed to create insight:', error);
      throw new Error('Failed to create insight');
    }
  }

  /**
   * Updates an existing insight.
   * @param insightId - The ID of the insight to update.
   * @param insightData - The data to update.
   * @returns A promise that resolves to the updated insight.
   */
  async updateInsight(insightId: string, insightData: Partial<Insight>): Promise<Insight> {
    try {
      const response = await api.put<Insight>(`/insights/${insightId}`, insightData);
      return response;
    } catch (error) {
      console.error(`Failed to update insight ${insightId}:`, error);
      throw new Error(`Failed to update insight ${insightId}`);
    }
  }

  /**
   * Deletes an insight.
   * @param insightId - The ID of the insight to delete.
   * @returns A promise that resolves to a success response.
   */
  async deleteInsight(insightId: string): Promise<SuccessResponse> {
    try {
      const response = await api.delete<SuccessResponse>(`/insights/${insightId}`);
      return response;
    } catch (error) {
      console.error(`Failed to delete insight ${insightId}:`, error);
      throw new Error(`Failed to delete insight ${insightId}`);
    }
  }

  /**
   * Fetches available filter options for insights.
   * @returns A promise that resolves to InsightFilterOptions.
   */
  async getInsightFilterOptions(): Promise<InsightFilterOptions> {
    try {
      const response = await api.get<InsightFilterOptions>('/insights/filters');
      return response;
    } catch (error) {
      console.error('Failed to fetch insight filter options:', error);
      throw new Error('Failed to fetch insight filter options');
    }
  }
}

export const insightsService = new InsightsService();
export default insightsService;