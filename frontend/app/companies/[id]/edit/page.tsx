"use client"

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Checkbox } from "@/components/ui/checkbox"
import { Badge } from "@/components/ui/badge"
import { ArrowLeft, Save, Loader2, Building2, Phone, MapPin, Calendar, DollarSign } from "lucide-react"
import Link from "next/link"
import { useParams, useRouter } from "next/navigation"
import { companyApi, Company } from "@/lib/api"
import { toast } from "@/hooks/use-toast"

export default function CompanyEditPage() {
  const params = useParams()
  const router = useRouter()
  const [company, setCompany] = useState<Company | null>(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  
  // SAP코드여부 체크박스 상태
  const [sapHasPurchase, setSapHasPurchase] = useState(false)
  const [sapHasSales, setSapHasSales] = useState(false)

  // 폼 상태
  const [formData, setFormData] = useState({
    // 필수 필드
    company_code: '',
    company_name: '',
    // 기본정보
    customer_classification: '' as '기존' | '신규' | '이탈' | '기타' | '',
    company_type: '' as '개인' | '법인' | '',
    tax_id: '',
    established_date: '',
    ceo_name: '',
    head_address: '',
    city_district: '',
    processing_address: '',
    main_phone: '',
    industry_name: '',
    products: '',
    website: '',
    remarks: '',
    // SAP정보
    sap_code_type: '',
    company_code_sap: '',
    biz_code: '',
    biz_name: '',
    department_code: '',
    department: '',
    employee_number: '',
    employee_name: '',
    distribution_type_sap_code: '',
    distribution_type_sap: '',
    contact_person: '',
    contact_phone: '',
    code_create_date: '',
    transaction_start_date: '',
    payment_terms: '',
  })

  useEffect(() => {
    const loadCompany = async () => {
      try {
        setLoading(true)
        setError(null)
        const companyData = await companyApi.getCompany(params.id as string)
        setCompany(companyData)
        
        // 폼 데이터 초기화
        setFormData({
          company_code: companyData.company_code || '',
          company_name: companyData.company_name || '',
          customer_classification: companyData.customer_classification || '',
          company_type: companyData.company_type || '',
          tax_id: companyData.tax_id || '',
          established_date: companyData.established_date ? companyData.established_date.split('T')[0] : '',
          ceo_name: companyData.ceo_name || '',
          head_address: companyData.head_address || '',
          city_district: companyData.city_district || '',
          processing_address: companyData.processing_address || '',
          main_phone: companyData.main_phone || '',
          industry_name: companyData.industry_name || '',
          products: companyData.products || '',
          website: companyData.website || '',
          remarks: companyData.remarks || '',
          sap_code_type: companyData.sap_code_type || '',
          company_code_sap: companyData.company_code_sap || '',
          biz_code: companyData.biz_code || '',
          biz_name: companyData.biz_name || '',
          department_code: companyData.department_code || '',
          department: companyData.department || '',
          employee_number: companyData.employee_number || '',
          employee_name: companyData.employee_name || '',
          distribution_type_sap_code: companyData.distribution_type_sap_code || '',
          distribution_type_sap: companyData.distribution_type_sap || '',
          contact_person: companyData.contact_person || '',
          contact_phone: companyData.contact_phone || '',
          code_create_date: companyData.code_create_date ? companyData.code_create_date.split('T')[0] : '',
          transaction_start_date: companyData.transaction_start_date ? companyData.transaction_start_date.split('T')[0] : '',
          payment_terms: companyData.payment_terms || '',
        })
        
        // sap_code_type 값에 따라 체크박스 초기화
        const sapCodeType = companyData.sap_code_type
        if (sapCodeType === '매입매출') {
          setSapHasPurchase(true)
          setSapHasSales(true)
        } else if (sapCodeType === '매입') {
          setSapHasPurchase(true)
          setSapHasSales(false)
        } else if (sapCodeType === '매출') {
          setSapHasPurchase(false)
          setSapHasSales(true)
        } else {
          setSapHasPurchase(false)
          setSapHasSales(false)
        }
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
    
    try {
      setSaving(true)
      
      // 필수 필드 검증
      if (!formData.company_code.trim()) {
        toast({
          title: "오류",
          description: "회사코드는 필수 입력 항목입니다.",
          variant: "destructive",
        })
        return
      }

      if (!formData.company_name.trim()) {
        toast({
          title: "오류",
          description: "회사명은 필수 입력 항목입니다.",
          variant: "destructive",
        })
        return
      }

      // API 호출
      const cleanData: any = {}
      Object.keys(formData).forEach(key => {
        const value = formData[key as keyof typeof formData]
        if (value !== '' && value !== null) {
          cleanData[key] = value
        }
      })

      const updatedCompany = await companyApi.updateCompany(params.id as string, cleanData)
      
      toast({
        title: "성공",
        description: "회사 정보가 성공적으로 수정되었습니다.",
      })
      
      // 상세 페이지로 이동
      router.push(`/companies/${params.id}`)
      
    } catch (err) {
      console.error('Error updating company:', err)
      toast({
        title: "오류",
        description: "회사 정보 수정 중 오류가 발생했습니다.",
        variant: "destructive",
      })
    } finally {
      setSaving(false)
    }
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
            <Link href={`/companies/${params.id}`}>
              <ArrowLeft className="mr-2 h-4 w-4" />
              상세보기로
            </Link>
          </Button>
          <h1 className="text-3xl font-bold">회사 정보 수정</h1>
          <Badge variant="outline">{company.company_name}</Badge>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        <div className="grid gap-6 md:grid-cols-2">
          {/* 기본 정보 */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <Building2 className="h-5 w-5" />
                <span>기본 정보</span>
              </CardTitle>
              <CardDescription>회사의 기본적인 정보를 수정합니다.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="company_code">회사코드 *</Label>
                <Input
                  id="company_code"
                  value={formData.company_code}
                  onChange={(e) => handleInputChange('company_code', e.target.value)}
                  placeholder="회사코드"
                  required
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="company_name">회사명 *</Label>
                <Input
                  id="company_name"
                  value={formData.company_name}
                  onChange={(e) => handleInputChange('company_name', e.target.value)}
                  placeholder="회사명을 입력하세요"
                  required
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="customer_classification">고객분류</Label>
                  <Select value={formData.customer_classification || undefined} onValueChange={(value) => handleInputChange('customer_classification', value)}>
                    <SelectTrigger>
                      <SelectValue placeholder="고객분류 선택" />
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
                  <Select value={formData.company_type || undefined} onValueChange={(value) => handleInputChange('company_type', value)}>
                    <SelectTrigger>
                      <SelectValue placeholder="회사유형 선택" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="개인">개인</SelectItem>
                      <SelectItem value="법인">법인</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="tax_id">사업자등록번호</Label>
                <Input
                  id="tax_id"
                  value={formData.tax_id}
                  onChange={(e) => handleInputChange('tax_id', e.target.value)}
                  placeholder="사업자등록번호"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="established_date">설립일</Label>
                <Input
                  id="established_date"
                  type="date"
                  value={formData.established_date}
                  onChange={(e) => handleInputChange('established_date', e.target.value)}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="ceo_name">대표자명</Label>
                <Input
                  id="ceo_name"
                  value={formData.ceo_name}
                  onChange={(e) => handleInputChange('ceo_name', e.target.value)}
                  placeholder="대표자명"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="head_address">본사 주소</Label>
                <div className="flex items-start space-x-2">
                  <MapPin className="h-4 w-4 mt-3 text-muted-foreground" />
                  <Textarea
                    id="head_address"
                    value={formData.head_address}
                    onChange={(e) => handleInputChange('head_address', e.target.value)}
                    placeholder="본사 주소"
                    rows={2}
                  />
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="city_district">시/구</Label>
                <Input
                  id="city_district"
                  value={formData.city_district}
                  onChange={(e) => handleInputChange('city_district', e.target.value)}
                  placeholder="예: 서울특별시 강남구"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="processing_address">공장 주소</Label>
                <Textarea
                  id="processing_address"
                  value={formData.processing_address}
                  onChange={(e) => handleInputChange('processing_address', e.target.value)}
                  placeholder="공장 주소"
                  rows={2}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="main_phone">대표번호</Label>
                <div className="flex items-center space-x-2">
                  <Phone className="h-4 w-4 text-muted-foreground" />
                  <Input
                    id="main_phone"
                    value={formData.main_phone}
                    onChange={(e) => handleInputChange('main_phone', e.target.value)}
                    placeholder="대표번호"
                  />
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="industry_name">업종명</Label>
                <Input
                  id="industry_name"
                  value={formData.industry_name}
                  onChange={(e) => handleInputChange('industry_name', e.target.value)}
                  placeholder="업종명"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="products">주요제품</Label>
                <Textarea
                  id="products"
                  value={formData.products}
                  onChange={(e) => handleInputChange('products', e.target.value)}
                  placeholder="주요제품"
                  rows={3}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="website">웹사이트</Label>
                <Input
                  id="website"
                  type="url"
                  value={formData.website}
                  onChange={(e) => handleInputChange('website', e.target.value)}
                  placeholder="https://example.com"
                />
              </div>
            </CardContent>
          </Card>

          {/* SAP 정보 */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <DollarSign className="h-5 w-5" />
                <span>SAP 정보</span>
              </CardTitle>
              <CardDescription>SAP 관련 정보를 수정합니다.</CardDescription>
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
                  onChange={(e) => handleInputChange('company_code_sap', e.target.value)}
                  placeholder="SAP거래처코드"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="biz_code">사업</Label>
                  <Input
                    id="biz_code"
                    value={formData.biz_code}
                    onChange={(e) => handleInputChange('biz_code', e.target.value)}
                    placeholder="사업 코드"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="biz_name">사업부</Label>
                  <Input
                    id="biz_name"
                    value={formData.biz_name}
                    onChange={(e) => handleInputChange('biz_name', e.target.value)}
                    placeholder="사업부"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="department_code">지점/팀</Label>
                  <Input
                    id="department_code"
                    value={formData.department_code}
                    onChange={(e) => handleInputChange('department_code', e.target.value)}
                    placeholder="지점/팀 코드"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="department">팀명</Label>
                  <Input
                    id="department"
                    value={formData.department}
                    onChange={(e) => handleInputChange('department', e.target.value)}
                    placeholder="팀명"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="employee_number">사원번호</Label>
                  <Input
                    id="employee_number"
                    value={formData.employee_number}
                    onChange={(e) => handleInputChange('employee_number', e.target.value)}
                    placeholder="사원번호"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="employee_name">영업 사원</Label>
                  <Input
                    id="employee_name"
                    value={formData.employee_name}
                    onChange={(e) => handleInputChange('employee_name', e.target.value)}
                    placeholder="영업 사원명"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="distribution_type_sap_code">유통형태코드</Label>
                  <Input
                    id="distribution_type_sap_code"
                    value={formData.distribution_type_sap_code}
                    onChange={(e) => handleInputChange('distribution_type_sap_code', e.target.value)}
                    placeholder="유통형태코드"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="distribution_type_sap">유통형태</Label>
                  <Input
                    id="distribution_type_sap"
                    value={formData.distribution_type_sap}
                    onChange={(e) => handleInputChange('distribution_type_sap', e.target.value)}
                    placeholder="유통형태"
                  />
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="contact_person">거래처 담당자</Label>
                <Input
                  id="contact_person"
                  value={formData.contact_person}
                  onChange={(e) => handleInputChange('contact_person', e.target.value)}
                  placeholder="거래처 담당자명"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="contact_phone">담당자 연락처</Label>
                <div className="flex items-center space-x-2">
                  <Phone className="h-4 w-4 text-muted-foreground" />
                  <Input
                    id="contact_phone"
                    value={formData.contact_phone}
                    onChange={(e) => handleInputChange('contact_phone', e.target.value)}
                    placeholder="담당자 연락처"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="code_create_date">코드생성일</Label>
                  <div className="flex items-center space-x-2">
                    <Calendar className="h-4 w-4 text-muted-foreground" />
                    <Input
                      id="code_create_date"
                      type="date"
                      value={formData.code_create_date}
                      onChange={(e) => handleInputChange('code_create_date', e.target.value)}
                    />
                  </div>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="transaction_start_date">거래시작일</Label>
                  <div className="flex items-center space-x-2">
                    <Calendar className="h-4 w-4 text-muted-foreground" />
                    <Input
                      id="transaction_start_date"
                      type="date"
                      value={formData.transaction_start_date}
                      onChange={(e) => handleInputChange('transaction_start_date', e.target.value)}
                    />
                  </div>
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="payment_terms">결제조건</Label>
                <Input
                  id="payment_terms"
                  value={formData.payment_terms}
                  onChange={(e) => handleInputChange('payment_terms', e.target.value)}
                  placeholder="결제조건"
                />
              </div>
            </CardContent>
          </Card>
        </div>

        {/* 참고사항 */}
        <Card>
          <CardHeader>
            <CardTitle>참고사항</CardTitle>
            <CardDescription>추가적인 메모나 참고사항을 입력하세요.</CardDescription>
          </CardHeader>
          <CardContent>
            <Textarea
              value={formData.remarks}
              onChange={(e) => handleInputChange('remarks', e.target.value)}
              placeholder="참고사항을 입력하세요..."
              rows={4}
            />
          </CardContent>
        </Card>

        {/* 저장 버튼 */}
        <div className="flex justify-end space-x-4">
          <Button variant="outline" asChild>
            <Link href={`/companies/${params.id}`}>취소</Link>
          </Button>
          <Button type="submit" disabled={saving}>
            {saving ? (
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
    </div>
  )
}
