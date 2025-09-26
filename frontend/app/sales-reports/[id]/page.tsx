"use client"

import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Separator } from "@/components/ui/separator"
import { ArrowLeft, Edit, FileImage, Loader2, Trash2 } from "lucide-react"
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
        setReport(reportData)
      } catch (err) {
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
      if (!report || !report.company) return;
      setOtherLoading(true)
      setOtherError(null)
      try {
        const data = await salesReportApi.getReports({
          companyId: report.company,
          ordering: "-visitDate",
          page_size: 100, // 충분히 크게 받아서 10개만 보여줌
        })
        setOtherReports((data as any).results)
      } catch (err) {
        setOtherError("같은 회사의 영업일지를 불러오는 중 오류가 발생했습니다.")
      } finally {
        setOtherLoading(false)
      }
    }
    if (report && report.company) {
      fetchOtherReports()
    }
  }, [report])

  const handleDownloadImage = () => {
    // 영업일지를 이미지로 변환하여 다운로드하는 로직
    // 실제로는 html2canvas 등을 사용하여 구현
    console.log("영업일지 이미지 다운로드")
  }

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
          <Button variant="outline" onClick={handleDownloadImage}>
            <FileImage className="mr-2 h-4 w-4" />
            이미지 다운로드
          </Button>
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
            <CardTitle>영업일지 #{report.id}</CardTitle>
            <Badge variant={report.type === "대면" ? "default" : "secondary"}>{report.type}</Badge>
          </div>
          <CardDescription>
            {report.visitDate} - {report.author_name} ({report.team_display})
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="space-y-4">
              <div>
                <h3 className="font-semibold text-sm text-muted-foreground mb-1">작성자</h3>
                <p className="text-lg">{report.author_name}</p>
              </div>
              <div>
                <h3 className="font-semibold text-sm text-muted-foreground mb-1">팀명</h3>
                <p className="text-lg">{report.team_display}</p>
              </div>
              <div>
                <h3 className="font-semibold text-sm text-muted-foreground mb-1">방문일자</h3>
                <p className="text-lg">{report.visitDate}</p>
              </div>
            </div>

            <div className="space-y-4">
              <div>
                <h3 className="font-semibold text-sm text-muted-foreground mb-1">회사명</h3>
                <p className="text-lg font-medium">{report.company_display}</p>
              </div>
              <div>
                <h3 className="font-semibold text-sm text-muted-foreground mb-1">소재지</h3>
                <p className="text-lg">{report.location}</p>
              </div>
              <div>
                <h3 className="font-semibold text-sm text-muted-foreground mb-1">사용품목</h3>
                <p className="text-lg">{report.products}</p>
              </div>
            </div>
          </div>

          <Separator />

          <div>
            <h3 className="font-semibold text-lg mb-3">미팅 내용 (이슈사항)</h3>
            <div className="bg-gray-50 p-4 rounded-lg">
              <pre className="whitespace-pre-wrap text-sm leading-relaxed">{report.content}</pre>
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
                        <TableCell>{r.content.slice(0, 40)}{r.content.length > 40 ? '...' : ''}</TableCell>
                        <TableCell>{r.author_name}</TableCell>
                        <TableCell><Badge variant={r.type === "대면" ? "default" : "secondary"}>{r.type}</Badge></TableCell>
                        <TableCell className="text-center">{isCurrent ? <span className="text-gray-700 font-semibold">현재</span> : <Button size="sm" variant="outline">이동</Button>}</TableCell>
                      </TableRow>
                    )
                  })}
                </TableBody>
              </Table>
              {otherReports.length > 10 && !showAll && (
                <div className="flex justify-end mt-2">
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
