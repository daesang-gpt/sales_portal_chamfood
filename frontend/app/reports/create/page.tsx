"use client"

import type React from "react"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Calendar } from "@/components/ui/calendar"
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover"
import { CalendarIcon, ArrowLeft, Save, FileText } from "lucide-react"
import { format } from "date-fns"
import { ko } from "date-fns/locale"
import Link from "next/link"
import { useRouter } from "next/navigation"

export default function CreateReportPage() {
  const router = useRouter()
  const [date, setDate] = useState<Date>()
  const [formData, setFormData] = useState({
    company: "",
    companyCode: "",
    contactType: "",
    location: "",
    product: "",
    content: "",
    tags: "",
    status: "진행중",
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    console.log("영업일지 제출:", { ...formData, date })
    // 실제 제출 로직 구현 후 목록으로 이동
    router.push("/reports")
  }

  const handleSaveDraft = () => {
    console.log("임시저장:", { ...formData, date })
    // 임시저장 로직 구현
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <div className="flex items-center space-x-4">
              <Link href="/reports">
                <Button variant="outline" size="sm">
                  <ArrowLeft className="h-4 w-4 mr-2" />
                  목록으로
                </Button>
              </Link>
              <div>
                <h1 className="text-2xl font-bold text-gray-900">영업일지 작성</h1>
                <p className="text-gray-600">새로운 영업일지를 작성합니다</p>
              </div>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <FileText className="h-5 w-5" />
              영업일지 작성
            </CardTitle>
            <CardDescription>영업 활동 내용을 상세히 기록해주세요.</CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-6">
              {/* 기본 정보 */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-2">
                  <Label htmlFor="date">방문일자 *</Label>
                  <Popover>
                    <PopoverTrigger asChild>
                      <Button variant="outline" className="w-full justify-start text-left font-normal bg-transparent">
                        <CalendarIcon className="mr-2 h-4 w-4" />
                        {date ? format(date, "PPP", { locale: ko }) : "날짜를 선택하세요"}
                      </Button>
                    </PopoverTrigger>
                    <PopoverContent className="w-auto p-0">
                      <Calendar mode="single" selected={date} onSelect={setDate} initialFocus />
                    </PopoverContent>
                  </Popover>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="company">회사명 *</Label>
                  <Input
                    id="company"
                    value={formData.company}
                    onChange={(e) => setFormData({ ...formData, company: e.target.value })}
                    placeholder="회사명을 입력하세요"
                    required
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-2">
                  <Label htmlFor="companyCode">회사코드</Label>
                  <Input
                    id="companyCode"
                    value={formData.companyCode}
                    onChange={(e) => setFormData({ ...formData, companyCode: e.target.value })}
                    placeholder="예: C0000126"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="contactType">영업형태 *</Label>
                  <Select
                    value={formData.contactType}
                    onValueChange={(value) => setFormData({ ...formData, contactType: value })}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="영업형태를 선택하세요" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="대면">대면</SelectItem>
                      <SelectItem value="전화">전화</SelectItem>
                      <SelectItem value="이메일">이메일</SelectItem>
                      <SelectItem value="화상회의">화상회의</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-2">
                  <Label htmlFor="location">소재지 *</Label>
                  <Select
                    value={formData.location}
                    onValueChange={(value) => setFormData({ ...formData, location: value })}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="지역을 선택하세요" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="서울">서울</SelectItem>
                      <SelectItem value="경기">경기</SelectItem>
                      <SelectItem value="인천">인천</SelectItem>
                      <SelectItem value="수도권">수도권</SelectItem>
                      <SelectItem value="부산">부산</SelectItem>
                      <SelectItem value="대구">대구</SelectItem>
                      <SelectItem value="대전">대전</SelectItem>
                      <SelectItem value="광주">광주</SelectItem>
                      <SelectItem value="울산">울산</SelectItem>
                      <SelectItem value="충북">충북</SelectItem>
                      <SelectItem value="충남">충남</SelectItem>
                      <SelectItem value="전북">전북</SelectItem>
                      <SelectItem value="전남">전남</SelectItem>
                      <SelectItem value="경북">경북</SelectItem>
                      <SelectItem value="경남">경남</SelectItem>
                      <SelectItem value="강원">강원</SelectItem>
                      <SelectItem value="제주">제주</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="status">진행상태</Label>
                  <Select
                    value={formData.status}
                    onValueChange={(value) => setFormData({ ...formData, status: value })}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="진행중">진행중</SelectItem>
                      <SelectItem value="완료">완료</SelectItem>
                      <SelectItem value="검토중">검토중</SelectItem>
                      <SelectItem value="보류">보류</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="product">사용품목 *</Label>
                <Input
                  id="product"
                  value={formData.product}
                  onChange={(e) => setFormData({ ...formData, product: e.target.value })}
                  placeholder="예: 국내산 닭, 태국산 통날개, 브라질산 원료육 등"
                  required
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="content">미팅 내용 (이슈사항) *</Label>
                <Textarea
                  id="content"
                  value={formData.content}
                  onChange={(e) => setFormData({ ...formData, content: e.target.value })}
                  placeholder="미팅 내용과 주요 이슈사항을 상세히 기록해주세요&#10;&#10;예시:&#10;- 치킨 프랜차이즈 '푸라닭' 본사 미팅&#10;- 신메뉴 1종에 한하여 수입산 전환 검토&#10;- 태국산 통날개 요청, 유럽산/브라질산도 함께 제안&#10;- 국내산 사용 업체로 마케팅된 업체여서 내부 협의 필요"
                  rows={8}
                  required
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="tags">태그 (키워드)</Label>
                <Input
                  id="tags"
                  value={formData.tags}
                  onChange={(e) => setFormData({ ...formData, tags: e.target.value })}
                  placeholder="쉼표로 구분하여 입력 (예: 프랜차이즈, 신메뉴, 수입산, 태국산)"
                />
                <p className="text-xs text-gray-500">검색 및 분류에 활용되는 키워드를 입력해주세요</p>
              </div>

              {/* 제출 버튼 */}
              <div className="flex gap-4 pt-6">
                <Button type="submit" className="flex-1">
                  <Save className="h-4 w-4 mr-2" />
                  영업일지 저장
                </Button>
                <Button type="button" variant="outline" onClick={handleSaveDraft}>
                  임시저장
                </Button>
                <Link href="/reports">
                  <Button type="button" variant="outline">
                    취소
                  </Button>
                </Link>
              </div>
            </form>
          </CardContent>
        </Card>
      </main>
    </div>
  )
}
