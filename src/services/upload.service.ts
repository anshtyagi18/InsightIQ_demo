/**
 * Upload Service for InsightIQ
 * Handles file uploads, validation, and upload status monitoring
 * Connects to /api/v1/files/* endpoints
 */

import { api } from './api';
import { parseDatasetFile } from './bi-engine';

export interface CleaningAction {
  category: string;
  type: string;
  description: string;
  column?: string;
  count: number;
  sample_before?: any;
  sample_after?: any;
}

export interface CleaningIssue {
  type: string;
  severity: string;
  message: string;
  column?: string;
  affected_count: number;
}

export interface GeminiAssistedActions {
  assisted: boolean;
  model?: string;
  columns_removed: Array<{
    column: string;
    reason: string;
    redundancy_type: string;
  }>;
  columns_added: Array<{
    column: string;
    formula?: string;
    rationale?: string;
    source_columns?: string[];
  }>;
  messy_rows_purged: Array<{
    column: string;
    criteria: string;
    count: number;
    reason: string;
  }>;
}

export interface CleaningReport {
  cleanliness_score_before: number;
  cleanliness_score_after: number;
  summary: string;
  actions_taken: CleaningAction[];
  issues_detected: CleaningIssue[];
  rows_before: number;
  rows_after: number;
  cols_before: number;
  cols_after: number;
  gemini_assisted_actions?: GeminiAssistedActions;
}

export interface FileUploadResponse {
  status: string;
  message: string;
  session_id: string;
  file_info: {
    filename: string;
    size_bytes: number;
    size_mb: number;
    content_type: string;
    extension: string;
    upload_time: string;
  };
  storage?: {
    storage_type?: string;
    file_path: string;
    relative_path?: string;
    stored_filename?: string;
    original_filename: string;
    content_type?: string;
    size_bytes?: number;
    file_hash?: string;
    upload_time?: string;
    access_url?: string;
    metadata?: Record<string, any>;
    backup_preserved?: boolean;
  };
  preview?: {
    rows: Record<string, any>[];
    columns: string[];
    total_rows: number;
    preview_rows: number;
  };
  cleaning_report?: CleaningReport;
  cleaned_preview?: Record<string, any>[];
  cleaned_data?: Record<string, any>[];
  preview_before?: Record<string, any>[];
  preview_after?: Record<string, any>[];
  columns_profile?: Array<{
    name: string;
    original_name: string;
    type: string;
    null_count: number;
    null_percentage: number;
    unique_count: number;
    sample_values: any[];
    min?: number;
    max?: number;
    mean?: number;
    median?: number;
    sum?: number;
  }>;
  is_analytics_ready?: boolean;
  storage_error?: string;
  preview_error?: string;
}

export interface FileValidationRequest {
  file_info: {
    filename: string;
    size: number;
    type: string;
  };
}

export interface FileValidationResponse {
  status: string;
  is_valid: boolean;
  file_format: string;
  estimated_size: number;
  validation_errors?: string[];
  supported_formats: string[];
  max_file_size: number;
}

export interface UploadStatusResponse {
  status: string;
  file_id: string;
  upload_progress: number;
  processing_progress: number;
  current_stage: string;
  estimated_completion: string;
  error_message?: string;
}

class UploadService {
  /**
   * Upload a file to the backend
   */
  async uploadFile(file: File, options?: { 
    onProgress?: (progress: number) => void;
    sessionId?: string;
    includePreview?: boolean;
    previewRows?: number;
    storeFile?: boolean;
  }): Promise<FileUploadResponse> {
    try {
      const formData = new FormData();
      formData.append('file', file);

      // Build query parameters
      const params = new URLSearchParams();
      if (options?.includePreview !== undefined) {
        params.append('include_preview', options.includePreview.toString());
      }
      if (options?.previewRows !== undefined) {
        params.append('preview_rows', options.previewRows.toString());
      }
      if (options?.storeFile !== undefined) {
        params.append('store_file', options.storeFile.toString());
      }

      // Prepare headers
      const headers: Record<string, string> = {
        'Content-Type': 'multipart/form-data',
      };
      
      if (options?.sessionId) {
        headers['X-Session-ID'] = options.sessionId;
      }

      const url = `/api/v1/files/upload${params.toString() ? '?' + params.toString() : ''}`;

      const response = await api.post<FileUploadResponse>(
        url,
        formData,
        {
          headers,
          onUploadProgress: (progressEvent) => {
            if (options?.onProgress && progressEvent.total) {
              const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total);
              options.onProgress(progress);
            }
          },
        }
      );
      
      return response;
    } catch (error) {
      console.warn('⚠️ File upload API endpoint offline. Parsing file locally:', error);
      if (options?.onProgress) options.onProgress(100);
      const parsed = await parseDatasetFile(file);
      const cols = parsed.data.length > 0 ? Object.keys(parsed.data[0]) : [];
      return {
        status: 'success',
        message: 'File uploaded and parsed locally',
        session_id: options?.sessionId || `local_sess_${Date.now()}`,
        file_info: {
          filename: file.name,
          size_bytes: file.size,
          size_mb: Number((file.size / (1024 * 1024)).toFixed(2)),
          content_type: file.type || 'text/csv',
          extension: file.name.split('.').pop() || 'csv',
          upload_time: new Date().toISOString(),
        },
        preview: {
          rows: parsed.data.slice(0, options?.previewRows || 10),
          columns: cols,
          total_rows: parsed.data.length,
          preview_rows: Math.min(parsed.data.length, options?.previewRows || 10),
        }
      };
    }
  }

  /**
   * Preview a file without storing it
   */
  async previewFile(file: File, previewRows: number = 10): Promise<FileUploadResponse> {
    try {
      const formData = new FormData();
      formData.append('file', file);

      const params = new URLSearchParams({
        preview_rows: previewRows.toString()
      });

      const response = await api.post<FileUploadResponse>(
        `/api/v1/files/preview?${params.toString()}`,
        formData,
        {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        }
      );
      
      return response;
    } catch (error) {
      console.warn('⚠️ Preview API offline. Previewing locally:', error);
      const parsed = await parseDatasetFile(file);
      const cols = parsed.data.length > 0 ? Object.keys(parsed.data[0]) : [];
      return {
        status: 'success',
        message: 'File previewed locally',
        session_id: `local_sess_${Date.now()}`,
        file_info: {
          filename: file.name,
          size_bytes: file.size,
          size_mb: Number((file.size / (1024 * 1024)).toFixed(2)),
          content_type: file.type || 'text/csv',
          extension: file.name.split('.').pop() || 'csv',
          upload_time: new Date().toISOString(),
        },
        preview: {
          rows: parsed.data.slice(0, previewRows),
          columns: cols,
          total_rows: parsed.data.length,
          preview_rows: Math.min(parsed.data.length, previewRows),
        }
      };
    }
  }

  /**
   * Get supported file formats and limits
   */
  async getSupportedFormats(): Promise<{
    formats: string[];
    max_size: number;
    description: Record<string, string>;
  }> {
    try {
      const response = await api.get('/api/v1/files/formats');
      return response;
    } catch (error) {
      console.error('Failed to get supported formats:', error);
      // Return defaults as fallback
      return {
        formats: ['csv', 'xlsx', 'xls', 'json'],
        max_size: 10 * 1024 * 1024, // 10MB to match backend
        description: {
          csv: 'Comma-separated values',
          xlsx: 'Excel spreadsheet (modern)',
          xls: 'Excel spreadsheet (legacy)',
          json: 'JavaScript Object Notation'
        }
      };
    }
  }

  /**
   * Run intelligent Python Excel/CSV cleaning pipeline on a file
   */
  async cleanFile(file: File, options?: Record<string, any>): Promise<FileUploadResponse> {
    const formData = new FormData();
    formData.append('file', file);
    if (options) {
      formData.append('options', JSON.stringify(options));
    }

    const response = await api.post<FileUploadResponse>(
      '/api/v1/files/clean',
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      }
    );
    return response;
  }

  /**
   * Export cleaned dataset as a fresh .xlsx spreadsheet file
   * Original uploaded file remains completely unchanged
   */
  async exportCleanedFile(file: File, options?: Record<string, any>): Promise<Blob> {
    const formData = new FormData();
    formData.append('file', file);
    if (options) {
      formData.append('options', JSON.stringify(options));
    }

    const response = await fetch('/api/v1/files/export-cleaned', {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      throw new Error(`Export failed: ${response.statusText}`);
    }

    return response.blob();
  }

  /**
   * Download a file
   */
  async downloadFile(filePath: string): Promise<Blob> {
    try {
      const response = await api.get(`/api/v1/files/download/${filePath}`, {
        responseType: 'blob'
      });
      return response;
    } catch (error) {
      console.error('File download failed:', error);
      throw new Error(`Failed to download file: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  /**
   * Get file information
   */
  async getFileInfo(filePath: string): Promise<any> {
    try {
      const response = await api.get(`/api/v1/files/info/${filePath}`);
      return response;
    } catch (error) {
      console.error('Failed to get file info:', error);
      throw new Error(`Failed to get file info: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  /**
   * Request intelligent dataset interpretation from Gemini & Python/Pandas analytical backend.
   * Calculations and cleaning are performed entirely on the backend.
   * Gemini interprets pre-computed metrics to generate Executive Summary, Key Insights,
   * Executive Business Insights, and chart recommendations with rationale.
   * Backend generates the final charts.
   */
  async interpretDataset(
    data: Record<string, any>[],
    datasetName: string = 'Uploaded Dataset'
  ): Promise<any> {
    try {
      const response = await fetch('/api/v1/analytics/interpret', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          data,
          dataset_name: datasetName,
        }),
      });

      if (!response.ok) {
        throw new Error(`Interpretation request failed with status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Failed to interpret dataset with Gemini:', error);
      throw error;
    }
  }

  /**
   * Validate file client-side before upload
   */
  validateFileClientSide(file: File): { isValid: boolean; errors: string[] } {
    const errors: string[] = [];
    const maxSize = 10 * 1024 * 1024; // 10MB to match backend
    const supportedTypes = ['text/csv', 'application/vnd.ms-excel', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', 'application/json'];
    
    // Check file size
    if (file.size > maxSize) {
      errors.push(`File size (${Math.round(file.size / (1024 * 1024))}MB) exceeds maximum allowed size (10MB)`);
    }
    
    // Check file type
    if (!supportedTypes.includes(file.type) && !file.name.toLowerCase().match(/\.(csv|xlsx|xls|json)$/)) {
      errors.push('File type not supported. Please upload CSV, Excel, or JSON files.');
    }
    
    // Check file name
    if (file.name.length > 255) {
      errors.push('File name is too long (maximum 255 characters)');
    }
    
    return {
      isValid: errors.length === 0,
      errors
    };
  }
}

// Export singleton instance
export const uploadService = new UploadService();
export default uploadService; 