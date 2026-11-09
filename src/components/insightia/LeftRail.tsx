/**
 * Left Rail Component for Insightia.
 * Schema inspector, Health score indicator, One-click & manual cleaning triggers,
 * Cleaning audit log, and Multi-format export toolbar.
 */

import React, { useState } from 'react';
import { 
  Sparkles, 
  Trash2, 
  Wand2, 
  FileSpreadsheet, 
  FileText, 
  Code, 
  Download, 
  History, 
  AlertTriangle, 
  Search,
  CheckCircle2,
  Settings2,
  Layers,
  ChevronRight,
  Database
} from 'lucide-react';
import { DatasetProfile, dataIntelligenceService } from '@/services/data-intelligence.service';
import { toast } from 'sonner';

interface LeftRailProps {
  profile: DatasetProfile | null;
  isLoading: boolean;
  onClean: (action: any, params?: any) => Promise<void>;
  onExport: (format: 'csv' | 'xlsx' | 'json' | 'pdf') => void;
}

export const LeftRail: React.FC<LeftRailProps> = ({
  profile,
  isLoading,
  onClean,
  onExport
}) => {
  const [columnSearch, setColumnSearch] = useState('');
  const [showCleanModal, setShowCleanModal] = useState(false);
  const [cleanAction, setCleanAction] = useState<'impute' | 'drop_na' | 'remove_outliers' | 'coerce_types'>('impute');
  const [imputeStrategy, setImputeStrategy] = useState<'mean' | 'median' | 'mode'>('median');
  const [outlierMethod, setOutlierMethod] = useState<'iqr' | 'zscore'>('iqr');
  const [selectedColumn, setSelectedColumn] = useState<string>('all');
  const [showAuditTrail, setShowAuditTrail] = useState(false);

  if (!profile) {
    return (
      <aside className="w-80 h-full bg-zinc-950 border-r border-zinc-800 p-4 flex flex-col items-center justify-center text-center text-zinc-500">
        <Database className="w-10 h-10 mb-3 opacity-30 text-indigo-400" />
        <h3 className="text-sm font-semibold text-zinc-300 mb-1">No Active Dataset</h3>
        <p className="text-xs text-zinc-500 max-w-xs">
          Upload a file or choose a sample dataset from the canvas to view schema and health audits.
        </p>
      </aside>
    );
  }

  const healthScore = profile.health_score;
  const healthColor = healthScore >= 85 ? 'text-emerald-400' : healthScore >= 65 ? 'text-amber-400' : 'text-rose-400';
  const healthBg = healthScore >= 85 ? 'bg-emerald-950/40 border-emerald-800/40' : healthScore >= 65 ? 'bg-amber-950/40 border-amber-800/40' : 'bg-rose-950/40 border-rose-800/40';

  const filteredColumns = profile.columns.filter(c => 
    c.name.toLowerCase().includes(columnSearch.toLowerCase())
  );

  const handleExecuteCustomClean = async () => {
    let params: Record<string, any> = {};
    if (cleanAction === 'impute') {
      params = {
        strategy: imputeStrategy,
        columns: selectedColumn === 'all' ? undefined : [selectedColumn]
      };
    } else if (cleanAction === 'drop_na') {
      params = {
        columns: selectedColumn === 'all' ? undefined : [selectedColumn]
      };
    } else if (cleanAction === 'remove_outliers') {
      params = {
        method: outlierMethod,
        columns: selectedColumn === 'all' ? undefined : [selectedColumn]
      };
    }

    setShowCleanModal(false);
    await onClean(cleanAction, params);
  };

  return (
    <aside className="w-80 h-full bg-zinc-950 border-r border-zinc-800 flex flex-col overflow-hidden select-none">
      {/* Platform Branding */}
      <div className="p-3.5 border-b border-zinc-800 flex items-center justify-between bg-zinc-950">
        <div className="flex items-center gap-2">
          <div className="w-6 h-6 rounded bg-indigo-600 flex items-center justify-center text-white font-bold text-xs shadow-sm">
            IQ
          </div>
          <span className="font-semibold text-zinc-100 text-sm tracking-tight">Insightia</span>
          <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-zinc-800 text-zinc-400">PRO</span>
        </div>
        <span className="text-[10px] text-zinc-500 font-mono">v2.0</span>
      </div>

      <div className="flex-1 overflow-y-auto p-3.5 space-y-4">
        {/* Health Score Gauge */}
        <div className={`p-3 rounded-lg border ${healthBg} transition-all`}>
          <div className="flex items-center justify-between mb-1.5">
            <span className="text-xs font-medium text-zinc-300">Data Health Score</span>
            <span className={`text-base font-bold font-mono ${healthColor}`}>{healthScore}%</span>
          </div>
          {/* Progress bar */}
          <div className="w-full h-1.5 bg-zinc-900 rounded-full overflow-hidden">
            <div 
              className={`h-full transition-all duration-500 ${
                healthScore >= 85 ? 'bg-emerald-500' : healthScore >= 65 ? 'bg-amber-500' : 'bg-rose-500'
              }`}
              style={{ width: `${healthScore}%` }}
            />
          </div>
          <div className="flex justify-between items-center mt-2 text-[10px] text-zinc-400 font-mono">
            <span>Missing: {profile.missing_rate}%</span>
            <span>Dups: {profile.duplicate_rows}</span>
            <span>Outliers: {profile.outlier_count}</span>
          </div>
        </div>

        {/* Cleaning Action Buttons */}
        <div className="space-y-2">
          <button
            onClick={() => onClean('auto_clean')}
            disabled={isLoading}
            className="w-full flex items-center justify-center gap-2 py-2 px-3 bg-indigo-600 hover:bg-indigo-500 text-white rounded-md text-xs font-semibold shadow-sm transition-colors disabled:opacity-50"
          >
            <Sparkles className="w-3.5 h-3.5" />
            <span>One-Click Auto-Clean</span>
          </button>

          <button
            onClick={() => setShowCleanModal(true)}
            disabled={isLoading}
            className="w-full flex items-center justify-center gap-1.5 py-1.5 px-3 bg-zinc-900 hover:bg-zinc-800 border border-zinc-800 text-zinc-200 rounded-md text-xs font-medium transition-colors"
          >
            <Settings2 className="w-3.5 h-3.5 text-zinc-400" />
            <span>Configure Cleaning Pipeline</span>
          </button>
        </div>

        {/* Column Schema Section */}
        <div>
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-semibold text-zinc-300 flex items-center gap-1.5">
              <Layers className="w-3.5 h-3.5 text-indigo-400" />
              Dataset Schema ({profile.columns.length})
            </span>
          </div>

          <div className="relative mb-2">
            <Search className="w-3.5 h-3.5 absolute left-2 top-1/2 -translate-y-1/2 text-zinc-500" />
            <input
              type="text"
              placeholder="Filter columns..."
              value={columnSearch}
              onChange={(e) => setColumnSearch(e.target.value)}
              className="w-full pl-7 pr-2 py-1 text-xs bg-zinc-900 border border-zinc-800 rounded text-zinc-200 placeholder-zinc-500 focus:outline-none"
            />
          </div>

          <div className="space-y-1 max-h-56 overflow-y-auto pr-1">
            {filteredColumns.map((col) => (
              <div 
                key={col.name}
                className="flex items-center justify-between p-1.5 bg-zinc-900/60 hover:bg-zinc-900 border border-zinc-800/80 rounded text-xs transition-colors"
              >
                <div className="flex items-center gap-1.5 min-w-0 flex-1">
                  <span className={`text-[9px] font-mono font-medium px-1 py-0.5 rounded ${
                    col.type === 'numeric' ? 'bg-indigo-950 text-indigo-300 border border-indigo-800/50' :
                    col.type === 'datetime' ? 'bg-cyan-950 text-cyan-300 border border-cyan-800/50' :
                    col.type === 'categorical' ? 'bg-emerald-950 text-emerald-300 border border-emerald-800/50' :
                    'bg-zinc-800 text-zinc-400'
                  }`}>
                    {col.type.slice(0, 3).toUpperCase()}
                  </span>
                  <span className="text-zinc-200 truncate font-mono text-[11px]" title={col.name}>
                    {col.name}
                  </span>
                </div>

                <div className="flex items-center gap-1 text-[10px] font-mono shrink-0">
                  {col.missing_count > 0 && (
                    <span className="text-amber-400 bg-amber-950/60 px-1 rounded border border-amber-800/30">
                      {col.missing_count} null
                    </span>
                  )}
                  {col.outliers_count > 0 && (
                    <span className="text-rose-400 bg-rose-950/60 px-1 rounded border border-rose-800/30">
                      {col.outliers_count} out
                    </span>
                  )}
                  {col.missing_count === 0 && col.outliers_count === 0 && (
                    <span className="text-zinc-500">100%</span>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Audit Log Accordion */}
        {profile.audit_log && profile.audit_log.length > 0 && (
          <div className="border border-zinc-800 rounded-lg p-2.5 bg-zinc-900/50">
            <button 
              onClick={() => setShowAuditTrail(!showAuditTrail)}
              className="w-full flex items-center justify-between text-xs font-semibold text-zinc-300"
            >
              <span className="flex items-center gap-1.5">
                <History className="w-3.5 h-3.5 text-zinc-400" />
                Audit Trail ({profile.audit_log.length})
              </span>
              <ChevronRight className={`w-3.5 h-3.5 text-zinc-500 transition-transform ${showAuditTrail ? 'rotate-90' : ''}`} />
            </button>

            {showAuditTrail && (
              <div className="mt-2 space-y-1.5 max-h-36 overflow-y-auto">
                {profile.audit_log.map((entry, idx) => (
                  <div key={idx} className="text-[11px] bg-zinc-950 p-1.5 rounded border border-zinc-800 text-zinc-400">
                    <p className="text-zinc-300 font-medium leading-tight">{entry.message}</p>
                    <span className="text-[9px] text-zinc-500 mt-1 block">
                      {new Date(entry.timestamp).toLocaleTimeString()}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Multi-Format Export Toolbar */}
      <div className="p-3 border-t border-zinc-800 bg-zinc-950 space-y-1.5">
        <span className="text-[11px] font-semibold text-zinc-400 flex items-center gap-1">
          <Download className="w-3 h-3 text-indigo-400" />
          Export Dataset
        </span>
        <div className="grid grid-cols-2 gap-1.5">
          <button
            onClick={() => onExport('csv')}
            className="flex items-center gap-1.5 px-2 py-1.5 rounded bg-zinc-900 hover:bg-zinc-800 border border-zinc-800 text-[11px] text-zinc-200 transition-colors"
          >
            <FileSpreadsheet className="w-3 h-3 text-emerald-400" />
            <span>CSV</span>
          </button>
          <button
            onClick={() => onExport('xlsx')}
            className="flex items-center gap-1.5 px-2 py-1.5 rounded bg-zinc-900 hover:bg-zinc-800 border border-zinc-800 text-[11px] text-zinc-200 transition-colors"
          >
            <FileSpreadsheet className="w-3 h-3 text-blue-400" />
            <span>Styled Excel</span>
          </button>
          <button
            onClick={() => onExport('json')}
            className="flex items-center gap-1.5 px-2 py-1.5 rounded bg-zinc-900 hover:bg-zinc-800 border border-zinc-800 text-[11px] text-zinc-200 transition-colors"
          >
            <Code className="w-3 h-3 text-amber-400" />
            <span>JSON Schema</span>
          </button>
          <button
            onClick={() => onExport('pdf')}
            className="flex items-center gap-1.5 px-2 py-1.5 rounded bg-zinc-900 hover:bg-zinc-800 border border-zinc-800 text-[11px] text-zinc-200 transition-colors"
          >
            <FileText className="w-3 h-3 text-rose-400" />
            <span>Executive PDF</span>
          </button>
        </div>
      </div>

      {/* Custom Cleaning Modal */}
      {showCleanModal && (
        <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-zinc-900 border border-zinc-800 rounded-lg p-5 max-w-md w-full shadow-xl space-y-4">
            <div className="flex items-center justify-between border-b border-zinc-800 pb-3">
              <h3 className="text-sm font-semibold text-zinc-100 flex items-center gap-2">
                <Wand2 className="w-4 h-4 text-indigo-400" />
                Data Cleaning Pipeline Setup
              </h3>
              <button 
                onClick={() => setShowCleanModal(false)}
                className="text-zinc-500 hover:text-zinc-300 text-xs"
              >
                ✕
              </button>
            </div>

            <div className="space-y-3 text-xs">
              <div>
                <label className="text-zinc-400 font-medium block mb-1">Target Operation</label>
                <select
                  value={cleanAction}
                  onChange={(e: any) => setCleanAction(e.target.value)}
                  className="w-full bg-zinc-950 border border-zinc-800 rounded p-2 text-zinc-200 focus:outline-none"
                >
                  <option value="impute">Impute Missing Values (Mean / Median / Mode)</option>
                  <option value="drop_na">Drop Rows with Missing Values</option>
                  <option value="remove_outliers">Remove Statistical Outliers</option>
                  <option value="coerce_types">Coerce Data Types (Date/Numeric)</option>
                </select>
              </div>

              {cleanAction === 'impute' && (
                <div>
                  <label className="text-zinc-400 font-medium block mb-1">Imputation Strategy</label>
                  <select
                    value={imputeStrategy}
                    onChange={(e: any) => setImputeStrategy(e.target.value)}
                    className="w-full bg-zinc-950 border border-zinc-800 rounded p-2 text-zinc-200 focus:outline-none"
                  >
                    <option value="median">Median (Recommended for skewed numeric)</option>
                    <option value="mean">Mean (Average)</option>
                    <option value="mode">Mode (Most frequent value)</option>
                  </select>
                </div>
              )}

              {cleanAction === 'remove_outliers' && (
                <div>
                  <label className="text-zinc-400 font-medium block mb-1">Outlier Boundary Method</label>
                  <select
                    value={outlierMethod}
                    onChange={(e: any) => setOutlierMethod(e.target.value)}
                    className="w-full bg-zinc-950 border border-zinc-800 rounded p-2 text-zinc-200 focus:outline-none"
                  >
                    <option value="iqr">1.5x Interquartile Range (IQR)</option>
                    <option value="zscore">Z-Score (|z| &gt; 3)</option>
                  </select>
                </div>
              )}

              <div>
                <label className="text-zinc-400 font-medium block mb-1">Target Column</label>
                <select
                  value={selectedColumn}
                  onChange={(e) => setSelectedColumn(e.target.value)}
                  className="w-full bg-zinc-950 border border-zinc-800 rounded p-2 text-zinc-200 focus:outline-none"
                >
                  <option value="all">All Applicable Columns</option>
                  {profile.columns.map(c => (
                    <option key={c.name} value={c.name}>{c.name} ({c.type})</option>
                  ))}
                </select>
              </div>
            </div>

            <div className="flex justify-end gap-2 pt-2 border-t border-zinc-800">
              <button
                onClick={() => setShowCleanModal(false)}
                className="px-3 py-1.5 text-xs text-zinc-400 hover:text-zinc-200"
              >
                Cancel
              </button>
              <button
                onClick={handleExecuteCustomClean}
                className="px-4 py-1.5 text-xs font-semibold bg-indigo-600 hover:bg-indigo-500 text-white rounded transition-colors"
              >
                Execute Pipeline
              </button>
            </div>
          </div>
        </div>
      )}
    </aside>
  );
};

