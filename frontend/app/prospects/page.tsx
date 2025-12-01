"use client"

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Search, Plus, Building2, Phone, MapPin, ExternalLink, Loader2 } from "lucide-react"
import Link from "next/link"
import { prospectCompanyApi, ProspectCompany, ProspectCompanyStats } from "@/lib/api"

const industryMap = {
  "축산물 가공장": "축산물 가공장",
  "식품 가공장": "식품 가공장",
  "도소매": "도소매",
} as const

type IndustryType = keyof typeof industryMap

export default function ProspectsPage() {
  const [searchTerm, setSearchTerm] = useState("")
  const [activeTab, setActiveTab] = useState<IndustryType>("축산물 가공장")
  const [prospects, setProspects] = useState<ProspectCompany[]>([])
  const [stats, setStats] = useState<ProspectCompanyStats>({})
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // 통계 데이터 로드
  useEffect(() => {
    const loadStats = async () => {
      try {
        const statsData = await prospectCompanyApi.getProspectCompanyStats()
        setStats(statsData)
      } catch (err) {
        console.error('통계 데이터 로드 오류:', err)
      }
    }
    loadStats()
  }, [])

  // 업체 목록 로드
  useEffect(() => {
    const loadProspects = async () => {
      try {
        setLoading(true)
        setError(null)
        const data = await prospectCompanyApi.getProspectCompanies(activeTab, searchTerm)
        setProspects(data)
      } catch (err) {
        setError(err instanceof Error ? err.message : '데이터를 불러오는 중 오류가 발생했습니다.')
        console.error('업체 목록 로드 오류:', err)
      } finally {
        setLoading(false)
      }
    }
    loadProspects()
  }, [activeTab, searchTerm])

  const getPriorityColor = (priority?: string) => {
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

  const handleNaverMapClick = (companyName: string) => {
    const url = `https://map.naver.com/p/search/${encodeURIComponent(companyName)}`
    window.open(url, '_blank')
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
        {Object.entries(industryMap).map(([industryKey, industryValue]) => {
          const industryStats = stats[industryValue] || { total: 0, ourCustomers: 0, ratio: 0 }
          return (
            <Card key={industryKey}>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">{industryKey}</CardTitle>
                <Building2 className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{industryStats.total}개사</div>
                <div className="flex items-center space-x-2 text-xs text-muted-foreground">
                  <span>자사 거래: {industryStats.ourCustomers}개사</span>
                  <Badge variant="outline" className="text-xs">
                    {industryStats.ratio}%
                  </Badge>
                </div>
              </CardContent>
            </Card>
          )
        })}
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

          <Tabs value={activeTab} onValueChange={(value) => setActiveTab(value as IndustryType)}>
            <TabsList className="grid w-full grid-cols-3">
              <TabsTrigger value="축산물 가공장">축산물 가공장</TabsTrigger>
              <TabsTrigger value="식품 가공장">식품 가공장</TabsTrigger>
              <TabsTrigger value="도소매">도소매</TabsTrigger>
            </TabsList>

            <TabsContent value={activeTab}>
              {loading ? (
                <div className="flex items-center justify-center py-8">
                  <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
                  <span className="ml-2 text-muted-foreground">로딩 중...</span>
                </div>
              ) : error ? (
                <div className="text-center py-8 text-red-600">{error}</div>
              ) : prospects.length === 0 ? (
                <div className="text-center py-8 text-muted-foreground">데이터가 없습니다.</div>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>업체명</TableHead>
                      <TableHead>소재지</TableHead>
                      <TableHead>전화번호</TableHead>
                      <TableHead>주요제품</TableHead>
                      <TableHead>우선순위</TableHead>
                      <TableHead>자사거래</TableHead>
                      <TableHead>작업</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {prospects.map((prospect) => (
                      <TableRow key={prospect.id}>
                        <TableCell className="font-medium">{prospect.company_name}</TableCell>
                        <TableCell>
                          <div className="flex items-center space-x-1">
                            <MapPin className="h-3 w-3" />
                            <span className="text-sm">{prospect.location || '-'}</span>
                          </div>
                        </TableCell>
                        <TableCell>
                          <div className="flex items-center space-x-1">
                            <Phone className="h-3 w-3" />
                            <span className="text-sm">{prospect.phone || '-'}</span>
                          </div>
                        </TableCell>
                        <TableCell>{prospect.main_products || '-'}</TableCell>
                        <TableCell>
                          {prospect.priority ? (
                            <Badge variant={getPriorityColor(prospect.priority)}>
                              {prospect.priority}
                            </Badge>
                          ) : (
                            '-'
                          )}
                        </TableCell>
                        <TableCell>
                          {prospect.has_transaction === '거래중' ? (
                            <Badge variant="outline" className="text-green-600">
                              거래중
                            </Badge>
                          ) : prospect.has_transaction === '미거래' ? (
                            <Badge variant="outline" className="text-gray-500">
                              미거래
                            </Badge>
                          ) : (
                            '-'
                          )}
                        </TableCell>
                        <TableCell>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleNaverMapClick(prospect.company_name)}
                          >
                            <ExternalLink className="h-4 w-4" />
                          </Button>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>
    </div>
  )
}
