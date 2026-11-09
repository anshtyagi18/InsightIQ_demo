/**
 * Center Canvas Component for Insightia.
 * High-density executive layout: KPI metrics, sample dataset selector,
 * drag-and-drop file uploader, EDA charts, correlation heatmap, and TanStack data grid.
 */

import React, { useState, useMemo } from 'react';
import { 
  BarChart3, 
  Table as TableIcon, 
  Activity, 
  UploadCloud, 
  Sparkles, 
  FileSpreadsheet, 
  ArrowUpRight, 
  Layers, 
  AlertCircle, 
  CheckCircle2, 
  TrendingUp, 
  Zap,
  Info,
  Calendar,
  DollarSign
} from 'lucide-react';
import { 
  ResponsiveContainer, 
  BarChart, 
  Bar, 
  LineChart, 
  Line, 
  XAxis, 
  YAxis, 
  Tooltip, 
  CartesianGrid,
  Cell 
} from 'recharts';
import { DatasetProfile, dataIntelligenceService } from '@/services/data-intelligence.service';
import { DataTable } from './DataTable';
import { toast } from 'sonner';

interface CenterCanvasProps {
  profile: DatasetProfile | null;
  isLoading: boolean;
  onUploadFile: (file: File) => Promise<void>;
  onLoadSample: (sampleId: 'ecommerce_sales' | 'customer_churn' | 'financial_kpi') => Promise<void>;
}

export const CenterCanvas: React.FC<CenterCanvasProps> = ({
  profile,
  isLoading,
  onUploadFile,
  onLoadSample,
}) => {
  const [activeTab, setActiveTab] = useState<'eda' | 'table' | 'stats'>('eda');
  const [selectedHistCol, setSelectedHistCol] = useState<string>('');
  const [isDragging, setIsDragging] = useState(false);

  // Default selected histogram column when profile changes
  React.useEffect(() => {
    if (profile && profile.columns.length > 0) {
      const numCol = profile.columns.find(c => c.type === 'numeric');
      setSelectedHistCol(numCol ? numCol.name : profile.columns[0].name);
    }
  }, [profile]);

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = async (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      const file = e.dataTransfer.files[0];
      await onUploadFile(file);
    }
  };

  const handleFileInput = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      const file = e.target.files[0];
      await onUploadFile(file);
    }
  };

  // Hist data for selected column
  const histData = useMemo(() => {
    if (!profile || !selectedHistCol) return [];
    const col = profile.columns.find(c => c.name === selectedHistCol);
    if (!col) return [];
    return col.top_values || [];
  }, [profile, selectedHistCol]);

  // Numeric columns for correlation heatmap
  const numericCols = useMemo(() => {
    if (!profile) return [];
    return profile.columns.filter(c => c.type === 'numeric');
  }, [profile]);

  return (
    <main className="flex-1 h-full bg-zinc-950 flex flex-col overflow-y-auto">
      {/* Top Banner / Breadcrumb */}
      <div className="p-4 border-b border-zinc-800/80 bg-zinc-950 flex flex-wrap items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-lg font-bold text-zinc-100 tracking-tight">
              {profile ? profile.dataset_name : 'AI Data Analytics Platform'}
            </h1>
            {profile && (
              <span className={`text-xs font-mono px-2.5 py-0.5 rounded border font-semibold ${
                profile.health_score >= 85 
                  ? 'bg-emerald-950/60 text-emerald-400 border-emerald-800/40' 
                  : 'bg-amber-950/60 text-amber-400 border-amber-800/40'
              }`}>
                HEALTH: {profile.health_score}%
              </span>
            )}
          </div>
          <p className="text-sm text-zinc-300 mt-0.5">
            {profile 
              ? `${profile.total_rows.toLocaleString()} records • ${profile.total_cols} dimensions • Deterministic Pandas Engine`
              : 'Enterprise automated EDA, clean pipelines, and grounded multilingual intelligence'
            }
          </p>
        </div>

        {/* Upload Button */}
        <label className="cursor-pointer inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md bg-zinc-900 hover:bg-zinc-800 border border-zinc-800 text-xs font-medium text-zinc-100 transition-colors shadow-sm">
          <UploadCloud className="w-3.5 h-3.5 text-indigo-400" />
          <span>Upload File (.csv, .xlsx, .json)</span>
          <input 
            type="file" 
            accept=".csv,.xlsx,.xls,.json" 
            className="hidden" 
            onChange={handleFileInput}
            disabled={isLoading}
          />
        </label>
      </div>

      <div className="p-4 space-y-4">
        {/* Sample Datasets Quick Selector (Zero Blank State) */}
        <div className="bg-zinc-900/40 border border-zinc-800/80 rounded-lg p-3 flex flex-wrap items-center justify-between gap-3">
          <span className="text-xs font-medium text-zinc-400 flex items-center gap-1.5">
            <Zap className="w-3.5 h-3.5 text-amber-400" />
            Quick Test Datasets:
          </span>
          <div className="flex flex-wrap items-center gap-2">
            <button
              onClick={() => onLoadSample('ecommerce_sales')}
              disabled={isLoading}
              className="text-xs px-2.5 py-1 rounded bg-zinc-900 hover:bg-zinc-800 border border-zinc-800 text-zinc-200 hover:text-white transition-colors disabled:opacity-40"
            >
              🛍️ Global E-Commerce (1k rows)
            </button>
            <button
              onClick={() => onLoadSample('customer_churn')}
              disabled={isLoading}
              className="text-xs px-2.5 py-1 rounded bg-zinc-900 hover:bg-zinc-800 border border-zinc-800 text-zinc-200 hover:text-white transition-colors disabled:opacity-40"
            >
              🔄 SaaS Churn (850 rows)
            </button>
            <button
              onClick={() => onLoadSample('financial_kpi')}
              disabled={isLoading}
              className="text-xs px-2.5 py-1 rounded bg-zinc-900 hover:bg-zinc-800 border border-zinc-800 text-zinc-200 hover:text-white transition-colors disabled:opacity-40"
            >
              📊 Financial Ledger (500 rows)
            </button>
          </div>
        </div>

        {/* Empty Upload State if no dataset */}
        {!profile && (
          <div
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            className={`border-2 border-dashed rounded-xl p-12 text-center transition-colors flex flex-col items-center justify-center ${
              isDragging ? 'border-indigo-500 bg-indigo-950/20' : 'border-zinc-800 bg-zinc-900/20'
            }`}
          >
            <div className="w-12 h-12 rounded-full bg-zinc-900 border border-zinc-800 flex items-center justify-center text-zinc-400 mb-3">
              <UploadCloud className="w-6 h-6 text-indigo-400" />
            </div>
            <h3 className="text-sm font-semibold text-zinc-200 mb-1">
              Drag and drop your dataset file here
            </h3>
            <p className="text-xs text-zinc-500 max-w-sm mb-4">
              Supports CSV, Excel (.xlsx, .xls), and JSON up to 50MB. Auto-detects schema, missingness, and statistical health.
            </p>
            <label className="cursor-pointer inline-flex items-center gap-2 px-4 py-2 rounded-md bg-indigo-600 hover:bg-indigo-500 text-xs font-semibold text-white transition-colors shadow-sm">
              <UploadCloud className="w-4 h-4" />
              <span>Browse Local Files</span>
              <input 
                type="file" 
                accept=".csv,.xlsx,.xls,.json" 
                className="hidden" 
                onChange={handleFileInput}
                disabled={isLoading}
              />
            </label>
          </div>
        )}

        {/* Active Dataset Dashboard */}
        {profile && (
          <>
            {/* KPI Cards Strip */}
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
              <div className="p-3 bg-zinc-900 border border-zinc-800 rounded-lg">
                <span className="text-xs text-zinc-400 font-semibold uppercase tracking-wider">Total Rows</span>
                <p className="text-xl font-bold font-mono text-zinc-100 mt-1">
                  {profile.total_rows.toLocaleString()}
                </p>
                <span className="text-xs text-zinc-400 font-medium">Records</span>
              </div>

              <div className="p-3 bg-zinc-900 border border-zinc-800 rounded-lg">
                <span className="text-xs text-zinc-400 font-semibold uppercase tracking-wider">Features</span>
                <p className="text-xl font-bold font-mono text-zinc-100 mt-1">
                  {profile.total_cols}
                </p>
                <span className="text-xs text-zinc-400 font-medium">Columns</span>
              </div>

              <div className="p-3 bg-zinc-900 border border-zinc-800 rounded-lg">
                <span className="text-xs text-zinc-400 font-semibold uppercase tracking-wider">Missing Cells</span>
                <p className={`text-xl font-bold font-mono mt-1 ${profile.missing_cells > 0 ? 'text-amber-400' : 'text-emerald-400'}`}>
                  {profile.missing_cells}
                </p>
                <span className="text-xs text-zinc-400 font-medium">{profile.missing_rate}% rate</span>
              </div>

              <div className="p-3 bg-zinc-900 border border-zinc-800 rounded-lg">
                <span className="text-xs text-zinc-400 font-semibold uppercase tracking-wider">Duplicate Rows</span>
                <p className={`text-xl font-bold font-mono mt-1 ${profile.duplicate_rows > 0 ? 'text-amber-400' : 'text-emerald-400'}`}>
                  {profile.duplicate_rows}
                </p>
                <span className="text-xs text-zinc-400 font-medium">{profile.duplicate_rate}% rate</span>
              </div>

              <div className="p-3 bg-zinc-900 border border-zinc-800 rounded-lg">
                <span className="text-xs text-zinc-400 font-semibold uppercase tracking-wider">Outliers (IQR)</span>
                <p className={`text-xl font-bold font-mono mt-1 ${profile.outlier_count > 0 ? 'text-rose-400' : 'text-emerald-400'}`}>
                  {profile.outlier_count}
                </p>
                <span className="text-xs text-zinc-400 font-medium">1.5x boundary</span>
              </div>

              <div className="p-3 bg-zinc-900 border border-zinc-800 rounded-lg">
                <span className="text-xs text-zinc-400 font-semibold uppercase tracking-wider">Health Score</span>
                <p className={`text-xl font-bold font-mono mt-1 ${profile.health_score >= 85 ? 'text-emerald-400' : 'text-amber-400'}`}>
                  {profile.health_score}%
                </p>
                <span className="text-xs text-zinc-400 font-medium">
                  {profile.health_score >= 85 ? 'Excellent' : 'Needs Clean'}
                </span>
              </div>
            </div>

            {/* Navigation Tabs */}
            <div className="flex items-center gap-1 border-b border-zinc-800 pt-1">
              <button
                onClick={() => setActiveTab('eda')}
                className={`flex items-center gap-1.5 px-3 py-2 text-xs font-semibold border-b-2 transition-colors ${
                  activeTab === 'eda'
                    ? 'border-indigo-500 text-indigo-400'
                    : 'border-transparent text-zinc-400 hover:text-zinc-200'
                }`}
              >
                <BarChart3 className="w-3.5 h-3.5" />
                <span>Visual EDA & Insights</span>
              </button>

              <button
                onClick={() => setActiveTab('table')}
                className={`flex items-center gap-1.5 px-3 py-2 text-xs font-semibold border-b-2 transition-colors ${
                  activeTab === 'table'
                    ? 'border-indigo-500 text-indigo-400'
                    : 'border-transparent text-zinc-400 hover:text-zinc-200'
                }`}
              >
                <TableIcon className="w-3.5 h-3.5" />
                <span>Data Grid View ({profile.preview.length})</span>
              </button>

              <button
                onClick={() => setActiveTab('stats')}
                className={`flex items-center gap-1.5 px-3 py-2 text-xs font-semibold border-b-2 transition-colors ${
                  activeTab === 'stats'
                    ? 'border-indigo-500 text-indigo-400'
                    : 'border-transparent text-zinc-400 hover:text-zinc-200'
                }`}
              >
                <Activity className="w-3.5 h-3.5" />
                <span>Statistical Summary & Correlations</span>
              </button>
            </div>

            {/* Tab 1: Visual EDA & Insights */}
            {activeTab === 'eda' && (
              <div className="space-y-4">
                {/* Strategic Insights Grid */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  {profile.insights.map((ins, idx) => (
                    <div 
                      key={idx}
                      className="p-3 rounded-lg border border-zinc-800 bg-zinc-900/70 space-y-1"
                    >
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-semibold text-zinc-200 flex items-center gap-1.5">
                          {ins.level === 'success' ? <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" /> :
                           ins.level === 'warning' ? <AlertCircle className="w-3.5 h-3.5 text-amber-400" /> :
                           ins.level === 'alert' ? <AlertCircle className="w-3.5 h-3.5 text-rose-400" /> :
                           <Info className="w-3.5 h-3.5 text-indigo-400" />}
                          {ins.title}
                        </span>
                        <span className="text-[9px] uppercase font-mono px-1.5 py-0.5 rounded bg-zinc-800 text-zinc-400">
                          {ins.type}
                        </span>
                      </div>
                      <p className="text-xs text-zinc-400 leading-relaxed">
                        {ins.description}
                      </p>
                    </div>
                  ))}
                </div>

                {/* Distribution Histogram & Frequency breakdown */}
                <div className="p-4 bg-zinc-900 border border-zinc-800 rounded-lg space-y-3">
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <div>
                      <h3 className="text-xs font-semibold text-zinc-200">
                        Feature Value Distribution & Frequency
                      </h3>
                      <p className="text-[11px] text-zinc-500">
                        Inspect histograms or category occurrences
                      </p>
                    </div>

                    <div className="flex items-center gap-2">
                      <span className="text-xs text-zinc-400">Select Feature:</span>
                      <select
                        value={selectedHistCol}
                        onChange={(e) => setSelectedHistCol(e.target.value)}
                        className="bg-zinc-950 border border-zinc-800 text-zinc-200 text-xs rounded px-2.5 py-1 focus:outline-none"
                      >
                        {profile.columns.map(c => (
                          <option key={c.name} value={c.name}>
                            {c.name} ({c.type})
                          </option>
                        ))}
                      </select>
                    </div>
                  </div>

                  <div className="h-60 w-full pt-2">
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={histData} margin={{ top: 10, right: 10, bottom: 25, left: -10 }}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#27272a" />
                        <XAxis 
                          dataKey="name" 
                          stroke="#71717a" 
                          fontSize={10} 
                          interval={0} 
                          angle={-20} 
                          textAnchor="end" 
                        />
                        <YAxis stroke="#71717a" fontSize={10} />
                        <Tooltip 
                          contentStyle={{ 
                            backgroundColor: '#18181b', 
                            borderColor: '#27272a', 
                            fontSize: '11px', 
                            color: '#f4f4f5' 
                          }} 
                        />
                        <Bar dataKey="count" fill="#6366f1" radius={[4, 4, 0, 0]}>
                          {histData.map((_, index) => (
                            <Cell key={`cell-${index}`} fill={index % 2 === 0 ? '#6366f1' : '#818cf8'} />
                          ))}
                        </Bar>
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                </div>
              </div>
            )}

            {/* Tab 2: High-Craft Data Grid */}
            {activeTab === 'table' && (
              <div className="h-[520px]">
                <DataTable 
                  data={profile.preview}
                  columns={profile.columns}
                  totalRows={profile.total_rows}
                />
              </div>
            )}

            {/* Tab 3: Statistical Profile & Pearson Correlation */}
            {activeTab === 'stats' && (
              <div className="space-y-4">
                {/* 5-Number Summary Table */}
                <div className="bg-zinc-900 border border-zinc-800 rounded-lg overflow-hidden">
                  <div className="p-3 border-b border-zinc-800 bg-zinc-900/90 flex items-center justify-between">
                    <h3 className="text-xs font-semibold text-zinc-200">
                      Numeric Statistics & Outlier Boundaries (IQR)
                    </h3>
                    <span className="text-[11px] text-zinc-500 font-mono">
                      {numericCols.length} Numeric Columns
                    </span>
                  </div>

                  <div className="overflow-x-auto">
                    <table className="w-full text-left text-xs font-mono">
                      <thead className="bg-zinc-950 border-b border-zinc-800 text-zinc-400">
                        <tr>
                          <th className="py-2 px-3">Column</th>
                          <th className="py-2 px-3 text-right">Min</th>
                          <th className="py-2 px-3 text-right">25% (Q1)</th>
                          <th className="py-2 px-3 text-right">Median</th>
                          <th className="py-2 px-3 text-right">Mean</th>
                          <th className="py-2 px-3 text-right">75% (Q3)</th>
                          <th className="py-2 px-3 text-right">Max</th>
                          <th className="py-2 px-3 text-right">Std Dev</th>
                          <th className="py-2 px-3 text-right">Skewness</th>
                          <th className="py-2 px-3 text-right">Outliers</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-zinc-800/60 text-zinc-300">
                        {numericCols.map((col) => {
                          const s = col.stats || {};
                          return (
                            <tr key={col.name} className="hover:bg-zinc-800/40 transition-colors">
                              <td className="py-2 px-3 font-semibold text-zinc-100 font-sans">
                                {col.name}
                              </td>
                              <td className="py-2 px-3 text-right">{s.min?.toLocaleString() ?? '-'}</td>
                              <td className="py-2 px-3 text-right">{s.q25?.toLocaleString() ?? '-'}</td>
                              <td className="py-2 px-3 text-right text-indigo-400 font-semibold">{s.median?.toLocaleString() ?? '-'}</td>
                              <td className="py-2 px-3 text-right">{s.mean?.toLocaleString() ?? '-'}</td>
                              <td className="py-2 px-3 text-right">{s.q75?.toLocaleString() ?? '-'}</td>
                              <td className="py-2 px-3 text-right">{s.max?.toLocaleString() ?? '-'}</td>
                              <td className="py-2 px-3 text-right text-zinc-400">{s.std?.toLocaleString() ?? '-'}</td>
                              <td className="py-2 px-3 text-right">
                                <span className={Math.abs(s.skewness || 0) > 1 ? 'text-amber-400' : 'text-zinc-400'}>
                                  {s.skewness ?? '-'}
                                </span>
                              </td>
                              <td className="py-2 px-3 text-right">
                                <span className={(s.outliers_iqr || 0) > 0 ? 'text-rose-400 font-semibold' : 'text-zinc-500'}>
                                  {s.outliers_iqr ?? 0}
                                </span>
                              </td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  </div>
                </div>

                {/* Pearson Correlation Matrix */}
                {Object.keys(profile.correlations).length > 0 && (
                  <div className="bg-zinc-900 border border-zinc-800 rounded-lg p-4 space-y-3">
                    <div className="flex items-center justify-between">
                      <h3 className="text-xs font-semibold text-zinc-200">
                        Pairwise Pearson Correlation Matrix
                      </h3>
                      <span className="text-[11px] text-zinc-500">
                        [-1.0 Negative, 0.0 Neutral, +1.0 Positive]
                      </span>
                    </div>

                    <div className="overflow-x-auto">
                      <table className="w-full text-xs font-mono text-center border-collapse">
                        <thead>
                          <tr>
                            <th className="p-2 text-left text-zinc-400 font-sans">Feature</th>
                            {numericCols.map(c => (
                              <th key={c.name} className="p-2 text-zinc-400 font-sans truncate max-w-[80px]" title={c.name}>
                                {c.name.slice(0, 8)}
                              </th>
                            ))}
                          </tr>
                        </thead>
                        <tbody>
                          {numericCols.map(c1 => (
                            <tr key={c1.name}>
                              <td className="p-2 text-left font-semibold text-zinc-200 font-sans truncate max-w-[120px]" title={c1.name}>
                                {c1.name}
                              </td>
                              {numericCols.map(c2 => {
                                const val = profile.correlations[c1.name]?.[c2.name] ?? 0;
                                const isSelf = c1.name === c2.name;
                                const isStrong = Math.abs(val) >= 0.5 && !isSelf;
                                
                                return (
                                  <td 
                                    key={c2.name} 
                                    className={`p-2 border border-zinc-800/80 ${
                                      isSelf ? 'bg-zinc-800/30 text-zinc-500' :
                                      val > 0.5 ? 'bg-indigo-950/40 text-indigo-300 font-semibold' :
                                      val < -0.5 ? 'bg-rose-950/40 text-rose-300 font-semibold' :
                                      'text-zinc-400'
                                    }`}
                                  >
                                    {val.toFixed(2)}
                                  </td>
                                );
                              })}
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                )}
              </div>
            )}
          </>
        )}
      </div>
    </main>
  );
};

