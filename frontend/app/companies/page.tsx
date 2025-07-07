"use client"

import { useState } from "react"
import { Search, Plus, Building2, Phone, MapPin, Calendar, DollarSign, Eye, Edit } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import Link from "next/link"

// 샘플 회사 데이터
const sampleCompanies = [
  {
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
    monthlySales: 150000000,
    lastContact: "2025-01-07",
    status: "활성",
  },
  {
    id: 2,
    name: "(주)사세",
    code: "C0000127",
    sapCode: "1114756",
    smCode: "62539",
    type: "가공장",
    industry: "축육(가공장)",
    ceo: "박대표",
    address: "충북 청주시 흥덕구 산업로 456",
    phone: "043-534-0900",
    manager: "최담당",
    managerPhone: "010-2345-6789",
    establishedDate: "2010-08-20",
    contractDate: "2023-01-15",
    paymentTerms: "월말 마감, 45일이내, 어음결제",
    customerType: "기존",
    website: "",
    monthlySales: 89000000,
    lastContact: "2025-01-06",
    status: "활성",
  },
  {
    id: 3,
    name: "푸라닭 본사",
    code: "C0000128",
    sapCode: "1114757",
    smCode: "62540",
    type: "프랜차이즈",
    industry: "외식업",
    ceo: "정대표",
    address: "서울시 송파구 올림픽로 789",
    phone: "02-3456-7890",
    manager: "김매니저",
    managerPhone: "010-3456-7890",
    establishedDate: "2018-05-10",
    contractDate: "2024-11-20",
    paymentTerms: "15일단위 마감, 30일이내, 현금결제",
    customerType: "신규",
    website: "www.puradak.co.kr",
    monthlySales: 320000000,
    lastContact: "2025-01-05",
    status: "활성",
  },
  {
    id: 4,
    name: "움버거",
    code: "C0000129",
    sapCode: "1114758",
    smCode: "62541",
    type: "프랜차이즈",
    industry: "외식업",
    ceo: "한대표",
    address: "서울시 마포구 홍대로 321",
    phone: "02-4567-8901",
    manager: "이팀장",
    managerPhone: "010-4567-8901",
    establishedDate: "2020-12-01",
    contractDate: "2024-08-15",
    paymentTerms: "월말 마감, 30일이내, 현금결제",
    customerType: "신규",
    website: "www.umburger.co.kr",
    monthlySales: 45000000,
    lastContact: "2025-01-04",
    status: "활성",
  },
]

export default function CompaniesListPage() {
  const [searchTerm, setSearchTerm] = useState("")
  const [filterType, setFilterType] = useState("all")
  const [filterStatus, setFilterStatus] = useState("all")

  const filteredCompanies = sampleCompanies.filter((company) => {
    const matchesSearch =
      company.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      company.code.toLowerCase().includes(searchTerm.toLowerCase()) ||
      company.industry.toLowerCase().includes(searchTerm.toLowerCase())
    const matchesType = filterType === "all" || company.type === filterType
    const matchesStatus = filterStatus === "all" || company.status === filterStatus

    return matchesSearch && matchesType && matchesStatus
  })

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">회사 관리</h1>
              <p className="text-gray-600">거래처 및 고객사 정보 관리</p>
            </div>
            <div className="flex items-center space-x-4">
              <Link href="/">
                <Button variant="outline">대시보드</Button>
              </Link>
              <Button>
                <Plus className="h-4 w-4 mr-2" />
                회사 등록
              </Button>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* 통계 카드 */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-6">
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">전체 회사</p>
                  <p className="text-2xl font-bold">{sampleCompanies.length}</p>
                </div>
                <Building2 className="h-8 w-8 text-blue-500" />
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">활성 거래처</p>
                  <p className="text-2xl font-bold">{sampleCompanies.filter((c) => c.status === "활성").length}</p>
                </div>
                <Badge className="bg-green-100 text-green-800">활성</Badge>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">신규 고객</p>
                  <p className="text-2xl font-bold">
                    {sampleCompanies.filter((c) => c.customerType === "신규").length}
                  </p>
                </div>
                <Badge className="bg-blue-100 text-blue-800">신규</Badge>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">월 평균 매출</p>
                  <p className="text-2xl font-bold">
                    {Math.round(
                      (sampleCompanies.reduce((sum, c) => sum + c.monthlySales, 0) /
                        sampleCompanies.length /
                        100000000) *
                        10,
                    ) / 10}
                    억
                  </p>
                </div>
                <DollarSign className="h-8 w-8 text-green-500" />
              </div>
            </CardContent>
          </Card>
        </div>

        {/* 검색 및 필터 */}
        <Card className="mb-6">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Search className="h-5 w-5" />
              검색 및 필터
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div className="md:col-span-2">
                <Input
                  placeholder="회사명, 회사코드, 업종으로 검색..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="w-full"
                />
              </div>
              <Select value={filterType} onValueChange={setFilterType}>
                <SelectTrigger>
                  <SelectValue placeholder="회사 유형" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">전체</SelectItem>
                  <SelectItem value="가공장">가공장</SelectItem>
                  <SelectItem value="프랜차이즈">프랜차이즈</SelectItem>
                  <SelectItem value="도소매">도소매</SelectItem>
                </SelectContent>
              </Select>
              <Select value={filterStatus} onValueChange={setFilterStatus}>
                <SelectTrigger>
                  <SelectValue placeholder="상태" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">전체</SelectItem>
                  <SelectItem value="활성">활성</SelectItem>
                  <SelectItem value="비활성">비활성</SelectItem>
                  <SelectItem value="보류">보류</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </CardContent>
        </Card>

        {/* 회사 목록 */}
        <Card>
          <CardHeader>
            <div className="flex justify-between items-center">
              <div>
                <CardTitle>회사 목록</CardTitle>
                <CardDescription>총 {filteredCompanies.length}개 회사</CardDescription>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {filteredCompanies.map((company) => (
                <div key={company.id} className="border rounded-lg p-6 hover:bg-gray-50 transition-colors">
                  <div className="flex justify-between items-start mb-4">
                    <div className="flex items-center space-x-4">
                      <div>
                        <h3 className="font-semibold text-xl">{company.name}</h3>
                        <div className="flex items-center space-x-2 mt-1">
                          <span className="text-sm text-gray-500">코드: {company.code}</span>
                          <span className="text-sm text-gray-500">SAP: {company.sapCode}</span>
                        </div>
                      </div>
                      <Badge variant={company.type === "프랜차이즈" ? "default" : "secondary"}>{company.type}</Badge>
                      <Badge variant="outline" className="border-green-500 text-green-700">
                        {company.status}
                      </Badge>
                    </div>
                    <div className="flex items-center space-x-2">
                      <Link href={`/companies/${company.id}`}>
                        <Button variant="outline" size="sm">
                          <Eye className="h-4 w-4 mr-1" />
                          상세
                        </Button>
                      </Link>
                      <Button variant="outline" size="sm">
                        <Edit className="h-4 w-4 mr-1" />
                        수정
                      </Button>
                    </div>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-4">
                    <div className="flex items-center text-sm text-gray-600">
                      <Building2 className="h-4 w-4 mr-2" />
                      {company.industry}
                    </div>
                    <div className="flex items-center text-sm text-gray-600">
                      <Phone className="h-4 w-4 mr-2" />
                      {company.phone}
                    </div>
                    <div className="flex items-center text-sm text-gray-600">
                      <MapPin className="h-4 w-4 mr-2" />
                      {company.address.split(" ").slice(0, 2).join(" ")}
                    </div>
                    <div className="flex items-center text-sm text-gray-600">
                      <Calendar className="h-4 w-4 mr-2" />
                      계약: {company.contractDate}
                    </div>
                  </div>

                  <div className="flex justify-between items-center">
                    <div className="flex items-center space-x-4">
                      <div className="text-sm">
                        <span className="text-gray-500">담당자:</span>
                        <span className="ml-1 font-medium">{company.manager}</span>
                      </div>
                      <div className="text-sm">
                        <span className="text-gray-500">월 매출:</span>
                        <span className="ml-1 font-medium text-blue-600">
                          {(company.monthlySales / 100000000).toFixed(1)}억원
                        </span>
                      </div>
                    </div>
                    <div className="text-xs text-gray-500">최근 연락: {company.lastContact}</div>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </main>
    </div>
  )
}
