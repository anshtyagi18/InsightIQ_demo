/**
 * Enhanced Dashboard with Dashboard Agent Integration and Real-time Updates
 * 
 * This component demonstrates the full integration with the Dashboard Agent API,
 * providing AI-powered summaries, KPI analysis, alert processing, and real-time updates via WebSocket.
 */

import React, { useState, useEffect } from 'react';
import { 
  TrendingUp, 
  Users, 
  DollarSign, 
  BarChart3, 
  Lightbulb, 
  Target, 
  Zap, 
  RefreshCw,
  Bot,
  AlertTriangle,
  CheckCircle,
  Loader2,
  Wifi,
  WifiOff,
  Radio,
  Bell,
  Activity
} from "lucide-react";

import { Header } from "@/components/layout/header";
import { KPICard } from "@/components/dashboard/kpi-card";
import { ChartCard } from "@/components/dashboard/chart-card";
import { InsightCard } from "@/components/dashboard/insight-card";
import { AnalyticsAreaChart } from "@/components/charts/area-chart";
import { AnalyticsLineChart } from "@/components/charts/line-chart";
import { AnalyticsBarChart } from "@/components/charts/bar-chart";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Separator } from "@/components/ui/separator";

import { 
  useDashboardData, 
  useAgentHealth, 
  useCustomInsight,
  useCacheManagement
} from "@/hooks/useDashboardAgent";
import { 
  useRealTimeDashboard, 
  useDashboardUpdates, 
  useWebSocketHealth 
} from "@/hooks/useWebSocket";
import { DashboardData } from "@/types/dashboard";

export function EnhancedDashboard() {
  const [companyName] = useState("TechCorp Inc.");
  const [timePeriod, setTimePeriod] = useState("last_month");
  const [customPrompt, setCustomPrompt] = useState("");
  const [showRealTimeUpdates, setShowRealTimeUpdates] = useState(true);
  const [dashboardData, setDashboardData] = useState<DashboardData | null>(null);
  const [loadingDashboard, setLoadingDashboard] = useState(false);
  const [dashboardError, setDashboardError] = useState<string | null>(null);

  // Dashboard Agent hooks
  const { 
    loading: dashboardLoading, 
    error: dashboardError,
    summary,
    kpiAnalysis,
    alertsAnalysis,
    refetch: refetchDashboard
  } = useDashboardData(companyName, null, timePeriod, {
    enableAI: true,
    fallbackMode: true,
    autoRefresh: false
  });

  const { 
    isHealthy, 
    aiAvailable, 
    loading: healthLoading 
  } = useAgentHealth(30000); // Check every 30 seconds

  const {
    insight: customInsight,
    loading: insightLoading,
    error: insightError,
    generateInsight,
    reset: resetInsight
  } = useCustomInsight();

  const { clearAgentCache } = useCacheManagement();

  // Real-time WebSocket hooks
  const realTimeDashboard = useRealTimeDashboard(companyName, [
    'dashboard_updates',
    'kpi_analysis', 
    'alerts',
    'custom_insights'
  ]);

  const {
    summaryUpdate,
    kpiUpdate,
    alertsUpdate,
    customInsightUpdate,
    clearUpdates,
    hasUpdates
  } = useDashboardUpdates();

  const wsHealth = useWebSocketHealth();

  // Handle custom insight generation
  const handleGenerateCustomInsight = async () => {
    if (!customPrompt.trim() || !dashboardData) return;
    
    await generateInsight(
      dashboardData.metrics || {},
      customPrompt,
      `Company: ${companyName}, Period: ${timePeriod}`
    );
  };

  // Real-time connection status indicator
  const ConnectionStatusIndicator = () => (
    <div className="flex items-center gap-2 text-sm">
      {realTimeDashboard.connected ? (
        <div className="flex items-center gap-1">
          <Wifi className="h-4 w-4 text-green-500" />
          <span className="text-white/80">Live</span>
          <Badge variant="secondary" className="text-xs">
            <Radio className="h-3 w-3 mr-1" />
            {realTimeDashboard.updateCount}
          </Badge>
        </div>
      ) : (
        <div className="flex items-center gap-1">
          <WifiOff className="h-4 w-4 text-red-500" />
          <span className="text-white/60">Offline</span>
        </div>
      )}
    </div>
  );

  // Agent status indicator
  const AgentStatusIndicator = () => (
    <div className="flex items-center gap-2 text-sm">
      {healthLoading ? (
        <Loader2 className="h-4 w-4 animate-spin" />
      ) : isHealthy ? (
        <CheckCircle className="h-4 w-4 text-green-500" />
      ) : (
        <AlertTriangle className="h-4 w-4 text-red-500" />
      )}
      <span className="text-white/80">
        Agent: {healthLoading ? 'Checking...' : isHealthy ? 'Online' : 'Offline'}
      </span>
      {aiAvailable && (
        <Badge variant="secondary" className="text-xs">
          <Bot className="h-3 w-3 mr-1" />
          AI Enabled
        </Badge>
      )}
    </div>
  );

  // Real-time updates notification
  const RealTimeUpdatesNotification = () => {
    if (!hasUpdates || !showRealTimeUpdates) return null;

    return (
      <Alert className="border-blue-500/50 bg-blue-500/10 mb-4">
        <Bell className="h-4 w-4" />
        <AlertDescription className="text-blue-200 flex items-center justify-between">
          <span>New real-time updates available!</span>
          <div className="flex gap-2">
            <Button 
              size="sm" 
              variant="outline" 
              className="border-blue-400/50 text-blue-200 hover:bg-blue-400/20"
              onClick={() => {
                refetchDashboard();
                clearUpdates();
              }}
            >
              Apply Updates
            </Button>
            <Button 
              size="sm" 
              variant="ghost" 
              className="text-blue-200 hover:bg-blue-400/20"
              onClick={clearUpdates}
            >
              Dismiss
            </Button>
          </div>
        </AlertDescription>
      </Alert>
    );
  };

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <Header />
        <div className="flex items-center gap-4">
          <ConnectionStatusIndicator />
          <AgentStatusIndicator />
          <Button
            onClick={refetchDashboard}
            disabled={dashboardLoading}
            size="sm"
            variant="outline"
            className="border-white/20 text-white hover:bg-white/10"
          >
            {dashboardLoading ? (
              <Loader2 className="h-4 w-4 animate-spin mr-2" />
            ) : (
              <RefreshCw className="h-4 w-4 mr-2" />
            )}
            Refresh
          </Button>
        </div>
      </div>

      {/* Real-time Updates Notification */}
      <RealTimeUpdatesNotification />

      {/* Error Alert */}
      {dashboardError && (
        <Alert className="border-red-500/50 bg-red-500/10">
          <AlertTriangle className="h-4 w-4" />
          <AlertDescription className="text-red-200">
            {dashboardError}
          </AlertDescription>
        </Alert>
      )}

      {/* WebSocket Connection Info (Development) */}
      {process.env.NODE_ENV === 'development' && (
        <Card className="glass-card border-white/10">
          <CardHeader className="pb-2">
            <CardTitle className="text-white text-sm">Real-time Connection Status</CardTitle>
          </CardHeader>
          <CardContent className="pt-0">
            <div className="text-xs text-white/60 space-y-1">
              <div>Client ID: {wsHealth.clientId}</div>
              <div>Connected: {realTimeDashboard.connected ? 'Yes' : 'No'}</div>
              <div>Subscriptions: {realTimeDashboard.subscriptions.join(', ')}</div>
              <div>Updates Received: {realTimeDashboard.updateCount}</div>
              {realTimeDashboard.lastUpdate && (
                <div>Last Update: {new Date(realTimeDashboard.lastUpdate.timestamp).toLocaleTimeString()}</div>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      {/* AI-Generated Summary with Real-time Indicator */}
      {(summary || summaryUpdate) && (
        <Card className="glass-card border-white/10">
          <CardHeader>
            <CardTitle className="text-white flex items-center gap-2">
              <Bot className="h-5 w-5" />
              AI Dashboard Summary
              {(summary || summaryUpdate?.summary)?.ai_generated && (
                <Badge variant="secondary" className="text-xs">
                  AI Generated
                </Badge>
              )}
              {summaryUpdate && (
                <Badge variant="outline" className="text-xs border-green-400/50 text-green-200">
                  <Radio className="h-3 w-3 mr-1" />
                  Live Update
                </Badge>
              )}
            </CardTitle>
            <CardDescription className="text-white/60">
              Generated for {timePeriod} • {(summary || summaryUpdate?.summary)?.kpis_analyzed} KPIs analyzed
            </CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-white/90 leading-relaxed">
              {summaryUpdate?.summary?.content || summary?.content}
            </p>
            {(summary || summaryUpdate?.summary)?.fallback_reason && (
              <p className="text-yellow-400 text-sm mt-2">
                Note: {(summary || summaryUpdate?.summary)?.fallback_reason}
              </p>
            )}
          </CardContent>
        </Card>
      )}

      {/* KPI Cards with AI Analysis */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <KPICard
          title="Total Revenue"
          value="$127.5K"
          change="+12.5% from last month"
          changeType="positive"
          icon={DollarSign}
        />
        <KPICard
          title="Active Users"
          value="14.2K"
          change="+8.3% from last month"
          changeType="positive"
          icon={Users}
        />
        <KPICard
          title="Conversion Rate"
          value="3.24%"
          change="-2.1% from last month"
          changeType="negative"
          icon={TrendingUp}
        />
        <KPICard
          title="Avg. Session"
          value="4m 32s"
          change="+0.8% from last month"
          changeType="positive"
          icon={BarChart3}
        />
      </div>

      {/* KPI Analysis with Real-time Updates */}
      {(kpiAnalysis || kpiUpdate) && (
        <Card className="glass-card border-white/10">
          <CardHeader>
            <CardTitle className="text-white flex items-center gap-2">
              <BarChart3 className="h-5 w-5" />
              KPI Analysis
              {(kpiAnalysis || kpiUpdate?.analysis)?.ai_generated && (
                <Badge variant="secondary" className="text-xs">
                  AI Powered
                </Badge>
              )}
              {kpiUpdate && (
                <Badge variant="outline" className="text-xs border-green-400/50 text-green-200">
                  <Radio className="h-3 w-3 mr-1" />
                  Live Update
                </Badge>
              )}
            </CardTitle>
            <CardDescription className="text-white/60">
              {(kpiAnalysis || kpiUpdate?.analysis)?.analysis_type} analysis • {(kpiAnalysis || kpiUpdate?.analysis)?.kpis_count} metrics
            </CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-white/90 leading-relaxed">
              {kpiUpdate?.analysis?.insights || kpiAnalysis?.insights}
            </p>
          </CardContent>
        </Card>
      )}

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <ChartCard title="Traffic Overview">
          <AnalyticsAreaChart />
        </ChartCard>
        <ChartCard title="User Engagement">
          <AnalyticsLineChart />
        </ChartCard>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <ChartCard title="Revenue Analytics">
            <AnalyticsBarChart />
          </ChartCard>
        </div>
        
        {/* AI Insights and Alerts with Real-time Updates */}
        <div className="space-y-4">
          <h3 className="text-lg font-semibold text-white mb-4">AI Insights & Alerts</h3>
          
          {/* AI-Generated Alert Analysis with Real-time Updates */}
          {(alertsAnalysis || alertsUpdate) && (
            <Card className="glass-card border-white/10">
              <CardHeader className="pb-3">
                <CardTitle className="text-white text-sm flex items-center gap-2">
                  <Zap className="h-4 w-4" />
                  Alert Analysis
                  {(alertsAnalysis || alertsUpdate?.alert_analysis)?.ai_generated && (
                    <Badge variant="secondary" className="text-xs">AI</Badge>
                  )}
                  {alertsUpdate && (
                    <Badge variant="outline" className="text-xs border-green-400/50 text-green-200">
                      <Radio className="h-3 w-3 mr-1" />
                      Live
                    </Badge>
                  )}
                </CardTitle>
              </CardHeader>
              <CardContent className="pt-0">
                <p className="text-white/80 text-sm leading-relaxed">
                  {alertsUpdate?.alert_analysis?.summary || alertsAnalysis?.summary}
                </p>
                <p className="text-white/60 text-xs mt-2">
                  {(alertsAnalysis || alertsUpdate?.alert_analysis)?.total_alerts} alerts processed
                </p>
              </CardContent>
            </Card>
          )}

          {/* Static Insights (fallback) */}
          <InsightCard
            title="Revenue Opportunity"
            description="Customer segment A shows 23% higher conversion potential. Consider targeted campaigns."
            icon={Target}
            priority="high"
            tags={["Revenue", "Conversion"]}
            action={
              <Button size="sm" className="glass-button text-white">
                View Details
              </Button>
            }
          />
          
          <InsightCard
            title="Performance Alert"
            description="Page load times increased by 15% this week. Infrastructure optimization recommended."
            icon={Zap}
            priority="medium"
            tags={["Performance", "UX"]}
            action={
              <Button size="sm" variant="outline" className="border-white/20 text-white hover:bg-white/10">
                Investigate
              </Button>
            }
          />

          {/* Custom Insight Generator with Real-time Updates */}
          <Card className="glass-card border-white/10">
            <CardHeader className="pb-3">
              <CardTitle className="text-white text-sm flex items-center gap-2">
                <Lightbulb className="h-4 w-4" />
                Custom AI Insight
                {realTimeDashboard.connected && (
                  <Badge variant="outline" className="text-xs border-green-400/50 text-green-200">
                    Live
                  </Badge>
                )}
              </CardTitle>
            </CardHeader>
            <CardContent className="pt-0 space-y-3">
              <textarea
                value={customPrompt}
                onChange={(e) => setCustomPrompt(e.target.value)}
                placeholder="Ask AI to analyze specific aspects of your data..."
                className="w-full p-2 text-sm bg-white/5 border border-white/10 rounded text-white placeholder-white/40 resize-none"
                rows={3}
              />
              <div className="flex gap-2">
                <Button
                  onClick={handleGenerateCustomInsight}
                  disabled={insightLoading || !customPrompt.trim()}
                  size="sm"
                  className="glass-button text-white flex-1"
                >
                  {insightLoading ? (
                    <Loader2 className="h-3 w-3 animate-spin mr-1" />
                  ) : (
                    <Bot className="h-3 w-3 mr-1" />
                  )}
                  Generate
                </Button>
                {(customInsight || customInsightUpdate) && (
                  <Button
                    onClick={() => {
                      resetInsight();
                      clearUpdates();
                    }}
                    size="sm"
                    variant="outline"
                    className="border-white/20 text-white hover:bg-white/10"
                  >
                    Clear
                  </Button>
                )}
              </div>
              
              {insightError && (
                <p className="text-red-400 text-xs">{insightError}</p>
              )}
              
              {(customInsight || customInsightUpdate) && (
                <div className="mt-3 p-3 bg-white/5 rounded border border-white/10">
                  <p className="text-white/90 text-sm leading-relaxed">
                    {customInsightUpdate?.insight?.insight || customInsight?.insight}
                  </p>
                  {(customInsight || customInsightUpdate?.insight)?.ai_generated && (
                    <div className="flex items-center gap-2 mt-2">
                      <Badge variant="secondary" className="text-xs">
                        AI Generated
                      </Badge>
                      {customInsightUpdate && (
                        <Badge variant="outline" className="text-xs border-green-400/50 text-green-200">
                          <Radio className="h-3 w-3 mr-1" />
                          Real-time
                        </Badge>
                      )}
                      {(customInsight || customInsightUpdate?.insight)?.confidence && (
                        <span className="text-white/60 text-xs">
                          Confidence: {Math.round((customInsight || customInsightUpdate?.insight)?.confidence * 100)}%
                        </span>
                      )}
                    </div>
                  )}
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Debug Info (development only) */}
      {process.env.NODE_ENV === 'development' && dashboardData && (
        <Card className="glass-card border-white/10">
          <CardHeader>
            <CardTitle className="text-white text-sm">Debug Info</CardTitle>
          </CardHeader>
          <CardContent>
            <pre className="text-white/60 text-xs overflow-auto">
              {JSON.stringify({
                generated_at: dashboardData.generated_at,
                company_name: dashboardData.company_name,
                time_period: dashboardData.time_period,
                summary_ai: summary?.ai_generated,
                kpi_ai: kpiAnalysis?.ai_generated,
                alerts_ai: alertsAnalysis?.ai_generated,
                websocket_connected: realTimeDashboard.connected,
                real_time_updates: realTimeDashboard.updateCount,
                active_subscriptions: realTimeDashboard.subscriptions,
                has_live_updates: hasUpdates
              }, null, 2)}
            </pre>
          </CardContent>
        </Card>
      )}
    </div>
  );
} 