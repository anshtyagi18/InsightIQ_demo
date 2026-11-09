/**
 * Agents service for InsightIQ
 * Handles agent management, monitoring, and task execution
 * Connects to /api/v1/agents/* endpoints
 */

import { api } from './api';

export interface Agent {
  agentId: string;
  agentType: string;
  status: string;
  capabilities: string[];
  lastActivity: string;
  healthScore: number;
  config?: Record<string, any>;
}

export interface AgentHealth {
  agentId: string;
  healthStatus: {
    status: string;
    uptime: string;
    memoryUsage: string;
    cpuUsage: string;
  };
  lastChecked: string;
}

export interface AgentsListResponse {
  status: string;
  agents: Agent[];
  totalCount: number;
  activeCount: number;
}

export interface TaskRequest {
  taskType: string;
  parameters?: Record<string, any>;
  priority?: number;
  timeout?: number;
}

export interface TaskResponse {
  status: string;
  agentId: string;
  taskId: string;
  message: string;
  sentAt: string;
}

export interface AgentStatusResponse {
  status: string;
  agents_available: string[];
  configuration: {
    model: string;
    project_id: string;
    has_api_key: boolean;
    vertex_ai_enabled: boolean;
    is_production_ready: boolean;
  };
  last_updated: string;
}

export interface FileAnalysisRequest {
  file_info: {
    type: string;
    size: number;
    columns: string[];
    preview_rows: Record<string, any>[];
    total_rows: number;
    filename: string;
  };
}

export interface FileAnalysisResponse {
  status: string;
  file_analysis: {
    type: string;
    size_mb: number;
    columns_count: number;
    sample_rows: number;
  };
  processing_pipeline: string[];
  complexity_score: number;
  estimated_processing_time: number;
}

export interface DataProcessingRequest {
  data: Record<string, any>;
  pipeline: string[];
}

export interface DataProcessingResponse {
  status: string;
  pipeline_executed: string[];
  step_results: Record<string, any>;
  processed_data: Record<string, any>;
  recommendations: string[];
}

export interface AgentHealthCheck {
  status: string;
  timestamp: string;
  checks: {
    configuration: boolean;
    agents_importable: boolean;
    api_endpoints: string;
    orchestrator?: boolean;
    data_cleaner?: boolean;
  };
  error?: string;
}

class AgentsService {
  /**
   * Get all registered agents
   */
  async getAgents(): Promise<AgentsListResponse> {
    try {
      const response = await api.get<AgentsListResponse>('/agents');
      return response;
    } catch (error) {
      throw new Error('Failed to fetch agents');
    }
  }

  /**
   * Get specific agent information
   */
  async getAgent(agentId: string): Promise<Agent> {
    try {
      const response = await api.get<Agent>(`/agents/${agentId}`);
      return response;
    } catch (error) {
      throw new Error(`Failed to fetch agent ${agentId}`);
    }
  }

  /**
   * Register a new agent
   */
  async registerAgent(agentData: Partial<Agent>): Promise<any> {
    try {
      const response = await api.post('/agents/register', agentData);
      return response;
    } catch (error) {
      throw new Error('Failed to register agent');
    }
  }

  /**
   * Unregister an agent
   */
  async unregisterAgent(agentId: string): Promise<any> {
    try {
      const response = await api.delete(`/agents/${agentId}`);
      return response;
    } catch (error) {
      throw new Error(`Failed to unregister agent ${agentId}`);
    }
  }

  /**
   * Get agent health status
   */
  async getAgentHealth(agentId: string): Promise<AgentHealth> {
    try {
      const response = await api.get<AgentHealth>(`/agents/${agentId}/health`);
      return response;
    } catch (error) {
      throw new Error(`Failed to get health for agent ${agentId}`);
    }
  }

  /**
   * Send task to specific agent
   */
  async sendTaskToAgent(agentId: string, task: TaskRequest): Promise<TaskResponse> {
    try {
      const response = await api.post<TaskResponse>(`/agents/${agentId}/tasks`, task);
      return response;
    } catch (error) {
      throw new Error(`Failed to send task to agent ${agentId}`);
    }
  }

  /**
   * Get agent statistics
   */
  async getAgentStatistics(): Promise<any> {
    try {
      const response = await api.get('/agents/statistics');
      return response;
    } catch (error) {
      throw new Error('Failed to get agent statistics');
    }
  }

  /**
   * Get available agent types
   */
  async getAgentTypes(): Promise<any> {
    try {
      const response = await api.get('/agents/types/available');
      return response;
    } catch (error) {
      throw new Error('Failed to get agent types');
    }
  }

  /**
   * Get agent status and configuration
   */
  async getAgentStatus(): Promise<AgentStatusResponse> {
    try {
      const response = await api.get<AgentStatusResponse>('/api/v1/agents/status');
      return response;
    } catch (error) {
      throw new Error('Failed to fetch agent status');
    }
  }

  /**
   * Analyze uploaded file to determine processing requirements
   */
  async analyzeFile(request: FileAnalysisRequest): Promise<FileAnalysisResponse> {
    try {
      const response = await api.post<FileAnalysisResponse>('/api/v1/agents/analyze-file', request);
      return response;
    } catch (error) {
      throw new Error('Failed to analyze file');
    }
  }

  /**
   * Analyze uploaded file directly via form data
   */
  async analyzeUpload(file: File): Promise<FileAnalysisResponse> {
    try {
      const formData = new FormData();
      formData.append('file', file);
      
      const response = await api.post<FileAnalysisResponse>('/api/v1/agents/analyze-upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      return response;
    } catch (error) {
      throw new Error('Failed to analyze uploaded file');
    }
  }

  /**
   * Process data using agent pipeline
   */
  async processData(request: DataProcessingRequest): Promise<DataProcessingResponse> {
    try {
      const response = await api.post<DataProcessingResponse>('/api/v1/agents/process-data', request);
      return response;
    } catch (error) {
      throw new Error('Failed to process data');
    }
  }

  /**
   * Clean data using data cleaner agent
   */
  async cleanData(data: Record<string, any>): Promise<any> {
    try {
      const response = await api.post('/api/v1/agents/clean-data', data);
      return response;
    } catch (error) {
      throw new Error('Failed to clean data');
    }
  }

  /**
   * Generate dashboard plan based on analysis results
   */
  async generateDashboardPlan(analysisResults: Record<string, any>): Promise<any> {
    try {
      const response = await api.post('/api/v1/agents/generate-dashboard-plan', analysisResults);
      return response;
    } catch (error) {
      throw new Error('Failed to generate dashboard plan');
    }
  }

  /**
   * Agent health check
   */
  async healthCheck(): Promise<AgentHealthCheck> {
    try {
      const response = await api.get<AgentHealthCheck>('/api/v1/agents/health');
      return response;
    } catch (error) {
      throw new Error('Failed to check agent health');
    }
  }

  /**
   * Get agent information for dashboard integration
   */
  async getAgentInfo(): Promise<any> {
    try {
      // Note: This endpoint is in the dashboard router
      const response = await api.get('/api/v1/dashboard/agent-info');
      return response;
    } catch (error) {
      throw new Error('Failed to get agent info');
    }
  }
}

// Export singleton instance
export const agentsService = new AgentsService();
export default agentsService;