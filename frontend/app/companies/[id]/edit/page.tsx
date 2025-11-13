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
import { ArrowLeft, Save, Loader2, Building2, Phone, MapPin, Calendar, DollarSign, Plus, Trash2 } from "lucide-react"
import Link from "next/link"
import { useParams, useRouter } from "next/navigation"
import { companyApi, Company, companyFinancialStatusApi, CompanyFinancialStatus } from "@/lib/api"
import { toast } from "@/hooks/use-toast"
import { LocationSelect } from "@/components/ui/location-select"
import { SapCodeSelect } from "@/components/ui/sap-code-select"
import { bizCodes, departmentCodes, employeeCodes, distributionTypeCodes, paymentTerms } from "@/lib/constants/sapCodes"
import { getUserFromToken } from "@/lib/auth"

export default function CompanyEditPage() {
  const params = useParams()
  const router = useRouter()
  const [company, setCompany] = useState<Company | null>(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [isViewer, setIsViewer] = useState(false)
  const [isCheckingRole, setIsCheckingRole] = useState(true)
  
  // SAP코드여부 체크박스 상태
  const [sapHasPurchase, setSapHasPurchase] = useState(false)
  const [sapHasSales, setSapHasSales] = useState(false)
  
  // 재무 정보 상태
  const [financialStatuses, setFinancialStatuses] = useState<Array<{
    fiscal_year: string
    total_assets: string
    capital: string
    total_equity: string
    revenue: string
    operating_income: string
    net_income: string
  }>>([])

  // 폼 상태
  const [formData, setFormData] = useState({
    // 필수 필드
    company_code: '',
    company_name: '',
    // 기본정보
    customer_classification: '' as '잠재' | '신규' | '기존' | '이탈' | '벤더' | '',
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
    const currentUser = getUserFromToken();
    if (!currentUser) {
      router.push('/login');
      return;
    }
    if (currentUser.role === 'viewer') {
      setError('뷰어 권한은 회사를 수정할 수 없습니다.');
      setIsViewer(true);
      setIsCheckingRole(false);
      router.replace(`/companies/${params.id}`);
      return;
    }
    setIsCheckingRole(false);
  }, [router, params.id])

  useEffect(() => {
    if (isCheckingRole || isViewer) {
      return
    }
    const loadCompany = async () => {
      try {
        setLoading(true)
        setError(null)
        const companyData = await companyApi.getCompany(params.id as string)
        setCompany(companyData)
        
        // 재무 정보 로드
        try {
          console.log('재무 정보 로드 시작, company_code:', params.id)
          const financialData = await companyFinancialStatusApi.getByCompanyCode(params.id as string)
          console.log('재무 정보 API 응답:', financialData)
          
          // 페이지네이션 형식일 수도 있으므로 확인
          const list = Array.isArray(financialData) ? financialData : (Array.isArray((financialData as Record<string, unknown>)?.results) ? (financialData as Record<string, unknown>).results as CompanyFinancialStatus[] : [])
          console.log('재무 정보 리스트:', list)
          
          if (list && list.length > 0) {
            const mappedData = list.map((item) => {
              const fiscalYear = item.fiscal_year ? item.fiscal_year.split('T')[0].substring(0, 4) : ''
              console.log('재무 정보 항목:', item, '파싱된 연도:', fiscalYear)
              return {
                fiscal_year: fiscalYear,
                total_assets: item.total_assets?.toString() || '',
                capital: item.capital?.toString() || '',
                total_equity: item.total_equity?.toString() || '',
                revenue: item.revenue?.toString() || '',
                operating_income: item.operating_income?.toString() || '',
                net_income: item.net_income?.toString() || '',
              }
            })
            console.log('매핑된 재무 정보:', mappedData)
            setFinancialStatuses(mappedData)
          } else {
            console.log('재무 정보가 없습니다.')
            setFinancialStatuses([])
          }
        } catch (err) {
          console.error('재무 정보 로드 오류:', err)
          // 재무 정보가 없어도 계속 진행
          setFinancialStatuses([])
        }
        
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
  }, [params.id, isCheckingRole, isViewer])

  const handleInputChange = (field: string, value: string) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }))
  }

  // 재무 정보 핸들러
  const handleFinancialChange = (index: number, field: string, value: string) => {
    setFinancialStatuses(prev => {
      const updated = [...prev]
      updated[index] = { ...updated[index], [field]: value }
      return updated
    })
  }

  const addFinancialStatus = () => {
    setFinancialStatuses(prev => [...prev, {
      fiscal_year: '',
      total_assets: '',
      capital: '',
      total_equity: '',
      revenue: '',
      operating_income: '',
      net_income: '',
    }])
  }

  const removeFinancialStatus = (index: number) => {
    setFinancialStatuses(prev => prev.filter((_, i) => i !== index))
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
        // sap_code_type이 빈 문자열일 때는 명시적으로 null로 설정하여 기존 값 제거
        if (key === 'sap_code_type' && value === '') {
          cleanData[key] = null
        } else if (value !== '' && value !== null) {
          cleanData[key] = value
        }
      })

      // 재무 정보 추가 (삭제를 위해 항상 전송, 빈 배열도 포함)
      const validFinancialStatuses = financialStatuses.filter(fs => 
        fs.fiscal_year && (
          fs.total_assets || fs.capital || fs.total_equity || 
          fs.revenue || fs.operating_income || fs.net_income
        )
      )
      
      // 재무 정보를 항상 전송 (빈 배열도 포함하여 삭제 처리)
      cleanData.financial_statuses = validFinancialStatuses

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
        <div className="text-center text-red-500 py-12">뷰어 권한은 회사를 수정할 수 없습니다.</div>
      </div>
    )
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
                <Label htmlFor="company_code" className="text-sm font-semibold text-foreground">회사코드 *</Label>
                <Input
                  id="company_code"
                  value={formData.company_code}
                  onChange={(e) => handleInputChange('company_code', e.target.value)}
                  placeholder="회사코드"
                  required
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="company_name" className="text-sm font-semibold text-foreground">회사명 *</Label>
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
                  <Label htmlFor="customer_classification" className="text-sm font-semibold text-foreground">고객분류</Label>
                  <Select value={formData.customer_classification || undefined} onValueChange={(value) => handleInputChange('customer_classification', value)}>
                    <SelectTrigger>
                      <SelectValue placeholder="고객분류 선택" />
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
                <Label htmlFor="tax_id" className="text-sm font-semibold text-foreground">사업자등록번호</Label>
                <Input
                  id="tax_id"
                  value={formData.tax_id}
                  onChange={(e) => handleInputChange('tax_id', e.target.value)}
                  placeholder="사업자등록번호"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="established_date" className="text-sm font-semibold text-foreground">설립일</Label>
                <Input
                  id="established_date"
                  type="date"
                  value={formData.established_date}
                  onChange={(e) => handleInputChange('established_date', e.target.value)}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="ceo_name" className="text-sm font-semibold text-foreground">대표자명</Label>
                <Input
                  id="ceo_name"
                  value={formData.ceo_name}
                  onChange={(e) => handleInputChange('ceo_name', e.target.value)}
                  placeholder="대표자명"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="head_address" className="text-sm font-semibold text-foreground">본사 주소</Label>
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
                <Label htmlFor="city_district" className="text-sm font-semibold text-foreground">시/구</Label>
                <LocationSelect
                  value={formData.city_district}
                  onChange={(value) => handleInputChange('city_district', value)}
                  placeholder="지역을 선택하세요"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="processing_address" className="text-sm font-semibold text-foreground">공장 주소</Label>
                <Textarea
                  id="processing_address"
                  value={formData.processing_address}
                  onChange={(e) => handleInputChange('processing_address', e.target.value)}
                  placeholder="공장 주소"
                  rows={2}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="main_phone" className="text-sm font-semibold text-foreground">대표번호</Label>
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
                <Label htmlFor="industry_name" className="text-sm font-semibold text-foreground">업종명</Label>
                <Input
                  id="industry_name"
                  value={formData.industry_name}
                  onChange={(e) => handleInputChange('industry_name', e.target.value)}
                  placeholder="업종명"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="products" className="text-sm font-semibold text-foreground">주요제품</Label>
                <Textarea
                  id="products"
                  value={formData.products}
                  onChange={(e) => handleInputChange('products', e.target.value)}
                  placeholder="주요제품"
                  rows={3}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="website" className="text-sm font-semibold text-foreground">웹사이트</Label>
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
                  onChange={(e) => handleInputChange('company_code_sap', e.target.value)}
                  placeholder="SAP거래처코드"
                />
              </div>

              <SapCodeSelect
                options={bizCodes}
                codeValue={formData.biz_code}
                nameValue={formData.biz_name}
                onCodeChange={(code) => handleInputChange('biz_code', code)}
                onNameChange={(name) => handleInputChange('biz_name', name)}
                codeLabel="사업"
                nameLabel="사업부"
                namePlaceholder="사업부를 선택하세요"
              />

              <SapCodeSelect
                options={departmentCodes}
                codeValue={formData.department_code}
                nameValue={formData.department}
                onCodeChange={(code) => handleInputChange('department_code', code)}
                onNameChange={(name) => handleInputChange('department', name)}
                codeLabel="지점/팀"
                nameLabel="팀명"
                namePlaceholder="팀명을 선택하세요"
              />

              <SapCodeSelect
                options={employeeCodes}
                codeValue={formData.employee_number}
                nameValue={formData.employee_name}
                onCodeChange={(code) => handleInputChange('employee_number', code)}
                onNameChange={(name) => handleInputChange('employee_name', name)}
                codeLabel="사원번호"
                nameLabel="영업 사원"
                namePlaceholder="영업 사원을 선택하세요"
              />

              <SapCodeSelect
                options={distributionTypeCodes}
                codeValue={formData.distribution_type_sap_code}
                nameValue={formData.distribution_type_sap}
                onCodeChange={(code) => handleInputChange('distribution_type_sap_code', code)}
                onNameChange={(name) => handleInputChange('distribution_type_sap', name)}
                codeLabel="유통형태코드"
                nameLabel="유통형태"
                namePlaceholder="유통형태를 선택하세요"
              />

              <div className="space-y-2">
                <Label htmlFor="contact_person" className="text-sm font-semibold text-foreground">거래처 담당자</Label>
                <Input
                  id="contact_person"
                  value={formData.contact_person}
                  onChange={(e) => handleInputChange('contact_person', e.target.value)}
                  placeholder="거래처 담당자명"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="contact_phone" className="text-sm font-semibold text-foreground">담당자 연락처</Label>
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
                  <Label htmlFor="code_create_date" className="text-sm font-semibold text-foreground">코드생성일</Label>
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
                  <Label htmlFor="transaction_start_date" className="text-sm font-semibold text-foreground">거래시작일</Label>
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
                <Label htmlFor="payment_terms" className="text-sm font-semibold text-foreground">결제조건</Label>
                <Select 
                  value={formData.payment_terms || undefined} 
                  onValueChange={(value) => handleInputChange('payment_terms', value)}
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

        {/* 재무 정보 */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="flex items-center space-x-2">
                  <DollarSign className="h-5 w-5" />
                  <span>재무 정보</span>
                </CardTitle>
                <CardDescription>회사의 재무 정보를 입력하세요. 연도별로 여러 개를 추가할 수 있습니다.</CardDescription>
              </div>
              <Button type="button" variant="outline" size="sm" onClick={addFinancialStatus}>
                <Plus className="mr-2 h-4 w-4" />
                추가
              </Button>
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            {financialStatuses.length === 0 ? (
              <div className="text-center py-8 text-muted-foreground">
                <p>재무 정보가 없습니다. "추가" 버튼을 클릭하여 추가하세요.</p>
              </div>
            ) : (
              financialStatuses.map((financial, index) => (
                <div key={index} className="border rounded-lg p-4 space-y-4">
                  <div className="flex items-center justify-between mb-4">
                    <h4 className="font-semibold">재무 정보 #{index + 1}</h4>
                    <Button
                      type="button"
                      variant="ghost"
                      size="sm"
                      onClick={() => removeFinancialStatus(index)}
                    >
                      <Trash2 className="h-4 w-4 text-destructive" />
                    </Button>
                  </div>
                  <div className="grid grid-cols-7 gap-3">
                    <div className="space-y-2">
                      <Label className="text-xs">결산년도 *</Label>
                      <Input
                        type="text"
                        placeholder="예: 2024"
                        value={financial.fiscal_year}
                        onChange={(e) => handleFinancialChange(index, 'fiscal_year', e.target.value)}
                        maxLength={4}
                        className="h-9"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label className="text-xs">총자산</Label>
                      <Input
                        type="number"
                        placeholder="총자산"
                        value={financial.total_assets}
                        onChange={(e) => handleFinancialChange(index, 'total_assets', e.target.value)}
                        className="h-9"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label className="text-xs">자본금</Label>
                      <Input
                        type="number"
                        placeholder="자본금"
                        value={financial.capital}
                        onChange={(e) => handleFinancialChange(index, 'capital', e.target.value)}
                        className="h-9"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label className="text-xs">자본총계</Label>
                      <Input
                        type="number"
                        placeholder="자본총계"
                        value={financial.total_equity}
                        onChange={(e) => handleFinancialChange(index, 'total_equity', e.target.value)}
                        className="h-9"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label className="text-xs">매출액</Label>
                      <Input
                        type="number"
                        placeholder="매출액"
                        value={financial.revenue}
                        onChange={(e) => handleFinancialChange(index, 'revenue', e.target.value)}
                        className="h-9"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label className="text-xs">영업이익</Label>
                      <Input
                        type="number"
                        placeholder="영업이익"
                        value={financial.operating_income}
                        onChange={(e) => handleFinancialChange(index, 'operating_income', e.target.value)}
                        className="h-9"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label className="text-xs">당기순이익</Label>
                      <Input
                        type="number"
                        placeholder="당기순이익"
                        value={financial.net_income}
                        onChange={(e) => handleFinancialChange(index, 'net_income', e.target.value)}
                        className="h-9"
                      />
                    </div>
                  </div>
                </div>
              ))
            )}
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
