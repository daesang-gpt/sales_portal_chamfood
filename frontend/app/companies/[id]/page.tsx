"use client"

import { useState } from "react"
import { ArrowLeft, Building2, DollarSign, FileText, Edit, Save, User, CreditCard, BarChart3 } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import Link from "next/link"

// 샘플 회사 상세 데이터
const companyDetail = {
  id: 1,
  name: "아이더스에프앤비",
  code: "C0000126",
  sapCode: "1114755",
  smCode: "62538",
  type: "프랜차이즈",
  industry: "축육(가공장)",
  ceo: "김대표",
  address: "서울시 강남구 테헤란로 123",
  phone: "02-1234-5678",
  manager: "이담당",
  managerPhone: "010-1234-5678",
  establishedDate: "2015-03-15",
  contractDate: "2025-04-02",
  paymentTerms: "15일단위 마감, 30일이내, 현금결제",
  customerType: "기존",
  website: "www.aidersf.co.kr",
  status: "활성",
  notes:
    "치킨 프랜차이즈 '푸라닭' 본사 운영. 전국 720여개 매장 보유. 국내산 사용 업체로 마케팅하고 있어 수입산 전환 시 신중한 접근 필요.",
}

// 샘플 매출 데이터
const salesData = [
  { month: "2024-07", sales: 120000000, volume: 850, orders: 12 },
  { month: "2024-08", sales: 135000000, volume: 920, orders: 14 },
  { month: "2024-09", sales: 145000000, volume: 980, orders: 15 },
  { month: "2024-10", sales: 160000000, volume: 1100, orders: 18 },
  { month: "2024-11", sales: 150000000, volume: 1050, orders: 16 },
  { month: "2024-12", sales: 175000000, volume: 1200, orders: 20 },
]

// 샘플 영업일지 데이터
const relatedReports = [
  {
    id: 1,
    date: "2025-01-07",
    contactType: "대면",
    product: "국내산 닭",
    summary: "신메뉴 수입산 전환 검토 관련 미팅",
    status: "진행중",
  },
  {
    id: 2,
    date: "2024-12-15",
    contactType: "전화",
    product: "국내산 닭",
    summary: "12월 물량 확정 및 1월 계획 논의",
    status: "완료",
  },
  {
    id: 3,
    date: "2024-11-28",
    contactType: "대면",
    product: "국내산 닭",
    summary: "연말 프로모션 관련 협의",
    status: "완료",
  },
]

export default function CompanyDetailPage({ params }: { params: { id: string } }) {
  const [isEditing, setIsEditing] = useState(false)
  const [formData, setFormData] = useState(companyDetail)

  const handleSave = () => {
    console.log("회사 정보 저장:", formData)
    setIsEditing(false)
    // 실제 저장 로직 구현
  }

  const totalSales = salesData.reduce((sum, data) => sum + data.sales, 0)
  const totalVolume = salesData.reduce((sum, data) => sum + data.volume, 0)
  const totalOrders = salesData.reduce((sum, data) => sum + data.orders, 0)

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <div className="flex items-center space-x-4">
              <Link href="/companies">
                <Button variant="outline" size="sm">
                  <ArrowLeft className="h-4 w-4 mr-2" />
                  목록으로
                </Button>
              </Link>
              <div>
                <h1 className="text-2xl font-bold text-gray-900">{formData.name}</h1>
                <p className="text-gray-600">회사 상세 정보</p>
              </div>
            </div>
            <div className="flex items-center space-x-2">
              {isEditing ? (
                <>
                  <Button onClick={handleSave}>
                    <Save className="h-4 w-4 mr-2" />
                    저장
                  </Button>
                  <Button variant="outline" onClick={() => setIsEditing(false)}>
                    취소
                  </Button>
                </>
              ) : (
                <Button onClick={() => setIsEditing(true)}>
                  <Edit className="h-4 w-4 mr-2" />
                  수정
                </Button>
              )}
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Tabs defaultValue="info" className="space-y-6">
          <TabsList className="grid w-full grid-cols-4">
            <TabsTrigger value="info">기본 정보</TabsTrigger>
            <TabsTrigger value="sales">매출 현황</TabsTrigger>
            <TabsTrigger value="reports">영업일지</TabsTrigger>
            <TabsTrigger value="analysis">분석</TabsTrigger>
          </TabsList>

          <TabsContent value="info" className="space-y-6">
            {/* 기본 정보 카드 */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              <Card className="lg:col-span-2">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Building2 className="h-5 w-5" />
                    회사 기본 정보
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-6">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label>회사명</Label>
                      {isEditing ? (
                        <Input
                          value={formData.name}
                          onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                        />
                      ) : (
                        <p className="text-lg font-semibold">{formData.name}</p>
                      )}
                    </div>
                    <div className="space-y-2">
                      <Label>회사코드</Label>
                      {isEditing ? (
                        <Input
                          value={formData.code}
                          onChange={(e) => setFormData({ ...formData, code: e.target.value })}
                        />
                      ) : (
                        <p>{formData.code}</p>
                      )}
                    </div>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div className="space-y-2">
                      <Label>SAP 코드</Label>
                      {isEditing ? (
                        <Input
                          value={formData.sapCode}
                          onChange={(e) => setFormData({ ...formData, sapCode: e.target.value })}
                        />
                      ) : (
                        <p>{formData.sapCode}</p>
                      )}
                    </div>
                    <div className="space-y-2">
                      <Label>SM 코드</Label>
                      {isEditing ? (
                        <Input
                          value={formData.smCode}
                          onChange={(e) => setFormData({ ...formData, smCode: e.target.value })}
                        />
                      ) : (
                        <p>{formData.smCode}</p>
                      )}
                    </div>
                    <div className="space-y-2">
                      <Label>기업형태</Label>
                      {isEditing ? (
                        <Select
                          value={formData.type}
                          onValueChange={(value) => setFormData({ ...formData, type: value })}
                        >
                          <SelectTrigger>
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="가공장">가공장</SelectItem>
                            <SelectItem value="프랜차이즈">프랜차이즈</SelectItem>
                            <SelectItem value="도소매">도소매</SelectItem>
                          </SelectContent>
                        </Select>
                      ) : (
                        <Badge variant="outline">{formData.type}</Badge>
                      )}
                    </div>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label>대표자명</Label>
                      {isEditing ? (
                        <Input
                          value={formData.ceo}
                          onChange={(e) => setFormData({ ...formData, ceo: e.target.value })}
                        />
                      ) : (
                        <p>{formData.ceo}</p>
                      )}
                    </div>
                    <div className="space-y-2">
                      <Label>설립일</Label>
                      {isEditing ? (
                        <Input
                          type="date"
                          value={formData.establishedDate}
                          onChange={(e) => setFormData({ ...formData, establishedDate: e.target.value })}
                        />
                      ) : (
                        <p>{formData.establishedDate}</p>
                      )}
                    </div>
                  </div>

                  <div className="space-y-2">
                    <Label>주소</Label>
                    {isEditing ? (
                      <Input
                        value={formData.address}
                        onChange={(e) => setFormData({ ...formData, address: e.target.value })}
                      />
                    ) : (
                      <p>{formData.address}</p>
                    )}
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label>대표번호</Label>
                      {isEditing ? (
                        <Input
                          value={formData.phone}
                          onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                        />
                      ) : (
                        <p>{formData.phone}</p>
                      )}
                    </div>
                    <div className="space-y-2">
                      <Label>홈페이지</Label>
                      {isEditing ? (
                        <Input
                          value={formData.website}
                          onChange={(e) => setFormData({ ...formData, website: e.target.value })}
                        />
                      ) : (
                        <p>{formData.website || "없음"}</p>
                      )}
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <User className="h-5 w-5" />
                    담당자 정보
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="space-y-2">
                    <Label>담당자</Label>
                    {isEditing ? (
                      <Input
                        value={formData.manager}
                        onChange={(e) => setFormData({ ...formData, manager: e.target.value })}
                      />
                    ) : (
                      <p className="font-medium">{formData.manager}</p>
                    )}
                  </div>
                  <div className="space-y-2">
                    <Label>담당자 연락처</Label>
                    {isEditing ? (
                      <Input
                        value={formData.managerPhone}
                        onChange={(e) => setFormData({ ...formData, managerPhone: e.target.value })}
                      />
                    ) : (
                      <p>{formData.managerPhone}</p>
                    )}
                  </div>
                  <div className="space-y-2">
                    <Label>거래개시일</Label>
                    {isEditing ? (
                      <Input
                        type="date"
                        value={formData.contractDate}
                        onChange={(e) => setFormData({ ...formData, contractDate: e.target.value })}
                      />
                    ) : (
                      <p>{formData.contractDate}</p>
                    )}
                  </div>
                  <div className="space-y-2">
                    <Label>고객사 구분</Label>
                    {isEditing ? (
                      <Select
                        value={formData.customerType}
                        onValueChange={(value) => setFormData({ ...formData, customerType: value })}
                      >
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="기존">기존</SelectItem>
                          <SelectItem value="신규">신규</SelectItem>
                        </SelectContent>
                      </Select>
                    ) : (
                      <Badge variant={formData.customerType === "신규" ? "default" : "secondary"}>
                        {formData.customerType}
                      </Badge>
                    )}
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* 거래 조건 및 참고사항 */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <CreditCard className="h-5 w-5" />
                    거래 조건
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    <Label>지급조건</Label>
                    {isEditing ? (
                      <Textarea
                        value={formData.paymentTerms}
                        onChange={(e) => setFormData({ ...formData, paymentTerms: e.target.value })}
                        rows={3}
                      />
                    ) : (
                      <p className="text-sm bg-gray-50 p-3 rounded">{formData.paymentTerms}</p>
                    )}
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>참고사항</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    <Label>메모</Label>
                    {isEditing ? (
                      <Textarea
                        value={formData.notes}
                        onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                        rows={3}
                        placeholder="회사 관련 중요 정보나 특이사항을 기록하세요"
                      />
                    ) : (
                      <p className="text-sm bg-gray-50 p-3 rounded">{formData.notes}</p>
                    )}
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          <TabsContent value="sales" className="space-y-6">
            {/* 매출 요약 */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <Card>
                <CardContent className="p-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-gray-600">총 매출액</p>
                      <p className="text-2xl font-bold">{(totalSales / 100000000).toFixed(1)}억원</p>
                    </div>
                    <DollarSign className="h-8 w-8 text-green-500" />
                  </div>
                </CardContent>
              </Card>
              <Card>
                <CardContent className="p-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-gray-600">총 매출량</p>
                      <p className="text-2xl font-bold">{totalVolume.toLocaleString()}kg</p>
                    </div>
                    <BarChart3 className="h-8 w-8 text-blue-500" />
                  </div>
                </CardContent>
              </Card>
              <Card>
                <CardContent className="p-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-gray-600">총 주문건수</p>
                      <p className="text-2xl font-bold">{totalOrders}건</p>
                    </div>
                    <FileText className="h-8 w-8 text-purple-500" />
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* 월별 매출 현황 */}
            <Card>
              <CardHeader>
                <CardTitle>월별 매출 현황</CardTitle>
                <CardDescription>최근 6개월 매출 데이터</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {salesData.map((data, index) => (
                    <div key={index} className="flex items-center justify-between p-4 border rounded-lg">
                      <div className="flex items-center space-x-4">
                        <div className="w-16 text-sm font-medium">{data.month}</div>
                        <div className="flex-1">
                          <div className="flex justify-between text-sm mb-1">
                            <span>매출액: {(data.sales / 100000000).toFixed(1)}억원</span>
                            <span>매출량: {data.volume}kg</span>
                            <span>주문: {data.orders}건</span>
                          </div>
                          <div className="w-full bg-gray-200 rounded-full h-2">
                            <div
                              className="bg-blue-600 h-2 rounded-full"
                              style={{ width: `${(data.sales / Math.max(...salesData.map((d) => d.sales))) * 100}%` }}
                            ></div>
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="reports" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <FileText className="h-5 w-5" />
                  관련 영업일지
                </CardTitle>
                <CardDescription>이 회사와 관련된 영업일지 목록</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {relatedReports.map((report) => (
                    <div key={report.id} className="border rounded-lg p-4">
                      <div className="flex justify-between items-start mb-2">
                        <div className="flex items-center space-x-2">
                          <Badge variant={report.contactType === "대면" ? "default" : "secondary"}>
                            {report.contactType}
                          </Badge>
                          <span className="text-sm text-gray-500">{report.date}</span>
                        </div>
                        <Badge
                          variant="outline"
                          className={
                            report.status === "완료"
                              ? "border-green-500 text-green-700"
                              : "border-blue-500 text-blue-700"
                          }
                        >
                          {report.status}
                        </Badge>
                      </div>
                      <p className="font-medium mb-1">{report.product}</p>
                      <p className="text-sm text-gray-600">{report.summary}</p>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="analysis" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>매출 분석</CardTitle>
                <CardDescription>회사별 매출 트렌드 및 분석</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="h-64 flex items-center justify-center bg-gray-50 rounded-lg">
                  <div className="text-center">
                    <BarChart3 className="h-12 w-12 text-gray-400 mx-auto mb-2" />
                    <p className="text-sm text-gray-500">매출 분석 차트 영역</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </main>
    </div>
  )
}
