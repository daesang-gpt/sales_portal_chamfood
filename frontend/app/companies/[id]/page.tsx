"use client"

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Separator } from "@/components/ui/separator"
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar, ComposedChart } from "recharts"
import { ArrowLeft, Edit, Building2, Phone, MapPin, Calendar, DollarSign, Loader2 } from "lucide-react"
import Link from "next/link"
import { useParams, useRouter } from "next/navigation"
import { companyApi, Company, salesReportApi, SalesReport } from "@/lib/api"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { isAdmin } from "@/lib/auth"
import { toast } from "@/hooks/use-toast"
import { companyFinancialStatusApi, CompanyFinancialStatus } from '@/lib/api'

export default function CompanyDetailPage() {
  const params = useParams()
  const [company, setCompany] = useState<Company | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  // const [users, setUsers] = useState<User[]>([]);
  const router = useRouter();
  const [isAdminUser, setIsAdminUser] = useState(false);
  const [financialStatus, setFinancialStatus] = useState<CompanyFinancialStatus[]>([]);

  useEffect(() => {
    const loadCompany = async () => {
      try {
        setLoading(true)
        setError(null)
        const companyData = await companyApi.getCompany(Number(params.id))
        setCompany(companyData)
      } catch (err) {
        setError('회사 정보를 불러오는 중 오류가 발생했습니다.')
        console.error('Error loading company:', err)
      } finally {
        setLoading(false)
      }
    }

    if (params.id) {
      loadCompany()
      setIsAdminUser(isAdmin());
    }
  }, [params.id])

  useEffect(() => {
    // 회사매출현황 불러오기
    console.log("useEffect - company?.sales_diary_company_code", company?.sales_diary_company_code); // 추가

    const fetchFinancialStatus = async () => {
      if (!company?.sales_diary_company_code) return;
      try {
        const data = await companyFinancialStatusApi.getByCompanyCode(company.sales_diary_company_code);
        const list = Array.isArray(data) ? data : (data as any).results;
        setFinancialStatus(list.sort((a: any, b: any) => b.fiscal_year.localeCompare(a.fiscal_year)));
        console.log("setFinancialStatus", data); // 추가

      } catch (e) {
        setFinancialStatus([]);
        console.log("setFinancialStatus error", e); // 추가
      }
    };
    if (company?.sales_diary_company_code) {
      fetchFinancialStatus();
    }
  }, [company?.sales_diary_company_code]);

  // 데이터 매핑 헬퍼 함수
  const getCompanyDisplayName = (company: Company) => {
    return company.company_name || 'Unknown Company'
  }

  const getCompanyCode = (company: Company) => {
    return company.sales_diary_company_code || '-'
  }

  const getCompanySapCode = (company: Company) => {
    return company.company_code_sap || '-'
  }

  const getCompanyType = (company: Company) => {
    return company.company_type || '-'
  }

  const getCompanyEstablishDate = (company: Company) => {
    return company.established_date || '-'
  }

  const getCompanyRepresentative = (company: Company) => {
    return company.ceo_name || '-'
  }

  const getCompanyAddress = (company: Company) => {
    return company.address || '-'
  }

  const getCompanyContact = (company: Company) => {
    return company.main_phone || company.contact_phone || '-'
  }

  const getCompanyManager = (company: Company) => {
    return company.contact_person || '-'
  }

  const getCompanyManagerPhone = (company: Company) => {
    return company.contact_phone || '-'
  }

  const getCompanyDistributionType = (company: Company) => {
    return company.distribution_type_sap || '-'
  }

  const getCompanyMainProducts = (company: Company) => {
    return company.main_product || '-'
  }

  const getCompanyStartDate = (company: Company) => {
    return company.transaction_start_date || '-'
  }

  const getCompanyPaymentTerms = (company: Company) => {
    return company.payment_terms || '-'
  }

  const getCompanyCustomerType = (company: Company) => {
    return company.customer_classification || '-'
  }

  const getCompanyNotes = (company: Company) => {
    return company.remarks || '-'
  }

  const getSalesPersonName = (company: Company) => {
    return company.username_display || '-';
  }

  // 회사 삭제 함수
  const handleDelete = async () => {
    if (!company) return;
    if (!window.confirm('정말로 이 회사를 삭제하시겠습니까?')) return;
    try {
      setLoading(true);
      await companyApi.deleteCompany(company.id);
      toast({ title: '삭제 완료', description: '회사가 삭제되었습니다.' });
      router.push('/companies');
    } catch (err: any) {
      let msg = '회사 삭제 중 오류가 발생했습니다.';
      // Error 객체이면서 message가 있으면 그대로 사용
      if (err instanceof Error && err.message) {
        msg = err.message;
      }
      // Error 객체가 아니고 error 필드가 있으면 사용
      else if (err && typeof err === 'object' && 'error' in err) {
        msg = (err as any).error;
      }
      // 그래도 없으면 전체 stringify
      else if (err) {
        msg = JSON.stringify(err);
      }
      toast({ title: '삭제 불가', description: msg, variant: 'destructive' });
      alert(msg);
    } finally {
      setLoading(false);
    }
  };

  // 그래프 데이터 변환
  const assetChartData = financialStatus.map(f => ({
    year: f.fiscal_year.slice(0,4),
    총자산: f.total_assets,
    자본금: f.capital,
    자본총계: f.total_equity,
  })).reverse();
  const profitChartData = financialStatus.map(f => ({
    year: f.fiscal_year.slice(0,4),
    매출액: f.revenue,
    영업이익: f.operating_income,
    당기순이익: f.net_income,
  })).reverse();

  console.log('assetChartData', assetChartData);
  console.log('profitChartData', profitChartData);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="flex items-center space-x-2">
          <Loader2 className="h-6 w-6 animate-spin" />
          <span>회사 정보를 불러오는 중...</span>
        </div>
      </div>
    )
  }

  if (error || !company) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <p className="text-red-500 mb-4">{error || '회사 정보를 찾을 수 없습니다.'}</p>
          <Button asChild>
            <Link href="/companies">목록으로 돌아가기</Link>
          </Button>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <Button variant="outline" size="sm" asChild>
            <Link href="/companies">
              <ArrowLeft className="mr-2 h-4 w-4" />
              목록으로
            </Link>
          </Button>
          <h1 className="text-3xl font-bold">{getCompanyDisplayName(company)}</h1>
          <Badge variant={getCompanyCustomerType(company) === "신규" ? "default" : "secondary"}>
            {getCompanyCustomerType(company)}
          </Badge>
        </div>
        <div className="flex gap-2">
          <Button asChild>
            <Link href={`/companies/${company.id}/edit`}>
              <Edit className="mr-2 h-4 w-4" />
              수정
            </Link>
          </Button>
          {isAdminUser && company && (
            <Button variant="destructive" onClick={handleDelete}>
              삭제
            </Button>
          )}
        </div>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        {/* 회사 기본 정보 */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Building2 className="h-5 w-5" />
              <span>기본 정보</span>
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4 text-base text-gray-800">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-sm font-medium text-muted-foreground">회사코드</p>
                <p className="text-lg">{getCompanyCode(company)}</p>
              </div>
              <div>
                <p className="text-sm font-medium text-muted-foreground">SAP코드</p>
                <p className="text-lg">{getCompanySapCode(company)}</p>
              </div>
              <div>
                <p className="text-sm font-medium text-muted-foreground">기업형태</p>
                <p className="text-lg">{getCompanyType(company)}</p>
              </div>
              <div>
                <p className="text-sm font-medium text-muted-foreground">설립일</p>
                <p className="text-lg">{getCompanyEstablishDate(company)}</p>
              </div>
              <div>
                <p className="text-sm font-medium text-muted-foreground">영업 사원</p>
                <p className="text-lg">{getSalesPersonName(company)}</p>
              </div>
            </div>

            <Separator />

            <div>
              <p className="text-sm font-medium text-muted-foreground mb-1">대표자명</p>
              <p className="text-lg">{getCompanyRepresentative(company)}</p>
            </div>

            <div>
              <p className="text-sm font-medium text-muted-foreground mb-1">주소</p>
              <div className="flex items-start space-x-2">
                <MapPin className="h-4 w-4 mt-1 text-muted-foreground" />
                <p className="text-lg">{getCompanyAddress(company)}</p>
              </div>
            </div>

            <div>
              <p className="text-sm font-medium text-muted-foreground mb-1">대표번호</p>
              <div className="flex items-center space-x-2">
                <Phone className="h-4 w-4 text-muted-foreground" />
                <p className="text-lg">{getCompanyContact(company)}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* 거래 정보 */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <DollarSign className="h-5 w-5" />
              <span>거래 정보</span>
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4 text-base text-gray-800">
            <div>
              <p className="text-sm font-medium text-muted-foreground mb-1">담당자</p>
              <p className="text-lg">{getCompanyManager(company)}</p>
            </div>

            <div>
              <p className="text-sm font-medium text-muted-foreground mb-1">담당자 연락처</p>
              <div className="flex items-center space-x-2">
                <Phone className="h-4 w-4 text-muted-foreground" />
                <p className="text-lg">{getCompanyManagerPhone(company)}</p>
              </div>
            </div>

            <div>
              <p className="text-sm font-medium text-muted-foreground mb-1">유통형태</p>
              <p className="text-lg">{getCompanyDistributionType(company)}</p>
            </div>

            <div>
              <p className="text-sm font-medium text-muted-foreground mb-1">주생산품</p>
              <p className="text-lg">{getCompanyMainProducts(company)}</p>
            </div>

            <div>
              <p className="text-sm font-medium text-muted-foreground mb-1">거래개시일</p>
              <div className="flex items-center space-x-2">
                <Calendar className="h-4 w-4 text-muted-foreground" />
                <p className="text-lg">{getCompanyStartDate(company)}</p>
              </div>
            </div>

            <div>
              <p className="text-sm font-medium text-muted-foreground mb-1">지급조건</p>
              <p className="text-lg">{getCompanyPaymentTerms(company)}</p>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* 매출 차트 */}
      <div className="grid gap-6 md:grid-cols-2">
        {/* 최근자산규모 그래프 */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle>최근자산규모</CardTitle>
            <span className="text-xs text-muted-foreground">(단위: 천원)</span>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={assetChartData} barCategoryGap={20}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="year" />
                <YAxis tickFormatter={v => v.toLocaleString()} width={80} minTickGap={2} tickMargin={8} />
                <Tooltip formatter={(v: number) => v.toLocaleString()} />
                <Bar dataKey="총자산" fill="#1B3A5D" />
                <Bar dataKey="자본금" fill="#4B2991" />
                <Bar dataKey="자본총계" fill="#15803D" />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
        {/* 최근영업실적 그래프 */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle>최근영업실적</CardTitle>
            <span className="text-xs text-muted-foreground">(단위: 천원)</span>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={220}>
              <ComposedChart data={profitChartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f1f1f1" />
                <XAxis 
                  dataKey="year" 
                  tickFormatter={(value) => `${value}년`}
                  style={{ fontSize: '12px', fill: '#666' }}
                />
                <YAxis 
                  yAxisId="left"
                  tickFormatter={(value) => value.toLocaleString()}
                  style={{ fontSize: '11px', fill: '#666' }}
                  label={{ value: '매출액 (천원)', angle: -90, position: 'insideLeft', style: { textAnchor: 'middle', fill: '#4F9DDE', fontSize: '12px' } }}
                />
                <YAxis 
                  yAxisId="right" 
                  orientation="right"
                  tickFormatter={(value) => value.toLocaleString()}
                  style={{ fontSize: '11px', fill: '#666' }}
                  label={{ value: '이익 (천원)', angle: 90, position: 'insideRight', style: { textAnchor: 'middle', fill: '#2ca02c', fontSize: '12px' } }}
                />
                <Tooltip 
                  formatter={(value: number, name: string) => [value.toLocaleString() + ' 천원', name]}
                  labelFormatter={(label) => `${label}년`}
                />
                {/* 순서: 매출액(Bar) - 영업이익(Line) - 당기순이익(Line) */}
                <Bar 
                  dataKey="매출액" 
                  fill="#4F9DDE" 
                  yAxisId="left"
                  radius={[4, 4, 0, 0]}
                />
                <Line 
                  type="monotone" 
                  dataKey="영업이익" 
                  stroke="#2ca02c" 
                  strokeWidth={3}
                  yAxisId="right"
                  dot={{ fill: '#2ca02c', strokeWidth: 2, r: 4 }}
                />
                <Line 
                  type="monotone" 
                  dataKey="당기순이익" 
                  stroke="#ff7f0e" 
                  strokeWidth={3}
                  yAxisId="right"
                  dot={{ fill: '#ff7f0e', strokeWidth: 2, r: 4 }}
                />
              </ComposedChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      {/* 참고사항 */}
      {getCompanyNotes(company) !== '-' && (
        <Card>
          <CardHeader>
            <CardTitle>참고사항</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-lg">{getCompanyNotes(company)}</p>
          </CardContent>
        </Card>
      )}

      {/* 영업일지 리스트 */}
      <CompanySalesReportList companyId={company.sales_diary_company_code || ""} />
    </div>
  )
}

function CompanySalesReportList({ companyId }: { companyId: string }) {
  const [reports, setReports] = useState<SalesReport[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showAll, setShowAll] = useState(false);
  const router = useRouter();

  useEffect(() => {
    const fetchReports = async () => {
      setLoading(true);
      setError(null);
      try {
        const data = await salesReportApi.getReports({
          companyId,
          ordering: "-visitDate",
          page_size: 100,
        });
        setReports((data as any).results);
      } catch (err) {
        setError("영업일지 리스트를 불러오는 중 오류가 발생했습니다.");
      } finally {
        setLoading(false);
      }
    };
    if (companyId) fetchReports();
  }, [companyId]);

  return (
    <div className="mt-10">
      <h2 className="text-xl font-bold mb-4">영업일지 리스트</h2>
      {loading ? (
        <div className="flex items-center space-x-2 text-muted-foreground"><Loader2 className="h-5 w-5 animate-spin" /> 불러오는 중...</div>
      ) : error ? (
        <div className="text-red-600">{error}</div>
      ) : reports.length === 0 ? (
        <div className="text-muted-foreground">등록된 영업일지가 없습니다.</div>
      ) : (
        <Card className="bg-white">
          <CardContent className="p-0 text-base text-gray-800">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>방문일자</TableHead>
                  <TableHead>미팅 내용(이슈사항)</TableHead>
                  <TableHead>작성자</TableHead>
                  <TableHead>영업형태</TableHead>
                  <TableHead className="text-center">상세보기</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {(showAll ? reports : reports.slice(0, 10)).map((r) => (
                  <TableRow key={r.id} className="hover:bg-gray-50 cursor-pointer" onClick={() => router.push(`/sales-reports/${r.id}`)}>
                    <TableCell>{new Date(r.visitDate).toLocaleDateString('ko-KR')}</TableCell>
                    <TableCell>{r.content.slice(0, 40)}{r.content.length > 40 ? '...' : ''}</TableCell>
                    <TableCell>{r.author_name}</TableCell>
                    <TableCell><Badge variant={r.type === "대면" ? "default" : "secondary"}>{r.type}</Badge></TableCell>
                    <TableCell className="text-center"><Button size="sm" variant="outline" onClick={e => {e.stopPropagation(); router.push(`/sales-reports/${r.id}`)}}>상세보기</Button></TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
            {reports.length > 10 && !showAll && (
              <div className="flex justify-end mt-2">
                <Button size="sm" variant="ghost" onClick={() => setShowAll(true)}>더 보기</Button>
              </div>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  );
}
