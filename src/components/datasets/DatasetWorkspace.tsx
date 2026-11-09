import React, { useState, useMemo } from 'react';
import { SavedDataset, datasetStorage } from '@/services/dataset-storage.service';
import { 
  advancedCleanDataset, 
  AdvancedCleaningOptions, 
  DatasetProfile, 
  profileDataset 
} from '@/services/bi-engine';
import { 
  ArrowLeft, 
  Sliders, 
  Table, 
  History, 
  Sparkles, 
  CheckCircle2, 
  Trash2, 
  Play, 
  RefreshCw, 
  FileText, 
  Check, 
  AlertTriangle, 
  Filter, 
  Type, 
  Layers, 
  BarChart2, 
  Eye
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { toast } from 'sonner';

interface DatasetWorkspaceProps {
  dataset: SavedDataset;
  onBack: () => void;
  onPowerDashboard: (dataset: SavedDataset) => void;
  onUpdateDataset: (updated: SavedDataset) => void;
}

export const DatasetWorkspace: React.FC<DatasetWorkspaceProps> = ({
  dataset,
  onBack,
  onPowerDashboard,
  onUpdateDataset,
}) => {
  const [activeTab, setActiveTab] = useState<'overview' | 'cleaner' | 'grid' | 'history'>('cleaner');

  // Interactive Cleaning Options State
  const [droppedColumns, setDroppedColumns] = useState<string[]>([]);
  const [renamedColumns, setRenamedColumns] = useState<Record<string, string>>({});
  const [missingStrategy, setMissingStrategy] = useState<'median' | 'mean' | 'mode' | 'zero' | 'custom' | 'drop_row' | 'ffill' | 'bfill'>('median');
  const [customMissingValue, setCustomMissingValue] = useState<string>('N/A');
  const [removeDuplicates, setRemoveDuplicates] = useState<boolean>(true);
  const [selectedDuplicateKeys, setSelectedDuplicateKeys] = useState<string[]>([]);
  const [trimWhitespace, setTrimWhitespace] = useState<boolean>(true);
  const [stringCase, setStringCase] = useState<'none' | 'lowercase' | 'uppercase'>('none');
  const [typeCasts, setTypeCasts] = useState<Record<string, 'numeric' | 'categorical' | 'date' | 'boolean'>>({});

  // Search & Pagination for Grid
  const [gridSearch, setGridSearch] = useState<string>('');
  const [gridPage, setGridPage] = useState<number>(1);
  const pageSize = 15;

  // Compute live profile on current raw rows
  const profile = useMemo(() => {
    return profileDataset(dataset.rawRows);
  }, [dataset.rawRows]);

  // Compute live Pandas cleaning diff preview
  const cleaningOptions: AdvancedCleaningOptions = useMemo(() => {
    return {
      droppedColumns,
      renamedColumns,
      missingStrategy,
      customMissingValue,
      removeDuplicates,
      duplicateKeys: selectedDuplicateKeys,
      trimWhitespace,
      stringCase,
      typeCasts,
    };
  }, [
    droppedColumns, 
    renamedColumns, 
    missingStrategy, 
    customMissingValue, 
    removeDuplicates, 
    selectedDuplicateKeys, 
    trimWhitespace, 
    stringCase, 
    typeCasts
  ]);

  const cleaningResult = useMemo(() => {
    return advancedCleanDataset(dataset.rawRows, cleaningOptions);
  }, [dataset.rawRows, cleaningOptions]);

  // Handle Save Cleaned Data
  const handleApplyAndSave = async () => {
    try {
      const summaryMsg = cleaningResult.summaryText;
      const updated = await datasetStorage.updateDataset(
        dataset.id, 
        { cleanedRows: cleaningResult.cleanedData },
        { action: 'Pandas Cleaning Suite', details: summaryMsg }
      );

      if (updated) {
        onUpdateDataset(updated);
        toast.success('Cleaned dataset saved successfully!');
      }
    } catch (err) {
      toast.error('Failed to save cleaned dataset');
    }
  };

  // Toggle Column Drop
  const toggleDropColumn = (colName: string) => {
    if (droppedColumns.includes(colName)) {
      setDroppedColumns(droppedColumns.filter(c => c !== colName));
    } else {
      setDroppedColumns([...droppedColumns, colName]);
    }
  };

  // Handle Rename Column
  const handleRenameColumn = (original: string, newName: string) => {
    if (!newName || newName === original) {
      const next = { ...renamedColumns };
      delete next[original];
      setRenamedColumns(next);
    } else {
      setRenamedColumns({ ...renamedColumns, [original]: newName });
    }
  };

  // Toggle Duplicate Key
  const toggleDuplicateKey = (colName: string) => {
    if (selectedDuplicateKeys.includes(colName)) {
      setSelectedDuplicateKeys(selectedDuplicateKeys.filter(k => k !== colName));
    } else {
      setSelectedDuplicateKeys([...selectedDuplicateKeys, colName]);
    }
  };

  // Filtered rows for Grid view
  const filteredGridRows = useMemo(() => {
    const rows = cleaningResult.cleanedData;
    if (!gridSearch.trim()) return rows;
    const q = gridSearch.toLowerCase();
    return rows.filter(r => 
      Object.values(r).some(v => String(v).toLowerCase().includes(q))
    );
  }, [cleaningResult.cleanedData, gridSearch]);

  const totalGridPages = Math.ceil(filteredGridRows.length / pageSize) || 1;
  const paginatedGridRows = useMemo(() => {
    const start = (gridPage - 1) * pageSize;
    return filteredGridRows.slice(start, start + pageSize);
  }, [filteredGridRows, gridPage]);

  return (
    <div className="space-y-6">
      {/* Workspace Header */}
      <div className="bg-white/5 border border-white/10 rounded-2xl p-6 backdrop-blur-xl">
        <div className="flex flex-col lg:flex-row justify-between items-start lg:items-center gap-4">
          <div className="flex items-center gap-4">
            <Button
              variant="outline"
              size="sm"
              onClick={onBack}
              className="border-white/20 hover:bg-white/10 text-white"
            >
              <ArrowLeft className="w-4 h-4 mr-2" /> Back
            </Button>

            <div>
              <div className="flex items-center gap-3">
                <h1 className="text-2xl font-bold text-white">{dataset.name}</h1>
                <Badge className="bg-blue-500/20 text-blue-300 border-blue-500/30">
                  {dataset.filename}
                </Badge>
              </div>
              <p className="text-xs text-white/60 mt-1">
                Raw: {dataset.rowCount} rows × {dataset.columnCount} cols | Cleaned: {cleaningResult.rowsAfter} rows × {cleaningResult.colsAfter} cols
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3 w-full lg:w-auto">
            <Button
              onClick={handleApplyAndSave}
              className="bg-emerald-600 hover:bg-emerald-500 text-white shadow-lg"
            >
              <Check className="w-4 h-4 mr-2" /> Apply & Save
            </Button>

            <Button
              onClick={() => onPowerDashboard(dataset)}
              className="bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white shadow-lg"
            >
              <Play className="w-4 h-4 mr-2 fill-current" /> Open in Dashboard
            </Button>
          </div>
        </div>

        {/* Tab Selection */}
        <div className="flex items-center gap-2 border-t border-white/10 pt-4 mt-6 overflow-x-auto">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setActiveTab('cleaner')}
            className={`text-sm rounded-lg ${
              activeTab === 'cleaner' 
                ? 'bg-blue-600 text-white font-semibold' 
                : 'text-white/60 hover:text-white hover:bg-white/5'
            }`}
          >
            <Sliders className="w-4 h-4 mr-2" /> Cleaning Suite
          </Button>

          <Button
            variant="ghost"
            size="sm"
            onClick={() => setActiveTab('overview')}
            className={`text-sm rounded-lg ${
              activeTab === 'overview' 
                ? 'bg-blue-600 text-white font-semibold' 
                : 'text-white/60 hover:text-white hover:bg-white/5'
            }`}
          >
            <BarChart2 className="w-4 h-4 mr-2" /> Column Profiler
          </Button>

          <Button
            variant="ghost"
            size="sm"
            onClick={() => setActiveTab('grid')}
            className={`text-sm rounded-lg ${
              activeTab === 'grid' 
                ? 'bg-blue-600 text-white font-semibold' 
                : 'text-white/60 hover:text-white hover:bg-white/5'
            }`}
          >
            <Table className="w-4 h-4 mr-2" /> Data Grid
          </Button>

          <Button
            variant="ghost"
            size="sm"
            onClick={() => setActiveTab('history')}
            className={`text-sm rounded-lg ${
              activeTab === 'history' 
                ? 'bg-blue-600 text-white font-semibold' 
                : 'text-white/60 hover:text-white hover:bg-white/5'
            }`}
          >
            <History className="w-4 h-4 mr-2" /> Cleaning Log
          </Button>
        </div>
      </div>

      {/* TAB 1: PANDAS DATA CLEANING SUITE */}
      {activeTab === 'cleaner' && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Cleaning Controls (Left 2 Columns) */}
          <div className="lg:col-span-2 space-y-6">
            {/* 1. Columns Management */}
            <div className="glass-card p-6 rounded-2xl border border-white/10">
              <h3 className="text-base font-bold text-white mb-4 flex items-center gap-2">
                <Layers className="w-4 h-4 text-blue-400" /> Column Selector & Renaming
              </h3>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-3 max-h-60 overflow-y-auto pr-2">
                {profile.columns.map(col => {
                  const isDropped = droppedColumns.includes(col.name);
                  return (
                    <div
                      key={col.name}
                      className={`flex items-center justify-between p-3 rounded-xl border transition-all ${
                        isDropped 
                          ? 'bg-red-500/10 border-red-500/30 opacity-60' 
                          : 'bg-white/5 border-white/10 hover:border-white/20'
                      }`}
                    >
                      <div className="flex items-center gap-3">
                        <input
                          type="checkbox"
                          checked={!isDropped}
                          onChange={() => toggleDropColumn(col.name)}
                          className="rounded border-white/30 text-blue-600 focus:ring-blue-500 bg-black/40"
                        />
                        <div>
                          <p className="text-sm font-semibold text-white">{col.name}</p>
                          <span className="text-xs text-white/50">{col.type} • {col.nullPercentage}% null</span>
                        </div>
                      </div>

                      <Input
                        placeholder="Rename..."
                        defaultValue={renamedColumns[col.name] || ''}
                        onBlur={(e) => handleRenameColumn(col.name, e.target.value)}
                        className="w-28 h-8 text-xs bg-black/30 border-white/10 text-white"
                        disabled={isDropped}
                      />
                    </div>
                  );
                })}
              </div>
            </div>

            {/* 2. Missing Data & Duplicates */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Missing Values */}
              <div className="glass-card p-6 rounded-2xl border border-white/10">
                <h3 className="text-base font-bold text-white mb-4 flex items-center gap-2">
                  <Filter className="w-4 h-4 text-indigo-400" /> Missing Values Strategy
                </h3>

                <div className="space-y-4">
                  <div>
                    <Label className="text-xs text-white/70 mb-1 block">Global Strategy</Label>
                    <select
                      value={missingStrategy}
                      onChange={(e: any) => setMissingStrategy(e.target.value)}
                      className="w-full bg-black/40 border border-white/10 rounded-lg p-2.5 text-sm text-white focus:outline-none focus:border-blue-500"
                    >
                      <option value="median">Fill Numeric with Median / Mode for Text</option>
                      <option value="mean">Fill Numeric with Mean / Mode for Text</option>
                      <option value="mode">Fill All with Column Mode</option>
                      <option value="zero">Fill Missing with Zero (0)</option>
                      <option value="custom">Fill Missing with Custom Text</option>
                      <option value="drop_row">Drop Rows with Missing Values</option>
                      <option value="ffill">Forward Fill (ffill)</option>
                      <option value="bfill">Backward Fill (bfill)</option>
                    </select>
                  </div>

                  {missingStrategy === 'custom' && (
                    <div>
                      <Label className="text-xs text-white/70 mb-1 block">Custom Placeholder Text</Label>
                      <Input
                        value={customMissingValue}
                        onChange={(e) => setCustomMissingValue(e.target.value)}
                        className="bg-black/40 border-white/10 text-white"
                        placeholder="e.g. Unknown"
                      />
                    </div>
                  )}
                </div>
              </div>

              {/* Duplicate Rows */}
              <div className="glass-card p-6 rounded-2xl border border-white/10">
                <h3 className="text-base font-bold text-white mb-4 flex items-center gap-2">
                  <RefreshCw className="w-4 h-4 text-teal-400" /> Deduplication Controls
                </h3>

                <div className="space-y-4">
                  <div className="flex items-center justify-between p-3 bg-white/5 rounded-xl border border-white/10">
                    <div>
                      <p className="text-sm font-semibold text-white">Remove Duplicates</p>
                      <p className="text-xs text-white/50">Auto-detect identical rows</p>
                    </div>
                    <input
                      type="checkbox"
                      checked={removeDuplicates}
                      onChange={(e) => setRemoveDuplicates(e.target.checked)}
                      className="rounded border-white/30 text-blue-600 focus:ring-blue-500 bg-black/40 w-5 h-5"
                    />
                  </div>

                  {removeDuplicates && (
                    <div>
                      <Label className="text-xs text-white/70 mb-2 block">Deduplicate on Specific Key Columns (Optional)</Label>
                      <div className="flex flex-wrap gap-2 max-h-28 overflow-y-auto">
                        {profile.columns.map(c => {
                          const isSelected = selectedDuplicateKeys.includes(c.name);
                          return (
                            <button
                              key={c.name}
                              type="button"
                              onClick={() => toggleDuplicateKey(c.name)}
                              className={`text-xs px-2.5 py-1 rounded-lg border transition-all ${
                                isSelected 
                                  ? 'bg-blue-600 border-blue-500 text-white font-semibold' 
                                  : 'bg-white/5 border-white/10 text-white/60 hover:text-white'
                              }`}
                            >
                              {c.name}
                            </button>
                          );
                        })}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </div>

            {/* 3. Text & Type Conversion */}
            <div className="glass-card p-6 rounded-2xl border border-white/10">
              <h3 className="text-base font-bold text-white mb-4 flex items-center gap-2">
                <Type className="w-4 h-4 text-purple-400" /> String Sanitization & Type Conversion
              </h3>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="flex items-center justify-between p-3 bg-white/5 rounded-xl border border-white/10">
                  <div>
                    <p className="text-sm font-semibold text-white">Trim Whitespace</p>
                    <p className="text-xs text-white/50">Remove leading & trailing spaces</p>
                  </div>
                  <input
                    type="checkbox"
                    checked={trimWhitespace}
                    onChange={(e) => setTrimWhitespace(e.target.checked)}
                    className="rounded border-white/30 text-blue-600 focus:ring-blue-500 bg-black/40 w-5 h-5"
                  />
                </div>

                <div>
                  <Label className="text-xs text-white/70 mb-1 block">Text Case Transformation</Label>
                  <select
                    value={stringCase}
                    onChange={(e: any) => setStringCase(e.target.value)}
                    className="w-full bg-black/40 border border-white/10 rounded-lg p-2.5 text-sm text-white focus:outline-none focus:border-blue-500"
                  >
                    <option value="none">Preserve Original Case</option>
                    <option value="lowercase">Force Lowercase (abc)</option>
                    <option value="uppercase">Force Uppercase (ABC)</option>
                  </select>
                </div>
              </div>
            </div>
          </div>

          {/* Right Column: Live Diff & Summary */}
          <div className="space-y-6">
            <div className="glass-card p-6 rounded-2xl border border-blue-500/30 bg-blue-500/5">
              <h3 className="text-base font-bold text-white mb-4 flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-blue-400" /> Cleaning Summary Preview
              </h3>

              <div className="grid grid-cols-2 gap-3 mb-4">
                <div className="p-3 bg-black/30 rounded-xl text-center">
                  <p className="text-xs text-white/50">Rows</p>
                  <p className="text-lg font-bold text-white">
                    {cleaningResult.rowsBefore} → <span className="text-emerald-400">{cleaningResult.rowsAfter}</span>
                  </p>
                </div>
                <div className="p-3 bg-black/30 rounded-xl text-center">
                  <p className="text-xs text-white/50">Columns</p>
                  <p className="text-lg font-bold text-white">
                    {cleaningResult.colsBefore} → <span className="text-emerald-400">{cleaningResult.colsAfter}</span>
                  </p>
                </div>
              </div>

              <div className="p-3 bg-black/40 rounded-xl border border-white/10 text-xs text-white/80 space-y-2 mb-4">
                <p className="font-semibold text-blue-300">Operations Applied:</p>
                {cleaningResult.changesLog.length === 0 ? (
                  <p className="text-white/50 italic">No modifications selected.</p>
                ) : (
                  <ul className="list-disc list-inside space-y-1">
                    {cleaningResult.changesLog.map((log, idx) => (
                      <li key={idx} className="text-white/70">{log}</li>
                    ))}
                  </ul>
                )}
              </div>

              <Button
                onClick={handleApplyAndSave}
                className="w-full bg-emerald-600 hover:bg-emerald-500 text-white font-semibold shadow-lg"
              >
                <Check className="w-4 h-4 mr-2" /> Save Cleaned Dataset
              </Button>
            </div>

            {/* Live Sample Table Preview */}
            <div className="glass-card p-6 rounded-2xl border border-white/10">
              <h4 className="text-sm font-bold text-white mb-3 flex items-center gap-2">
                <Eye className="w-4 h-4 text-indigo-400" /> Cleaned Sample Preview (First 5 Rows)
              </h4>

              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs border-collapse">
                  <thead>
                    <tr className="border-b border-white/10 text-white/50">
                      {cleaningResult.profile.columns.slice(0, 4).map(c => (
                        <th key={c.name} className="py-2 px-2 font-medium">{c.name}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-white/5">
                    {cleaningResult.cleanedData.slice(0, 5).map((r, i) => (
                      <tr key={i} className="hover:bg-white/5">
                        {cleaningResult.profile.columns.slice(0, 4).map(c => (
                          <td key={c.name} className="py-2 px-2 text-white/80 truncate max-w-[100px]">
                            {String(r[c.name] ?? '')}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* TAB 2: COLUMN PROFILER */}
      {activeTab === 'overview' && (
        <div className="glass-card p-6 rounded-2xl border border-white/10">
          <h3 className="text-lg font-bold text-white mb-4">Detailed Column Analysis</h3>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm border-collapse">
              <thead>
                <tr className="border-b border-white/10 text-white/60">
                  <th className="py-3 px-4">Column Name</th>
                  <th className="py-3 px-4">Inferred Type</th>
                  <th className="py-3 px-4">Missing</th>
                  <th className="py-3 px-4">Unique</th>
                  <th className="py-3 px-4">Min / Max / Mean</th>
                  <th className="py-3 px-4">Sample Values</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/10">
                {profile.columns.map(col => (
                  <tr key={col.name} className="hover:bg-white/5">
                    <td className="py-3 px-4 font-semibold text-white">{col.name}</td>
                    <td className="py-3 px-4">
                      <Badge variant="outline" className="text-blue-300 border-blue-500/30">
                        {col.type}
                      </Badge>
                    </td>
                    <td className="py-3 px-4 text-white/80">
                      {col.nullCount} ({col.nullPercentage}%)
                    </td>
                    <td className="py-3 px-4 text-white/80">{col.uniqueCount}</td>
                    <td className="py-3 px-4 text-white/80 text-xs">
                      {col.type === 'numeric' ? (
                        <span>Min: {col.min} | Max: {col.max} | Avg: {col.mean}</span>
                      ) : (
                        <span className="text-white/40">N/A</span>
                      )}
                    </td>
                    <td className="py-3 px-4 text-white/60 text-xs truncate max-w-xs">
                      {col.sampleValues.join(', ')}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* TAB 3: DATA GRID */}
      {activeTab === 'grid' && (
        <div className="glass-card p-6 rounded-2xl border border-white/10 space-y-4">
          <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
            <Input
              placeholder="Search table rows..."
              value={gridSearch}
              onChange={(e) => {
                setGridSearch(e.target.value);
                setGridPage(1);
              }}
              className="max-w-xs bg-black/40 border-white/10 text-white"
            />
            <p className="text-xs text-white/60">
              Showing {(gridPage - 1) * pageSize + 1} - {Math.min(gridPage * pageSize, filteredGridRows.length)} of {filteredGridRows.length} rows
            </p>
          </div>

          <div className="overflow-x-auto rounded-xl border border-white/10">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="bg-white/10 text-white border-b border-white/10">
                  {cleaningResult.profile.columns.map(c => (
                    <th key={c.name} className="py-3 px-3 font-semibold whitespace-nowrap">{c.name}</th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5">
                {paginatedGridRows.map((row, idx) => (
                  <tr key={idx} className="hover:bg-white/5">
                    {cleaningResult.profile.columns.map(c => (
                      <td key={c.name} className="py-2.5 px-3 text-white/80 whitespace-nowrap">
                        {String(row[c.name] ?? '')}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          <div className="flex items-center justify-between border-t border-white/10 pt-4">
            <Button
              size="sm"
              variant="outline"
              disabled={gridPage === 1}
              onClick={() => setGridPage(gridPage - 1)}
              className="border-white/10 text-white"
            >
              Previous
            </Button>
            <span className="text-xs text-white/60">Page {gridPage} of {totalGridPages}</span>
            <Button
              size="sm"
              variant="outline"
              disabled={gridPage >= totalGridPages}
              onClick={() => setGridPage(gridPage + 1)}
              className="border-white/10 text-white"
            >
              Next
            </Button>
          </div>
        </div>
      )}

      {/* TAB 4: HISTORY */}
      {activeTab === 'history' && (
        <div className="glass-card p-6 rounded-2xl border border-white/10 space-y-4">
          <h3 className="text-base font-bold text-white flex items-center gap-2">
            <History className="w-4 h-4 text-blue-400" /> Dataset Audit Log & Cleaning History
          </h3>

          <div className="space-y-3">
            {dataset.cleaningHistory.map((item) => (
              <div key={item.id} className="p-4 bg-white/5 border border-white/10 rounded-xl flex items-start justify-between">
                <div>
                  <Badge className="bg-blue-500/20 text-blue-300 border-blue-500/30 mb-1">
                    {item.action}
                  </Badge>
                  <p className="text-sm text-white font-medium">{item.details}</p>
                </div>
                <span className="text-xs text-white/40">
                  {new Date(item.timestamp).toLocaleString()}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
