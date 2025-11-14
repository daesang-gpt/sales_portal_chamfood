"use client"

import { useState, useEffect, useCallback } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Search, Plus, Building2, Loader2, ChevronLeft, ChevronRight } from "lucide-react"
import Link from "next/link"
import { companyApi, Company, CompanyFilters, PaginatedResponse } from "@/lib/api"
import { CompanyStats } from "@/lib/types/company"
import { PaginationInput } from "@/components/ui/pagination"
import { useRouter, useSearchParams } from "next/navigation"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { getUserFromToken } from "@/lib/auth"

export default function CompaniesPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  
  // URL의 page 파라미터를 단일 소스로 사용
  const currentPage = Number(searchParams.get("page")) || 1;
  const urlSearchTerm = searchParams.get("search") || "";
  const urlCustomerClassification = searchParams.get("customer_classification") || "";
  
  const [companies, setCompanies] = useState<Company[]>([])
  const [stats, setStats] = useState<CompanyStats>({
    total: 0,
    potentialCustomers: 0,
    newCustomers: 0,
    existingCustomers: 0,
    churnedCustomers: 0,
    filteredTotal: undefined,
    filteredPotentialCustomers: undefined,
    filteredNewCustomers: undefined,
    filteredExistingCustomers: undefined,
    filteredChurnedCustomers: undefined
  })
  // URL 파라미터에서 초기값 설정
  const [searchTerm, setSearchTerm] = useState(urlSearchTerm);
  const [pendingSearch, setPendingSearch] = useState(urlSearchTerm);
  const [customerClassification, setCustomerClassification] = useState(urlCustomerClassification);
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [totalPages, setTotalPages] = useState(1)
  const [totalCount, setTotalCount] = useState(0)
  const [isViewer, setIsViewer] = useState(false)

  // 통계 데이터만 별도로 로드
  const loadStats = async () => {
    try {
      const statsData = await companyApi.getCompanyStats()
      setStats(statsData)
    } catch (err) {
      console.error('Error loading stats:', err)
    }
  }

  // 회사 목록과 통계를 로드하는 함수
  const loadCompanies = useCallback(async (page: number, search: string, customerClassification: string) => {
    try {
      setLoading(true)
      setError(null)
      
      // 필터 객체 생성
      const filters: CompanyFilters = {
        search: search,
        ordering: '-company_code'
      };
      
      // 고객구분이 선택된 경우에만 필터에 추가
      if (customerClassification && customerClassification !== "전체") {
        filters.customer_classification = customerClassification;
      }
      
      // 회사 목록과 통계를 병렬로 로드
      const [companiesData, statsData] = await Promise.all([
        companyApi.getCompanies(filters, page),
        companyApi.getCompanyStats(search || undefined)
      ])
      
      setCompanies(companiesData.results)
      setTotalCount(companiesData.count)
      setTotalPages(Math.ceil(companiesData.count / 10))
      setStats(statsData)
    } catch (err) {
      setError('데이터를 불러오는 중 오류가 발생했습니다.')
      console.error('Error loading companies:', err)
    } finally {
      setLoading(false)
    }
  }, []);

  // URL의 page, searchTerm, customerClassification이 변경될 때마다 데이터 로드 (초기 로드, 브라우저 뒤로가기 포함)
  useEffect(() => {
    const user = getUserFromToken();
    setIsViewer(user?.role === 'viewer');
  }, []);

  useEffect(() => {
    loadCompanies(currentPage, searchTerm, customerClassification);
  }, [currentPage, searchTerm, customerClassification, loadCompanies]);

  // URL의 search 파라미터가 변경되면 로컬 상태 동기화
  useEffect(() => {
    if (urlSearchTerm !== searchTerm) {
      setSearchTerm(urlSearchTerm);
      setPendingSearch(urlSearchTerm);
    }
  }, [urlSearchTerm, searchTerm]);

  // URL의 customer_classification 파라미터가 변경되면 로컬 상태 동기화
  useEffect(() => {
    if (urlCustomerClassification !== customerClassification) {
      setCustomerClassification(urlCustomerClassification);
    }
  }, [urlCustomerClassification, customerClassification]);

  // 페이지 변경 핸들러 (URL만 업데이트)
  const handlePageChange = (page: number) => {
    const params = new URLSearchParams(searchParams.toString());
    params.set("page", String(page));
    router.replace(`/companies?${params.toString()}`);
  };

  // 검색 버튼 클릭 핸들러
  const handleSearch = () => {
    const params = new URLSearchParams(searchParams.toString());
    params.set("page", "1");
    if (pendingSearch.trim()) {
      params.set("search", pendingSearch.trim());
    } else {
      params.delete("search");
    }
    // 고객구분은 이미 URL에 있으므로 그대로 유지 (또는 별도로 설정)
    router.replace(`/companies?${params.toString()}`);
  };

  // 고객구분 변경 핸들러
  const handleCustomerClassificationChange = (value: string) => {
    const params = new URLSearchParams(searchParams.toString());
    params.set("page", "1");
    if (value && value !== "전체") {
      params.set("customer_classification", value);
    } else {
      params.delete("customer_classification");
    }
    router.replace(`/companies?${params.toString()}`);
  };

  // 통계 카드 클릭 핸들러
  const handleCardClick = (classification: string | null) => {
    const params = new URLSearchParams(searchParams.toString());
    params.set("page", "1");
    // 현재 검색어는 유지
    if (searchTerm) {
      params.set("search", searchTerm);
    }
    // 고객구분 필터 설정
    if (classification) {
      params.set("customer_classification", classification);
    } else {
      // "총 등록 회사" 카드 클릭 시 고객구분 필터 제거
      params.delete("customer_classification");
    }
    router.replace(`/companies?${params.toString()}`);
  };

  // 데이터 매핑 헬퍼 함수
  const getCompanyDisplayName = (company: Company) => {
    return company.company_name || 'Unknown Company'
  }
  const getSalesPersonName = (company: Company) => {
    return company.employee_name || '-';
  }

  const getCompanyRepresentative = (company: Company) => {
    return company.ceo_name || '-'
  }

  const getCompanyCustomerType = (company: Company) => {
    return company.customer_classification || '-'
  }

  const getCompanyCityDistrict = (company: Company) => {
    return company.city_district || '-'
  }

  const getCompanySapCodeType = (company: Company) => {
    return company.sap_code_type || '-'
  }

  const getCompanyStartDate = (company: Company) => {
    return company.transaction_start_date || '-'
  }

  const getSapCodeBadgeStyle = (sapCodeType: string) => {
    if (sapCodeType === "매출") {
      return "bg-black text-white border-black";
    } else if (sapCodeType === "매입") {
      return "bg-white text-black border border-gray-300";
    } else if (sapCodeType === "매입매출") {
      return "bg-gray-500 text-white border-gray-500";
    }
    return "";
  }

  const getCustomerTypeBadgeStyle = (customerType: string) => {
    if (customerType === "잠재") {
      return "bg-yellow-400 text-yellow-950 border-yellow-500 font-semibold";
    } else if (customerType === "기존") {
      return "bg-white text-gray-900 border-2 border-gray-400 font-semibold";
    } else if (customerType === "이탈") {
      return "bg-red-500 text-white border-red-600 font-semibold";
    } else if (customerType === "벤더") {
      return "bg-green-500 text-white border-green-600 font-semibold";
    } else if (customerType === "신규") {
      return "bg-blue-500 text-white border-blue-600 font-semibold";
    }
    return "";
  }

  if (loading && companies.length === 0) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="flex items-center space-x-2">
          <Loader2 className="h-6 w-6 animate-spin" />
          <span>데이터를 불러오는 중...</span>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <p className="text-red-500 mb-4">{error}</p>
          <Button onClick={() => loadCompanies(currentPage, searchTerm, customerClassification)}>다시 시도</Button>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold">회사 관리</h1>
        {!isViewer && (
          <Button asChild>
            <Link href="/companies/new">
              <Plus className="mr-2 h-4 w-4" />
              회사 등록
            </Link>
          </Button>
        )}
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-5">
        <Card 
          className="cursor-pointer hover:bg-muted/50 transition-colors"
          onClick={() => handleCardClick(null)}
        >
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">총 등록 회사</CardTitle>
            <Building2 className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {stats.total}개
              {searchTerm && stats.filteredTotal !== undefined && (
                <>
                  <br />
                  <span className="text-blue-600">검색결과: {stats.filteredTotal}개</span>
                </>
              )}
            </div>
            <p className="text-xs text-muted-foreground">전체 등록된 회사 수</p>
          </CardContent>
        </Card>

        <Card 
          className="cursor-pointer hover:bg-muted/50 transition-colors"
          onClick={() => handleCardClick('잠재')}
        >
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">잠재 거래처</CardTitle>
            <Badge className="h-4 w-4 bg-yellow-400 text-yellow-950 border-yellow-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {stats.potentialCustomers}개
              {searchTerm && stats.filteredPotentialCustomers !== undefined && (
                <>
                  <br />
                  <span className="text-blue-600">검색결과: {stats.filteredPotentialCustomers}개</span>
                </>
              )}
            </div>
            <p className="text-xs text-muted-foreground">SAP 거래처 등록 전, 컨택 업체</p>
          </CardContent>
        </Card>

        <Card 
          className="cursor-pointer hover:bg-muted/50 transition-colors"
          onClick={() => handleCardClick('신규')}
        >
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">신규 거래처</CardTitle>
            <Badge className="h-4 w-4 bg-blue-500 text-white border-blue-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {stats.newCustomers}개
              {searchTerm && stats.filteredNewCustomers !== undefined && (
                <>
                  <br />
                  <span className="text-blue-600">검색결과: {stats.filteredNewCustomers}개</span>
                </>
              )}
            </div>
            <p className="text-xs text-muted-foreground">SAP 등록일 기준 3개월 이내 업체</p>
          </CardContent>
        </Card>

        <Card 
          className="cursor-pointer hover:bg-muted/50 transition-colors"
          onClick={() => handleCardClick('기존')}
        >
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">기존 거래처</CardTitle>
            <Badge variant="secondary" className="h-4 w-4 bg-white text-gray-900 border-2 border-gray-400" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {stats.existingCustomers}개
              {searchTerm && stats.filteredExistingCustomers !== undefined && (
                <>
                  <br />
                  <span className="text-blue-600">검색결과: {stats.filteredExistingCustomers}개</span>
                </>
              )}
            </div>
            <p className="text-xs text-muted-foreground">SAP 등록일 기준 3개월 초과 업체</p>
          </CardContent>
        </Card>

        <Card 
          className="cursor-pointer hover:bg-muted/50 transition-colors"
          onClick={() => handleCardClick('이탈')}
        >
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">이탈 거래처</CardTitle>
            <Badge className="h-4 w-4 bg-red-500 text-white border-red-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {stats.churnedCustomers}개
              {searchTerm && stats.filteredChurnedCustomers !== undefined && (
                <>
                  <br />
                  <span className="text-blue-600">검색결과: {stats.filteredChurnedCustomers}개</span>
                </>
              )}
            </div>
            <p className="text-xs text-muted-foreground">마지막 거래일 3개월 초과 업체</p>
            <p className="text-xs text-muted-foreground">(SAP 등록 후 미거래 업체 포함)</p>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>회사 목록</CardTitle>
          <CardDescription>등록된 회사 정보를 확인하고 관리할 수 있습니다.</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center space-x-2 mb-4">
            <div className="relative flex-1">
              <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="회사명 또는 영업 사원으로 검색..."
                value={pendingSearch}
                onChange={e => setPendingSearch(e.target.value)}
                className="pl-8"
                onKeyDown={e => { if (e.key === 'Enter') handleSearch(); }}
              />
            </div>
            <Select value={customerClassification || "전체"} onValueChange={handleCustomerClassificationChange}>
              <SelectTrigger className="w-[180px]">
                <SelectValue placeholder="고객구분 선택" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="전체">전체</SelectItem>
                <SelectItem value="잠재">잠재</SelectItem>
                <SelectItem value="신규">신규</SelectItem>
                <SelectItem value="기존">기존</SelectItem>
                <SelectItem value="이탈">이탈</SelectItem>
                <SelectItem value="벤더">벤더</SelectItem>
              </SelectContent>
            </Select>
            <Button onClick={handleSearch} variant="default">검색</Button>
            {loading && <Loader2 className="h-4 w-4 animate-spin" />}
          </div>

          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>고객구분</TableHead>
                <TableHead>회사명</TableHead>
                <TableHead>시/구</TableHead>
                <TableHead>대표자</TableHead>
                <TableHead>영업 사원</TableHead>
                <TableHead>SAP코드여부</TableHead>
                <TableHead>거래개시일</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {companies.map((company) => (
                <TableRow 
                  key={company.company_code}
                  className="cursor-pointer hover:bg-muted/50"
                  onClick={() => {
                    const params = new URLSearchParams();
                    params.set("page", String(currentPage));
                    if (searchTerm) params.set("search", searchTerm);
                    if (customerClassification) params.set("customer_classification", customerClassification);
                    router.push(`/companies/${company.company_code}?${params.toString()}`);
                  }}
                >
                  <TableCell>
                    {(() => {
                      const customerType = getCompanyCustomerType(company);
                      const badgeStyle = getCustomerTypeBadgeStyle(customerType);
                      return (
                        <Badge 
                          variant="outline"
                          className={badgeStyle || undefined}
                        >
                          {customerType}
                        </Badge>
                      );
                    })()}
                  </TableCell>
                  <TableCell className="font-medium">
                    {getCompanyDisplayName(company)}
                  </TableCell>
                  <TableCell>{getCompanyCityDistrict(company)}</TableCell>
                  <TableCell>{getCompanyRepresentative(company)}</TableCell>
                  <TableCell>{getSalesPersonName(company)}</TableCell>
                  <TableCell>
                    {(() => {
                      const sapCodeType = getCompanySapCodeType(company);
                      return (
                        <Badge 
                          variant={sapCodeType === '-' ? "secondary" : "outline"}
                          className={getSapCodeBadgeStyle(sapCodeType) || undefined}
                        >
                          {sapCodeType}
                        </Badge>
                      );
                    })()}
                  </TableCell>
                  <TableCell>{getCompanyStartDate(company)}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
          
          {companies.length === 0 && !loading && (
            <div className="text-center py-8 text-muted-foreground">
              검색 결과가 없습니다.
            </div>
          )}

          {/* 페이지네이션 */}
          {companies.length > 0 && (
            <div className="flex items-center justify-between mt-6">
              <div className="text-sm text-muted-foreground">
                총 {totalCount}개의 회사 중 {(currentPage - 1) * 10 + 1}-{Math.min(currentPage * 10, totalCount)}번째
              </div>
              <div className="flex items-center space-x-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handlePageChange(Math.max(currentPage - 1, 1))}
                  disabled={currentPage === 1}
                >
                  <ChevronLeft className="h-4 w-4" />
                  이전
                </Button>
                
                <div className="flex items-center space-x-1">
                  {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                    let pageNum;
                    if (totalPages <= 5) {
                      pageNum = i + 1;
                    } else if (currentPage <= 3) {
                      pageNum = i + 1;
                    } else if (currentPage >= totalPages - 2) {
                      pageNum = totalPages - 4 + i;
                    } else {
                      pageNum = currentPage - 2 + i;
                    }
                    
                    return (
                      <Button
                        key={pageNum}
                        variant={currentPage === pageNum ? "default" : "outline"}
                        size="sm"
                        onClick={() => handlePageChange(pageNum)}
                        className="w-8 h-8 p-0"
                      >
                        {pageNum}
                      </Button>
                    );
                  })}
                </div>
                
                <PaginationInput
                  currentPage={currentPage}
                  totalPages={totalPages}
                  onPageChange={handlePageChange}
                />
                
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handlePageChange(Math.min(currentPage + 1, totalPages))}
                  disabled={currentPage === totalPages}
                >
                  다음
                  <ChevronRight className="h-4 w-4" />
                </Button>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
