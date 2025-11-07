// SAP 코드 상수 정의

export interface SapCodeOption {
  code: string;
  name: string;
}

// 사업부 코드
export const bizCodes: SapCodeOption[] = [
  { code: '1033', name: '축산유통사업부' },
];

// 지점/팀 코드
export const departmentCodes: SapCodeOption[] = [
  { code: '347', name: '중부지점' },
  { code: '381', name: '가공장영업팀' },
  { code: '383', name: '신경로영업팀' },
  { code: '382', name: '도매영업팀' },
];

// 사원 코드
export const employeeCodes: SapCodeOption[] = [
  { code: '240527', name: '김 윤성' },
  { code: '240526', name: '김 영길' },
  { code: '250010', name: '선 효지' },
  { code: '240071', name: '김 신현' },
  { code: '250012', name: '김 예지' },
  { code: '250013', name: '전 병희' },
  { code: '250368', name: '오 세훈' },
  { code: '230111', name: '이 태훈' },
  { code: '250011', name: '임 수정' },
  { code: '250015', name: '엄 재후' },
  { code: '250016', name: '윤 영상' },
  { code: '240529', name: '박 정우' },
  { code: '240260', name: '서 대한' },
  { code: '195859', name: '김 태훈' },
  { code: '195701', name: '장 경재' },
  { code: '195846', name: '황 유빈' },
];

// 유통형태 코드
export const distributionTypeCodes: SapCodeOption[] = [
  { code: 'J7030', name: '축육(도매)' },
  { code: 'J7020', name: '축육(가공장)' },
  { code: 'J7010', name: '축육(실수요)' },
  { code: 'J7040', name: '축육(FC)' },
  { code: 'J7050', name: '축육(마트)' },
];

// 결제조건 리스트
export const paymentTerms: string[] = [
  '15일단위 마감, 30일이내, 현금결제(영업)',
  '선입금(영업)',
  '상계',
  '말일 마감, 당월 말일, 현금결제(영업)',
  '말일 마감, 60일이내, 현금결제(영업)',
  '말일 마감, 5일이내, 현금결제(영업)',
  '말일 마감, 45일이내, 현금결제(영업)',
  '말일 마감, 30일이내, 현금결제(유통)',
  '말일 마감, 30일이내, 현금결제(영업)',
  '말일 마감, 20일이내, 현금결제(유통)',
  '말일 마감, 20일이내, 현금결제(영업)',
  '말일 마감, 15일이내, 현금결제(영업)',
  '말일 마감, 10일이내, 현금결제(유통)',
  '말일 마감, 10일이내, 현금결제(영업)',
  '말일 마감, 0일이내, 현금결제(유통)',
  '15일 마감, 익월 말일, 현금결제(영업)',
  '15일 단위 현금',
  '10일단위 마감, 10일이내, 현금결제(영업)',
];

// 유틸리티 함수: 코드로 이름 찾기
export function getNameByCode(code: string, options: SapCodeOption[]): string | undefined {
  return options.find(option => option.code === code)?.name;
}

// 유틸리티 함수: 이름으로 코드 찾기
export function getCodeByName(name: string, options: SapCodeOption[]): string | undefined {
  return options.find(option => option.name === name)?.code;
}

