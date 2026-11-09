import { useState, useCallback } from 'react';

export interface ExportOptions {
  format: 'pdf' | 'png' | 'html';
  width?: number;
  height?: number;
  fullPage?: boolean;
}

export interface ExportStatus {
  isExporting: boolean;
  progress: number;
  error: string | null;
  exportId: string | null;
  downloadUrl: string | null;
}

export interface DashboardData {
  title: string;
  description?: string;
  kpis: any[];
  charts: any[];
  layout: any;
  theme?: string;
}

const API_BASE_URL = '/api/v1';

export function useExport() {
  const [status, setStatus] = useState<ExportStatus>({
    isExporting: false,
    progress: 0,
    error: null,
    exportId: null,
    downloadUrl: null,
  });

  const exportDashboard = useCallback(async (
    dashboardData: DashboardData,
    options: ExportOptions
  ) => {
    try {
      setStatus({
        isExporting: true,
        progress: 10,
        error: null,
        exportId: null,
        downloadUrl: null,
      });

      // Prepare request payload
      const requestBody = {
        dashboard_data: dashboardData,
        format: options.format,
        options: {
          format: options.format,
          width: options.width || 1200,
          height: options.height || 800,
          full_page: options.fullPage ?? true,
          scale: 1.0,
          background: true,
          wait_for: "[data-charts-ready='true']",
          timeout: 30000,
          margin: {
            top: "1cm",
            right: "1cm", 
            bottom: "1cm",
            left: "1cm"
          }
        }
      };

      setStatus(prev => ({ ...prev, progress: 30 }));

      // Make API call
      const response = await fetch(`${API_BASE_URL}/export/dashboard`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include', // Include cookies for authentication
        body: JSON.stringify(requestBody),
      });

      setStatus(prev => ({ ...prev, progress: 60 }));

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: 'Export failed' }));
        throw new Error(errorData.detail || `Export failed with status ${response.status}`);
      }

      const result = await response.json();
      
      setStatus(prev => ({ ...prev, progress: 90 }));

      // Success
      setStatus({
        isExporting: false,
        progress: 100,
        error: null,
        exportId: result.export_id,
        downloadUrl: result.download_url,
      });

      // Trigger download
      if (result.download_url) {
        const downloadLink = document.createElement('a');
        downloadLink.href = `${API_BASE_URL}${result.download_url}`;
        downloadLink.download = `dashboard-${result.export_id}.${options.format}`;
        document.body.appendChild(downloadLink);
        downloadLink.click();
        document.body.removeChild(downloadLink);
      }

      return result;

    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Export failed';
      setStatus({
        isExporting: false,
        progress: 0,
        error: errorMessage,
        exportId: null,
        downloadUrl: null,
      });
      throw error;
    }
  }, []);

  const quickExport = useCallback(async (
    dashboardData: DashboardData,
    format: 'pdf' | 'png',
    options: Partial<ExportOptions> = {}
  ) => {
    try {
      setStatus({
        isExporting: true,
        progress: 20,
        error: null,
        exportId: null,
        downloadUrl: null,
      });

      const endpoint = format === 'pdf' ? '/export/quick-pdf' : '/export/quick-png';
      const params = new URLSearchParams({
        width: (options.width || 1200).toString(),
        height: (options.height || 800).toString(),
        ...(format === 'png' && { full_page: (options.fullPage ?? true).toString() })
      });

      setStatus(prev => ({ ...prev, progress: 50 }));

      const response = await fetch(`${API_BASE_URL}${endpoint}?${params}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify(dashboardData),
      });

      setStatus(prev => ({ ...prev, progress: 80 }));

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: 'Quick export failed' }));
        throw new Error(errorData.detail || `Quick export failed with status ${response.status}`);
      }

      const result = await response.json();

      setStatus({
        isExporting: false,
        progress: 100,
        error: null,
        exportId: result.export_id,
        downloadUrl: result.download_url,
      });

      // Trigger download
      if (result.download_url) {
        const downloadLink = document.createElement('a');
        downloadLink.href = `${API_BASE_URL}${result.download_url}`;
        downloadLink.download = `dashboard-quick-${result.export_id}.${format}`;
        document.body.appendChild(downloadLink);
        downloadLink.click();
        document.body.removeChild(downloadLink);
      }

      return result;

    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Quick export failed';
      setStatus({
        isExporting: false,
        progress: 0,
        error: errorMessage,
        exportId: null,
        downloadUrl: null,
      });
      throw error;
    }
  }, []);

  const checkExportPermissions = useCallback(async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/export/permissions`, {
        credentials: 'include',
      });
      
      if (!response.ok) {
        throw new Error('Failed to check permissions');
      }
      
      return await response.json();
    } catch (error) {
      console.error('Failed to check export permissions:', error);
      return { formats: [] }; // Default to no permissions
    }
  }, []);

  const clearStatus = useCallback(() => {
    setStatus({
      isExporting: false,
      progress: 0,
      error: null,
      exportId: null,
      downloadUrl: null,
    });
  }, []);

  return {
    status,
    exportDashboard,
    quickExport,
    checkExportPermissions,
    clearStatus,
  };
} 