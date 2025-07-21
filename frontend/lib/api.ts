const API_BASE_URL = 'http://localhost:8000/api';

export interface SalesReport {
  id: number;
  author: number;  // User ID
  author_name: string;
  author_department: string;
  team: string;
  team_display: string;  // 표시용 팀명
  visitDate: string;
  company: string;
  company_obj?: number;  // Company ID (선택사항)
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
}

export interface CompanyFilters {
  search?: string;
  customer_classification?: string;
  industry_name?: string;
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
    throw new Error(`API 호출 실패: ${response.status} - ${endpoint}`);
  }
  
  return response.json();
}

// 페이지네이션 응답 타입
export interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

// 영업일지 관련 API
export const salesReportApi = {
  // 영업일지 목록 조회 (페이지네이션 지원)
  getReports: (page?: number): Promise<PaginatedResponse<SalesReport>> => {
    const params = new URLSearchParams();
    if (page) {
      params.append('page', page.toString());
    }
    const queryString = params.toString() ? `?${params.toString()}` : '';
    return apiCall<PaginatedResponse<SalesReport>>(`/reports/${queryString}`);
  },

  // 영업일지 상세 조회
  getReport: (id: number): Promise<SalesReport> => {
    return apiCall<SalesReport>(`/reports/${id}/`);
  },

  // 영업일지 생성
  createReport: (data: Omit<SalesReport, 'id' | 'createdAt' | 'author' | 'author_name' | 'author_department' | 'team'>): Promise<SalesReport> => {
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
}; 