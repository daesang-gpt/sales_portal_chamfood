"use client"

import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Checkbox } from "@/components/ui/checkbox"
import { ArrowLeft, Save, Loader2 } from "lucide-react"
import Link from "next/link"
import { companyApi, Company } from "@/lib/api"
import { useToast } from "@/hooks/use-toast"
import { LocationSelect } from "@/components/ui/location-select"

export default function NewCompanyPage() {
  const router = useRouter()
  const { toast } = useToast()
  const [loading, setLoading] = useState(false)
  // SAP코드여부 체크박스 상태
  const [sapHasPurchase, setSapHasPurchase] = useState(false)
  const [sapHasSales, setSapHasSales] = useState(false)
  
  const [formData, setFormData] = useState({
    // 필수 필드
    company_code: "",
    company_name: "",
    // 기본정보
    customer_classification: "" as '기존' | '신규' | '이탈' | '기타' | '',
    company_type: "" as '개인' | '법인' | '',
    tax_id: "",
    established_date: "",
    ceo_name: "",
    head_address: "",
    city_district: "",
    processing_address: "",
    main_phone: "",
    industry_name: "",
    products: "",
    website: "",
    remarks: "",
    // SAP정보
    sap_code_type: "",
    company_code_sap: "",
    biz_code: "",
    biz_name: "",
    department_code: "",
    department: "",
    employee_number: "",
    employee_name: "",
    distribution_type_sap_code: "",
    distribution_type_sap: "",
    contact_person: "",
    contact_phone: "",
    code_create_date: "",
    transaction_start_date: "",
    payment_terms: "",
  })

  const handleInputChange = (field: string, value: string) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }))
  }

  // SAP코드여부 체크박스 핸들러
  const handleSapCodeTypeChange = (purchase: boolean, sales: boolean) => {
    setSapHasPurchase(purchase)
    setSapHasSales(sales)
    
    // 체크 상태에 따라 sap_code_type 값 계산
    let sapCodeType: string | null = null
    if (purchase && sales) {
      sapCodeType = '매입매출'
    } else if (purchase) {
      sapCodeType = '매입'
    } else if (sales) {
      sapCodeType = '매출'
    }
    
    setFormData(prev => ({
      ...prev,
      sap_code_type: sapCodeType || ''
    }))
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    // 필수 필드 검증
    if (!formData.company_code.trim()) {
      toast({
        title: "오류",
        description: "회사코드는 필수 입력 항목입니다.",
        variant: "destructive"
      })
      return
    }

    if (!formData.company_name.trim()) {
      toast({
        title: "오류",
        description: "회사명은 필수 입력 항목입니다.",
        variant: "destructive"
      })
      return
    }

    try {
      setLoading(true)
      
      // 빈 문자열을 undefined로 변환하여 API에 전송하지 않음
      const cleanData: any = {}
      Object.keys(formData).forEach(key => {
        const value = formData[key as keyof typeof formData]
        if (value !== '' && value !== null) {
          cleanData[key] = value
        }
      })
      
      await companyApi.createCompany(cleanData)
      
      toast({
        title: "성공",
        description: "회사가 성공적으로 등록되었습니다.",
      })
      
      router.push("/companies")
    } catch (error) {
      console.error("회사 등록 오류:", error)
      toast({
        title: "오류",
        description: "회사 등록 중 오류가 발생했습니다. 다시 시도해주세요.",
        variant: "destructive"
      })
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center space-x-4">
        <Button variant="ghost" size="sm" asChild>
          <Link href="/companies">
            <ArrowLeft className="mr-2 h-4 w-4" />
            목록으로
          </Link>
        </Button>
        <h1 className="text-3xl font-bold">회사 등록</h1>
      </div>

      <form onSubmit={handleSubmit}>
        <div className="grid gap-6 md:grid-cols-2">
          {/* 기본 정보 */}
          <Card>
            <CardHeader>
              <CardTitle>기본 정보</CardTitle>
              <CardDescription>회사의 기본적인 정보를 입력해주세요.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="company_code">회사코드 *</Label>
                <Input
                  id="company_code"
                  value={formData.company_code}
                  onChange={(e) => handleInputChange("company_code", e.target.value)}
                  placeholder="예: C0000001"
                  required
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="company_name">회사명 *</Label>
                <Input
                  id="company_name"
                  value={formData.company_name}
                  onChange={(e) => handleInputChange("company_name", e.target.value)}
                  placeholder="회사명을 입력하세요"
                  required
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="customer_classification">고객분류</Label>
                <Select value={formData.customer_classification || undefined} onValueChange={(value) => handleInputChange("customer_classification", value)}>
                  <SelectTrigger>
                    <SelectValue placeholder="고객분류를 선택하세요" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="기존">기존</SelectItem>
                    <SelectItem value="신규">신규</SelectItem>
                    <SelectItem value="이탈">이탈</SelectItem>
                    <SelectItem value="기타">기타</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label htmlFor="company_type">회사유형</Label>
                <Select value={formData.company_type || undefined} onValueChange={(value) => handleInputChange("company_type", value)}>
                  <SelectTrigger>
                    <SelectValue placeholder="회사유형을 선택하세요" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="개인">개인</SelectItem>
                    <SelectItem value="법인">법인</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label htmlFor="tax_id">사업자등록번호</Label>
                <Input
                  id="tax_id"
                  value={formData.tax_id}
                  onChange={(e) => handleInputChange("tax_id", e.target.value)}
                  placeholder="사업자등록번호를 입력하세요"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="established_date">설립일</Label>
                <Input
                  id="established_date"
                  type="date"
                  value={formData.established_date}
                  onChange={(e) => handleInputChange("established_date", e.target.value)}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="ceo_name">대표자명</Label>
                <Input
                  id="ceo_name"
                  value={formData.ceo_name}
                  onChange={(e) => handleInputChange("ceo_name", e.target.value)}
                  placeholder="대표자명을 입력하세요"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="head_address">본사 주소</Label>
                <Textarea
                  id="head_address"
                  value={formData.head_address}
                  onChange={(e) => handleInputChange("head_address", e.target.value)}
                  placeholder="본사 주소를 입력하세요"
                  rows={2}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="city_district">시/구</Label>
                <LocationSelect
                  value={formData.city_district}
                  onChange={(value) => handleInputChange("city_district", value)}
                  placeholder="지역을 선택하세요"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="processing_address">공장 주소</Label>
                <Textarea
                  id="processing_address"
                  value={formData.processing_address}
                  onChange={(e) => handleInputChange("processing_address", e.target.value)}
                  placeholder="공장 주소를 입력하세요"
                  rows={2}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="main_phone">대표전화</Label>
                <Input
                  id="main_phone"
                  value={formData.main_phone}
                  onChange={(e) => handleInputChange("main_phone", e.target.value)}
                  placeholder="대표전화번호를 입력하세요"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="industry_name">업종명</Label>
                <Input
                  id="industry_name"
                  value={formData.industry_name}
                  onChange={(e) => handleInputChange("industry_name", e.target.value)}
                  placeholder="업종명을 입력하세요"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="products">주요제품</Label>
                <Textarea
                  id="products"
                  value={formData.products}
                  onChange={(e) => handleInputChange("products", e.target.value)}
                  placeholder="주요제품을 입력하세요"
                  rows={3}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="website">웹사이트</Label>
                <Input
                  id="website"
                  value={formData.website}
                  onChange={(e) => handleInputChange("website", e.target.value)}
                  placeholder="https://example.com"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="remarks">참고사항</Label>
                <Textarea
                  id="remarks"
                  value={formData.remarks}
                  onChange={(e) => handleInputChange("remarks", e.target.value)}
                  placeholder="참고사항을 입력하세요"
                  rows={4}
                />
              </div>
            </CardContent>
          </Card>

          {/* SAP 정보 */}
          <Card>
            <CardHeader>
              <CardTitle>SAP 정보</CardTitle>
              <CardDescription>SAP 관련 정보를 입력해주세요.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label>SAP코드여부</Label>
                <div className="flex items-center space-x-4">
                  <div className="flex items-center space-x-2">
                    <Checkbox
                      id="sap_has_purchase"
                      checked={sapHasPurchase}
                      onCheckedChange={(checked) => {
                        handleSapCodeTypeChange(checked === true, sapHasSales)
                      }}
                    />
                    <Label htmlFor="sap_has_purchase" className="font-normal cursor-pointer">
                      매입
                    </Label>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Checkbox
                      id="sap_has_sales"
                      checked={sapHasSales}
                      onCheckedChange={(checked) => {
                        handleSapCodeTypeChange(sapHasPurchase, checked === true)
                      }}
                    />
                    <Label htmlFor="sap_has_sales" className="font-normal cursor-pointer">
                      매출
                    </Label>
                  </div>
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="company_code_sap">SAP거래처코드</Label>
                <Input
                  id="company_code_sap"
                  value={formData.company_code_sap}
                  onChange={(e) => handleInputChange("company_code_sap", e.target.value)}
                  placeholder="SAP거래처코드를 입력하세요"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="biz_code">사업</Label>
                <Input
                  id="biz_code"
                  value={formData.biz_code}
                  onChange={(e) => handleInputChange("biz_code", e.target.value)}
                  placeholder="사업 코드를 입력하세요"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="biz_name">사업부</Label>
                <Input
                  id="biz_name"
                  value={formData.biz_name}
                  onChange={(e) => handleInputChange("biz_name", e.target.value)}
                  placeholder="사업부명을 입력하세요"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="department_code">지점/팀</Label>
                <Input
                  id="department_code"
                  value={formData.department_code}
                  onChange={(e) => handleInputChange("department_code", e.target.value)}
                  placeholder="지점/팀 코드를 입력하세요"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="department">팀명</Label>
                <Input
                  id="department"
                  value={formData.department}
                  onChange={(e) => handleInputChange("department", e.target.value)}
                  placeholder="팀명을 입력하세요"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="employee_number">사원번호</Label>
                <Input
                  id="employee_number"
                  value={formData.employee_number}
                  onChange={(e) => handleInputChange("employee_number", e.target.value)}
                  placeholder="사원번호를 입력하세요"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="employee_name">영업 사원</Label>
                <Input
                  id="employee_name"
                  value={formData.employee_name}
                  onChange={(e) => handleInputChange("employee_name", e.target.value)}
                  placeholder="영업 사원명을 입력하세요"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="distribution_type_sap_code">유통형태코드</Label>
                <Input
                  id="distribution_type_sap_code"
                  value={formData.distribution_type_sap_code}
                  onChange={(e) => handleInputChange("distribution_type_sap_code", e.target.value)}
                  placeholder="유통형태코드를 입력하세요"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="distribution_type_sap">유통형태</Label>
                <Input
                  id="distribution_type_sap"
                  value={formData.distribution_type_sap}
                  onChange={(e) => handleInputChange("distribution_type_sap", e.target.value)}
                  placeholder="유통형태를 입력하세요"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="contact_person">거래처 담당자</Label>
                <Input
                  id="contact_person"
                  value={formData.contact_person}
                  onChange={(e) => handleInputChange("contact_person", e.target.value)}
                  placeholder="거래처 담당자명을 입력하세요"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="contact_phone">담당자 연락처</Label>
                <Input
                  id="contact_phone"
                  value={formData.contact_phone}
                  onChange={(e) => handleInputChange("contact_phone", e.target.value)}
                  placeholder="담당자 연락처를 입력하세요"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="code_create_date">코드생성일</Label>
                <Input
                  id="code_create_date"
                  type="date"
                  value={formData.code_create_date}
                  onChange={(e) => handleInputChange("code_create_date", e.target.value)}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="transaction_start_date">거래시작일</Label>
                <Input
                  id="transaction_start_date"
                  type="date"
                  value={formData.transaction_start_date}
                  onChange={(e) => handleInputChange("transaction_start_date", e.target.value)}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="payment_terms">결제조건</Label>
                <Input
                  id="payment_terms"
                  value={formData.payment_terms}
                  onChange={(e) => handleInputChange("payment_terms", e.target.value)}
                  placeholder="결제조건을 입력하세요"
                />
              </div>
            </CardContent>
          </Card>
        </div>

        <div className="flex justify-end space-x-4 mt-6">
          <Button variant="outline" type="button" asChild>
            <Link href="/companies">취소</Link>
          </Button>
          <Button type="submit" disabled={loading}>
            {loading ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                등록 중...
              </>
            ) : (
              <>
                <Save className="mr-2 h-4 w-4" />
                회사 등록
              </>
            )}
          </Button>
        </div>
      </form>
    </div>
  )
}
