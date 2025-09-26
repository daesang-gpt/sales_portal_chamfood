"use client"

import { useEffect, useState } from "react"
import { useParams, useRouter, useSearchParams } from "next/navigation"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Loader2, Save, ArrowLeft } from "lucide-react"
import Link from "next/link"
import { salesReportApi, companyApi, SalesReport, Company } from "@/lib/api"
import dynamic from "next/dynamic"
import { fetchRecommendedTags } from '@/lib/api'

// CompanySearchInput을 클라이언트에서만 로드
const CompanySearchInput = dynamic(
  () => import("@/components/ui/company-search-input").then(mod => ({ default: mod.CompanySearchInput })),
  { 
    ssr: false,
    loading: () => <Input placeholder="로딩 중..." disabled required />
  }
)

export default function EditSalesReportPage() {
  const params = useParams()
  const router = useRouter()
  const searchParams = useSearchParams();
  const page = searchParams.get("page") || "1";
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [companies, setCompanies] = useState<Company[]>([])
  const [companiesLoading, setCompaniesLoading] = useState(true)
  const [formData, setFormData] = useState({
    company: "",
    company_obj: undefined as number | null | undefined,
    type: "",
    location: "",
    products: "",
    content: "",
    tags: "",
    visitDate: "",
  })
  const [tagLoading, setTagLoading] = useState(false)

  useEffect(() => {
    fetchCompanies()
    fetchReport()
    // eslint-disable-next-line
  }, [params.id])

  const fetchCompanies = async () => {
    try {
      setCompaniesLoading(true)
      const data = await companyApi.getCompanies()
      setCompanies((data as any).results) // 반드시 (data as any).results로 배열만 저장
    } catch (err) {
      // 무시
    } finally {
      setCompaniesLoading(false)
    }
  }

  const fetchReport = async () => {
    try {
      setLoading(true)
      setError(null)
      const report = await salesReportApi.getReport(Number(params.id))
      setFormData({
        company: report.company_display, // 회사명으로 표시
        company_obj: report.company_obj,
        type: report.type,
        location: report.location,
        products: report.products,
        content: report.content,
        tags: report.tags,
        visitDate: report.visitDate,
      })
    } catch (err) {
      setError("영업일지 정보를 불러오지 못했습니다.")
    } finally {
      setLoading(false)
    }
  }

  const handleInputChange = (field: string, value: string | number | undefined) => {
    setFormData((prev) => ({ ...prev, [field]: value }))
  }

  const handleCompanyChange = (companyName: string, companyId?: number) => {
    setFormData(prev => ({ 
      ...prev, 
      company: companyName, 
      company_obj: companyId 
    }))
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!formData.visitDate) {
      setError('방문일자를 입력해주세요.')
      return
    }
    setSaving(true)
    setError(null)
    let companyId = formData.company_obj
    try {
      // 저장 시점에 회사 id가 없으면 자동 등록
      if (!companyId && formData.company) {
        try {
          const company = await companyApi.autoCreateCompany(formData.company)
          companyId = company.id
        } catch (err) {
          setError('회사 자동 등록에 실패했습니다.')
          setSaving(false)
          return
        }
      }
      const submitData = { 
        ...formData, 
        company_obj: companyId || null,
        visitDate: formData.visitDate // 날짜 형식 확인
      }
      console.log('제출 데이터:', submitData)
      await salesReportApi.updateReport(Number(params.id), submitData)
      router.push(`/sales-reports/${params.id}?page=${page}`)
    } catch (err) {
      setError('영업일지 수정 중 오류가 발생했습니다.')
    } finally {
      setSaving(false)
    }
  }

  // 추천 태그 추출 핸들러
  const handleRecommendTags = async () => {
    if (!formData.content.trim()) {
      setError('미팅 내용을 먼저 입력해주세요.');
      return;
    }
    setTagLoading(true);
    try {
      const tags = await fetchRecommendedTags(formData.content);
      setFormData((prev) => ({ ...prev, tags: tags.join(', ') }));
    } catch (err) {
      setError('추천 태그 추출에 실패했습니다.');
    } finally {
      setTagLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <Loader2 className="h-6 w-6 animate-spin" />
        <span className="ml-2">불러오는 중...</span>
      </div>
    )
  }

  if (error) {
    return (
      <div className="space-y-6">
        <div className="flex items-center space-x-4">
          <Button variant="outline" size="sm" asChild>
            <Link href={`/sales-reports/${params.id}?page=${page}`}>
              <ArrowLeft className="mr-2 h-4 w-4" />
              상세로
            </Link>
          </Button>
          <h1 className="text-3xl font-bold">영업일지 수정</h1>
        </div>
        <Card>
          <CardContent className="pt-6">
            <div className="text-center text-red-600">{error}</div>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center space-x-4">
        <Button variant="outline" size="sm" asChild>
          <Link href={`/sales-reports/${params.id}?page=${page}`}>
            <ArrowLeft className="mr-2 h-4 w-4" />
            상세로
          </Link>
        </Button>
        <h1 className="text-3xl font-bold">영업일지 수정</h1>
      </div>
      <Card>
        <CardHeader>
          <CardTitle>영업일지 정보 수정</CardTitle>
          <CardDescription>필요한 정보를 수정 후 저장하세요.</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="space-y-2">
                <Label>방문일자</Label>
                <Input
                  type="date"
                  value={formData.visitDate}
                  onChange={e => handleInputChange("visitDate", e.target.value)}
                  required
                />
              </div>
              {/* 회사명 입력: CompanySearchInput으로 교체 */}
              <div className="space-y-2">
                <Label>회사명</Label>
                <CompanySearchInput
                  value={formData.company}
                  selectedCompanyId={formData.company_obj ?? undefined}
                  onChange={handleCompanyChange}
                  placeholder="회사명을 입력하거나 선택하세요"
                />
              </div>
              <div className="space-y-2">
                <Label>영업형태</Label>
                <Select value={formData.type} onValueChange={value => handleInputChange("type", value)}>
                  <SelectTrigger>
                    <SelectValue placeholder="영업형태 선택" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="대면">대면</SelectItem>
                    <SelectItem value="전화">전화</SelectItem>
                    <SelectItem value="화상">화상</SelectItem>
                    <SelectItem value="이메일">이메일</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label>소재지</Label>
                <Select value={formData.location} onValueChange={value => handleInputChange("location", value)}>
                  <SelectTrigger>
                    <SelectValue placeholder="소재지 선택" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="수도권">수도권</SelectItem>
                    <SelectItem value="충청권">충청권</SelectItem>
                    <SelectItem value="영남권">영남권</SelectItem>
                    <SelectItem value="호남권">호남권</SelectItem>
                    <SelectItem value="강원권">강원권</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2 md:col-span-2">
                <Label htmlFor="products">사용품목</Label>
                <Input
                  id="products"
                  value={formData.products}
                  onChange={e => handleInputChange("products", e.target.value)}
                  placeholder="예: 국내산 닭, 수입산 돼지고기"
                  required
                />
              </div>
              <div className="space-y-2 md:col-span-2">
                <Label htmlFor="content">미팅 내용 (이슈사항)</Label>
                <Textarea
                  id="content"
                  value={formData.content}
                  onChange={e => handleInputChange("content", e.target.value)}
                  placeholder="영업 활동 내용을 상세히 기록해주세요..."
                  rows={6}
                  required
                />
              </div>
              <div className="space-y-2 md:col-span-2">
                <div className="flex items-center gap-2">
                  <Label htmlFor="tags">태그 (키워드)</Label>
                  <Button type="button" variant="secondary" size="sm" onClick={handleRecommendTags} disabled={tagLoading}>
                    {tagLoading ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : null}
                    키워드 추출
                  </Button>
                </div>
                <Input
                  id="tags"
                  value={formData.tags}
                  onChange={e => handleInputChange("tags", e.target.value)}
                  placeholder="쉼표로 구분하여 입력 (예: 신규고객, 대량주문)"
                />
              </div>
            </div>
            <div className="flex justify-end space-x-4">
              <Button type="button" variant="outline" asChild disabled={saving}>
                <Link href={`/sales-reports/${params.id}?page=${page}`}>취소</Link>
              </Button>
              <Button type="submit" disabled={saving}>
                {saving ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    저장 중...
                  </>
                ) : (
                  <>
                    <Save className="mr-2 h-4 w-4" />
                    저장
                  </>
                )}
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  )
} 