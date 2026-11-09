import React, { useState, useEffect } from 'react';
import { 
  Bot, 
  Activity, 
  Wifi, 
  WifiOff, 
  Settings, 
  Play, 
  Pause, 
  RotateCcw,
  Zap,
  Brain,
  Database,
  AlertTriangle,
  CheckCircle,
  XCircle,
  TrendingUp,
  Users
} from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Separator } from '@/components/ui/separator';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Switch } from '@/components/ui/switch';
import { Label } from '@/components/ui/label';

import { 
  useAgentHealth, 
  useAgentInfo, 
  useDashboardConfig,
  useCacheManagement
} from '@/hooks/useDashboardAgent';
import { useWebSocketConnection, useRealTimeDashboard } from '@/hooks/useWebSocket';
import { DashboardData } from '@/types/dashboard';

interface AgentControlPanelProps {
  companyName: string;
  dashboardData: DashboardData;
  onRefreshRequested?: () => Promise<void>;
  className?: string;
}

export function AgentControlPanel({ 
  companyName, 
  dashboardData, 
  onRefreshRequested,
  className = ""
}: AgentControlPanelProps) {
  // Agent Health & Info
  const { healthStatus, isHealthy, aiAvailable, loading: healthLoading } = useAgentHealth(30000);
  const { agentInfo, loading: infoLoading, refresh: refreshInfo } = useAgentInfo();

  // Configuration Management
  const { config, updateConfig } = useDashboardConfig();
  const { clearAllCache, clearDashboardCache, clearAgentCache } = useCacheManagement();

  // WebSocket Connection
  const websocketConnection = useWebSocketConnection(companyName, config.autoRefresh);
  
  // Real-time Dashboard
  const realtimeDashboard = useRealTimeDashboard(companyName);

  // Local State
  const [isManualRefreshLoading, setIsManualRefreshLoading] = useState(false);
  const [cacheClearing, setCacheClearing] = useState(false);

  // Handle manual refresh
  const handleManualRefresh = async () => {
    setIsManualRefreshLoading(true);
    try {
      if (onRefreshRequested) {
        await onRefreshRequested();
      }
      await refreshInfo();
    } finally {
      setIsManualRefreshLoading(false);
    }
  };

  // Handle cache clearing
  const handleClearCache = async () => {
    setCacheClearing(true);
    try {
      await clearAgentCache();
      setTimeout(() => {
        if (onRefreshRequested) {
          onRefreshRequested();
        }
      }, 500);
    } finally {
      setCacheClearing(false);
    }
  };

  // Status indicator component
  const StatusIndicator = ({ status, label, icon: Icon }: { 
    status: 'healthy' | 'error' | 'warning' | 'unknown';
    label: string; 
    icon: React.ElementType;
  }) => {
    const statusConfig = {
      healthy: { color: 'text-green-400', bgColor: 'bg-green-500/20', borderColor: 'border-green-400/30' },
      error: { color: 'text-red-400', bgColor: 'bg-red-500/20', borderColor: 'border-red-400/30' },
      warning: { color: 'text-yellow-400', bgColor: 'bg-yellow-500/20', borderColor: 'border-yellow-400/30' },
      unknown: { color: 'text-gray-400', bgColor: 'bg-gray-500/20', borderColor: 'border-gray-400/30' }
    };

    const config = statusConfig[status];

    return (
      <div className={`flex items-center gap-2 p-2 rounded-md ${config.bgColor} ${config.borderColor} border`}>
        <Icon className={`w-4 h-4 ${config.color}`} />
        <span className={`text-sm ${config.color}`}>{label}</span>
      </div>
    );
  };

  // Real-time metrics
  const connectionUptime = websocketConnection.connected ? 
    Date.now() - (new Date().getTime() - 300000) : 0; // Mock uptime for demo

  return (
    <Card className={`glass-card border-white/10 bg-white/5 ${className}`}>
      <CardHeader>
        <CardTitle className="text-white flex items-center gap-2">
          <Bot className="w-5 h-5 text-blue-400" />
          Dashboard Agent Control
          <Badge 
            variant="outline" 
            className={isHealthy 
              ? 'border-green-400/30 text-green-300 bg-green-500/10' 
              : 'border-red-400/30 text-red-300 bg-red-500/10'
            }
          >
            {isHealthy ? 'Online' : 'Offline'}
          </Badge>
        </CardTitle>
        <CardDescription className="text-gray-300">
          Real-time monitoring and control of the AI Dashboard Agent
        </CardDescription>
      </CardHeader>

      <CardContent className="space-y-6">
        {/* Agent Status Overview */}
        <div className="grid grid-cols-2 gap-3">
          <StatusIndicator 
            status={isHealthy ? 'healthy' : 'error'}
            label="Agent Health"
            icon={isHealthy ? CheckCircle : XCircle}
          />
          <StatusIndicator 
            status={aiAvailable ? 'healthy' : 'warning'}
            label="AI Available"
            icon={Brain}
          />
          <StatusIndicator 
            status={websocketConnection.connected ? 'healthy' : 'warning'}
            label="Real-time"
            icon={websocketConnection.connected ? Wifi : WifiOff}
          />
          <StatusIndicator 
            status={config.enableCache ? 'healthy' : 'unknown'}
            label="Caching"
            icon={Database}
          />
        </div>

        <Separator className="bg-white/10" />

        {/* Agent Information */}
        {agentInfo && (
          <div className="space-y-3">
            <h4 className="text-sm font-medium text-white">Agent Information</h4>
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <span className="text-gray-400">Version:</span>
                <span className="text-white ml-2">{agentInfo.version}</span>
              </div>
              <div>
                <span className="text-gray-400">Provider:</span>
                <span className="text-white ml-2">{agentInfo.ai_provider?.available ? 'Available' : 'Unavailable'}</span>
              </div>
              <div>
                <span className="text-gray-400">Requests:</span>
                <span className="text-white ml-2">{agentInfo.ai_provider?.total_requests || 0}</span>
              </div>
              <div>
                <span className="text-gray-400">Success Rate:</span>
                <span className="text-green-400 ml-2">
                  {agentInfo.ai_provider?.error_rate !== undefined ? 
                    `${((1 - agentInfo.ai_provider.error_rate) * 100).toFixed(1)}%` : 
                    'N/A'
                  }
                </span>
              </div>
            </div>
          </div>
        )}

        <Separator className="bg-white/10" />

        {/* Real-time Configuration */}
        <div className="space-y-3">
          <h4 className="text-sm font-medium text-white">Real-time Configuration</h4>
          
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <Label htmlFor="auto-refresh" className="text-sm text-gray-300">
                Auto Refresh
              </Label>
              <Switch
                id="auto-refresh"
                checked={config.autoRefresh}
                onCheckedChange={(checked) => updateConfig({ autoRefresh: checked })}
              />
            </div>

            <div className="flex items-center justify-between">
              <Label htmlFor="enable-ai" className="text-sm text-gray-300">
                AI Analysis
              </Label>
              <Switch
                id="enable-ai"
                checked={config.enableAI}
                onCheckedChange={(checked) => updateConfig({ enableAI: checked })}
              />
            </div>

            <div className="flex items-center justify-between">
              <Label htmlFor="enable-cache" className="text-sm text-gray-300">
                Data Caching
              </Label>
              <Switch
                id="enable-cache"
                checked={config.enableCache}
                onCheckedChange={(checked) => updateConfig({ enableCache: checked })}
              />
            </div>
          </div>
        </div>

        <Separator className="bg-white/10" />

        {/* Real-time Metrics */}
        <div className="space-y-3">
          <h4 className="text-sm font-medium text-white">Real-time Metrics</h4>
          
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <span className="text-gray-400">WebSocket Status:</span>
              <div className="flex items-center gap-2 mt-1">
                {websocketConnection.connected ? (
                  <>
                    <Wifi className="w-3 h-3 text-green-400" />
                    <span className="text-green-400">Connected</span>
                  </>
                ) : (
                  <>
                    <WifiOff className="w-3 h-3 text-red-400" />
                    <span className="text-red-400">Disconnected</span>
                  </>
                )}
              </div>
            </div>

            <div>
              <span className="text-gray-400">Data Updates:</span>
              <div className="text-blue-400 mt-1">
                {realtimeDashboard.updateCount || 0} total
              </div>
            </div>

            <div>
              <span className="text-gray-400">Refresh Rate:</span>
              <div className="text-white mt-1">
                {config.refreshInterval ? `${config.refreshInterval / 1000}s` : 'Manual'}
              </div>
            </div>

            <div>
              <span className="text-gray-400">Last Update:</span>
              <div className="text-white mt-1">
                {realtimeDashboard.lastUpdate ? 
                  new Date(realtimeDashboard.lastUpdate).toLocaleTimeString() : 
                  'Never'
                }
              </div>
            </div>
          </div>
        </div>

        <Separator className="bg-white/10" />

        {/* Control Actions */}
        <div className="space-y-3">
          <h4 className="text-sm font-medium text-white">Control Actions</h4>
          
          <div className="grid grid-cols-2 gap-2">
            <Button
              onClick={handleManualRefresh}
              disabled={isManualRefreshLoading || healthLoading}
              size="sm"
              className="glass-button text-white"
            >
              {isManualRefreshLoading ? (
                <Activity className="w-4 h-4 mr-2 animate-spin" />
              ) : (
                <RotateCcw className="w-4 h-4 mr-2" />
              )}
              Refresh
            </Button>

            <Button
              onClick={handleClearCache}
              disabled={cacheClearing}
              size="sm"
              variant="outline"
              className="border-white/20 text-white hover:bg-white/10"
            >
              {cacheClearing ? (
                <Activity className="w-4 h-4 mr-2 animate-spin" />
              ) : (
                <Database className="w-4 h-4 mr-2" />
              )}
              Clear Cache
            </Button>

            <Button
              onClick={() => websocketConnection.connected ? websocketConnection.disconnect() : websocketConnection.connect()}
              size="sm"
              variant="outline"
              className="border-white/20 text-white hover:bg-white/10"
            >
              {websocketConnection.connected ? (
                <>
                  <Pause className="w-4 h-4 mr-2" />
                  Disconnect
                </>
              ) : (
                <>
                  <Play className="w-4 h-4 mr-2" />
                  Connect
                </>
              )}
            </Button>

            <Button
              onClick={() => updateConfig({ autoRefresh: !config.autoRefresh })}
              size="sm"
              variant="outline"
              className="border-white/20 text-white hover:bg-white/10"
            >
              {config.autoRefresh ? (
                <>
                  <Pause className="w-4 h-4 mr-2" />
                  Pause
                </>
              ) : (
                <>
                  <Play className="w-4 h-4 mr-2" />
                  Start
                </>
              )}
            </Button>
          </div>
        </div>

        {/* Error Display */}
        {(websocketConnection.error || !isHealthy) && (
          <Alert className="border-yellow-500 bg-yellow-500/10">
            <AlertTriangle className="h-4 w-4" />
            <AlertDescription className="text-yellow-200">
              {websocketConnection.error || 'Agent health check failed. Some features may be limited.'}
            </AlertDescription>
          </Alert>
        )}
      </CardContent>
    </Card>
  );
} 