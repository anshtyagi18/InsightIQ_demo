/**
 * Question-Driven Analysis & Chart Generation Service.
 * 
 * Interacts with /api/v1/analytics/question to execute Python-calculated
 * aggregations and AI interpretations.
 */

export interface QuestionChartItem {
  id: string;
  chart_type: 'bar' | 'line' | 'area' | 'pie' | 'scatter';
  title: string;
  subtitle?: string;
  x_key: string;
  y_keys: string[];
  x_label: string;
  y_label: string;
  legend?: string[];
  highlight_item?: {
    key: string;
    value: string;
    label: string;
  };
  data: Record<string, any>[];
  recharts_config: Record<string, any>;
  data_columns: string[];
}

export interface QuestionAnalysisResponse {
  status: string;
  question: string;
  intent: {
    metric?: string;
    dimension?: string;
    has_temporal: boolean;
    has_year: boolean;
    has_month: boolean;
    sub_questions: string[];
  };
  direct_answer: string;
  key_metrics: Array<{
    label: string;
    value: string;
    formatted?: string;
    numeric?: number;
    badge?: string;
    is_primary?: boolean;
  }>;
  charts: QuestionChartItem[];
  calculations_summary: {
    total_rows_analyzed: number;
    metric_used?: string;
    columns_available: string[];
    timestamp: string;
  };
  ai_interpretation?: {
    summary: string;
    takeaways: string[];
    generated_at: string;
    model_used: string;
  };
}

export interface QuestionHistoryEntry {
  id: string;
  timestamp: string;
  question: string;
  result: QuestionAnalysisResponse;
}

class QuestionAnalysisService {
  /**
   * Submits a question and dataset to the backend.
   * Python performs core calculations and chart data preparation.
   * AI interprets the calculated findings.
   */
  async analyzeQuestion(
    data: Record<string, any>[],
    question: string,
    datasetName: string = 'Dataset'
  ): Promise<QuestionAnalysisResponse> {
    if (!data || data.length === 0) {
      throw new Error('No dataset records available for analysis.');
    }

    if (!question || !question.trim()) {
      throw new Error('Please enter a question to analyze.');
    }

    const response = await fetch('/api/v1/analytics/question', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        data,
        question: question.trim(),
        datasetName,
      }),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.error || `Server returned error ${response.status}`);
    }

    const json = await response.json();
    if (!json.success || !json.data) {
      throw new Error(json.error || 'Failed to analyze question');
    }

    return json.data as QuestionAnalysisResponse;
  }

  /**
   * Generates smart, dataset-aware suggestion questions based on detected column types.
   */
  generateSampleQuestions(data: Record<string, any>[]): string[] {
    if (!data || data.length === 0) {
      return [
        'Show sales by year and which month had the highest sales.',
        'What are the top categories by total revenue?',
        'Compare performance across regions',
      ];
    }

    const sample = data[0] || {};
    const cols = Object.keys(sample);

    const dateCol = cols.find(c => /date|time|created|period|order_date/i.test(c));
    const metricCol = cols.find(c => /sales|revenue|amount|profit|total/i.test(c)) ||
      cols.find(c => typeof sample[c] === 'number');
    const catCol = cols.find(c => /category|product|region|segment|channel|rep|country/i.test(c)) ||
      cols.find(c => typeof sample[c] === 'string' && !/date|id/i.test(c));

    const cleanMetric = metricCol ? metricCol.replace(/_/g, ' ') : 'sales';
    const cleanCat = catCol ? catCol.replace(/_/g, ' ') : 'category';

    const suggestions: string[] = [];

    if (dateCol) {
      suggestions.push(`Show ${cleanMetric} by year and which month had the highest ${cleanMetric}.`);
      suggestions.push(`Monthly ${cleanMetric} trend and peak periods`);
    } else {
      suggestions.push(`Show total ${cleanMetric} and breakdown`);
    }

    if (catCol) {
      suggestions.push(`Which ${cleanCat} generated the highest ${cleanMetric}?`);
      suggestions.push(`Compare ${cleanMetric} across ${cleanCat}s`);
    }

    // Secondary metric if available (e.g. Profit vs Revenue)
    const secondMetric = cols.find(c => c !== metricCol && /profit|margin|cost|fee|discount/i.test(c));
    if (secondMetric) {
      const cleanSecond = secondMetric.replace(/_/g, ' ');
      suggestions.push(`Compare ${cleanMetric} versus ${cleanSecond}`);
    }

    return suggestions.slice(0, 4);
  }
}

export const questionAnalysisService = new QuestionAnalysisService();
