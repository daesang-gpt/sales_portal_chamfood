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
import { SapCodeSelect } from "@/components/ui/sap-code-select"
import { bizCodes, departmentCodes, employeeCodes, distributionTypeCodes, paymentTerms } from "@/lib/constants/sapCodes"
import { getUserFromToken } from "@/lib/auth"

export default function NewCompanyPage() {
  const router = useRouter()
  const { toast } = useToast()
  const [loading, setLoading] = useState(false)
  // SAP코드여부 체크박스 상태
  const [sapHasPurchase, setSapHasPurchase] = useState(false)
  const [sapHasSales, setSapHasSales] = useState(false)
  const [isViewer, setIsViewer] = useState(false)
  const [isCheckingRole, setIsCheckingRole] = useState(true)

  useEffect(() => {
    const currentUser = getUserFromToken();
    if (!currentUser) {
      router.push('/login');
      return;
    }
    if (currentUser.role === 'viewer') {
      setIsViewer(true);
      setIsCheckingRole(false);
      toast({
        title: "접근 불가",
        description: "뷰어 권한은 회사를 등록할 수 없습니다.",
        variant: "destructive"
      });
      router.replace('/companies');
      return;
    }
    setIsCheckingRole(false);
  }, [router, toast])
  
  const [formData, setFormData] = useState({
    // 필수 필드
    company_name: "",
    // 기본정보
    customer_classification: "" as '잠재' | '신규' | '기존' | '이탈' | '벤더' | '',
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
      // company_code는 제외 (백엔드에서 자동 생성)
      const cleanData: any = {}
      Object.keys(formData).forEach(key => {
        const value = formData[key as keyof typeof formData]
        if (key !== 'company_code' && value !== '' && value !== null) {
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

  if (isCheckingRole) {
    return (
      <div className="space-y-6">
        <div className="text-center text-muted-foreground py-12">권한을 확인하는 중입니다...</div>
      </div>
    )
  }

  if (isViewer) {
    return (
      <div className="space-y-6">
        <div className="text-center text-red-500 py-12">뷰어 권한은 회사를 등록할 수 없습니다.</div>
      </div>
    )
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
                <Label htmlFor="company_name" className="text-sm font-semibold text-foreground">회사명 *</Label>
                <Input
                  id="company_name"
                  value={formData.company_name}
                  onChange={(e) => handleInputChange("company_name", e.target.value)}
                  placeholder="회사명을 입력하세요"
                  required
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="customer_classification" className="text-sm font-semibold text-foreground">고객분류</Label>
                <Select value={formData.customer_classification || undefined} onValueChange={(value) => handleInputChange("customer_classification", value)}>
                  <SelectTrigger>
                    <SelectValue placeholder="고객분류를 선택하세요" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="잠재">잠재</SelectItem>
                    <SelectItem value="신규">신규</SelectItem>
                    <SelectItem value="기존">기존</SelectItem>
                    <SelectItem value="이탈">이탈</SelectItem>
                    <SelectItem value="벤더">벤더</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label htmlFor="company_type" className="text-sm font-semibold text-foreground">회사유형</Label>
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
                <Label htmlFor="tax_id" className="text-sm font-semibold text-foreground">사업자등록번호</Label>
                <Input
                  id="tax_id"
                  value={formData.tax_id}
                  onChange={(e) => handleInputChange("tax_id", e.target.value)}
                  placeholder="사업자등록번호를 입력하세요"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="established_date" className="text-sm font-semibold text-foreground">설립일</Label>
                <Input
                  id="established_date"
                  type="date"
                  value={formData.established_date}
                  onChange={(e) => handleInputChange("established_date", e.target.value)}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="ceo_name" className="text-sm font-semibold text-foreground">대표자명</Label>
                <Input
                  id="ceo_name"
                  value={formData.ceo_name}
                  onChange={(e) => handleInputChange("ceo_name", e.target.value)}
                  placeholder="대표자명을 입력하세요"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="head_address" className="text-sm font-semibold text-foreground">본사 주소</Label>
                <Textarea
                  id="head_address"
                  value={formData.head_address}
                  onChange={(e) => handleInputChange("head_address", e.target.value)}
                  placeholder="본사 주소를 입력하세요"
                  rows={2}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="city_district" className="text-sm font-semibold text-foreground">시/구</Label>
                <LocationSelect
                  value={formData.city_district}
                  onChange={(value) => handleInputChange("city_district", value)}
                  placeholder="지역을 선택하세요"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="processing_address" className="text-sm font-semibold text-foreground">공장 주소</Label>
                <Textarea
                  id="processing_address"
                  value={formData.processing_address}
                  onChange={(e) => handleInputChange("processing_address", e.target.value)}
                  placeholder="공장 주소를 입력하세요"
                  rows={2}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="main_phone" className="text-sm font-semibold text-foreground">대표전화</Label>
                <Input
                  id="main_phone"
                  value={formData.main_phone}
                  onChange={(e) => handleInputChange("main_phone", e.target.value)}
                  placeholder="대표전화번호를 입력하세요"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="industry_name" className="text-sm font-semibold text-foreground">업종명</Label>
                <Input
                  id="industry_name"
                  value={formData.industry_name}
                  onChange={(e) => handleInputChange("industry_name", e.target.value)}
                  placeholder="업종명을 입력하세요"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="products" className="text-sm font-semibold text-foreground">주요제품</Label>
                <Textarea
                  id="products"
                  value={formData.products}
                  onChange={(e) => handleInputChange("products", e.target.value)}
                  placeholder="주요제품을 입력하세요"
                  rows={3}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="website" className="text-sm font-semibold text-foreground">웹사이트</Label>
                <Input
                  id="website"
                  value={formData.website}
                  onChange={(e) => handleInputChange("website", e.target.value)}
                  placeholder="https://example.com"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="remarks" className="text-sm font-semibold text-foreground">참고사항</Label>
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
                <Label className="text-sm font-semibold text-foreground">SAP코드여부</Label>
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
                <Label htmlFor="company_code_sap" className="text-sm font-semibold text-foreground">SAP거래처코드</Label>
                <Input
                  id="company_code_sap"
                  value={formData.company_code_sap}
                  onChange={(e) => handleInputChange("company_code_sap", e.target.value)}
                  placeholder="SAP거래처코드를 입력하세요"
                />
              </div>

              <SapCodeSelect
                options={bizCodes}
                codeValue={formData.biz_code}
                nameValue={formData.biz_name}
                onCodeChange={(code) => handleInputChange("biz_code", code)}
                onNameChange={(name) => handleInputChange("biz_name", name)}
                codeLabel="사업"
                nameLabel="사업부"
                namePlaceholder="사업부를 선택하세요"
              />

              <SapCodeSelect
                options={departmentCodes}
                codeValue={formData.department_code}
                nameValue={formData.department}
                onCodeChange={(code) => handleInputChange("department_code", code)}
                onNameChange={(name) => handleInputChange("department", name)}
                codeLabel="지점/팀"
                nameLabel="팀명"
                namePlaceholder="팀명을 선택하세요"
              />

              <SapCodeSelect
                options={employeeCodes}
                codeValue={formData.employee_number}
                nameValue={formData.employee_name}
                onCodeChange={(code) => handleInputChange("employee_number", code)}
                onNameChange={(name) => handleInputChange("employee_name", name)}
                codeLabel="사원번호"
                nameLabel="영업 사원"
                namePlaceholder="영업 사원을 선택하세요"
              />

              <SapCodeSelect
                options={distributionTypeCodes}
                codeValue={formData.distribution_type_sap_code}
                nameValue={formData.distribution_type_sap}
                onCodeChange={(code) => handleInputChange("distribution_type_sap_code", code)}
                onNameChange={(name) => handleInputChange("distribution_type_sap", name)}
                codeLabel="유통형태코드"
                nameLabel="유통형태"
                namePlaceholder="유통형태를 선택하세요"
              />

              <div className="space-y-2">
                <Label htmlFor="contact_person" className="text-sm font-semibold text-foreground">거래처 담당자</Label>
                <Input
                  id="contact_person"
                  value={formData.contact_person}
                  onChange={(e) => handleInputChange("contact_person", e.target.value)}
                  placeholder="거래처 담당자명을 입력하세요"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="contact_phone" className="text-sm font-semibold text-foreground">담당자 연락처</Label>
                <Input
                  id="contact_phone"
                  value={formData.contact_phone}
                  onChange={(e) => handleInputChange("contact_phone", e.target.value)}
                  placeholder="담당자 연락처를 입력하세요"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="code_create_date" className="text-sm font-semibold text-foreground">코드생성일</Label>
                <Input
                  id="code_create_date"
                  type="date"
                  value={formData.code_create_date}
                  onChange={(e) => handleInputChange("code_create_date", e.target.value)}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="transaction_start_date" className="text-sm font-semibold text-foreground">거래시작일</Label>
                <Input
                  id="transaction_start_date"
                  type="date"
                  value={formData.transaction_start_date}
                  onChange={(e) => handleInputChange("transaction_start_date", e.target.value)}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="payment_terms" className="text-sm font-semibold text-foreground">결제조건</Label>
                <Select 
                  value={formData.payment_terms || undefined} 
                  onValueChange={(value) => handleInputChange("payment_terms", value)}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="결제조건을 선택하세요" />
                  </SelectTrigger>
                  <SelectContent>
                    {paymentTerms.map((term) => (
                      <SelectItem key={term} value={term}>
                        {term}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
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
