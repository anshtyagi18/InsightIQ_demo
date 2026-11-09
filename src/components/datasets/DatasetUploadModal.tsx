import React, { useState } from 'react';
import { parseDatasetFile } from '@/services/bi-engine';
import { datasetStorage, SavedDataset } from '@/services/dataset-storage.service';
import { Upload, X, FileSpreadsheet, Check, Sparkles, AlertCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { toast } from 'sonner';

interface DatasetUploadModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: (dataset: SavedDataset) => void;
}

export const DatasetUploadModal: React.FC<DatasetUploadModalProps> = ({
  isOpen,
  onClose,
  onSuccess,
}) => {
  const [file, setFile] = useState<File | null>(null);
  const [datasetName, setDatasetName] = useState<string>('');
  const [isProcessing, setIsProcessing] = useState<boolean>(false);
  const [dragOver, setDragOver] = useState<boolean>(false);

  if (!isOpen) return null;

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const selected = e.target.files[0];
      setFile(selected);
      if (!datasetName) {
        const nameWithoutExt = selected.name.replace(/\.[^/.]+$/, '');
        setDatasetName(nameWithoutExt.replace(/_/g, ' ').replace(/-/g, ' '));
      }
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const selected = e.dataTransfer.files[0];
      setFile(selected);
      if (!datasetName) {
        const nameWithoutExt = selected.name.replace(/\.[^/.]+$/, '');
        setDatasetName(nameWithoutExt.replace(/_/g, ' ').replace(/-/g, ' '));
      }
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) {
      toast.error('Please select a file to upload');
      return;
    }

    setIsProcessing(true);
    try {
      const parsed = await parseDatasetFile(file);
      if (!parsed.data || parsed.data.length === 0) {
        toast.error('File contains no valid rows or data');
        setIsProcessing(false);
        return;
      }

      const columns = Object.keys(parsed.data[0]);
      const saved = await datasetStorage.saveDataset({
        name: datasetName || file.name,
        filename: file.name,
        sizeBytes: file.size,
        rowCount: parsed.data.length,
        columnCount: columns.length,
        columns,
        rawRows: parsed.data,
        cleanedRows: parsed.data,
        profile: undefined as any,
        cleaningHistory: [
          {
            id: '1',
            timestamp: new Date().toISOString(),
            action: 'Upload',
            details: `Uploaded ${file.name} (${parsed.data.length} rows, ${columns.length} cols)`
          }
        ]
      });

      toast.success(`Dataset "${saved.name}" uploaded successfully!`);
      onSuccess(saved);
      onClose();
    } catch (err: any) {
      toast.error(`Upload error: ${err.message || 'Failed to parse file'}`);
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md animate-fade-in">
      <div className="glass-card border border-white/20 rounded-2xl w-full max-w-lg p-6 bg-slate-900/95 text-white shadow-2xl relative">
        <button
          onClick={onClose}
          className="absolute top-4 right-4 text-white/60 hover:text-white p-1 rounded-lg"
        >
          <X className="w-5 h-5" />
        </button>

        <div className="flex items-center gap-3 mb-6">
          <div className="p-3 rounded-xl bg-blue-500/20 text-blue-400">
            <Upload className="w-6 h-6" />
          </div>
          <div>
            <h2 className="text-xl font-bold">Upload New Dataset</h2>
            <p className="text-xs text-white/60">Supports CSV, Excel (.xlsx, .xls) and JSON formats</p>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <Label className="text-sm font-semibold text-white/80 mb-1 block">Dataset Title</Label>
            <Input
              value={datasetName}
              onChange={(e) => setDatasetName(e.target.value)}
              placeholder="e.g. Q3 Regional Sales Performance"
              className="bg-black/40 border-white/10 text-white"
            />
          </div>

          <div
            onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
            onDragLeave={() => setDragOver(false)}
            onDrop={handleDrop}
            className={`border-2 border-dashed rounded-xl p-8 text-center transition-all cursor-pointer ${
              dragOver 
                ? 'border-blue-500 bg-blue-500/10' 
                : file 
                  ? 'border-emerald-500/50 bg-emerald-500/5' 
                  : 'border-white/20 hover:border-white/40 bg-black/20'
            }`}
            onClick={() => document.getElementById('file-upload-input')?.click()}
          >
            <input
              id="file-upload-input"
              type="file"
              accept=".csv,.xlsx,.xls,.json"
              onChange={handleFileChange}
              className="hidden"
            />

            {file ? (
              <div className="space-y-2">
                <FileSpreadsheet className="w-10 h-10 text-emerald-400 mx-auto" />
                <p className="font-semibold text-white text-sm">{file.name}</p>
                <p className="text-xs text-white/50">{(file.size / 1024).toFixed(1)} KB</p>
              </div>
            ) : (
              <div className="space-y-2">
                <Upload className="w-10 h-10 text-blue-400 mx-auto" />
                <p className="text-sm font-medium text-white">
                  Drag and drop file here, or <span className="text-blue-400 underline">browse</span>
                </p>
                <p className="text-xs text-white/40">CSV, XLSX, XLS up to 50MB</p>
              </div>
            )}
          </div>

          <div className="flex justify-end gap-3 pt-4 border-t border-white/10">
            <Button
              type="button"
              variant="outline"
              onClick={onClose}
              className="border-white/10 text-white"
            >
              Cancel
            </Button>
            <Button
              type="submit"
              disabled={!file || isProcessing}
              className="bg-blue-600 hover:bg-blue-500 text-white shadow-lg font-semibold"
            >
              {isProcessing ? 'Processing Dataset...' : 'Upload & Save Dataset'}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
};
