/**
 * Preline Empty Contents Component
 * Styled in Pure Smooth Z-Black (#0e0e11) with crisp zinc-800 separators.
 */

import React from 'react';
import { FolderOpen, UploadCloud, Database } from 'lucide-react';

interface PrelineEmptyViewProps {
  onUploadClick: () => void;
  onLoadSample: (sampleId: 'ecommerce_sales' | 'customer_churn' | 'financial_kpi') => void;
}

export const PrelineEmptyView: React.FC<PrelineEmptyViewProps> = ({
  onUploadClick,
  onLoadSample,
}) => {
  return (
    <div className="space-y-6 select-none">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-zinc-100">
          Empty Contents
        </h1>
        <p className="text-xs text-zinc-400 mt-0.5">
          Standard Preline placeholder template for zero-data and initial onboarding states
        </p>
      </div>

      {/* Main Empty State Container */}
      <div className="bg-[#0e0e11] rounded-xl border border-[#27272a] p-12 text-center shadow-xs flex flex-col items-center justify-center min-h-[460px]">
        {/* Stylized Icon Badge */}
        <div className="w-16 h-16 rounded-2xl bg-[#141418] border border-blue-500/20 flex items-center justify-center text-blue-400 mb-4 shadow-xs">
          <FolderOpen className="w-8 h-8" />
        </div>

        <h3 className="text-lg font-bold text-zinc-100 mb-2">
          No records found in this view
        </h3>

        <p className="text-xs text-zinc-400 max-w-md leading-relaxed mb-6">
          You haven't filtered or uploaded any dataset for this specific view yet.
          Get started by uploading your own CSV, Excel, or JSON data, or populate with curated enterprise datasets.
        </p>

        <div className="flex flex-wrap items-center justify-center gap-3">
          <button
            onClick={onUploadClick}
            className="inline-flex items-center gap-2 bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold px-4 py-2 rounded-lg shadow-xs transition-colors"
          >
            <UploadCloud className="w-4 h-4" />
            <span>Upload your dataset</span>
          </button>

          <button
            onClick={() => onLoadSample('ecommerce_sales')}
            className="inline-flex items-center gap-2 bg-[#141418] hover:bg-[#1b1b22] border border-[#27272a] text-zinc-200 text-xs font-medium px-4 py-2 rounded-lg transition-colors"
          >
            <Database className="w-4 h-4 text-zinc-400" />
            <span>Load E-Commerce Sample</span>
          </button>
        </div>

        {/* Feature Highlights */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mt-12 pt-8 border-t border-[#27272a] w-full max-w-2xl text-left">
          <div className="p-3 bg-[#141418] border border-[#27272a] rounded-lg">
            <h4 className="text-xs font-bold text-zinc-100 mb-1">
              Multi-Format Ingest
            </h4>
            <p className="text-[11px] text-zinc-400">
              Native support for .csv, .xlsx, .xls, and .json files.
            </p>
          </div>

          <div className="p-3 bg-[#141418] border border-[#27272a] rounded-lg">
            <h4 className="text-xs font-bold text-zinc-100 mb-1">
              Deterministic AI
            </h4>
            <p className="text-[11px] text-zinc-400">
              0% hallucination python code sandbox execution.
            </p>
          </div>

          <div className="p-3 bg-[#141418] border border-[#27272a] rounded-lg">
            <h4 className="text-xs font-bold text-zinc-100 mb-1">
              Executive Reports
            </h4>
            <p className="text-[11px] text-zinc-400">
              Generate PDF reports, Excel workbooks, and CSVs.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};
