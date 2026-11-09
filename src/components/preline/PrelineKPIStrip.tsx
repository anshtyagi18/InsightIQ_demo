/**
 * Preline KPI Strip Component
 * 4-Segment Reactive KPI card styled in Pure Smooth Z-Black (#0e0e11)
 * Displays Live Dataset Metrics: Total Records, Features, Missing Values, and Duplicate Records.
 * Includes direct 1-click remediation buttons for missing values and duplicates.
 */

import React from 'react';
import { 
  Database, 
  Layers, 
  AlertCircle, 
  CopyCheck, 
  TrendingUp, 
  Wand2, 
  Trash2, 
  CheckCircle2,
  Loader2
} from 'lucide-react';
import { DatasetProfile } from '@/services/data-intelligence.service';

export interface KPIData {
  profile?: DatasetProfile | null;
  activeSegment?: number;
  onSelectSegment?: (index: number) => void;
  onFixMissing?: () => void;
  onRemoveDuplicates?: () => void;
  isCleaning?: boolean;
}

export const PrelineKPIStrip: React.FC<KPIData> = ({
  profile,
  activeSegment = 0,
  onSelectSegment,
  onFixMissing,
  onRemoveDuplicates,
  isCleaning = false,
}) => {
  const totalRows = profile ? profile.total_rows : 1012;
  const totalCols = profile ? profile.total_cols : 10;
  const missingCells = profile ? profile.missing_cells : 1;
  const duplicateRows = profile ? profile.duplicate_rows : 0;
  const healthScore = profile ? profile.health_score : 92;

  const segments = [
    {
      id: 0,
      icon: Database,
      label: "Total Records",
      value: totalRows.toLocaleString(),
      subtext: profile ? `${profile.dataset_name}` : "Active entries",
      statusText: `${healthScore}% Health`,
      isPositive: healthScore >= 80,
      action: null,
    },
    {
      id: 1,
      icon: Layers,
      label: "Features & Columns",
      value: `${totalCols}`,
      subtext: profile ? `${profile.columns.filter(c => c.type === 'numeric').length} numeric, ${profile.columns.filter(c => c.type !== 'numeric').length} categorical` : "10 columns typed",
      statusText: "100% Inferred",
      isPositive: true,
      action: null,
    },
    {
      id: 2,
      icon: AlertCircle,
      label: "Missing Values",
      value: missingCells.toLocaleString(),
      subtext: missingCells === 0 ? "Zero null records" : `${((profile?.missing_rate || 0.001) * 100).toFixed(1)}% missingness`,
      statusText: missingCells === 0 ? "Cleaned" : "Action Required",
      isPositive: missingCells === 0,
      action: missingCells > 0 && onFixMissing ? {
        label: "Fix Missing",
        onClick: (e: React.MouseEvent) => {
          e.stopPropagation();
          onFixMissing();
        }
      } : null,
    },
    {
      id: 3,
      icon: CopyCheck,
      label: "Duplicate Rows",
      value: duplicateRows.toLocaleString(),
      subtext: duplicateRows === 0 ? "Unique dataset" : `${((profile?.duplicate_rate || 0) * 100).toFixed(1)}% duplicates`,
      statusText: duplicateRows === 0 ? "Deduplicated" : "Action Required",
      isPositive: duplicateRows === 0,
      action: duplicateRows > 0 && onRemoveDuplicates ? {
        label: "Deduplicate",
        onClick: (e: React.MouseEvent) => {
          e.stopPropagation();
          onRemoveDuplicates();
        }
      } : null,
    },
  ];

  return (
    <div className="bg-[#0e0e11] rounded-xl border border-[#27272a] overflow-hidden shadow-xs transition-colors select-none">
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 divide-y sm:divide-y-0 sm:divide-x divide-[#27272a]">
        {segments.map((seg, idx) => {
          const Icon = seg.icon;
          const isActive = activeSegment === idx;

          return (
            <div
              key={seg.id}
              onClick={() => onSelectSegment?.(idx)}
              className={`relative p-5 cursor-pointer transition-all duration-150 flex flex-col justify-between ${
                isActive ? 'bg-[#141418]' : 'bg-[#0e0e11] hover:bg-[#121216]'
              }`}
            >
              {/* Top Active Indicator */}
              {isActive && (
                <div className="absolute top-0 left-0 right-0 h-[3px] bg-blue-500 shadow-sm shadow-blue-500/50" />
              )}

              {/* Header: Icon + Label */}
              <div>
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2 text-zinc-400">
                    <Icon className={`w-4 h-4 ${isActive ? 'text-blue-400' : 'text-zinc-400'}`} />
                    <span className="text-xs font-semibold uppercase tracking-wider text-zinc-300">
                      {seg.label}
                    </span>
                  </div>

                  {/* Status Badge */}
                  <span
                    className={`inline-flex items-center gap-1 text-[11px] font-semibold px-2 py-0.5 rounded-full border ${
                      seg.isPositive
                        ? 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20'
                        : 'text-amber-400 bg-amber-500/10 border-amber-500/20'
                    }`}
                  >
                    {seg.isPositive ? <CheckCircle2 className="w-3 h-3" /> : <AlertCircle className="w-3 h-3" />}
                    <span>{seg.statusText}</span>
                  </span>
                </div>

                {/* Primary Metric Number */}
                <div className="flex items-baseline gap-2 mb-1">
                  <span className="text-2xl font-bold tracking-tight text-zinc-100 font-mono">
                    {seg.value}
                  </span>
                </div>

                <p className="text-xs text-zinc-400 truncate">
                  {seg.subtext}
                </p>
              </div>

              {/* Action Button if Remediation Needed */}
              {seg.action && (
                <div className="mt-3 pt-2.5 border-t border-[#27272a]/60 flex items-center justify-between">
                  <button
                    onClick={seg.action.onClick}
                    disabled={isCleaning}
                    className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-semibold bg-blue-600 hover:bg-blue-500 text-white shadow-xs transition-all disabled:opacity-50"
                  >
                    {isCleaning ? (
                      <Loader2 className="w-3 h-3 animate-spin" />
                    ) : (
                      <Wand2 className="w-3 h-3" />
                    )}
                    <span>{seg.action.label}</span>
                  </button>
                  <span className="text-[11px] text-zinc-400 font-medium">1-Click Fix</span>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};
