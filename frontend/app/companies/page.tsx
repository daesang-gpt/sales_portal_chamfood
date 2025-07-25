"use client"

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Search, Plus, Eye, Building2, Phone, Loader2, ChevronLeft, ChevronRight } from "lucide-react"
import Link from "next/link"
import { companyApi, Company, CompanyFilters, PaginatedResponse } from "@/lib/api"
import { PaginationInput } from "@/components/ui/pagination"
import { useRouter, useSearchParams } from "next/navigation"
// User 타입 정의 (간단히 id, name만 사용)
// type User = { id: number; name: string };

export default function CompaniesPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const initialPage = Number(searchParams.get("page")) || 1;
  const [companies, setCompanies] = useState<Company[]>([])
  const [stats, setStats] = useState({
    total: 0,
    newCustomers: 0,
    existingCustomers: 0,
    thisMonthNew: 0
  })
  const [searchTerm, setSearchTerm] = useState("");
  const [pendingSearch, setPendingSearch] = useState("");
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [currentPage, setCurrentPage] = useState(initialPage)
  const [totalPages, setTotalPages] = useState(1)
  const [totalCount, setTotalCount] = useState(0)
  // const [users, setUsers] = useState<User[]>([]);

  // 데이터 로드
  const loadData = async (page: number = 1) => {
    try {
      setLoading(true)
      setError(null)
      
      // 회사 목록과 통계를 병렬로 로드
      const [companiesData, statsData] = await Promise.all([
        companyApi.getCompanies({ search: searchTerm }, page),
        companyApi.getCompanyStats()
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
  }

  // 통계 데이터만 별도로 로드
  const loadStats = async () => {
    try {
      const statsData = await companyApi.getCompanyStats()
      setStats(statsData)
    } catch (err) {
      console.error('Error loading stats:', err)
    }
  }

  // 초기 로드
  useEffect(() => {
    loadData(currentPage)
  }, [])

  // 페이지 변경, 검색어 변경 시 회사 목록만 로드
  useEffect(() => {
    const loadCompanies = async () => {
      try {
        setLoading(true)
        setError(null)
        const companiesData = await companyApi.getCompanies({ search: searchTerm }, currentPage)
        setCompanies(companiesData.results)
        setTotalCount(companiesData.count)
        setTotalPages(Math.ceil(companiesData.count / 10))
      } catch (err) {
        setError('데이터를 불러오는 중 오류가 발생했습니다.')
        console.error('Error loading companies:', err)
      } finally {
        setLoading(false)
      }
    }
    loadCompanies()
  }, [currentPage, searchTerm])

  // 페이지네이션, 검색어 쿼리스트링 동기화
  useEffect(() => {
    const params = new URLSearchParams(searchParams.toString());
    params.set("page", String(currentPage));
    if (searchTerm) {
      params.set("search", searchTerm);
    } else {
      params.delete("search");
    }
    router.replace(`/companies?${params.toString()}`);
    // eslint-disable-next-line
  }, [currentPage, searchTerm]);

  // 검색 버튼 또는 엔터로만 검색 실행
  useEffect(() => {
    if (searchTerm !== "") {
      const params = new URLSearchParams(searchParams.toString());
      params.set("page", "1");
      router.replace(`/companies?${params.toString()}`);
    }
    // eslint-disable-next-line
  }, [searchTerm]);

  const handleSearch = () => {
    setSearchTerm(pendingSearch);
    setCurrentPage(1);
  };

  // 데이터 매핑 헬퍼 함수
  const getCompanyDisplayName = (company: Company) => {
    return company.company_name || 'Unknown Company'
  }
  const getSalesPersonName = (company: Company) => {
    return company.username_display || '-';
  }

  const getCompanyType = (company: Company) => {
    return company.company_type || '-'
  }

  const getCompanyRepresentative = (company: Company) => {
    return company.ceo_name || '-'
  }

  const getCompanyContact = (company: Company) => {
    return company.main_phone || company.contact_phone || '-'
  }

  const getCompanyCustomerType = (company: Company) => {
    return company.customer_classification || '-'
  }

  const getCompanyStartDate = (company: Company) => {
    return company.transaction_start_date || '-'
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
          <Button onClick={() => loadData(currentPage)}>다시 시도</Button>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold">회사 관리</h1>
        <Button asChild>
          <Link href="/companies/new">
            <Plus className="mr-2 h-4 w-4" />
            회사 등록
          </Link>
        </Button>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">총 등록 회사</CardTitle>
            <Building2 className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.total}개사</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">신규 고객사</CardTitle>
            <Badge className="h-4 w-4" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.newCustomers}개사</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">기존 고객사</CardTitle>
            <Badge variant="secondary" className="h-4 w-4" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.existingCustomers}개사</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">이번 달 신규</CardTitle>
            <Plus className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.thisMonthNew}개사</div>
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
            <Button onClick={handleSearch} variant="default">검색</Button>
            {loading && <Loader2 className="h-4 w-4 animate-spin" />}
          </div>

          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>회사명</TableHead>
                <TableHead>영업 사원</TableHead>
                <TableHead>기업형태</TableHead>
                <TableHead>대표자</TableHead>
                <TableHead>연락처</TableHead>
                <TableHead>고객구분</TableHead>
                <TableHead>거래개시일</TableHead>
                <TableHead>작업</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {companies.map((company) => (
                <TableRow key={company.id}>
                  <TableCell className="font-medium">
                    {getCompanyDisplayName(company)}
                  </TableCell>
                  <TableCell>{getSalesPersonName(company)}</TableCell>
                  <TableCell>{getCompanyType(company)}</TableCell>
                  <TableCell>{getCompanyRepresentative(company)}</TableCell>
                  <TableCell>
                    <div className="flex items-center space-x-1">
                      <Phone className="h-3 w-3" />
                      <span className="text-sm">{getCompanyContact(company)}</span>
                    </div>
                  </TableCell>
                  <TableCell>
                    <Badge variant={getCompanyCustomerType(company) === "신규" ? "default" : "secondary"}>
                      {getCompanyCustomerType(company)}
                    </Badge>
                  </TableCell>
                  <TableCell>{getCompanyStartDate(company)}</TableCell>
                  <TableCell>
                    <Button variant="ghost" size="sm" asChild>
                      <Link href={`/companies/${company.id}`}>
                        <Eye className="h-4 w-4" />
                      </Link>
                    </Button>
                  </TableCell>
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
                  onClick={() => setCurrentPage(prev => Math.max(prev - 1, 1))}
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
                        onClick={() => setCurrentPage(pageNum)}
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
                  onPageChange={setCurrentPage}
                />
                
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setCurrentPage(prev => Math.min(prev + 1, totalPages))}
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
