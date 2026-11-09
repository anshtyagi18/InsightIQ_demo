/**
 * Master Preline Analytics Dashboard Component
 * Styled in Pure Smooth Z-Black (#09090b / #0e0e11) with crisp zinc-800 separators (#27272a).
 */

import React, { useState, useEffect, useCallback } from 'react';
import { 
  Calendar, 
  Plus, 
  UploadCloud, 
  Download, 
  Sparkles, 
  Wand2, 
  FileSpreadsheet, 
  FileText, 
  Code,
  CheckCircle2,
  X,
  RefreshCw
} from 'lucide-react';
import { PrelineTopHeader } from './PrelineTopHeader';
import { PrelineDoubleSidebar } from './PrelineDoubleSidebar';
import { PrelineKPIStrip } from './PrelineKPIStrip';
import { PrelineWorldMap } from './PrelineWorldMap';
import { PrelineCountryTable, DEFAULT_COUNTRIES } from './PrelineCountryTable';
import { PrelineAnalyticsChart } from './PrelineAnalyticsChart';
import { PrelineDataGrid } from './PrelineDataGrid';
import { PrelineCopilotDrawer } from './PrelineCopilotDrawer';
import { PrelineVisitorsView } from './PrelineVisitorsView';
import { PrelineSurveyView } from './PrelineSurveyView';
import { PrelineIncidentsView } from './PrelineIncidentsView';
import { PrelineEmptyView } from './PrelineEmptyView';
import { DatasetProfile, dataIntelligenceService } from '@/services/data-intelligence.service';
import { toast } from 'sonner';

export const PrelineDashboard: React.FC = () => {
  // Navigation & UI States
  const [activeView, setActiveView] = useState('overview');
  const [selectedCountry, setSelectedCountry] = useState<string | null>(null);
  const [activeSegment, setActiveSegment] = useState(0);
  const [isCopilotOpen, setIsCopilotOpen] = useState(false);
  const [isDarkMode, setIsDarkMode] = useState(true);
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [showExportModal, setShowExportModal] = useState(false);

  // Backend Dataset & Profile States
  const [profile, setProfile] = useState<DatasetProfile | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  // Auto-load default dataset on startup for zero blank states
  useEffect(() => {
    const initData = async () => {
      try {
        setIsLoading(true);
        const data = await dataIntelligenceService.loadSampleDataset('ecommerce_sales');
        setProfile(data);
      } catch (e) {
        console.warn('Initial sample load note:', e);
      } finally {
        setIsLoading(false);
      }
    };
    initData();
  }, []);

  // Upload handler
  const handleFileUpload = useCallback(async (file: File) => {
    setIsLoading(true);
    setShowUploadModal(false);
    const toastId = toast.loading(`Uploading and inspecting ${file.name}...`);
    try {
      const data = await dataIntelligenceService.uploadDataset(file);
      setProfile(data);
      toast.success(`Successfully loaded ${data.total_rows.toLocaleString()} records! Health score: ${data.health_score}%`, {
        id: toastId,
      });
    } catch (err: any) {
      toast.error(`Upload error: ${err.response?.data?.detail || err.message}`, { id: toastId });
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Sample Switcher
  const handleSampleSwitch = useCallback(async (sampleId: 'ecommerce_sales' | 'customer_churn' | 'financial_kpi') => {
    setIsLoading(true);
    const toastId = toast.loading('Loading sample dataset...');
    try {
      const data = await dataIntelligenceService.loadSampleDataset(sampleId);
      setProfile(data);
      toast.success(`Loaded ${data.dataset_name}!`, { id: toastId });
    } catch (e: any) {
      toast.error(`Failed to switch: ${e.message}`, { id: toastId });
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Auto-Clean Trigger
  const handleAutoClean = useCallback(async () => {
    if (!profile) return;
    setIsLoading(true);
    const toastId = toast.loading('Running automated data cleaning pipeline...');
    try {
      const updated = await dataIntelligenceService.cleanDataset(profile.session_id, 'auto_clean');
      setProfile(updated);
      toast.success(updated.audit_entry || 'Dataset cleaned successfully!', { id: toastId });
    } catch (err: any) {
      toast.error(`Clean error: ${err.message}`, { id: toastId });
    } finally {
      setIsLoading(false);
    }
  }, [profile]);

  // Export Trigger
  const handleExport = useCallback((fmt: 'csv' | 'xlsx' | 'json' | 'pdf') => {
    if (!profile) {
      toast.error("Please load a dataset first.");
      return;
    }
    toast.info(`Generating ${fmt.toUpperCase()} download...`);
    dataIntelligenceService.triggerDownload(profile.session_id, fmt);
    setShowExportModal(false);
  }, [profile]);

  // Handle country click toggle
  const handleCountryToggle = (country: string) => {
    if (selectedCountry === country) {
      setSelectedCountry(null);
    } else {
      setSelectedCountry(country);
      toast.info(`Filtering data for ${country}`);
    }
  };

  return (
    <div className="h-screen w-screen flex flex-col bg-[#09090b] text-zinc-100 overflow-hidden font-sans">
      {/* 1. TOP HEADER - Pure Smooth Z-Black */}
      <PrelineTopHeader
        onUploadClick={() => setShowUploadModal(true)}
        onExportClick={() => setShowExportModal(true)}
        isDarkMode={isDarkMode}
        onToggleDarkMode={() => setIsDarkMode(!isDarkMode)}
      />

      {/* 2. BODY WORKSPACE (Double Sidebar + Main Canvas) */}
      <div className="flex-1 flex overflow-hidden">
        {/* Double Column Left Sidebar - Pure Smooth Z-Black */}
        <PrelineDoubleSidebar
          activeView={activeView}
          onSelectView={setActiveView}
          onOpenCopilot={() => setIsCopilotOpen(true)}
          onOpenUpload={() => setShowUploadModal(true)}
          onAutoClean={handleAutoClean}
          creditsUsed={profile ? Math.min(100, Math.round(profile.health_score * 0.8)) : 65}
          totalCredits={100}
        />

        {/* MAIN CANVAS - Pure Smooth Z-Black */}
        <main className="flex-1 overflow-y-auto bg-[#09090b] p-6 space-y-6 transition-colors">
          {/* VIEW ROUTER */}
          {activeView === 'overview' && (
            <>
              {/* Top Title Row: "Overview" + Today Date Filter + "+ Add activity" CTA */}
              <div className="flex flex-wrap items-center justify-between gap-4">
                <div>
                  <h1 className="text-2xl font-bold tracking-tight text-zinc-100">
                    Overview
                  </h1>
                  {profile && (
                    <div className="flex items-center gap-2 mt-1 text-xs text-zinc-400">
                      <span className="font-medium text-zinc-300">{profile.dataset_name}</span>
                      <span>•</span>
                      <span>{profile.total_rows.toLocaleString()} rows</span>
                      <span>•</span>
                      <span className="inline-flex items-center gap-1 text-emerald-400 font-semibold bg-emerald-500/10 px-2 py-0.5 rounded-full border border-emerald-500/20">
                        <CheckCircle2 className="w-3 h-3" />
                        Health {profile.health_score}%
                      </span>
                    </div>
                  )}
                </div>

                <div className="flex items-center gap-2.5">
                  {/* Quick Sample Dataset Selector Pills */}
                  <div className="hidden sm:flex items-center gap-1.5 bg-[#121215] p-1 rounded-lg text-xs font-medium text-zinc-300 border border-[#27272a]">
                    <button
                      onClick={() => handleSampleSwitch('ecommerce_sales')}
                      className="px-2.5 py-1 rounded-md hover:bg-[#1c1c22] hover:text-zinc-100 transition-all text-xs"
                    >
                      E-Commerce
                    </button>
                    <button
                      onClick={() => handleSampleSwitch('customer_churn')}
                      className="px-2.5 py-1 rounded-md hover:bg-[#1c1c22] hover:text-zinc-100 transition-all text-xs"
                    >
                      SaaS Churn
                    </button>
                    <button
                      onClick={() => handleSampleSwitch('financial_kpi')}
                      className="px-2.5 py-1 rounded-md hover:bg-[#1c1c22] hover:text-zinc-100 transition-all text-xs"
                    >
                      Financial
                    </button>
                  </div>

                  {/* Date Filter Dropdown (Matches Preline "Today v") */}
                  <button className="inline-flex items-center gap-2 bg-[#141418] hover:bg-[#1b1b22] border border-[#27272a] text-xs font-medium text-zinc-200 px-3 py-1.5 rounded-lg shadow-2xs transition-colors">
                    <Calendar className="w-3.5 h-3.5 text-zinc-400" />
                    <span>Today</span>
                    <span className="text-zinc-500">▾</span>
                  </button>

                  {/* Primary Action Button (Matches "+ Add activity") */}
                  <button
                    onClick={() => setShowUploadModal(true)}
                    className="inline-flex items-center gap-1.5 bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold px-3.5 py-1.5 rounded-lg shadow-xs transition-colors"
                  >
                    <Plus className="w-3.5 h-3.5" />
                    <span>Add activity</span>
                  </button>
                </div>
              </div>

              {/* 3. 4-SEGMENT HORIZONTAL KPI STRIP */}
              <PrelineKPIStrip
                activeSegment={activeSegment}
                onSelectSegment={setActiveSegment}
                users={profile ? profile.total_rows.toLocaleString() : "54,382"}
                usersTrend="1.2%"
                isUsersPositive={true}
                newUsers={profile ? Math.round(profile.total_rows * 0.06).toLocaleString() : "3,301"}
                newUsersTrend="5.2%"
                isNewUsersPositive={false}
                returningUsers={profile ? (profile.total_rows - Math.round(profile.total_rows * 0.06)).toLocaleString() : "50,402"}
                returningUsersTrend="14.7%"
                isReturningPositive={false}
                avgEngagement="2m 25s"
                avgEngagementTrend="3%"
                isEngagementPositive={true}
              />

              {/* 4. WORLD MAP & COUNTRY TABLE SECTION - Smooth Z-Black with crisp separator */}
              <div className="bg-[#0e0e11] rounded-xl border border-[#27272a] p-6 shadow-xs transition-colors">
                <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-center">
                  {/* Left Map (Col 7) */}
                  <div className="lg:col-span-7 flex flex-col justify-center">
                    <PrelineWorldMap
                      selectedCountry={selectedCountry}
                      onSelectCountry={handleCountryToggle}
                    />
                  </div>

                  {/* Right Country Table (Col 5) */}
                  <div className="lg:col-span-5 border-t lg:border-t-0 lg:border-l border-[#27272a] pt-6 lg:pt-0 lg:pl-8">
                    <PrelineCountryTable
                      selectedCountry={selectedCountry}
                      onSelectCountry={handleCountryToggle}
                    />
                  </div>
                </div>
              </div>

              {/* 5. GROWTH TIMELINE CHART & AUTO-CLEAN CARD ROW */}
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <div className="lg:col-span-2">
                  <PrelineAnalyticsChart
                    title="Visitors & Sessions Growth"
                    totalValue={profile ? `${(profile.total_rows * 52).toLocaleString()}` : "54,382"}
                    trendPercentage="+12.5%"
                  />
                </div>

                {/* Quick Actions & Export Card */}
                <div className="bg-[#0e0e11] rounded-xl border border-[#27272a] p-5 shadow-xs flex flex-col justify-between transition-colors">
                  <div>
                    <span className="text-xs font-semibold text-zinc-400 uppercase tracking-wider block mb-1">
                      Actions &amp; Data Health
                    </span>
                    <h3 className="text-base font-bold text-zinc-100 mb-2">
                      Intelligent Data Engine
                    </h3>
                    <p className="text-xs text-zinc-400 leading-relaxed mb-4">
                      Run automated missingness imputation, remove statistical outliers, or export executive PDF and Excel reports.
                    </p>

                    <div className="space-y-2">
                      <button
                        onClick={handleAutoClean}
                        disabled={isLoading || !profile}
                        className="w-full flex items-center justify-center gap-2 py-2 px-3 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-xs font-semibold shadow-xs transition-colors disabled:opacity-50"
                      >
                        <Wand2 className="w-3.5 h-3.5" />
                        <span>Run One-Click Auto-Clean</span>
                      </button>

                      <button
                        onClick={() => setIsCopilotOpen(true)}
                        className="w-full flex items-center justify-center gap-2 py-2 px-3 bg-[#181822] hover:bg-[#20202e] text-indigo-400 border border-indigo-500/30 rounded-lg text-xs font-semibold transition-colors"
                      >
                        <Sparkles className="w-3.5 h-3.5" />
                        <span>Open AI Data Copilot</span>
                      </button>
                    </div>
                  </div>

                  {/* Export Toolbar */}
                  <div className="pt-4 mt-4 border-t border-[#27272a]">
                    <span className="text-[11px] font-semibold text-zinc-400 uppercase tracking-wider block mb-2">
                      One-Click Export
                    </span>
                    <div className="grid grid-cols-2 gap-2">
                      <button
                        onClick={() => handleExport('csv')}
                        className="inline-flex items-center justify-center gap-1.5 py-1.5 px-2 bg-[#141418] hover:bg-[#1b1b22] border border-[#27272a] rounded-lg text-xs font-medium text-zinc-200 transition-colors"
                      >
                        <FileSpreadsheet className="w-3.5 h-3.5 text-emerald-400" />
                        <span>CSV</span>
                      </button>
                      <button
                        onClick={() => handleExport('xlsx')}
                        className="inline-flex items-center justify-center gap-1.5 py-1.5 px-2 bg-[#141418] hover:bg-[#1b1b22] border border-[#27272a] rounded-lg text-xs font-medium text-zinc-200 transition-colors"
                      >
                        <FileSpreadsheet className="w-3.5 h-3.5 text-blue-400" />
                        <span>Excel</span>
                      </button>
                      <button
                        onClick={() => handleExport('json')}
                        className="inline-flex items-center justify-center gap-1.5 py-1.5 px-2 bg-[#141418] hover:bg-[#1b1b22] border border-[#27272a] rounded-lg text-xs font-medium text-zinc-200 transition-colors"
                      >
                        <Code className="w-3.5 h-3.5 text-amber-400" />
                        <span>JSON</span>
                      </button>
                      <button
                        onClick={() => handleExport('pdf')}
                        className="inline-flex items-center justify-center gap-1.5 py-1.5 px-2 bg-[#141418] hover:bg-[#1b1b22] border border-[#27272a] rounded-lg text-xs font-medium text-zinc-200 transition-colors"
                      >
                        <FileText className="w-3.5 h-3.5 text-rose-400" />
                        <span>PDF</span>
                      </button>
                    </div>
                  </div>
                </div>
              </div>

              {/* 6. LIVE DATA GRID TABLE */}
              {profile && (
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <div>
                      <div className="flex items-center gap-2">
                        <h3 className="text-base font-bold text-zinc-100">
                          Live Data Inspector
                        </h3>
                        {selectedCountry && (
                          <span className="inline-flex items-center gap-1 text-xs font-medium bg-blue-600/15 text-blue-400 px-2 py-0.5 rounded-full border border-blue-500/30">
                            Country: {selectedCountry}
                            <button
                              onClick={() => setSelectedCountry(null)}
                              className="hover:text-blue-200 ml-1"
                            >
                              <X className="w-3 h-3" />
                            </button>
                          </span>
                        )}
                      </div>
                      <p className="text-xs text-zinc-400">
                        Sorted and filtered directly with your active dataset
                      </p>
                    </div>
                  </div>

                  <PrelineDataGrid
                    data={profile.preview}
                    columns={profile.columns}
                    totalRows={profile.total_rows}
                    onExportCsv={() => handleExport('csv')}
                    filterQuery={selectedCountry}
                  />
                </div>
              )}
            </>
          )}

          {/* VISITORS VIEW */}
          {activeView === 'visitors' && (
            <PrelineVisitorsView totalRows={profile ? profile.total_rows : 54382} />
          )}

          {/* SURVEY VIEW */}
          {activeView === 'survey' && (
            <PrelineSurveyView />
          )}

          {/* INCIDENTS VIEW */}
          {activeView === 'incidents' && (
            <PrelineIncidentsView
              profile={profile}
              onRefreshProfile={(updated) => setProfile(updated)}
            />
          )}

          {/* EMPTY VIEW */}
          {activeView === 'empty' && (
            <PrelineEmptyView
              onUploadClick={() => setShowUploadModal(true)}
              onLoadSample={handleSampleSwitch}
            />
          )}
        </main>
      </div>

      {/* 3. COPILOT FLYOUT DRAWER */}
      <PrelineCopilotDrawer
        isOpen={isCopilotOpen}
        onClose={() => setIsCopilotOpen(false)}
        sessionId={profile ? profile.session_id : null}
        onDatasetMutated={async () => {
          if (profile) {
            const updated = await dataIntelligenceService.cleanDataset(profile.session_id, 'coerce_types');
            setProfile(updated);
          }
        }}
      />

      {/* 4. UPLOAD MODAL */}
      {showUploadModal && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-[#121215] rounded-2xl border border-[#27272a] p-6 max-w-md w-full shadow-2xl space-y-4 animate-in fade-in zoom-in-95 duration-150">
            <div className="flex items-center justify-between border-b border-[#27272a] pb-3">
              <h3 className="text-sm font-bold text-zinc-100 flex items-center gap-2">
                <UploadCloud className="w-4 h-4 text-blue-400" />
                Upload Dataset
              </h3>
              <button
                onClick={() => setShowUploadModal(false)}
                className="text-zinc-400 hover:text-zinc-100 text-xs p-1"
              >
                ✕
              </button>
            </div>

            <p className="text-xs text-zinc-400">
              Select a CSV, Excel (.xlsx, .xls), or JSON file up to 50MB. Auto-generates health score, column types, and statistical anomalies.
            </p>

            <label className="border-2 border-dashed border-[#27272a] hover:border-blue-500 rounded-xl p-8 flex flex-col items-center justify-center cursor-pointer transition-colors bg-[#0e0e11] hover:bg-blue-950/10 block">
              <UploadCloud className="w-8 h-8 text-blue-400 mb-2" />
              <span className="text-xs font-semibold text-zinc-200">
                Click to browse or drag file here
              </span>
              <span className="text-[11px] text-zinc-500 mt-1">
                CSV, XLSX, XLS, JSON
              </span>
              <input
                type="file"
                accept=".csv,.xlsx,.xls,.json"
                className="hidden"
                onChange={(e) => {
                  if (e.target.files && e.target.files.length > 0) {
                    handleFileUpload(e.target.files[0]);
                  }
                }}
              />
            </label>
          </div>
        </div>
      )}
    </div>
  );
};
