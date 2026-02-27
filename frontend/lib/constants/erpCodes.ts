// ERP 코드 상수 정의

export interface ErpCodeOption {
  code: string;
  name: string;
}

// 사원 코드 (참푸드 담당자)
export const employeeCodes: ErpCodeOption[] = [];

// 유통형태 코드
export const distributionTypeCodes: ErpCodeOption[] = [];

// 결제조건 리스트
export const paymentTerms: string[] = [
  '선입금',
  '말일 마감 익월 10일',
  '말일 마감 익월 15일',
  '말일 마감 익월 30일',
  '말일 마감 익월 45일',
  '말일 마감 익월 60일',
  '현금결제',
  '상계',
];

// 유틸리티 함수: 코드로 이름 찾기
export function getNameByCode(code: string, options: ErpCodeOption[]): string | undefined {
  return options.find(option => option.code === code)?.name;
}

// 유틸리티 함수: 이름으로 코드 찾기
export function getCodeByName(name: string, options: ErpCodeOption[]): string | undefined {
  return options.find(option => option.name === name)?.code;
}
