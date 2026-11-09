import { WorkflowResult, WorkflowStatus } from '@/services';

export interface AnalyticsData {
  timestamp: string;
  value: number;
  category?: string;
  metadata?: Record<string, any>;
}

export interface FilterCriteria {
  dateRange?: {
    start: Date;
    end: Date;
  };
  categories?: string[];
  valueRange?: {
    min: number;
    max: number;
  };
  searchTerm?: string;
  status?: string[];
}

export interface ProcessedInsights {
  trends: {
    direction: 'up' | 'down' | 'stable';
    percentage: number;
    period: string;
  };
  statistics: {
    mean: number;
    median: number;
    standardDeviation: number;
    min: number;
    max: number;
    total: number;
    count: number;
  };
  distributions: {
    category: string;
    count: number;
    percentage: number;
  }[];
  timeSeriesData: {
    name: string;
    value: number;
    timestamp: string;
  }[];
}

// Generate mock analytics data for demonstration
export const generateMockAnalyticsData = (
  count: number = 30,
  categories: string[] = ['Revenue', 'Users', 'Performance', 'Conversion']
): AnalyticsData[] => {
  const data: AnalyticsData[] = [];
  const now = new Date();
  
  for (let i = 0; i < count; i++) {
    const date = new Date(now.getTime() - (count - i) * 24 * 60 * 60 * 1000);
    data.push({
      timestamp: date.toISOString(),
      value: Math.floor(Math.random() * 1000) + Math.sin(i * 0.3) * 100 + 500,
      category: categories[Math.floor(Math.random() * categories.length)],
      metadata: {
        source: ['web', 'mobile', 'api'][Math.floor(Math.random() * 3)],
        region: ['US', 'EU', 'ASIA'][Math.floor(Math.random() * 3)],
      }
    });
  }
  
  return data;
};

// Filter data based on criteria
export const filterAnalyticsData = (
  data: AnalyticsData[],
  criteria: FilterCriteria
): AnalyticsData[] => {
  return data.filter(item => {
    // Date range filter
    if (criteria.dateRange) {
      const itemDate = new Date(item.timestamp);
      if (itemDate < criteria.dateRange.start || itemDate > criteria.dateRange.end) {
        return false;
      }
    }
    
    // Category filter
    if (criteria.categories && criteria.categories.length > 0) {
      if (!item.category || !criteria.categories.includes(item.category)) {
        return false;
      }
    }
    
    // Value range filter
    if (criteria.valueRange) {
      if (item.value < criteria.valueRange.min || item.value > criteria.valueRange.max) {
        return false;
      }
    }
    
    // Search term filter
    if (criteria.searchTerm) {
      const searchLower = criteria.searchTerm.toLowerCase();
      const searchableText = [
        item.category,
        item.metadata?.source,
        item.metadata?.region,
        item.value.toString(),
      ].join(' ').toLowerCase();
      
      if (!searchableText.includes(searchLower)) {
        return false;
      }
    }
    
    return true;
  });
};

// Calculate statistics from data
export const calculateStatistics = (values: number[]) => {
  if (values.length === 0) {
    return {
      mean: 0,
      median: 0,
      standardDeviation: 0,
      min: 0,
      max: 0,
      total: 0,
      count: 0,
    };
  }
  
  const sorted = [...values].sort((a, b) => a - b);
  const total = values.reduce((sum, val) => sum + val, 0);
  const mean = total / values.length;
  
  const median = values.length % 2 === 0
    ? (sorted[values.length / 2 - 1] + sorted[values.length / 2]) / 2
    : sorted[Math.floor(values.length / 2)];
  
  const variance = values.reduce((sum, val) => sum + Math.pow(val - mean, 2), 0) / values.length;
  const standardDeviation = Math.sqrt(variance);
  
  return {
    mean: Number(mean.toFixed(2)),
    median: Number(median.toFixed(2)),
    standardDeviation: Number(standardDeviation.toFixed(2)),
    min: Math.min(...values),
    max: Math.max(...values),
    total: Number(total.toFixed(2)),
    count: values.length,
  };
};

// Calculate trend analysis
export const calculateTrend = (data: AnalyticsData[]): {
  direction: 'up' | 'down' | 'stable';
  percentage: number;
  period: string;
} => {
  if (data.length < 2) {
    return { direction: 'stable', percentage: 0, period: 'insufficient data' };
  }
  
  const sortedData = [...data].sort((a, b) => 
    new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime()
  );
  
  const firstHalf = sortedData.slice(0, Math.floor(sortedData.length / 2));
  const secondHalf = sortedData.slice(Math.floor(sortedData.length / 2));
  
  const firstHalfAvg = firstHalf.reduce((sum, item) => sum + item.value, 0) / firstHalf.length;
  const secondHalfAvg = secondHalf.reduce((sum, item) => sum + item.value, 0) / secondHalf.length;
  
  const percentageChange = ((secondHalfAvg - firstHalfAvg) / firstHalfAvg) * 100;
  
  let direction: 'up' | 'down' | 'stable' = 'stable';
  if (Math.abs(percentageChange) > 5) {
    direction = percentageChange > 0 ? 'up' : 'down';
  }
  
  const startDate = new Date(sortedData[0].timestamp);
  const endDate = new Date(sortedData[sortedData.length - 1].timestamp);
  const daysDiff = Math.ceil((endDate.getTime() - startDate.getTime()) / (1000 * 60 * 60 * 24));
  
  return {
    direction,
    percentage: Number(Math.abs(percentageChange).toFixed(1)),
    period: `${daysDiff} days`,
  };
};

// Generate category distribution
export const generateDistribution = (data: AnalyticsData[]): {
  category: string;
  count: number;
  percentage: number;
}[] => {
  const categoryCount = data.reduce((acc, item) => {
    const category = item.category || 'Unknown';
    acc[category] = (acc[category] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);
  
  const total = data.length;
  
  return Object.entries(categoryCount).map(([category, count]) => ({
    category,
    count,
    percentage: Number(((count / total) * 100).toFixed(1)),
  }));
};

// Process complete analytics insights
export const processAnalyticsInsights = (data: AnalyticsData[]): ProcessedInsights => {
  const values = data.map(item => item.value);
  const statistics = calculateStatistics(values);
  const trends = calculateTrend(data);
  const distributions = generateDistribution(data);
  
  const timeSeriesData = data
    .sort((a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime())
    .map(item => ({
      name: new Date(item.timestamp).toLocaleDateString(),
      value: item.value,
      timestamp: item.timestamp,
    }));
  
  return {
    trends,
    statistics,
    distributions,
    timeSeriesData,
  };
};

// Process workflow results for analytics
export const processWorkflowResults = (
  workflowResults: WorkflowResult[],
  activeWorkflows: Map<string, WorkflowStatus>
): {
  completionTimes: { name: string; value: number }[];
  statusDistribution: { name: string; value: number }[];
  timelineData: { name: string; completed: number; active: number; failed: number }[];
  performanceMetrics: {
    averageProcessingTime: number;
    successRate: number;
    totalCompleted: number;
    totalActive: number;
  };
} => {
  // Completion times chart data
  const completionTimes = workflowResults.map((result, index) => ({
    name: `WF ${index + 1}`,
    value: result.processing_time,
  }));
  
  // Status distribution
  const statusCounts = Array.from(activeWorkflows.values()).reduce((acc, workflow) => {
    acc[workflow.status] = (acc[workflow.status] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);
  
  statusCounts['completed'] = (statusCounts['completed'] || 0) + workflowResults.length;
  
  const statusDistribution = Object.entries(statusCounts).map(([status, count]) => ({
    name: status.charAt(0).toUpperCase() + status.slice(1),
    value: count,
  }));
  
  // Timeline data (simplified - group by day)
  const timelineData = generateTimelineData(workflowResults, activeWorkflows);
  
  // Performance metrics
  const totalCompleted = workflowResults.length;
  const totalActive = Array.from(activeWorkflows.values()).filter(w => w.status === 'running').length;
  const totalFailed = Array.from(activeWorkflows.values()).filter(w => w.status === 'failed').length;
  const averageProcessingTime = totalCompleted > 0 
    ? workflowResults.reduce((sum, r) => sum + r.processing_time, 0) / totalCompleted
    : 0;
  const successRate = totalCompleted + totalActive + totalFailed > 0
    ? (totalCompleted / (totalCompleted + totalFailed)) * 100
    : 100;
  
  return {
    completionTimes,
    statusDistribution,
    timelineData,
    performanceMetrics: {
      averageProcessingTime: Number(averageProcessingTime.toFixed(1)),
      successRate: Number(successRate.toFixed(1)),
      totalCompleted,
      totalActive,
    },
  };
};

// Helper function to generate timeline data
const generateTimelineData = (
  workflowResults: WorkflowResult[],
  activeWorkflows: Map<string, WorkflowStatus>
) => {
  const last7Days = Array.from({ length: 7 }, (_, i) => {
    const date = new Date();
    date.setDate(date.getDate() - (6 - i));
    return date.toISOString().split('T')[0];
  });
  
  return last7Days.map(date => {
    const completed = workflowResults.filter(r => 
      r.completed_at.startsWith(date)
    ).length;
    
    // For active/failed, we'll use current counts proportionally spread
    const active = Math.floor(Array.from(activeWorkflows.values()).filter(w => w.status === 'running').length / 7);
    const failed = Math.floor(Array.from(activeWorkflows.values()).filter(w => w.status === 'failed').length / 7);
    
    return {
      name: new Date(date).toLocaleDateString('en-US', { weekday: 'short' }),
      completed,
      active,
      failed,
    };
  });
};

// Export data to CSV format
export const exportToCSV = (data: AnalyticsData[], filename: string = 'analytics-data.csv') => {
  if (data.length === 0) return;
  
  const headers = ['timestamp', 'value', 'category', 'source', 'region'];
  const csvContent = [
    headers.join(','),
    ...data.map(item => [
      item.timestamp,
      item.value,
      item.category || '',
      item.metadata?.source || '',
      item.metadata?.region || '',
    ].join(','))
  ].join('\n');
  
  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
  const link = document.createElement('a');
  
  if (link.download !== undefined) {
    const url = URL.createObjectURL(blob);
    link.setAttribute('href', url);
    link.setAttribute('download', filename);
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  }
};

// Format numbers for display
export const formatNumber = (num: number, decimals: number = 0): string => {
  if (num >= 1000000) {
    return (num / 1000000).toFixed(decimals) + 'M';
  } else if (num >= 1000) {
    return (num / 1000).toFixed(decimals) + 'K';
  }
  return num.toFixed(decimals);
};

// Format percentage
export const formatPercentage = (num: number, decimals: number = 1): string => {
  return `${num.toFixed(decimals)}%`;
}; 