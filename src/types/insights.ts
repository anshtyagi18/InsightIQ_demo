/**
 * Types related to Insights API
 */

export interface Insight {
  id: string;
  title: string;
  summary: string;
  details: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  category: string;
  timestamp: string;
  source: string; // e.g., "Pattern Analysis Agent"
  dataPoints?: Record<string, any>; // Related data points for context
  actions?: InsightAction[];
}

export interface InsightAction {
  id: string;
  label: string;
  type: 'link' | 'api_call' | 'modal';
  target?: string; // URL for link, API endpoint for api_call, modal ID for modal
  payload?: Record<string, any>; // Data for API call or modal
}

export interface InsightFilterOptions {
  severity?: ('low' | 'medium' | 'high' | 'critical')[];
  category?: string[];
  dateRange?: {
    startDate?: string;
    endDate?: string;
  };
  source?: string[];
}

export interface InsightsResponse {
  insights: Insight[];
  totalCount: number;
  filterOptions?: InsightFilterOptions; // For available filter values
}