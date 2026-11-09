import React, { useState, useMemo } from 'react';
import { DatasetProfile, ChartConfig, buildCustomChartConfig } from '../../services/bi-engine';
import DynamicChart from './dynamic-chart';
import { Card, CardHeader, CardTitle, CardContent } from '../ui/card';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select';
import { Badge } from '../ui/badge';
import { Popover, PopoverContent, PopoverTrigger } from '../ui/popover';
import { Command, CommandEmpty, CommandGroup, CommandInput, CommandItem, CommandList } from '../ui/command';
import { Dialog, DialogContent } from '../ui/dialog';
import { cn } from '@/lib/utils';
import { BarChart3, Plus, X, Sparkles, Filter, Sliders, Layers, Check, ChevronsUpDown } from 'lucide-react';

interface CustomChartBuilderProps {
  data: Record<string, any>[];
  profile: DatasetProfile;
  isOpen: boolean;
  onClose: () => void;
  onAddChart: (chart: ChartConfig) => void;
}

export const CustomChartBuilder: React.FC<CustomChartBuilderProps> = ({
  data,
  profile,
  isOpen,
  onClose,
  onAddChart,
}) => {
  const allColumns = useMemo(() => profile ? profile.columns.map(c => c.name) : [], [profile]);
  const numericColumns = useMemo(() => profile ? profile.numericColumns : [], [profile]);
  const categoricalColumns = useMemo(() => profile ? profile.categoricalColumns : [], [profile]);

  // Default selections
  const defaultX = profile?.primaryDimension || categoricalColumns[0] || allColumns[0] || 'Category';
  const defaultY = profile?.primaryMetric || numericColumns[0] || '__count__';

  const [chartType, setChartType] = useState<'bar' | 'horizontal_bar' | 'line' | 'area' | 'pie' | 'donut' | 'composed'>('bar');
  const [xAxisCol, setXAxisCol] = useState<string>(defaultX);
  const [yAxisCol, setYAxisCol] = useState<string>(defaultY);
  const [secondaryYAxisCol, setSecondaryYAxisCol] = useState<string>('none');
  const [aggregation, setAggregation] = useState<'sum' | 'mean' | 'count' | 'min' | 'max'>('sum');
  const [sortOrder, setSortOrder] = useState<'desc' | 'asc' | 'alpha'>('desc');
  const [limit, setLimit] = useState<number>(10);
  const [customTitle, setCustomTitle] = useState<string>('');

  // Per-chart optional filter
  const [filterCol, setFilterCol] = useState<string>('none');
  const [filterVals, setFilterVals] = useState<string[]>([]);
  const [filterOpen, setFilterOpen] = useState(false);

  // Values for filter dropdown if selected
  const filterOptions = useMemo(() => {
    if (filterCol === 'none' || !data) return [];
    const unique = new Set<string>();
    data.forEach(r => {
      const val = String(r[filterCol] ?? '').trim();
      if (val) unique.add(val);
    });
    return Array.from(unique).sort().slice(0, 100); // Allow up to 100 options
  }, [data, filterCol]);

  // Live generated chart config
  const previewChartConfig = useMemo(() => {
    if (!xAxisCol || !data || data.length === 0 || !profile) return null;

    return buildCustomChartConfig(data, profile, {
      title: customTitle.trim() || undefined,
      chart_type: chartType,
      xAxisCol,
      yAxisCol,
      secondaryYAxisCol: secondaryYAxisCol !== 'none' ? secondaryYAxisCol : undefined,
      aggregation,
      sortOrder,
      limit,
      filterCol: filterCol !== 'none' ? filterCol : undefined,
      filterVal: filterVals.length > 0 ? filterVals : undefined,
    });
  }, [data, profile, customTitle, chartType, xAxisCol, yAxisCol, secondaryYAxisCol, aggregation, sortOrder, limit, filterCol, filterVals]);

  if (!isOpen) return null;

  const handleCreateChart = () => {
    if (previewChartConfig) {
      onAddChart(previewChartConfig);
      onClose();
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={(open) => !open && onClose()}>
      <DialogContent
        onOpenAutoFocus={(e) => e.preventDefault()}
        className="fixed left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 z-50 w-[95vw] max-w-5xl bg-slate-900 border-slate-800 p-0 overflow-hidden shadow-2xl gap-0 max-h-[90vh] h-[90vh] md:h-auto flex flex-col [&>button]:hidden"
      >
        
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-slate-800 bg-slate-950/60 shrink-0">
          <div className="flex items-center gap-3">
            <div className="p-2.5 bg-gradient-to-tr from-indigo-500/20 to-purple-500/20 rounded-xl border border-indigo-500/30">
              <BarChart3 className="w-6 h-6 text-indigo-400" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-white flex items-center gap-2">
                Custom Chart Studio
                <Badge variant="outline" className="border-indigo-500/40 text-indigo-300 bg-indigo-500/10 text-xs">
                  Data-Driven
                </Badge>
              </h2>
              <p className="text-xs text-slate-400">
                Create unlimited custom visual analytics powered by active dataset column metrics
              </p>
            </div>
          </div>
          <Button
            variant="ghost"
            size="sm"
            onClick={onClose}
            className="text-slate-400 hover:text-white rounded-lg"
          >
            <X className="w-5 h-5" />
          </Button>
        </div>

        {/* Studio Content Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 p-6 flex-1 overflow-y-auto min-h-0">
          
          {/* Controls Panel (Left 5 Cols) */}
          <div className="lg:col-span-5 space-y-5 bg-slate-950/40 p-5 rounded-xl border border-slate-800/80">
            
            {/* Chart Title */}
            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-slate-300 flex items-center gap-1.5">
                <Sparkles className="w-3.5 h-3.5 text-indigo-400" />
                Chart Title
              </label>
              <Input
                placeholder={previewChartConfig ? previewChartConfig.title : 'e.g. Sales by State'}
                value={customTitle}
                onChange={e => setCustomTitle(e.target.value)}
                className="bg-slate-900 border-slate-700 text-xs text-white"
              />
            </div>

            {/* Chart Type Selection */}
            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-slate-300 flex items-center gap-1.5">
                <Layers className="w-3.5 h-3.5 text-blue-400" />
                Chart Type
              </label>
              <Select value={chartType} onValueChange={(val: any) => setChartType(val)}>
                <SelectTrigger className="bg-slate-900 border-slate-700 text-xs text-white">
                  <SelectValue placeholder="Select chart type" />
                </SelectTrigger>
                <SelectContent position="popper" className="bg-slate-900 border-slate-700 text-white text-xs">
                  <SelectItem value="bar">📊 Vertical Bar Chart</SelectItem>
                  <SelectItem value="horizontal_bar">📋 Horizontal Ranking Bar</SelectItem>
                  <SelectItem value="line">📈 Line Trend Chart</SelectItem>
                  <SelectItem value="area">🌊 Filled Area Chart</SelectItem>
                  <SelectItem value="donut">🍩 Donut Share Chart</SelectItem>
                  <SelectItem value="pie">🥧 Pie Share Chart</SelectItem>
                  <SelectItem value="composed">🔀 Composed Multi-Metric Chart</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {/* X-Axis / Grouping Column */}
            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-slate-300">
                Group By / X-Axis Column
              </label>
              <Select value={xAxisCol} onValueChange={setXAxisCol}>
                <SelectTrigger className="bg-slate-900 border-slate-700 text-xs text-white">
                  <SelectValue placeholder="Select grouping column" />
                </SelectTrigger>
                <SelectContent position="popper" className="bg-slate-900 border-slate-700 text-white text-xs max-h-60">
                  {allColumns.map(col => (
                    <SelectItem key={col} value={col}>
                      {col} {categoricalColumns.includes(col) ? '(Category)' : numericColumns.includes(col) ? '(Metric)' : ''}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* Y-Axis / Metric Column & Aggregation */}
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-slate-300">
                  Y-Axis Metric
                </label>
                <Select value={yAxisCol} onValueChange={setYAxisCol}>
                  <SelectTrigger className="bg-slate-900 border-slate-700 text-xs text-white">
                    <SelectValue placeholder="Select metric" />
                  </SelectTrigger>
                  <SelectContent position="popper" className="bg-slate-900 border-slate-700 text-white text-xs max-h-60">
                    <SelectItem value="__count__">🔢 Record Count (Frequency)</SelectItem>
                    {numericColumns.map(col => (
                      <SelectItem key={col} value={col}>
                        {col}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-slate-300">
                  Aggregation
                </label>
                <Select value={aggregation} onValueChange={(val: any) => setAggregation(val)}>
                  <SelectTrigger className="bg-slate-900 border-slate-700 text-xs text-white">
                    <SelectValue placeholder="Select aggregation" />
                  </SelectTrigger>
                  <SelectContent position="popper" className="bg-slate-900 border-slate-700 text-white text-xs">
                    <SelectItem value="sum">Sum (Total)</SelectItem>
                    <SelectItem value="mean">Average (Mean)</SelectItem>
                    <SelectItem value="count">Count (Entries)</SelectItem>
                    <SelectItem value="min">Minimum</SelectItem>
                    <SelectItem value="max">Maximum</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            {/* Secondary Metric for Composed Chart */}
            {chartType === 'composed' && (
              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-slate-300">
                  Secondary Metric (Line Overlay)
                </label>
                <Select value={secondaryYAxisCol} onValueChange={setSecondaryYAxisCol}>
                  <SelectTrigger className="bg-slate-900 border-slate-700 text-xs text-white">
                    <SelectValue placeholder="None" />
                  </SelectTrigger>
                  <SelectContent position="popper" className="bg-slate-900 border-slate-700 text-white text-xs">
                    <SelectItem value="none">None</SelectItem>
                    {numericColumns.map(col => (
                      <SelectItem key={col} value={col}>{col}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            )}

            {/* Sort & Limit */}
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-slate-300">
                  Sorting
                </label>
                <Select value={sortOrder} onValueChange={(val: any) => setSortOrder(val)}>
                  <SelectTrigger className="bg-slate-900 border-slate-700 text-xs text-white">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent position="popper" className="bg-slate-900 border-slate-700 text-white text-xs">
                    <SelectItem value="desc">Highest First</SelectItem>
                    <SelectItem value="asc">Lowest First</SelectItem>
                    <SelectItem value="alpha">Alphabetical (A-Z)</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-slate-300">
                  Limit Rows
                </label>
                <Select value={String(limit)} onValueChange={val => setLimit(Number(val))}>
                  <SelectTrigger className="bg-slate-900 border-slate-700 text-xs text-white">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent position="popper" className="bg-slate-900 border-slate-700 text-white text-xs">
                    <SelectItem value="5">Top 5</SelectItem>
                    <SelectItem value="10">Top 10</SelectItem>
                    <SelectItem value="20">Top 20</SelectItem>
                    <SelectItem value="0">All Items</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            {/* Per-Chart Filter Option */}
            <div className="pt-2 border-t border-slate-800 space-y-2">
              <label className="text-xs font-semibold text-slate-300 flex items-center gap-1.5">
                <Filter className="w-3.5 h-3.5 text-emerald-400" />
                Optional Chart Filter
              </label>
              <div className="grid grid-cols-2 gap-2">
                <Select value={filterCol} onValueChange={val => { setFilterCol(val); setFilterVals([]); }}>
                  <SelectTrigger className="bg-slate-900 border-slate-700 text-xs text-white">
                    <SelectValue placeholder="No filter" />
                  </SelectTrigger>
                  <SelectContent position="popper" className="bg-slate-900 border-slate-700 text-white text-xs">
                    <SelectItem value="none">All Data</SelectItem>
                    {allColumns.map(col => (
                      <SelectItem key={col} value={col}>{col}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>

                {filterCol !== 'none' && (
                  <Popover open={filterOpen} onOpenChange={setFilterOpen}>
                    <PopoverTrigger asChild>
                      <Button
                        variant="outline"
                        role="combobox"
                        aria-expanded={filterOpen}
                        className="w-full justify-between bg-slate-900 border-slate-700 text-xs text-white px-3 font-normal h-8"
                      >
                        <span className="truncate">
                          {filterVals.length === 0 ? 'All Values' : 
                           filterVals.length === 1 ? filterVals[0] : 
                           `${filterVals.length} selected`}
                        </span>
                        <ChevronsUpDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />
                      </Button>
                    </PopoverTrigger>
                    <PopoverContent className="w-full p-0 bg-slate-900 border-slate-700" align="start">
                      <Command className="bg-slate-900 text-white">
                        <CommandInput placeholder="Search values..." className="text-xs h-8" />
                        <CommandList>
                          <CommandEmpty>No value found.</CommandEmpty>
                          <CommandGroup>
                            <CommandItem
                              onSelect={() => setFilterVals([])}
                              className="text-xs text-white hover:bg-slate-800"
                            >
                              <div className={cn(
                                "mr-2 flex h-4 w-4 items-center justify-center rounded-sm border border-slate-600",
                                filterVals.length === 0 ? "bg-emerald-500 border-emerald-500" : "opacity-50"
                              )}>
                                {filterVals.length === 0 && <Check className="h-3 w-3 text-white" />}
                              </div>
                              All Values (Clear)
                            </CommandItem>
                            {filterOptions.map((opt) => {
                              const isSelected = filterVals.includes(opt);
                              return (
                                <CommandItem
                                  key={opt}
                                  value={opt}
                                  onSelect={() => {
                                    setFilterVals(prev =>
                                      isSelected
                                        ? prev.filter((val) => val !== opt)
                                        : [...prev, opt]
                                    );
                                  }}
                                  className="text-xs text-white hover:bg-slate-800"
                                >
                                  <div className={cn(
                                    "mr-2 flex h-4 w-4 items-center justify-center rounded-sm border",
                                    isSelected 
                                      ? "bg-indigo-500 border-indigo-500" 
                                      : "border-slate-600 opacity-50"
                                  )}>
                                    {isSelected && <Check className="h-3 w-3 text-white" />}
                                  </div>
                                  <span className="truncate">{opt}</span>
                                </CommandItem>
                              );
                            })}
                          </CommandGroup>
                        </CommandList>
                      </Command>
                    </PopoverContent>
                  </Popover>
                )}
              </div>
            </div>

          </div>

          {/* Live Preview Panel (Right 7 Cols) */}
          <div className="lg:col-span-7 flex flex-col space-y-4">
            <Card className="bg-slate-950 border-slate-800 p-4 flex-1 flex flex-col min-h-[400px]">
              <div className="flex items-center justify-between mb-4 pb-2 border-b border-slate-800">
                <div className="flex items-center gap-2">
                  <Sliders className="w-4 h-4 text-emerald-400" />
                  <span className="text-xs font-semibold text-slate-300">Live Preview</span>
                </div>
                {previewChartConfig && (
                  <Badge variant="outline" className="border-emerald-500/40 text-emerald-300 bg-emerald-500/10 text-xs">
                    {previewChartConfig.data.length} Data Groups
                  </Badge>
                )}
              </div>

              {previewChartConfig && previewChartConfig.data.length > 0 ? (
                <div className="flex-1 w-full min-h-[320px]">
                  <DynamicChart chartConfig={previewChartConfig} data={previewChartConfig.data} />
                </div>
              ) : (
                <div className="flex-1 flex flex-col items-center justify-center text-center p-8 text-slate-500">
                  <BarChart3 className="w-10 h-10 mx-auto mb-2 opacity-40 text-indigo-400" />
                  <p className="text-xs">Select columns and metrics to preview your custom chart</p>
                </div>
              )}
            </Card>

            {/* Action Footer */}
            <div className="flex items-center justify-end gap-3 pt-2 border-t border-slate-800">
              <Button
                variant="outline"
                onClick={onClose}
                className="border-slate-700 text-slate-300 hover:bg-slate-800 text-xs"
              >
                Cancel
              </Button>
              <Button
                onClick={handleCreateChart}
                disabled={!previewChartConfig || previewChartConfig.data.length === 0}
                className="bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 text-white font-medium text-xs gap-2 px-5 py-2.5 shadow-lg shadow-indigo-500/20"
              >
                <Plus className="w-4 h-4" />
                Add Chart to Dashboard
              </Button>
            </div>
          </div>

        </div>
      </DialogContent>
    </Dialog>
  );
};

export default CustomChartBuilder;
