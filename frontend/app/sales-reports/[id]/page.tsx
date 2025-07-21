"use client"

import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Separator } from "@/components/ui/separator"
import { ArrowLeft, Edit, FileImage, Loader2 } from "lucide-react"
import Link from "next/link"
import { useParams } from "next/navigation"
import { useEffect, useState } from "react"
import { salesReportApi, SalesReport } from "@/lib/api"

export default function SalesReportDetailPage() {
  const params = useParams()
  const [report, setReport] = useState<SalesReport | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

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

  const handleDownloadImage = () => {
    // 영업일지를 이미지로 변환하여 다운로드하는 로직
    // 실제로는 html2canvas 등을 사용하여 구현
    console.log("영업일지 이미지 다운로드")
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
            <Link href="/sales-reports">
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
            <Link href="/sales-reports">
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
          <Button asChild>
            <Link href={`/sales-reports/${report.id}/edit`}>
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
    </div>
  )
}
