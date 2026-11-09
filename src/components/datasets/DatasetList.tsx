import React, { useState } from 'react';
import { SavedDataset, datasetStorage } from '@/services/dataset-storage.service';
import { 
  Database, 
  Sparkles, 
  Trash2, 
  Download, 
  Play, 
  FileSpreadsheet, 
  Calendar, 
  CheckCircle2, 
  Table, 
  Sliders, 
  Upload, 
  Plus, 
  ArrowRight,
  Layers,
  AlertTriangle
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { parseDatasetFile } from '@/services/bi-engine';
import { toast } from 'sonner';

interface DatasetListProps {
  datasets: SavedDataset[];
  activeDatasetId: string | null;
  onSelectDataset: (id: string) => void;
  onPowerDashboard: (dataset: SavedDataset) => void;
  onRefresh: () => void;
  onOpenUploadModal: () => void;
}

export const DatasetList: React.FC<DatasetListProps> = ({
  datasets,
  activeDatasetId,
  onSelectDataset,
  onPowerDashboard,
  onRefresh,
  onOpenUploadModal,
}) => {
  const [datasetToDelete, setDatasetToDelete] = useState<{ id: string; name: string } | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);

  const confirmDelete = async () => {
    if (!datasetToDelete) return;
    const { id, name } = datasetToDelete;

    setIsDeleting(true);
    try {
      await datasetStorage.deleteDataset(id);
      toast.success(`Dataset "${name}" deleted`);
      setDatasetToDelete(null);
      onRefresh();
    } catch (err) {
      toast.error('Failed to delete dataset');
    } finally {
      setIsDeleting(false);
    }
  };

  const handleOpenDeleteDialog = (e: React.MouseEvent, id: string, name: string) => {
    e.stopPropagation();
    setDatasetToDelete({ id, name });
  };

  const handleExport = (e: React.MouseEvent, dataset: SavedDataset, format: 'csv' | 'json') => {
    e.stopPropagation();
    try {
      let content = '';
      let mimeType = '';
      let filename = `${dataset.name.toLowerCase().replace(/\s+/g, '_')}_cleaned.${format}`;

      if (format === 'json') {
        content = JSON.stringify(dataset.cleanedRows, null, 2);
        mimeType = 'application/json';
      } else {
        // Convert to CSV
        if (dataset.cleanedRows.length === 0) return;
        const headers = Object.keys(dataset.cleanedRows[0]);
        const csvLines = [
          headers.join(','),
          ...dataset.cleanedRows.map(row => 
            headers.map(h => {
              const val = row[h] ?? '';
              const strVal = String(val).replace(/"/g, '""');
              return strVal.includes(',') || strVal.includes('\n') ? `"${strVal}"` : strVal;
            }).join(',')
          )
        ];
        content = csvLines.join('\n');
        mimeType = 'text/csv';
      }

      const blob = new Blob([content], { type: mimeType });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      toast.success(`Exported ${dataset.name} as ${format.toUpperCase()}`);
    } catch (err) {
      toast.error('Export failed');
    }
  };

  return (
    <div className="space-y-6">
      {/* Action Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 bg-white/5 border border-white/10 rounded-2xl p-6 backdrop-blur-xl">
        <div>
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <Database className="w-5 h-5 text-blue-400" />
            Your Saved Datasets
          </h2>
          <p className="text-sm text-white/60 mt-1">
            Manage, clean, and activate your datasets to power dashboards and analytics.
          </p>
        </div>

        <div className="flex items-center gap-3 w-full sm:w-auto">
          <Button
            onClick={onOpenUploadModal}
            className="bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white shadow-lg flex-1 sm:flex-none"
          >
            <Upload className="w-4 h-4 mr-2" />
            Upload Dataset
          </Button>
        </div>
      </div>

      {/* Datasets Grid */}
      {datasets.length === 0 ? (
        <div className="glass-card p-12 text-center rounded-2xl border border-white/10">
          <FileSpreadsheet className="w-12 h-12 text-blue-400/50 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-white mb-2">No Datasets Available</h3>
          <p className="text-sm text-white/60 max-w-md mx-auto mb-6">
            Upload a CSV, Excel, or JSON file to start cleaning data and generating interactive dashboards.
          </p>
          <Button onClick={onOpenUploadModal} className="bg-blue-600 text-white">
            <Plus className="w-4 h-4 mr-2" /> Upload First Dataset
          </Button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {datasets.map((ds) => {
            const isActive = ds.id === activeDatasetId;
            return (
              <div
                key={ds.id}
                onClick={() => onSelectDataset(ds.id)}
                className={`group relative glass-card p-6 rounded-2xl border transition-all duration-300 hover:border-blue-500/50 cursor-pointer flex flex-col justify-between ${
                  isActive 
                    ? 'border-blue-500 bg-blue-500/10 shadow-lg shadow-blue-500/10' 
                    : 'border-white/10 hover:bg-white/5'
                }`}
              >
                <div>
                  {/* Top Bar */}
                  <div className="flex items-start justify-between gap-2 mb-3">
                    <div className="flex items-center gap-2">
                      <div className="p-2 rounded-lg bg-blue-500/20 text-blue-400">
                        <FileSpreadsheet className="w-5 h-5" />
                      </div>
                      <div>
                        <h3 className="font-bold text-white text-base truncate max-w-[180px] group-hover:text-blue-300 transition-colors">
                          {ds.name}
                        </h3>
                        <p className="text-xs text-white/50 truncate max-w-[180px]">
                          {ds.filename}
                        </p>
                      </div>
                    </div>

                    {isActive ? (
                      <Badge className="bg-emerald-500/20 text-emerald-300 border-emerald-500/30 flex items-center gap-1">
                        <CheckCircle2 className="w-3 h-3" /> Active
                      </Badge>
                    ) : (
                      <Badge variant="outline" className="text-white/40 border-white/10">
                        Saved
                      </Badge>
                    )}
                  </div>

                  {/* Metrics Bar */}
                  <div className="grid grid-cols-3 gap-2 py-3 border-y border-white/10 my-4 text-center">
                    <div>
                      <p className="text-xs text-white/50">Rows</p>
                      <p className="text-sm font-semibold text-white">{ds.rowCount.toLocaleString()}</p>
                    </div>
                    <div>
                      <p className="text-xs text-white/50">Columns</p>
                      <p className="text-sm font-semibold text-white">{ds.columnCount}</p>
                    </div>
                    <div>
                      <p className="text-xs text-white/50">Quality</p>
                      <p className="text-sm font-semibold text-emerald-400">{ds.profile?.completeness || 100}%</p>
                    </div>
                  </div>

                  {/* Column Badges */}
                  <div className="flex flex-wrap gap-1.5 mb-4">
                    {ds.columns.slice(0, 4).map((col) => (
                      <span key={col} className="text-[11px] px-2 py-0.5 rounded bg-white/5 text-white/70 border border-white/5">
                        {col}
                      </span>
                    ))}
                    {ds.columns.length > 4 && (
                      <span className="text-[11px] px-2 py-0.5 rounded bg-white/5 text-white/40">
                        +{ds.columns.length - 4} more
                      </span>
                    )}
                  </div>
                </div>

                {/* Footer Buttons */}
                <div className="pt-2 flex items-center justify-between gap-2 border-t border-white/5">
                  <div className="flex items-center gap-1">
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={(e) => handleExport(e, ds, 'csv')}
                      className="h-8 px-2 text-white/70 hover:text-white hover:bg-white/10"
                      title="Export CSV"
                    >
                      <Download className="w-3.5 h-3.5" />
                    </Button>
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={(e) => handleOpenDeleteDialog(e, ds.id, ds.name)}
                      className="h-8 px-2 text-red-400/70 hover:text-red-400 hover:bg-red-500/10"
                      title="Delete Dataset"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </Button>
                  </div>

                  <div className="flex items-center gap-2">
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={(e) => {
                        e.stopPropagation();
                        onSelectDataset(ds.id);
                      }}
                      className="h-8 text-xs border-white/20 hover:bg-white/10 text-white"
                    >
                      <Sliders className="w-3.5 h-3.5 mr-1" /> Clean
                    </Button>

                    <Button
                      size="sm"
                      onClick={(e) => {
                        e.stopPropagation();
                        onPowerDashboard(ds);
                      }}
                      className="h-8 text-xs bg-blue-600 hover:bg-blue-500 text-white"
                    >
                      <Play className="w-3.5 h-3.5 mr-1 fill-current" /> Dashboard
                    </Button>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Delete Confirmation Dialog */}
      <Dialog open={!!datasetToDelete} onOpenChange={(open) => !open && setDatasetToDelete(null)}>
        <DialogContent className="fixed left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 z-50 bg-slate-900 border-slate-800 text-white max-w-md w-[95vw]">
          <DialogHeader>
            <div className="flex items-center gap-3 mb-2">
              <div className="p-2 rounded-xl bg-red-500/20 text-red-400 border border-red-500/30">
                <AlertTriangle className="w-5 h-5" />
              </div>
              <DialogTitle className="text-lg font-bold text-white">Delete Dataset</DialogTitle>
            </div>
            <DialogDescription className="text-slate-300 text-sm">
              Are you sure you want to permanently delete <span className="font-semibold text-white">"{datasetToDelete?.name}"</span>? This will remove all associated raw and cleaned data from your workspace.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter className="mt-4 flex gap-2 sm:justify-end">
            <Button
              variant="outline"
              onClick={() => setDatasetToDelete(null)}
              disabled={isDeleting}
              className="border-slate-700 bg-slate-800 text-slate-200 hover:bg-slate-700 text-xs"
            >
              Cancel
            </Button>
            <Button
              onClick={confirmDelete}
              disabled={isDeleting}
              className="bg-red-600 hover:bg-red-500 text-white text-xs font-semibold"
            >
              {isDeleting ? 'Deleting...' : 'Delete Dataset'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};
