'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { isAdmin, isAuthenticated, logout, getUserFromToken } from '@/lib/auth';
import { companyApi } from '@/lib/api';

export default function AdminPage() {
  const [user, setUser] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(true);
  const router = useRouter();

  useEffect(() => {
    // 인증 및 권한 확인
    if (!isAuthenticated()) {
      router.push('/login');
      return;
    }

    if (!isAdmin()) {
      router.push('/');
      return;
    }

    const currentUser = getUserFromToken();
    setUser(currentUser);
    setIsLoading(false);
  }, [router]);

  const handleLogout = () => {
    logout();
    router.push('/login');
  };

  const uploadSalesData = () => {
    console.log('업로드 함수 호출됨');
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = '.csv,.xlsx,.tsv';
    input.onchange = async (event) => {
      const file = (event.target as HTMLInputElement).files?.[0];
      console.log('선택된 파일:', file);
      if (file) {
        console.log('파일 업로드 시작:', file.name, file.size);
        try {
          console.log('API 호출 시작');
          const result = await companyApi.uploadSalesDataCsv(file);
          console.log('업로드 결과:', result);
          alert(`업로드 완료!\n신규 생성: ${result.created_count}건\n업데이트: ${result.updated_count}건\n\n총 오류: ${result.errors.length}개`);
          if (result.errors.length > 0) {
            console.log('업로드 오류:', result.errors);
          }
        } catch (error: any) {
          console.error('업로드 오류:', error);
          alert(`업로드 실패: ${error.message}`);
        }
      } else {
        console.log('파일이 선택되지 않음');
      }
    };
    input.click();
  };

  const uploadSapCompanies = () => {
    console.log('SAP 거래처 업로드 함수 호출됨');
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = '.tsv';
    input.onchange = async (event) => {
      const file = (event.target as HTMLInputElement).files?.[0];
      console.log('선택된 파일:', file);
      if (file) {
        console.log('파일 업로드 시작:', file.name, file.size);
        try {
          console.log('API 호출 시작');
          const result = await companyApi.uploadCompaniesSapTsv(file);
          console.log('업로드 결과:', result);
          let message = `업로드 완료!\n신규 생성: ${result.created_count}건\n업데이트: ${result.updated_count}건`;
          if (result.errors.length > 0) {
            message += `\n\n총 오류: ${result.errors.length}개`;
            if (result.errors.length <= 5) {
              message += `\n\n오류 목록:\n${result.errors.join('\n')}`;
            } else {
              message += `\n\n오류 목록 (최대 5개):\n${result.errors.slice(0, 5).join('\n')}\n...`;
            }
            console.log('업로드 오류:', result.errors);
          }
          alert(message);
        } catch (error: any) {
          console.error('업로드 오류:', error);
          alert(`업로드 실패: ${error.message}`);
        }
      } else {
        console.log('파일이 선택되지 않음');
      }
    };
    input.click();
  };

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-lg">로딩 중...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-4xl mx-auto">
        <div className="flex justify-between items-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900">관리자 대시보드</h1>
          <Button onClick={handleLogout} variant="outline">
            로그아웃
          </Button>
        </div>

        {user && (
          <Card className="mb-8">
            <CardHeader>
              <CardTitle>관리자 정보</CardTitle>
              <CardDescription>현재 로그인된 관리자 정보입니다.</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-sm font-medium text-gray-500">이름</p>
                  <p className="text-lg">{user.name}</p>
                </div>
                <div>
                  <p className="text-sm font-medium text-gray-500">부서</p>
                  <p className="text-lg">{user.department}</p>
                </div>
                <div>
                  <p className="text-sm font-medium text-gray-500">사번</p>
                  <p className="text-lg">{user.employee_number}</p>
                </div>
                <div>
                  <p className="text-sm font-medium text-gray-500">권한</p>
                  <p className="text-lg">
                    {user.role === 'admin' ? '관리자' : user.role === 'viewer' ? '뷰어' : '사용자'}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <Card>
            <CardHeader>
              <CardTitle>사용자 관리</CardTitle>
              <CardDescription>전체 사용자 목록을 확인하고 관리합니다.</CardDescription>
            </CardHeader>
            <CardContent>
              <Button 
                className="w-full"
                onClick={() => router.push('/admin/users')}
              >
                사용자 목록 보기
              </Button>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>회사 관리</CardTitle>
              <CardDescription>등록된 회사 정보를 관리합니다.</CardDescription>
            </CardHeader>
            <CardContent>
              <Button className="w-full">회사 목록 보기</Button>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>보고서 관리</CardTitle>
              <CardDescription>판매 보고서를 확인하고 관리합니다.</CardDescription>
            </CardHeader>
            <CardContent>
              <Button className="w-full">보고서 목록 보기</Button>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>통계</CardTitle>
              <CardDescription>전체 통계 정보를 확인합니다.</CardDescription>
            </CardHeader>
            <CardContent>
              <Button className="w-full">통계 보기</Button>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>시스템 설정</CardTitle>
              <CardDescription>시스템 설정을 관리합니다.</CardDescription>
            </CardHeader>
            <CardContent>
              <Button className="w-full">설정 관리</Button>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>로그</CardTitle>
              <CardDescription>시스템 로그를 확인합니다.</CardDescription>
            </CardHeader>
            <CardContent>
              <Button className="w-full">로그 보기</Button>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>CSV 데이터 관리</CardTitle>
              <CardDescription>영업일지와 회사 데이터를 CSV로 다운로드/업로드합니다.</CardDescription>
            </CardHeader>
            <CardContent>
              <Button 
                className="w-full"
                onClick={() => router.push('/admin/csv-management')}
              >
                CSV 관리
              </Button>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>매출 데이터 관리</CardTitle>
              <CardDescription>실제 매출 데이터를 CSV/XLSX/TSV 파일로 업로드하고 대시보드 차트에 반영합니다.</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                <Button 
                  className="w-full"
                  onClick={() => uploadSalesData()}
                >
                  매출 데이터 업로드 (CSV/XLSX/TSV)
                </Button>
                <p className="text-xs text-gray-500 text-center">
                  필수 컬럼: 매출일자, 거래처명, 매출금액, 매출부서, 매출담당자 등
                </p>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>SAP 거래처 업로드</CardTitle>
              <CardDescription>SAP 거래처 정보 TSV 파일을 업로드하여 기존 거래처를 업데이트하거나 신규 거래처를 추가합니다.</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                <Button 
                  className="w-full"
                  onClick={() => uploadSapCompanies()}
                >
                  SAP 거래처 업로드 (TSV)
                </Button>
                <p className="text-xs text-gray-500 text-center">
                  필수 컬럼: 고객, 고객번호1, 사업자등록번호 등
                </p>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
} 