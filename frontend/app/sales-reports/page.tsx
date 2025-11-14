"use client"

import { useState, useEffect, useCallback } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Search, Plus, Loader2, ChevronLeft, ChevronRight } from "lucide-react"
import Link from "next/link"
import { salesReportApi, SalesReport, PaginatedResponse } from "@/lib/api"
import { PaginationInput } from "@/components/ui/pagination"
import { useRouter, useSearchParams } from "next/navigation"
import { getUserFromToken } from "@/lib/auth"

const PERIOD_OPTIONS = [
  { label: "1개월", value: "1m" },
  { label: "3개월", value: "3m" },
  { label: "6개월", value: "6m" },
  { label: "전체", value: "all" },
];

export default function SalesReportsPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  
  // URL 파라미터에서 초기값 읽기
  const urlSearch = searchParams.get("search") || "";
  const urlPeriod = searchParams.get("period") || "all";
  
  const [inputValue, setInputValue] = useState(urlSearch);
  const [searchTerm, setSearchTerm] = useState(urlSearch);
  const [period, setPeriod] = useState(urlPeriod);
  
  // URL의 page 파라미터를 단일 소스로 사용
  const currentPage = Number(searchParams.get("page")) || 1;
  const [reports, setReports] = useState<SalesReport[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [totalPages, setTotalPages] = useState(1);
  const [totalCount, setTotalCount] = useState(0);
  const [isViewer, setIsViewer] = useState(false);

  // API 호출 함수
  const fetchReports = useCallback(async (page: number, search: string = searchTerm, periodValue: string = period) => {
    setLoading(true);
    setError(null);
    try {
      const data = await salesReportApi.getReports({
        page,
        page_size: 10,
        search: search.trim() ? search : undefined,
        period: periodValue,
        ordering: "-visitDate",
      });
      setReports(data.results);
      setTotalCount(data.count);
      setTotalPages(data.total_pages);
    } catch (err) {
      setError("영업일지를 불러오는 중 오류가 발생했습니다.");
    } finally {
      setLoading(false);
    }
  }, [searchTerm, period]);

  // URL 파라미터 변경 시 상태 동기화
  useEffect(() => {
    const urlSearch = searchParams.get("search");
    const urlPeriod = searchParams.get("period");
    
    // 검색어 동기화
    if (urlSearch) {
      setInputValue(urlSearch);
      setSearchTerm(urlSearch);
    } else {
      // URL에 검색어가 없으면 초기화
      setInputValue("");
      setSearchTerm("");
    }
    
    // 기간 동기화
    if (urlPeriod && PERIOD_OPTIONS.some(opt => opt.value === urlPeriod)) {
      setPeriod(urlPeriod);
    } else {
      setPeriod("all");
    }
  }, [searchParams]);

  // URL의 page 파라미터가 변경될 때마다 데이터 로드 (초기 로드, 브라우저 뒤로가기 포함)
  useEffect(() => {
    const user = getUserFromToken();
    setIsViewer(user?.role === 'viewer');
  }, []);

  useEffect(() => {
    fetchReports(currentPage, searchTerm, period);
  }, [currentPage, searchTerm, period, fetchReports]);

  // 페이지 변경 핸들러 (URL만 업데이트)
  const handlePageChange = (page: number) => {
    const params = new URLSearchParams();
    params.set("page", String(page));
    if (searchTerm.trim()) {
      params.set("search", searchTerm.trim());
    }
    if (period !== "all") {
      params.set("period", period);
    }
    router.replace(`/sales-reports?${params.toString()}`);
  };

  // 기간 변경 핸들러
  const handlePeriodChange = (periodValue: string) => {
    setPeriod(periodValue);
    setInputValue("");
    setSearchTerm("");
    const params = new URLSearchParams();
    params.set("page", "1");
    if (periodValue !== "all") {
      params.set("period", periodValue);
    }
    router.replace(`/sales-reports?${params.toString()}`);
  };

  // 검색 버튼 클릭 핸들러
  const handleSearch = () => {
    setSearchTerm(inputValue);
    const params = new URLSearchParams();
    params.set("page", "1");
    if (inputValue.trim()) {
      params.set("search", inputValue.trim());
    }
    if (period !== "all") {
      params.set("period", period);
    }
    router.replace(`/sales-reports?${params.toString()}`);
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('ko-KR');
  };

  const getTypeBadge = (type: string) => {
    const variants: Record<string, "default" | "secondary" | "outline"> = {
      '대면': 'default',
      '전화': 'secondary',
      '화상': 'outline',
      '이메일': 'outline',
    };
    return variants[type] || 'outline';
  };

  const getSalesStageStyle = (stage: string | null | undefined) => {
    if (!stage) {
      return 'bg-gray-100 text-gray-600';
    }
    
    const stageStyles: Record<string, string> = {
      '초기 컨택': 'bg-gradient-to-r from-gray-50 to-gray-100 text-gray-700 border-gray-200',
      '협상 진행(니즈 파악)': 'bg-gradient-to-r from-gray-200 to-gray-300 text-gray-800 border-gray-300',
      '계약 체결(거래처 등록)': 'bg-gradient-to-r from-gray-300 to-gray-400 text-gray-900 border-gray-400',
      '납품 관리': 'bg-gradient-to-r from-gray-500 to-gray-600 text-white border-gray-600',
      '관계 유지': 'bg-gradient-to-r from-gray-700 to-gray-800 text-white border-gray-800',
    };
    
    return stageStyles[stage] || 'bg-gray-100 text-gray-600';
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="flex items-center space-x-2">
          <Loader2 className="h-6 w-6 animate-spin" />
          <span>영업일지를 불러오는 중...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <h1 className="text-3xl font-bold">영업일지 관리</h1>
          {!isViewer && (
          <Button asChild>
            <Link href="/sales-reports/new">
              <Plus className="mr-2 h-4 w-4" />
              영업일지 작성
            </Link>
          </Button>
          )}
        </div>
        <Card>
          <CardContent className="flex items-center justify-center min-h-[200px]">
            <div className="text-center">
              <p className="text-red-600 mb-4">{error}</p>
              <Button onClick={() => fetchReports(currentPage, searchTerm, period)} variant="outline">
                다시 시도
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold">영업일지 관리</h1>
        {!isViewer && (
        <Button asChild>
          <Link href="/sales-reports/new">
            <Plus className="mr-2 h-4 w-4" />
            영업일지 작성
          </Link>
        </Button>
        )}
      </div>
      <Card>
        <CardHeader>
          <CardTitle>영업일지 목록</CardTitle>
          <CardDescription>등록된 영업일지를 확인하고 관리할 수 있습니다.</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center space-x-2 mb-4">
            <div className="relative flex-1">
              <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="회사명, 작성자 또는 태그로 검색..."
                value={inputValue}
                onChange={e => setInputValue(e.target.value)}
                className="pl-8"
                onKeyDown={e => { if (e.key === 'Enter') handleSearch(); }}
              />
            </div>
            <Button onClick={handleSearch} variant="default">검색</Button>
            <div className="flex gap-2 ml-4">
              {PERIOD_OPTIONS.map(opt => (
                <Button
                  key={opt.value}
                  onClick={() => handlePeriodChange(opt.value)}
                  variant={period === opt.value ? "default" : "outline"}
                >
                  {opt.label}
                </Button>
              ))}
            </div>
          </div>
          {reports.length === 0 ? (
            <div className="text-center py-8">
              <p className="text-muted-foreground">등록된 영업일지가 없습니다.</p>
              {!isViewer && (
              <Button asChild className="mt-4">
                <Link href="/sales-reports/new">
                  <Plus className="mr-2 h-4 w-4" />
                  첫 번째 영업일지 작성하기
                </Link>
              </Button>
              )}
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>작성자</TableHead>
                  <TableHead>팀명</TableHead>
                  <TableHead>방문일자</TableHead>
                  <TableHead>회사명</TableHead>
                  <TableHead>영업형태 / 영업단계</TableHead>
                  <TableHead>태그</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {reports.map((report: SalesReport) => {
                  const tagsArr = report.tags ? report.tags.split(',').filter((tag: string) => tag.trim()) : [];
                  const showTags = tagsArr.slice(0, 3);
                  return (
                    <TableRow 
                      key={report.id}
                      className="cursor-pointer hover:bg-muted/50"
                      onClick={() => router.push(`/sales-reports/${report.id}?page=${currentPage}`)}
                    >
                      <TableCell className="font-medium">{report.author_name}</TableCell>
                      <TableCell>{report.author_department}</TableCell>
                      <TableCell>{formatDate(report.visitDate)}</TableCell>
                      <TableCell>{report.company_display || report.company_name || '-'}</TableCell>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          <Badge variant={getTypeBadge(report.type)}>
                            {report.type}
                          </Badge>
                          <Badge 
                            variant="outline" 
                            className={`${getSalesStageStyle(report.sales_stage)} border`}
                          >
                            {report.sales_stage || '미지정'}
                          </Badge>
                        </div>
                      </TableCell>
                      <TableCell>
                        <div className="flex gap-1 items-center">
                          {tagsArr.length > 0 ? (
                            <>
                              {showTags.map((tag: string, index: number) => (
                                <Badge key={index} variant="outline" className="text-xs">
                                  {tag.trim()}
                                </Badge>
                              ))}
                              {tagsArr.length > 3 && (
                                <span className="text-xs text-muted-foreground ml-1">...</span>
                              )}
                            </>
                          ) : (
                            <Badge variant="outline" className="text-xs">
                              없음
                            </Badge>
                          )}
                        </div>
                      </TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          )}
          {/* 페이지네이션 */}
          {reports.length > 0 && (
            <div className="flex items-center justify-between mt-6">
              <div className="text-sm text-muted-foreground">
                총 {totalCount}개의 영업일지 중 {(currentPage - 1) * 10 + 1}-{Math.min(currentPage * 10, totalCount)}번째
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
  );
}
