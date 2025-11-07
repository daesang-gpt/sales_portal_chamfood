"use client"

import { useEffect, useState, useCallback } from "react"
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
import { LocationSelect } from "@/components/ui/location-select"

// CompanySearchInput을 클라이언트에서만 로드
const CompanySearchInput = dynamic(
  () => import("@/components/ui/company-search-input").then(mod => ({ default: mod.CompanySearchInput })),
  { 
    ssr: false,
    loading: () => <Input placeholder="로딩 중..." disabled />
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
  const [fieldErrors, setFieldErrors] = useState({
    visitDate: '',
    company: '',
    content: ''
  })
  const [companies, setCompanies] = useState<Company[]>([])
  const [companiesLoading, setCompaniesLoading] = useState(true)
  const [formData, setFormData] = useState({
    company: "",
    company_obj: undefined as string | null | undefined, // company_code (string)
    sales_stage: "",
    type: "",
    location: "",
    products: "",
    content: "",
    tags: "",
    visitDate: "",
  })
  const [tagLoading, setTagLoading] = useState(false)
  const [isNewCompany, setIsNewCompany] = useState(false)
  const [productSuggestions, setProductSuggestions] = useState<string[]>([])

  const fetchCompanies = useCallback(async () => {
    try {
      setCompaniesLoading(true)
      const data = await companyApi.getCompanies()
      setCompanies(data.results)
    } catch (err) {
      // 무시
    } finally {
      setCompaniesLoading(false)
    }
  }, []);

  const fetchReport = useCallback(async () => {
    if (!params.id) return;
    try {
      setLoading(true)
      setError(null)
      const report = await salesReportApi.getReport(Number(params.id))
      setFormData({
        company: report.company_display || report.company_name || '', // 표시명 우선
        company_obj: report.company_code || undefined,
        sales_stage: report.sales_stage || "",
        type: report.type,
        location: "", // 기존 영업일지 수정 시에는 소재지 필요 없음
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
  }, [params.id]);

  useEffect(() => {
    fetchCompanies()
    fetchReport()
  }, [fetchCompanies, fetchReport])

  const handleInputChange = (field: string, value: string | number | undefined) => {
    setFormData((prev) => ({ ...prev, [field]: value }))
  }

  const handleCompanyChange = async (companyName: string, companyId?: string) => {
    setFormData(prev => ({ 
      ...prev, 
      company: companyName, 
      company_obj: companyId
    }))
    
    // 회사가 선택된 경우
    if (companyId) {
      setIsNewCompany(false)
      // 해당 회사의 유니크한 상품명 불러오기
      try {
        const response = await companyApi.getUniqueProducts(companyId);
        // 중복 제거, 빈 값 제거, 가나다순 정렬
        const uniqueProducts = [...new Set(response.products || [])]
          .filter(p => p && p.trim())
          .sort((a, b) => a.localeCompare(b, 'ko')); // 한국어 가나다순 정렬
        setProductSuggestions(uniqueProducts);
        
        // 사용품목 입력칸에 자동으로 채우기 (각 상품마다 줄바꿈)
        if (uniqueProducts.length > 0) {
          setFormData(prev => ({ ...prev, products: uniqueProducts.join(',\n') }));
        }
      } catch (err) {
        console.error('상품명 조회 오류:', err);
        setProductSuggestions([]);
      }
    } else {
      setIsNewCompany(true)
      setProductSuggestions([])
      // 회사 선택이 해제된 경우 필드 초기화
      setFormData(prev => ({
        ...prev,
        products: ''
      }));
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    // 에러 초기화
    setError(null)
    setFieldErrors({
      visitDate: '',
      company: '',
      content: ''
    })

    const missingFields = []

    if (!formData.visitDate) {
      missingFields.push('방문일자')
    }

    if (!formData.company || !formData.company.trim()) {
      missingFields.push('회사명')
    }

    if (!formData.content || !formData.content.trim()) {
      missingFields.push('미팅 내용')
    }

    if (!formData.type) {
      missingFields.push('영업형태')
    }

    if (missingFields.length > 0) {
      const errorMessage = missingFields.length === 1 
        ? `${missingFields[0]}을(를) 입력해주세요.`
        : `${missingFields.join(', ')}을(를) 입력해주세요.`
      setError(errorMessage)
      return
    }

    setSaving(true)
    setError(null)
    let companyCode = formData.company_obj
    try {
      // 저장 시점에 회사 id가 없으면 자동 등록
      if (!companyCode && formData.company) {
        // 신규 회사인 경우 소재지 필수 체크
        if (!formData.location.trim()) {
          setError('신규 회사의 경우 소재지를 입력해주세요.')
          setSaving(false)
          return
        }
        
        try {
          const company = await companyApi.autoCreateCompany(formData.company, formData.location)
          companyCode = company.company_code // company_code 문자열
        } catch (err) {
          setError('회사 자동 등록에 실패했습니다.')
          setSaving(false)
          return
        }
      }
      const submitData = { 
        ...formData, 
        company_obj: companyCode || null,
        visitDate: formData.visitDate, // 날짜 형식 확인
        location: isNewCompany ? formData.location : undefined, // 신규 회사인 경우에만 소재지 포함
      }
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
    setError(null);
    try {
      console.log('키워드 추출 시작:', formData.content.substring(0, 50));
      const tags = await fetchRecommendedTags(formData.content);
      console.log('키워드 추출 결과:', tags);
      setFormData((prev) => ({ ...prev, tags: tags.join(', ') }));
    } catch (err) {
      console.error('키워드 추출 오류:', err);
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
            {/* 1. 방문일자 */}
            <div className="space-y-2 max-w-md">
              <Label className="text-sm font-semibold text-foreground">방문일자 *</Label>
              <Input
                type="date"
                value={formData.visitDate}
                onChange={e => handleInputChange("visitDate", e.target.value)}
                className="w-full"
              />
            </div>

            {/* 2. 회사명 */}
            <div className="space-y-2 max-w-md">
              <Label className="text-sm font-semibold text-foreground">회사명 *</Label>
              <CompanySearchInput
                value={formData.company}
                selectedCompanyId={formData.company_obj || undefined}
                onChange={handleCompanyChange}
                placeholder="회사명을 입력하거나 선택하세요"
              />
            </div>

            {/* 3-0. 영업단계 */}
            <div className="space-y-2 max-w-md">
              <Label className="text-sm font-semibold text-foreground">영업단계</Label>
              <Select value={formData.sales_stage || undefined} onValueChange={value => handleInputChange("sales_stage", value)}>
                <SelectTrigger className="w-full">
                  <SelectValue placeholder="영업단계를 선택하세요" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="초기 컨택">초기 컨택</SelectItem>
                  <SelectItem value="협상 진행(니즈 파악)">협상 진행(니즈 파악)</SelectItem>
                  <SelectItem value="계약 체결(거래처 등록)">계약 체결(거래처 등록)</SelectItem>
                  <SelectItem value="납품 관리">납품 관리</SelectItem>
                  <SelectItem value="관계 유지">관계 유지</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {/* 4. 영업형태 */}
            <div className="space-y-2 max-w-md">
              <Label className="text-sm font-semibold text-foreground">영업형태 *</Label>
              <Select value={formData.type || undefined} onValueChange={value => handleInputChange("type", value)}>
                <SelectTrigger className="w-full">
                  <SelectValue placeholder="영업형태를 선택하세요" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="대면">대면</SelectItem>
                  <SelectItem value="전화">전화</SelectItem>
                  <SelectItem value="화상">화상</SelectItem>
                  <SelectItem value="이메일">이메일</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {/* 2-1. 소재지 (신규 회사만) */}
            {!formData.company_obj && formData.company && (
              <div className="space-y-2 max-w-md">
                <Label className="text-sm font-semibold text-foreground">소재지 (신규 회사) *</Label>
                <LocationSelect
                  value={formData.location}
                  onChange={(value) => handleInputChange("location", value)}
                  placeholder="지역을 선택하세요"
                  required
                />
              </div>
            )}

            {/* 4. 사용품목 */}
            <div className="space-y-2">
              <Label htmlFor="products" className="text-sm font-semibold text-foreground">사용품목</Label>
              <Textarea
                id="products"
                value={formData.products || ''}
                onChange={e => handleInputChange("products", e.target.value)}
                placeholder="기존 회사 선택 시 판매했던 상품명이 자동으로 채워집니다. 신규 회사인 경우, 주로 사용하는 품목을 입력해주세요."
                rows={3}
                className="resize-none"
              />
            </div>

            {/* 5. 미팅 내용 */}
            <div className="space-y-2">
              <Label htmlFor="content" className="text-sm font-semibold text-foreground">미팅 내용 (이슈사항) *</Label>
              <Textarea
                id="content"
                value={formData.content}
                onChange={e => handleInputChange("content", e.target.value)}
                placeholder="영업 활동 내용을 상세히 기록해주세요..."
                rows={6}
                className="resize-none"
              />
            </div>

            {/* 6. 태그 (키워드) */}
            <div className="space-y-2">
              <div className="flex items-center gap-2">
                <Label htmlFor="tags" className="text-sm font-semibold text-foreground">태그 (키워드)</Label>
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

            {/* 에러 메시지 */}
            {error && (
              <div className="p-3 bg-red-50 border border-red-200 rounded-md">
                <p className="text-red-600 text-sm">{error}</p>
              </div>
            )}

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