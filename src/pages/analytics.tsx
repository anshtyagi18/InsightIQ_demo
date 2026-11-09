import React, { useState, useEffect, useCallback } from 'react';
import { 
  BarChart3, 
  Users, 
  TrendingUp, 
  Activity,
  Download,
  RotateCcw,
  FileText,
  Upload,
  Trash2,
  ArrowLeft,
  RefreshCw
} from 'lucide-react';
import { toast } from "sonner";
import { useNavigate } from "react-router-dom";

import { GlassCard } from '@/components/ui/glass-card';
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { ChartContainer, SimpleLineChart, SimpleBarChart, SimplePieChart } from '@/components/analytics/chart-components';
import { analyticsService } from '@/services';
import { Alert, AlertDescription } from '@/components/ui/alert';

interface DashboardMetrics {
  totalDashboards: number;
  avgProcessingTime: number;
  successRate: number;
  totalDataProcessed: number;
}

interface ChartData {
  processingTimes: { name: string; value: number }[];
  successRates: { name: string; value: number }[];
  dataDistribution: { name: string; value: number }[];
}

function Header() {
  const navigate = useNavigate();
  
  return (
    <div className="mb-8">
      <div className="flex items-center gap-4 mb-4">
        <Button
          variant="outline"
          size="sm"
          onClick={() => navigate('/')}
          className="glass-button"
        >
          <ArrowLeft className="h-4 w-4 mr-2" />
          Back to Dashboard
        </Button>
      </div>
      <h1 className="text-3xl font-bold bg-gradient-to-r from-purple-600 to-pink-600 bg-clip-text text-transparent mb-2">
        Analytics Dashboard
      </h1>
      <p className="text-muted-foreground">
        Real-time insights and performance metrics from your dashboard generation workflows
      </p>
    </div>
  );
}

export function Analytics() {
  const navigate = useNavigate();
  
  // State management
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [isResetting, setIsResetting] = useState(false);
  const [selectedTimeRange, setSelectedTimeRange] = useState('30d');
  const [metrics, setMetrics] = useState<DashboardMetrics | null>(null);
  const [chartData, setChartData] = useState<ChartData | null>(null);
  const [insights, setInsights] = useState<string[]>([]);
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);

  // Load analytics data function
  const loadAnalyticsData = useCallback(async () => {
    try {
      setIsLoading(true);
      
      console.log('📊 Loading analytics data...');
      
      // Calculate metrics from real dashboard data
      const calculatedMetrics = analyticsService.calculateMetrics();
      setMetrics(calculatedMetrics);
      
      // Generate chart data
      const generatedChartData = analyticsService.generateChartData();
      setChartData(generatedChartData);
      
      // Generate AI insights
      const generatedInsights = analyticsService.generateInsights(calculatedMetrics);
      setInsights(generatedInsights);
      
      setLastUpdate(new Date());
      
      console.log('✅ Analytics data loaded successfully', { 
        totalDashboards: calculatedMetrics.totalDashboards,
        successRate: calculatedMetrics.successRate,
        avgProcessingTime: calculatedMetrics.avgProcessingTime
      });
      
    } catch (error) {
      console.error('❌ Error loading analytics data:', error);
      toast.error('Failed to load analytics data');
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Refresh handler
  const handleRefresh = useCallback(async () => {
    setIsRefreshing(true);
    await loadAnalyticsData();
    setIsRefreshing(false);
    toast.success('Analytics data refreshed');
  }, [loadAnalyticsData]);

  // Reset all analytics data
  const handleResetAnalytics = useCallback(async () => {
    if (!confirm('⚠️ Are you sure you want to reset all analytics data? This will permanently delete all dashboard generation history and cannot be undone.')) {
      return;
    }
    
    try {
      setIsResetting(true);
      
      console.log('🧹 Resetting all analytics data...');
      
      // Clear all stored data using the analytics service
      analyticsService.clearAllData();
      
      // Reset state
      setMetrics(null);
      setChartData(null);
      setInsights([]);
      setLastUpdate(null);
      
      // Reload to show empty state
      await loadAnalyticsData();
      
      toast.success('All analytics data has been reset');
      console.log('✅ Analytics data reset completed');
      
    } catch (error) {
      console.error('❌ Error resetting analytics data:', error);
      toast.error('Failed to reset analytics data');
    } finally {
      setIsResetting(false);
    }
  }, [loadAnalyticsData]);

  // Export handler
  const handleExport = useCallback(() => {
    if (!metrics || !chartData) {
      toast.error('No data available to export');
      return;
    }
    
    const exportData = {
      metrics,
      chartData,
      insights,
      lastUpdate: lastUpdate?.toISOString(),
      generatedAt: new Date().toISOString(),
      exportedFrom: 'InsightIQ - Analytics Dashboard'
    };
    
    const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `analytics-export-${new Date().toISOString().split('T')[0]}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    
    toast.success('Analytics data exported successfully');
  }, [metrics, chartData, insights, lastUpdate]);

  // Format helper functions
  const formatTime = (seconds: number) => {
    if (seconds < 60) return `${seconds.toFixed(1)}s`;
    return `${(seconds / 60).toFixed(1)}m`;
  };

  const formatNumber = (num: number) => {
    if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M`;
    if (num >= 1000) return `${(num / 1000).toFixed(1)}K`;
    return num.toString();
  };

  // Load data on component mount
  useEffect(() => {
    loadAnalyticsData();
  }, [loadAnalyticsData]);

  // Loading state
  if (isLoading) {
    return (
      <div className="space-y-6 animate-fade-in">
        <Header />
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="glass-card p-6 animate-pulse">
              <div className="h-4 bg-muted rounded w-3/4 mb-2"></div>
              <div className="h-8 bg-muted rounded w-1/2 mb-2"></div>
              <div className="h-3 bg-muted rounded w-2/3"></div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  // Empty state
  if (!metrics || metrics.totalDashboards === 0) {
    return (
      <div className="space-y-6 animate-fade-in">
        <Header />
        <GlassCard className="p-8 text-center">
          <FileText className="h-16 w-16 mx-auto mb-4 text-muted-foreground" />
          <h3 className="text-xl font-semibold mb-2">No Analytics Data Available</h3>
          <p className="text-muted-foreground mb-6">
            Upload data files and generate dashboards to see comprehensive analytics insights and performance metrics.
          </p>
          <div className="flex flex-col sm:flex-row gap-3 justify-center">
            <Button onClick={() => navigate('/')} className="glass-button-primary">
              <Upload className="h-4 w-4 mr-2" />
              Go to Dashboard
            </Button>
            <Button 
              variant="outline" 
              onClick={() => {
                analyticsService.addSampleDataIfEmpty();
                handleRefresh();
              }}
              className="glass-button"
            >
              <BarChart3 className="h-4 w-4 mr-2" />
              Load Sample Data
            </Button>
          </div>
        </GlassCard>
      </div>
    );
  }

  // Main analytics view
  return (
    <div className="space-y-6 animate-fade-in">
      <Header />
      
      {/* Last Updated Info */}
      {lastUpdate && (
        <Alert className="border-blue-500/50 bg-blue-500/10">
          <Activity className="h-4 w-4" />
          <AlertDescription className="text-blue-200">
            Analytics last updated: {lastUpdate.toLocaleString()}
          </AlertDescription>
        </Alert>
      )}
      
      {/* Analytics Header */}
      <GlassCard className="p-6">
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
          <div>
            <h2 className="text-2xl font-bold bg-gradient-to-r from-purple-600 to-pink-600 bg-clip-text text-transparent">
              Dashboard Analytics
            </h2>
            <p className="text-muted-foreground">Real-time insights from your dashboard generation workflows</p>
          </div>
          
          <div className="flex items-center gap-3">
            <Select value={selectedTimeRange} onValueChange={setSelectedTimeRange}>
              <SelectTrigger className="w-32 glass-button">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="7d">Last 7 days</SelectItem>
                <SelectItem value="30d">Last 30 days</SelectItem>
                <SelectItem value="90d">Last 90 days</SelectItem>
              </SelectContent>
            </Select>
            
            <Button
              variant="outline"
              size="sm"
              onClick={handleRefresh}
              disabled={isRefreshing}
              className="glass-button"
            >
              <RefreshCw className={`h-4 w-4 mr-2 ${isRefreshing ? 'animate-spin' : ''}`} />
              {isRefreshing ? 'Refreshing...' : 'Refresh'}
            </Button>
            
            <Button
              size="sm"
              onClick={handleExport}
              className="glass-button-primary"
            >
              <Download className="h-4 w-4 mr-2" />
              Export
            </Button>

            <Button
              variant="destructive"
              size="sm"
              onClick={handleResetAnalytics}
              disabled={isResetting}
              className="bg-red-600/20 border-red-500/50 text-red-200 hover:bg-red-600/30"
            >
              <Trash2 className={`h-4 w-4 mr-2 ${isResetting ? 'animate-spin' : ''}`} />
              {isResetting ? 'Resetting...' : 'Reset All Data'}
            </Button>
          </div>
        </div>
      </GlassCard>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <GlassCard className="p-6 hover:scale-105 transition-all duration-300">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-muted-foreground">Total Dashboards</p>
              <p className="text-2xl font-bold text-foreground">{metrics.totalDashboards}</p>
              <p className="text-xs text-muted-foreground mt-1">Generated successfully</p>
            </div>
            <div className="p-3 rounded-lg bg-blue-500/10 text-blue-500">
              <BarChart3 className="h-6 w-6" />
            </div>
          </div>
        </GlassCard>

        <GlassCard className="p-6 hover:scale-105 transition-all duration-300">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-muted-foreground">Avg Processing Time</p>
              <p className="text-2xl font-bold text-foreground">{formatTime(metrics.avgProcessingTime)}</p>
              <p className="text-xs text-muted-foreground mt-1">Per dashboard</p>
            </div>
            <div className="p-3 rounded-lg bg-green-500/10 text-green-500">
              <Activity className="h-6 w-6" />
            </div>
          </div>
        </GlassCard>

        <GlassCard className="p-6 hover:scale-105 transition-all duration-300">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-muted-foreground">Success Rate</p>
              <p className="text-2xl font-bold text-foreground">{metrics.successRate.toFixed(1)}%</p>
              <p className="text-xs text-muted-foreground mt-1">
                {metrics.successRate > 95 ? 'Excellent' : metrics.successRate > 85 ? 'Good' : 'Needs improvement'}
              </p>
            </div>
            <div className="p-3 rounded-lg bg-purple-500/10 text-purple-500">
              <TrendingUp className="h-6 w-6" />
            </div>
          </div>
        </GlassCard>

        <GlassCard className="p-6 hover:scale-105 transition-all duration-300">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-muted-foreground">Data Processed</p>
              <p className="text-2xl font-bold text-foreground">{formatNumber(metrics.totalDataProcessed)}</p>
              <p className="text-xs text-muted-foreground mt-1">Data points</p>
            </div>
            <div className="p-3 rounded-lg bg-orange-500/10 text-orange-500">
              <Users className="h-6 w-6" />
            </div>
          </div>
        </GlassCard>
      </div>

      {/* Charts Section */}
      {chartData && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <GlassCard className="p-6">
            <ChartContainer title="Processing Performance">
              <SimpleLineChart 
                data={chartData.processingTimes} 
                dataKey="value"
                height={250}
                showGrid={true}
              />
            </ChartContainer>
          </GlassCard>

          <GlassCard className="p-6">
            <ChartContainer title="Success Rate Trends">
              <SimpleBarChart 
                data={chartData.successRates} 
                dataKey="value"
                height={250}
                showGrid={true}
              />
            </ChartContainer>
          </GlassCard>

          <GlassCard className="p-6">
            <ChartContainer title="Data Distribution">
              <SimplePieChart 
                data={chartData.dataDistribution} 
                dataKey="value"
                height={250}
              />
            </ChartContainer>
          </GlassCard>

          {/* AI Insights Panel */}
          <GlassCard className="p-6">
            <div className="flex items-center gap-2 mb-4">
              <div className="p-2 rounded-lg bg-gradient-to-r from-purple-500/10 to-pink-500/10">
                <Activity className="h-5 w-5 text-purple-500" />
              </div>
              <h3 className="text-lg font-semibold">AI Insights</h3>
            </div>
            
            <div className="space-y-3">
              {insights.length > 0 ? (
                insights.map((insight, index) => (
                  <div key={index} className="p-3 rounded-lg bg-gradient-to-r from-blue-500/5 to-purple-500/5 border border-blue-500/20">
                    <p className="text-sm text-foreground">{insight}</p>
                  </div>
                ))
              ) : (
                <div className="p-3 rounded-lg bg-muted/50 text-center">
                  <p className="text-sm text-muted-foreground">No AI insights available yet</p>
                </div>
              )}
            </div>
            
            <div className="mt-4 pt-3 border-t border-border">
              <Badge variant="outline" className="text-xs">
                <Activity className="h-3 w-3 mr-1" />
                AI-Powered Analysis
              </Badge>
            </div>
          </GlassCard>
        </div>
      )}
    </div>
  );
}
