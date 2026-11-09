/**
 * Services index for InsightIQ
 * Central export point for all services
 */

// Core API service
export { api, apiRequest, healthCheck } from './api';

// Feature-specific services
export { dashboardService } from './dashboard.service';
export { EnhancedDashboardService } from './enhanced-dashboard.service';
export { analyticsService, AnalyticsService } from './analytics.service';
export { agentsService } from './agents';
export { uploadService } from './upload.service';
export { exportService } from './export.service';
export { webSocketService } from './websocket.service';

// Legacy services (to be phased out)

// Types from services
export type {
  DashboardGenerationRequest,
  ChartRecommendationRequest,
  KPICalculationRequest,
  DashboardConfig,
  ChartConfig,
  KPIConfig,
  LayoutTemplate,
  ThemeConfig,
} from './dashboard.service';

export type {
  LangGraphDashboardRequest,
  WorkflowStatus,
  WorkflowResult,
  WorkflowCheckpoint,
  DashboardGenerationResponse,
  ErrorDetails,
  ServiceError,
} from './enhanced-dashboard.service';

export type {
  AgentStatusResponse,
  FileAnalysisRequest,
  FileAnalysisResponse,
  DataProcessingRequest,
  DataProcessingResponse,
  AgentHealthCheck,
} from './agents';

export type {
  FileUploadResponse,
  FileValidationRequest,
  FileValidationResponse,
  UploadStatusResponse,
} from './upload.service';

export type {
  DashboardExportRequest,
  ExportResponse,
  ExportStatusResponse,
} from './export.service';

export type {
  WebSocketMessage,
  WebSocketConfig,
  ConnectionStatus,
} from './websocket.service'; 