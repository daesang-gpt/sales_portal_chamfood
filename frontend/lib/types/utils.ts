// 타입 가드 및 유틸리티 함수

import type { SalesReport, Company } from './index';

/**
 * 객체가 SalesReport인지 확인하는 타입 가드
 */
export function isSalesReport(obj: unknown): obj is SalesReport {
  if (!obj || typeof obj !== 'object') {
    return false;
  }
  
  const report = obj as Record<string, unknown>;
  return (
    typeof report.id === 'number' &&
    typeof report.author === 'number' &&
    typeof report.author_name === 'string' &&
    typeof report.visitDate === 'string' &&
    typeof report.type === 'string' &&
    typeof report.products === 'string' &&
    typeof report.content === 'string'
  );
}

/**
 * 객체가 Company인지 확인하는 타입 가드
 */
export function isCompany(obj: unknown): obj is Company {
  if (!obj || typeof obj !== 'object') {
    return false;
  }
  
  const company = obj as Record<string, unknown>;
  return (
    typeof company.company_code === 'string' &&
    typeof company.company_name === 'string'
  );
}

