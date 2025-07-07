"use client"

import { useState } from "react"
import { Search, Plus, Eye, Edit, Calendar, Building2, MapPin } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import Link from "next/link"

// 샘플 영업일지 데이터
const sampleReports = [
  {
    id: 1,
    date: "2025-01-07",
    company: "아이더스에프앤비",
    companyCode: "C0000126",
    contactType: "대면",
    location: "수도권",
    product: "국내산 닭",
    summary: "치킨 프랜차이즈 '푸라닭' 본사 미팅, 신메뉴 수입산 전환 검토",
    tags: ["프랜차이즈", "신메뉴", "수입산"],
    status: "진행중",
    createdAt: "2025-01-07 15:30",
  },
  {
    id: 2,
    date: "2025-01-06",
    company: "(주)사세",
    companyCode: "C0000127",
    contactType: "전화",
    location: "충북",
    product: "수입산 돼지고기",
    summary: "브라질산 원료육 패티 제조 관련 문의",
    tags: ["가공장", "브라질산", "패티"],
    status: "완료",
    createdAt: "2025-01-06 14:20",
  },
  {
    id: 3,
    date: "2025-01-05",
    company: "푸라닭 본사",
    companyCode: "C0000128",
    contactType: "대면",
    location: "서울",
    product: "태국산 통날개",
    summary: "깐풍치킨 메뉴용 태국산 통날개 제안",
    tags: ["프랜차이즈", "태국산", "통날개"],
    status: "검토중",
    createdAt: "2025-01-05 16:45",
  },
  {
    id: 4,
    date: "2025-01-04",
    company: "움버거",
    companyCode: "C0000129",
    contactType: "전화",
    location: "서울",
    product: "브라질산 원료육",
    summary: "버거 패티용 브라질산 원료육 공급 협의",
    tags: ["프랜차이즈", "브라질산", "패티"],
    status: "완료",
    createdAt: "2025-01-04 11:30",
  },
]

export default function ReportsListPage() {
  const [searchTerm, setSearchTerm] = useState("")
  const [filterType, setFilterType] = useState("all")
  const [filterStatus, setFilterStatus] = useState("all")

  const filteredReports = sampleReports.filter((report) => {
    const matchesSearch =
      report.company.toLowerCase().includes(searchTerm.toLowerCase()) ||
      report.product.toLowerCase().includes(searchTerm.toLowerCase()) ||
      report.summary.toLowerCase().includes(searchTerm.toLowerCase())
    const matchesType = filterType === "all" || report.contactType === filterType
    const matchesStatus = filterStatus === "all" || report.status === filterStatus

    return matchesSearch && matchesType && matchesStatus
  })

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">영업일지 관리</h1>
              <p className="text-gray-600">영업일지 작성 및 관리</p>
            </div>
            <div className="flex items-center space-x-4">
              <Link href="/">
                <Button variant="outline">대시보드</Button>
              </Link>
              <Link href="/reports/create">
                <Button>
                  <Plus className="h-4 w-4 mr-2" />
                  영업일지 작성
                </Button>
              </Link>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
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
                  placeholder="회사명, 품목, 내용으로 검색..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="w-full"
                />
              </div>
              <Select value={filterType} onValueChange={setFilterType}>
                <SelectTrigger>
                  <SelectValue placeholder="영업형태" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">전체</SelectItem>
                  <SelectItem value="대면">대면</SelectItem>
                  <SelectItem value="전화">전화</SelectItem>
                  <SelectItem value="이메일">이메일</SelectItem>
                </SelectContent>
              </Select>
              <Select value={filterStatus} onValueChange={setFilterStatus}>
                <SelectTrigger>
                  <SelectValue placeholder="진행상태" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">전체</SelectItem>
                  <SelectItem value="진행중">진행중</SelectItem>
                  <SelectItem value="완료">완료</SelectItem>
                  <SelectItem value="검토중">검토중</SelectItem>
                  <SelectItem value="보류">보류</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </CardContent>
        </Card>

        {/* 영업일지 목록 */}
        <Card>
          <CardHeader>
            <div className="flex justify-between items-center">
              <div>
                <CardTitle>영업일지 목록</CardTitle>
                <CardDescription>총 {filteredReports.length}건의 영업일지</CardDescription>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {filteredReports.map((report) => (
                <div key={report.id} className="border rounded-lg p-4 hover:bg-gray-50 transition-colors">
                  <div className="flex justify-between items-start mb-3">
                    <div className="flex items-center space-x-4">
                      <div>
                        <h3 className="font-semibold text-lg">{report.company}</h3>
                        <p className="text-sm text-gray-500">코드: {report.companyCode}</p>
                      </div>
                      <Badge variant={report.contactType === "대면" ? "default" : "secondary"}>
                        {report.contactType}
                      </Badge>
                      <Badge
                        variant="outline"
                        className={
                          report.status === "완료"
                            ? "border-green-500 text-green-700"
                            : report.status === "진행중"
                              ? "border-blue-500 text-blue-700"
                              : "border-yellow-500 text-yellow-700"
                        }
                      >
                        {report.status}
                      </Badge>
                    </div>
                    <div className="flex items-center space-x-2">
                      <Link href={`/reports/${report.id}`}>
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

                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-3">
                    <div className="flex items-center text-sm text-gray-600">
                      <Calendar className="h-4 w-4 mr-2" />
                      방문일: {report.date}
                    </div>
                    <div className="flex items-center text-sm text-gray-600">
                      <MapPin className="h-4 w-4 mr-2" />
                      {report.location}
                    </div>
                    <div className="flex items-center text-sm text-gray-600">
                      <Building2 className="h-4 w-4 mr-2" />
                      {report.product}
                    </div>
                  </div>

                  <p className="text-gray-700 mb-3">{report.summary}</p>

                  <div className="flex justify-between items-center">
                    <div className="flex flex-wrap gap-1">
                      {report.tags.map((tag, index) => (
                        <Badge key={index} variant="secondary" className="text-xs">
                          {tag}
                        </Badge>
                      ))}
                    </div>
                    <span className="text-xs text-gray-500">작성: {report.createdAt}</span>
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
