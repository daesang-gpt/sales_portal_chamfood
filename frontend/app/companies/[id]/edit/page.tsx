"use client"

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Badge } from "@/components/ui/badge"
import { Separator } from "@/components/ui/separator"
import { ArrowLeft, Save, Loader2, Building2, Phone, MapPin, Calendar, DollarSign } from "lucide-react"
import Link from "next/link"
import { useParams, useRouter } from "next/navigation"
import { companyApi, Company } from "@/lib/api"
import { toast } from "@/hooks/use-toast"
// User 타입 정의 (간단히 id, name만 사용)
type User = { id: number; name: string };

export default function CompanyEditPage() {
  const params = useParams()
  const router = useRouter()
  const [company, setCompany] = useState<Company | null>(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [users, setUsers] = useState<User[]>([]);

  // 폼 상태
  const [formData, setFormData] = useState({
    company_name: '',
    sales_diary_company_code: '',
    company_code_sm: '',
    company_code_sap: '',
    company_type: '',
    established_date: '',
    ceo_name: '',
    address: '',
    contact_person: '',
    contact_phone: '',
    main_phone: '',
    distribution_type_sap: '',
    industry_name: '',
    main_product: '',
    transaction_start_date: '',
    payment_terms: '',
    customer_classification: '',
    website: '',
    remarks: '',
    username: null as number | null
  })

  useEffect(() => {
    const loadCompany = async () => {
      try {
        setLoading(true)
        setError(null)
        const companyData = await companyApi.getCompany(Number(params.id))
        setCompany(companyData)
        
        // 폼 데이터 초기화
        setFormData({
          company_name: companyData.company_name || '',
          sales_diary_company_code: companyData.sales_diary_company_code || '',
          company_code_sm: companyData.company_code_sm || '',
          company_code_sap: companyData.company_code_sap || '',
          company_type: companyData.company_type || '',
          established_date: companyData.established_date ? companyData.established_date.split('T')[0] : '',
          ceo_name: companyData.ceo_name || '',
          address: companyData.address || '',
          contact_person: companyData.contact_person || '',
          contact_phone: companyData.contact_phone || '',
          main_phone: companyData.main_phone || '',
          distribution_type_sap: companyData.distribution_type_sap || '',
          industry_name: companyData.industry_name || '',
          main_product: companyData.main_product || '',
          transaction_start_date: companyData.transaction_start_date ? companyData.transaction_start_date.split('T')[0] : '',
          payment_terms: companyData.payment_terms || '',
          customer_classification: companyData.customer_classification || '',
          website: companyData.website || '',
          remarks: companyData.remarks || '',
          username: companyData.username ?? null
        })
      } catch (err) {
        setError('회사 정보를 불러오는 중 오류가 발생했습니다.')
        console.error('Error loading company:', err)
      } finally {
        setLoading(false)
      }
    }
    // 영업 사원 목록 불러오기
    const fetchUsers = async () => {
      try {
        const res = await fetch("/api/users/");
        if (res.ok) {
          const data = await res.json();
          setUsers(data);
        }
      } catch {}
    };

    if (params.id) {
      loadCompany()
      fetchUsers()
    }
  }, [params.id])

  const handleInputChange = (field: string, value: string | null | number) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }))
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    try {
      setSaving(true)
      
      // 필수 필드 검증
      if (!formData.company_name.trim()) {
        toast({
          title: "오류",
          description: "회사명은 필수 입력 항목입니다.",
          variant: "destructive",
        })
        return
      }

      // API 호출
      const updatedCompany = await companyApi.updateCompany(Number(params.id), {
        ...formData,
        username: formData.username ?? null
      })
      
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
                  <Label htmlFor="sales_diary_company_code">영업일지 회사코드</Label>
                  <Input
                    id="sales_diary_company_code"
                    value={formData.sales_diary_company_code}
                    onChange={(e) => handleInputChange('sales_diary_company_code', e.target.value)}
                    placeholder="영업일지 회사코드"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="company_code_sap">SAP 회사코드</Label>
                  <Input
                    id="company_code_sap"
                    value={formData.company_code_sap}
                    onChange={(e) => handleInputChange('company_code_sap', e.target.value)}
                    placeholder="SAP 회사코드"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="company_type">기업형태</Label>
                  <Input
                    id="company_type"
                    value={formData.company_type}
                    onChange={(e) => handleInputChange('company_type', e.target.value)}
                    placeholder="기업형태"
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
                <Label htmlFor="address">주소</Label>
                <div className="flex items-start space-x-2">
                  <MapPin className="h-4 w-4 mt-3 text-muted-foreground" />
                  <Textarea
                    id="address"
                    value={formData.address}
                    onChange={(e) => handleInputChange('address', e.target.value)}
                    placeholder="회사 주소"
                    rows={2}
                  />
                </div>
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
                <Label htmlFor="username">영업 사원</Label>
                <Select
                  value={formData.username !== null ? String(formData.username) : ''}
                  onValueChange={value => handleInputChange('username', value ? Number(value) : null)}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="영업 사원 선택" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="">(없음)</SelectItem>
                    {users.map(user => (
                      <SelectItem key={user.id} value={String(user.id)}>{user.name}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
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
              <CardDescription>거래 관련 정보를 수정합니다.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="contact_person">담당자</Label>
                <Input
                  id="contact_person"
                  value={formData.contact_person}
                  onChange={(e) => handleInputChange('contact_person', e.target.value)}
                  placeholder="담당자명"
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

              <div className="space-y-2">
                <Label htmlFor="distribution_type_sap">유통형태</Label>
                <Input
                  id="distribution_type_sap"
                  value={formData.distribution_type_sap}
                  onChange={(e) => handleInputChange('distribution_type_sap', e.target.value)}
                  placeholder="유통형태"
                />
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
                <Label htmlFor="main_product">주생산품</Label>
                <Input
                  id="main_product"
                  value={formData.main_product}
                  onChange={(e) => handleInputChange('main_product', e.target.value)}
                  placeholder="주생산품"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="transaction_start_date">거래개시일</Label>
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

              <div className="space-y-2">
                <Label htmlFor="payment_terms">지급조건</Label>
                <Input
                  id="payment_terms"
                  value={formData.payment_terms}
                  onChange={(e) => handleInputChange('payment_terms', e.target.value)}
                  placeholder="지급조건"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="customer_classification">고객분류</Label>
                <Select
                  value={formData.customer_classification}
                  onValueChange={(value) => handleInputChange('customer_classification', value)}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="고객분류 선택" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="신규">신규</SelectItem>
                    <SelectItem value="기존">기존</SelectItem>
                    <SelectItem value="잠재">잠재</SelectItem>
                  </SelectContent>
                </Select>
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