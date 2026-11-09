import React, { useState, useEffect, useMemo } from 'react';
import {
  BarChart,
  Bar,
  LineChart,
  Line,
  AreaChart,
  Area,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  Sparkles,
  Send,
  HelpCircle,
  Clock,
  CheckCircle2,
  TrendingUp,
  Table as TableIcon,
  BarChart3,
  Trash2,
  Brain,
  Lightbulb,
  ArrowUpRight,
  Database,
} from 'lucide-react';
import {
  questionAnalysisService,
  QuestionAnalysisResponse,
  QuestionChartItem,
  QuestionHistoryEntry,
} from '@/services/question-analysis.service';

interface QuestionChartStudioProps {
  data: Record<string, any>[];
  datasetName?: string;
  initialQuestion?: string;
  onQuestionAnalyzed?: (result: QuestionAnalysisResponse) => void;
  className?: string;
}

const PALETTE = ['#3b82f6', '#10b981', '#8b5cf6', '#f59e0b', '#ec4899', '#06b6d4', '#6366f1'];

export const QuestionChartStudio: React.FC<QuestionChartStudioProps> = ({
  data,
  datasetName = 'Dataset',
  initialQuestion,
  onQuestionAnalyzed,
  className = '',
}) => {
  const [questionInput, setQuestionInput] = useState<string>(
    initialQuestion || 'Show sales by year and which month had the highest sales.'
  );
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [history, setHistory] = useState<QuestionHistoryEntry[]>([]);
  const [activeQuestionId, setActiveQuestionId] = useState<string | null>(null);
  const [viewModes, setViewModes] = useState<Record<string, 'chart' | 'table'>>({});

  // Generate dataset-aware suggested questions
  const suggestions = useMemo(() => {
    return questionAnalysisService.generateSampleQuestions(data);
  }, [data]);

  // Execute Question Analysis
  const handleRunAnalysis = async (queryToRun?: string) => {
    const query = (queryToRun || questionInput).trim();
    if (!query) return;

    if (!data || data.length === 0) {
      setError('Please upload or select a dataset first.');
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const res = await questionAnalysisService.analyzeQuestion(data, query, datasetName);
      const newEntry: QuestionHistoryEntry = {
        id: `q_${Date.now()}`,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        question: query,
        result: res,
      };

      setHistory((prev) => [newEntry, ...prev]);
      setActiveQuestionId(newEntry.id);
      setQuestionInput('');
      onQuestionAnalyzed?.(res);
    } catch (err) {
      console.error('Question analysis error:', err);
      setError(err instanceof Error ? err.message : 'Failed to analyze question');
    } finally {
      setIsLoading(false);
    }
  };

  const initialRunRef = React.useRef(false);

  // Run initial question once if data is available and no history yet
  useEffect(() => {
    if (data && data.length > 0 && !initialRunRef.current && initialQuestion) {
      initialRunRef.current = true;
      handleRunAnalysis(initialQuestion);
    }
  }, [data, initialQuestion]);

  // Current active result
  const activeEntry = useMemo(() => {
    if (!activeQuestionId) return history[0] || null;
    return history.find((h) => h.id === activeQuestionId) || history[0] || null;
  }, [history, activeQuestionId]);

  const toggleViewMode = (chartId: string) => {
    setViewModes((prev) => ({
      ...prev,
      [chartId]: prev[chartId] === 'table' ? 'chart' : 'table',
    }));
  };

  const removeHistoryEntry = (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    setHistory((prev) => {
      const remaining = prev.filter((h) => h.id !== id);
      if (activeQuestionId === id) {
        setActiveQuestionId(remaining[0]?.id || null);
      }
      return remaining;
    });
  };

  return (
    <div className={`space-y-6 ${className}`}>
      {/* 1. Primary Question Studio Input Card */}
      <Card className="bg-slate-900/90 border-indigo-500/30 shadow-xl backdrop-blur-md overflow-hidden">
        <div className="bg-gradient-to-r from-indigo-900/40 via-purple-900/30 to-slate-900/40 p-5 sm:p-6 border-b border-white/10">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-4">
            <div className="flex items-center gap-3">
              <div className="p-2.5 bg-indigo-500/20 text-indigo-400 rounded-xl border border-indigo-500/30 shadow-inner">
                <Sparkles className="w-5 h-5 text-indigo-300 animate-pulse" />
              </div>
              <div>
                <h3 className="text-xl font-bold text-white flex items-center gap-2">
                  Question-Driven Chart Studio
                  <Badge variant="outline" className="border-indigo-400/40 text-indigo-300 bg-indigo-500/10 text-xs py-0.5">
                    Python Engine + Gemini AI
                  </Badge>
                </h3>
                <p className="text-xs text-slate-300 mt-0.5">
                  Ask what you want to analyze. Core calculations and chart data are calculated in Python; AI interprets the strategic output.
                </p>
              </div>
            </div>

            <div className="flex items-center gap-2 text-xs text-slate-400 bg-slate-950/60 px-3 py-1.5 rounded-lg border border-slate-800">
              <Database className="w-3.5 h-3.5 text-emerald-400" />
              <span>Dataset: <strong className="text-slate-200">{datasetName}</strong> ({data.length} rows)</span>
            </div>
          </div>

          {/* Search/Query Input */}
          <div className="relative flex items-center gap-2">
            <div className="relative flex-1">
              <HelpCircle className="w-5 h-5 absolute left-3.5 top-3.5 text-indigo-400/70 pointer-events-none" />
              <Input
                value={questionInput}
                onChange={(e) => setQuestionInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !isLoading) {
                    handleRunAnalysis();
                  }
                }}
                placeholder="e.g. Show sales by year and which month had the highest sales."
                className="pl-11 pr-4 py-6 bg-slate-950/90 border-indigo-500/40 text-white placeholder:text-slate-500 text-sm sm:text-base focus-visible:ring-indigo-500 focus-visible:border-indigo-400 shadow-inner rounded-xl"
              />
            </div>
            <Button
              onClick={() => handleRunAnalysis()}
              disabled={isLoading || !questionInput.trim() || data.length === 0}
              className="h-12 px-6 bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 text-white font-semibold text-sm rounded-xl shadow-lg shadow-indigo-500/25 transition-all duration-200 disabled:opacity-50"
            >
              {isLoading ? (
                <div className="flex items-center gap-2">
                  <div className="animate-spin h-4 w-4 border-2 border-white border-t-transparent rounded-full" />
                  <span>Computing...</span>
                </div>
              ) : (
                <div className="flex items-center gap-2">
                  <span>Analyze Question</span>
                  <Send className="w-4 h-4" />
                </div>
              )}
            </Button>
          </div>

          {/* Smart Suggested Chips */}
          <div className="mt-4 flex flex-wrap items-center gap-2">
            <span className="text-xs font-medium text-indigo-300 flex items-center gap-1 mr-1">
              <Lightbulb className="w-3.5 h-3.5 text-amber-400" /> Suggestions:
            </span>
            {suggestions.map((sug, i) => (
              <button
                key={i}
                type="button"
                onClick={() => {
                  setQuestionInput(sug);
                  handleRunAnalysis(sug);
                }}
                disabled={isLoading}
                className="text-xs px-3 py-1.5 rounded-full bg-slate-800/80 hover:bg-indigo-600/30 text-slate-300 hover:text-white border border-slate-700 hover:border-indigo-500/50 transition-all flex items-center gap-1.5 shadow-sm"
              >
                <span>{sug}</span>
                <ArrowUpRight className="w-3 h-3 text-indigo-400 opacity-70" />
              </button>
            ))}
          </div>
        </div>

        {/* Question History Drawer / Tabs */}
        {history.length > 0 && (
          <div className="px-6 py-3 bg-slate-950/80 border-t border-slate-800/80 flex items-center justify-between gap-4 overflow-x-auto">
            <div className="flex items-center gap-2">
              <Clock className="w-3.5 h-3.5 text-slate-400" />
              <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
                Question History ({history.length}):
              </span>
            </div>

            <div className="flex items-center gap-2 overflow-x-auto py-1">
              {history.map((h) => {
                const isActive = activeEntry?.id === h.id;
                return (
                  <div
                    key={h.id}
                    onClick={() => setActiveQuestionId(h.id)}
                    className={`cursor-pointer group flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-medium transition-all whitespace-nowrap border ${
                      isActive
                        ? 'bg-indigo-600 text-white border-indigo-400 shadow-md shadow-indigo-600/30'
                        : 'bg-slate-900 text-slate-300 border-slate-800 hover:bg-slate-800 hover:text-white'
                    }`}
                  >
                    <span className="max-w-[200px] truncate">{h.question}</span>
                    <Badge
                      variant="outline"
                      className={`text-[10px] py-0 px-1.5 ${
                        isActive ? 'border-indigo-200 text-white bg-indigo-700/50' : 'border-slate-700 text-slate-400'
                      }`}
                    >
                      {h.result.charts.length} {h.result.charts.length === 1 ? 'chart' : 'charts'}
                    </Badge>
                    <button
                      type="button"
                      onClick={(e) => removeHistoryEntry(h.id, e)}
                      className="opacity-60 hover:opacity-100 hover:text-red-300 ml-0.5"
                    >
                      <Trash2 className="w-3 h-3" />
                    </button>
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </Card>

      {/* Error state */}
      {error && (
        <Card className="bg-red-950/30 border-red-500/40 p-4">
          <div className="flex items-center gap-3 text-red-300 text-sm">
            <div className="p-2 bg-red-500/20 rounded-lg text-red-400 font-bold">!</div>
            <div>
              <div className="font-semibold">Analysis Notice</div>
              <div>{error}</div>
            </div>
          </div>
        </Card>
      )}

      {/* 2. Active Question Results Display */}
      {activeEntry && (
        <div className="space-y-6">
          {/* Active Question Banner */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 p-4 rounded-xl bg-slate-900/60 border border-slate-800">
            <div>
              <div className="text-xs text-indigo-400 font-semibold tracking-wider uppercase mb-1">
                Active Analysis Target
              </div>
              <h4 className="text-lg font-bold text-white">"{activeEntry.question}"</h4>
            </div>

            <div className="flex items-center gap-2">
              <Badge className="bg-emerald-500/20 text-emerald-300 border-emerald-500/40 text-xs px-2.5 py-1">
                <CheckCircle2 className="w-3.5 h-3.5 mr-1" />
                Python Exact Calculations
              </Badge>
              <Badge className="bg-purple-500/20 text-purple-300 border-purple-500/40 text-xs px-2.5 py-1">
                <Brain className="w-3.5 h-3.5 mr-1" />
                {activeEntry.result.ai_interpretation?.model_used || 'Gemini 3.8 Flash'}
              </Badge>
            </div>
          </div>

          {/* Factual Calculated Metrics Cards */}
          {activeEntry.result.key_metrics && activeEntry.result.key_metrics.length > 0 && (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              {activeEntry.result.key_metrics.map((metric, idx) => (
                <Card
                  key={idx}
                  className={`bg-slate-900/90 border ${
                    metric.is_primary ? 'border-amber-500/50 bg-gradient-to-br from-slate-900 to-amber-950/20' : 'border-slate-800'
                  } p-4 shadow-lg`}
                >
                  <div className="flex items-start justify-between">
                    <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
                      {metric.label}
                    </span>
                    {metric.badge && (
                      <Badge className="bg-amber-500/20 text-amber-300 border-amber-500/30 text-[10px]">
                        {metric.badge}
                      </Badge>
                    )}
                  </div>
                  <div className="mt-2 text-2xl font-bold text-white">
                    {metric.formatted || metric.value}
                  </div>
                </Card>
              ))}
            </div>
          )}

          {/* Targeted Charts Grid - ONLY Relevant Charts */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {activeEntry.result.charts.map((chart) => {
              const viewMode = viewModes[chart.id] || 'chart';
              return (
                <Card
                  key={chart.id}
                  className="bg-slate-900/95 border-slate-800 shadow-xl overflow-hidden flex flex-col"
                >
                  <CardHeader className="pb-3 border-b border-slate-800/80 bg-slate-950/40 flex flex-row items-center justify-between gap-2">
                    <div>
                      <div className="flex items-center gap-2">
                        <CardTitle className="text-base sm:text-lg font-bold text-white">
                          {chart.title}
                        </CardTitle>
                        <Badge variant="outline" className="text-[10px] border-indigo-400/40 text-indigo-300 uppercase">
                          {chart.chart_type}
                        </Badge>
                      </div>
                      {chart.subtitle && (
                        <CardDescription className="text-xs text-slate-400 mt-1">
                          {chart.subtitle}
                        </CardDescription>
                      )}
                    </div>

                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => toggleViewMode(chart.id)}
                      className="h-8 px-2.5 text-xs text-slate-400 hover:text-white hover:bg-slate-800"
                    >
                      {viewMode === 'chart' ? (
                        <>
                          <TableIcon className="w-3.5 h-3.5 mr-1" /> Table
                        </>
                      ) : (
                        <>
                          <BarChart3 className="w-3.5 h-3.5 mr-1" /> Chart
                        </>
                      )}
                    </Button>
                  </CardHeader>

                  <CardContent className="p-4 sm:p-6 flex-1 flex flex-col justify-center min-h-[340px]">
                    {viewMode === 'chart' ? (
                      <div className="w-full h-72 sm:h-80">
                        {renderChartComponent(chart)}
                      </div>
                    ) : (
                      <div className="w-full overflow-x-auto max-h-80 border border-slate-800 rounded-lg">
                        <table className="w-full text-xs text-left text-slate-300">
                          <thead className="text-[11px] uppercase bg-slate-950 text-slate-400 border-b border-slate-800 sticky top-0">
                            <tr>
                              {Object.keys(chart.data[0] || {}).map((col) => (
                                <th key={col} className="px-3 py-2 font-semibold">
                                  {col}
                                </th>
                              ))}
                            </tr>
                          </thead>
                          <tbody className="divide-y divide-slate-800/60 bg-slate-900/60">
                            {chart.data.map((row, rIdx) => (
                              <tr key={rIdx} className="hover:bg-slate-800/40">
                                {Object.values(row).map((val, cIdx) => (
                                  <td key={cIdx} className="px-3 py-2">
                                    {typeof val === 'number' ? val.toLocaleString() : String(val ?? '')}
                                  </td>
                                ))}
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    )}

                    {/* Highlight Pill if present */}
                    {chart.highlight_item && (
                      <div className="mt-3 p-2.5 rounded-lg bg-amber-500/10 border border-amber-500/20 flex items-center justify-between text-xs">
                        <span className="text-slate-300">
                          Target Highlight: <strong className="text-amber-300">{chart.highlight_item.value}</strong>
                        </span>
                        <Badge className="bg-amber-500/20 text-amber-300 border-amber-500/40">
                          {chart.highlight_item.label}
                        </Badge>
                      </div>
                    )}
                  </CardContent>
                </Card>
              );
            })}
          </div>

          {/* 3. AI Executive Interpretation Card */}
          {activeEntry.result.ai_interpretation && (
            <Card className="bg-gradient-to-br from-purple-950/40 via-slate-900 to-indigo-950/40 border-purple-500/30 p-6 shadow-2xl">
              <div className="flex items-center justify-between gap-4 mb-4 border-b border-purple-500/20 pb-3">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-purple-500/20 text-purple-300 rounded-lg border border-purple-500/30">
                    <Brain className="w-5 h-5 text-purple-400" />
                  </div>
                  <div>
                    <h3 className="text-lg font-bold text-white">
                      AI Executive Interpretation & Strategic Insights
                    </h3>
                    <p className="text-xs text-purple-200/70">
                      Grounded strictly in Python-verified calculations • No hallucinated metrics
                    </p>
                  </div>
                </div>

                <Badge variant="outline" className="border-purple-400/50 text-purple-200 bg-purple-500/10 text-xs">
                  {activeEntry.result.ai_interpretation.model_used}
                </Badge>
              </div>

              {/* Direct Calculated Answer Callout */}
              <div className="mb-4 p-4 rounded-xl bg-slate-950/70 border border-indigo-500/20">
                <div className="text-xs font-semibold text-indigo-400 uppercase tracking-wider mb-1">
                  Direct Calculated Answer
                </div>
                <div className="text-sm sm:text-base text-white font-medium">
                  {activeEntry.result.direct_answer}
                </div>
              </div>

              {/* Executive Interpretation Narrative */}
              <div className="space-y-3 text-sm text-slate-200 leading-relaxed">
                {activeEntry.result.ai_interpretation.summary.split('\n\n').map((para, pIdx) => (
                  <p key={pIdx}>{para}</p>
                ))}
              </div>

              {/* Actionable Takeaways */}
              {activeEntry.result.ai_interpretation.takeaways &&
                activeEntry.result.ai_interpretation.takeaways.length > 0 && (
                  <div className="mt-6 pt-4 border-t border-purple-500/20">
                    <div className="text-xs font-semibold text-purple-300 uppercase tracking-wider mb-3 flex items-center gap-1.5">
                      <TrendingUp className="w-3.5 h-3.5 text-emerald-400" /> Strategic Recommendations
                    </div>
                    <ul className="space-y-2">
                      {activeEntry.result.ai_interpretation.takeaways.map((item, tIdx) => (
                        <li key={tIdx} className="flex items-start gap-2.5 text-xs sm:text-sm text-slate-300">
                          <CheckCircle2 className="w-4 h-4 text-emerald-400 mt-0.5 flex-shrink-0" />
                          <span>{item}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
            </Card>
          )}
        </div>
      )}

      {/* Empty State when no question has been asked yet */}
      {!activeEntry && !isLoading && (
        <Card className="bg-slate-900/60 border-slate-800 p-12 text-center">
          <div className="max-w-md mx-auto space-y-4">
            <div className="w-14 h-14 rounded-2xl bg-indigo-500/10 text-indigo-400 flex items-center justify-center mx-auto border border-indigo-500/20 shadow-inner">
              <Sparkles className="w-7 h-7" />
            </div>
            <h4 className="text-lg font-bold text-white">Ask your first question to generate charts</h4>
            <p className="text-sm text-slate-400">
              InsightIQ eliminates random charts by generating only the targeted visualizations and calculations needed to answer your questions.
            </p>
            <div className="pt-2">
              <Button
                onClick={() => handleRunAnalysis('Show sales by year and which month had the highest sales.')}
                className="bg-indigo-600 hover:bg-indigo-500 text-white text-xs px-4 py-2"
              >
                Run Example: "Show sales by year and which month had highest sales"
              </Button>
            </div>
          </div>
        </Card>
      )}
    </div>
  );
};

// Sub-component to render appropriate chart type dynamically
function renderChartComponent(chart: QuestionChartItem) {
  const { chart_type, data, x_key, y_keys, x_label, y_label, recharts_config, highlight_item } = chart;
  const primaryMetric = y_keys[0] || 'value';

  const axisStyle = { fontSize: 11, fill: '#94a3b8' };
  const gridStyle = { stroke: '#334155', strokeDasharray: '3 3' };

  switch (chart_type) {
    case 'line':
      return (
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data} margin={{ top: 15, right: 25, left: 15, bottom: 25 }}>
            <CartesianGrid {...gridStyle} />
            <XAxis dataKey={x_key} tick={axisStyle} stroke="#475569" label={{ value: x_label, position: 'insideBottom', offset: -12, fill: '#94a3b8', fontSize: 11 }} />
            <YAxis tick={axisStyle} stroke="#475569" label={{ value: y_label, angle: -90, position: 'insideLeft', offset: 0, fill: '#94a3b8', fontSize: 11 }} />
            <Tooltip
              contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px', color: '#fff', fontSize: '12px' }}
              formatter={(val: any) => [typeof val === 'number' ? `$${val.toLocaleString()}` : val, primaryMetric]}
            />
            <Legend wrapperStyle={{ paddingTop: '10px', fontSize: '12px' }} />
            <Line
              type="monotone"
              dataKey={primaryMetric}
              stroke="#3b82f6"
              strokeWidth={3}
              dot={(props) => {
                const isHighlighted = highlight_item && props.payload[highlight_item.key] === highlight_item.value;
                return (
                  <circle
                    key={props.index}
                    cx={props.cx}
                    cy={props.cy}
                    r={isHighlighted ? 7 : 4}
                    fill={isHighlighted ? '#f59e0b' : '#3b82f6'}
                    stroke="#ffffff"
                    strokeWidth={isHighlighted ? 2.5 : 1.5}
                  />
                );
              }}
              activeDot={{ r: 8, stroke: '#ffffff', strokeWidth: 2 }}
            />
          </LineChart>
        </ResponsiveContainer>
      );

    case 'area':
      return (
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={data} margin={{ top: 15, right: 25, left: 15, bottom: 25 }}>
            <defs>
              <linearGradient id="areaGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#8b5cf6" stopOpacity={0.7} />
                <stop offset="95%" stopColor="#8b5cf6" stopOpacity={0.05} />
              </linearGradient>
            </defs>
            <CartesianGrid {...gridStyle} />
            <XAxis dataKey={x_key} tick={axisStyle} stroke="#475569" label={{ value: x_label, position: 'insideBottom', offset: -12, fill: '#94a3b8', fontSize: 11 }} />
            <YAxis tick={axisStyle} stroke="#475569" label={{ value: y_label, angle: -90, position: 'insideLeft', offset: 0, fill: '#94a3b8', fontSize: 11 }} />
            <Tooltip
              contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px', color: '#fff', fontSize: '12px' }}
              formatter={(val: any) => [typeof val === 'number' ? `$${val.toLocaleString()}` : val, primaryMetric]}
            />
            <Legend wrapperStyle={{ paddingTop: '10px', fontSize: '12px' }} />
            <Area type="monotone" dataKey={primaryMetric} stroke="#8b5cf6" strokeWidth={2.5} fillOpacity={1} fill="url(#areaGradient)" />
          </AreaChart>
        </ResponsiveContainer>
      );

    case 'pie':
      return (
        <ResponsiveContainer width="100%" height="100%">
          <PieChart margin={{ top: 10, right: 10, left: 10, bottom: 20 }}>
            <Tooltip
              contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px', color: '#fff', fontSize: '12px' }}
              formatter={(val: any) => [typeof val === 'number' ? `$${val.toLocaleString()}` : val, primaryMetric]}
            />
            <Legend wrapperStyle={{ fontSize: '12px', paddingTop: '10px' }} />
            <Pie
              data={data}
              dataKey={primaryMetric}
              nameKey={x_key}
              cx="50%"
              cy="50%"
              outerRadius={95}
              innerRadius={45}
              paddingAngle={4}
              label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
            >
              {data.map((_, index) => (
                <Cell key={`cell-${index}`} fill={PALETTE[index % PALETTE.length]} />
              ))}
            </Pie>
          </PieChart>
        </ResponsiveContainer>
      );

    case 'bar':
    default:
      return (
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} margin={{ top: 15, right: 25, left: 15, bottom: 25 }}>
            <CartesianGrid {...gridStyle} />
            <XAxis dataKey={x_key} tick={axisStyle} stroke="#475569" label={{ value: x_label, position: 'insideBottom', offset: -12, fill: '#94a3b8', fontSize: 11 }} />
            <YAxis tick={axisStyle} stroke="#475569" label={{ value: y_label, angle: -90, position: 'insideLeft', offset: 0, fill: '#94a3b8', fontSize: 11 }} />
            <Tooltip
              contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px', color: '#fff', fontSize: '12px' }}
              formatter={(val: any) => [typeof val === 'number' ? `$${val.toLocaleString()}` : val, primaryMetric]}
            />
            <Legend wrapperStyle={{ paddingTop: '10px', fontSize: '12px' }} />
            <Bar dataKey={primaryMetric} fill="#3b82f6" radius={[6, 6, 0, 0]}>
              {data.map((entry, index) => {
                const isHighlighted = highlight_item && entry[highlight_item.key] === highlight_item.value;
                return (
                  <Cell
                    key={`cell-${index}`}
                    fill={isHighlighted ? '#f59e0b' : PALETTE[index % PALETTE.length]}
                  />
                );
              })}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      );
  }
}
