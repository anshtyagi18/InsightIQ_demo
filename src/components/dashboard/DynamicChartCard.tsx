import React, { useState, useMemo } from 'react';
import { ChartConfig } from '../../services/bi-engine';
import DynamicChart from './dynamic-chart';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../ui/card';
import { Button } from '../ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select';
import { Badge } from '../ui/badge';
import { exportToCSV, exportToJSON } from '../../services/export-utility';
import { Download, Trash2, X, Tag } from 'lucide-react';
import { ExcelChartFilter, ColumnFilterState, applyExcelFilters, isFilterActive, getFilterBadgeText } from './ExcelChartFilter';

interface DynamicChartCardProps {
  chart: ChartConfig;
  onUpdateChart?: (updatedChart: ChartConfig) => void;
  onDeleteChart?: (chartId: string) => void;
  datasetName?: string;
}

export const DynamicChartCard: React.FC<DynamicChartCardProps> = ({
  chart,
  onUpdateChart,
  onDeleteChart,
  datasetName = 'Dataset',
}) => {
  const [currentChartType, setCurrentChartType] = useState<ChartConfig['chart_type']>(chart.chart_type);
  const [activeFilters, setActiveFilters] = useState<ColumnFilterState>({});
  const [showDataLabels, setShowDataLabels] = useState<boolean>(
    Boolean(chart.recharts_config?.showDataLabels || (chart as any).showDataLabels)
  );

  // Detect available columns in the chart data for filtering
  const availableColumns = useMemo(() => {
    const rawData = chart.data || [];
    if (rawData.length === 0) return chart.xAxis ? [chart.xAxis] : [];
    
    // Get all column names from first row
    const cols = Object.keys(rawData[0] || {});
    
    // Sort so xAxis comes first if present, followed by others
    if (chart.xAxis && cols.includes(chart.xAxis)) {
      return [chart.xAxis, ...cols.filter(c => c !== chart.xAxis)];
    }
    return cols;
  }, [chart.data, chart.xAxis]);

  // Filter chart data dynamically based on multi-column Excel filter selections and rules
  const filteredData = useMemo(() => {
    const rawData = chart.data || [];
    return applyExcelFilters(rawData, activeFilters);
  }, [chart.data, activeFilters]);

  // Active chart config with potential modified type and data labels state
  const activeConfig: ChartConfig = useMemo(() => {
    return {
      ...chart,
      chart_type: currentChartType,
      data: filteredData,
      recharts_config: {
        ...(chart.recharts_config || {}),
        showDataLabels,
      },
    };
  }, [chart, currentChartType, filteredData, showDataLabels]);

  // Handle Chart Type Toggle
  const handleTypeChange = (newType: ChartConfig['chart_type']) => {
    setCurrentChartType(newType);
    if (onUpdateChart) {
      onUpdateChart({ ...chart, chart_type: newType });
    }
  };

  // Export Individual Chart Data
  const handleExportCSV = () => {
    const filename = `${chart.title.replace(/[^a-zA-Z0-9]/g, '_')}_data.csv`;
    exportToCSV(filteredData, filename);
  };

  const handleExportJSON = () => {
    const filename = `${chart.title.replace(/[^a-zA-Z0-9]/g, '_')}_chart.json`;
    const exportPayload = {
      chart_id: chart.id,
      title: chart.title,
      chart_type: currentChartType,
      datasetName,
      exportedAt: new Date().toISOString(),
      data: filteredData,
      activeFilters,
    };
    exportToJSON(exportPayload as any, filename);
  };

  const removeColumnFilter = (col: string) => {
    setActiveFilters(prev => {
      const copy = { ...prev };
      delete copy[col];
      return copy;
    });
  };

  const resetAllFilters = () => {
    setActiveFilters({});
  };

  const activeFilterColumns = Object.keys(activeFilters).filter(
    k => isFilterActive(activeFilters[k])
  );

  const totalRawRows = chart.data?.length || 0;
  const isFiltered = activeFilterColumns.length > 0;

  return (
    <Card className="bg-slate-900/90 border-slate-800 hover:border-slate-700/80 transition-all duration-300 shadow-xl overflow-hidden flex flex-col justify-between">
      
      {/* Header */}
      <CardHeader className="pb-3 border-b border-slate-800/60 bg-slate-950/40">
        <div className="flex items-start justify-between gap-4">
          
          <div className="space-y-1">
            <div className="flex items-center gap-2 flex-wrap">
              <CardTitle className="text-white text-base font-semibold tracking-tight">
                {chart.title}
              </CardTitle>
              {isFiltered && (
                <Badge variant="outline" className="border-emerald-500/40 text-emerald-300 bg-emerald-500/10 text-[10px]">
                  Filtered ({filteredData.length}/{totalRawRows} rows)
                </Badge>
              )}
            </div>
            <CardDescription className="text-slate-400 text-xs line-clamp-2">
              {chart.description}
            </CardDescription>
          </div>

          {/* Quick Action Controls */}
          <div className="flex items-center gap-1.5 shrink-0">
            
            {/* Chart Type Quick Switcher */}
            <Select value={currentChartType} onValueChange={(val: any) => handleTypeChange(val)}>
              <SelectTrigger className="h-7 w-28 bg-slate-950 border-slate-700 text-slate-300 text-[11px] px-2">
                <SelectValue />
              </SelectTrigger>
              <SelectContent position="popper" className="bg-slate-900 border-slate-700 text-white text-xs z-50">
                <SelectItem value="bar">📊 Bar Chart</SelectItem>
                <SelectItem value="horizontal_bar">📋 Horiz. Bar</SelectItem>
                <SelectItem value="line">📈 Line Chart</SelectItem>
                <SelectItem value="area">🌊 Area Chart</SelectItem>
                <SelectItem value="donut">🍩 Donut Chart</SelectItem>
                <SelectItem value="pie">🥧 Pie Chart</SelectItem>
                <SelectItem value="composed">🔀 Composed</SelectItem>
              </SelectContent>
            </Select>

            {/* Toggle Data Labels Control */}
            <Button
              variant={showDataLabels ? "secondary" : "ghost"}
              size="sm"
              onClick={() => setShowDataLabels(!showDataLabels)}
              className={`h-7 px-2 text-[11px] gap-1 transition-all ${
                showDataLabels 
                  ? 'bg-blue-600/30 text-blue-300 border border-blue-500/50 hover:bg-blue-600/40' 
                  : 'text-slate-400 hover:text-white hover:bg-slate-800/60'
              }`}
              title={showDataLabels ? "Hide Data Labels on chart" : "Show Data Labels on chart"}
            >
              <Tag className="w-3 h-3" />
              <span>Labels</span>
            </Button>

            {/* Excel-style Filter Component */}
            <ExcelChartFilter
              data={chart.data || []}
              availableColumns={availableColumns}
              activeFilters={activeFilters}
              onApplyFilters={setActiveFilters}
              onResetAllFilters={resetAllFilters}
              defaultColumn={chart.xAxis}
            />

            {/* Individual Export Dropdown */}
            <div className="relative group">
              <Button
                variant="ghost"
                size="icon"
                onClick={handleExportCSV}
                className="h-7 w-7 text-slate-400 hover:text-white"
                title="Export Chart Data (CSV)"
              >
                <Download className="w-3.5 h-3.5" />
              </Button>
            </div>

            {/* Remove Chart */}
            {onDeleteChart && (
              <Button
                variant="ghost"
                size="icon"
                onClick={() => onDeleteChart(chart.id)}
                className="h-7 w-7 text-slate-400 hover:text-red-400"
                title="Delete chart"
              >
                <Trash2 className="w-3.5 h-3.5" />
              </Button>
            )}

          </div>

        </div>

        {/* Active Applied Filters Chips Bar */}
        {isFiltered && (
          <div className="mt-2 pt-2 border-t border-slate-800/60 flex items-center gap-1.5 flex-wrap">
            <span className="text-[10px] uppercase font-semibold tracking-wider text-slate-500 mr-1">
              Active Filters:
            </span>
            {activeFilterColumns.map(col => {
              const badgeText = getFilterBadgeText(col, activeFilters[col]);
              return (
                <div
                  key={col}
                  className="inline-flex items-center gap-1 bg-slate-950 border border-slate-700/80 rounded px-1.5 py-0.5 text-[11px] text-slate-300"
                >
                  <span className="text-emerald-400 font-medium">{col}:</span>
                  <span>{badgeText}</span>
                  <button
                    type="button"
                    onClick={() => removeColumnFilter(col)}
                    className="ml-0.5 text-slate-400 hover:text-white"
                    title={`Remove ${col} filter`}
                  >
                    <X className="w-2.5 h-2.5" />
                  </button>
                </div>
              );
            })}
            <button
              type="button"
              onClick={resetAllFilters}
              className="text-[10px] text-slate-400 hover:text-red-400 underline ml-auto"
            >
              Reset All
            </button>
          </div>
        )}
      </CardHeader>

      {/* Chart Canvas */}
      <CardContent className="p-4 pt-5 flex-1 flex flex-col min-h-0">
        <div className="w-full h-full min-h-[300px]">
          <DynamicChart chartConfig={activeConfig} data={filteredData as any} />
        </div>
      </CardContent>

    </Card>
  );
};

export default DynamicChartCard;
