/**
 * Dynamic KPI Component
 * Renders KPI cards based on backend configuration
 */

import React from 'react';
import { TrendingUp, TrendingDown, Minus, Target } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { KPIConfig, dashboardService } from '@/services/dashboard.service';

interface DynamicKPIProps {
  kpiConfig: KPIConfig;
  className?: string;
  theme?: {
    colors: Record<string, string>;
  };
}

export const DynamicKPI: React.FC<DynamicKPIProps> = ({
  kpiConfig,
  className = '',
  theme
}) => {
  const { name, value, unit, trend, trend_percentage, description, format_type } = kpiConfig;
  
  // Format the KPI value using utility function
  const formatKPIValue = (kpi: KPIConfig): string => {
    const { value, format_type, unit } = kpi;
    
    // Add null safety check for value
    const safeValue = value ?? 0;
    
    switch (format_type) {
      case 'currency':
        return new Intl.NumberFormat('en-US', {
          style: 'currency',
          currency: 'USD',
        }).format(safeValue);
      
      case 'percentage':
        return `${safeValue.toFixed(1)}%`;
      
      case 'number':
      default:
        const formatted = new Intl.NumberFormat('en-US').format(safeValue);
        return unit ? `${formatted} ${unit}` : formatted;
    }
  };

  // Get trend indicator utility function
  const getTrendIndicator = (kpi: KPIConfig): { icon: string; color: string; text: string } => {
    const { trend, trend_percentage } = kpi;
    
    // Add null safety check for trend_percentage
    const safePercentage = trend_percentage ?? 0;
    
    switch (trend) {
      case 'up':
        return {
          icon: '↗️',
          color: 'text-green-500',
          text: `+${safePercentage.toFixed(1)}%`
        };
      
      case 'down':
        return {
          icon: '↘️',
          color: 'text-red-500',
          text: `-${Math.abs(safePercentage).toFixed(1)}%`
        };
      
      case 'neutral':
      default:
        return {
          icon: '→',
          color: 'text-gray-500',
          text: 'No change'
        };
    }
  };
  
  // Format the KPI value
  const formattedValue = formatKPIValue(kpiConfig);
  
  // Get trend indicator
  const trendIndicator = getTrendIndicator(kpiConfig);
  
  // Trend icon based on direction
  const getTrendIcon = () => {
    switch (trend) {
      case 'up':
        return <TrendingUp className="w-4 h-4" />;
      case 'down':
        return <TrendingDown className="w-4 h-4" />;
      case 'neutral':
      default:
        return <Minus className="w-4 h-4" />;
    }
  };

  // Get trend color classes
  const getTrendColorClasses = () => {
    switch (trend) {
      case 'up':
        return 'text-green-400 bg-green-500/10 border-green-400/30';
      case 'down':
        return 'text-red-400 bg-red-500/10 border-red-400/30';
      case 'neutral':
      default:
        return 'text-gray-400 bg-gray-500/10 border-gray-400/30';
    }
  };

  // Get value color based on trend
  const getValueColorClasses = () => {
    switch (trend) {
      case 'up':
        return 'text-green-300';
      case 'down':
        return 'text-red-300';
      case 'neutral':
      default:
        return 'text-white';
    }
  };

  return (
    <Card className={`${className} bg-white/5 border-white/20 hover:bg-white/10 transition-colors`}>
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Target className="w-4 h-4 text-blue-400" />
            <CardTitle className="text-white text-sm font-medium">{name}</CardTitle>
          </div>
          {(trend_percentage ?? 0) > 0 && (
            <Badge 
              variant="outline" 
              className={`text-xs ${getTrendColorClasses()}`}
            >
              <div className="flex items-center space-x-1">
                {getTrendIcon()}
                <span>{trendIndicator.text}</span>
              </div>
            </Badge>
          )}
        </div>
      </CardHeader>
      <CardContent className="pt-2">
        <div className="space-y-2">
          {/* Main KPI Value */}
          <div className={`text-2xl font-bold ${getValueColorClasses()}`}>
            {formattedValue}
          </div>
          
          {/* Description */}
          <CardDescription className="text-white/60 text-xs leading-relaxed">
            {description}
          </CardDescription>
          
          {/* Additional Metadata */}
          <div className="flex items-center justify-between text-xs">
            <span className="text-white/50">
              Type: {format_type}
            </span>
            {unit && (
              <span className="text-white/50">
                Unit: {unit}
              </span>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

// KPI Grid Component for multiple KPIs
interface DynamicKPIGridProps {
  kpis: KPIConfig[];
  className?: string;
  theme?: {
    colors: Record<string, string>;
  };
  columns?: number;
}

export const DynamicKPIGrid: React.FC<DynamicKPIGridProps> = ({
  kpis,
  className = '',
  theme,
  columns = 3
}) => {
  const gridColsClass = `grid-cols-1 md:grid-cols-${Math.min(columns, 3)} xl:grid-cols-${columns}`;
  
  return (
    <div className={`grid gap-4 ${gridColsClass} ${className}`}>
      {kpis.map((kpi, index) => (
        <DynamicKPI
          key={`${kpi.name}-${index}`}
          kpiConfig={kpi}
          theme={theme}
        />
      ))}
    </div>
  );
};

// Compact KPI Row Component for smaller displays
interface DynamicKPIRowProps {
  kpis: KPIConfig[];
  className?: string;
  theme?: {
    colors: Record<string, string>;
  };
}

export const DynamicKPIRow: React.FC<DynamicKPIRowProps> = ({
  kpis,
  className = '',
  theme
}) => {
  return (
    <div className={`flex flex-wrap gap-4 ${className}`}>
      {kpis.map((kpi, index) => (
        <div key={`${kpi.name}-${index}`} className="flex-1 min-w-0">
          <DynamicKPI
            kpiConfig={kpi}
            theme={theme}
            className="h-full"
          />
        </div>
      ))}
    </div>
  );
};

export default DynamicKPI; 