import React, { useState } from 'react';
import { 
  Download, 
  FileText, 
  FileSpreadsheet, 
  FileCode, 
  Loader2, 
  CheckCircle, 
  AlertCircle, 
  Printer, 
  Table
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { 
  DropdownMenu, 
  DropdownMenuContent, 
  DropdownMenuItem, 
  DropdownMenuTrigger,
  DropdownMenuSeparator,
  DropdownMenuLabel
} from '@/components/ui/dropdown-menu';
import { Badge } from '@/components/ui/badge';
import { 
  exportToCSV, 
  exportToExcel, 
  exportToPDFReport, 
  exportToJSON, 
  ComprehensiveReportData 
} from '@/services/export-utility';
import { profileDataset, generateForecast } from '@/services/bi-engine';

interface ExportComponentProps {
  data: Record<string, any>[];
  datasetName?: string;
  kpis?: any[];
  charts?: any[];
  insights?: any[];
  cleaningSummary?: any;
  className?: string;
  size?: 'default' | 'sm' | 'lg' | 'icon';
  variant?: 'default' | 'outline' | 'ghost';
}

export const ExportComponent: React.FC<ExportComponentProps> = ({
  data,
  datasetName = 'Dataset_Analysis',
  kpis = [],
  charts = [],
  insights = [],
  cleaningSummary,
  className = '',
  size = 'default',
  variant = 'outline'
}) => {
  const [isExporting, setIsExporting] = useState(false);
  const [exportSuccess, setExportSuccess] = useState<string | null>(null);

  const handleExportPDF = () => {
    setIsExporting(true);
    try {
      const profile = profileDataset(data);
      const forecast = generateForecast(data, profile);

      const reportData: ComprehensiveReportData = {
        datasetName,
        generatedAt: new Date().toLocaleDateString('en-US', {
          year: 'numeric',
          month: 'long',
          day: 'numeric',
          hour: '2-digit',
          minute: '2-digit'
        }),
        recordCount: data.length,
        profile,
        cleaningSummary,
        kpis,
        insights,
        charts,
        forecasting: forecast,
        data
      };

      exportToPDFReport(reportData);
      setExportSuccess('Business PDF Report opened for printing.');
    } catch (err) {
      console.error('PDF Export Error:', err);
      alert('Failed to generate PDF Report.');
    } finally {
      setIsExporting(false);
      setTimeout(() => setExportSuccess(null), 3000);
    }
  };

  const handleExportCSV = () => {
    setIsExporting(true);
    try {
      const cleanName = datasetName.toLowerCase().replace(/[^a-z0-9]/g, '_');
      exportToCSV(data, `${cleanName}_data.csv`);
      setExportSuccess('CSV dataset downloaded successfully.');
    } catch (err) {
      console.error('CSV Export Error:', err);
      alert('Failed to export CSV.');
    } finally {
      setIsExporting(false);
      setTimeout(() => setExportSuccess(null), 3000);
    }
  };

  const handleExportExcel = () => {
    setIsExporting(true);
    try {
      const cleanName = datasetName.toLowerCase().replace(/[^a-z0-9]/g, '_');
      exportToExcel(data, `${cleanName}_excel.csv`);
      setExportSuccess('Excel-compatible dataset downloaded.');
    } catch (err) {
      console.error('Excel Export Error:', err);
      alert('Failed to export Excel file.');
    } finally {
      setIsExporting(false);
      setTimeout(() => setExportSuccess(null), 3000);
    }
  };

  const handleExportJSON = () => {
    setIsExporting(true);
    try {
      const profile = profileDataset(data);
      const forecast = generateForecast(data, profile);

      const reportData: ComprehensiveReportData = {
        datasetName,
        generatedAt: new Date().toISOString(),
        recordCount: data.length,
        profile,
        cleaningSummary,
        kpis,
        insights,
        charts,
        forecasting: forecast,
        data
      };

      const cleanName = datasetName.toLowerCase().replace(/[^a-z0-9]/g, '_');
      exportToJSON(reportData, `${cleanName}_report.json`);
      setExportSuccess('JSON dashboard data exported.');
    } catch (err) {
      console.error('JSON Export Error:', err);
      alert('Failed to export JSON file.');
    } finally {
      setIsExporting(false);
      setTimeout(() => setExportSuccess(null), 3000);
    }
  };

  return (
    <div className={`relative inline-block ${className}`}>
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button 
            variant={variant} 
            size={size} 
            disabled={isExporting || !data || data.length === 0}
            className="bg-emerald-600 hover:bg-emerald-700 text-white font-semibold border-none shadow-lg shadow-emerald-600/25 transition-all"
          >
            {isExporting ? (
              <Loader2 className="w-4 h-4 mr-2 animate-spin" />
            ) : (
              <Download className="w-4 h-4 mr-2" />
            )}
            Export Analysis
          </Button>
        </DropdownMenuTrigger>
        
        <DropdownMenuContent align="end" className="w-72 bg-slate-900 border-slate-700 text-slate-100 shadow-2xl p-2">
          <DropdownMenuLabel className="text-xs font-semibold text-slate-400 uppercase tracking-wider px-2 py-1">
            Export Options & Reports
          </DropdownMenuLabel>
          <DropdownMenuSeparator className="bg-slate-800" />
          
          {/* Executive PDF Report */}
          <DropdownMenuItem 
            onClick={handleExportPDF}
            className="cursor-pointer hover:bg-slate-800 rounded-lg p-2 transition-colors focus:bg-slate-800"
          >
            <div className="flex items-start gap-3 w-full">
              <div className="p-2 bg-emerald-950 border border-emerald-800/60 rounded-lg text-emerald-400 mt-0.5">
                <Printer className="w-4 h-4" />
              </div>
              <div>
                <div className="font-semibold text-xs text-white flex items-center gap-1.5">
                  Executive PDF Report
                  <Badge variant="outline" className="text-[10px] border-emerald-500/40 text-emerald-300 py-0 px-1">
                    Print / PDF
                  </Badge>
                </div>
                <div className="text-[11px] text-slate-400 mt-0.5">
                  Full business report with KPIs, charts, cleaning log & trend forecast
                </div>
              </div>
            </div>
          </DropdownMenuItem>

          {/* Excel File */}
          <DropdownMenuItem 
            onClick={handleExportExcel}
            className="cursor-pointer hover:bg-slate-800 rounded-lg p-2 transition-colors focus:bg-slate-800"
          >
            <div className="flex items-start gap-3 w-full">
              <div className="p-2 bg-green-950 border border-green-800/60 rounded-lg text-green-400 mt-0.5">
                <FileSpreadsheet className="w-4 h-4" />
              </div>
              <div>
                <div className="font-semibold text-xs text-white">
                  Excel Spreadsheet (.csv)
                </div>
                <div className="text-[11px] text-slate-400 mt-0.5">
                  Excel-formatted dataset with UTF-8 encoding ({data.length} rows)
                </div>
              </div>
            </div>
          </DropdownMenuItem>

          {/* CSV File */}
          <DropdownMenuItem 
            onClick={handleExportCSV}
            className="cursor-pointer hover:bg-slate-800 rounded-lg p-2 transition-colors focus:bg-slate-800"
          >
            <div className="flex items-start gap-3 w-full">
              <div className="p-2 bg-cyan-950 border border-cyan-800/60 rounded-lg text-cyan-400 mt-0.5">
                <Table className="w-4 h-4" />
              </div>
              <div>
                <div className="font-semibold text-xs text-white">
                  Raw / Cleaned CSV File
                </div>
                <div className="text-[11px] text-slate-400 mt-0.5">
                  Standard comma-separated table data file
                </div>
              </div>
            </div>
          </DropdownMenuItem>

          {/* JSON File */}
          <DropdownMenuItem 
            onClick={handleExportJSON}
            className="cursor-pointer hover:bg-slate-800 rounded-lg p-2 transition-colors focus:bg-slate-800"
          >
            <div className="flex items-start gap-3 w-full">
              <div className="p-2 bg-purple-950 border border-purple-800/60 rounded-lg text-purple-400 mt-0.5">
                <FileCode className="w-4 h-4" />
              </div>
              <div>
                <div className="font-semibold text-xs text-white">
                  JSON Dashboard Metadata
                </div>
                <div className="text-[11px] text-slate-400 mt-0.5">
                  Machine-readable JSON schema with all analysis metrics
                </div>
              </div>
            </div>
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>

      {/* Success Notification Toast */}
      {exportSuccess && (
        <div className="absolute right-0 top-12 z-50 min-w-[280px]">
          <div className="bg-emerald-950 border border-emerald-500/50 text-emerald-200 text-xs p-3 rounded-xl shadow-2xl flex items-center gap-2">
            <CheckCircle className="w-4 h-4 text-emerald-400 shrink-0" />
            <span>{exportSuccess}</span>
          </div>
        </div>
      )}
    </div>
  );
};

export default ExportComponent;
