/**
 * Dashboard Layout Component
 * Modern redesigned UI while preserving all functionality
 */

import React, { useState, useCallback, useEffect } from 'react';
import { Upload, Download, RefreshCw, Settings, Grid, BarChart3, MessageCircle, TrendingUp, Sparkles, Zap, ChartBar, Target, Brain, Rocket, CheckCircle, Hash, Filter, X, Eye, Plus } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { ConversationalAnalytics } from '@/components/chat/conversational-analytics';

import { DynamicKPI, DynamicKPIGrid } from './dynamic-kpi';
import { DynamicChart } from './dynamic-chart';
import { DynamicChartCard } from './DynamicChartCard';
import { CustomChartBuilder } from './CustomChartBuilder';
import FileUploadWithProgress from '@/components/upload/FileUploadWithProgress';

import { useDashboard } from '@/hooks/useDashboard';
import { 
  DashboardConfig,
  ChartConfig,
  KPIConfig,
  LayoutTemplate,
  ThemeConfig
} from '@/services/dashboard.service';
import { SmartMetricSelector } from './SmartMetricSelector';
import { 
  SAMPLE_DATASETS, 
  generateBIDashboard, 
  cleanDataset, 
  profileDataset, 
  parseDatasetFile,
  BusinessInsight 
} from '@/services/bi-engine';
import { datasetStorage } from '@/services/dataset-storage.service';
import { uploadService, CleaningReport } from '@/services/upload.service';
import { DataCleaningView } from './data-cleaning-view';
import { ForecastingView } from './forecasting-view';
import { InsightCard } from './insight-card';
import { DatasetExecutiveSummary } from './DatasetExecutiveSummary';
import { ExportComponent } from '@/components/export/ExportComponent';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Input } from '@/components/ui/input';
import { Search, AlertTriangle } from 'lucide-react';

interface DashboardLayoutProps {
  className?: string;
  theme?: ThemeConfig;
  autoRefresh?: boolean;
  allowUpload?: boolean;
  allowExport?: boolean;
}

export const DashboardLayout: React.FC<DashboardLayoutProps> = ({
  className = '',
  theme,
  autoRefresh = false,
  allowUpload = true,
  allowExport = true,
}) => {
  const [activeTab, setActiveTab] = useState('overview');
  const [showUpload, setShowUpload] = useState(true);
  const [showChatMode, setShowChatMode] = useState(false);
  const [uploadMode, setUploadMode] = useState<'standard' | 'chat'>('standard');
  
  // Smart Metric Selector states
  const [showMetricSelector, setShowMetricSelector] = useState(false);
  const [fileAnalysis, setFileAnalysis] = useState<any>(null);
  const [selectedMetrics, setSelectedMetrics] = useState<string[]>([]);
  const [metricPairs, setMetricPairs] = useState<any[]>([]);
  const [analyzingFile, setAnalyzingFile] = useState(false);
  const [currentFile, setCurrentFile] = useState<File | null>(null);

  // BI Dataset & Filter States
  const [rawData, setRawData] = useState<Record<string, any>[]>([]);
  const [cleanedData, setCleanedData] = useState<Record<string, any>[]>([]);
  const [cleaningReport, setCleaningReport] = useState<CleaningReport | null>(null);
  const [datasetName, setDatasetName] = useState<string>('Uploaded Dataset');
  const [selectedCategoryFilter, setSelectedCategoryFilter] = useState<string>('ALL');
  const [searchFilterQuery, setSearchFilterQuery] = useState<string>('');
  const [showCustomChartBuilder, setShowCustomChartBuilder] = useState(false);

  // Dashboard Integration Hook
  const {
    dashboard,
    upload,
    export: exportState,
    uploadAndGenerateDashboard,
    generateDashboardFromUpload,
    exportDashboard,
    getChartRecommendations,
    calculateKPIs,
    setDashboard,
    resetDashboard,
    analyzeFileStructure,
    generateDashboardWithSelectedMetrics,
    generateDashboardWithMetricPairs,
    isReady,
    hasData,
    isLoading,
  } = useDashboard({ autoRefresh });

  // Auto-load active saved dataset on mount
  useEffect(() => {
    const loadActiveDataset = async () => {
      try {
        const active = await datasetStorage.getActiveDataset();
        if (active && active.cleanedRows && active.cleanedRows.length > 0) {
          setRawData(active.rawRows || active.cleanedRows);
          setCleanedData(active.cleanedRows);
          setDatasetName(active.name);
          setShowUpload(false);

          const biDashboard = generateBIDashboard(active.cleanedRows, active.name);
          setDashboard({
            config: biDashboard as any,
            charts: biDashboard.charts,
            kpis: biDashboard.kpis,
          });
        }
      } catch (err) {
        console.warn('Failed to auto-load active dataset:', err);
      }
    };
    loadActiveDataset();
  }, [setDashboard]);

  // Handle file upload for Smart Metric Selector
  const handleFileAnalysis = useCallback(async (file: File) => {
    setAnalyzingFile(true);
    
    try {
      console.log('🔍 Starting file analysis for Smart Metric Selector...');
      
      const analysis = await analyzeFileStructure(file);
      setFileAnalysis(analysis);
      
      // Pre-select recommended metrics
      const recommendedMetrics = analysis.column_classifications
        .filter(col => col.recommended)
        .map(col => col.column_name);
      setSelectedMetrics(recommendedMetrics);
      
      // Show metric selector
      setShowMetricSelector(true);
      setShowUpload(false);
      
      console.log('✅ File analysis completed, showing metric selector');
    } catch (error) {
      console.error('❌ File analysis failed:', error);
      alert(`File analysis failed: ${error instanceof Error ? error.message : 'Unknown error'}\n\nPlease try a different file or use standard upload.`);
    } finally {
      setAnalyzingFile(false);
    }
  }, [analyzeFileStructure]);

  // Handle file selection for Smart Metric Selector
  const handleFileSelection = useCallback(async (file: File) => {
    setCurrentFile(file);
    setDatasetName(file.name);
    try {
      const uploadRes = await uploadService.uploadFile(file);
      if (uploadRes.cleaning_report) {
        setCleaningReport(uploadRes.cleaning_report);
      }
      if (uploadRes.cleaned_data && uploadRes.cleaned_data.length > 0) {
        setCleanedData(uploadRes.cleaned_data);
        setRawData(uploadRes.preview_before || uploadRes.cleaned_data);
      } else {
        const parsed = await parseDatasetFile(file);
        const cleaned = cleanDataset(parsed.data);
        setRawData(parsed.data);
        setCleanedData(cleaned.cleanedData);
      }
    } catch (err) {
      console.warn('Backend parse in handleFileSelection failed, using fallback:', err);
      try {
        const parsed = await parseDatasetFile(file);
        const cleaned = cleanDataset(parsed.data);
        setRawData(parsed.data);
        setCleanedData(cleaned.cleanedData);
      } catch (localErr) {
        console.error('Local fallback failed:', localErr);
      }
    }
    // Automatically analyze the file when selected
    handleFileAnalysis(file);
  }, [handleFileAnalysis]);

  // Sample Dataset Handler
  const handleLoadSampleDataset = useCallback(async (sampleId: string) => {
    const sample = SAMPLE_DATASETS.find(s => s.id === sampleId) || SAMPLE_DATASETS[0];
    const cleaned = cleanDataset(sample.data);
    const biDashboard = generateBIDashboard(cleaned.cleanedData, sample.name);

    setRawData(sample.data);
    setCleanedData(cleaned.cleanedData);
    setDatasetName(sample.name);
    setSelectedCategoryFilter('ALL');
    setSearchFilterQuery('');

    setDashboard({
      config: biDashboard as any,
      charts: biDashboard.charts,
      kpis: biDashboard.kpis,
    });

    try {
      await datasetStorage.saveDataset({
        name: sample.name,
        filename: `${sample.id}.csv`,
        sizeBytes: sample.data.length * 120,
        rowCount: sample.data.length,
        columnCount: Object.keys(sample.data[0] || {}).length,
        columns: Object.keys(sample.data[0] || {}),
        rawRows: sample.data,
        cleanedRows: cleaned.cleanedData,
        profile: profileDataset(cleaned.cleanedData),
        cleaningHistory: [{ id: Date.now().toString(), timestamp: new Date().toISOString(), action: 'Load Sample', details: `Loaded ${sample.name}` }],
        isActive: true,
      });
    } catch (e) {
      console.warn('Dataset storage save warning:', e);
    }

    setShowUpload(false);
    setActiveTab('overview');
  }, [setDashboard]);

  // Apply Data Cleaning Handler
  const handleApplyCleaning = useCallback(async (newCleanedData: Record<string, any>[], summaryMsg: string) => {
    setCleanedData(newCleanedData);
    const biDashboard = generateBIDashboard(newCleanedData, datasetName || 'Cleaned Dataset');

    setDashboard({
      config: biDashboard as any,
      charts: biDashboard.charts,
      kpis: biDashboard.kpis,
    });

    try {
      const active = await datasetStorage.getActiveDataset();
      if (active) {
        await datasetStorage.updateDataset(active.id, {
          cleanedRows: newCleanedData,
          rowCount: newCleanedData.length,
          profile: profileDataset(newCleanedData),
        }, {
          action: 'Data Cleaning',
          details: summaryMsg || 'Applied custom cleaning rules',
        });
      }
    } catch (e) {
      console.warn('Dataset cleaning update warning:', e);
    }

    setActiveTab('overview');
  }, [datasetName, setDashboard]);

  // Filter change handler
  const handleFilterChange = useCallback((catVal: string, searchVal: string) => {
    setSelectedCategoryFilter(catVal);
    setSearchFilterQuery(searchVal);

    const activeDataset = cleanedData.length > 0 ? cleanedData : rawData;
    if (activeDataset.length === 0) return;

    const prof = profileDataset(activeDataset);
    const catCol = prof.primaryDimension;

    const filters = {
      categoryFilters: catVal !== 'ALL' && catCol ? { [catCol]: catVal } : undefined,
      searchQuery: searchVal || undefined,
    };

    const biDashboard = generateBIDashboard(activeDataset, datasetName || 'Filtered Dataset', filters);
    setDashboard({
      config: biDashboard as any,
      charts: biDashboard.charts,
      kpis: biDashboard.kpis,
    });
  }, [cleanedData, rawData, datasetName, setDashboard]);

  // Handle Smart Metric Selector dashboard generation
  const handleSmartMetricGeneration = useCallback(async () => {
    if (!currentFile) return;
    
    // Check if we're using pairs or individual metrics
    const validPairs = metricPairs.filter(pair => pair.xAxis && pair.yAxis);
    
    if (validPairs.length === 0 && selectedMetrics.length === 0) {
      alert('Please select at least one metric pair or individual metrics to generate a dashboard.');
      return;
    }
    
    try {
      if (validPairs.length > 0) {
        console.log('🎯 Generating dashboard with metric pairs:', validPairs);
        
        // Generate dashboard with paired metrics
        await generateDashboardWithMetricPairs(
          currentFile,
          validPairs,
          {
            layoutType: 'responsive',
            theme: theme?.name || 'default'
          }
        );
      } else {
        console.log('🎯 Generating dashboard with selected metrics:', selectedMetrics);
        
        await generateDashboardWithSelectedMetrics(
          currentFile,
          selectedMetrics,
          {
            layoutType: 'responsive',
            theme: theme?.name || 'default'
          }
        );
      }
      
      // Reset states and navigate to dashboard
      setShowMetricSelector(false);
      setFileAnalysis(null);
      setCurrentFile(null);
      setSelectedMetrics([]);
      setMetricPairs([]);
      setActiveTab('overview');
      
      console.log('✅ Smart Metric Selector dashboard generation completed');
    } catch (error) {
      console.error('❌ Smart Metric Selector dashboard generation failed:', error);
      alert(`Dashboard generation failed: ${error instanceof Error ? error.message : 'Unknown error'}\n\nPlease try again or use standard upload.`);
    }
  }, [currentFile, selectedMetrics, metricPairs, generateDashboardWithSelectedMetrics, theme]);

  // Handle file upload and dashboard generation (original functionality)
  const handleFileUpload = useCallback(async (file: File) => {
    try {
      await uploadAndGenerateDashboard(file, {
        layoutType: 'responsive',
        theme: theme?.name || 'default',
      });
      setShowUpload(false);
      setActiveTab('overview');
    } catch (error) {
      console.error('Dashboard generation failed:', error);
    }
  }, [uploadAndGenerateDashboard, theme]);

  // Handle dashboard export
  const handleExport = useCallback(async (format: 'pdf' | 'png' | 'html' | 'json') => {
    if (!dashboard.config) return;
    
    try {
      await exportDashboard({
        dashboard_config: dashboard.config,
        export_format: format,
        export_options: {
          include_data: true,
          high_resolution: format === 'png',
        },
        metadata: {
          title: `Dashboard - ${new Date().toLocaleDateString()}`,
          description: 'Generated by InsightIQ',
        },
      });
    } catch (error) {
      console.error('Export failed:', error);
    }
  }, [dashboard.config, exportDashboard]);



  // Render KPI grid based on layout
  const renderKPIGrid = () => {
    if (!dashboard.kpis.length) return null;

    return (
      <div className="mb-8">
        <div className="flex items-center gap-3 mb-6">
          <div className="p-2 bg-gradient-to-r from-green-500/20 to-emerald-500/20 rounded-lg border border-green-400/30">
            <Target className="w-5 h-5 text-green-400" />
          </div>
          <h3 className="text-xl font-semibold text-white">Key Performance Indicators</h3>
          <Badge variant="outline" className="border-green-400/50 text-green-200">
            {dashboard.kpis.length} KPIs
          </Badge>
        </div>
        <DynamicKPIGrid 
          kpis={dashboard.kpis}
          columns={4}
          theme={theme}
          className="gap-6"
        />
      </div>
    );
  };

  // Render charts grid with custom chart building & interactive controls
  const renderChartsGrid = () => {
    if (!dashboard.charts.length && !hasData) return null;

    return (
      <div className="mb-8">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-gradient-to-r from-blue-500/20 to-purple-500/20 rounded-lg border border-blue-400/30">
              <ChartBar className="w-5 h-5 text-blue-400" />
            </div>
            <div>
              <h3 className="text-xl font-semibold text-white">Analytics Visualizations</h3>
              <p className="text-xs text-slate-400">Data-driven charts generated from active dataset columns</p>
            </div>
            <Badge variant="outline" className="border-blue-400/50 text-blue-200 ml-2">
              {dashboard.charts.length} Charts
            </Badge>
          </div>

          <Button
            onClick={() => setShowCustomChartBuilder(true)}
            className="bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 text-white font-medium text-xs gap-2 px-4 py-2 shadow-lg shadow-indigo-500/20"
          >
            <Plus className="w-4 h-4" />
            + Add Custom Chart
          </Button>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {dashboard.charts.map((chart, index) => (
            <DynamicChartCard
              key={chart.id || `chart_${index}`}
              chart={chart}
              datasetName={datasetName}
              onUpdateChart={updatedChart => {
                const updatedList = dashboard.charts.map((c, i) =>
                  (c.id === updatedChart.id || i === index) ? updatedChart : c
                );
                setDashboard({ ...dashboard, charts: updatedList });
              }}
              onDeleteChart={chartId => {
                const remaining = dashboard.charts.filter((c, i) => (c.id !== chartId && i !== index));
                setDashboard({ ...dashboard, charts: remaining });
              }}
            />
          ))}
        </div>
      </div>
    );
  };

  // Render enhanced upload section
  const renderUploadSection = () => (
    <section className="relative" data-upload-section>
      {/* Background with enhanced styling */}
      <div className="absolute inset-0 bg-gradient-to-br from-indigo-900/20 via-purple-900/20 to-pink-900/20 rounded-3xl"></div>
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_50%,rgba(120,119,198,0.15),rgba(255,255,255,0))] rounded-3xl"></div>
      
      <Card className="relative backdrop-blur-xl bg-black/40 border-white/20 shadow-2xl shadow-black/50 rounded-3xl overflow-hidden">
        {/* Enhanced Mode Selector */}
        <CardHeader className="pb-4">
          <div className="text-center mb-6">
            <CardTitle className="text-2xl font-bold text-white mb-2">
              Choose Your Dashboard Mode
            </CardTitle>
            <CardDescription className="text-white/70 text-base">
              Select how you want to create your analytics dashboard
            </CardDescription>
          </div>

          <div className="flex gap-3 mt-6">
            <Button
              variant={uploadMode === 'standard' ? 'default' : 'outline'}
              onClick={() => {
                setUploadMode('standard');
                setShowChatMode(false);
                setShowMetricSelector(false);
              }}
              className={`flex-1 h-12 transition-all duration-300 ${
                uploadMode === 'standard' 
                  ? 'bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 shadow-lg shadow-blue-500/25' 
                  : 'border-white/20 text-white/80 hover:bg-white/10'
              }`}
            >
              <BarChart3 className="w-5 h-5 mr-2" />
              <div className="text-left">
                <div className="font-semibold">Standard Mode</div>
                <div className="text-xs opacity-80">Auto-generate dashboard</div>
              </div>
            </Button>
            <Button
              variant={uploadMode === 'chat' ? 'default' : 'outline'}
              onClick={() => setUploadMode('chat')}
              className={`flex-1 h-12 transition-all duration-300 ${
                uploadMode === 'chat' 
                  ? 'bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 shadow-lg shadow-purple-500/25' 
                  : 'border-white/20 text-white/80 hover:bg-white/10'
              }`}
            >
              <MessageCircle className="w-5 h-5 mr-2" />
              <div className="text-left">
                <div className="font-semibold">Chat Mode</div>
                <div className="text-xs opacity-80">Conversational analysis</div>
              </div>
            </Button>
          </div>
          
          {/* Enhanced Mode Description */}
          <div className="mt-4 p-4 rounded-xl bg-gradient-to-r from-white/5 to-white/10 border border-white/10">
            {uploadMode === 'standard' ? (
              <div className="flex items-start gap-3">
                <BarChart3 className="w-5 h-5 text-blue-400 mt-0.5" />
                <div>
                  <h4 className="font-medium text-white mb-1">Standard Mode Features</h4>
                  <p className="text-sm text-white/70 mb-2">
                    Automatically analyzes your data and creates comprehensive dashboards with intelligent chart recommendations.
                  </p>
                  <div className="flex flex-wrap gap-2">
                    <Badge className="bg-blue-500/20 text-blue-300 text-xs">
                      Smart Metric Selector
                    </Badge>
                    <Badge className="bg-blue-500/20 text-blue-300 text-xs">
                      Auto Chart Generation
                    </Badge>
                    <Badge className="bg-blue-500/20 text-blue-300 text-xs">
                      Business KPIs
                    </Badge>
                  </div>
                </div>
              </div>
            ) : (
              <div className="flex items-start gap-3">
                <MessageCircle className="w-5 h-5 text-purple-400 mt-0.5" />
                <div>
                  <h4 className="font-medium text-white mb-1">Chat Mode Features</h4>
                  <p className="text-sm text-white/70 mb-2">
                    Have a conversation about your data. Ask questions, get insights, and build custom dashboards through natural language.
                  </p>
                  <div className="flex flex-wrap gap-2">
                    <Badge className="bg-purple-500/20 text-purple-300 text-xs">
                      Natural Language
                    </Badge>
                    <Badge className="bg-purple-500/20 text-purple-300 text-xs">
                      Custom Analysis
                    </Badge>
                    <Badge className="bg-purple-500/20 text-purple-300 text-xs">
                      Interactive Q&A
                    </Badge>
                  </div>
                </div>
              </div>
            )}
          </div>
        </CardHeader>

        <CardContent className="relative z-10">
          {/* Upload Mode Content */}
          {uploadMode === 'standard' ? (
            <div className="space-y-4">
              {!showMetricSelector ? (
                <FileUploadWithProgress
                  onUploadComplete={async (result) => {
                    console.log('📁 File upload completed:', result);
                    if (result.cleaning_report) {
                      setCleaningReport(result.cleaning_report);
                    }
                    if (result.cleaned_data && result.cleaned_data.length > 0) {
                      setCleanedData(result.cleaned_data);
                      if (result.preview_before) {
                        setRawData(result.preview_before);
                      }
                    }
                    if (currentFile) {
                      await handleFileAnalysis(currentFile);
                    } else {
                      // Fallback to original behavior for direct uploads without file selection
                      try {
                        let filePath = result.storage?.relative_path || 
                                      result.storage?.file_path || 
                                      result.storage?.stored_filename;
                        const sessionId = result.session_id;
                        
                        if (!filePath) {
                          throw new Error('File path not found in upload result');
                        }
                          
                        const dashboardConfig = await generateDashboardFromUpload(
                          filePath,
                          sessionId,
                          {
                            layoutType: 'responsive',
                            theme: 'default'
                          }
                        );
                        
                        setShowUpload(false);
                        setActiveTab('overview');
                        
                      } catch (error) {
                        console.error('❌ AI dashboard generation failed:', error);
                        alert(`AI Dashboard generation failed: ${error instanceof Error ? error.message : 'Unknown error'}\n\nPlease try uploading your file again.`);
                      }
                    }
                  }}
                  onUploadError={(error) => {
                    console.error('❌ File upload error:', error);
                  }}
                  onFileSelect={handleFileSelection} // Add file selection handler
                  maxFileSize={100}
                  acceptedTypes={['.csv', '.xlsx', '.xls', '.json']}
                />
              ) : null}
              
              {/* Enhanced Smart Metric Selector Feature */}
              <div className="mb-4 p-4 rounded-xl bg-gradient-to-r from-green-500/10 to-blue-500/10 border border-green-500/20">
                <div className="flex items-center gap-3 mb-2">
                  <div className="w-8 h-8 rounded-full bg-green-500/20 flex items-center justify-center">
                    <CheckCircle className="w-4 h-4 text-green-400" />
                  </div>
                  <div>
                    <h4 className="font-medium text-white">Smart Metric Selector (NEW)</h4>
                    <p className="text-sm text-white/70">
                      Choose exactly which columns to analyze before generating your dashboard
                    </p>
                  </div>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-3 mt-3">
                  <div className="flex items-center gap-2 text-sm text-white/80">
                    <Hash className="w-4 h-4 text-blue-400" />
                    <span>Select key metrics only</span>
                  </div>
                  <div className="flex items-center gap-2 text-sm text-white/80">
                    <Filter className="w-4 h-4 text-purple-400" />
                    <span>Filter irrelevant columns</span>
                  </div>
                  <div className="flex items-center gap-2 text-sm text-white/80">
                    <TrendingUp className="w-4 h-4 text-green-400" />
                    <span>Focused insights</span>
                  </div>
                </div>
              </div>
            </div>
          ) : (
            /* Chat Mode - Show the conversational analytics component directly */
            <ConversationalAnalytics 
              onAnalyticsGenerated={async (dashboardData) => {
                console.log('🤖 Chat Mode: Analytics generated successfully:', dashboardData);
                
                try {
                  const dashboardConfig: DashboardConfig = {
                    dashboard_id: `chat-dashboard-${Date.now()}`,
                    layout: {
                      type: 'responsive',
                      theme: theme?.name || 'default',
                      grid: {
                        columns: 12,
                        rows: 'auto',
                        gap: 4
                      }
                    },
                    kpis: dashboardData.kpis || [],
                    charts: dashboardData.charts || [],
                    metadata: {
                      created_at: new Date().toISOString(),
                      data_source: 'conversational_analytics',
                      insights: dashboardData.insights || []
                    },
                    generated_at: new Date().toISOString()
                  };
                  
                  setDashboard({
                    config: dashboardConfig,
                    charts: dashboardData.charts || [],
                    kpis: dashboardData.kpis || [],
                  });
                  
                  setShowChatMode(false);
                  setShowUpload(false);
                  setActiveTab('overview');
                  
                } catch (error) {
                  console.error('❌ Failed to apply chat-generated dashboard:', error);
                  alert('Failed to generate dashboard from chat. Please try again.');
                }
              }}
              onClose={() => {
                setShowChatMode(false);
                setUploadMode('standard');
              }}
            />
          )}
          
          {/* File analysis progress indicator */}
          {analyzingFile && (
            <div className="mt-6 p-4 rounded-xl bg-blue-500/10 border border-blue-500/20">
              <div className="flex items-center gap-3">
                <div className="animate-spin h-5 w-5 border-2 border-blue-500 border-t-transparent rounded-full"></div>
                <div className="text-sm font-medium text-blue-200">
                  Analyzing file structure for Smart Metric Selector...
                </div>
              </div>
              <p className="text-xs text-blue-300 mt-2">
                This will help you choose which columns to include in your dashboard
              </p>
            </div>
          )}
          
          {/* Enhanced progress indicator for AI processing */}
          {upload.progress > 0 && upload.uploading && (
            <div className="mt-6 p-4 rounded-xl bg-blue-500/10 border border-blue-500/20">
              <div className="flex items-center gap-3 mb-3">
                <div className="animate-spin h-5 w-5 border-2 border-blue-500 border-t-transparent rounded-full"></div>
                <div className="text-sm font-medium text-blue-200">
                  Uploading... {upload.progress}%
                </div>
              </div>
              <div className="w-full bg-white/10 rounded-full h-2">
                <div 
                  className="bg-gradient-to-r from-blue-500 to-purple-500 h-2 rounded-full transition-all duration-300"
                  style={{ width: `${upload.progress}%` }}
                />
              </div>
            </div>
          )}
          
          {/* Enhanced AI processing indicator */}
          {isLoading && !upload.uploading && !analyzingFile && (
            <div className="mt-6 p-6 rounded-xl bg-gradient-to-r from-purple-500/10 to-pink-500/10 border border-purple-500/20">
              <div className="flex items-center gap-4 mb-4">
                <div className="animate-pulse w-12 h-12 rounded-full bg-gradient-to-r from-purple-500 to-pink-500 flex items-center justify-center">
                  <Sparkles className="w-6 h-6 text-white" />
                </div>
                <div>
                  <div className="text-lg font-semibold text-white mb-1">
                    AI Processing Your Data
                  </div>
                  <div className="text-sm text-purple-200">
                    Analyzing patterns and generating intelligent visualizations...
                  </div>
                </div>
              </div>
              
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="flex items-center gap-3 p-3 rounded-lg bg-white/5">
                  <Brain className="w-5 h-5 text-purple-400" />
                  <div className="text-sm">
                    <div className="font-medium text-white">Pattern Recognition</div>
                    <div className="text-purple-200 text-xs">Identifying data relationships</div>
                  </div>
                </div>
                <div className="flex items-center gap-3 p-3 rounded-lg bg-white/5">
                  <BarChart3 className="w-5 h-5 text-blue-400" />
                  <div className="text-sm">
                    <div className="font-medium text-white">Chart Generation</div>
                    <div className="text-blue-200 text-xs">Creating optimal visualizations</div>
                  </div>
                </div>
                <div className="flex items-center gap-3 p-3 rounded-lg bg-white/5">
                  <TrendingUp className="w-5 h-5 text-green-400" />
                  <div className="text-sm">
                    <div className="font-medium text-white">KPI Calculation</div>
                    <div className="text-green-200 text-xs">Generating business insights</div>
                  </div>
                </div>
              </div>
              
              <div className="mt-4 text-center">
                <div className="text-xs text-white/60">
                  This intelligent analysis typically takes 30-60 seconds
                </div>
              </div>
            </div>
          )}

          {/* Sample Datasets Selector */}
          <div className="mt-6 pt-6 border-t border-white/10 text-center">
            <div className="text-sm font-semibold text-white mb-3 flex items-center justify-center gap-2">
              <Zap className="w-4 h-4 text-amber-400" /> Or load a sample dataset instantly
            </div>
            <div className="flex flex-wrap justify-center gap-3">
              {SAMPLE_DATASETS.map(sample => (
                <Button
                  key={sample.id}
                  variant="outline"
                  size="sm"
                  onClick={() => handleLoadSampleDataset(sample.id)}
                  className="border-slate-600 bg-slate-800/80 text-slate-200 hover:bg-emerald-600 hover:text-white hover:border-emerald-500 transition-all text-xs py-2 px-3"
                >
                  <TrendingUp className="w-3.5 h-3.5 mr-1.5 text-emerald-400" />
                  {sample.name}
                </Button>
              ))}
            </div>
          </div>
        </CardContent>
      </Card>
    </section>
  );

  // Smart Metric Selector Inline Section (replaces fullscreen overlay)
  const renderMetricSelector = () => (
    showMetricSelector && fileAnalysis && (
      <div className="w-full">
        <Card className="border-white/20 bg-gradient-to-br from-gray-900 to-black">
          <CardHeader className="flex flex-row items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <BarChart3 className="w-5 h-5 text-blue-400" />
              <CardTitle className="text-white">Select metric pairs</CardTitle>
            </div>
            <Button
              onClick={() => {
                setShowMetricSelector(false);
                setFileAnalysis(null);
                setCurrentFile(null);
                setSelectedMetrics([]);
              }}
              variant="ghost"
              size="sm"
              className="text-white/60 hover:text-white hover:bg-white/10"
            >
              <X className="w-4 h-4" />
            </Button>
          </CardHeader>
          <CardContent className="p-6">
            <SmartMetricSelector
              fileAnalysis={fileAnalysis}
              selectedMetrics={selectedMetrics}
              onMetricsChange={setSelectedMetrics}
              onMetricPairsChange={setMetricPairs}
              onGenerate={handleSmartMetricGeneration}
              isGenerating={isLoading}
              className="w-full"
            />
          </CardContent>
        </Card>
      </div>
    )
  );

  const renderDashboardControls = () => (
    <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6 mb-8">
      <div className="space-y-2">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-gradient-to-r from-blue-500/20 to-purple-500/20 rounded-lg">
            <BarChart3 className="w-6 h-6 text-blue-400" />
          </div>
          <h2 className="text-3xl font-bold text-white">Analytics Dashboard</h2>
        </div>
        <p className="text-white/60 flex items-center gap-2">
          {dashboard.lastGenerated ? (
            <>
              <span className="w-2 h-2 bg-green-400 rounded-full"></span>
              Generated {dashboard.lastGenerated.toLocaleString()}
            </>
          ) : (
            <>
              <span className="w-2 h-2 bg-orange-400 rounded-full"></span>
              Ready for data upload
            </>
          )}
        </p>
      </div>
      
      <div className="flex flex-wrap items-center gap-3">
        {isReady && (
          <>
            <Badge variant="outline" className="border-green-400/50 text-green-200 bg-green-500/10 px-3 py-1">
              <Target className="w-3 h-3 mr-1" />
              {dashboard.charts.length} Charts
            </Badge>
            <Badge variant="outline" className="border-blue-400/50 text-blue-200 bg-blue-500/10 px-3 py-1">
              <ChartBar className="w-3 h-3 mr-1" />
              {dashboard.kpis.length} KPIs
            </Badge>
          </>
        )}
        
        {isReady && (
          <Button
            variant="outline"
            size="sm"
            onClick={resetDashboard}
            className="border-red-400/50 text-red-200 hover:bg-red-500/20 transition-all duration-300 hover:scale-105"
          >
            <RefreshCw className="h-4 w-4 mr-2" />
            Reset
          </Button>
        )}
      </div>
    </div>
  );

  const renderGlobalFilterBar = () => {
    const activeDataset = cleanedData.length > 0 ? cleanedData : rawData;
    if (!activeDataset || activeDataset.length === 0) return null;

    const prof = profileDataset(activeDataset);
    const catCol = prof.primaryDimension;

    let categoryOptions: string[] = [];
    if (catCol) {
      const uniqueVals = new Set<string>();
      activeDataset.forEach(row => {
        const val = String(row[catCol] ?? '').trim();
        if (val) uniqueVals.add(val);
      });
      categoryOptions = Array.from(uniqueVals).slice(0, 30);
    }

    return (
      <Card className="bg-slate-900/80 border-slate-800 p-4 mb-6 backdrop-blur-md">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <Filter className="w-4 h-4 text-emerald-400" />
            <span className="text-sm font-semibold text-white">Interactive Dashboard Filters</span>
            {selectedCategoryFilter !== 'ALL' || searchFilterQuery ? (
              <Badge variant="outline" className="border-emerald-500/40 text-emerald-300 bg-emerald-500/10">
                Filtered View ({activeDataset.length} rows)
              </Badge>
            ) : null}
          </div>

          <div className="flex flex-wrap items-center gap-3">
            {catCol && categoryOptions.length > 0 && (
              <div className="flex items-center gap-2">
                <span className="text-xs text-slate-400">{catCol}:</span>
                <Select 
                  value={selectedCategoryFilter} 
                  onValueChange={val => handleFilterChange(val, searchFilterQuery)}
                >
                  <SelectTrigger className="w-44 bg-slate-950 border-slate-700 text-white text-xs h-8">
                    <SelectValue placeholder={`All ${catCol}s`} />
                  </SelectTrigger>
                  <SelectContent className="bg-slate-900 border-slate-700 text-white text-xs">
                    <SelectItem value="ALL">All Categories</SelectItem>
                    {categoryOptions.map(opt => (
                      <SelectItem key={opt} value={opt}>{opt}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            )}

            <div className="relative w-48">
              <Search className="w-3.5 h-3.5 absolute left-2.5 top-2 text-slate-400" />
              <Input 
                placeholder="Filter keyword..."
                value={searchFilterQuery}
                onChange={e => handleFilterChange(selectedCategoryFilter, e.target.value)}
                className="pl-8 bg-slate-950 border-slate-700 text-xs text-white h-8"
              />
            </div>

            {(selectedCategoryFilter !== 'ALL' || searchFilterQuery) && (
              <Button 
                variant="ghost" 
                size="sm" 
                onClick={() => handleFilterChange('ALL', '')}
                className="text-xs text-slate-400 hover:text-white h-8"
              >
                <X className="w-3.5 h-3.5 mr-1" /> Reset
              </Button>
            )}

            <div className="pl-2 border-l border-slate-800">
              <ExportComponent
                data={activeDataset}
                datasetName={datasetName || 'Dashboard_Analysis'}
                kpis={dashboard.kpis}
                charts={dashboard.charts}
                insights={(dashboard.config as any)?.insights || []}
                size="sm"
              />
            </div>
          </div>
        </div>
      </Card>
    );
  };

  const renderBusinessInsightsSection = () => {
    const insights: BusinessInsight[] = (dashboard.config as any)?.insights || [];
    if (!insights || insights.length === 0) return null;

    return (
      <div className="mb-8">
        <div className="flex items-center gap-3 mb-6">
          <div className="p-2 bg-gradient-to-r from-purple-500/20 to-pink-500/20 rounded-lg border border-purple-400/30">
            <Brain className="w-5 h-5 text-purple-400" />
          </div>
          <h3 className="text-xl font-semibold text-white">Executive Business Insights</h3>
          <Badge variant="outline" className="border-purple-400/50 text-purple-200">
            {insights.length} Rules Computed
          </Badge>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {insights.map(item => (
            <InsightCard
              key={item.id}
              title={item.title}
              description={item.description}
              icon={item.type === 'risk' ? AlertTriangle : item.type === 'driver' ? TrendingUp : CheckCircle}
              priority={item.impact === 'high' ? 'high' : item.impact === 'medium' ? 'medium' : 'low'}
              tags={[item.badgeText]}
            />
          ))}
        </div>
      </div>
    );
  };

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Dashboard Controls - Show when we have data */}
      {(isReady || isLoading) && renderDashboardControls()}

      {/* Enhanced Loading State */}
      {isLoading && (
        <Alert className="border-blue-500/50 bg-gradient-to-r from-blue-500/10 to-purple-500/10 overflow-hidden relative">
          <div className="absolute inset-0 bg-gradient-to-r from-blue-500/5 to-purple-500/5 animate-pulse"></div>
          <AlertDescription className="text-blue-200 relative z-10">
            {upload.uploading && (
              <div className="flex items-center gap-3">
                <div className="animate-spin h-5 w-5 border-2 border-blue-500 border-t-transparent rounded-full"></div>
                <div>
                  <div className="font-semibold">Uploading file... {upload.progress}%</div>
                  <div className="text-xs text-blue-300/80 mt-1">Please wait while we process your data</div>
                </div>
              </div>
            )}
            {dashboard.loading && (
              <div className="flex items-center gap-3">
                <div className="p-2 bg-gradient-to-r from-blue-500/20 to-purple-500/20 rounded-lg">
                  <Brain className="animate-pulse h-5 w-5 text-blue-400" />
                </div>
                <div>
                  <div className="font-semibold">AI Dashboard Generation in Progress</div>
                  <div className="text-xs text-blue-300/80 mt-1">
                    Analyzing Excel columns • Detecting business patterns • Creating intelligent charts and KPIs
                  </div>
                </div>
              </div>
            )}
            {exportState.exporting && (
              <div className="flex items-center gap-3">
                <div className="animate-spin h-5 w-5 border-2 border-blue-500 border-t-transparent rounded-full"></div>
                <div>
                  <div className="font-semibold">Exporting dashboard...</div>
                  <div className="text-xs text-blue-300/80 mt-1">Preparing your export file</div>
                </div>
              </div>
            )}
          </AlertDescription>
        </Alert>
      )}

      {/* Enhanced Error State */}
      {(dashboard.error || upload.error || exportState.error) && (
        <Alert variant="destructive" className="border-red-500/50 bg-gradient-to-r from-red-500/10 to-pink-500/10">
          <AlertDescription className="text-red-200">
            <div className="font-semibold mb-1">Operation Failed</div>
            <div className="text-sm">{dashboard.error || upload.error || exportState.error}</div>
          </AlertDescription>
        </Alert>
      )}

      {/* Upload Section */}
      {showUpload && allowUpload && renderUploadSection()}

      {/* Smart Metric Selector Modal/Overlay */}
      {renderMetricSelector()}

      {/* Enhanced Dashboard Content */}
      {isReady && hasData && (
        <div className="space-y-6">
          {renderGlobalFilterBar()}

          <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
            <TabsList className="bg-white/10 border-white/20 p-1 h-auto flex flex-wrap">
              <TabsTrigger value="overview" className="text-white data-[state=active]:bg-white/20 px-6 py-3 transition-all duration-300">
                <Grid className="h-4 w-4 mr-2" />
                Overview
              </TabsTrigger>
              <TabsTrigger value="charts" className="text-white data-[state=active]:bg-white/20 px-6 py-3 transition-all duration-300">
                <BarChart3 className="h-4 w-4 mr-2" />
                Charts
              </TabsTrigger>
              <TabsTrigger value="kpis" className="text-white data-[state=active]:bg-white/20 px-6 py-3 transition-all duration-300">
                <Target className="h-4 w-4 mr-2" />
                KPIs
              </TabsTrigger>
              <TabsTrigger value="profiler" className="text-white data-[state=active]:bg-white/20 px-6 py-3 transition-all duration-300">
                <Zap className="h-4 w-4 mr-2 text-emerald-400" />
                Data Profiler & Cleaning
              </TabsTrigger>
            </TabsList>

            <TabsContent value="overview" className="space-y-8 mt-8">
              <DatasetExecutiveSummary
                data={cleanedData.length > 0 ? cleanedData : rawData}
                datasetName={datasetName}
                kpis={dashboard.kpis}
                insights={(dashboard.config as any)?.insights || []}
                cleaningReport={cleaningReport}
              />
              {renderKPIGrid()}
              {renderBusinessInsightsSection()}
              {dashboard.kpis.length > 0 && dashboard.charts.length > 0 && (
                <Separator className="bg-gradient-to-r from-transparent via-white/20 to-transparent" />
              )}
              {renderChartsGrid()}
            </TabsContent>

            <TabsContent value="charts" className="space-y-8 mt-8">
              {renderChartsGrid()}
            </TabsContent>

            <TabsContent value="kpis" className="space-y-8 mt-8">
              {renderKPIGrid()}
            </TabsContent>

            <TabsContent value="profiler" className="space-y-8 mt-8">
              <DataCleaningView 
                rawData={rawData.length > 0 ? rawData : (dashboard.config as any)?.sample_rows || []}
                cleanedData={cleanedData}
                cleaningReport={cleaningReport}
                currentFile={currentFile}
                datasetName={datasetName}
                onApplyCleaning={handleApplyCleaning}
              />
            </TabsContent>
          </Tabs>
        </div>
      )}

      {/* Enhanced Export Status */}
      {exportState.result && (
        <Alert className="border-green-500/50 bg-gradient-to-r from-green-500/10 to-emerald-500/10">
          <AlertDescription className="text-green-200">
            <div className="flex items-center gap-3">
              <div className="w-2 h-2 bg-green-400 rounded-full"></div>
              <span className="font-semibold">Dashboard exported successfully!</span>
              <Button 
                variant="link" 
                className="text-green-200 p-0 h-auto hover:text-green-100 transition-colors"
                onClick={() => window.open(exportState.result?.download_url, '_blank')}
              >
                Download →
              </Button>
            </div>
          </AlertDescription>
        </Alert>
      )}
      {/* Custom Chart Builder Modal */}
      {(cleanedData.length > 0 || rawData.length > 0) && (
        <CustomChartBuilder
          isOpen={showCustomChartBuilder}
          onClose={() => setShowCustomChartBuilder(false)}
          data={cleanedData.length > 0 ? cleanedData : rawData}
          profile={profileDataset(cleanedData.length > 0 ? cleanedData : rawData)}
          onAddChart={newChart => {
            setDashboard({
              ...dashboard,
              charts: [newChart, ...dashboard.charts],
            });
          }}
        />
      )}
    </div>
  );
};

export default DashboardLayout; 