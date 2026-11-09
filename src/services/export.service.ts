/**
 * Export Service for InsightIQ
 * Handles dashboard and data export functionality
 * Connects to /api/v1/export/* endpoints
 */

import { api } from './api';

export interface DashboardExportRequest {
  dashboard_config: Record<string, any>;
  export_format: 'pdf' | 'png' | 'html' | 'json';
  export_options?: {
    include_data?: boolean;
    high_resolution?: boolean;
    page_size?: 'A4' | 'A3' | 'letter' | 'custom';
    orientation?: 'portrait' | 'landscape';
    custom_dimensions?: {
      width: number;
      height: number;
    };
  };
  metadata?: {
    title?: string;
    description?: string;
    author?: string;
    company?: string;
  };
}

export interface ExportResponse {
  status: string;
  export_id: string;
  download_url: string;
  file_size: number;
  export_format: string;
  expires_at: string;
  metadata: {
    filename: string;
    generated_at: string;
    dashboard_id?: string;
  };
}

export interface ExportStatusResponse {
  status: 'pending' | 'processing' | 'completed' | 'failed';
  export_id: string;
  progress: number;
  estimated_completion?: string;
  error_message?: string;
  download_url?: string;
}

class ExportService {
  /**
   * Export dashboard in specified format
   */
  async exportDashboard(request: DashboardExportRequest): Promise<ExportResponse> {
    try {
      const response = await api.post<ExportResponse>('/api/v1/export/dashboard', request);
      return response;
    } catch (error) {
      console.error('Dashboard export failed:', error);
      throw new Error(`Failed to export dashboard: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  /**
   * Get export status by export ID
   */
  async getExportStatus(exportId: string): Promise<ExportStatusResponse> {
    try {
      const response = await api.get<ExportStatusResponse>(`/api/v1/export/status/${exportId}`);
      return response;
    } catch (error) {
      console.error('Export status retrieval failed:', error);
      throw new Error(`Failed to get export status: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  /**
   * Download exported file
   */
  async downloadExport(exportId: string, filename?: string): Promise<Blob> {
    try {
      const response = await api.get(`/api/v1/export/download/${exportId}`, {
        responseType: 'blob'
      });
      
      return response as Blob;
    } catch (error) {
      console.error('Export download failed:', error);
      throw new Error(`Failed to download export: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  /**
   * Trigger browser download for exported file
   */
  async triggerDownload(exportId: string, filename: string): Promise<void> {
    try {
      const blob = await this.downloadExport(exportId);
      
      // Create download link
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      
      // Cleanup
      window.URL.revokeObjectURL(url);
      document.body.removeChild(link);
    } catch (error) {
      console.error('Download trigger failed:', error);
      throw new Error(`Failed to trigger download: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  /**
   * Get available export formats and their capabilities
   */
  getExportFormats(): {
    format: string;
    name: string;
    description: string;
    features: string[];
    file_extension: string;
  }[] {
    return [
      {
        format: 'pdf',
        name: 'PDF Document',
        description: 'High-quality PDF suitable for printing and sharing',
        features: ['Vector graphics', 'Searchable text', 'Print-ready'],
        file_extension: '.pdf'
      },
      {
        format: 'png',
        name: 'PNG Image',
        description: 'High-resolution image format',
        features: ['Lossless compression', 'Transparent background', 'High DPI'],
        file_extension: '.png'
      },
      {
        format: 'html',
        name: 'Interactive HTML',
        description: 'Fully interactive web dashboard',
        features: ['Interactive charts', 'Responsive layout', 'Real-time updates'],
        file_extension: '.html'
      },
      {
        format: 'json',
        name: 'JSON Data',
        description: 'Dashboard configuration and data in JSON format',
        features: ['Machine-readable', 'API integration', 'Data export'],
        file_extension: '.json'
      }
    ];
  }

  /**
   * Validate export request before submission
   */
  validateExportRequest(request: DashboardExportRequest): { isValid: boolean; errors: string[] } {
    const errors: string[] = [];
    
    // Check required fields
    if (!request.dashboard_config) {
      errors.push('Dashboard configuration is required');
    }
    
    if (!request.export_format) {
      errors.push('Export format is required');
    }
    
    // Validate export format
    const validFormats = ['pdf', 'png', 'html', 'json'];
    if (request.export_format && !validFormats.includes(request.export_format)) {
      errors.push(`Invalid export format. Supported formats: ${validFormats.join(', ')}`);
    }
    
    // Validate custom dimensions if provided
    if (request.export_options?.page_size === 'custom') {
      const dimensions = request.export_options.custom_dimensions;
      if (!dimensions || !dimensions.width || !dimensions.height) {
        errors.push('Custom dimensions (width and height) are required for custom page size');
      }
      
      if (dimensions && (dimensions.width < 100 || dimensions.height < 100)) {
        errors.push('Custom dimensions must be at least 100x100 pixels');
      }
    }
    
    return {
      isValid: errors.length === 0,
      errors
    };
  }
}

// Export singleton instance
export const exportService = new ExportService();
export default exportService; 