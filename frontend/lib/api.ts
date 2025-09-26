// 환경에 따른 API URL 설정
const getApiBaseUrl = () => {
  // 브라우저 환경에서 현재 호스트 확인
  if (typeof window !== 'undefined') {
    const hostname = window.location.hostname;
    const port = window.location.port;
    
    // 개발 환경 체크 (더 포괄적으로)
    if (hostname === 'localhost' || 
        hostname === '127.0.0.1' || 
        hostname.startsWith('172.28.') ||  // Docker/VM 환경
        port === '3000') {
      return 'http://127.0.0.1:8000/api';
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
  company_obj?: number | null;  // Company ID (선택사항)
  company_display: string;  // 표시용 회사명
  type: string;
  location: string;
  products: string;
  content: string;
  tags: string;
  createdAt: string;
}

// 새로운 Company 타입 (CSV 데이터 구조에 맞춤)
export interface Company {
  id: number;
  company_name: string;
  sales_diary_company_code?: string;
  company_code_sm?: string;
  company_code_sap?: string;
  company_type?: string;
  established_date?: string;
  ceo_name?: string;
  address?: string;
  contact_person?: string;
  contact_phone?: string;
  main_phone?: string;
  distribution_type_sap?: string;
  industry_name?: string;
  main_product?: string;
  transaction_start_date?: string;
  payment_terms?: string;
  customer_classification?: string;
  website?: string;
  remarks?: string;
  username?: number | null; // 영업 사원 (User FK)
  username_display?: string | null; // 영업 사원 이름
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
  const token = localStorage.getItem('access_token');
  
  const config: RequestInit = {
    headers: {
      'Content-Type': 'application/json',
      ...(token && { 'Authorization': `Bearer ${token}` }),
      ...options.headers,
    },
    ...options,
  };

  const response = await fetch(`${API_BASE_URL}${endpoint}`, config);
  
  if (!response.ok) {
    console.error(`API 호출 실패: ${response.status} - ${endpoint}`);
    console.error('Response:', response);
    
    // 응답 본문을 읽어서 더 자세한 오류 정보 제공
    try {
      const errorData = await response.json();
      console.error('Error details:', errorData);
      // errorData가 객체이고 error 필드가 있으면 그 메시지만 전달
      if (errorData && typeof errorData === 'object' && errorData.error) {
        throw new Error(errorData.error);
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
    company_obj?: number | null;
    type: string;
    location: string;
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

  // 회사명 자동완성 검색
  suggestCompanies: (query: string): Promise<Array<{id: number, name: string}>> => {
    if (!query.trim()) {
      return Promise.resolve([]);
    }
    return apiCall<Array<{id: number, name: string}>>(`/company/suggest/?query=${encodeURIComponent(query)}`);
  },

  // 회사 상세 조회
  getCompany: (id: number): Promise<Company> => {
    return apiCall<Company>(`/companies/${id}/`);
  },

  // 회사 생성
  createCompany: (data: Partial<Company>): Promise<Company> => {
    return apiCall<Company>('/companies/', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  // 회사 수정
  updateCompany: (id: number, data: Partial<Company>): Promise<Company> => {
    return apiCall<Company>(`/companies/${id}/`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  },

  // 회사 삭제
  deleteCompany: (id: number): Promise<void> => {
    return apiCall<void>(`/companies/${id}/`, {
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
}; 

export const companyFinancialStatusApi = {
  getByCompanyCode: async (companyCode: string): Promise<CompanyFinancialStatus[]> => {
    // 회사코드로 필터링 (company__sales_diary_company_code)
    const params = new URLSearchParams({
      'company__sales_diary_company_code': companyCode
    });
    return apiCall<CompanyFinancialStatus[]>(`/company-financial-status/?${params.toString()}`);
  },
};

// 키워드 추출(추천 태그) API
export async function fetchRecommendedTags(content: string): Promise<string[]> {
  const res = await apiCall<{ keywords: string[] }>(
    '/extract-keywords/',
    {
      method: 'POST',
      body: JSON.stringify({ text: content }),
    }
  );
  return res.keywords;
} 