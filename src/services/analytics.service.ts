/**
 * Analytics Service
 * Connects real uploaded dashboard data to the analytics page with real-time tracking
 */

import { WorkflowResult } from './enhanced-dashboard.service';

export interface AnalyticsMetrics {
  totalDashboards: number;
  avgProcessingTime: number;
  successRate: number;
  totalDataProcessed: number;
  totalFileSize: number;
  peakUsageHour: string;
}

export interface AnalyticsChartData {
  processingTimes: { name: string; value: number; timestamp: string }[];
  successRates: { name: string; value: number }[];
  dataDistribution: { name: string; value: number; color: string }[];
  performanceTrends: { date: string; processing_time: number; success_rate: number }[];
}

export interface AnalyticsInsight {
  id: string;
  type: 'performance' | 'usage' | 'optimization' | 'anomaly';
  title: string;
  description: string;
  impact: 'high' | 'medium' | 'low';
  actionRequired: boolean;
  timestamp: string;
}

export interface DashboardGenerationEvent {
  id: string;
  dashboard_id: string;
  file_name: string;
  file_size: number;
  processing_time: number;
  charts_generated: number;
  kpis_generated: number;
  success: boolean;
  error_message?: string;
  timestamp: string;
}

export class AnalyticsService {
  private static instance: AnalyticsService;
  private readonly storageKey = 'dashboard_analytics_data';
  private readonly eventsKey = 'dashboard_generation_events';

  private constructor() {}

  static getInstance(): AnalyticsService {
    if (!AnalyticsService.instance) {
      AnalyticsService.instance = new AnalyticsService();
    }
    return AnalyticsService.instance;
  }

  /**
   * Track a new dashboard generation event in real-time
   */
  trackDashboardGeneration(event: Omit<DashboardGenerationEvent, 'id' | 'timestamp'>): void {
    try {
      const fullEvent: DashboardGenerationEvent = {
        ...event,
        id: `event_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
        timestamp: new Date().toISOString()
      };

      const existingEvents = this.getDashboardGenerationEvents();
      const updatedEvents = [...existingEvents, fullEvent];

      // Keep only the last 100 events to prevent storage bloat
      if (updatedEvents.length > 100) {
        updatedEvents.splice(0, updatedEvents.length - 100);
      }

      localStorage.setItem(this.eventsKey, JSON.stringify(updatedEvents));
      
      console.log('📊 Dashboard generation event tracked:', fullEvent);
      
      // Also save to analytics data for backward compatibility
      this.trackEvent('dashboard_generated', {
        dashboard_id: event.dashboard_id,
        success: event.success,
        processing_time: event.processing_time,
        charts_count: event.charts_generated,
        kpis_count: event.kpis_generated
      });
      
    } catch (error) {
      console.error('Failed to track dashboard generation event:', error);
    }
  }

  /**
   * Get all dashboard generation events
   */
  getDashboardGenerationEvents(): DashboardGenerationEvent[] {
    try {
      const saved = localStorage.getItem(this.eventsKey);
      return saved ? JSON.parse(saved) : [];
    } catch (error) {
      console.error('Failed to load dashboard generation events:', error);
      return [];
    }
  }

  /**
   * Clear all tracking data
   */
  clearAllData(): void {
    try {
      localStorage.removeItem('dashboard_results');
      localStorage.removeItem(this.storageKey);
      localStorage.removeItem(this.eventsKey);
      console.log('✅ All analytics data cleared');
    } catch (error) {
      console.error('Failed to clear analytics data:', error);
    }
  }

  /**
   * Get all dashboard results from storage
   */
  private getDashboardResults(): WorkflowResult[] {
    try {
      const saved = localStorage.getItem('dashboard_results');
      return saved ? JSON.parse(saved) : [];
    } catch (error) {
      console.error('Failed to load dashboard results:', error);
      return [];
    }
  }

  /**
   * Add sample dashboard data for testing (if no real data exists)
   */
  addSampleDataIfEmpty(): void {
    const existing = this.getDashboardResults();
    if (existing.length > 0) {
      console.log('✅ Real dashboard data found, skipping sample data');
      return;
    }

    console.log('📝 Adding sample dashboard data for analytics testing');
    
    const sampleData: WorkflowResult[] = [
      {
        workflow_id: 'sample_dashboard_1',
        dashboard_config: {
          dashboard_id: 'sample_1',
          title: 'Sales Analytics Dashboard',
          charts: [
            { chart_type: 'bar', title: 'Monthly Sales' },
            { chart_type: 'line', title: 'Revenue Trend' },
            { chart_type: 'pie', title: 'Product Distribution' }
          ],
          kpis: [
            { name: 'Total Revenue', value: 125000 },
            { name: 'Orders', value: 450 }
          ]
        },
        metadata: { file_type: 'xlsx', file_size: 25600 },
        quality_metrics: { charts_generated: 3, kpis_generated: 2, confidence_score: 0.85 },
        processing_time: 12.5,
        completed_at: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000).toISOString() // 2 days ago
      },
      {
        workflow_id: 'sample_dashboard_2',
        dashboard_config: {
          dashboard_id: 'sample_2',
          title: 'Customer Insights Dashboard',
          charts: [
            { chart_type: 'line', title: 'Customer Growth' },
            { chart_type: 'bar', title: 'Demographics' }
          ],
          kpis: [
            { name: 'Active Users', value: 1250 },
            { name: 'Retention Rate', value: 78 }
          ]
        },
        metadata: { file_type: 'csv', file_size: 18400 },
        quality_metrics: { charts_generated: 2, kpis_generated: 2, confidence_score: 0.92 },
        processing_time: 8.3,
        completed_at: new Date(Date.now() - 1 * 24 * 60 * 60 * 1000).toISOString() // 1 day ago
      },
      {
        workflow_id: 'sample_dashboard_3',
        dashboard_config: {
          dashboard_id: 'sample_3',
          title: 'Financial Overview Dashboard',
          charts: [
            { chart_type: 'line', title: 'Cash Flow' },
            { chart_type: 'bar', title: 'Expenses' },
            { chart_type: 'pie', title: 'Budget Allocation' },
            { chart_type: 'area', title: 'Profit Margin' }
          ],
          kpis: [
            { name: 'Net Profit', value: 45000 },
            { name: 'Operating Margin', value: 23.5 },
            { name: 'ROI', value: 15.2 }
          ]
        },
        metadata: { file_type: 'xlsx', file_size: 42300 },
        quality_metrics: { charts_generated: 4, kpis_generated: 3, confidence_score: 0.88 },
        processing_time: 15.7,
        completed_at: new Date().toISOString() // Today
      }
    ];

    try {
      localStorage.setItem('dashboard_results', JSON.stringify(sampleData));
      console.log('✅ Sample dashboard data added successfully');
    } catch (error) {
      console.error('Failed to add sample data:', error);
    }
  }

  /**
   * Calculate comprehensive analytics metrics
   */
  calculateMetrics(): AnalyticsMetrics {
    const dashboards = this.getDashboardResults();
    
    if (dashboards.length === 0) {
      return {
        totalDashboards: 0,
        avgProcessingTime: 0,
        successRate: 0,
        totalDataProcessed: 0,
        totalFileSize: 0,
        peakUsageHour: '9:00 AM'
      };
    }

    const successfulDashboards = dashboards.filter(d => d.workflow_id && d.dashboard_config);
    const totalProcessingTime = dashboards.reduce((sum, d) => sum + (d.processing_time || 0), 0);
    
    return {
      totalDashboards: dashboards.length,
      avgProcessingTime: totalProcessingTime / dashboards.length,
      successRate: (successfulDashboards.length / dashboards.length) * 100,
      totalDataProcessed: this.estimateDataPoints(dashboards),
      totalFileSize: this.estimateTotalFileSize(dashboards),
      peakUsageHour: this.calculatePeakUsageHour(dashboards)
    };
  }

  /**
   * Generate chart data for visualization
   */
  generateChartData(): AnalyticsChartData {
    const dashboards = this.getDashboardResults();
    
    return {
      processingTimes: this.generateProcessingTimeData(dashboards),
      successRates: this.generateSuccessRateData(dashboards),
      dataDistribution: this.generateDataDistribution(dashboards),
      performanceTrends: this.generatePerformanceTrends(dashboards)
    };
  }

  /**
   * Generate AI-powered insights (simplified version returning strings)
   */
  generateInsights(metrics: AnalyticsMetrics): string[] {
    const insights: string[] = [];

    // Performance insights
    if (metrics.avgProcessingTime > 30) {
      insights.push(`Processing time averaging ${metrics.avgProcessingTime.toFixed(1)}s is above optimal range. Consider optimizing data preprocessing steps for better performance.`);
    } else if (metrics.avgProcessingTime < 10) {
      insights.push(`Excellent processing performance with ${metrics.avgProcessingTime.toFixed(1)}s average time. Your workflows are highly optimized.`);
    }

    // Success rate insights
    if (metrics.successRate < 90) {
      insights.push(`Success rate of ${metrics.successRate.toFixed(1)}% is below the 90% target. Review failed workflows for common error patterns and data quality issues.`);
    } else if (metrics.successRate > 95) {
      insights.push(`Outstanding success rate of ${metrics.successRate.toFixed(1)}% indicates robust and reliable dashboard generation workflows.`);
    }

    // Usage insights
    if (metrics.totalDashboards > 10) {
      insights.push(`High activity detected with ${metrics.totalDashboards} dashboards generated. Peak usage occurs during ${metrics.peakUsageHour}.`);
    } else if (metrics.totalDashboards > 0) {
      insights.push(`Getting started with ${metrics.totalDashboards} dashboard${metrics.totalDashboards > 1 ? 's' : ''} generated. Upload more data files to unlock deeper insights.`);
    }

    // Data processing insights
    const avgDataPerDashboard = metrics.totalDataProcessed / metrics.totalDashboards;
    if (avgDataPerDashboard > 5000) {
      insights.push(`Processing large datasets with average of ${avgDataPerDashboard.toLocaleString()} data points per dashboard. Consider data sampling for faster processing.`);
    } else if (avgDataPerDashboard > 1000) {
      insights.push(`Handling medium-sized datasets efficiently with ${avgDataPerDashboard.toLocaleString()} average data points per dashboard.`);
    }

    // File size insights
    if (metrics.totalFileSize > 50000000) { // 50MB+
      insights.push(`Large file processing detected (${Math.round(metrics.totalFileSize / 1000000)}MB total). Monitor storage usage and consider archiving older results.`);
    }

    // Default insight if no specific conditions met
    if (insights.length === 0) {
      insights.push(`Analytics system is running smoothly with ${metrics.totalDashboards} dashboard${metrics.totalDashboards !== 1 ? 's' : ''} processed successfully.`);
    }

    return insights;
  }

  /**
   * Save analytics event (for future tracking)
   */
  trackEvent(event: string, metadata: Record<string, any>) {
    const analyticsData = this.getAnalyticsData();
    const newEvent = {
      id: Date.now().toString(),
      event,
      metadata,
      timestamp: new Date().toISOString()
    };

    analyticsData.events = [...(analyticsData.events || []), newEvent].slice(-100); // Keep last 100 events
    this.saveAnalyticsData(analyticsData);
  }

  private estimateDataPoints(dashboards: WorkflowResult[]): number {
    // Estimate based on dashboard complexity and metadata
    return dashboards.reduce((total, dashboard) => {
      const configStr = JSON.stringify(dashboard.dashboard_config || {});
      const complexity = configStr.length / 100; // Rough complexity measure
      const baseEstimate = 1000; // Base estimate per dashboard
      return total + Math.round(baseEstimate * (1 + complexity));
    }, 0);
  }

  private estimateTotalFileSize(dashboards: WorkflowResult[]): number {
    return dashboards.reduce((total, dashboard) => {
      return total + (dashboard.metadata?.file_size || 25000); // Default 25KB
    }, 0);
  }

  private calculatePeakUsageHour(dashboards: WorkflowResult[]): string {
    // Analyze completion times to find peak usage hour
    const hourCounts: Record<number, number> = {};
    
    dashboards.forEach(dashboard => {
      const hour = new Date(dashboard.completed_at).getHours();
      hourCounts[hour] = (hourCounts[hour] || 0) + 1;
    });

    const peakHour = Object.entries(hourCounts).reduce((max, [hour, count]) => 
      count > max.count ? { hour: parseInt(hour), count } : max, 
      { hour: 9, count: 0 }
    ).hour;

    const period = peakHour >= 12 ? 'PM' : 'AM';
    const displayHour = peakHour === 0 ? 12 : peakHour > 12 ? peakHour - 12 : peakHour;
    
    return `${displayHour}:00 ${period}`;
  }

  private generateProcessingTimeData(dashboards: WorkflowResult[]) {
    return dashboards.slice(-10).map((dashboard, index) => ({
      name: `Run ${index + 1}`,
      value: dashboard.processing_time || 0,
      timestamp: dashboard.completed_at
    }));
  }

  private generateSuccessRateData(dashboards: WorkflowResult[]) {
    const grouped = this.groupDashboardsByDay(dashboards);
    return Object.entries(grouped).slice(-7).map(([date, data]) => ({
      name: new Date(date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
      value: data.total > 0 ? Math.round((data.successful / data.total) * 100) : 0
    }));
  }

  private generateDataDistribution(dashboards: WorkflowResult[]) {
    const types: Record<string, number> = {};
    
    dashboards.forEach(dashboard => {
      const fileType = dashboard.metadata?.file_type || 'unknown';
      types[fileType] = (types[fileType] || 0) + 1;
    });

    const colors = ['#8884d8', '#82ca9d', '#ffc658', '#ff7300', '#8dd1e1'];
    
    return Object.entries(types).map(([type, count], index) => ({
      name: type.toUpperCase(),
      value: count,
      color: colors[index % colors.length]
    }));
  }

  private generatePerformanceTrends(dashboards: WorkflowResult[]) {
    const grouped = this.groupDashboardsByDay(dashboards);
    return Object.entries(grouped).slice(-7).map(([date, data]) => ({
      date: new Date(date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
      processing_time: data.avgProcessingTime,
      success_rate: data.total > 0 ? (data.successful / data.total) * 100 : 0
    }));
  }

  private groupDashboardsByDay(dashboards: WorkflowResult[]) {
    return dashboards.reduce((acc, dashboard) => {
      const date = new Date(dashboard.completed_at || Date.now()).toISOString().split('T')[0];
      
      if (!acc[date]) {
        acc[date] = { total: 0, successful: 0, totalProcessingTime: 0, avgProcessingTime: 0 };
      }
      
      acc[date].total++;
      acc[date].totalProcessingTime += dashboard.processing_time || 0;
      acc[date].avgProcessingTime = acc[date].totalProcessingTime / acc[date].total;
      
      if (dashboard.workflow_id && dashboard.dashboard_config) {
        acc[date].successful++;
      }
      
      return acc;
    }, {} as Record<string, any>);
  }

  private getAnalyticsData() {
    try {
      const saved = localStorage.getItem(this.storageKey);
      return saved ? JSON.parse(saved) : { events: [] };
    } catch (error) {
      console.error('Failed to load analytics data:', error);
      return { events: [] };
    }
  }

  private saveAnalyticsData(data: any) {
    try {
      localStorage.setItem(this.storageKey, JSON.stringify(data));
    } catch (error) {
      console.error('Failed to save analytics data:', error);
    }
  }
}

export const analyticsService = AnalyticsService.getInstance(); 