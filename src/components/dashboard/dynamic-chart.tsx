/**
 * Dynamic Chart Component
 * Renders different chart types based on backend configuration
 */

import React from 'react';
import {
  LineChart,
  AreaChart,
  BarChart,
  PieChart,
  ScatterChart,
  RadarChart,
  ComposedChart,
  Line,
  Area,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Pie,
  Cell,
  Scatter,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
  LabelList,
} from 'recharts';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { ChartConfig } from '@/services/dashboard.service';

interface DynamicChartProps {
  chartConfig: ChartConfig;
  data: Record<string, unknown>[];
  className?: string;
  theme?: {
    chart_palette: string[];
    colors: Record<string, string>;
  };
}

export const DynamicChart: React.FC<DynamicChartProps> = ({
  chartConfig,
  data,
  className = '',
  theme
}) => {
  const { chart_type, title, description, confidence, recharts_config, data_columns } = chartConfig;
  
  // Provide default recharts_config if undefined
  const safeRechartsConfig = recharts_config || {};
  
  // Provide default data_columns if undefined or empty
  const safeDataColumns = data_columns && data_columns.length > 0 ? data_columns : ['x', 'y'];
  
  // Provide safe data array
  const safeData = data || [];
  
  // Provide default colors
  const colors = theme?.chart_palette || [
    '#3b82f6', '#ef4444', '#10b981', '#f59e0b', '#8b5cf6', '#06b6d4'
  ];

  // Derive descriptive X and Y axis titles
  const formatAxisLabel = (s: string) => {
    if (!s) return '';
    return String(s)
      .replace(/_/g, ' ')
      .replace(/([a-z])([A-Z])/g, '$1 $2')
      .replace(/\b\w/g, c => c.toUpperCase())
      .trim();
  };

  const rawXTitle =
    safeRechartsConfig.xaxis_title ||
    safeRechartsConfig.xAxisKey ||
    (chartConfig as any).xAxis ||
    safeDataColumns[0] ||
    'Category';

  const rawYTitle =
    safeRechartsConfig.yaxis_title ||
    safeRechartsConfig.dataKey ||
    (safeRechartsConfig.dataKeys && safeRechartsConfig.dataKeys.join(', ')) ||
    (chartConfig as any).yAxis ||
    (chartConfig as any).yAxes?.join(', ') ||
    safeDataColumns[1] ||
    'Value';

  const xAxisTitle = formatAxisLabel(rawXTitle);
  const yAxisTitle = formatAxisLabel(rawYTitle);

  // Common axis label and tick styling
  const axisTickStyle = { fontSize: 11, fill: '#94a3b8' };
  const axisLineStyle = { stroke: '#374151' };
  
  const xAxisLabelProps = {
    value: xAxisTitle,
    position: 'insideBottom' as const,
    offset: -8,
    fill: '#cbd5e1',
    fontSize: 11,
    fontWeight: 500,
  };

  const yAxisLabelProps = {
    value: yAxisTitle,
    angle: -90,
    position: 'insideLeft' as const,
    offset: -5,
    fill: '#cbd5e1',
    fontSize: 11,
    fontWeight: 500,
    style: { textAnchor: 'middle' },
  };

  // Common chart props with ample padding for axis titles
  const chartProps = {
    data: safeData,
    margin: safeRechartsConfig.margin || { top: 15, right: 30, left: 45, bottom: 45 },
  };

  const showDataLabels = Boolean(safeRechartsConfig?.showDataLabels || (chartConfig as any).showDataLabels);

  const renderChart = () => {
    // If no data is available, show a placeholder
    if (!safeData || safeData.length === 0) {
      return (
        <div className="flex items-center justify-center h-64 text-gray-500">
          <p>No data available for this chart</p>
        </div>
      );
    }

    switch (chart_type) {
      case 'line':
        return (
          <ResponsiveContainer width="100%" height="100%">
            <LineChart {...chartProps}>
              <CartesianGrid strokeDasharray="3 3" opacity={0.3} />
              <XAxis 
                dataKey={safeRechartsConfig.xAxisKey || safeDataColumns[0]} 
                tick={axisTickStyle}
                tickLine={axisLineStyle}
                axisLine={axisLineStyle}
                label={xAxisLabelProps}
              />
              <YAxis 
                tick={axisTickStyle}
                tickLine={axisLineStyle}
                axisLine={axisLineStyle}
                label={yAxisLabelProps}
              />
              <Tooltip 
                contentStyle={{
                  backgroundColor: '#ffffff',
                  border: '1px solid #cbd5e1',
                  borderRadius: '12px',
                  color: '#0f172a',
                  boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.3), 0 10px 10px -5px rgba(0, 0, 0, 0.2)',
                  fontSize: '14px',
                  fontWeight: '600',
                  padding: '10px 14px'
                }}
                itemStyle={{ color: '#0f172a', fontWeight: '600' }}
                labelStyle={{ color: '#2563eb', fontWeight: '700', marginBottom: '4px' }}
                cursor={{ stroke: colors[0], strokeWidth: 2, strokeDasharray: '5 5' }}
              />
              <Legend />
              <Line
                type="monotone"
                dataKey={safeRechartsConfig.dataKey || safeDataColumns[1]}
                stroke={colors[0]}
                strokeWidth={3}
                dot={{ fill: colors[0], strokeWidth: 2, r: 4 }}
                activeDot={{ r: 6, fill: colors[0], stroke: '#ffffff', strokeWidth: 2 }}
                connectNulls={false}
              >
                {showDataLabels && (
                  <LabelList 
                    dataKey={safeRechartsConfig.dataKey || safeDataColumns[1]} 
                    position="top" 
                    fill="#cbd5e1" 
                    fontSize={10} 
                  />
                )}
              </Line>
            </LineChart>
          </ResponsiveContainer>
        );

      case 'area':
        return (
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart {...chartProps}>
              <CartesianGrid strokeDasharray="3 3" opacity={0.3} />
              <XAxis 
                dataKey={safeRechartsConfig.xAxisKey || safeDataColumns[0]} 
                tick={axisTickStyle}
                tickLine={axisLineStyle}
                axisLine={axisLineStyle}
                label={xAxisLabelProps}
              />
              <YAxis 
                tick={axisTickStyle}
                tickLine={axisLineStyle}
                axisLine={axisLineStyle}
                label={yAxisLabelProps}
              />
              <Tooltip 
                contentStyle={{
                  backgroundColor: '#ffffff',
                  border: '1px solid #cbd5e1',
                  borderRadius: '12px',
                  color: '#0f172a',
                  boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.3), 0 10px 10px -5px rgba(0, 0, 0, 0.2)',
                  fontSize: '14px',
                  fontWeight: '600',
                  padding: '10px 14px'
                }}
                itemStyle={{ color: '#0f172a', fontWeight: '600' }}
                labelStyle={{ color: '#2563eb', fontWeight: '700', marginBottom: '4px' }}
                cursor={{ stroke: colors[0], strokeWidth: 2, strokeDasharray: '5 5' }}
              />
              <Legend />
              <Area
                type="monotone"
                dataKey={safeRechartsConfig.dataKey || safeDataColumns[1]}
                stroke={colors[0]}
                fill={colors[0]}
                fillOpacity={0.3}
                strokeWidth={3}
                dot={{ fill: colors[0], strokeWidth: 2, r: 4 }}
                activeDot={{ r: 6, fill: colors[0], stroke: '#ffffff', strokeWidth: 2 }}
              >
                {showDataLabels && (
                  <LabelList 
                    dataKey={safeRechartsConfig.dataKey || safeDataColumns[1]} 
                    position="top" 
                    fill="#cbd5e1" 
                    fontSize={10} 
                  />
                )}
              </Area>
            </AreaChart>
          </ResponsiveContainer>
        );

      case 'bar':
        return (
          <ResponsiveContainer width="100%" height="100%">
            <BarChart {...chartProps}>
              <CartesianGrid strokeDasharray="3 3" opacity={0.3} />
              <XAxis 
                dataKey={safeRechartsConfig.xAxisKey || safeDataColumns[0]} 
                tick={axisTickStyle}
                tickLine={axisLineStyle}
                axisLine={axisLineStyle}
                label={xAxisLabelProps}
              />
              <YAxis 
                tick={axisTickStyle}
                tickLine={axisLineStyle}
                axisLine={axisLineStyle}
                label={yAxisLabelProps}
              />
              <Tooltip 
                contentStyle={{
                  backgroundColor: '#ffffff',
                  border: '1px solid #cbd5e1',
                  borderRadius: '12px',
                  color: '#0f172a',
                  boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.3), 0 10px 10px -5px rgba(0, 0, 0, 0.2)',
                  fontSize: '14px',
                  fontWeight: '600',
                  padding: '10px 14px'
                }}
                itemStyle={{ color: '#0f172a', fontWeight: '600' }}
                labelStyle={{ color: '#2563eb', fontWeight: '700', marginBottom: '4px' }}
                cursor={{ fill: 'rgba(255, 255, 255, 0.1)' }}
              />
              <Legend />
              <Bar
                dataKey={safeRechartsConfig.dataKey || safeDataColumns[1]}
                fill={colors[0]}
                radius={[4, 4, 0, 0]}
                stroke={colors[0]}
                strokeOpacity={0.8}
              >
                {showDataLabels && (
                  <LabelList 
                    dataKey={safeRechartsConfig.dataKey || safeDataColumns[1]} 
                    position="top" 
                    fill="#cbd5e1" 
                    fontSize={10} 
                  />
                )}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        );

      case 'donut':
      case 'pie':
        // Process data to reduce clutter and improve visual appeal
        const isDonut = chart_type === 'donut';
        const processedPieData = (() => {
          if (!safeData || safeData.length === 0) return [];
          
          const dataKey = (safeRechartsConfig.dataKeys && safeRechartsConfig.dataKeys[0]) || safeRechartsConfig.dataKey || safeDataColumns[1] || 'value';
          const nameKey = safeRechartsConfig.xAxisKey || safeRechartsConfig.nameKey || safeDataColumns[0] || 'name';
          
          // Sort data by value (descending)
          const sortedData = [...safeData].sort((a, b) => {
            const aVal = Number(a[dataKey]) || 0;
            const bVal = Number(b[dataKey]) || 0;
            return bVal - aVal;
          });
          
          // Calculate total for percentage calculations
          const total = sortedData.reduce((sum, item) => sum + (Number(item[dataKey]) || 0), 0);
          
          // Take top 6 items and group the rest as "Others"
          const topItems = sortedData.slice(0, 6);
          const remainingItems = sortedData.slice(6);
          
          let processedData = topItems.map(item => ({
            ...item,
            [nameKey]: item[nameKey] || item.name || 'Unknown',
            [dataKey]: Number(item[dataKey]) || 0,
            percentage: total > 0 ? ((Number(item[dataKey]) || 0) / total * 100) : 0
          }));
          
          // Add "Others" category if there are remaining items
          if (remainingItems.length > 0) {
            const othersValue = remainingItems.reduce((sum, item) => sum + (Number(item[dataKey]) || 0), 0);
            if (othersValue > 0) {
              const othersBreakdown = remainingItems.map(item => ({
                name: item[nameKey] || item.name || 'Unknown',
                value: Number(item[dataKey]) || 0,
                percentage: total > 0 ? ((Number(item[dataKey]) || 0) / total * 100) : 0
              }));
              
              processedData.push({
                [nameKey]: `Others (${remainingItems.length})`,
                [dataKey]: othersValue,
                percentage: total > 0 ? (othersValue / total * 100) : 0,
                ...({ isOthers: true, othersBreakdown: othersBreakdown } as any)
              });
            }
          }
          
          return processedData;
        })();
        
        const pieDataKey = (safeRechartsConfig.dataKeys && safeRechartsConfig.dataKeys[0]) || safeRechartsConfig.dataKey || safeDataColumns[1] || 'value';
        const pieNameKey = safeRechartsConfig.xAxisKey || safeRechartsConfig.nameKey || safeDataColumns[0] || 'name';
        
        return (
          <ResponsiveContainer width="100%" height="100%">
            <PieChart margin={{ top: 20, right: 20, bottom: 40, left: 20 }}>
              <Pie
                data={processedPieData}
                cx="50%"
                cy="45%"
                outerRadius={Math.min(chartProps.height * 0.32, 120)}
                innerRadius={isDonut ? Math.min(chartProps.height * 0.18, 65) : 0}
                fill={colors[0]}
                dataKey={pieDataKey}
                nameKey={pieNameKey}
                label={({ name, percent }) => 
                  percent > 0.05 ? `${(percent * 100).toFixed(1)}%` : ''
                }
                labelLine={false}
                stroke="#1e293b"
                strokeWidth={2}
                fontSize={11}
              >
                {processedPieData.map((entry, index) => (
                  <Cell 
                    key={`cell-${index}`} 
                    fill={colors[index % colors.length]}
                  />
                ))}
              </Pie>
              <Tooltip 
                contentStyle={{
                  backgroundColor: '#ffffff',
                  border: '1px solid #cbd5e1',
                  borderRadius: '12px',
                  color: '#0f172a',
                  boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.3), 0 10px 10px -5px rgba(0, 0, 0, 0.2)',
                  fontSize: '14px',
                  fontWeight: '600',
                  padding: '10px 14px'
                }}
                itemStyle={{ color: '#0f172a', fontWeight: '600' }}
                labelStyle={{ color: '#2563eb', fontWeight: '700', marginBottom: '4px' }}
              />
              <Legend 
                verticalAlign="bottom" 
                height={36}
                iconType="circle"
                wrapperStyle={{
                  fontSize: '11px',
                  color: '#94a3b8',
                  paddingTop: '8px'
                }}
                align="center"
              />
            </PieChart>
          </ResponsiveContainer>
        );

      case 'horizontal_bar':
        const hNameKey = safeRechartsConfig.xAxisKey || safeDataColumns[0] || 'name';
        const hDataKey = (safeRechartsConfig.dataKeys && safeRechartsConfig.dataKeys[0]) || safeDataColumns[1] || 'value';
        return (
          <ResponsiveContainer width="100%" height="100%">
            <BarChart {...chartProps} layout="vertical" margin={{ top: 15, right: 30, left: 60, bottom: 45 }}>
              <CartesianGrid strokeDasharray="3 3" opacity={0.15} horizontal={false} />
              <XAxis 
                type="number" 
                tick={axisTickStyle} 
                axisLine={axisLineStyle}
                label={{ 
                  value: yAxisTitle, 
                  position: 'insideBottom', 
                  offset: -8, 
                  fill: '#cbd5e1', 
                  fontSize: 11, 
                  fontWeight: 500 
                }}
              />
              <YAxis 
                dataKey={hNameKey} 
                type="category" 
                tick={axisTickStyle} 
                width={110} 
                axisLine={axisLineStyle}
                label={{ 
                  value: xAxisTitle, 
                  angle: -90, 
                  position: 'insideLeft', 
                  offset: -45, 
                  fill: '#cbd5e1', 
                  fontSize: 11, 
                  fontWeight: 500,
                  style: { textAnchor: 'middle' } 
                }}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#ffffff',
                  border: '1px solid #cbd5e1',
                  borderRadius: '12px',
                  color: '#0f172a',
                  boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.3), 0 10px 10px -5px rgba(0, 0, 0, 0.2)',
                  fontSize: '14px',
                  fontWeight: '600',
                  padding: '10px 14px'
                }}
                itemStyle={{ color: '#0f172a', fontWeight: '600' }}
                labelStyle={{ color: '#2563eb', fontWeight: '700', marginBottom: '4px' }}
              />
              <Bar dataKey={hDataKey} fill={colors[0] || '#06b6d4'} radius={[0, 6, 6, 0]}>
                {showDataLabels && (
                  <LabelList 
                    dataKey={hDataKey} 
                    position="right" 
                    fill="#cbd5e1" 
                    fontSize={10} 
                  />
                )}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        );

      case 'scatter':
        return (
          <ResponsiveContainer width="100%" height="100%">
            <ScatterChart {...chartProps}>
              <CartesianGrid strokeDasharray="3 3" opacity={0.3} />
              <XAxis 
                dataKey={safeRechartsConfig.xAxisKey || safeDataColumns[0]}
                type="number"
                tick={axisTickStyle}
                tickLine={axisLineStyle}
                axisLine={axisLineStyle}
                label={xAxisLabelProps}
              />
              <YAxis 
                dataKey={safeRechartsConfig.dataKey || safeDataColumns[1]}
                type="number"
                tick={axisTickStyle}
                tickLine={axisLineStyle}
                axisLine={axisLineStyle}
                label={yAxisLabelProps}
              />
              <Tooltip 
                cursor={{ strokeDasharray: '3 3', stroke: colors[0], strokeWidth: 2 }}
                contentStyle={{
                  backgroundColor: '#ffffff',
                  border: '1px solid #cbd5e1',
                  borderRadius: '12px',
                  color: '#0f172a',
                  boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.3), 0 10px 10px -5px rgba(0, 0, 0, 0.2)',
                  fontSize: '14px',
                  fontWeight: '600',
                  padding: '10px 14px'
                }}
                itemStyle={{ color: '#0f172a', fontWeight: '600' }}
                labelStyle={{ color: '#2563eb', fontWeight: '700', marginBottom: '4px' }}
              />
              <Legend />
              <Scatter
                name={title}
                data={safeData}
                fill={colors[0]}
                fillOpacity={0.8}
                stroke={colors[0]}
                strokeWidth={2}
                r={6}
              />
            </ScatterChart>
          </ResponsiveContainer>
        );

      case 'radar':
        return (
          <ResponsiveContainer width="100%" height="100%">
            <RadarChart {...chartProps}>
              <PolarGrid />
              <PolarAngleAxis dataKey={safeRechartsConfig.xAxisKey || safeDataColumns[0]} />
              <PolarRadiusAxis />
              <Tooltip 
                contentStyle={{
                  backgroundColor: '#ffffff',
                  border: '1px solid #cbd5e1',
                  borderRadius: '12px',
                  color: '#0f172a',
                  boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.3), 0 10px 10px -5px rgba(0, 0, 0, 0.2)',
                  fontSize: '14px',
                  fontWeight: '600',
                  padding: '10px 14px'
                }}
                itemStyle={{ color: '#0f172a', fontWeight: '600' }}
                labelStyle={{ color: '#2563eb', fontWeight: '700', marginBottom: '4px' }}
              />
              <Legend />
              {safeDataColumns.slice(1).map((column, index) => (
                <Radar
                  key={column}
                  name={column}
                  dataKey={column}
                  stroke={colors[index % colors.length]}
                  fill={colors[index % colors.length]}
                  fillOpacity={0.6}
                />
              ))}
            </RadarChart>
          </ResponsiveContainer>
        );

      case 'composed':
        return (
          <ResponsiveContainer width="100%" height="100%">
            <ComposedChart {...chartProps}>
              <CartesianGrid strokeDasharray="3 3" opacity={0.3} />
              <XAxis 
                dataKey={safeRechartsConfig.xAxisKey || safeDataColumns[0]}
                tick={axisTickStyle}
                tickLine={axisLineStyle}
                axisLine={axisLineStyle}
                label={xAxisLabelProps}
              />
              <YAxis 
                tick={axisTickStyle}
                tickLine={axisLineStyle}
                axisLine={axisLineStyle}
                label={yAxisLabelProps}
              />
              <Tooltip 
                contentStyle={{
                  backgroundColor: '#ffffff',
                  border: '1px solid #cbd5e1',
                  borderRadius: '12px',
                  color: '#0f172a',
                  boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.3), 0 10px 10px -5px rgba(0, 0, 0, 0.2)',
                  fontSize: '14px',
                  fontWeight: '600',
                  padding: '10px 14px'
                }}
                itemStyle={{ color: '#0f172a', fontWeight: '600' }}
                labelStyle={{ color: '#2563eb', fontWeight: '700', marginBottom: '4px' }}
              />
              <Legend />
              <Bar dataKey={safeDataColumns[1]} fill={colors[0]} radius={[4, 4, 0, 0]}>
                {showDataLabels && (
                  <LabelList 
                    dataKey={safeDataColumns[1]} 
                    position="top" 
                    fill="#cbd5e1" 
                    fontSize={10} 
                  />
                )}
              </Bar>
              {safeDataColumns.length > 2 && (
                <Line
                  type="monotone"
                  dataKey={safeDataColumns[2]}
                  stroke={colors[1]}
                  strokeWidth={3}
                  dot={{ fill: colors[1], strokeWidth: 2, r: 4 }}
                >
                  {showDataLabels && (
                    <LabelList 
                      dataKey={safeDataColumns[2]} 
                      position="top" 
                      fill="#cbd5e1" 
                      fontSize={10} 
                    />
                  )}
                </Line>
              )}
            </ComposedChart>
          </ResponsiveContainer>
        );

      case 'histogram':
        // Histogram is essentially a bar chart with binned data
        return (
          <ResponsiveContainer width="100%" height="100%">
            <BarChart {...chartProps}>
              <CartesianGrid strokeDasharray="3 3" opacity={0.3} />
              <XAxis 
                dataKey={safeRechartsConfig.xAxisKey || safeDataColumns[0]} 
                tick={axisTickStyle}
                tickLine={axisLineStyle}
                axisLine={axisLineStyle}
                label={xAxisLabelProps}
              />
              <YAxis 
                tick={axisTickStyle}
                tickLine={axisLineStyle}
                axisLine={axisLineStyle}
                label={{ 
                  value: 'Frequency', 
                  angle: -90, 
                  position: 'insideLeft', 
                  offset: -5,
                  fill: '#cbd5e1',
                  fontSize: 11,
                  fontWeight: 500,
                  style: { textAnchor: 'middle' }
                }}
              />
              <Tooltip 
                contentStyle={{
                  backgroundColor: '#ffffff',
                  border: '1px solid #cbd5e1',
                  borderRadius: '12px',
                  color: '#0f172a',
                  boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.3), 0 10px 10px -5px rgba(0, 0, 0, 0.2)',
                  fontSize: '14px',
                  fontWeight: '600',
                  padding: '10px 14px'
                }}
                itemStyle={{ color: '#0f172a', fontWeight: '600' }}
                labelStyle={{ color: '#2563eb', fontWeight: '700', marginBottom: '4px' }}
                cursor={{ fill: 'rgba(255, 255, 255, 0.1)' }}
              />
              <Bar
                dataKey={safeRechartsConfig.dataKey || 'frequency'}
                fill={colors[0]}
                stroke={colors[0]}
                strokeOpacity={0.8}
              />
            </BarChart>
          </ResponsiveContainer>
        );

      case 'heatmap':
        // For heatmap, we'll create a proper correlation matrix visualization
        return (
          <ResponsiveContainer width="100%" height="100%">
            <div className="w-full h-full relative">
              {/* Correlation Heatmap using CSS Grid */}
              <div className="absolute inset-0 p-4">
                <div className="text-white/90 text-sm font-medium mb-3">Correlation Matrix</div>
                <div className="grid gap-1" 
                     style={{ 
                       gridTemplateColumns: `repeat(${Math.sqrt(safeData.length)}, minmax(0, 1fr))`,
                       gridTemplateRows: `repeat(${Math.sqrt(safeData.length)}, minmax(0, 1fr))`
                     }}>
                  {safeData.map((cell, index) => {
                    const correlation = (cell as any).z || (cell as any).correlation || 0;
                    const intensity = Math.abs(Number(correlation));
                    const isPositive = Number(correlation) >= 0;
                    
                    return (
                      <div
                        key={index}
                        className={`
                          aspect-square flex items-center justify-center text-xs font-medium
                          border border-white/10 rounded cursor-pointer
                          transition-all duration-200 hover:scale-110 hover:z-10
                          ${isPositive ? 'bg-blue-500' : 'bg-red-500'}
                        `}
                        style={{
                          opacity: 0.3 + (intensity * 0.7),
                          color: intensity > 0.5 ? '#ffffff' : '#000000'
                        }}
                        title={`${(cell as any).x} vs ${(cell as any).y}: ${Number(correlation).toFixed(3)}`}
                      >
                        {Number(correlation).toFixed(2)}
                      </div>
                    );
                  })}
                </div>
                <div className="flex justify-between mt-3 text-xs text-white/60">
                  <span className="flex items-center">
                    <div className="w-3 h-3 bg-red-500 rounded mr-1"></div>
                    Negative
                  </span>
                  <span className="flex items-center">
                    <div className="w-3 h-3 bg-blue-500 rounded mr-1"></div>
                    Positive
                  </span>
                </div>
              </div>
            </div>
          </ResponsiveContainer>
        );

      case 'distribution_analysis':
        // Enhanced histogram with normal distribution overlay
        return (
          <ResponsiveContainer width="100%" height="100%">
            <ComposedChart {...chartProps}>
              <CartesianGrid strokeDasharray="3 3" opacity={0.3} />
              <XAxis 
                dataKey={safeRechartsConfig.xAxisKey || 'x'}
                tick={axisTickStyle}
                tickLine={axisLineStyle}
                axisLine={axisLineStyle}
                label={xAxisLabelProps}
              />
              <YAxis 
                tick={axisTickStyle}
                tickLine={axisLineStyle}
                axisLine={axisLineStyle}
                label={{
                  value: 'Density / Frequency',
                  angle: -90,
                  position: 'insideLeft',
                  offset: -5,
                  fill: '#cbd5e1',
                  fontSize: 11,
                  fontWeight: 500,
                  style: { textAnchor: 'middle' }
                }}
              />
              <Tooltip 
                contentStyle={{
                  backgroundColor: '#ffffff',
                  border: '1px solid #cbd5e1',
                  borderRadius: '12px',
                  color: '#0f172a',
                  boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.3), 0 10px 10px -5px rgba(0, 0, 0, 0.2)',
                  fontSize: '14px',
                  fontWeight: '600',
                  padding: '10px 14px'
                }}
                itemStyle={{ color: '#0f172a', fontWeight: '600' }}
                labelStyle={{ color: '#2563eb', fontWeight: '700', marginBottom: '4px' }}
              />
              <Legend />
              
              {/* Histogram bars */}
              <Bar
                dataKey="y"
                fill={colors[0]}
                radius={[2, 2, 0, 0]}
                fillOpacity={0.7}
                data={safeData.filter(d => d.type === 'histogram')}
                name="Observed Frequency"
              />
              
              {/* Normal distribution overlay */}
              <Line
                type="monotone"
                dataKey="y"
                stroke={colors[1] || '#ef4444'}
                strokeWidth={2}
                dot={false}
                data={safeData.filter(d => d.type === 'normal_fit')}
                name="Normal Distribution Fit"
                strokeDasharray="5 5"
              />
            </ComposedChart>
          </ResponsiveContainer>
        );

      case 'scatter_regression':
        // Scatter plot with regression line
        return (
          <ResponsiveContainer width="100%" height="100%">
            <ComposedChart {...chartProps}>
              <CartesianGrid strokeDasharray="3 3" opacity={0.3} />
              <XAxis 
                dataKey="x"
                type="number"
                domain={['dataMin', 'dataMax']}
                tick={axisTickStyle}
                tickLine={axisLineStyle}
                axisLine={axisLineStyle}
                label={{ 
                  value: safeRechartsConfig.xaxis_title ? formatAxisLabel(safeRechartsConfig.xaxis_title) : xAxisTitle, 
                  position: 'insideBottom', 
                  offset: -8, 
                  fill: '#cbd5e1', 
                  fontSize: 11, 
                  fontWeight: 500 
                }}
              />
              <YAxis 
                type="number"
                domain={['dataMin', 'dataMax']}
                tick={axisTickStyle}
                tickLine={axisLineStyle}
                axisLine={axisLineStyle}
                label={{ 
                  value: safeRechartsConfig.yaxis_title ? formatAxisLabel(safeRechartsConfig.yaxis_title) : yAxisTitle, 
                  angle: -90, 
                  position: 'insideLeft', 
                  offset: -5, 
                  fill: '#cbd5e1', 
                  fontSize: 11, 
                  fontWeight: 500,
                  style: { textAnchor: 'middle' }
                }}
              />
              <Tooltip 
                contentStyle={{
                  backgroundColor: '#ffffff',
                  border: '1px solid #cbd5e1',
                  borderRadius: '12px',
                  color: '#0f172a',
                  boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.3), 0 10px 10px -5px rgba(0, 0, 0, 0.2)',
                  fontSize: '14px',
                  fontWeight: '600',
                  padding: '10px 14px'
                }}
                itemStyle={{ color: '#0f172a', fontWeight: '600' }}
                labelStyle={{ color: '#2563eb', fontWeight: '700', marginBottom: '4px' }}
                formatter={(value, name) => [
                  typeof value === 'number' ? value.toFixed(3) : value,
                  name
                ]}
              />
              <Legend />
              
              {/* Scatter points */}
              <Scatter
                data={safeData.filter(d => d.type === 'scatter')}
                fill={colors[0]}
                fillOpacity={0.6}
                stroke={colors[0]}
                strokeWidth={1}
                name="Data Points"
              />
              
              {/* Regression line */}
              <Line
                type="linear"
                dataKey="y"
                stroke={colors[1] || '#ef4444'}
                strokeWidth={2}
                dot={false}
                data={safeData.filter(d => d.type === 'regression')}
                name="Regression Line"
                strokeDasharray="3 3"
              />
            </ComposedChart>
          </ResponsiveContainer>
        );

      case 'box_plot_advanced':
        // Advanced box plot with outlier detection
        return (
          <ResponsiveContainer width="100%" height="100%">
            <div className="w-full h-full relative p-4">
              <div className="text-white/90 text-sm font-medium mb-4">Distribution Analysis</div>
              <div className="flex items-end justify-around h-3/4">
                {safeData.map((boxData: any, index) => {
                  const height = chartProps.height - 120;
                  const boxHeight = height * 0.6;
                  const whiskerTop = height * 0.1;
                  const whiskerBottom = height * 0.9;
                  
                  return (
                    <div key={index} className="flex flex-col items-center relative" style={{ height }}>
                      {/* Category label */}
                      <div className="text-xs text-white/70 mb-2 text-center">
                        {boxData.category || `Category ${index + 1}`}
                      </div>
                      
                      {/* Outliers */}
                      {boxData.outliers && Array.isArray(boxData.outliers) && boxData.outliers.map((outlier: number, oIndex: number) => (
                        <div
                          key={oIndex}
                          className="w-1.5 h-1.5 bg-red-400 rounded-full absolute"
                          style={{
                            bottom: `${((Number(outlier) - Number(boxData.lower_fence)) / (Number(boxData.upper_fence) - Number(boxData.lower_fence))) * height}px`
                          }}
                          title={`Outlier: ${Number(outlier).toFixed(2)}`}
                        />
                      ))}
                      
                      {/* Upper whisker */}
                      <div 
                        className="w-0.5 bg-white/60 absolute"
                        style={{
                          height: `${whiskerTop}px`,
                          bottom: `${boxHeight + 20}px`
                        }}
                      />
                      
                      {/* Box */}
                      <div 
                        className={`border-2 border-white/60 relative`}
                        style={{
                          width: '30px',
                          height: `${boxHeight}px`,
                          backgroundColor: `${colors[index % colors.length]}40`,
                          borderColor: colors[index % colors.length]
                        }}
                      >
                        {/* Median line */}
                        <div 
                          className="absolute w-full border-t-2 border-white"
                          style={{
                            top: `${((Number(boxData.q3) - Number(boxData.median)) / (Number(boxData.q3) - Number(boxData.q1))) * boxHeight}px`
                          }}
                        />
                      </div>
                      
                      {/* Lower whisker */}
                      <div 
                        className="w-0.5 bg-white/60 absolute"
                        style={{
                          height: `${height - whiskerBottom}px`,
                          bottom: '10px'
                        }}
                      />
                      
                      {/* Statistics tooltip on hover */}
                      <div className="text-xs text-white/50 mt-1">
                        Outliers: {Number(boxData.outlier_count) || 0}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          </ResponsiveContainer>
        );

      case 'box':
        // Simplified box plot representation
        return (
          <ResponsiveContainer width="100%" height="100%">
            <div className="flex items-center justify-center h-full bg-gray-800/20 rounded-lg border border-gray-600/30">
              <div className="text-center text-white/70">
                <div className="text-lg font-semibold mb-2">Box Plot Distribution</div>
                <div className="text-sm">{description}</div>
                <div className="mt-4 text-xs text-blue-300">
                  Enhanced box plot with outlier detection available
                </div>
              </div>
            </div>
          </ResponsiveContainer>
        );

      default:
        return (
          <div className="flex items-center justify-center h-64 text-gray-500">
            <p>Unsupported chart type: {chart_type}</p>
          </div>
        );
    }
  };

  return (
    <Card className={`${className} w-full h-full flex flex-col bg-white/5 border-white/20 hover:bg-white/10 transition-all duration-300 hover:shadow-lg hover:shadow-blue-500/10`}>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="text-white text-lg font-semibold">{title}</CardTitle>
            <CardDescription className="text-white/70 text-sm">
              {description}
              {chart_type === 'pie' && safeData.length > 6 && (
                <span className="block text-xs text-blue-300 mt-1">
                  💡 Hover over "Others 🔍" to see detailed breakdown
                </span>
              )}
            </CardDescription>
          </div>
          <div className="flex items-center space-x-2">
            <Badge 
              variant="outline" 
              className="border-blue-400/30 text-blue-300 bg-blue-500/10 hover:bg-blue-500/20 transition-colors duration-200"
            >
              {chart_type}
            </Badge>
            <Badge 
              variant="outline" 
              className={`border-opacity-30 transition-colors duration-200 ${
                confidence >= 0.8 
                  ? 'border-green-400 text-green-300 bg-green-500/10 hover:bg-green-500/20'
                  : confidence >= 0.6 
                  ? 'border-yellow-400 text-yellow-300 bg-yellow-500/10 hover:bg-yellow-500/20'
                  : 'border-red-400 text-red-300 bg-red-500/10 hover:bg-red-500/20'
              }`}
            >
              {Math.round(confidence * 100)}% confidence
            </Badge>
          </div>
        </div>
      </CardHeader>
      <CardContent className={`p-4 flex-1 flex flex-col min-h-0 ${chart_type === 'pie' ? 'pb-4' : ''}`}>
        <div className={`chart-container flex-1 w-full h-full min-h-[300px] relative overflow-hidden rounded-lg ${chart_type === 'pie' ? 'min-h-[400px]' : ''}`}>
          <div className="chart-animation-wrapper w-full h-full transform transition-transform duration-300 hover:scale-[1.02]">
            {renderChart()}
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

export default DynamicChart; 