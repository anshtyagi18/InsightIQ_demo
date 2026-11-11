/**
 * Enhanced Dashboard Service with LangGraph Integration
 * 
 * Provides comprehensive dashboard generation capabilities with:
 * - LangGraph workflow integration
 * - Real-time workflow monitoring
 * - Data filtering insights
 * - Enhanced error handling
 * - Performance metrics tracking
 * - Checkpoint management
 */

import axios, { AxiosResponse, AxiosError } from 'axios';

// ===== TYPE DEFINITIONS =====

export interface LangGraphDashboardRequest {
  file_path: string;
  session_id?: string;
  user_requirements?: Record<string, any>;
  enable_ai_filtering?: boolean;
  enable_pivot_analysis?: boolean;
  workflow_config?: Record<string, any>;
}

export interface WorkflowStatus {
  workflow_id: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'paused' | 'cancelled';
  current_step: string;
  progress_percentage: number;
  estimated_completion?: string;
  metadata: Record<string, any>;
  last_updated: string;
}

export interface WorkflowResult {
  workflow_id: string;
  dashboard_config: Record<string, any>;
  metadata: Record<string, any>;
  quality_metrics: Record<string, any>;
  processing_time: number;
  completed_at: string;
}

export interface WorkflowCheckpoint {
  checkpoint_id: string;
  workflow_id: string;
  step_name: string;
  timestamp: string;
  state_data: Record<string, any>;
  checkpoint_hash: string;
  metadata: Record<string, any>;
}

export interface DashboardGenerationResponse {
  success: boolean;
  workflow_id: string;
  status: string;
  message: string;
  monitoring: {
    status_endpoint: string;
    results_endpoint: string;
    websocket_endpoint: string;
  };
  estimated_completion?: string;
  progress_percentage: number;
  current_step: string;
  started_at: string;
}

export interface ErrorDetails {
  error_id: string;
  error_type: string;
  severity: 'low' | 'medium' | 'high' | 'fatal';
  step: string;
  message: string;
  details: Record<string, any>;
  timestamp: string;
  recovery_options?: string[];
  auto_recoverable: boolean;
}

export interface ServiceError {
  type: 'network' | 'api' | 'validation' | 'workflow' | 'timeout' | 'unknown';
  message: string;
  details?: any;
  recoverable: boolean;
  retryable: boolean;
  workflow_id?: string;
}

// ===== ENHANCED DASHBOARD SERVICE =====

export class EnhancedDashboardService {
  private readonly baseURL: string;
  private readonly timeout: number;
  private statusUpdateCallbacks: Map<string, (status: WorkflowStatus) => void> = new Map();
  private pollingIntervals: Map<string, NodeJS.Timeout> = new Map();
  private readonly maxRetries: number = 3;
  private readonly retryDelay: number = 1000;

  constructor(
    baseURL: string = import.meta.env.VITE_API_BASE_URL || '',
    timeout: number = 300000 // 5 minutes for long-running workflows
  ) {
    this.baseURL = baseURL;
    this.timeout = timeout;
    
    // Configure axios defaults
    axios.defaults.timeout = this.timeout;
    axios.defaults.baseURL = this.baseURL;
    
    // Setup response interceptor for error handling
    this.setupAxiosInterceptors();
  }

  // ===== CORE DASHBOARD GENERATION =====

  /**
   * Generate a dashboard using LangGraph orchestrated workflow
   */
  async generateDashboardWithLangGraph(
    request: LangGraphDashboardRequest
  ): Promise<DashboardGenerationResponse> {
    try {
      console.log('🚀 Starting LangGraph dashboard generation:', request);
      
      const response = await this.makeRequestWithRetry<DashboardGenerationResponse>(
        'POST',
        '/api/v1/dashboard/generate-langgraph',
        request
      );

      console.log('✅ LangGraph workflow initiated:', response.data);
      
      // Start automatic status monitoring if successful
      if (response.data.success && response.data.workflow_id) {
        this.startStatusMonitoring(response.data.workflow_id);
      }

      return response.data;
      
    } catch (error) {
      const serviceError = this.handleError(error, 'generateDashboardWithLangGraph');
      console.error('❌ LangGraph dashboard generation failed:', serviceError);
      throw serviceError;
    }
  }

  // ===== WORKFLOW MONITORING =====

  /**
   * Get current workflow status
   */
  async getWorkflowStatus(workflowId: string): Promise<WorkflowStatus> {
    try {
      const response = await this.makeRequestWithRetry<WorkflowStatus>(
        'GET',
        `/api/v1/dashboard/workflow-status/${workflowId}`
      );

      console.log(`📊 Workflow ${workflowId} status:`, response.data);
      return response.data;
      
    } catch (error) {
      const serviceError = this.handleError(error, 'getWorkflowStatus', workflowId);
      console.error(`❌ Failed to get workflow status for ${workflowId}:`, serviceError);
      throw serviceError;
    }
  }

  /**
   * Get completed workflow results
   */
  async getWorkflowResults(workflowId: string): Promise<WorkflowResult> {
    try {
      const response = await this.makeRequestWithRetry<WorkflowResult>(
        'GET',
        `/api/v1/dashboard/workflow-results/${workflowId}`
      );

      console.log(`🎯 Workflow ${workflowId} results retrieved:`, response.data);
      return response.data;
      
    } catch (error) {
      const serviceError = this.handleError(error, 'getWorkflowResults', workflowId);
      console.error(`❌ Failed to get workflow results for ${workflowId}:`, serviceError);
      throw serviceError;
    }
  }

  /**
   * Resume a paused or failed workflow
   */
  async resumeWorkflow(
    workflowId: string, 
    checkpointId?: string
  ): Promise<{ success: boolean; workflow_id: string; current_status: string; current_step: string; message: string }> {
    try {
      console.log(`🔄 Resuming workflow ${workflowId} from checkpoint ${checkpointId || 'latest'}`);
      
      const response = await this.makeRequestWithRetry(
        'POST',
        `/api/v1/dashboard/workflow-resume/${workflowId}`,
        checkpointId ? { checkpoint_id: checkpointId } : {}
      );

      console.log(`✅ Workflow ${workflowId} resumed:`, response.data);
      
      // Restart status monitoring
      this.startStatusMonitoring(workflowId);
      
      return response.data;
      
    } catch (error) {
      const serviceError = this.handleError(error, 'resumeWorkflow', workflowId);
      console.error(`❌ Failed to resume workflow ${workflowId}:`, serviceError);
      throw serviceError;
    }
  }

  /**
   * List available checkpoints for a workflow
   */
  async listWorkflowCheckpoints(workflowId: string): Promise<WorkflowCheckpoint[]> {
    try {
      const response = await this.makeRequestWithRetry<{
        success: boolean;
        workflow_id: string;
        checkpoints: WorkflowCheckpoint[];
        checkpoint_count: number;
      }>('GET', `/api/v1/dashboard/workflow-checkpoints/${workflowId}`);

      console.log(`📋 Retrieved ${response.data.checkpoint_count} checkpoints for workflow ${workflowId}`);
      return response.data.checkpoints;
      
    } catch (error) {
      const serviceError = this.handleError(error, 'listWorkflowCheckpoints', workflowId);
      console.error(`❌ Failed to list checkpoints for workflow ${workflowId}:`, serviceError);
      throw serviceError;
    }
  }

  // ===== REAL-TIME STATUS MONITORING =====

  /**
   * Start automatic status monitoring for a workflow
   */
  startStatusMonitoring(
    workflowId: string,
    onStatusUpdate?: (status: WorkflowStatus) => void,
    pollInterval: number = 2000
  ): void {
    console.log(`🔍 Starting status monitoring for workflow ${workflowId}`);
    
    // Store callback if provided
    if (onStatusUpdate) {
      this.statusUpdateCallbacks.set(workflowId, onStatusUpdate);
    }

    // Clear any existing interval for this workflow
    this.stopStatusMonitoring(workflowId);

    // Start polling
    const intervalId = setInterval(async () => {
      try {
        const status = await this.getWorkflowStatus(workflowId);
        
        // Call update callback if registered
        const callback = this.statusUpdateCallbacks.get(workflowId);
        if (callback) {
          callback(status);
        }

        // Stop monitoring if workflow is completed or failed
        if (['completed', 'failed', 'cancelled'].includes(status.status)) {
          console.log(`⏹️ Stopping monitoring for workflow ${workflowId} - Status: ${status.status}`);
          this.stopStatusMonitoring(workflowId);
        }
        
      } catch (error) {
        console.error(`❌ Status monitoring error for workflow ${workflowId}:`, error);
        
        // Continue monitoring for recoverable errors, stop for fatal ones
        if (error instanceof Error && !this.isRecoverableError(error)) {
          this.stopStatusMonitoring(workflowId);
        }
      }
    }, pollInterval);

    this.pollingIntervals.set(workflowId, intervalId);
  }

  /**
   * Stop status monitoring for a workflow
   */
  stopStatusMonitoring(workflowId: string): void {
    const intervalId = this.pollingIntervals.get(workflowId);
    if (intervalId) {
      clearInterval(intervalId);
      this.pollingIntervals.delete(workflowId);
      this.statusUpdateCallbacks.delete(workflowId);
      console.log(`⏹️ Stopped status monitoring for workflow ${workflowId}`);
    }
  }

  /**
   * Stop all active monitoring
   */
  stopAllMonitoring(): void {
    console.log('⏹️ Stopping all workflow monitoring');
    this.pollingIntervals.forEach((intervalId, workflowId) => {
      clearInterval(intervalId);
      console.log(`⏹️ Stopped monitoring workflow ${workflowId}`);
    });
    this.pollingIntervals.clear();
    this.statusUpdateCallbacks.clear();
  }

  // ===== UTILITY METHODS =====

  /**
   * Wait for workflow completion with timeout
   */
  async waitForCompletion(
    workflowId: string,
    timeoutMs: number = 300000, // 5 minutes default
    onProgress?: (status: WorkflowStatus) => void
  ): Promise<WorkflowResult> {
    return new Promise((resolve, reject) => {
      let timeoutId: NodeJS.Timeout;
      
      // Set timeout
      timeoutId = setTimeout(() => {
        this.stopStatusMonitoring(workflowId);
        reject(new Error(`Workflow ${workflowId} timed out after ${timeoutMs}ms`));
      }, timeoutMs);

      // Start monitoring with completion handler
      this.startStatusMonitoring(workflowId, async (status: WorkflowStatus) => {
        // Call progress callback if provided
        if (onProgress) {
          onProgress(status);
        }

        // Check for completion
        if (status.status === 'completed') {
          clearTimeout(timeoutId);
          try {
            const results = await this.getWorkflowResults(workflowId);
            resolve(results);
          } catch (error) {
            reject(error);
          }
        } else if (status.status === 'failed') {
          clearTimeout(timeoutId);
          reject(new Error(`Workflow ${workflowId} failed: ${status.metadata?.error || 'Unknown error'}`));
        } else if (status.status === 'cancelled') {
          clearTimeout(timeoutId);
          reject(new Error(`Workflow ${workflowId} was cancelled`));
        }
      });
    });
  }

  /**
   * Get workflow performance metrics
   */
  getPerformanceMetrics(workflowResult: WorkflowResult): {
    processing_time: number;
    data_quality_score: number;
    accuracy_metrics: Record<string, number>;
    efficiency_rating: string;
  } {
    const quality = workflowResult.quality_metrics;
    const processingTime = workflowResult.processing_time;
    
    // Extract key performance indicators
    const dataQualityScore = quality?.overall_accuracy_score || 0;
    const accuracyMetrics = {
      data_quality: quality?.data_quality_score || 0,
      processing_accuracy: quality?.processing_score || 0,
      output_quality: quality?.output_quality_score || 0
    };
    
    // Determine efficiency rating
    let efficiencyRating = 'excellent';
    if (processingTime > 60) efficiencyRating = 'good';
    if (processingTime > 120) efficiencyRating = 'fair';
    if (processingTime > 300) efficiencyRating = 'slow';
    
    return {
      processing_time: processingTime,
      data_quality_score: dataQualityScore,
      accuracy_metrics: accuracyMetrics,
      efficiency_rating: efficiencyRating
    };
  }

  // ===== ERROR HANDLING =====

  private setupAxiosInterceptors(): void {
    axios.interceptors.response.use(
      (response) => response,
      (error) => {
        console.error('🚨 Axios interceptor caught error:', error);
        return Promise.reject(error);
      }
    );
  }

  private async makeRequestWithRetry<T>(
    method: 'GET' | 'POST' | 'PUT' | 'DELETE',
    url: string,
    data?: any,
    retryCount: number = 0
  ): Promise<AxiosResponse<T>> {
    try {
      let response: AxiosResponse<T>;
      
      switch (method) {
        case 'GET':
          response = await axios.get<T>(url);
          break;
        case 'POST':
          response = await axios.post<T>(url, data);
          break;
        case 'PUT':
          response = await axios.put<T>(url, data);
          break;
        case 'DELETE':
          response = await axios.delete<T>(url);
          break;
        default:
          throw new Error(`Unsupported HTTP method: ${method}`);
      }
      
      return response;
      
    } catch (error) {
      // Retry logic for recoverable errors
      if (retryCount < this.maxRetries && this.isRetryableError(error)) {
        console.warn(`⚠️ Request failed, retrying (${retryCount + 1}/${this.maxRetries}):`, error);
        await this.delay(this.retryDelay * Math.pow(2, retryCount)); // Exponential backoff
        return this.makeRequestWithRetry<T>(method, url, data, retryCount + 1);
      }
      
      throw error;
    }
  }

  private handleError(error: any, operation: string, workflowId?: string): ServiceError {
    console.error(`🚨 Error in ${operation}:`, error);
    
    // Network errors
    if (error.code === 'ECONNABORTED' || error.message?.includes('timeout')) {
      return {
        type: 'timeout',
        message: `Request timeout during ${operation}`,
        details: error,
        recoverable: true,
        retryable: true,
        workflow_id: workflowId
      };
    }
    
    if (error.code === 'ECONNREFUSED' || error.code === 'ENETUNREACH') {
      return {
        type: 'network',
        message: `Network connection failed during ${operation}`,
        details: error,
        recoverable: true,
        retryable: true,
        workflow_id: workflowId
      };
    }
    
    // API errors
    if (error.response) {
      const status = error.response.status;
      const data = error.response.data;
      
      if (status >= 400 && status < 500) {
        return {
          type: 'api',
          message: data?.detail || `Client error (${status}) during ${operation}`,
          details: data,
          recoverable: status === 404 || status === 429, // Not found or rate limited
          retryable: status === 429, // Only retry rate limits
          workflow_id: workflowId
        };
      }
      
      if (status >= 500) {
        return {
          type: 'api',
          message: data?.detail || `Server error (${status}) during ${operation}`,
          details: data,
          recoverable: true,
          retryable: true,
          workflow_id: workflowId
        };
      }
    }
    
    // Validation errors
    if (error.message?.includes('validation') || error.message?.includes('invalid')) {
      return {
        type: 'validation',
        message: `Validation error during ${operation}: ${error.message}`,
        details: error,
        recoverable: false,
        retryable: false,
        workflow_id: workflowId
      };
    }
    
    // Workflow-specific errors
    if (workflowId && (error.message?.includes('workflow') || error.message?.includes('checkpoint'))) {
      return {
        type: 'workflow',
        message: `Workflow error during ${operation}: ${error.message}`,
        details: error,
        recoverable: true,
        retryable: false, // Don't auto-retry workflow errors
        workflow_id: workflowId
      };
    }
    
    // Unknown errors
    return {
      type: 'unknown',
      message: `Unknown error during ${operation}: ${error.message || 'Unexpected error'}`,
      details: error,
      recoverable: false,
      retryable: false,
      workflow_id: workflowId
    };
  }

  private isRetryableError(error: any): boolean {
    // Network timeouts and connection issues
    if (error.code === 'ECONNABORTED' || error.code === 'ECONNREFUSED') {
      return true;
    }
    
    // Server errors (5xx)
    if (error.response?.status >= 500) {
      return true;
    }
    
    // Rate limiting (429)
    if (error.response?.status === 429) {
      return true;
    }
    
    return false;
  }

  private isRecoverableError(error: any): boolean {
    // Network errors are usually recoverable
    if (error.code === 'ECONNABORTED' || error.code === 'ECONNREFUSED') {
      return true;
    }
    
    // Server errors might be recoverable
    if (error.response?.status >= 500) {
      return true;
    }
    
    // Not found might be recoverable (resource might be created later)
    if (error.response?.status === 404) {
      return true;
    }
    
    return false;
  }

  private delay(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  // ===== CLEANUP =====

  /**
   * Cleanup service resources
   */
  destroy(): void {
    console.log('🧹 Cleaning up Enhanced Dashboard Service');
    this.stopAllMonitoring();
  }
}

// Export class for instantiation
export default EnhancedDashboardService;