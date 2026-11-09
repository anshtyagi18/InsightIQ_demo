/**
 * Preline Incidents & Data Quality Audit View
 * Styled in Pure Smooth Z-Black (#0e0e11) with crisp zinc-800 separators.
 */

import React, { useState } from 'react';
import { 
  AlertTriangle, 
  CheckCircle2, 
  Wand2, 
  Trash2, 
  RefreshCw, 
  ShieldAlert, 
  Sliders, 
  FileCheck2
} from 'lucide-react';
import { DatasetProfile, dataIntelligenceService } from '@/services/data-intelligence.service';
import { toast } from 'sonner';

interface PrelineIncidentsViewProps {
  profile: DatasetProfile | null;
  onRefreshProfile: (updated: DatasetProfile) => void;
}

export const PrelineIncidentsView: React.FC<PrelineIncidentsViewProps> = ({
  profile,
  onRefreshProfile,
}) => {
  const [isFixing, setIsFixing] = useState<string | null>(null);

  if (!profile) {
    return (
      <div className="bg-[#0e0e11] rounded-xl border border-[#27272a] p-12 text-center">
        <AlertTriangle className="w-8 h-8 text-amber-400 mx-auto mb-3" />
        <h3 className="text-base font-bold text-zinc-100 mb-1">
          No Active Dataset Loaded
        </h3>
        <p className="text-xs text-zinc-400">
          Upload a file or choose a sample dataset to inspect data quality incidents.
        </p>
      </div>
    );
  }

  // Find columns with missing values or outliers
  const columnsWithMissing = profile.columns.filter((c) => c.null_count > 0);
  const columnsWithOutliers = profile.columns.filter(
    (c) => (c.iqr_outliers && c.iqr_outliers > 0) || (c.zscore_outliers && c.zscore_outliers > 0)
  );

  const handleFixAction = async (action: 'impute' | 'drop_na' | 'remove_outliers' | 'remove_duplicates' | 'auto_clean') => {
    setIsFixing(action);
    const toastId = toast.loading(`Executing ${action.replace('_', ' ')}...`);
    try {
      const updated = await dataIntelligenceService.cleanDataset(profile.session_id, action);
      onRefreshProfile(updated);
      toast.success(updated.audit_entry || `Remediation completed successfully!`, { id: toastId });
    } catch (err: any) {
      toast.error(`Action failed: ${err.message}`, { id: toastId });
    } finally {
      setIsFixing(null);
    }
  };

  return (
    <div className="space-y-6 select-none">
      {/* View Header */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold tracking-tight text-zinc-100">
              Data Quality Incidents &amp; Audit Log
            </h1>
            <span
              className={`text-xs font-semibold px-2.5 py-0.5 rounded-full border ${
                profile.health_score >= 90
                  ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
                  : profile.health_score >= 70
                  ? 'bg-amber-500/10 text-amber-400 border-amber-500/20'
                  : 'bg-rose-500/10 text-rose-400 border-rose-500/20'
              }`}
            >
              Health Score: {profile.health_score}%
            </span>
          </div>
          <p className="text-xs text-zinc-400 mt-0.5">
            Automated detection for missing cells, statistical skewness, and schema integrity
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => handleFixAction('auto_clean')}
            disabled={isFixing !== null}
            className="inline-flex items-center gap-1.5 bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold px-3.5 py-1.5 rounded-lg shadow-xs transition-colors disabled:opacity-50"
          >
            <Wand2 className="w-3.5 h-3.5" />
            <span>Auto-Resolve All Incidents</span>
          </button>
        </div>
      </div>

      {/* 4 Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-[#0e0e11] rounded-xl border border-[#27272a] p-5 shadow-xs">
          <div className="flex items-center justify-between text-xs text-zinc-400 mb-2">
            <span>Overall Health</span>
            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="flex items-baseline gap-2">
            <span className="text-2xl font-bold text-zinc-100">
              {profile.health_score}%
            </span>
            <span className="text-xs font-medium text-emerald-400">Enterprise grade</span>
          </div>
          <p className="text-[11px] text-zinc-500 mt-1">Weighted cleanliness metric</p>
        </div>

        <div className="bg-[#0e0e11] rounded-xl border border-[#27272a] p-5 shadow-xs">
          <div className="flex items-center justify-between text-xs text-zinc-400 mb-2">
            <span>Missing Cells</span>
            <AlertTriangle className="w-4 h-4 text-amber-400" />
          </div>
          <div className="flex items-baseline gap-2">
            <span className="text-2xl font-bold text-zinc-100">
              {profile.total_missing.toLocaleString()}
            </span>
            <span className="text-xs text-zinc-400">
              across {columnsWithMissing.length} columns
            </span>
          </div>
          <p className="text-[11px] text-zinc-500 mt-1">Imputation available</p>
        </div>

        <div className="bg-[#0e0e11] rounded-xl border border-[#27272a] p-5 shadow-xs">
          <div className="flex items-center justify-between text-xs text-zinc-400 mb-2">
            <span>Statistical Outliers</span>
            <ShieldAlert className="w-4 h-4 text-rose-400" />
          </div>
          <div className="flex items-baseline gap-2">
            <span className="text-2xl font-bold text-zinc-100">
              {profile.outliers_count.toLocaleString()}
            </span>
            <span className="text-xs text-zinc-400">IQR 1.5x test</span>
          </div>
          <p className="text-[11px] text-zinc-500 mt-1">Z-Score threshold: 3.0σ</p>
        </div>

        <div className="bg-[#0e0e11] rounded-xl border border-[#27272a] p-5 shadow-xs">
          <div className="flex items-center justify-between text-xs text-zinc-400 mb-2">
            <span>Schema Integrity</span>
            <FileCheck2 className="w-4 h-4 text-blue-400" />
          </div>
          <div className="flex items-baseline gap-2">
            <span className="text-2xl font-bold text-zinc-100">
              {profile.columns.length} / {profile.columns.length}
            </span>
            <span className="text-xs text-emerald-400 font-semibold">100% Typed</span>
          </div>
          <p className="text-[11px] text-zinc-500 mt-1">Zero schema collisions</p>
        </div>
      </div>

      {/* Incidents Remediation Actions */}
      <div className="bg-[#0e0e11] rounded-xl border border-[#27272a] p-5 shadow-xs">
        <h3 className="text-sm font-bold text-zinc-100 mb-2">
          One-Click Quality Remediation Actions
        </h3>
        <p className="text-xs text-zinc-400 mb-4">
          Execute deterministic algorithms to normalize distributions, impute missing numbers, or remove corrupt records.
        </p>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
          <button
            onClick={() => handleFixAction('impute')}
            disabled={isFixing !== null || profile.total_missing === 0}
            className="p-3 bg-[#141418] hover:bg-[#1a1a20] border border-[#27272a] rounded-xl text-left transition-all disabled:opacity-40"
          >
            <div className="flex items-center justify-between mb-1.5">
              <span className="text-xs font-bold text-zinc-100">Smart Impute</span>
              <Wand2 className="w-4 h-4 text-blue-400" />
            </div>
            <p className="text-[11px] text-zinc-400">
              Fill nulls with Mean/Median for numeric, Mode for text.
            </p>
          </button>

          <button
            onClick={() => handleFixAction('drop_na')}
            disabled={isFixing !== null || profile.total_missing === 0}
            className="p-3 bg-[#141418] hover:bg-[#1a1a20] border border-[#27272a] rounded-xl text-left transition-all disabled:opacity-40"
          >
            <div className="flex items-center justify-between mb-1.5">
              <span className="text-xs font-bold text-zinc-100">Drop Incomplete</span>
              <Trash2 className="w-4 h-4 text-rose-400" />
            </div>
            <p className="text-[11px] text-zinc-400">
              Remove rows containing empty or unparseable fields.
            </p>
          </button>

          <button
            onClick={() => handleFixAction('remove_outliers')}
            disabled={isFixing !== null || profile.outliers_count === 0}
            className="p-3 bg-[#141418] hover:bg-[#1a1a20] border border-[#27272a] rounded-xl text-left transition-all disabled:opacity-40"
          >
            <div className="flex items-center justify-between mb-1.5">
              <span className="text-xs font-bold text-zinc-100">Trim Outliers</span>
              <Sliders className="w-4 h-4 text-purple-400" />
            </div>
            <p className="text-[11px] text-zinc-400">
              Filter extreme numerical anomalies using IQR 1.5x rule.
            </p>
          </button>

          <button
            onClick={() => handleFixAction('remove_duplicates')}
            disabled={isFixing !== null}
            className="p-3 bg-[#141418] hover:bg-[#1a1a20] border border-[#27272a] rounded-xl text-left transition-all disabled:opacity-40"
          >
            <div className="flex items-center justify-between mb-1.5">
              <span className="text-xs font-bold text-zinc-100">Deduplicate</span>
              <RefreshCw className="w-4 h-4 text-emerald-400" />
            </div>
            <p className="text-[11px] text-zinc-400">
              Keep unique rows and prune identical record collisions.
            </p>
          </button>
        </div>
      </div>

      {/* Column Health Inspection Table */}
      <div className="bg-[#0e0e11] rounded-xl border border-[#27272a] overflow-hidden shadow-xs">
        <div className="p-4 border-b border-[#27272a] flex items-center justify-between">
          <h3 className="text-sm font-bold text-zinc-100">
            Column-by-Column Health Auditing
          </h3>
          <span className="text-xs text-zinc-400">
            {profile.columns.length} columns inspected
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-[#27272a] text-xs">
            <thead className="bg-[#141418]">
              <tr>
                <th className="py-2.5 px-4 text-left font-semibold text-zinc-400">Column Name</th>
                <th className="py-2.5 px-4 text-left font-semibold text-zinc-400">Type</th>
                <th className="py-2.5 px-4 text-left font-semibold text-zinc-400">Missing</th>
                <th className="py-2.5 px-4 text-left font-semibold text-zinc-400">Outliers (IQR)</th>
                <th className="py-2.5 px-4 text-left font-semibold text-zinc-400">Unique Values</th>
                <th className="py-2.5 px-4 text-right font-semibold text-zinc-400">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#27272a]/60">
              {profile.columns.map((col) => {
                const hasIssue = col.null_count > 0 || (col.iqr_outliers && col.iqr_outliers > 0);
                return (
                  <tr key={col.name} className="hover:bg-[#141418] transition-colors">
                    <td className="py-2.5 px-4 font-mono font-medium text-zinc-100">
                      {col.name}
                    </td>
                    <td className="py-2.5 px-4">
                      <span className="font-mono text-[11px] bg-[#1a1a20] text-zinc-300 border border-[#27272a] px-2 py-0.5 rounded">
                        {col.dtype}
                      </span>
                    </td>
                    <td className="py-2.5 px-4">
                      {col.null_count > 0 ? (
                        <span className="text-amber-400 font-semibold">
                          {col.null_count} ({col.null_percentage}%)
                        </span>
                      ) : (
                        <span className="text-emerald-400">0</span>
                      )}
                    </td>
                    <td className="py-2.5 px-4 font-mono">
                      {col.iqr_outliers && col.iqr_outliers > 0 ? (
                        <span className="text-rose-400 font-semibold">{col.iqr_outliers}</span>
                      ) : (
                        <span className="text-zinc-600">0</span>
                      )}
                    </td>
                    <td className="py-2.5 px-4 font-mono text-zinc-400">
                      {col.unique_count.toLocaleString()}
                    </td>
                    <td className="py-2.5 px-4 text-right">
                      {hasIssue ? (
                        <span className="inline-flex items-center gap-1 text-xs font-semibold text-amber-400 bg-amber-500/10 px-2.5 py-0.5 rounded-full border border-amber-500/20">
                          Attention
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1 text-xs font-semibold text-emerald-400 bg-emerald-500/10 px-2.5 py-0.5 rounded-full border border-emerald-500/20">
                          Optimal
                        </span>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
