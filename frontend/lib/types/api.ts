// 공통 API 타입 정의

// 페이지네이션 응답 타입
export interface PaginatedResponse<T> {
  results: T[];
  count: number;
  total_pages: number;
  current_page: number;
}

// API 에러 응답 타입
export interface ApiErrorResponse {
  error?: string;
  detail?: string;
  message?: string;
}

