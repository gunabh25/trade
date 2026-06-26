export type ApiErrorCode =
  | 'VALIDATION_ERROR'
  | 'NOT_FOUND'
  | 'UNAUTHORIZED'
  | 'FORBIDDEN'
  | 'CONFLICT'
  | 'INTERNAL_ERROR'
  | 'SERVICE_UNAVAILABLE';

export interface ApiErrorDetail {
  field?: string;
  message: string;
}

export interface ApiErrorResponse {
  error: {
    code: ApiErrorCode;
    message: string;
    details?: ApiErrorDetail[];
    requestId?: string;
  };
}

export interface ApiSuccessResponse<T> {
  data: T;
  meta?: {
    requestId?: string;
  };
}

export type ApiResponse<T> = ApiSuccessResponse<T>;

export interface PaginationMeta {
  page: number;
  pageSize: number;
  total: number;
  totalPages: number;
}

export interface PaginatedResponse<T> {
  data: T[];
  meta: PaginationMeta & { requestId?: string };
}
