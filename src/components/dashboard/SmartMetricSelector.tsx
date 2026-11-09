import React, { useState, useEffect, useMemo, useRef } from 'react';
import { 
  CheckCircle, 
  Circle, 
  Info, 
  Search, 
  Filter, 
  Hash, 
  Calendar, 
  BarChart3, 
  Tag, 
  TrendingUp,
  Eye,
  EyeOff,
  CheckCircle2,
  AlertCircle,
  Plus,
  X,
  ArrowRight,
  Shuffle,
  Target,
  Zap,
  Lightbulb,
  RefreshCw
} from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Checkbox } from "@/components/ui/checkbox";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";

interface ColumnClassification {
  column_name: string;
  column_type: 'numeric' | 'categorical' | 'date' | 'other';
  business_context: string;
  business_context_display?: string;
  is_key_metric: boolean;
  sample_values: string[];
  null_count: number;
  unique_count: number;
  recommended: boolean;
  data_quality?: 'good' | 'issues';
}

interface FileAnalysisResponse {
  file_metadata: {
    filename: string;
    total_rows: number;
    total_columns: number;
    sheet_name: string;
    file_size_mb: number;
  };
  column_classifications: ColumnClassification[];
  summary: {
    total_analyzable_columns: number;
    key_metrics_count: number;
    recommended_count: number;
    numeric_columns: number;
    categorical_columns: number;
    date_columns: number;
  };
}

interface MetricPair {
  id: string;
  xAxis: ColumnClassification | null;
  yAxis: ColumnClassification | null;
  chartType: 'scatter' | 'bar' | 'line' | 'area' | 'auto';
  name?: string;
}

interface SmartMetricSelectorProps {
  fileAnalysis: FileAnalysisResponse;
  selectedMetrics: string[]; // Legacy prop for compatibility
  onMetricsChange: (metrics: string[]) => void; // Legacy prop for compatibility  
  onMetricPairsChange?: (pairs: MetricPair[]) => void; // New prop for pairs
  onGenerate: () => void;
  isGenerating?: boolean;
  className?: string;
}

interface MetricGroup {
  title: string;
  description: string;
  icon: React.ReactNode;
  columns: ColumnClassification[];
  color: string;
  bgColor: string;
}

export function SmartMetricSelector({
  fileAnalysis,
  selectedMetrics = [], // Legacy compatibility
  onMetricsChange,
  onMetricPairsChange,
  onGenerate,
  isGenerating = false,
  className = ''
}: SmartMetricSelectorProps) {
  const [searchTerm, setSearchTerm] = useState('');
  const [metricPairs, setMetricPairs] = useState<MetricPair[]>([]);
  const [mode, setMode] = useState<'pairs' | 'individual'>('pairs');
  const [autoSuggestEnabled, setAutoSuggestEnabled] = useState(true);
  
  // Prevent layout jump when Select opens by restoring scroll position
  const pageScrollYRef = useRef(0);
  const handleSelectOpenChange = (open: boolean) => {
    if (open) {
      pageScrollYRef.current = window.scrollY;
      // Restore scroll position on next frame
      requestAnimationFrame(() => {
        window.scrollTo({ top: pageScrollYRef.current });
      });
    }
  };
  
  // Ref to track the newly added pair for scrolling
  const newPairRef = useRef<string | null>(null);
  const pairRefs = useRef<{[key: string]: HTMLDivElement | null}>({});

  // Scroll to newly added pair
  useEffect(() => {
    if (newPairRef.current && pairRefs.current[newPairRef.current]) {
      const element = pairRefs.current[newPairRef.current];
      if (element) {
        setTimeout(() => {
          element.scrollIntoView({ 
            behavior: 'smooth', 
            block: 'nearest',
            inline: 'nearest'
          });
          // Clear the ref after scrolling
          newPairRef.current = null;
        }, 100); // Small delay to ensure DOM is updated
      }
    }
  }, [metricPairs.length]);

  // Create metric groups for easier selection
  const metricGroups = useMemo((): MetricGroup[] => {
    const { column_classifications } = fileAnalysis;
    
    const keyMetrics = column_classifications.filter(col => col.is_key_metric);
    const numericColumns = column_classifications.filter(col => 
      col.column_type === 'numeric' && !col.is_key_metric
    );
    const dateColumns = column_classifications.filter(col => col.column_type === 'date');
    const categoricalColumns = column_classifications.filter(col => col.column_type === 'categorical');

    return [
      {
        title: 'Key Business Metrics',
        description: 'Primary revenue, quantity, and performance metrics',
        icon: <TrendingUp className="w-4 h-4" />,
        columns: keyMetrics,
        color: 'text-green-400',
        bgColor: 'bg-green-500/10 border-green-500/30'
      },
      {
        title: 'Numeric Data',
        description: 'Quantitative data suitable for Y-axis values',
        icon: <Hash className="w-4 h-4" />,
        columns: numericColumns,
        color: 'text-blue-400',
        bgColor: 'bg-blue-500/10 border-blue-500/30'
      },
      {
        title: 'Categories',
        description: 'Perfect for X-axis grouping and segmentation',
        icon: <Tag className="w-4 h-4" />,
        columns: categoricalColumns,
        color: 'text-orange-400',
        bgColor: 'bg-orange-500/10 border-orange-500/30'
      },
      {
        title: 'Date & Time',
        description: 'Temporal data for time-series analysis',
        icon: <Calendar className="w-4 h-4" />,
        columns: dateColumns,
        color: 'text-purple-400',
        bgColor: 'bg-purple-500/10 border-purple-500/30'
      }
    ].filter(group => group.columns.length > 0);
  }, [fileAnalysis]);

  // Auto-suggest smart pairs based on data analysis
  const autoSuggestPairs = () => {
    const { column_classifications } = fileAnalysis;
    const suggested: MetricPair[] = [];
    
    // Strategy 1: Key metrics vs categories
    const keyMetrics = column_classifications.filter(col => col.is_key_metric);
    const categories = column_classifications.filter(col => col.column_type === 'categorical');
    
    keyMetrics.slice(0, 3).forEach((metric, idx) => {
      categories.slice(0, 1).forEach(category => {
        suggested.push({
          id: `suggested-${idx}-${metric.column_name}-${category.column_name}`,
          xAxis: category,
          yAxis: metric,
          chartType: 'auto',
          name: `${metric.business_context} by ${category.business_context}`
        });
      });
    });

    // Strategy 2: Numeric correlations
    const numericCols = column_classifications.filter(col => col.column_type === 'numeric');
    if (numericCols.length >= 2) {
      for (let i = 0; i < Math.min(2, numericCols.length - 1); i++) {
        suggested.push({
          id: `correlation-${i}`,
          xAxis: numericCols[i],
          yAxis: numericCols[i + 1],
          chartType: 'scatter',
          name: `${numericCols[i].business_context} vs ${numericCols[i + 1].business_context}`
        });
      }
    }

    // Strategy 3: Time series
    const dateCols = column_classifications.filter(col => col.column_type === 'date');
    if (dateCols.length > 0 && keyMetrics.length > 0) {
      suggested.push({
        id: `timeseries-0`,
        xAxis: dateCols[0],
        yAxis: keyMetrics[0],
        chartType: 'line',
        name: `${keyMetrics[0].business_context} over time`
      });
    }

    setMetricPairs(suggested.slice(0, 5)); // Limit to 5 suggestions
  };

  // Initialize with auto-suggestions
  useEffect(() => {
    if (autoSuggestEnabled && metricPairs.length === 0) {
      autoSuggestPairs();
    }
  }, [fileAnalysis, autoSuggestEnabled]);

  // Update legacy selectedMetrics when pairs change
  useEffect(() => {
    const allMetrics = new Set<string>();
    metricPairs.forEach(pair => {
      if (pair.xAxis) allMetrics.add(pair.xAxis.column_name);
      if (pair.yAxis) allMetrics.add(pair.yAxis.column_name);
    });
    onMetricsChange(Array.from(allMetrics));
    
    // Call new callback if provided
    if (onMetricPairsChange) {
      onMetricPairsChange(metricPairs);
    }
  }, [metricPairs, onMetricsChange, onMetricPairsChange]);

  // Add new empty pair with scroll behavior
  const addNewPair = () => {
    const newPairId = `pair-${Date.now()}`;
    const newPair: MetricPair = {
      id: newPairId,
      xAxis: null,
      yAxis: null,
      chartType: 'auto'
    };
    
    // Mark this as the new pair to scroll to
    newPairRef.current = newPairId;
    setMetricPairs([...metricPairs, newPair]);
  };

  // Remove pair
  const removePair = (pairId: string) => {
    setMetricPairs(metricPairs.filter(pair => pair.id !== pairId));
  };

  // Update pair
  const updatePair = (pairId: string, updates: Partial<MetricPair>) => {
    setMetricPairs(metricPairs.map(pair => 
      pair.id === pairId ? { ...pair, ...updates } : pair
    ));
  };

  // Get available columns for selection (not already used in the same pair)
  const getAvailableColumns = (currentPairId: string, forAxis: 'x' | 'y') => {
    const currentPair = metricPairs.find(pair => pair.id === currentPairId);
    const otherAxisColumn = forAxis === 'x' ? currentPair?.yAxis : currentPair?.xAxis;
    
    return fileAnalysis.column_classifications.filter(col => {
      // Can't use the same column for both X and Y in the same pair
      if (otherAxisColumn && col.column_name === otherAxisColumn.column_name) {
        return false;
      }
      return true;
    });
  };

  // Get chart type icon
  const getChartTypeIcon = (chartType: string) => {
    switch (chartType) {
      case 'bar': return <BarChart3 className="w-4 h-4" />;
      case 'line': return <TrendingUp className="w-4 h-4" />;
      case 'scatter': return <Target className="w-4 h-4" />;
      case 'area': return <BarChart3 className="w-4 h-4" />;
      default: return <Zap className="w-4 h-4" />;
    }
  };

  // Get column type icon
  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'numeric': return <Hash className="w-4 h-4 text-blue-400" />;
      case 'categorical': return <Tag className="w-4 h-4 text-orange-400" />;
      case 'date': return <Calendar className="w-4 h-4 text-purple-400" />;
      default: return <Circle className="w-4 h-4 text-gray-400" />;
    }
  };

  // Smart chart type recommendation
  const recommendChartType = (xAxis: ColumnClassification | null, yAxis: ColumnClassification | null): 'scatter' | 'bar' | 'line' | 'area' | 'auto' => {
    if (!xAxis || !yAxis) return 'auto';
    
    if (xAxis.column_type === 'date' && yAxis.column_type === 'numeric') return 'line';
    if (xAxis.column_type === 'categorical' && yAxis.column_type === 'numeric') return 'bar';
    if (xAxis.column_type === 'numeric' && yAxis.column_type === 'numeric') return 'scatter';
    
    return 'auto';
  };

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Header */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold text-white mb-2">Smart Metric Pairing</h2>
            <p className="text-white/70">
              Select metric pairs to create meaningful chart relationships between your data columns
            </p>
          </div>
          <Button
            onClick={() => setMode(mode === 'pairs' ? 'individual' : 'pairs')}
            variant="outline"
            className="border-white/20 text-white/70 hover:bg-white/10"
          >
            <Shuffle className="w-4 h-4 mr-2" />
            {mode === 'pairs' ? 'Switch to Individual' : 'Switch to Pairs'}
          </Button>
        </div>

        {/* File Overview */}
        <Card className="bg-white/5 border-white/20">
          <CardContent className="p-4">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
              <div>
                <p className="text-white/60">File</p>
                <p className="text-white font-medium truncate">{fileAnalysis.file_metadata.filename}</p>
              </div>
              <div>
                <p className="text-white/60">Rows</p>
                <p className="text-white font-medium">{fileAnalysis.file_metadata.total_rows.toLocaleString()}</p>
              </div>
              <div>
                <p className="text-white/60">Total Columns</p>
                <p className="text-white font-medium">{fileAnalysis.file_metadata.total_columns}</p>
              </div>
              <div>
                <p className="text-white/60">Current Pairs</p>
                <p className="text-white font-medium">{metricPairs.filter(p => p.xAxis && p.yAxis).length}</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {mode === 'pairs' ? (
        <>
          {/* Auto-suggestion controls */}
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Button
                onClick={autoSuggestPairs}
                variant="outline"
                size="sm"
                className="border-blue-500/50 text-blue-400 hover:bg-blue-500/10"
              >
                <Lightbulb className="w-4 h-4 mr-2" />
                Auto-Suggest Pairs
              </Button>
              <Button
                onClick={() => setMetricPairs([])}
                variant="outline"
                size="sm"
                className="border-red-500/50 text-red-400 hover:bg-red-500/10"
              >
                <RefreshCw className="w-4 h-4 mr-2" />
                Clear All
              </Button>
            </div>
            <Button
              onClick={addNewPair}
              className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white"
            >
              <Plus className="w-4 h-4 mr-2" />
              Add Pair
            </Button>
          </div>

          {/* Pairs List */}
          <div className="space-y-4 overscroll-contain">
            {metricPairs.length === 0 ? (
              <Card className="bg-gradient-to-r from-blue-500/10 to-purple-500/10 border-blue-500/30">
                <CardContent className="p-8 text-center">
                  <div className="space-y-4">
                    <div className="w-16 h-16 bg-blue-500/20 rounded-full flex items-center justify-center mx-auto">
                      <BarChart3 className="w-8 h-8 text-blue-400" />
                    </div>
                    <div>
                      <h3 className="text-xl font-semibold text-white mb-2">Create Your First Metric Pair</h3>
                      <p className="text-white/70 mb-4">
                        Pair your data columns to create meaningful charts. For example, pair a category column (X-axis) 
                        with a numeric value (Y-axis) to show relationships.
                      </p>
                      <div className="flex flex-col sm:flex-row gap-3 justify-center">
                        <Button
                          onClick={autoSuggestPairs}
                          className="bg-gradient-to-r from-green-600 to-blue-600 hover:from-green-700 hover:to-blue-700"
                        >
                          <Lightbulb className="w-4 h-4 mr-2" />
                          Auto-Suggest Smart Pairs
                        </Button>
                        <Button
                          onClick={addNewPair}
                          variant="outline"
                          className="border-white/20 text-white hover:bg-white/10"
                        >
                          <Plus className="w-4 h-4 mr-2" />
                          Create Manual Pair
                        </Button>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ) : (
              metricPairs.map((pair, index) => (
                <Card 
                  key={pair.id} 
                  ref={(el) => {
                    pairRefs.current[pair.id] = el;
                  }}
                  className="bg-white/5 border-white/20 hover:bg-white/[0.07] transition-all duration-200"
                  data-pair-id={pair.id}
                >
                  <CardHeader className="pb-3">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <div className="w-8 h-8 bg-gradient-to-r from-blue-500/20 to-purple-500/20 rounded-lg flex items-center justify-center">
                          <span className="text-sm font-bold text-white">{index + 1}</span>
                        </div>
                        <div>
                          <CardTitle className="text-lg text-white">
                            {pair.name || `Chart Pair ${index + 1}`}
                          </CardTitle>
                          <CardDescription className="text-white/60">
                            {pair.xAxis && pair.yAxis 
                              ? `${pair.xAxis.column_name} → ${pair.yAxis.column_name}`
                              : 'Configure X and Y axes'
                            }
                          </CardDescription>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        {pair.xAxis && pair.yAxis && (
                          <Badge className="bg-green-500/20 text-green-300 border-green-500/30">
                            <CheckCircle2 className="w-3 h-3 mr-1" />
                            Ready
                          </Badge>
                        )}
                        <Button
                          onClick={() => removePair(pair.id)}
                          variant="ghost"
                          size="sm"
                          className="text-red-400 hover:bg-red-500/20 w-8 h-8 p-0"
                        >
                          <X className="w-4 h-4" />
                        </Button>
                      </div>
                    </div>
                  </CardHeader>
                  
                  <CardContent className="space-y-4">
                    <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
                      {/* X-Axis Selection */}
                      <div className="space-y-2">
                        <Label className="text-white/70 text-sm font-medium">X-Axis (Categories/Groups)</Label>
                        <Select
                          onOpenChange={handleSelectOpenChange}
                          value={pair.xAxis?.column_name || ''}
                          onValueChange={(value) => {
                            const column = fileAnalysis.column_classifications.find(col => col.column_name === value);
                            const updates: Partial<MetricPair> = { xAxis: column || null };
                            
                            // Auto-recommend chart type when both axes are selected
                            if (column && pair.yAxis) {
                              updates.chartType = recommendChartType(column, pair.yAxis);
                            }
                            
                            updatePair(pair.id, updates);
                          }}
                        >
                          <SelectTrigger className="bg-white/5 border-white/20 text-white">
                            <SelectValue placeholder="Select X-axis column..." />
                          </SelectTrigger>
                          <SelectContent portalContainer={pairRefs.current[pair.id] as unknown as HTMLElement} className="bg-gray-900 border-gray-700 z-50 max-h-72 overflow-auto">
                            {getAvailableColumns(pair.id, 'x').map((col) => (
                              <SelectItem 
                                key={col.column_name} 
                                value={col.column_name}
                                className="text-white hover:bg-gray-800"
                              >
                                <div className="flex items-center gap-2">
                                  {getTypeIcon(col.column_type)}
                                  <span>{col.column_name}</span>
                                  <Badge className="ml-auto text-xs bg-white/10 text-white/70">
                                    {col.column_type}
                                  </Badge>
                                </div>
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                        {pair.xAxis && (
                          <div className="text-xs text-white/60 pl-2">
                            {pair.xAxis.business_context} • {pair.xAxis.unique_count} unique values
                          </div>
                        )}
                      </div>

                      {/* Y-Axis Selection */}
                      <div className="space-y-2">
                        <Label className="text-white/70 text-sm font-medium">Y-Axis (Values/Metrics)</Label>
                        <Select
                          onOpenChange={handleSelectOpenChange}
                          value={pair.yAxis?.column_name || ''}
                          onValueChange={(value) => {
                            const column = fileAnalysis.column_classifications.find(col => col.column_name === value);
                            const updates: Partial<MetricPair> = { yAxis: column || null };
                            
                            // Auto-recommend chart type when both axes are selected
                            if (column && pair.xAxis) {
                              updates.chartType = recommendChartType(pair.xAxis, column);
                            }
                            
                            updatePair(pair.id, updates);
                          }}
                        >
                          <SelectTrigger className="bg-white/5 border-white/20 text-white">
                            <SelectValue placeholder="Select Y-axis column..." />
                          </SelectTrigger>
                          <SelectContent portalContainer={pairRefs.current[pair.id] as unknown as HTMLElement} className="bg-gray-900 border-gray-700 z-50 max-h-72 overflow-auto">
                            {getAvailableColumns(pair.id, 'y').map((col) => (
                              <SelectItem 
                                key={col.column_name} 
                                value={col.column_name}
                                className="text-white hover:bg-gray-800"
                              >
                                <div className="flex items-center gap-2">
                                  {getTypeIcon(col.column_type)}
                                  <span>{col.column_name}</span>
                                  <Badge className="ml-auto text-xs bg-white/10 text-white/70">
                                    {col.column_type}
                                  </Badge>
                                </div>
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                        {pair.yAxis && (
                          <div className="text-xs text-white/60 pl-2">
                            {pair.yAxis.business_context} • {pair.yAxis.is_key_metric ? 'Key Metric' : 'Standard Metric'}
                          </div>
                        )}
                      </div>

                      {/* Chart Type Selection */}
                      <div className="space-y-2">
                        <Label className="text-white/70 text-sm font-medium">Chart Type</Label>
                        <Select
                          onOpenChange={handleSelectOpenChange}
                          value={pair.chartType}
                          onValueChange={(value) => updatePair(pair.id, { chartType: value as 'scatter' | 'bar' | 'line' | 'area' | 'auto' })}
                        >
                          <SelectTrigger className="bg-white/5 border-white/20 text-white">
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent portalContainer={pairRefs.current[pair.id] as unknown as HTMLElement} className="bg-gray-900 border-gray-700 z-50 max-h-72 overflow-auto">
                            <SelectItem value="auto" className="text-white hover:bg-gray-800">
                              <div className="flex items-center gap-2">
                                <Zap className="w-4 h-4" />
                                Auto-Select
                              </div>
                            </SelectItem>
                            <SelectItem value="bar" className="text-white hover:bg-gray-800">
                              <div className="flex items-center gap-2">
                                <BarChart3 className="w-4 h-4" />
                                Bar Chart
                              </div>
                            </SelectItem>
                            <SelectItem value="line" className="text-white hover:bg-gray-800">
                              <div className="flex items-center gap-2">
                                <TrendingUp className="w-4 h-4" />
                                Line Chart
                              </div>
                            </SelectItem>
                            <SelectItem value="scatter" className="text-white hover:bg-gray-800">
                              <div className="flex items-center gap-2">
                                <Target className="w-4 h-4" />
                                Scatter Plot
                              </div>
                            </SelectItem>
                          </SelectContent>
                        </Select>
                      </div>
                    </div>

                    {/* Pair Preview */}
                    {pair.xAxis && pair.yAxis && (
                      <div className="mt-4 p-3 rounded-lg bg-gradient-to-r from-green-500/10 to-blue-500/10 border border-green-500/20">
                        <div className="flex items-center gap-3">
                          {getChartTypeIcon(pair.chartType)}
                          <div className="flex-1">
                            <div className="text-sm font-medium text-white">
                              {pair.chartType === 'auto' ? 'Smart' : pair.chartType.charAt(0).toUpperCase() + pair.chartType.slice(1)} Chart Preview
                            </div>
                            <div className="text-xs text-white/70">
                              Shows <strong>{pair.yAxis.business_context}</strong> grouped by <strong>{pair.xAxis.business_context}</strong>
                            </div>
                          </div>
                          <Badge className="bg-green-500/20 text-green-300 border-green-500/30 text-xs">
                            <CheckCircle2 className="w-3 h-3 mr-1" />
                            Ready to Generate
                          </Badge>
                        </div>
                      </div>
                    )}
                  </CardContent>
                </Card>
              ))
            )}
          </div>

          {/* Summary */}
          {metricPairs.length > 0 && (
            <Card className="bg-gradient-to-r from-blue-500/10 to-purple-500/10 border-blue-500/30">
              <CardHeader className="pb-3">
                <CardTitle className="text-white flex items-center gap-2">
                  <BarChart3 className="w-5 h-5" />
                  Dashboard Generation Summary
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
                  <div className="flex items-center gap-2">
                    <CheckCircle2 className="w-4 h-4 text-green-400" />
                    <span className="text-white/70">Configured Pairs:</span>
                    <span className="text-white font-medium">
                      {metricPairs.filter(p => p.xAxis && p.yAxis).length}
                    </span>
                  </div>
                  <div className="flex items-center gap-2">
                    <TrendingUp className="w-4 h-4 text-blue-400" />
                    <span className="text-white/70">Charts to Generate:</span>
                    <span className="text-white font-medium">
                      {metricPairs.filter(p => p.xAxis && p.yAxis).length}
                    </span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Target className="w-4 h-4 text-purple-400" />
                    <span className="text-white/70">Unique Columns:</span>
                    <span className="text-white font-medium">
                      {new Set([
                        ...metricPairs.filter(p => p.xAxis).map(p => p.xAxis!.column_name),
                        ...metricPairs.filter(p => p.yAxis).map(p => p.yAxis!.column_name)
                      ]).size}
                    </span>
                  </div>
                </div>

                {metricPairs.filter(p => p.xAxis && p.yAxis).length > 0 && (
                  <Alert className="bg-green-500/10 border-green-500/30">
                    <CheckCircle2 className="h-4 w-4 text-green-400" />
                    <AlertDescription className="text-green-200">
                      <strong>Ready to Generate!</strong> Your metric pairs will create {metricPairs.filter(p => p.xAxis && p.yAxis).length} 
                      intelligent chart{metricPairs.filter(p => p.xAxis && p.yAxis).length !== 1 ? 's' : ''} with proper X/Y axis relationships.
                    </AlertDescription>
                  </Alert>
                )}
              </CardContent>
            </Card>
          )}

          {/* Generate Button */}
          <div className="flex justify-center pt-4">
            <Button
              onClick={onGenerate}
              disabled={isGenerating || metricPairs.filter(p => p.xAxis && p.yAxis).length === 0}
              className="bg-gradient-to-r from-green-600 to-blue-600 hover:from-green-700 hover:to-blue-700 text-white px-8 py-3 text-lg font-semibold shadow-lg shadow-green-500/25"
            >
              {isGenerating ? (
                <>
                  <RefreshCw className="w-5 h-5 mr-3 animate-spin" />
                  Generating Dashboard...
                </>
              ) : (
                <>
                  <BarChart3 className="w-5 h-5 mr-3" />
                  Generate Dashboard with {metricPairs.filter(p => p.xAxis && p.yAxis).length} Chart{metricPairs.filter(p => p.xAxis && p.yAxis).length !== 1 ? 's' : ''}
                </>
              )}
            </Button>
          </div>
        </>
      ) : (
        // Legacy individual mode for backwards compatibility
        <div className="space-y-4">
          <Alert className="bg-yellow-500/10 border-yellow-500/30">
            <Info className="h-4 w-4 text-yellow-400" />
            <AlertDescription className="text-yellow-200">
              <strong>Individual Mode:</strong> This mode selects individual columns. 
              For better chart relationships, switch to Pairs Mode above.
            </AlertDescription>
          </Alert>
          
          {/* Column Groups */}
          <div className="space-y-4">
            {metricGroups.map((group, groupIndex) => (
              <Card key={groupIndex} className={group.bgColor}>
                <CardHeader className="pb-3">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <div className={`${group.color}`}>{group.icon}</div>
                      <CardTitle className="text-sm font-medium text-white">{group.title}</CardTitle>
                      <Badge variant="secondary" className="text-xs">
                        {group.columns.length}
                      </Badge>
                    </div>
                  </div>
                  <CardDescription className="text-xs text-white/70">
                    {group.description}
                  </CardDescription>
                </CardHeader>
                <CardContent className="pt-0">
                  <div className="space-y-2">
                    {group.columns.map((column, columnIndex) => {
                      const isSelected = selectedMetrics.includes(column.column_name);
                      
                      return (
                        <div
                          key={columnIndex}
                          className={`flex items-center gap-3 p-2 rounded-lg border cursor-pointer transition-all ${
                            isSelected 
                              ? 'bg-white/20 border-white/30' 
                              : 'bg-white/5 border-white/10 hover:bg-white/10'
                          }`}
                          onClick={() => {
                            if (isSelected) {
                              onMetricsChange(selectedMetrics.filter(m => m !== column.column_name));
                            } else {
                              onMetricsChange([...selectedMetrics, column.column_name]);
                            }
                          }}
                        >
                          <Checkbox
                            checked={isSelected}
                            onChange={() => {}} // Handled by div onClick
                            className="pointer-events-none"
                          />
                          
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-2">
                              {getTypeIcon(column.column_type)}
                              <span className="font-medium text-sm truncate text-white">
                                {column.column_name}
                              </span>
                              {column.is_key_metric && (
                                <Badge className="bg-green-500/20 text-green-300 text-xs">
                                  Key
                                </Badge>
                              )}
                            </div>
                            <div className="text-xs text-white/60 truncate">
                              {column.business_context}
                            </div>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      )}
    </div>
  );
} 