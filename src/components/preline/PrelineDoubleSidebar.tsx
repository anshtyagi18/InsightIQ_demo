/**
 * Preline Dual-Column Left Sidebar Component
 * Styled in Pure Smooth Z-Black (#09090b / #0c0c0e) with crisp zinc-800 separators.
 */

import React, { useState } from 'react';
import { 
  Home, 
  Users, 
  Sparkles, 
  CheckCircle, 
  ArrowUpCircle, 
  Plug, 
  Box, 
  Grid, 
  Layout, 
  ChevronDown,
  Zap
} from 'lucide-react';

interface PrelineDoubleSidebarProps {
  activeView: string;
  onSelectView: (view: string) => void;
  onOpenCopilot?: () => void;
  onOpenUpload?: () => void;
  onAutoClean?: () => void;
  creditsUsed?: number;
  totalCredits?: number;
}

export const PrelineDoubleSidebar: React.FC<PrelineDoubleSidebarProps> = ({
  activeView = 'overview',
  onSelectView,
  onOpenCopilot,
  onOpenUpload,
  onAutoClean,
  creditsUsed = 65,
  totalCredits = 100,
}) => {
  const [channelsOpen, setChannelsOpen] = useState(true);

  // Circular progress calculation
  const radius = 16;
  const circumference = 2 * Math.PI * radius;
  const progressPercent = Math.min(100, Math.max(0, (creditsUsed / totalCredits) * 100));
  const strokeDashoffset = circumference - (progressPercent / 100) * circumference;

  return (
    <div className="flex h-full select-none">
      {/* 1. SLIM ICON RAIL (64px) - Pure Smooth Z-Black */}
      <aside className="w-16 h-full bg-[#09090b] border-r border-[#27272a] flex flex-col items-center justify-between py-3.5 z-20">
        {/* Top: Stylized Preline Logo */}
        <div className="flex flex-col items-center gap-6">
          <div 
            onClick={() => onSelectView('overview')}
            className="w-9 h-9 rounded-xl bg-blue-600 flex items-center justify-center text-white font-bold text-base shadow-sm cursor-pointer hover:bg-blue-500 transition-colors"
          >
            <span className="font-serif">P</span>
          </div>

          {/* Navigation Icons Stack */}
          <nav className="flex flex-col items-center gap-2">
            {/* 1. Overview */}
            <button
              onClick={() => onSelectView('overview')}
              className={`p-2.5 rounded-xl transition-all ${
                activeView === 'overview'
                  ? 'bg-blue-600/15 text-blue-400 border border-blue-500/20'
                  : 'text-zinc-400 hover:text-zinc-100 hover:bg-[#18181b]'
              }`}
              title="Overview"
            >
              <Home className="w-5 h-5" />
            </button>

            {/* 2. Visitors */}
            <button
              onClick={() => onSelectView('visitors')}
              className={`p-2.5 rounded-xl transition-all ${
                activeView === 'visitors'
                  ? 'bg-blue-600/15 text-blue-400 border border-blue-500/20'
                  : 'text-zinc-400 hover:text-zinc-100 hover:bg-[#18181b]'
              }`}
              title="Visitors / Demographics"
            >
              <Users className="w-5 h-5" />
            </button>

            {/* 3. AI Copilot */}
            <button
              onClick={onOpenCopilot}
              className={`p-2.5 rounded-xl transition-all ${
                activeView === 'copilot'
                  ? 'bg-blue-600/15 text-blue-400 border border-blue-500/20'
                  : 'text-zinc-400 hover:text-zinc-100 hover:bg-[#18181b]'
              }`}
              title="AI Copilot"
            >
              <Sparkles className="w-5 h-5 text-indigo-400" />
            </button>

            {/* 4. Quality Audit / Incidents */}
            <button
              onClick={() => onSelectView('incidents')}
              className={`p-2.5 rounded-xl transition-all ${
                activeView === 'incidents'
                  ? 'bg-blue-600/15 text-blue-400 border border-blue-500/20'
                  : 'text-zinc-400 hover:text-zinc-100 hover:bg-[#18181b]'
              }`}
              title="Data Quality Audit"
            >
              <CheckCircle className="w-5 h-5" />
            </button>

            {/* 5. Ingestion / Upload */}
            <button
              onClick={onOpenUpload}
              className="p-2.5 rounded-xl text-zinc-400 hover:text-blue-400 hover:bg-[#18181b] transition-all"
              title="Upload Dataset"
            >
              <ArrowUpCircle className="w-5 h-5" />
            </button>

            {/* 6. Empty Contents View */}
            <button
              onClick={() => onSelectView('empty')}
              className={`p-2.5 rounded-xl transition-all ${
                activeView === 'empty'
                  ? 'bg-blue-600/15 text-blue-400 border border-blue-500/20'
                  : 'text-zinc-400 hover:text-zinc-100 hover:bg-[#18181b]'
              }`}
              title="Empty State View"
            >
              <Plug className="w-5 h-5" />
            </button>
          </nav>
        </div>

        {/* Bottom: User Avatar */}
        <div className="relative cursor-pointer group">
          <img
            src="https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=100&h=100&fit=crop&crop=faces"
            alt="User Profile"
            className="w-8 h-8 rounded-full object-cover ring-2 ring-[#27272a] group-hover:ring-blue-500 transition-all"
          />
          <span className="absolute bottom-0 right-0 w-2.5 h-2.5 rounded-full bg-emerald-500 ring-2 ring-[#09090b]" />
        </div>
      </aside>

      {/* 2. SECONDARY SUB-NAV RAIL (224px) - Pure Smooth Z-Black */}
      <aside className="w-56 h-full bg-[#0c0c0e] border-r border-[#27272a] flex flex-col justify-between p-3.5 overflow-y-auto">
        <div>
          {/* Quick Actions Search */}
          <div className="relative mb-4">
            <input
              type="text"
              placeholder="Quick actions"
              readOnly
              onClick={onOpenCopilot}
              className="w-full bg-[#141418] hover:bg-[#18181d] border border-[#27272a] text-xs rounded-lg pl-3 pr-8 py-1.5 text-zinc-200 placeholder-zinc-500 focus:outline-none focus:border-blue-500 cursor-pointer transition-colors"
            />
            <span className="absolute right-2 top-1/2 -translate-y-1/2 text-[10px] font-mono text-zinc-400 bg-[#1b1b22] border border-[#27272a] px-1 py-0.2 rounded shadow-2xs">
              ⌘ K
            </span>
          </div>

          {/* Main Sub-Nav List */}
          <nav className="space-y-1">
            <button
              onClick={() => onSelectView('overview')}
              className={`w-full text-left px-3 py-2 rounded-lg text-xs font-semibold transition-colors flex items-center justify-between ${
                activeView === 'overview'
                  ? 'bg-blue-600/15 text-blue-400 border border-blue-500/20'
                  : 'text-zinc-300 hover:bg-[#141418] hover:text-zinc-100'
              }`}
            >
              <span>Overview</span>
            </button>

            <button
              onClick={() => onSelectView('visitors')}
              className={`w-full text-left px-3 py-2 rounded-lg text-xs font-medium transition-colors flex items-center justify-between ${
                activeView === 'visitors'
                  ? 'bg-blue-600/15 text-blue-400 border border-blue-500/20'
                  : 'text-zinc-300 hover:bg-[#141418] hover:text-zinc-100'
              }`}
            >
              <span>Visitors</span>
            </button>

            <button
              onClick={() => onSelectView('survey')}
              className={`w-full text-left px-3 py-2 rounded-lg text-xs font-medium transition-colors flex items-center justify-between ${
                activeView === 'survey'
                  ? 'bg-blue-600/15 text-blue-400 border border-blue-500/20'
                  : 'text-zinc-300 hover:bg-[#141418] hover:text-zinc-100'
              }`}
            >
              <span>Survey</span>
              <span className="text-[10px] font-medium bg-[#1a1a20] text-zinc-400 border border-[#27272a] px-1.5 py-0.2 rounded">
                Beta
              </span>
            </button>

            <button
              onClick={() => onSelectView('incidents')}
              className={`w-full text-left px-3 py-2 rounded-lg text-xs font-medium transition-colors flex items-center justify-between ${
                activeView === 'incidents'
                  ? 'bg-blue-600/15 text-blue-400 border border-blue-500/20'
                  : 'text-zinc-300 hover:bg-[#141418] hover:text-zinc-100'
              }`}
            >
              <span>Incidents</span>
            </button>

            <button
              onClick={() => onSelectView('empty')}
              className={`w-full text-left px-3 py-2 rounded-lg text-xs font-medium transition-colors flex items-center justify-between ${
                activeView === 'empty'
                  ? 'bg-blue-600/15 text-blue-400 border border-blue-500/20'
                  : 'text-zinc-300 hover:bg-[#141418] hover:text-zinc-100'
              }`}
            >
              <span>Empty Contents</span>
            </button>
          </nav>

          {/* Section: Channels */}
          <div className="mt-6">
            <button
              onClick={() => setChannelsOpen(!channelsOpen)}
              className="flex items-center justify-between w-full text-left text-[11px] font-semibold text-zinc-500 uppercase tracking-wider mb-2 px-2 hover:text-zinc-300 transition-colors"
            >
              <span className="flex items-center gap-1">
                <ChevronDown className={`w-3 h-3 transition-transform ${channelsOpen ? '' : '-rotate-90'}`} />
                Channels
              </span>
            </button>

            {channelsOpen && (
              <div className="space-y-1">
                <button
                  onClick={() => onSelectView('overview')}
                  className="w-full flex items-center gap-2.5 px-3 py-1.5 text-xs text-zinc-400 hover:bg-[#141418] hover:text-zinc-100 rounded-lg transition-colors"
                >
                  <div className="w-5 h-5 rounded bg-[#18181d] border border-[#27272a] text-blue-400 flex items-center justify-center">
                    <Box className="w-3 h-3" />
                  </div>
                  <span>PRO</span>
                </button>

                <button
                  onClick={() => onSelectView('overview')}
                  className="w-full flex items-center gap-2.5 px-3 py-1.5 text-xs text-zinc-400 hover:bg-[#141418] hover:text-zinc-100 rounded-lg transition-colors"
                >
                  <div className="w-5 h-5 rounded bg-[#18181d] border border-[#27272a] text-blue-400 flex items-center justify-center">
                    <Grid className="w-3 h-3" />
                  </div>
                  <span>Blocks</span>
                </button>

                <button
                  onClick={() => onSelectView('overview')}
                  className="w-full flex items-center gap-2.5 px-3 py-1.5 text-xs text-zinc-400 hover:bg-[#141418] hover:text-zinc-100 rounded-lg transition-colors"
                >
                  <div className="w-5 h-5 rounded bg-[#18181d] border border-[#27272a] text-blue-400 flex items-center justify-center">
                    <Layout className="w-3 h-3" />
                  </div>
                  <span>Templates</span>
                </button>
              </div>
            )}
          </div>
        </div>

        {/* Bottom Credits Card */}
        <div className="mt-4 pt-3 border-t border-[#27272a]">
          <div className="bg-[#121216] border border-[#27272a] rounded-xl p-3 space-y-2">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs font-bold text-zinc-100">
                  {creditsUsed}/{totalCredits} credits used
                </p>
                <p className="text-[11px] text-zinc-400">
                  Invite team members
                </p>
              </div>

              {/* Circular Progress Ring */}
              <div className="relative w-9 h-9 flex items-center justify-center">
                <svg className="w-9 h-9 -rotate-90">
                  <circle
                    cx="18"
                    cy="18"
                    r={radius}
                    stroke="#27272a"
                    strokeWidth="3"
                    fill="transparent"
                  />
                  <circle
                    cx="18"
                    cy="18"
                    r={radius}
                    stroke="#3b82f6"
                    strokeWidth="3"
                    strokeDasharray={circumference}
                    strokeDashoffset={strokeDashoffset}
                    strokeLinecap="round"
                    fill="transparent"
                    className="transition-all duration-500"
                  />
                </svg>
              </div>
            </div>

            <button
              onClick={onAutoClean}
              className="inline-flex items-center gap-1.5 text-xs font-semibold text-blue-400 hover:text-blue-300 transition-colors pt-1"
            >
              <Zap className="w-3.5 h-3.5 fill-blue-400" />
              <span>Upgrade now</span>
            </button>
          </div>

          {/* Small thumbnail preview banner underneath */}
          <div 
            onClick={() => onSelectView('overview')}
            className="mt-2.5 bg-[#141418] border border-[#27272a] rounded-lg p-2 flex items-center gap-2 cursor-pointer hover:border-zinc-600 transition-all"
          >
            <div className="w-7 h-5 rounded bg-[#1b1b22] border border-blue-500/30 overflow-hidden flex items-center justify-center">
              <span className="text-[8px] font-mono text-blue-400 font-bold">AI</span>
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-[10px] font-semibold text-zinc-200 truncate">Insightia Engine</p>
              <p className="text-[9px] text-zinc-400">FastAPI &amp; Pandas</p>
            </div>
          </div>
        </div>
      </aside>
    </div>
  );
};
