"use client"

import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Separator } from "@/components/ui/separator"
import { ArrowLeft, ArrowRight, Edit, Loader2, Trash2 } from "lucide-react"
import Link from "next/link"
import { useParams, useRouter, useSearchParams } from "next/navigation"
import { useEffect, useState } from "react"
import { salesReportApi, SalesReport } from "@/lib/api"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"

export default function SalesReportDetailPage() {
  const params = useParams()
  const router = useRouter()
  const searchParams = useSearchParams();
  const page = searchParams.get("page") || "1";
  const [report, setReport] = useState<SalesReport | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [deleting, setDeleting] = useState(false)
  const [otherReports, setOtherReports] = useState<SalesReport[]>([])
  const [showAll, setShowAll] = useState(false)
  const [otherLoading, setOtherLoading] = useState(false)
  const [otherError, setOtherError] = useState<string | null>(null)

  useEffect(() => {
    const fetchReport = async () => {
      try {
        setLoading(true)
        const reportData = await salesReportApi.getReport(Number(params.id))
        console.log('[영업일지 상세] 영업일지 데이터:', reportData);
        console.log('[영업일지 상세] company_code:', reportData.company_code);
        console.log('[영업일지 상세] company_code_resolved:', (reportData as any).company_code_resolved);
        console.log('[영업일지 상세] company_obj:', (reportData as any).company_obj);
        setReport(reportData)
      } catch (err) {
        console.error('[영업일지 상세] 오류:', err);
        setError(err instanceof Error ? err.message : '영업일지를 불러오는데 실패했습니다.')
      } finally {
        setLoading(false)
      }
    }

    if (params.id) {
      fetchReport()
    }
  }, [params.id])

  // 같은 회사의 다른 영업일지 불러오기
  useEffect(() => {
    const fetchOtherReports = async () => {
      if (!report) return;
      
      // company_code 확인 (다양한 필드에서 시도)
      const companyCode = report.company_code || (report as any).company_code_resolved || null;
      if (!companyCode) {
        console.warn('영업일지에 company_code가 없습니다:', report);
        setOtherError("회사 정보를 찾을 수 없어 영업일지 리스트를 불러올 수 없습니다.")
        setOtherLoading(false)
        return;
      }
      
      setOtherLoading(true)
      setOtherError(null)
      try {
        console.log('영업일지 리스트 조회:', { companyId: companyCode });
        const data = await salesReportApi.getReports({
          companyId: companyCode,
          ordering: "-visitDate",
          page_size: 100, // 충분히 크게 받아서 10개만 보여줌
        })
        console.log('영업일지 리스트 응답:', data);
        setOtherReports((data as any).results || [])
      } catch (err) {
        console.error('영업일지 리스트 조회 오류:', err);
        setOtherError("같은 회사의 영업일지를 불러오는 중 오류가 발생했습니다.")
      } finally {
        setOtherLoading(false)
      }
    }
    if (report) {
      fetchOtherReports()
    }
  }, [report])


  const handleDelete = async () => {
    if (!report) return
    
    if (!confirm('정말로 이 영업일지를 삭제하시겠습니까? 이 작업은 되돌릴 수 없습니다.')) {
      return
    }

    try {
      setDeleting(true)
      await salesReportApi.deleteReport(report.id)
      alert('영업일지가 성공적으로 삭제되었습니다.')
      router.push(`/sales-reports?page=${page}`)
    } catch (err) {
      alert('영업일지 삭제에 실패했습니다: ' + (err instanceof Error ? err.message : '알 수 없는 오류'))
    } finally {
      setDeleting(false)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="flex items-center space-x-2">
          <Loader2 className="h-6 w-6 animate-spin" />
          <span>영업일지를 불러오는 중...</span>
        </div>
      </div>
    )
  }

  if (error || !report) {
    return (
      <div className="space-y-6">
        <div className="flex items-center space-x-4">
          <Button variant="outline" size="sm" asChild>
            <Link href={`/sales-reports?page=${page}`}>
              <ArrowLeft className="mr-2 h-4 w-4" />
              목록으로
            </Link>
          </Button>
          <h1 className="text-3xl font-bold">영업일지 상세</h1>
        </div>
        <Card>
          <CardContent className="pt-6">
            <div className="text-center text-red-600">
              {error || '영업일지를 찾을 수 없습니다.'}
            </div>
          </CardContent>
        </Card>
      </div>
    )
  }

  // 태그 문자열을 배열로 변환
  const tags = report.tags ? report.tags.split(',').map(tag => tag.trim()).filter(tag => tag) : []

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

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <Button variant="outline" size="sm" asChild>
            <Link href={`/sales-reports?page=${page}`}>
              <ArrowLeft className="mr-2 h-4 w-4" />
              목록으로
            </Link>
          </Button>
          <h1 className="text-3xl font-bold">영업일지 상세</h1>
        </div>
        <div className="flex space-x-2">
          <Button 
            variant="destructive" 
            onClick={handleDelete}
            disabled={deleting}
          >
            {deleting ? (
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            ) : (
              <Trash2 className="mr-2 h-4 w-4" />
            )}
            삭제
          </Button>
          <Button asChild>
            <Link href={`/sales-reports/${report.id}/edit?page=${page}`}>
              <Edit className="mr-2 h-4 w-4" />
              수정
            </Link>
          </Button>
        </div>
      </div>

      <Card id="sales-report-content">
        <CardHeader>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <CardTitle className="text-2xl">{report.company_display || report.company_name || '-'}</CardTitle>
              <Button variant="ghost" size="sm" asChild disabled={!(report.company_code || (report.company_display || report.company_name))}>
                <Link href={report.company_code 
                  ? `/companies/${report.company_code}` 
                  : `/companies?search=${encodeURIComponent((report.company_display || report.company_name || ''))}`
                }>
                  회사 정보 바로가기
                  <ArrowRight className="ml-1 h-4 w-4" />
                </Link>
              </Button>
            </div>
            <div className="flex items-center gap-2">
              <Badge variant={report.type === "대면" ? "default" : "secondary"}>{report.type}</Badge>
              <Badge variant="outline">{(report as any).sales_stage || '미지정'}</Badge>
            </div>
          </div>
          <CardDescription className="text-base">
            {report.visitDate} - {report.author_name} ({report.author_department})
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div>
            <h3 className="font-semibold text-lg mb-3">사용품목</h3>
            <div className="bg-gray-50 p-4 rounded-lg">
              <pre className="whitespace-pre-wrap text-sm leading-relaxed" style={{ fontFamily: '"Malgun Gothic", "맑은 고딕", sans-serif' }}>
                {report.products || '작성 내용 없음'}
              </pre>
            </div>
          </div>

          <Separator />

          {/* 본문에서는 영업단계 섹션 제거 (헤더에 표시) */}

          <div>
            <h3 className="font-semibold text-lg mb-3">미팅 내용 (이슈사항)</h3>
            <div className="bg-gray-50 p-4 rounded-lg">
              <pre className="whitespace-pre-wrap text-sm leading-relaxed" style={{ fontFamily: '"Malgun Gothic", "맑은 고딕", sans-serif' }}>{report.content}</pre>
            </div>
          </div>

          {tags.length > 0 && (
            <>
              <Separator />
              <div>
                <h3 className="font-semibold text-sm text-muted-foreground mb-2">태그</h3>
                <div className="flex gap-2">
                  {tags.map((tag, index) => (
                    <Badge key={index} variant="outline">
                      {tag}
                    </Badge>
                  ))}
                </div>
              </div>
            </>
          )}
        </CardContent>
      </Card>

      {/* 같은 회사의 다른 영업일지 리스트 */}
      <div className="mt-10">
        <h2 className="text-xl font-bold mb-4">영업일지 리스트</h2>
        {otherLoading ? (
          <div className="flex items-center space-x-2 text-muted-foreground"><Loader2 className="h-5 w-5 animate-spin" /> 불러오는 중...</div>
        ) : otherError ? (
          <div className="text-red-600">{otherError}</div>
        ) : otherReports.length === 0 ? (
          <div className="text-muted-foreground">같은 회사의 다른 영업일지가 없습니다.</div>
        ) : (
          <Card className="bg-white">
            <CardContent className="p-0">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>방문일자</TableHead>
                    <TableHead>영업단계</TableHead>
                    <TableHead>미팅 내용(이슈사항)</TableHead>
                    <TableHead>작성자</TableHead>
                    <TableHead>영업형태</TableHead>
                    <TableHead className="text-center">상세보기</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {(showAll ? otherReports : otherReports.slice(0, 10)).map((r) => {
                    const isCurrent = r.id === report.id
                    return (
                      <TableRow key={r.id} className={isCurrent ? "bg-gray-200 font-semibold" : "hover:bg-gray-50 cursor-pointer"} onClick={() => !isCurrent && router.push(`/sales-reports/${r.id}`)}>
                        <TableCell>{new Date(r.visitDate).toLocaleDateString('ko-KR')}</TableCell>
                        <TableCell>
                          <Badge 
                            variant="outline" 
                            className={`${getSalesStageStyle((r as any).sales_stage)} border`}
                          >
                            {(r as any).sales_stage || '미지정'}
                          </Badge>
                        </TableCell>
                        <TableCell>{r.content.slice(0, 40)}{r.content.length > 40 ? '...' : ''}</TableCell>
                        <TableCell>{(r as any).author_name || ''}</TableCell>
                        <TableCell>
                          <Badge variant={r.type === "대면" ? "default" : "secondary"}>{r.type}</Badge>
                        </TableCell>
                        <TableCell className="text-center">{isCurrent ? <span className="text-gray-700 font-semibold">현재</span> : <Button size="sm" variant="outline">이동</Button>}</TableCell>
                      </TableRow>
                    )
                  })}
                </TableBody>
              </Table>
              {otherReports.length > 10 && !showAll && (
                <div className="flex justify-center mt-4 pb-2">
                  <Button size="sm" variant="ghost" onClick={() => setShowAll(true)}>더 보기</Button>
                </div>
              )}
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  )
}
