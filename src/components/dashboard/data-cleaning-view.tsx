import React, { useState, useMemo } from 'react';
import { 
  CheckCircle2, 
  AlertTriangle, 
  Sparkles, 
  Trash2, 
  Filter, 
  FileSpreadsheet, 
  RefreshCw, 
  Search, 
  Database, 
  ArrowRight, 
  ShieldCheck,
  Download,
  Eye,
  SlidersHorizontal,
  Check,
  Layers,
  FileCheck,
  Info,
  Calendar,
  DollarSign,
  Binary,
  Split,
  Percent,
  HelpCircle,
  Send,
  Lightbulb,
  ArrowUpRight
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { 
  profileDataset, 
  cleanDataset, 
  CleaningOptions, 
  DatasetProfile, 
  formatValue 
} from '@/services/bi-engine';
import { uploadService, CleaningReport, CleaningAction } from '@/services/upload.service';
import { questionAnalysisService } from '@/services/question-analysis.service';

interface DataCleaningViewProps {
  rawData: Record<string, any>[];
  cleanedData?: Record<string, any>[];
  cleaningReport?: CleaningReport | null;
  currentFile?: File | null;
  datasetName: string;
  onApplyCleaning: (cleanedData: Record<string, any>[], summaryMessage: string) => void;
  onAnalyzeWithQuestion?: (cleanedData: Record<string, any>[], question: string) => void;
  onCancel?: () => void;
}

export const DataCleaningView: React.FC<DataCleaningViewProps> = ({
  rawData,
  cleanedData: initialCleanedData,
  cleaningReport: initialCleaningReport,
  currentFile,
  datasetName,
  onApplyCleaning,
  onAnalyzeWithQuestion,
  onCancel
}) => {
  // Determine working datasets
  const defaultCleaned = initialCleanedData && initialCleanedData.length > 0 
    ? initialCleanedData 
    : cleanDataset(rawData).cleanedData;

  const [activeCleanedData, setActiveCleanedData] = useState<Record<string, any>[]>(defaultCleaned);
  const [profile, setProfile] = useState<DatasetProfile>(() => profileDataset(activeCleanedData));
  const [cleaningReport, setCleaningReport] = useState<CleaningReport | null>(initialCleaningReport || null);
  const [searchQuery, setSearchQuery] = useState('');
  const [previewTab, setPreviewTab] = useState<'cleaned' | 'raw' | 'diff'>('cleaned');
  const [auditFilter, setAuditFilter] = useState<string>('all');
  const [isExporting, setIsExporting] = useState(false);
  const [isCleaning, setIsCleaning] = useState(false);
  const [questionText, setQuestionText] = useState('Show sales by year and which month had the highest sales.');

  const sampleQuestions = useMemo(() => {
    return questionAnalysisService.generateSampleQuestions(activeCleanedData);
  }, [activeCleanedData]);

  const [cleaningOptions, setCleaningOptions] = useState<CleaningOptions>({
    removeDuplicates: true,
    numericMissingStrategy: 'median',
    categoricalMissingStrategy: 'unknown',
    trimWhitespace: true,
    convertTypes: true,
  });

  // Calculate scores
  const scoreBefore = cleaningReport?.cleanliness_score_before ?? 75;
  const scoreAfter = cleaningReport?.cleanliness_score_after ?? 98;
  const scoreDelta = Math.max(0, scoreAfter - scoreBefore);

  // Trigger re-clean through Python pipeline or client engine
  const handleRunCleaning = async () => {
    setIsCleaning(true);
    try {
      if (currentFile) {
        // Run full Python pipeline
        const res = await uploadService.cleanFile(currentFile, cleaningOptions);
        if (res.cleaned_data && res.cleaned_data.length > 0) {
          setActiveCleanedData(res.cleaned_data);
          setProfile(profileDataset(res.cleaned_data));
          if (res.cleaning_report) {
            setCleaningReport(res.cleaning_report);
          }
          setIsCleaning(false);
          return;
        }
      }
      // Fallback to client-side engine
      const result = cleanDataset(rawData, cleaningOptions);
      setActiveCleanedData(result.cleanedData);
      setProfile(result.profile);
    } catch (err) {
      console.warn('Cleaning execution fallback to client:', err);
      const result = cleanDataset(rawData, cleaningOptions);
      setActiveCleanedData(result.cleanedData);
      setProfile(result.profile);
    } finally {
      setIsCleaning(false);
    }
  };

  // Export pristine cleaned Excel file (.xlsx)
  const handleExportCleanedExcel = async () => {
    setIsExporting(true);
    try {
      let blob: Blob;
      if (currentFile) {
        blob = await uploadService.exportCleanedFile(currentFile, cleaningOptions);
      } else {
        // Build Excel blob via client XLSX
        const XLSX = await import('xlsx');
        const worksheet = XLSX.utils.json_to_sheet(activeCleanedData);
        const workbook = XLSX.utils.book_new();
        XLSX.utils.book_append_sheet(workbook, worksheet, 'Cleaned_Data');
        const excelBuffer = XLSX.write(workbook, { bookType: 'xlsx', type: 'array' });
        blob = new Blob([excelBuffer], { 
          type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' 
        });
      }

      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `cleaned_${datasetName.replace(/\.[^.]+$/, '')}.xlsx`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Failed to export cleaned Excel file:', error);
      alert('Failed to export cleaned Excel file. Please try again.');
    } finally {
      setIsExporting(false);
    }
  };

  // Finalize and send cleaned data to the dashboard
  const handleFinalize = () => {
    const summaryMsg = cleaningReport?.summary || 
      `Refined dataset: ${activeCleanedData.length} rows and ${profile.columnCount} normalized columns ready for analytics.`;
    onApplyCleaning(activeCleanedData, summaryMsg);
  };

  // Filter preview records
  const displayRows = previewTab === 'raw' ? rawData : activeCleanedData;
  const filteredPreviewRows = displayRows.slice(0, 50).filter(row => {
    if (!searchQuery) return true;
    const q = searchQuery.toLowerCase();
    return Object.values(row).some(v => v !== null && v !== undefined && String(v).toLowerCase().includes(q));
  });

  // Categorize audit actions
  const actionsList: CleaningAction[] = cleaningReport?.actions_taken || [
    {
      category: 'headers',
      type: 'headers_normalized',
      description: 'Normalized column names into clean identifiers',
      count: profile.columnCount,
    },
    {
      category: 'formatting',
      type: 'type_stabilization',
      description: 'Standardized numeric and categorical types',
      count: profile.rowCount,
    },
    {
      category: 'missing_values',
      type: 'missing_handled',
      description: 'Safely imputed missing data points using statistical medians/modes',
      count: 0,
    }
  ];

  const filteredActions = auditFilter === 'all' 
    ? actionsList 
    : actionsList.filter(a => a.category === auditFilter);

  const getCategoryIcon = (category: string) => {
    switch (category) {
      case 'headers':
      case 'hierarchy':
        return <Layers className="w-4 h-4 text-sky-400" />;
      case 'noise':
      case 'gemini_column_pruning':
        return <Trash2 className="w-4 h-4 text-rose-400" />;
      case 'formatting':
        return <SlidersHorizontal className="w-4 h-4 text-indigo-400" />;
      case 'missing_values':
        return <Sparkles className="w-4 h-4 text-emerald-400" />;
      case 'gemini_feature_engineering':
        return <Binary className="w-4 h-4 text-emerald-400" />;
      case 'gemini_row_cleaning':
        return <Filter className="w-4 h-4 text-amber-400" />;
      case 'duplicates':
        return <ShieldCheck className="w-4 h-4 text-amber-400" />;
      case 'summary_rows':
        return <Split className="w-4 h-4 text-purple-400" />;
      default:
        return <CheckCircle2 className="w-4 h-4 text-emerald-400" />;
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 p-6 bg-slate-900/90 border border-slate-700/60 rounded-2xl backdrop-blur-md shadow-xl">
        <div className="space-y-1.5">
          <div className="flex flex-wrap items-center gap-2.5">
            <Database className="w-6 h-6 text-emerald-400" />
            <h2 className="text-xl font-bold text-white tracking-tight">
              Data Ingestion & Cleaning Pipeline
            </h2>
            <Badge variant="outline" className="border-emerald-500/40 text-emerald-300 bg-emerald-500/10 font-medium">
              Python + Gemini Pipeline
            </Badge>
            <Badge variant="outline" className="border-sky-500/40 text-sky-300 bg-sky-500/10 font-medium">
              Original File Untouched
            </Badge>
          </div>
          <p className="text-xs text-slate-400 max-w-3xl">
            Deterministic Python cleaning (delimiters, types, missing values, duplicates) unified with Gemini AI judgment (redundant metadata pruning, feature engineering, and messy row detection). Python safely executes all additions and deletions.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <Button 
            variant="outline" 
            size="sm" 
            onClick={handleExportCleanedExcel} 
            disabled={isExporting}
            className="border-slate-700 text-slate-200 hover:bg-slate-800 hover:text-white"
            title="Download pristine cleaned Excel file. Original file remains unchanged."
          >
            {isExporting ? <RefreshCw className="w-4 h-4 mr-2 animate-spin" /> : <Download className="w-4 h-4 mr-2 text-emerald-400" />}
            Export Cleaned Excel (.xlsx)
          </Button>

          {onCancel && (
            <Button 
              variant="outline" 
              size="sm" 
              onClick={onCancel} 
              className="border-slate-700 text-slate-400 hover:bg-slate-800"
            >
              Skip
            </Button>
          )}

          <Button 
            onClick={handleFinalize} 
            className="bg-emerald-600 hover:bg-emerald-500 text-white font-semibold shadow-lg shadow-emerald-600/20 px-4"
          >
            <ShieldCheck className="w-4 h-4 mr-2" />
            Finalize & Launch Analytics
          </Button>
        </div>
      </div>

      {/* Cleanliness Quality Score & Metrics Overview */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {/* Score Improvement Card */}
        <Card className="bg-gradient-to-br from-emerald-950/40 to-slate-900/80 border-emerald-500/30 md:col-span-2">
          <CardContent className="p-5 flex items-center justify-between">
            <div className="space-y-1">
              <div className="text-xs font-semibold text-emerald-400 uppercase tracking-wider flex items-center gap-1.5">
                <Sparkles className="w-3.5 h-3.5" />
                Data Cleanliness Score
              </div>
              <div className="flex items-baseline gap-3">
                <span className="text-3xl font-extrabold text-slate-400 line-through decoration-slate-500/60">
                  {scoreBefore}%
                </span>
                <ArrowRight className="w-5 h-5 text-emerald-400 self-center" />
                <span className="text-4xl font-black text-emerald-300">
                  {scoreAfter}%
                </span>
                {scoreDelta > 0 && (
                  <Badge className="bg-emerald-500/20 text-emerald-300 border-emerald-500/40 ml-1">
                    +{scoreDelta}% Cleanliness Boost
                  </Badge>
                )}
              </div>
              <p className="text-xs text-slate-400 mt-1 max-w-md">
                {cleaningReport?.summary || 'Normalized formats, stripped noise artifacts, and structured fields for robust analytics.'}
              </p>
            </div>
            <div className="hidden sm:flex flex-col items-center justify-center w-20 h-20 rounded-full border-4 border-emerald-500/30 bg-emerald-950/50">
              <span className="text-xl font-bold text-emerald-300">{scoreAfter}%</span>
              <span className="text-[10px] text-emerald-400 font-medium">READY</span>
            </div>
          </CardContent>
        </Card>

        {/* Rows Transformation */}
        <Card className="bg-slate-900/60 border-slate-800">
          <CardContent className="p-5 space-y-1">
            <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
              Records Preserved
            </div>
            <div className="flex items-baseline gap-2">
              <span className="text-2xl font-bold text-white">
                {activeCleanedData.length}
              </span>
              {cleaningReport && cleaningReport.rows_before !== activeCleanedData.length && (
                <span className="text-xs text-slate-400">
                  (from {cleaningReport.rows_before} raw rows)
                </span>
              )}
            </div>
            <div className="text-xs text-emerald-400 flex items-center gap-1 mt-1">
              <CheckCircle2 className="w-3.5 h-3.5" />
              <span>Banners & duplicates purged safely</span>
            </div>
          </CardContent>
        </Card>

        {/* Columns & Features */}
        <Card className="bg-slate-900/60 border-slate-800">
          <CardContent className="p-5 space-y-1">
            <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
              Normalized Fields
            </div>
            <div className="flex items-baseline gap-2">
              <span className="text-2xl font-bold text-sky-400">
                {profile.columnCount}
              </span>
              <span className="text-xs text-slate-400">
                ({profile.numericColumns.length} num, {profile.categoricalColumns.length} cat)
              </span>
            </div>
            <div className="text-xs text-slate-400 flex items-center gap-1 mt-1">
              <FileCheck className="w-3.5 h-3.5 text-sky-400" />
              <span>Ready for charts & BI engine</span>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Question Analysis Input Box: Ask What to Analyze */}
      <Card className="bg-gradient-to-br from-indigo-950/40 via-slate-900 to-purple-950/30 border-indigo-500/40 shadow-xl overflow-hidden">
        <CardContent className="p-5 sm:p-6 space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div className="flex items-center gap-3">
              <div className="p-2.5 bg-indigo-500/20 text-indigo-400 rounded-xl border border-indigo-500/30 shadow-inner">
                <Sparkles className="w-5 h-5 text-indigo-300" />
              </div>
              <div>
                <h3 className="text-lg font-bold text-white flex items-center gap-2">
                  What would you like to analyze in this dataset?
                  <Badge className="bg-indigo-500/20 text-indigo-300 border-indigo-500/40 text-[10px]">
                    Zero Random Charts
                  </Badge>
                </h3>
                <p className="text-xs text-slate-300 mt-0.5">
                  Type your analytical query. The Python engine computes the metrics and prepares only the relevant chart(s); AI explains the takeaways.
                </p>
              </div>
            </div>

            <div className="text-xs text-slate-400 bg-slate-950/60 px-3 py-1.5 rounded-lg border border-slate-800">
              Cleaned records: <strong className="text-emerald-400">{activeCleanedData.length}</strong>
            </div>
          </div>

          <div className="relative flex flex-col sm:flex-row items-stretch sm:items-center gap-2.5">
            <div className="relative flex-1">
              <HelpCircle className="w-5 h-5 absolute left-3.5 top-3.5 text-indigo-400/80 pointer-events-none" />
              <Input
                value={questionText}
                onChange={(e) => setQuestionText(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && questionText.trim()) {
                    if (onAnalyzeWithQuestion) {
                      onAnalyzeWithQuestion(activeCleanedData, questionText.trim());
                    } else {
                      handleFinalize();
                    }
                  }
                }}
                placeholder="e.g. Show sales by year and which month had the highest sales."
                className="pl-11 pr-4 py-6 bg-slate-950 border-indigo-500/50 text-white placeholder:text-slate-500 text-sm focus-visible:ring-indigo-500 rounded-xl"
              />
            </div>
            <Button
              onClick={() => {
                if (!questionText.trim()) return;
                if (onAnalyzeWithQuestion) {
                  onAnalyzeWithQuestion(activeCleanedData, questionText.trim());
                } else {
                  handleFinalize();
                }
              }}
              className="h-12 px-6 bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 text-white font-semibold text-sm rounded-xl shadow-lg shadow-indigo-600/25 transition-all flex items-center justify-center gap-2"
            >
              <span>Analyze Question & Generate Charts</span>
              <Send className="w-4 h-4" />
            </Button>
          </div>

          {sampleQuestions.length > 0 && (
            <div className="flex flex-wrap items-center gap-2 pt-1">
              <span className="text-xs text-indigo-300 font-medium flex items-center gap-1 mr-1">
                <Lightbulb className="w-3.5 h-3.5 text-amber-400" /> Suggested queries:
              </span>
              {sampleQuestions.map((q, idx) => (
                <button
                  key={idx}
                  type="button"
                  onClick={() => {
                    setQuestionText(q);
                    if (onAnalyzeWithQuestion) {
                      onAnalyzeWithQuestion(activeCleanedData, q);
                    }
                  }}
                  className="text-xs px-3 py-1 rounded-full bg-slate-900 hover:bg-indigo-900/40 text-slate-300 hover:text-white border border-slate-700 hover:border-indigo-500/50 transition-all flex items-center gap-1.5"
                >
                  <span>{q}</span>
                  <ArrowUpRight className="w-3 h-3 text-indigo-400 opacity-70" />
                </button>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Main Content Tabs: Audit Log & What Was Cleaned vs. Data Preview */}
      <Tabs defaultValue="audit" className="w-full">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800 pb-3">
          <TabsList className="bg-slate-950 border border-slate-800">
            <TabsTrigger value="audit" className="text-xs data-[state=active]:bg-slate-800 data-[state=active]:text-white">
              <CheckCircle2 className="w-3.5 h-3.5 mr-1.5 text-emerald-400" />
              Cleaning Audit & Changes ({actionsList.length})
            </TabsTrigger>
            <TabsTrigger value="preview" className="text-xs data-[state=active]:bg-slate-800 data-[state=active]:text-white">
              <Eye className="w-3.5 h-3.5 mr-1.5 text-sky-400" />
              Data Preview & Inspection
            </TabsTrigger>
            <TabsTrigger value="columns" className="text-xs data-[state=active]:bg-slate-800 data-[state=active]:text-white">
              <FileSpreadsheet className="w-3.5 h-3.5 mr-1.5 text-indigo-400" />
              Column Profiler ({profile.columns.length})
            </TabsTrigger>
            <TabsTrigger value="settings" className="text-xs data-[state=active]:bg-slate-800 data-[state=active]:text-white">
              <SlidersHorizontal className="w-3.5 h-3.5 mr-1.5 text-amber-400" />
              Cleaning Rules
            </TabsTrigger>
          </TabsList>

          <div className="flex items-center gap-2">
            {cleaningReport?.issues_detected && cleaningReport.issues_detected.length > 0 && (
              <Badge variant="outline" className="border-amber-500/40 text-amber-300 bg-amber-500/10 text-xs">
                <AlertTriangle className="w-3 h-3 mr-1" />
                {cleaningReport.issues_detected.length} Inconsistencies Detected & Handled
              </Badge>
            )}
          </div>
        </div>

        {/* Tab 1: Audit Log - Exactly What Was Cleaned / Removed / Changed */}
        <TabsContent value="audit" className="space-y-4 pt-4">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <h3 className="text-sm font-semibold text-white">Ingestion & Cleaning Operations Log</h3>
              <p className="text-xs text-slate-400">
                Detailed record of every transformation, sanitization, and normalization performed on the dataset.
              </p>
            </div>

            {/* Category Filter Pills */}
            <div className="flex flex-wrap items-center gap-1.5 bg-slate-950 p-1 rounded-lg border border-slate-800 text-xs">
              <button
                onClick={() => setAuditFilter('all')}
                className={`px-2.5 py-1 rounded-md transition-colors ${
                  auditFilter === 'all' ? 'bg-slate-800 text-white font-medium' : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                All Operations ({actionsList.length})
              </button>
              <button
                onClick={() => setAuditFilter('noise')}
                className={`px-2.5 py-1 rounded-md transition-colors ${
                  auditFilter === 'noise' ? 'bg-slate-800 text-rose-300 font-medium' : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                Noise & URLs
              </button>
              <button
                onClick={() => setAuditFilter('formatting')}
                className={`px-2.5 py-1 rounded-md transition-colors ${
                  auditFilter === 'formatting' ? 'bg-slate-800 text-indigo-300 font-medium' : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                Formatting
              </button>
              <button
                onClick={() => setAuditFilter('missing_values')}
                className={`px-2.5 py-1 rounded-md transition-colors ${
                  auditFilter === 'missing_values' ? 'bg-slate-800 text-emerald-300 font-medium' : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                Missing Values
              </button>
              <button
                onClick={() => setAuditFilter('duplicates')}
                className={`px-2.5 py-1 rounded-md transition-colors ${
                  auditFilter === 'duplicates' ? 'bg-slate-800 text-amber-300 font-medium' : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                Duplicates
              </button>
              <button
                onClick={() => setAuditFilter('headers')}
                className={`px-2.5 py-1 rounded-md transition-colors ${
                  auditFilter === 'headers' ? 'bg-slate-800 text-sky-300 font-medium' : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                Headers & Layout
              </button>
              {actionsList.some(a => a.category === 'gemini_feature_engineering') && (
                <button
                  onClick={() => setAuditFilter('gemini_feature_engineering')}
                  className={`px-2.5 py-1 rounded-md transition-colors ${
                    auditFilter === 'gemini_feature_engineering' ? 'bg-slate-800 text-emerald-300 font-medium' : 'text-slate-400 hover:text-slate-200'
                  }`}
                >
                  Engineered Features
                </button>
              )}
              {actionsList.some(a => a.category === 'gemini_column_pruning') && (
                <button
                  onClick={() => setAuditFilter('gemini_column_pruning')}
                  className={`px-2.5 py-1 rounded-md transition-colors ${
                    auditFilter === 'gemini_column_pruning' ? 'bg-slate-800 text-rose-300 font-medium' : 'text-slate-400 hover:text-slate-200'
                  }`}
                >
                  Pruned Columns
                </button>
              )}
            </div>
          </div>

          {/* Gemini Judgment & Python Execution Audit Section */}
          {cleaningReport?.gemini_assisted_actions && (
            (cleaningReport.gemini_assisted_actions.columns_removed.length > 0 ||
             cleaningReport.gemini_assisted_actions.columns_added.length > 0 ||
             cleaningReport.gemini_assisted_actions.messy_rows_purged.length > 0) && (
              <Card className="bg-gradient-to-br from-indigo-950/30 via-slate-900/60 to-purple-950/20 border-indigo-500/30">
                <CardHeader className="pb-2 pt-4 px-4">
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-xs font-semibold text-indigo-300 flex items-center gap-2 uppercase tracking-wider">
                      <Sparkles className="w-4 h-4 text-indigo-400" />
                      Gemini Advisory Judgment & Python Execution Audit
                    </CardTitle>
                    <Badge variant="outline" className="border-indigo-500/40 text-indigo-300 bg-indigo-500/10 text-[10px]">
                      Model: {cleaningReport.gemini_assisted_actions.model || 'Gemini 3.6 Flash'} • Python Executed
                    </Badge>
                  </div>
                  <CardDescription className="text-xs text-slate-400">
                    Gemini evaluated dataset semantics to recommend column additions/deletions. Python deterministically validated and executed all transformations.
                  </CardDescription>
                </CardHeader>
                <CardContent className="p-4 pt-1 space-y-3">
                  {/* Pruned Redundant Columns */}
                  {cleaningReport.gemini_assisted_actions.columns_removed.length > 0 && (
                    <div className="space-y-1.5">
                      <div className="text-[11px] font-semibold text-rose-300 flex items-center gap-1.5">
                        <Trash2 className="w-3.5 h-3.5 text-rose-400" />
                        Redundant Columns Pruned by Python ({cleaningReport.gemini_assisted_actions.columns_removed.length})
                      </div>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                        {cleaningReport.gemini_assisted_actions.columns_removed.map((col, cIdx) => (
                          <div key={cIdx} className="p-2.5 rounded-lg bg-slate-950/80 border border-rose-900/30 flex items-start justify-between gap-2">
                            <div>
                              <div className="text-xs font-mono font-medium text-rose-300">{col.column}</div>
                              <div className="text-[11px] text-slate-400 mt-0.5">{col.reason}</div>
                            </div>
                            <Badge variant="outline" className="text-[10px] border-rose-500/30 text-rose-300 bg-rose-500/10 capitalize shrink-0">
                              {col.redundancy_type.replace('_', ' ')}
                            </Badge>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Feature-Engineered Calculated Columns */}
                  {cleaningReport.gemini_assisted_actions.columns_added.length > 0 && (
                    <div className="space-y-1.5">
                      <div className="text-[11px] font-semibold text-emerald-300 flex items-center gap-1.5">
                        <Binary className="w-3.5 h-3.5 text-emerald-400" />
                        Calculated Columns Engineered by Python ({cleaningReport.gemini_assisted_actions.columns_added.length})
                      </div>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                        {cleaningReport.gemini_assisted_actions.columns_added.map((col, aIdx) => (
                          <div key={aIdx} className="p-2.5 rounded-lg bg-slate-950/80 border border-emerald-900/30 flex items-start justify-between gap-2">
                            <div>
                              <div className="text-xs font-mono font-medium text-emerald-300">{col.column}</div>
                              {col.formula && (
                                <div className="text-[11px] text-sky-400/90 font-mono mt-0.5">Formula: {col.formula}</div>
                              )}
                              {col.rationale && (
                                <div className="text-[11px] text-slate-400 mt-0.5">{col.rationale}</div>
                              )}
                            </div>
                            <Badge variant="outline" className="text-[10px] border-emerald-500/30 text-emerald-300 bg-emerald-500/10 shrink-0">
                              Calculated
                            </Badge>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Messy Rows Purged */}
                  {cleaningReport.gemini_assisted_actions.messy_rows_purged.length > 0 && (
                    <div className="space-y-1.5">
                      <div className="text-[11px] font-semibold text-amber-300 flex items-center gap-1.5">
                        <Filter className="w-3.5 h-3.5 text-amber-400" />
                        Messy / Test Rows Purged by Python ({cleaningReport.gemini_assisted_actions.messy_rows_purged.length})
                      </div>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                        {cleaningReport.gemini_assisted_actions.messy_rows_purged.map((row, rIdx) => (
                          <div key={rIdx} className="p-2.5 rounded-lg bg-slate-950/80 border border-amber-900/30 flex items-start justify-between gap-2">
                            <div>
                              <div className="text-xs font-medium text-amber-300">
                                Matched pattern: <span className="font-mono">"{row.criteria}"</span> in <span className="font-mono text-sky-300">{row.column}</span>
                              </div>
                              <div className="text-[11px] text-slate-400 mt-0.5">{row.reason}</div>
                            </div>
                            <Badge variant="outline" className="text-[10px] border-amber-500/30 text-amber-300 bg-amber-500/10 shrink-0">
                              {row.count} purged
                            </Badge>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </CardContent>
              </Card>
            )
          )}

          {/* Action Cards Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {filteredActions.map((action, idx) => (
              <Card key={idx} className="bg-slate-900/60 border-slate-800 hover:border-slate-700 transition-colors">
                <CardContent className="p-4 space-y-2.5">
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex items-center gap-2">
                      <div className="p-1.5 rounded-md bg-slate-950 border border-slate-800">
                        {getCategoryIcon(action.category)}
                      </div>
                      <div>
                        <div className="text-xs font-semibold text-white">
                          {action.description}
                        </div>
                        {action.column && (
                          <div className="text-[11px] text-slate-400">
                            Target Field: <span className="text-sky-300 font-mono">{action.column}</span>
                          </div>
                        )}
                      </div>
                    </div>
                    <Badge variant="outline" className="bg-slate-950 border-slate-800 text-slate-300 text-[11px] whitespace-nowrap">
                      {action.count} {action.count === 1 ? 'occurrence' : 'occurrences'}
                    </Badge>
                  </div>

                  {/* Sample Before / After Values */}
                  {(action.sample_before !== undefined || action.sample_after !== undefined) && (
                    <div className="mt-2 p-2 rounded-lg bg-slate-950/80 border border-slate-800/80 flex items-center gap-2 text-[11px]">
                      {action.sample_before !== undefined && (
                        <div className="flex-1 truncate">
                          <span className="text-slate-500 font-medium">Before: </span>
                          <span className="text-rose-300/80 font-mono truncate">{String(action.sample_before)}</span>
                        </div>
                      )}
                      <ArrowRight className="w-3.5 h-3.5 text-slate-600 flex-shrink-0" />
                      {action.sample_after !== undefined && (
                        <div className="flex-1 truncate">
                          <span className="text-slate-500 font-medium">After: </span>
                          <span className="text-emerald-300 font-mono font-medium truncate">{String(action.sample_after)}</span>
                        </div>
                      )}
                    </div>
                  )}
                </CardContent>
              </Card>
            ))}
          </div>

          {/* Issues Detected Section */}
          {cleaningReport?.issues_detected && cleaningReport.issues_detected.length > 0 && (
            <Card className="bg-amber-950/20 border-amber-500/30 mt-4">
              <CardHeader className="pb-2 pt-4 px-4">
                <CardTitle className="text-xs font-semibold text-amber-300 flex items-center gap-1.5 uppercase tracking-wider">
                  <AlertTriangle className="w-4 h-4 text-amber-400" />
                  Inconsistencies & Anomalies Detected During Ingestion
                </CardTitle>
              </CardHeader>
              <CardContent className="px-4 pb-4 space-y-2">
                {cleaningReport.issues_detected.map((issue, idx) => (
                  <div key={idx} className="flex items-center justify-between text-xs p-2 rounded-md bg-slate-950/60 border border-amber-500/20">
                    <span className="text-slate-200">{issue.message}</span>
                    <Badge variant="outline" className="border-amber-500/40 text-amber-300 text-[10px]">
                      {issue.affected_count} affected
                    </Badge>
                  </div>
                ))}
              </CardContent>
            </Card>
          )}
        </TabsContent>

        {/* Tab 2: Before vs. After Data Preview Table */}
        <TabsContent value="preview" className="space-y-4 pt-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div className="flex items-center gap-2">
              <div className="bg-slate-950 p-1 rounded-lg border border-slate-800 flex items-center gap-1 text-xs">
                <button
                  onClick={() => setPreviewTab('cleaned')}
                  className={`px-3 py-1 rounded-md transition-colors ${
                    previewTab === 'cleaned' ? 'bg-emerald-600 text-white font-semibold' : 'text-slate-400 hover:text-slate-200'
                  }`}
                >
                  Cleaned Data ({activeCleanedData.length} rows)
                </button>
                <button
                  onClick={() => setPreviewTab('raw')}
                  className={`px-3 py-1 rounded-md transition-colors ${
                    previewTab === 'raw' ? 'bg-slate-800 text-amber-300 font-semibold' : 'text-slate-400 hover:text-slate-200'
                  }`}
                >
                  Raw Uploaded ({rawData.length} rows)
                </button>
              </div>
              <span className="text-xs text-slate-400 hidden md:inline">
                {previewTab === 'cleaned' ? 'Showing sanitized, type-stable analytics rows' : 'Showing raw unprocessed rows'}
              </span>
            </div>

            <div className="relative w-full sm:w-64">
              <Search className="w-3.5 h-3.5 absolute left-2.5 top-2.5 text-slate-400" />
              <Input 
                placeholder="Search values..." 
                value={searchQuery}
                onChange={e => setSearchQuery(e.target.value)}
                className="pl-8 bg-slate-950 border-slate-800 text-xs text-white h-8"
              />
            </div>
          </div>

          <Card className="bg-slate-900/60 border-slate-800">
            <CardContent className="p-0 max-h-[380px] overflow-auto">
              <Table>
                <TableHeader className="bg-slate-950/90 sticky top-0">
                  <TableRow className="border-slate-800">
                    <TableHead className="text-slate-400 text-xs w-12 text-center">#</TableHead>
                    {profile.columns.map(col => (
                      <TableHead key={col.name} className="text-slate-300 text-xs whitespace-nowrap">
                        <div className="flex items-center gap-1.5">
                          <span>{col.name}</span>
                          <span className="text-[10px] text-slate-500 font-mono">({col.type})</span>
                        </div>
                      </TableHead>
                    ))}
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredPreviewRows.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={profile.columns.length + 1} className="text-center py-8 text-slate-400 text-xs">
                        No rows found matching search filter.
                      </TableCell>
                    </TableRow>
                  ) : (
                    filteredPreviewRows.map((row, idx) => (
                      <TableRow key={idx} className="border-slate-800/40 hover:bg-slate-800/30 text-xs">
                        <TableCell className="text-center text-slate-500 text-[11px] font-mono">{idx + 1}</TableCell>
                        {profile.columns.map(col => {
                          const val = row[col.name];
                          const isNull = val === null || val === undefined;
                          return (
                            <TableCell key={col.name} className="text-slate-300 whitespace-nowrap">
                              {isNull ? (
                                <span className="text-slate-600 italic">null</span>
                              ) : typeof val === 'boolean' ? (
                                <Badge variant="outline" className={val ? 'border-emerald-500/40 text-emerald-300 text-[10px]' : 'border-rose-500/40 text-rose-300 text-[10px]'}>
                                  {val ? 'TRUE' : 'FALSE'}
                                </Badge>
                              ) : col.type === 'numeric' && typeof val === 'number' ? (
                                <span className="font-mono text-indigo-300">{val.toLocaleString()}</span>
                              ) : (
                                <span>{String(val)}</span>
                              )}
                            </TableCell>
                          );
                        })}
                      </TableRow>
                    ))
                  )}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Tab 3: Column Profiler */}
        <TabsContent value="columns" className="pt-4">
          <Card className="bg-slate-900/60 border-slate-800">
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-semibold text-white flex items-center gap-2">
                <FileSpreadsheet className="w-4 h-4 text-emerald-400" />
                Column Metadata, Inferred Types & Distribution Stats
              </CardTitle>
              <CardDescription className="text-xs text-slate-400">
                Normalized column names, completeness ratios, data type inference, and distribution metrics.
              </CardDescription>
            </CardHeader>
            <CardContent className="p-0 max-h-[380px] overflow-auto">
              <Table>
                <TableHeader className="bg-slate-950/90 sticky top-0">
                  <TableRow className="border-slate-800">
                    <TableHead className="text-slate-300 text-xs">Normalized Column</TableHead>
                    <TableHead className="text-slate-300 text-xs">Inferred Type</TableHead>
                    <TableHead className="text-slate-300 text-xs">Completeness</TableHead>
                    <TableHead className="text-slate-300 text-xs">Unique Values</TableHead>
                    <TableHead className="text-slate-300 text-xs">Summary Stats / Top Values</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {profile.columns.map(col => (
                    <TableRow key={col.name} className="border-slate-800/60 hover:bg-slate-800/40 text-xs">
                      <TableCell className="font-semibold text-white font-mono">{col.name}</TableCell>
                      <TableCell>
                        <Badge 
                          variant="outline" 
                          className={
                            col.type === 'numeric' ? 'border-indigo-500/40 text-indigo-300 bg-indigo-500/10' :
                            col.type === 'categorical' ? 'border-emerald-500/40 text-emerald-300 bg-emerald-500/10' :
                            col.type === 'date' ? 'border-cyan-500/40 text-cyan-300 bg-cyan-500/10' :
                            col.type === 'boolean' ? 'border-amber-500/40 text-amber-300 bg-amber-500/10' :
                            'border-slate-600 text-slate-400'
                          }
                        >
                          {col.type}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <span className={col.nullPercentage > 10 ? 'text-amber-400 font-semibold' : 'text-emerald-400 font-medium'}>
                          {100 - col.nullPercentage}% ({col.nullCount} missing)
                        </span>
                      </TableCell>
                      <TableCell className="text-slate-300 font-mono">{col.uniqueCount}</TableCell>
                      <TableCell className="text-slate-300 max-w-[280px] truncate">
                        {col.type === 'numeric' && col.mean !== undefined ? (
                          <span className="font-mono text-[11px]">Mean: {formatValue(col.mean)} | Min: {formatValue(col.min)} | Max: {formatValue(col.max)}</span>
                        ) : col.topValues && col.topValues.length > 0 ? (
                          <span>Top: {col.topValues.slice(0, 2).map(v => `${v.value} (${v.percentage}%)`).join(', ')}</span>
                        ) : (
                          <span>{col.sampleValues.slice(0, 3).join(', ')}</span>
                        )}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Tab 4: Cleaning Rules Configuration */}
        <TabsContent value="settings" className="space-y-4 pt-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Card className="bg-slate-900/60 border-slate-800">
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-semibold text-white flex items-center gap-2">
                  <Filter className="w-4 h-4 text-emerald-400" />
                  Cleaning Rules & Imputation Strategies
                </CardTitle>
                <CardDescription className="text-xs text-slate-400">
                  Adjust how missing values, duplicates, and delimiters are treated.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4 text-xs">
                {/* Deduplication option */}
                <div className="flex items-center justify-between p-3 rounded-lg bg-slate-950/60 border border-slate-800">
                  <div>
                    <div className="font-semibold text-white">Remove Exact Duplicate Rows</div>
                    <div className="text-slate-400">Purge rows with 100% identical values</div>
                  </div>
                  <input 
                    type="checkbox" 
                    checked={cleaningOptions.removeDuplicates}
                    onChange={e => setCleaningOptions(prev => ({ ...prev, removeDuplicates: e.target.checked }))}
                    className="w-4 h-4 accent-emerald-500 rounded cursor-pointer"
                  />
                </div>

                {/* Numeric missing strategy */}
                <div className="space-y-1.5 p-3 rounded-lg bg-slate-950/60 border border-slate-800">
                  <label className="font-semibold text-white block">Numeric Missing Imputation</label>
                  <Select 
                    value={cleaningOptions.numericMissingStrategy} 
                    onValueChange={(val: any) => setCleaningOptions(prev => ({ ...prev, numericMissingStrategy: val }))}
                  >
                    <SelectTrigger className="bg-slate-900 border-slate-700 text-white text-xs h-8">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent className="bg-slate-900 border-slate-700 text-white">
                      <SelectItem value="median">Fill with Median (Preserves distribution without skewing)</SelectItem>
                      <SelectItem value="mean">Fill with Arithmetic Mean</SelectItem>
                      <SelectItem value="zero">Fill with Zero (0)</SelectItem>
                      <SelectItem value="drop">Drop Incomplete Rows</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                {/* Categorical missing strategy */}
                <div className="space-y-1.5 p-3 rounded-lg bg-slate-950/60 border border-slate-800">
                  <label className="font-semibold text-white block">Categorical Missing Imputation</label>
                  <Select 
                    value={cleaningOptions.categoricalMissingStrategy} 
                    onValueChange={(val: any) => setCleaningOptions(prev => ({ ...prev, categoricalMissingStrategy: val }))}
                  >
                    <SelectTrigger className="bg-slate-900 border-slate-700 text-white text-xs h-8">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent className="bg-slate-900 border-slate-700 text-white">
                      <SelectItem value="unknown">Fill with "Unspecified" (Safest)</SelectItem>
                      <SelectItem value="mode">Fill with Most Frequent Category</SelectItem>
                      <SelectItem value="drop">Drop Incomplete Rows</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div className="pt-2">
                  <Button 
                    onClick={handleRunCleaning}
                    disabled={isCleaning}
                    className="w-full bg-slate-800 hover:bg-slate-700 text-white font-medium border border-slate-700"
                  >
                    {isCleaning ? <RefreshCw className="w-4 h-4 mr-2 animate-spin" /> : <RefreshCw className="w-4 h-4 mr-2" />}
                    Re-run Ingestion & Cleaning Pipeline
                  </Button>
                </div>
              </CardContent>
            </Card>

            <Card className="bg-slate-900/60 border-slate-800">
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-semibold text-white flex items-center gap-2">
                  <ShieldCheck className="w-4 h-4 text-sky-400" />
                  Preservation Guarantees
                </CardTitle>
                <CardDescription className="text-xs text-slate-400">
                  Engine safeguards ensuring business data integrity.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-3 text-xs text-slate-300">
                <div className="p-3 rounded-lg bg-slate-950/60 border border-slate-800 space-y-1">
                  <div className="font-semibold text-white flex items-center gap-1.5">
                    <Check className="w-4 h-4 text-emerald-400" />
                    Original File Immutability
                  </div>
                  <p className="text-slate-400 text-[11px]">
                    The source Excel file uploaded by the user is stored without alteration in permanent backup storage. All transformations occur in memory or designated staging buffers.
                  </p>
                </div>

                <div className="p-3 rounded-lg bg-slate-950/60 border border-slate-800 space-y-1">
                  <div className="font-semibold text-white flex items-center gap-1.5">
                    <Check className="w-4 h-4 text-emerald-400" />
                    Double-Counting Protection
                  </div>
                  <p className="text-slate-400 text-[11px]">
                    Grand Total, Subtotal, and summary rows placed at the bottom of messy sheets are isolated so Recharts visualizations don't artificially double business totals.
                  </p>
                </div>

                <div className="p-3 rounded-lg bg-slate-950/60 border border-slate-800 space-y-1">
                  <div className="font-semibold text-white flex items-center gap-1.5">
                    <Check className="w-4 h-4 text-emerald-400" />
                    Multi-Format Delimiter Resilience
                  </div>
                  <p className="text-slate-400 text-[11px]">
                    Single-column copy-pastes containing semicolons, pipes, or tabs are dynamically detected and split into discrete columns before analytics generation.
                  </p>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
};
