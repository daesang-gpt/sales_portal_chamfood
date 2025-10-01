"use client"

import type React from "react"

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Calendar } from "@/components/ui/calendar"
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover"
import { CalendarIcon, Save, ArrowLeft, Loader2 } from "lucide-react"
import { format } from "date-fns"
import { ko } from "date-fns/locale"
import Link from "next/link"
import { useRouter } from "next/navigation"
import { salesReportApi } from "@/lib/api"
import { getUserFromToken } from "@/lib/auth"
import dynamic from "next/dynamic"
import { fetchRecommendedTags } from '@/lib/api'
import { companyApi } from "@/lib/api"

// CompanySearchInput을 클라이언트에서만 로드
const CompanySearchInput = dynamic(
  () => import("@/components/ui/company-search-input").then(mod => ({ default: mod.CompanySearchInput })),
  { 
    ssr: false,
    loading: () => <Input placeholder="로딩 중..." disabled />
  }
)

export default function NewSalesReportPage() {
  const router = useRouter()
  const [date, setDate] = useState<Date>()
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [formData, setFormData] = useState({
    company: "",
    company_obj: undefined as number | undefined,
    type: "",
    location: "",
    products: "",
    content: "",
    tags: "",
  })
  const [tagLoading, setTagLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!date) {
      setError('방문일자를 선택해주세요.')
      return
    }

    // 사용자 정보 가져오기
    const user = getUserFromToken();
    if (!user) {
      setError('로그인이 필요합니다. 다시 로그인 해주세요.')
      return
    }

    let companyId = formData.company_obj;
    try {
      setLoading(true)
      setError(null)
      // 회사 id가 없고 회사명이 있으면 자동 등록
      if (!companyId && formData.company) {
        try {
          const company = await companyApi.autoCreateCompany(formData.company);
          companyId = company.id;
        } catch (err) {
          setError('회사 자동 등록에 실패했습니다.');
          setLoading(false);
          return;
        }
      }
      const reportData = {
        visitDate: date.toISOString().split('T')[0], // YYYY-MM-DD 형식
        company: formData.company,
        company_obj: companyId || null,
        type: formData.type,
        location: formData.location,
        products: formData.products,
        content: formData.content,
        tags: formData.tags,
        author: user.id, // 작성자 ID
        team: user.department, // 부서/팀명
      }

      await salesReportApi.createReport(reportData)
      router.push("/sales-reports")
    } catch (err) {
      setError('영업일지 저장 중 오류가 발생했습니다.')
      console.error('영업일지 저장 오류:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleInputChange = (field: string, value: string | number | undefined) => {
    setFormData((prev) => ({ ...prev, [field]: value }))
  }

  const handleCompanyChange = async (companyName: string, companyId?: number) => {
    setFormData(prev => ({ 
      ...prev, 
      company: companyName, 
      company_obj: companyId 
    }))
    
    // 회사가 선택된 경우 해당 회사의 데이터 불러오기
    if (companyId) {
      try {
        const company = await companyApi.getCompany(companyId);
        setFormData(prev => ({
          ...prev,
          location: company.location || '',
          products: company.products || ''
        }));
      } catch (err) {
        console.error('회사 정보 불러오기 오류:', err);
      }
    } else {
      // 회사 선택이 해제된 경우 필드 초기화
      setFormData(prev => ({
        ...prev,
        location: '',
        products: ''
      }));
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

  return (
    <div className="space-y-6">
      <div className="flex items-center space-x-4">
        <Button variant="outline" size="sm" asChild>
          <Link href="/sales-reports">
            <ArrowLeft className="mr-2 h-4 w-4" />
            목록으로
          </Link>
        </Button>
        <h1 className="text-3xl font-bold">영업일지 작성</h1>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>새 영업일지</CardTitle>
          <CardDescription>영업 활동 내용을 상세히 기록해주세요.</CardDescription>
        </CardHeader>
        <CardContent>
          {error && (
            <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-md">
              <p className="text-red-600 text-sm">{error}</p>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="space-y-2">
                <Label>방문일자</Label>
                <Popover>
                  <PopoverTrigger asChild>
                    <Button variant="outline" className="w-full justify-start text-left font-normal bg-transparent">
                      <CalendarIcon className="mr-2 h-4 w-4" />
                      {date ? format(date, "PPP", { locale: ko }) : "날짜를 선택하세요"}
                    </Button>
                  </PopoverTrigger>
                  <PopoverContent className="w-auto p-0">
                    <Calendar value={date} onChange={(newDate) => setDate(newDate || undefined)} />
                  </PopoverContent>
                </Popover>
              </div>

              <div className="space-y-2">
                <Label>회사명</Label>
                <CompanySearchInput
                  value={formData.company}
                  selectedCompanyId={formData.company_obj}
                  onChange={handleCompanyChange}
                  placeholder="회사명을 입력하거나 선택하세요"
                />
              </div>

              <div className="space-y-2">
                <Label>영업형태</Label>
                <Select value={formData.type} onValueChange={(value) => handleInputChange("type", value)}>
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
                <Select value={formData.location || ''} onValueChange={(value) => handleInputChange("location", value)}>
                  <SelectTrigger>
                    <SelectValue placeholder="소재지를 선택하세요" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="수도권">수도권</SelectItem>
                    <SelectItem value="충청권">충청권</SelectItem>
                    <SelectItem value="강원권">강원권</SelectItem>
                    <SelectItem value="영남권">영남권</SelectItem>
                    <SelectItem value="호남권">호남권</SelectItem>
                    <SelectItem value="기타">기타</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label htmlFor="products">사용품목</Label>
                <Input
                  id="products"
                  value={formData.products || ''}
                  onChange={(e) => handleInputChange("products", e.target.value)}
                  placeholder="예: 국내산 닭, 수입산 돼지고기"
                />
              </div>

              <div className="space-y-2 md:col-span-2">
                <Label htmlFor="content">미팅 내용 (이슈사항)</Label>
                <Textarea
                  id="content"
                  value={formData.content}
                  onChange={(e) => handleInputChange("content", e.target.value)}
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
                  onChange={(e) => handleInputChange("tags", e.target.value)}
                  placeholder="쉼표로 구분하여 입력 (예: 신규고객, 대량주문)"
                />
              </div>
            </div>

            <div className="flex justify-end space-x-4">
              <Button type="button" variant="outline" asChild disabled={loading}>
                <Link href="/sales-reports">취소</Link>
              </Button>
              <Button type="submit" disabled={loading}>
                {loading ? (
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
