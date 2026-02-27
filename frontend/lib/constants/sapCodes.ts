// 하위 호환성을 위해 erpCodes.ts에서 re-export
export type { ErpCodeOption as SapCodeOption } from './erpCodes';
export {
  employeeCodes,
  distributionTypeCodes,
  paymentTerms,
  getNameByCode,
  getCodeByName,
} from './erpCodes';

// 빈 배열 (삭제된 필드 - 하위 호환성)
export const bizCodes: import('./erpCodes').ErpCodeOption[] = [];
export const departmentCodes: import('./erpCodes').ErpCodeOption[] = [];

