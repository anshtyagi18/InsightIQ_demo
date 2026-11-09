/**
 * Insightia Production-Ready 3-Panel Workspace.
 * Clean, "no-slop" enterprise data analytics platform following Linear / Supabase dark design aesthetic.
 */

import React, { useState, useEffect, useCallback } from 'react';
import { LeftRail } from './LeftRail';
import { CenterCanvas } from './CenterCanvas';
import { CopilotRail } from './CopilotRail';
import { DatasetProfile, dataIntelligenceService } from '@/services/data-intelligence.service';
import { toast } from 'sonner';

export const InsightiaWorkspace: React.FC = () => {
  const [profile, setProfile] = useState<DatasetProfile | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  // Auto-load sample dataset on first mount for instant zero-friction experience
  useEffect(() => {
    const initDefaultSample = async () => {
      try {
        setIsLoading(true);
        const data = await dataIntelligenceService.loadSampleDataset('ecommerce_sales');
        setProfile(data);
      } catch (err: any) {
        console.warn('Could not auto-load initial sample:', err);
      } finally {
        setIsLoading(false);
      }
    };

    initDefaultSample();
  }, []);

  // Handle local file upload
  const handleUploadFile = useCallback(async (file: File) => {
    setIsLoading(true);
    const toastId = toast.loading(`Uploading and profiling ${file.name}...`);
    try {
      const data = await dataIntelligenceService.uploadDataset(file);
      setProfile(data);
      toast.success(`Ingested ${data.total_rows.toLocaleString()} records! Health Score: ${data.health_score}%`, {
        id: toastId,
      });
    } catch (err: any) {
      toast.error(`Upload error: ${err.response?.data?.detail || err.message}`, {
        id: toastId,
      });
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Handle sample dataset switch
  const handleLoadSample = useCallback(async (sampleId: 'ecommerce_sales' | 'customer_churn' | 'financial_kpi') => {
    setIsLoading(true);
    const toastId = toast.loading('Loading curated sample dataset...');
    try {
      const data = await dataIntelligenceService.loadSampleDataset(sampleId);
      setProfile(data);
      toast.success(`Loaded ${data.dataset_name}!`, { id: toastId });
    } catch (err: any) {
      toast.error(`Error loading sample: ${err.message}`, { id: toastId });
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Handle data cleaning
  const handleClean = useCallback(async (action: any, params?: any) => {
    if (!profile) return;
    setIsLoading(true);
    const toastId = toast.loading(`Executing ${action} cleaning pipeline...`);
    try {
      const updated = await dataIntelligenceService.cleanDataset(profile.session_id, action, params);
      setProfile(updated);
      const deltaMsg = updated.health_score_delta 
        ? ` (Health Score: +${updated.health_score_delta}%)` 
        : '';
      toast.success(`${updated.audit_entry || 'Dataset cleaned successfully!'}${deltaMsg}`, {
        id: toastId,
      });
    } catch (err: any) {
      toast.error(`Cleaning error: ${err.response?.data?.detail || err.message}`, {
        id: toastId,
      });
    } finally {
      setIsLoading(false);
    }
  }, [profile]);

  // Handle exports
  const handleExport = useCallback((format: 'csv' | 'xlsx' | 'json' | 'pdf') => {
    if (!profile) {
      toast.error('No active dataset to export.');
      return;
    }
    toast.info(`Generating ${format.toUpperCase()} export...`);
    dataIntelligenceService.triggerDownload(profile.session_id, format);
  }, [profile]);

  // Refresh profile if copilot mutated data
  const handleDatasetMutated = useCallback(async () => {
    if (!profile) return;
    try {
      // Re-fetch sample or clean request to update preview
      const updated = await dataIntelligenceService.cleanDataset(profile.session_id, 'coerce_types');
      setProfile(updated);
    } catch (e) {
      console.warn('Profile refresh notice:', e);
    }
  }, [profile]);

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-zinc-950 text-zinc-100 font-sans antialiased">
      {/* 1. Left Rail (Schema, Health, Clean Actions, Audit, Exports) */}
      <LeftRail
        profile={profile}
        isLoading={isLoading}
        onClean={handleClean}
        onExport={handleExport}
      />

      {/* 2. Center Canvas (KPIs, Charts, EDA, TanStack Table) */}
      <CenterCanvas
        profile={profile}
        isLoading={isLoading}
        onUploadFile={handleUploadFile}
        onLoadSample={handleLoadSample}
      />

      {/* 3. Right Rail (Multilingual & Hinglish Grounded AI Copilot) */}
      <CopilotRail
        sessionId={profile ? profile.session_id : null}
        datasetName={profile ? profile.dataset_name : undefined}
        onDatasetMutated={handleDatasetMutated}
      />
    </div>
  );
};

