import React from 'react';
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
  Area,
  AreaChart,
} from 'recharts';

// Color palette for charts
const COLORS = {
  primary: '#3b82f6',
  secondary: '#8b5cf6', 
  success: '#10b981',
  warning: '#f59e0b',
  danger: '#ef4444',
  info: '#06b6d4',
  muted: '#6b7280',
};

const CHART_COLORS = [
  COLORS.primary,
  COLORS.secondary,
  COLORS.success,
  COLORS.warning,
  COLORS.danger,
  COLORS.info,
];

export interface ChartDataPoint {
  name: string;
  value: number;
  [key: string]: string | number;
}

interface BaseChartProps {
  data: ChartDataPoint[];
  height?: number;
  className?: string;
}

interface LineChartProps extends BaseChartProps {
  dataKey: string;
  lineColor?: string;
  showGrid?: boolean;
  showTooltip?: boolean;
}

interface BarChartProps extends BaseChartProps {
  dataKey: string;
  barColor?: string;
  showGrid?: boolean;
  showTooltip?: boolean;
}

interface PieChartProps extends BaseChartProps {
  dataKey: string;
  showLabels?: boolean;
  showTooltip?: boolean;
}

interface AreaChartProps extends BaseChartProps {
  dataKey: string;
  areaColor?: string;
  showGrid?: boolean;
  showTooltip?: boolean;
}

interface MultiLineChartProps extends BaseChartProps {
  dataKeys: string[];
  colors?: string[];
  showGrid?: boolean;
  showTooltip?: boolean;
  showLegend?: boolean;
}

// Custom tooltip component
const CustomTooltip = ({ active, payload, label }: any) => {
  if (active && payload && payload.length) {
    return (
      <div className="bg-white border border-gray-200 rounded-lg p-3 shadow-lg backdrop-blur-sm">
        <p className="text-gray-800 font-medium">{label}</p>
        {payload.map((entry: any, index: number) => (
          <p key={index} className="text-sm text-gray-700" style={{ color: entry.color }}>
            <span className="font-medium">{entry.name}:</span> {entry.value}
          </p>
        ))}
      </div>
    );
  }
  return null;
};

// Simple Line Chart
export const SimpleLineChart: React.FC<LineChartProps> = ({
  data,
  dataKey,
  height = 300,
  lineColor = COLORS.primary,
  showGrid = true,
  showTooltip = true,
  className = '',
}) => (
  <div className={`w-full ${className}`}>
    <ResponsiveContainer width="100%" height={height}>
      <LineChart data={data}>
        {showGrid && <CartesianGrid strokeDasharray="3 3" className="opacity-30" />}
        <XAxis 
          dataKey="name" 
          className="text-muted-foreground text-xs"
          tick={{ fontSize: 12 }}
        />
        <YAxis 
          className="text-muted-foreground text-xs"
          tick={{ fontSize: 12 }}
        />
        {showTooltip && <Tooltip content={<CustomTooltip />} />}
        <Line 
          type="monotone" 
          dataKey={dataKey} 
          stroke={lineColor}
          strokeWidth={2}
          dot={{ fill: lineColor, strokeWidth: 2, r: 4 }}
          activeDot={{ r: 6 }}
        />
      </LineChart>
    </ResponsiveContainer>
  </div>
);

// Simple Bar Chart
export const SimpleBarChart: React.FC<BarChartProps> = ({
  data,
  dataKey,
  height = 300,
  barColor = COLORS.primary,
  showGrid = true,
  showTooltip = true,
  className = '',
}) => (
  <div className={`w-full ${className}`}>
    <ResponsiveContainer width="100%" height={height}>
      <BarChart data={data}>
        {showGrid && <CartesianGrid strokeDasharray="3 3" className="opacity-30" />}
        <XAxis 
          dataKey="name" 
          className="text-muted-foreground text-xs"
          tick={{ fontSize: 12 }}
        />
        <YAxis 
          className="text-muted-foreground text-xs"
          tick={{ fontSize: 12 }}
        />
        {showTooltip && <Tooltip content={<CustomTooltip />} />}
        <Bar dataKey={dataKey} fill={barColor} radius={[4, 4, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  </div>
);

// Simple Pie Chart
export const SimplePieChart: React.FC<PieChartProps> = ({
  data,
  dataKey,
  height = 300,
  showLabels = false, // Default to false to reduce clutter
  showTooltip = true,
  className = '',
}) => (
  <div className={`w-full ${className}`}>
    <ResponsiveContainer width="100%" height={height}>
      <PieChart>
        <Pie
          data={data.slice(0, 6)} // Limit to 6 items max to reduce clutter
          cx="50%"
          cy="50%"
          labelLine={false}
          label={showLabels ? ({ name, percent }: any) => 
            percent > 0.05 ? `${name} ${(percent * 100).toFixed(0)}%` : '' // Only show labels for slices > 5%
          : false}
          outerRadius={Math.min(height * 0.35, 100)} // Responsive radius
          fill="#8884d8"
          dataKey={dataKey}
        >
          {data.slice(0, 6).map((entry, index) => (
            <Cell key={`cell-${index}`} fill={CHART_COLORS[index % CHART_COLORS.length]} />
          ))}
        </Pie>
        {showTooltip && <Tooltip content={<CustomTooltip />} />}
        <Legend 
          wrapperStyle={{ fontSize: '12px' }}
          iconSize={8}
        />
      </PieChart>
    </ResponsiveContainer>
  </div>
);

// Area Chart
export const SimpleAreaChart: React.FC<AreaChartProps> = ({
  data,
  dataKey,
  height = 300,
  areaColor = COLORS.primary,
  showGrid = true,
  showTooltip = true,
  className = '',
}) => (
  <div className={`w-full ${className}`}>
    <ResponsiveContainer width="100%" height={height}>
      <AreaChart data={data}>
        {showGrid && <CartesianGrid strokeDasharray="3 3" className="opacity-30" />}
        <XAxis 
          dataKey="name" 
          className="text-muted-foreground text-xs"
          tick={{ fontSize: 12 }}
        />
        <YAxis 
          className="text-muted-foreground text-xs"
          tick={{ fontSize: 12 }}
        />
        {showTooltip && <Tooltip content={<CustomTooltip />} />}
        <Area
          type="monotone"
          dataKey={dataKey}
          stroke={areaColor}
          fill={areaColor}
          fillOpacity={0.3}
          strokeWidth={2}
        />
      </AreaChart>
    </ResponsiveContainer>
  </div>
);

// Multi-line Chart
export const MultiLineChart: React.FC<MultiLineChartProps> = ({
  data,
  dataKeys,
  height = 300,
  colors = CHART_COLORS,
  showGrid = true,
  showTooltip = true,
  showLegend = true,
  className = '',
}) => (
  <div className={`w-full ${className}`}>
    <ResponsiveContainer width="100%" height={height}>
      <LineChart data={data}>
        {showGrid && <CartesianGrid strokeDasharray="3 3" className="opacity-30" />}
        <XAxis 
          dataKey="name" 
          className="text-muted-foreground text-xs"
          tick={{ fontSize: 12 }}
        />
        <YAxis 
          className="text-muted-foreground text-xs"
          tick={{ fontSize: 12 }}
        />
        {showTooltip && <Tooltip content={<CustomTooltip />} />}
        {showLegend && <Legend />}
        {dataKeys.map((dataKey, index) => (
          <Line
            key={dataKey}
            type="monotone"
            dataKey={dataKey}
            stroke={colors[index % colors.length]}
            strokeWidth={2}
            dot={{ strokeWidth: 2, r: 4 }}
            activeDot={{ r: 6 }}
          />
        ))}
      </LineChart>
    </ResponsiveContainer>
  </div>
);

// Chart container with title and actions
interface ChartContainerProps {
  title: string;
  children: React.ReactNode;
  actions?: React.ReactNode;
  className?: string;
}

export const ChartContainer: React.FC<ChartContainerProps> = ({
  title,
  children,
  actions,
  className = '',
}) => (
  <div className={`bg-background/50 border border-border rounded-lg p-4 ${className}`}>
    <div className="flex items-center justify-between mb-4">
      <h4 className="font-semibold text-foreground">{title}</h4>
      {actions && <div className="flex items-center gap-2">{actions}</div>}
    </div>
    {children}
  </div>
); 