// 회사 관련 타입 정의

export interface Company {
  company_code: string; // Primary Key
  company_name: string;
  // 기본정보
  customer_classification?: '잠재' | '신규' | '기존' | '이탈' | '벤더';
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
  ordering?: string;
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

// 회사 통계 타입
export interface CompanyStats {
  total: number;
  potentialCustomers: number;
  newCustomers: number;
  existingCustomers: number;
  churnedCustomers: number;
  filteredTotal?: number;
  filteredPotentialCustomers?: number;
  filteredNewCustomers?: number;
  filteredExistingCustomers?: number;
  filteredChurnedCustomers?: number;
}

// 회사 제안 타입 (자동완성)
export interface CompanySuggestion {
  id: string;
  name: string;  // 표시용: "회사명 (시/구)" 형식
  company_name?: string;  // 실제 회사명
}

// 회사 유니크 상품명 응답 타입
export interface CompanyUniqueProducts {
  products: string[];
}

// 회사 매출 데이터 타입
export interface CompanySalesData {
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
}

// 업체 리스트 타입
export interface ProspectCompany {
  id: number;
  license_number?: string;
  company_name: string;
  industry: '축산물 가공장' | '식품 가공장' | '도소매';
  ceo_name?: string;
  location?: string;
  main_products?: string;
  phone?: string;
  priority?: '높음' | '중간' | '낮음';
  has_transaction?: '거래중' | '미거래';
  created_at?: string;
  updated_at?: string;
}

// 업체 리스트 통계 타입
export interface ProspectCompanyStats {
  [key: string]: {
    total: number;
    ourCustomers: number;
    ratio: number;
  };
}

