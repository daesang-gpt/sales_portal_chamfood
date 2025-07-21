"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Search, Plus, Eye, Building2, Phone, MapPin } from "lucide-react"
import Link from "next/link"

const prospects = {
  가공장: [
    {
      id: 1,
      name: "대한육가공",
      location: "경기도 안양시",
      contact: "031-123-4567",
      products: "소시지, 햄류",
      status: "미접촉",
      priority: "높음",
      hasOurCustomer: false,
    },
    {
      id: 2,
      name: "프리미엄미트",
      location: "충남 천안시",
      contact: "041-987-6543",
      products: "정육, 가공육",
      status: "연락완료",
      priority: "중간",
      hasOurCustomer: true,
    },
  ],
  프랜차이즈: [
    {
      id: 3,
      name: "맛있는치킨",
      location: "서울시 강남구",
      contact: "02-555-1234",
      products: "치킨, 닭고기",
      status: "미접촉",
      priority: "높음",
      hasOurCustomer: false,
    },
    {
      id: 4,
      name: "한우마을",
      location: "부산시 해운대구",
      contact: "051-777-8888",
      products: "한우, 소고기",
      status: "협의중",
      priority: "높음",
      hasOurCustomer: true,
    },
  ],
  도소매: [
    {
      id: 5,
      name: "신선마트",
      location: "대구시 중구",
      contact: "053-222-3333",
      products: "정육, 냉동육",
      status: "미접촉",
      priority: "낮음",
      hasOurCustomer: false,
    },
  ],
}

const industryStats = {
  가공장: { total: 150, ourCustomers: 45, ratio: 30 },
  프랜차이즈: { total: 280, ourCustomers: 84, ratio: 30 },
  도소매: { total: 520, ourCustomers: 104, ratio: 20 },
}

export default function ProspectsPage() {
  const [searchTerm, setSearchTerm] = useState("")
  const [activeTab, setActiveTab] = useState("가공장")

  const filteredProspects = prospects[activeTab as keyof typeof prospects].filter(
    (prospect) =>
      prospect.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      prospect.location.toLowerCase().includes(searchTerm.toLowerCase()),
  )

  const getStatusColor = (status: string) => {
    switch (status) {
      case "미접촉":
        return "secondary"
      case "연락완료":
        return "default"
      case "협의중":
        return "destructive"
      default:
        return "secondary"
    }
  }

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case "높음":
        return "destructive"
      case "중간":
        return "default"
      case "낮음":
        return "secondary"
      default:
        return "secondary"
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold">업계 업체 리스트</h1>
        <Button asChild>
          <Link href="/prospects/new">
            <Plus className="mr-2 h-4 w-4" />
            업체 등록
          </Link>
        </Button>
      </div>

      {/* 업계별 통계 */}
      <div className="grid gap-4 md:grid-cols-3">
        {Object.entries(industryStats).map(([industry, stats]) => (
          <Card key={industry}>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">{industry}</CardTitle>
              <Building2 className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.total}개사</div>
              <div className="flex items-center space-x-2 text-xs text-muted-foreground">
                <span>자사 거래: {stats.ourCustomers}개사</span>
                <Badge variant="outline" className="text-xs">
                  {stats.ratio}%
                </Badge>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      <Card>
        <CardHeader>
          <CardTitle>신규 고객사 발굴 리스트</CardTitle>
          <CardDescription>업계별 잠재 고객사 정보 및 영업 현황</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center space-x-2 mb-4">
            <div className="relative flex-1">
              <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="업체명 또는 지역으로 검색..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-8"
              />
            </div>
          </div>

          <Tabs value={activeTab} onValueChange={setActiveTab}>
            <TabsList className="grid w-full grid-cols-3">
              <TabsTrigger value="가공장">가공장</TabsTrigger>
              <TabsTrigger value="프랜차이즈">프랜차이즈</TabsTrigger>
              <TabsTrigger value="도소매">도소매</TabsTrigger>
            </TabsList>

            {Object.entries(prospects).map(([category, categoryProspects]) => (
              <TabsContent key={category} value={category}>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>업체명</TableHead>
                      <TableHead>소재지</TableHead>
                      <TableHead>연락처</TableHead>
                      <TableHead>주요제품</TableHead>
                      <TableHead>영업상태</TableHead>
                      <TableHead>우선순위</TableHead>
                      <TableHead>자사거래</TableHead>
                      <TableHead>작업</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {filteredProspects.map((prospect) => (
                      <TableRow key={prospect.id}>
                        <TableCell className="font-medium">{prospect.name}</TableCell>
                        <TableCell>
                          <div className="flex items-center space-x-1">
                            <MapPin className="h-3 w-3" />
                            <span className="text-sm">{prospect.location}</span>
                          </div>
                        </TableCell>
                        <TableCell>
                          <div className="flex items-center space-x-1">
                            <Phone className="h-3 w-3" />
                            <span className="text-sm">{prospect.contact}</span>
                          </div>
                        </TableCell>
                        <TableCell>{prospect.products}</TableCell>
                        <TableCell>
                          <Badge variant={getStatusColor(prospect.status)}>{prospect.status}</Badge>
                        </TableCell>
                        <TableCell>
                          <Badge variant={getPriorityColor(prospect.priority)}>{prospect.priority}</Badge>
                        </TableCell>
                        <TableCell>
                          {prospect.hasOurCustomer ? (
                            <Badge variant="outline" className="text-green-600">
                              거래중
                            </Badge>
                          ) : (
                            <Badge variant="outline" className="text-gray-500">
                              미거래
                            </Badge>
                          )}
                        </TableCell>
                        <TableCell>
                          <Button variant="ghost" size="sm" asChild>
                            <Link href={`/prospects/${prospect.id}`}>
                              <Eye className="h-4 w-4" />
                            </Link>
                          </Button>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TabsContent>
            ))}
          </Tabs>
        </CardContent>
      </Card>
    </div>
  )
}
