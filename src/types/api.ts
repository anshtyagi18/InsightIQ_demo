/**
 * Common API types for InsightIQ
 */

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  pageSize: number;
  totalPages: number;
}

export interface ApiErrorResponse {
  detail: string | { msg: string; type: string }[];
}

export interface SuccessResponse {
  status: string;
  message: string;
}

// Add other common types as needed