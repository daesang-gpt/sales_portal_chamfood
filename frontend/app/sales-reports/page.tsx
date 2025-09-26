"use client"

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Search, Plus, Eye, Edit, Loader2, ChevronLeft, ChevronRight } from "lucide-react"
import Link from "next/link"
import { salesReportApi, SalesReport, PaginatedResponse } from "@/lib/api"
import { PaginationInput } from "@/components/ui/pagination"
import { useRouter, useSearchParams } from "next/navigation"

const PERIOD_OPTIONS = [
  { label: "1개월", value: "1m" },
  { label: "3개월", value: "3m" },
  { label: "6개월", value: "6m" },
  { label: "전체", value: "all" },
];

export default function SalesReportsPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const initialPage = Number(searchParams.get("page")) || 1;
  const [searchTerm, setSearchTerm] = useState("");
  const [period, setPeriod] = useState("all");
  const [currentPage, setCurrentPage] = useState(initialPage);
  const [reports, setReports] = useState<SalesReport[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [totalPages, setTotalPages] = useState(1);
  const [totalCount, setTotalCount] = useState(0);

  // 검색 버튼 클릭 시 API 호출
  const fetchReports = async (page = 1, search = searchTerm, periodValue = period) => {
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
      setReports((data as any).results);
      setTotalCount(data.count);
      setTotalPages(data.total_pages);
      setCurrentPage(data.current_page);
    } catch (err) {
      setError("영업일지를 불러오는 중 오류가 발생했습니다.");
    } finally {
      setLoading(false);
    }
  };

  // 최초 마운트 시 1회 호출
  useEffect(() => {
    fetchReports(1, searchTerm, period);
    // eslint-disable-next-line
  }, []);

  // 페이지 변경 시 API 호출
  useEffect(() => {
    if (currentPage !== initialPage) {
      fetchReports(currentPage, searchTerm, period);
      // URL 쿼리스트링 동기화
      const params = new URLSearchParams(searchParams.toString());
      params.set("page", String(currentPage));
      router.replace(`/sales-reports?${params.toString()}`);
    }
    // eslint-disable-next-line
  }, [currentPage]);

  // 기간 변경 시 API 호출
  useEffect(() => {
    fetchReports(1, searchTerm, period);
    setCurrentPage(1);
    // eslint-disable-next-line
  }, [period]);

  // 검색 버튼 클릭 핸들러
  const handleSearch = () => {
    fetchReports(1, searchTerm, period);
    setCurrentPage(1);
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
          <Button asChild>
            <Link href="/sales-reports/new">
              <Plus className="mr-2 h-4 w-4" />
              영업일지 작성
            </Link>
          </Button>
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
        <Button asChild>
          <Link href="/sales-reports/new">
            <Plus className="mr-2 h-4 w-4" />
            영업일지 작성
          </Link>
        </Button>
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
                value={searchTerm}
                onChange={e => setSearchTerm(e.target.value)}
                className="pl-8"
                onKeyDown={e => { if (e.key === 'Enter') handleSearch(); }}
              />
            </div>
            <Button onClick={handleSearch} variant="default">검색</Button>
            <div className="flex gap-2 ml-4">
              {PERIOD_OPTIONS.map(opt => (
                <Button
                  key={opt.value}
                  onClick={() => setPeriod(opt.value)}
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
              <Button asChild className="mt-4">
                <Link href="/sales-reports/new">
                  <Plus className="mr-2 h-4 w-4" />
                  첫 번째 영업일지 작성하기
                </Link>
              </Button>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>작성자</TableHead>
                  <TableHead>팀명</TableHead>
                  <TableHead>방문일자</TableHead>
                  <TableHead>회사명</TableHead>
                  <TableHead>영업형태</TableHead>
                  <TableHead>소재지</TableHead>
                  <TableHead>사용품목</TableHead>
                  <TableHead>태그</TableHead>
                  <TableHead>작업</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {reports.map((report: SalesReport) => {
                  const tagsArr = report.tags ? report.tags.split(',').filter((tag: string) => tag.trim()) : [];
                  const showTags = tagsArr.slice(0, 3);
                  return (
                    <TableRow key={report.id}>
                      <TableCell className="font-medium">{report.author_name}</TableCell>
                      <TableCell>{report.team_display}</TableCell>
                      <TableCell>{formatDate(report.visitDate)}</TableCell>
                      <TableCell>{report.company_display}</TableCell>
                      <TableCell>
                        <Badge variant={getTypeBadge(report.type)}>
                          {report.type}
                        </Badge>
                      </TableCell>
                      <TableCell>{report.location}</TableCell>
                      <TableCell>{report.products}</TableCell>
                      <TableCell>
                        <div className="flex gap-1 items-center">
                          {showTags.map((tag: string, index: number) => (
                            <Badge key={index} variant="outline" className="text-xs">
                              {tag.trim()}
                            </Badge>
                          ))}
                          {tagsArr.length > 3 && (
                            <span className="text-xs text-muted-foreground ml-1">...</span>
                          )}
                        </div>
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center space-x-2">
                          <Button variant="ghost" size="sm" asChild>
                            <Link href={`/sales-reports/${report.id}?page=${currentPage}`}>
                              <Eye className="h-4 w-4" />
                            </Link>
                          </Button>
                          <Button variant="ghost" size="sm" asChild>
                            <Link href={`/sales-reports/${report.id}/edit?page=${currentPage}`}>
                              <Edit className="h-4 w-4" />
                            </Link>
                          </Button>
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
  );
}
