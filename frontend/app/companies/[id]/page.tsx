"use client"

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Separator } from "@/components/ui/separator"
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar } from "recharts"
import { ArrowLeft, Edit, Building2, Phone, MapPin, Calendar, DollarSign, Loader2 } from "lucide-react"
import Link from "next/link"
import { useParams } from "next/navigation"
import { companyApi, Company } from "@/lib/api"

// 회사 년간 매출/손익 데이터
const yearlyData = [
  { month: "1월", 매출: 45000000, 손익: 4500000 },
  { month: "2월", 매출: 52000000, 손익: 5200000 },
  { month: "3월", 매출: 48000000, 손익: 4800000 },
  { month: "4월", 매출: 61000000, 손익: 6100000 },
  { month: "5월", 매출: 58000000, 손익: 5800000 },
  { month: "6월", 매출: 67000000, 손익: 6700000 },
]

// 당사-회사 월간 매출 데이터
const monthlySalesData = [
  { month: "1월", 매출: 12000000 },
  { month: "2월", 매출: 15000000 },
  { month: "3월", 매출: 18000000 },
  { month: "4월", 매출: 22000000 },
  { month: "5월", 매출: 25000000 },
  { month: "6월", 매출: 28000000 },
]

export default function CompanyDetailPage() {
  const params = useParams()
  const [company, setCompany] = useState<Company | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const loadCompany = async () => {
      try {
        setLoading(true)
        setError(null)
        const companyData = await companyApi.getCompany(Number(params.id))
        setCompany(companyData)
      } catch (err) {
        setError('회사 정보를 불러오는 중 오류가 발생했습니다.')
        console.error('Error loading company:', err)
      } finally {
        setLoading(false)
      }
    }

    if (params.id) {
      loadCompany()
    }
  }, [params.id])

  // 데이터 매핑 헬퍼 함수
  const getCompanyDisplayName = (company: Company) => {
    return company.company_name || 'Unknown Company'
  }

  const getCompanyCode = (company: Company) => {
    return company.sales_diary_company_code || '-'
  }

  const getCompanySapCode = (company: Company) => {
    return company.company_code_sap || '-'
  }

  const getCompanyType = (company: Company) => {
    return company.company_type || '-'
  }

  const getCompanyEstablishDate = (company: Company) => {
    return company.established_date || '-'
  }

  const getCompanyRepresentative = (company: Company) => {
    return company.ceo_name || '-'
  }

  const getCompanyAddress = (company: Company) => {
    return company.address || '-'
  }

  const getCompanyContact = (company: Company) => {
    return company.main_phone || company.contact_phone || '-'
  }

  const getCompanyManager = (company: Company) => {
    return company.contact_person || '-'
  }

  const getCompanyManagerPhone = (company: Company) => {
    return company.contact_phone || '-'
  }

  const getCompanyDistributionType = (company: Company) => {
    return company.distribution_type_sap || '-'
  }

  const getCompanyMainProducts = (company: Company) => {
    return company.main_product || '-'
  }

  const getCompanyStartDate = (company: Company) => {
    return company.transaction_start_date || '-'
  }

  const getCompanyPaymentTerms = (company: Company) => {
    return company.payment_terms || '-'
  }

  const getCompanyCustomerType = (company: Company) => {
    return company.customer_classification || '-'
  }

  const getCompanyNotes = (company: Company) => {
    return company.remarks || '-'
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="flex items-center space-x-2">
          <Loader2 className="h-6 w-6 animate-spin" />
          <span>회사 정보를 불러오는 중...</span>
        </div>
      </div>
    )
  }

  if (error || !company) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <p className="text-red-500 mb-4">{error || '회사 정보를 찾을 수 없습니다.'}</p>
          <Button asChild>
            <Link href="/companies">목록으로 돌아가기</Link>
          </Button>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <Button variant="outline" size="sm" asChild>
            <Link href="/companies">
              <ArrowLeft className="mr-2 h-4 w-4" />
              목록으로
            </Link>
          </Button>
          <h1 className="text-3xl font-bold">{getCompanyDisplayName(company)}</h1>
          <Badge variant={getCompanyCustomerType(company) === "신규" ? "default" : "secondary"}>
            {getCompanyCustomerType(company)}
          </Badge>
        </div>
        <Button asChild>
          <Link href={`/companies/${company.id}/edit`}>
            <Edit className="mr-2 h-4 w-4" />
            수정
          </Link>
        </Button>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        {/* 회사 기본 정보 */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Building2 className="h-5 w-5" />
              <span>기본 정보</span>
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-sm font-medium text-muted-foreground">회사코드</p>
                <p className="text-lg">{getCompanyCode(company)}</p>
              </div>
              <div>
                <p className="text-sm font-medium text-muted-foreground">SAP코드</p>
                <p className="text-lg">{getCompanySapCode(company)}</p>
              </div>
              <div>
                <p className="text-sm font-medium text-muted-foreground">기업형태</p>
                <p className="text-lg">{getCompanyType(company)}</p>
              </div>
              <div>
                <p className="text-sm font-medium text-muted-foreground">설립일</p>
                <p className="text-lg">{getCompanyEstablishDate(company)}</p>
              </div>
            </div>

            <Separator />

            <div>
              <p className="text-sm font-medium text-muted-foreground mb-1">대표자명</p>
              <p className="text-lg">{getCompanyRepresentative(company)}</p>
            </div>

            <div>
              <p className="text-sm font-medium text-muted-foreground mb-1">주소</p>
              <div className="flex items-start space-x-2">
                <MapPin className="h-4 w-4 mt-1 text-muted-foreground" />
                <p className="text-lg">{getCompanyAddress(company)}</p>
              </div>
            </div>

            <div>
              <p className="text-sm font-medium text-muted-foreground mb-1">대표번호</p>
              <div className="flex items-center space-x-2">
                <Phone className="h-4 w-4 text-muted-foreground" />
                <p className="text-lg">{getCompanyContact(company)}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* 거래 정보 */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <DollarSign className="h-5 w-5" />
              <span>거래 정보</span>
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <p className="text-sm font-medium text-muted-foreground mb-1">담당자</p>
              <p className="text-lg">{getCompanyManager(company)}</p>
            </div>

            <div>
              <p className="text-sm font-medium text-muted-foreground mb-1">담당자 연락처</p>
              <div className="flex items-center space-x-2">
                <Phone className="h-4 w-4 text-muted-foreground" />
                <p className="text-lg">{getCompanyManagerPhone(company)}</p>
              </div>
            </div>

            <div>
              <p className="text-sm font-medium text-muted-foreground mb-1">유통형태</p>
              <p className="text-lg">{getCompanyDistributionType(company)}</p>
            </div>

            <div>
              <p className="text-sm font-medium text-muted-foreground mb-1">주생산품</p>
              <p className="text-lg">{getCompanyMainProducts(company)}</p>
            </div>

            <div>
              <p className="text-sm font-medium text-muted-foreground mb-1">거래개시일</p>
              <div className="flex items-center space-x-2">
                <Calendar className="h-4 w-4 text-muted-foreground" />
                <p className="text-lg">{getCompanyStartDate(company)}</p>
              </div>
            </div>

            <div>
              <p className="text-sm font-medium text-muted-foreground mb-1">지급조건</p>
              <p className="text-lg">{getCompanyPaymentTerms(company)}</p>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* 매출 차트 */}
      <div className="grid gap-6 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>회사 년간 매출/손익 그래프</CardTitle>
            <CardDescription>최근 6개월 매출 및 손익 현황</CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={yearlyData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="month" />
                <YAxis tickFormatter={(value) => `${(value / 10000000).toFixed(0)}천만`} />
                <Tooltip
                  formatter={(value: number, name: string) => [`${(value / 10000000).toFixed(1)}천만원`, name]}
                />
                <Line type="monotone" dataKey="매출" stroke="#8884d8" strokeWidth={2} />
                <Line type="monotone" dataKey="손익" stroke="#82ca9d" strokeWidth={2} />
              </LineChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>당사-회사 월간 매출 그래프</CardTitle>
            <CardDescription>당사와의 월간 거래 매출 현황</CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={monthlySalesData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="month" />
                <YAxis tickFormatter={(value) => `${(value / 10000000).toFixed(0)}천만`} />
                <Tooltip formatter={(value: number) => [`${(value / 10000000).toFixed(1)}천만원`, "매출"]} />
                <Bar dataKey="매출" fill="#8884d8" />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      {/* 참고사항 */}
      {getCompanyNotes(company) !== '-' && (
        <Card>
          <CardHeader>
            <CardTitle>참고사항</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-lg">{getCompanyNotes(company)}</p>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
