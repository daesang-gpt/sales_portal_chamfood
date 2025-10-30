// 환경에 따른 API URL 설정
const getApiBaseUrl = () => {
  // 브라우저 환경에서 현재 호스트 확인
  if (typeof window !== 'undefined') {
    const hostname = window.location.hostname;
    const port = window.location.port;
    
    // localhost나 127.0.0.1인 경우
    if (hostname === 'localhost' || hostname === '127.0.0.1') {
      return 'http://127.0.0.1:8000/api';
    }
    
    // 172.28.x.x 같은 내부 IP인 경우 같은 호스트의 8000 포트 사용
    if (hostname.startsWith('172.28.') || hostname.startsWith('192.168.')) {
      return `http://${hostname}:8000/api`;
    }
    
    // 그 외의 경우 운영 환경으로 간주
    return 'http://192.168.99.37:8000/api';
  }
  
  // 서버 사이드 렌더링 시 개발 환경으로 간주
  return 'http://127.0.0.1:8000/api';
};

const API_BASE_URL = getApiBaseUrl();

export interface SalesReport {
  id: number;
  author: number;  // User ID
  author_name: string;
  author_department: string;
  team: string;
  team_display: string;  // 표시용 팀명
  visitDate: string;
  company: string;
  company_code?: string | null;  // 회사 코드(Primary Key)
  company_display: string;  // 표시용 회사명
  type: string;
  products: string;
  content: string;
  tags: string;
  createdAt: string;
}

// 새로운 Company 타입 (TSV 데이터 구조에 맞춤)
export interface Company {
  company_code: string; // Primary Key
  company_name: string;
  // 기본정보
  customer_classification?: '기존' | '신규' | '이탈' | '기타';
  company_type?: '개인' | '법인';
  tax_id?: string;
  established_date?: string;
  ceo_name?: string;
  head_address?: string;
  city_district?: string;
  processing_address?: string;
  main_phone?: string;
  industry_name?: string;
  products?: string;
  website?: string;
  remarks?: string;
  // SAP정보
  sap_code_type?: string;
  company_code_sap?: string;
  biz_code?: string;
  biz_name?: string;
  department_code?: string;
  department?: string;
  employee_number?: string;
  employee_name?: string;
  distribution_type_sap_code?: string;
  distribution_type_sap?: string;
  contact_person?: string;
  contact_phone?: string;
  code_create_date?: string;
  transaction_start_date?: string;
  payment_terms?: string;
}

export interface CompanyFilters {
  search?: string;
  customer_classification?: string;
  industry_name?: string;
}

export interface CompanyFinancialStatus {
  id: number;
  company: number;
  fiscal_year: string;
  total_assets: number;
  capital: number;
  total_equity: number;
  revenue: number;
  operating_income: number;
  net_income: number;
}

// API 호출 헬퍼 함수
async function apiCall<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const token = (typeof window !== 'undefined') ? localStorage.getItem('access_token') : null;

  const method = (options.method || 'GET').toString().toUpperCase();
  const isFormData = typeof FormData !== 'undefined' && options.body instanceof FormData;

  const baseHeaders: Record<string, string> = {
    ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
  };

  // 시작 헤더 병합 (사용자 지정 헤더 우선)
  let headers: HeadersInit = {
    ...baseHeaders,
    ...(options.headers as any),
  };

  // Content-Type은 다음 조건에서만 자동 설정
  // - 메서드가 GET/HEAD가 아님
  // - body가 FormData가 아님 (브라우저가 자동 설정)
  // - 사용자가 이미 Content-Type을 지정하지 않음
  const hasContentType = !!(headers as any)['Content-Type'] || !!(headers as any)['content-type'];
  if (method !== 'GET' && method !== 'HEAD' && !isFormData && !hasContentType) {
    headers = { 'Content-Type': 'application/json', ...headers };
  }

  const config: RequestInit = {
    ...options,
    headers,
  };

  const url = `${API_BASE_URL}${endpoint}`;
  try {
    const response = await fetch(url, config);
  
    if (!response.ok) {
      console.error(`API 호출 실패: ${response.status} - ${endpoint}`);
      console.error('Response:', response);
      
      // 응답 본문을 읽어서 더 자세한 오류 정보 제공
      try {
        const errorData = await response.json();
        console.error('Error details:', errorData);
        if (errorData && typeof errorData === 'object' && (errorData as any).error) {
          throw new Error((errorData as any).error);
        }
        throw new Error(`API 호출 실패: ${response.status} - ${endpoint}\n${JSON.stringify(errorData, null, 2)}`);
      } catch (parseError) {
        throw new Error(`API 호출 실패: ${response.status} - ${endpoint}`);
      }
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
    console.error('네트워크 호출 오류:', networkError, '\
요청 URL:', url, '\n옵션:', config);
    throw new Error('Failed to fetch: 네트워크 또는 CORS 오류가 발생했습니다.');
  }
}

// 페이지네이션 응답 타입
export interface PaginatedResponse<T> {
  results: T[];
  count: number;
  total_pages: number;
  current_page: number;
}

// 영업일지 관련 API
export const salesReportApi = {
  // 영업일지 목록 조회 (페이지네이션/검색/필터 지원)
  getReports: (paramsObj: {
    page?: number;
    page_size?: number;
    search?: string;
    period?: string;
    ordering?: string;
    companyId?: string | number;
  } = {}): Promise<PaginatedResponse<SalesReport>> => {
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
  createReport: (data: {
    visitDate: string;
    company: string;
    company_obj?: string | null;
    type: string;
    location?: string;  // 신규 회사 소재지 (optional)
    products: string;
    content: string;
    tags: string;
  }): Promise<SalesReport> => {
    return apiCall<SalesReport>('/reports/', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  // 영업일지 수정
  updateReport: (id: number, data: Partial<SalesReport>): Promise<SalesReport> => {
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
    if (page) {
      params.append('page', page.toString());
    }

    const queryString = params.toString() ? `?${params.toString()}` : '';
    return apiCall<PaginatedResponse<Company>>(`/companies/${queryString}`);
  },

  // 회사명 자동완성 검색 (회사명 (시/구) 형식)
  suggestCompanies: (query: string): Promise<Array<{id: string, name: string}>> => {
    if (!query.trim()) {
      return Promise.resolve([]);
    }
    return apiCall<Array<{id: string, name: string}>>(`/company/suggest/?query=${encodeURIComponent(query)}`);
  },

  // 회사의 유니크한 상품명 조회
  getUniqueProducts: (companyCode: string): Promise<{products: string[]}> => {
    return apiCall<{products: string[]}>(`/companies/${companyCode}/unique-products/`);
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
  getCompanyStats: async (): Promise<{
    total: number;
    newCustomers: number;
    existingCustomers: number;
    thisMonthNew: number;
  }> => {
    return apiCall<{
      total: number;
      newCustomers: number;
      existingCustomers: number;
      thisMonthNew: number;
    }>('/stats/companies/');
  },

  // 회사 자동 등록 (회사명만으로)
  autoCreateCompany: (company_name: string): Promise<Company> => {
    return apiCall<Company>('/companies/auto-create/', {
      method: 'POST',
      body: JSON.stringify({ company_name }),
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
      
      if (!response.ok) {
        const errorData = await response.json();
        console.error('API 오류:', errorData);
        throw new Error(errorData.error || '매출 데이터 업로드에 실패했습니다.');
      }
      
      const result = await response.json();
      console.log('성공 결과:', result);
      return result;
    } catch (error) {
      console.error('API 호출 중 오류:', error);
      throw error;
    }
  },
}; 

export const companyFinancialStatusApi = {
  getByCompanyCode: async (companyCode: string): Promise<CompanyFinancialStatus[]> => {
    // SAP 회사코드로 필터링 (company__company_code_sap)
    const params = new URLSearchParams({
      'company__company_code_sap': companyCode
    });
    return apiCall<CompanyFinancialStatus[]>(`/company-financial-status/?${params.toString()}`);
  },
};

// 회사별 SalesData API
export const companySalesDataApi = {
  getCompanySalesData: async (companyCode: string): Promise<{
    company_name: string;
    company_code_sap: string;
    sales_chart_data: Array<{
      month: string;
      매출금액: number;
      매출이익: number;
      GP: number;
    }>;
    products_chart_data: Array<{
      month: string;
      [key: string]: number | string; // 축종별 동적 키
    }>;
    total_records: number;
  }> => {
    return apiCall(`/companies/${companyCode}/sales-data/`);
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