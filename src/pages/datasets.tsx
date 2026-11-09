import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { datasetStorage, SavedDataset } from '@/services/dataset-storage.service';
import { DatasetList } from '@/components/datasets/DatasetList';
import { DatasetWorkspace } from '@/components/datasets/DatasetWorkspace';
import { DatasetUploadModal } from '@/components/datasets/DatasetUploadModal';
import { generateBIDashboard } from '@/services/bi-engine';
import { toast } from 'sonner';

export default function DatasetsPage() {
  const navigate = useNavigate();
  const [datasets, setDatasets] = useState<SavedDataset[]>([]);
  const [activeDatasetId, setActiveDatasetId] = useState<string | null>(null);
  const [selectedWorkspaceId, setSelectedWorkspaceId] = useState<string | null>(null);
  const [isUploadModalOpen, setIsUploadModalOpen] = useState<boolean>(false);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  // Load saved datasets
  const loadDatasets = useCallback(async () => {
    setIsLoading(true);
    try {
      const list = await datasetStorage.getAllDatasets();
      setDatasets([...list]);
      const active = await datasetStorage.getActiveDataset();
      setActiveDatasetId(active ? active.id : null);
    } catch (err) {
      console.error('Failed to load datasets:', err);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    loadDatasets();
  }, [loadDatasets]);

  // Handle Powering Dashboard
  const handlePowerDashboard = async (dataset: SavedDataset) => {
    try {
      await datasetStorage.setActiveDataset(dataset.id);
      setActiveDatasetId(dataset.id);

      // Generate BI dashboard config for this dataset
      const biDashboard = generateBIDashboard(dataset.cleanedRows, dataset.name);

      // Save state to current_dashboard_state so Dashboard uses it instantly
      const stateToSave = {
        config: biDashboard,
        charts: biDashboard.charts,
        kpis: biDashboard.kpis,
        loading: false,
        error: null,
        lastGenerated: new Date().toISOString()
      };
      localStorage.setItem('current_dashboard_state', JSON.stringify(stateToSave));

      toast.success(`Dashboard now powered by "${dataset.name}"`);
      navigate('/dashboard');
    } catch (err) {
      toast.error('Failed to activate dataset for dashboard');
    }
  };

  const selectedWorkspaceDataset = datasets.find(d => d.id === selectedWorkspaceId);

  return (
    <div className="space-y-6 animate-fade-in max-w-7xl mx-auto">
      {selectedWorkspaceDataset ? (
        <DatasetWorkspace
          dataset={selectedWorkspaceDataset}
          onBack={() => setSelectedWorkspaceId(null)}
          onPowerDashboard={handlePowerDashboard}
          onUpdateDataset={(updated) => {
            setDatasets(datasets.map(d => d.id === updated.id ? updated : d));
          }}
        />
      ) : (
        <DatasetList
          datasets={datasets}
          activeDatasetId={activeDatasetId}
          onSelectDataset={(id) => setSelectedWorkspaceId(id)}
          onPowerDashboard={handlePowerDashboard}
          onRefresh={loadDatasets}
          onOpenUploadModal={() => setIsUploadModalOpen(true)}
        />
      )}

      <DatasetUploadModal
        isOpen={isUploadModalOpen}
        onClose={() => setIsUploadModalOpen(false)}
        onSuccess={(newDataset) => {
          loadDatasets();
          setSelectedWorkspaceId(newDataset.id);
        }}
      />
    </div>
  );
}
