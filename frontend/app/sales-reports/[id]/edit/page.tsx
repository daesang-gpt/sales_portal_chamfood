"use client"

import { useEffect, useState } from "react"
import { useParams, useRouter } from "next/navigation"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Loader2, Save, ArrowLeft } from "lucide-react"
import Link from "next/link"
import { salesReportApi, companyApi, SalesReport, Company } from "@/lib/api"

export default function EditSalesReportPage() {
  const params = useParams()
  const router = useRouter()
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [companies, setCompanies] = useState<Company[]>([])
  const [companiesLoading, setCompaniesLoading] = useState(true)
  const [formData, setFormData] = useState({
    company: "",
    company_obj: undefined as number | undefined,
    type: "",
    location: "",
    products: "",
    content: "",
    tags: "",
    visitDate: "",
  })

  useEffect(() => {
    fetchCompanies()
    fetchReport()
    // eslint-disable-next-line
  }, [params.id])

  const fetchCompanies = async () => {
    try {
      setCompaniesLoading(true)
      const data = await companyApi.getCompanies()
      setCompanies(data)
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
        company: report.company,
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

  const handleCompanySelect = (companyId: string) => {
    if (companyId === 'new') {
      setFormData(prev => ({ ...prev, company: "", company_obj: undefined }))
    } else {
      const selectedCompany = companies.find(c => c.id.toString() === companyId)
      if (selectedCompany) {
        setFormData(prev => ({
          ...prev,
          company: selectedCompany.company_name,
          company_obj: selectedCompany.id
        }))
      }
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!formData.visitDate) {
      setError('방문일자를 입력해주세요.')
      return
    }
    try {
      setSaving(true)
      setError(null)
      await salesReportApi.updateReport(Number(params.id), formData)
      router.push(`/sales-reports/${params.id}`)
    } catch (err) {
      setError('영업일지 수정 중 오류가 발생했습니다.')
    } finally {
      setSaving(false)
    }
  }

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
            <Link href={`/sales-reports/${params.id}`}>
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
          <Link href={`/sales-reports/${params.id}`}>
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
              <div className="space-y-2">
                <Label>회사 선택</Label>
                <Select onValueChange={handleCompanySelect} value={formData.company_obj ? String(formData.company_obj) : 'new'}>
                  <SelectTrigger>
                    <SelectValue placeholder="회사를 선택하거나 신규 입력" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="new">신규 회사 입력</SelectItem>
                    {companiesLoading ? (
                      <SelectItem value="" disabled>로딩 중...</SelectItem>
                    ) : (
                      companies.map((company) => (
                        <SelectItem key={company.id} value={company.id.toString()}>
                          {company.company_name}
                        </SelectItem>
                      ))
                    )}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label htmlFor="company">회사명</Label>
                <Input
                  id="company"
                  value={formData.company}
                  onChange={e => handleInputChange("company", e.target.value)}
                  placeholder="회사명을 입력하세요"
                  required
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
                <Label htmlFor="tags">태그 (키워드)</Label>
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
                <Link href={`/sales-reports/${params.id}`}>취소</Link>
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