// 영업일지 관련 타입 정의

export interface SalesReport {
  id: number;
  author: number;  // User ID
  author_name: string;
  author_department: string;
  visitDate: string;
  company_name?: string | null;  // 회사명
  company_code?: string | null;  // 회사 코드(Primary Key)
  company_obj?: string | null;  // 회사 객체 ID (company_code)
  company_display?: string;  // 표시용 회사명 (옵션)
  company_city_district?: string | null;  // 회사 시/구
  sales_stage?: string;  // 영업단계
  company_code_resolved?: string | null;  // 해결된 company_code (API 응답용)
  type: string;
  products: string;
  content: string;
  tags: string;
  createdAt: string;
}

// 영업일지 생성 데이터 타입
export interface CreateSalesReportData {
  visitDate: string;
  company: string;
  company_obj?: string | null;
  sales_stage?: string | null;
  type: string;
  location?: string;  // 신규 회사 소재지 (optional)
  products: string;
  content: string;
  tags: string;
}

// 영업일지 수정 데이터 타입
export type UpdateSalesReportData = Partial<SalesReport>;

// 영업일지 조회 파라미터 타입
export interface SalesReportParams {
  page?: number;
  page_size?: number;
  search?: string;
  period?: string;
  ordering?: string;
  companyId?: string | number;
}

