// 타입 정의는 lib/types에서 import
import type {
  SalesReport,
  Company,
  CompanyFilters,
  CompanyFinancialStatus,
  PaginatedResponse,
  CompanyStats,
  CompanySuggestion,
  CompanyUniqueProducts,
  CompanySalesData,
  CreateSalesReportData,
  UpdateSalesReportData,
  SalesReportParams,
} from '@/lib/types';

// 환경에 따른 API URL 설정
const getApiBaseUrl = () => {
  // 환경 변수 우선 사용
  if (typeof process !== 'undefined' && process.env.NEXT_PUBLIC_API_URL) {
    return process.env.NEXT_PUBLIC_API_URL;
  }
  
  // 브라우저 환경에서 현재 호스트 확인
  if (typeof window !== 'undefined') {
    const hostname = window.location.hostname;
    const port = window.location.port;
    
    // 개발 환경에서만 로그 출력
    if (process.env.NODE_ENV === 'development') {
      console.log('[API] Current hostname:', hostname, 'port:', port);
    }
    
    // localhost나 127.0.0.1인 경우
    if (hostname === 'localhost' || hostname === '127.0.0.1') {
      const apiUrl = 'http://127.0.0.1:8000/api';
      if (process.env.NODE_ENV === 'development') {
        console.log('[API] Using development API URL:', apiUrl);
      }
      return apiUrl;
    }
    
    // 172.28.x.x 같은 내부 IP인 경우 같은 호스트의 8000 포트 사용
    if (hostname.startsWith('172.28.') || hostname.startsWith('192.168.')) {
      const apiUrl = `http://${hostname}:8000/api`;
      if (process.env.NODE_ENV === 'development') {
        console.log('[API] Using internal network API URL:', apiUrl);
      }
      return apiUrl;
    }
    
    // 그 외의 경우 운영 환경으로 간주
    const apiUrl = 'http://192.168.99.37:8000/api';
    if (process.env.NODE_ENV === 'development') {
      console.log('[API] Using production API URL:', apiUrl);
    }
    return apiUrl;
  }
  
  // 서버 사이드 렌더링 시 개발 환경으로 간주
  return 'http://127.0.0.1:8000/api';
};

const API_BASE_URL = getApiBaseUrl();

// API URL을 다른 곳에서도 사용할 수 있도록 export
export { getApiBaseUrl };
export const API_URL = API_BASE_URL;

// 타입 재export (하위 호환성 유지)
export type {
  SalesReport,
  Company,
  CompanyFilters,
  CompanyFinancialStatus,
  PaginatedResponse,
};

// API 호출 헬퍼 함수
async function apiCall<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const token = (typeof window !== 'undefined') ? localStorage.getItem('access_token') : null;

  const method = (options.method || 'GET').toString().toUpperCase();
  const isFormData = typeof FormData !== 'undefined' && options.body instanceof FormData;

  const baseHeaders: Record<string, string> = {
    ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
  };

  // 시작 헤더 병합 (사용자 지정 헤더 우선)
  const optionsHeaders = options.headers as Record<string, string> | undefined;
  let headers: HeadersInit = {
    ...baseHeaders,
    ...(optionsHeaders || {}),
  };

  // Content-Type은 다음 조건에서만 자동 설정
  // - 메서드가 GET/HEAD가 아님
  // - body가 FormData가 아님 (브라우저가 자동 설정)
  // - 사용자가 이미 Content-Type을 지정하지 않음
  const headersRecord = headers as Record<string, string>;
  const hasContentType = !!(headersRecord['Content-Type'] || headersRecord['content-type']);
  if (method !== 'GET' && method !== 'HEAD' && !isFormData && !hasContentType) {
    headers = { 'Content-Type': 'application/json', ...headers };
  }

  const config: RequestInit = {
    ...options,
    headers,
  };

  const url = `${API_BASE_URL}${endpoint}`;
  // 개발 환경에서만 로그 출력
  if (process.env.NODE_ENV === 'development') {
    console.log('[API] Making request to:', url, 'Method:', method);
  }
  try {
    const response = await fetch(url, config);
    if (process.env.NODE_ENV === 'development') {
      console.log('[API] Response status:', response.status, 'for', endpoint);
    }
  
    if (!response.ok) {
      console.error(`[API] 호출 실패: ${response.status} - ${endpoint}`);
      console.error('[API] Response:', response);
      
      // 응답 본문을 읽어서 더 자세한 오류 정보 제공
      let errorData;
      let errorText = '';
      
      try {
        // 먼저 텍스트로 읽어보기
        errorText = await response.text();
        console.error('[API] Raw error response:', errorText);
        
        // JSON 파싱 시도
        errorData = JSON.parse(errorText);
        console.error('[API] Parsed error details:', errorData);
      } catch (parseError) {
        console.error('[API] JSON 파싱 실패, 원시 응답:', errorText);
        console.error('[API] Parse error:', parseError);
      }
      
      // JWT 토큰 만료 처리
      if (response.status === 401 && errorData && typeof errorData === 'object') {
        const errorObj = errorData as Record<string, unknown>;
        const errorDetail = (errorObj.detail || errorObj.error || '') as string;
        if (errorDetail.includes('Given token not valid for any token type') || 
            errorDetail.includes('token_not_valid') ||
            errorDetail.includes('Token is invalid or expired')) {
          console.log('[API] JWT 토큰 만료 감지, 로그아웃 처리');
          
          // 토큰 정리
          if (typeof window !== 'undefined') {
            localStorage.removeItem('access_token');
            localStorage.removeItem('refresh_token');
            localStorage.removeItem('user');
            
            // 사용자에게 알림
            alert('로그인 세션이 만료되었습니다. 다시 로그인해주세요.');
            
            // 로그인 페이지로 리다이렉트
            window.location.href = '/login';
          }
          throw new Error('로그인 세션이 만료되었습니다.');
        }
      }
      
      // 백엔드에서 error 필드를 보낸 경우, 해당 메시지만 사용
      if (errorData && typeof errorData === 'object') {
        const errorObj = errorData as Record<string, unknown>;
        if (errorObj.error) {
          throw new Error(String(errorObj.error));
        }
      }
      
      // error 필드가 없는 경우, 기본 HTTP 상태 메시지 사용 
      const statusMessage = response.status === 404 ? '리소스를 찾을 수 없습니다.' :
                            response.status === 403 ? '접근 권한이 없습니다.' :
                            response.status === 500 ? '서버 오류가 발생했습니다.' :
                            response.status === 400 ? '요청이 잘못되었습니다.' :
                            '알 수 없는 오류가 발생했습니다.';
      
      throw new Error(statusMessage);
    }
    
    // DELETE 요청의 경우 빈 응답이므로 JSON 파싱을 시도하지 않음
    if (options.method === 'DELETE') {
      return undefined as T;
    }
    
    // 응답이 비어있는 경우 빈 객체 반환
    const text = await response.text();
    if (!text) {
      return undefined as T;
    }
    
    try {
      return JSON.parse(text);
    } catch (parseError) {
      console.error('JSON 파싱 오류:', parseError);
      throw new Error(`응답 파싱 실패: ${endpoint}`);
    }
  } catch (networkError) {
    console.error('[API] 네트워크 호출 오류:', networkError);
    console.error('[API] 요청 URL:', url);
    console.error('[API] 요청 옵션:', config);
    
    // 더 자세한 오류 메시지 제공
    if (networkError instanceof TypeError && networkError.message.includes('fetch')) {
      const errorMsg = `네트워크 오류: 백엔드 서버(${API_BASE_URL})에 연결할 수 없습니다. 서버가 실행 중인지 확인하세요.`;
      console.error('[API]', errorMsg);
      throw new Error(errorMsg);
    }
    
    if (networkError instanceof Error) {
      throw networkError;
    }
    
    throw new Error('알 수 없는 네트워크 오류가 발생했습니다.');
  }
}

// 영업일지 관련 API
export const salesReportApi = {
  // 영업일지 목록 조회 (페이지네이션/검색/필터 지원)
  getReports: (paramsObj: SalesReportParams = {}): Promise<PaginatedResponse<SalesReport>> => {
    const params = new URLSearchParams();
    if (paramsObj.page) params.append('page', paramsObj.page.toString());
    if (paramsObj.page_size) params.append('page_size', paramsObj.page_size.toString());
    if (paramsObj.search) params.append('search', paramsObj.search);
    if (paramsObj.period) params.append('period', paramsObj.period);
    if (paramsObj.ordering) params.append('ordering', paramsObj.ordering);
    if (paramsObj.companyId) params.append('companyId', paramsObj.companyId.toString());
    const queryString = params.toString() ? `?${params.toString()}` : '';
    return apiCall<PaginatedResponse<SalesReport>>(`/sales-reports${queryString}`);
  },

  // 영업일지 상세 조회
  getReport: (id: number): Promise<SalesReport> => {
    return apiCall<SalesReport>(`/reports/${id}/`);
  },

  // 영업일지 생성
  createReport: (data: CreateSalesReportData): Promise<SalesReport> => {
    return apiCall<SalesReport>('/reports/', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  // 영업일지 수정
  updateReport: (id: number, data: UpdateSalesReportData): Promise<SalesReport> => {
    return apiCall<SalesReport>(`/reports/${id}/`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  },

  // 영업일지 삭제
  deleteReport: (id: number): Promise<void> => {
    return apiCall<void>(`/reports/${id}/`, {
      method: 'DELETE',
    });
  },
};

// 회사 관련 API (업데이트됨)
export const companyApi = {
  // 회사 목록 조회 (필터링 및 페이지네이션 지원)
  getCompanies: (filters?: CompanyFilters, page?: number): Promise<PaginatedResponse<Company>> => {
    const params = new URLSearchParams();
    
    if (filters?.search) {
      params.append('search', filters.search);
    }
    if (filters?.customer_classification) {
      params.append('customer_classification', filters.customer_classification);
    }
    if (filters?.industry_name) {
      params.append('industry_name', filters.industry_name);
    }
    if (filters?.ordering) {
      params.append('ordering', filters.ordering);
    }
    if (page) {
      params.append('page', page.toString());
    }

    const queryString = params.toString() ? `?${params.toString()}` : '';
    return apiCall<PaginatedResponse<Company>>(`/companies/${queryString}`);
  },

  // 회사명 자동완성 검색 (회사명 (시/구) 형식)
  suggestCompanies: (query: string): Promise<CompanySuggestion[]> => {
    if (!query.trim()) {
      return Promise.resolve([]);
    }
    return apiCall<CompanySuggestion[]>(`/company/suggest/?query=${encodeURIComponent(query)}`);
  },

  // 회사의 유니크한 상품명 조회
  getUniqueProducts: (companyCode: string): Promise<CompanyUniqueProducts> => {
    return apiCall<CompanyUniqueProducts>(`/companies/${companyCode}/unique-products/`);
  },

  // 회사 상세 조회
  getCompany: (companyCode: string): Promise<Company> => {
    return apiCall<Company>(`/companies/${companyCode}/`);
  },

  // 회사 생성
  createCompany: (data: Partial<Company>): Promise<Company> => {
    return apiCall<Company>('/companies/', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  // 회사 수정
  updateCompany: (companyCode: string, data: Partial<Company>): Promise<Company> => {
    return apiCall<Company>(`/companies/${companyCode}/`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  },

  // 회사 삭제
  deleteCompany: (companyCode: string): Promise<void> => {
    return apiCall<void>(`/companies/${companyCode}/`, {
      method: 'DELETE',
    });
  },

  // 회사 통계 조회
  getCompanyStats: async (search?: string): Promise<CompanyStats> => {
    const params = new URLSearchParams();
    if (search) {
      params.append('search', search);
    }
    const queryString = params.toString() ? `?${params.toString()}` : '';
    return apiCall<CompanyStats>(`/stats/companies/${queryString}`);
  },

  // 회사 자동 등록 (회사명만으로)
  autoCreateCompany: (company_name: string, location?: string): Promise<Company> => {
    return apiCall<Company>('/companies/auto-create/', {
      method: 'POST',
      body: JSON.stringify({ company_name, location: location || '' }),
    });
  },

  // CSV 다운로드
  downloadReportsCsv: async (): Promise<Blob> => {
    const token = localStorage.getItem('access_token');
    const response = await fetch(`${API_BASE_URL}/export/reports/`, {
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      const errorMessage = errorData.error || `HTTP ${response.status}: ${response.statusText}`;
      throw new Error(errorMessage);
    }
    
    return response.blob();
  },

  downloadCompaniesCsv: async (): Promise<Blob> => {
    const token = localStorage.getItem('access_token');
    const response = await fetch(`${API_BASE_URL}/export/companies/`, {
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      const errorMessage = errorData.error || `HTTP ${response.status}: ${response.statusText}`;
      throw new Error(errorMessage);
    }
    
    return response.blob();
  },

  // CSV 업로드
  uploadReportsCsv: async (file: File): Promise<{
    message: string;
    created_count: number;
    updated_count: number;
    errors: string[];
  }> => {
    const token = localStorage.getItem('access_token');
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await fetch(`${API_BASE_URL}/import/reports/`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
      },
      body: formData,
    });
    
    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.error || 'CSV 업로드에 실패했습니다.');
    }
    
    return response.json();
  },

  uploadCompaniesCsv: async (file: File): Promise<{
    message: string;
    created_count: number;
    updated_count: number;
    errors: string[];
  }> => {
    const token = localStorage.getItem('access_token');
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await fetch(`${API_BASE_URL}/import/companies/`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
      },
      body: formData,
    });
    
    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.error || 'CSV 업로드에 실패했습니다.');
    }
    
    return response.json();
  },

  uploadCompaniesSapTsv: async (file: File): Promise<{
    message: string;
    created_count: number;
    updated_count: number;
    errors: string[];
  }> => {
    const token = localStorage.getItem('access_token');
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await fetch(`${API_BASE_URL}/import/companies-sap/`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
      },
      body: formData,
    });
    
    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.error || 'SAP 거래처 TSV 업로드에 실패했습니다.');
    }
    
    return response.json();
  },

  uploadSalesDataCsv: async (file: File): Promise<{
    message: string;
    created_count: number;
    updated_count: number;
    errors: string[];
  }> => {
    console.log('uploadSalesDataCsv 함수 호출됨');
    const token = localStorage.getItem('access_token');
    console.log('토큰 존재:', !!token);
    const formData = new FormData();
    formData.append('file', file);
    console.log('API_BASE_URL:', API_BASE_URL);
    console.log('요청 URL:', `${API_BASE_URL}/import/sales-data/`);
    
    try {
      const response = await fetch(`${API_BASE_URL}/import/sales-data/`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
        body: formData,
      });
      
      console.log('응답 상태:', response.status);
      console.log('응답 OK:', response.ok);
      console.log('응답 헤더:', Object.fromEntries(response.headers.entries()));
      
      if (!response.ok) {
        let errorData;
        try {
          const text = await response.text();
          console.log('오류 응답 본문:', text);
          errorData = text ? JSON.parse(text) : { error: `서버 오류 (${response.status})` };
        } catch (parseError) {
          console.error('오류 응답 파싱 실패:', parseError);
          errorData = { error: `서버 오류 (${response.status}): 응답을 파싱할 수 없습니다.` };
        }
        console.error('API 오류:', errorData);
        throw new Error(errorData.error || `매출 데이터 업로드에 실패했습니다. (상태 코드: ${response.status})`);
      }
      
      const result = await response.json();
      console.log('성공 결과:', result);
      return result;
    } catch (error) {
      console.error('API 호출 중 오류:', error);
      // 네트워크 오류인 경우 더 자세한 정보 제공
      if (error instanceof TypeError && error.message.includes('fetch')) {
        throw new Error(`네트워크 오류: 백엔드 서버(${API_BASE_URL})에 연결할 수 없습니다. 서버가 실행 중인지 확인하세요.`);
      }
      // 이미 Error 객체인 경우 그대로 throw
      if (error instanceof Error) {
        throw error;
      }
      // 그 외의 경우
      throw new Error(`매출 데이터 업로드 중 오류가 발생했습니다: ${String(error)}`);
    }
  },
}; 

export const companyFinancialStatusApi = {
  getByCompanyCode: async (companyCode: string): Promise<CompanyFinancialStatus[]> => {
    // company_code로 필터링 (재무정보는 company_code를 참조)
    const params = new URLSearchParams({
      'company__company_code': companyCode
    });
    return apiCall<CompanyFinancialStatus[]>(`/company-financial-status/?${params.toString()}`);
  },
};

// 회사별 SalesData API
export const companySalesDataApi = {
  getCompanySalesData: async (companyCode: string): Promise<CompanySalesData> => {
    return apiCall<CompanySalesData>(`/companies/${companyCode}/sales-data/`);
  },
};

// 키워드 추출(추천 태그) API
export async function fetchRecommendedTags(content: string): Promise<string[]> {
  console.log('fetchRecommendedTags 호출됨, content 길이:', content.length);
  try {
    const res = await apiCall<{ keywords: string[] }>(
      '/extract-keywords/',
      {
        method: 'POST',
        body: JSON.stringify({ text: content }),
      }
    );
    console.log('키워드 추출 API 응답:', res);
    if (!res || !res.keywords) {
      console.error('잘못된 응답 형식:', res);
      throw new Error('키워드를 추출할 수 없습니다.');
    }
    return res.keywords;
  } catch (error) {
    console.error('키워드 추출 API 호출 중 오류:', error);
    throw error;
  }
}

// 대시보드 통계 API
export const dashboardApi = {
  // 대시보드 주요 지표 통계
  getDashboardStats: async (): Promise<{
    thisMonthReports: number;
    reportsGrowthRate: number;
    thisMonthNewCompanies: number;
    totalContacts: number;
    faceToFaceContacts: number;
    phoneContacts: number;
    thisMonthRevenue: number;
    revenueGrowthRate: number;
  }> => {
    return apiCall('/stats/dashboard/');
  },

  // 대시보드 차트 데이터
  getDashboardCharts: async (): Promise<{
    salesData: Array<{
      name: string;
      매출액: number;
      매출수량: number;
      매출건수: number;
    }>;
    channelData: Array<{
      name: string;
      value: number;
      color: string;
    }>;
    recentActivities: Array<{
      company: string;
      type: string;
      date: string;
      author: string;
    }>;
  }> => {
    return apiCall('/charts/dashboard/');
  },
}; 