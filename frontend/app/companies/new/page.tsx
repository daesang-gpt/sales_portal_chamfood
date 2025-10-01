"use client"

import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { ArrowLeft, Save, Loader2 } from "lucide-react"
import Link from "next/link"
import { companyApi, Company } from "@/lib/api"
import { useToast } from "@/hooks/use-toast"

// User 타입 정의 (간단히 id, name만 사용)
type User = { id: number; name: string };

export default function NewCompanyPage() {
  const router = useRouter()
  const { toast } = useToast()
  const [loading, setLoading] = useState(false)
  const [users, setUsers] = useState<User[]>([]);
  const [formData, setFormData] = useState({
    company_name: "",
    sales_diary_company_code: "",
    company_code_sm: "",
    company_code_sap: "",
    company_type: "",
    established_date: "",
    ceo_name: "",
    address: "",
    contact_person: "",
    contact_phone: "",
    main_phone: "",
    distribution_type_sap: "",
    industry_name: "",
    main_product: "",
    transaction_start_date: "",
    payment_terms: "",
    customer_classification: "",
    website: "",
    remarks: "",
    username: null as number | null,
    location: "",  // 소재지 추가
    products: ""   // 사용품목 추가
  })

  // 영업 사원 목록 불러오기
  useEffect(() => {
    const fetchUsers = async () => {
      try {
        const res = await fetch("/api/users/");
        if (res.ok) {
          const data = await res.json();
          setUsers(data);
        }
      } catch {}
    };
    fetchUsers();
  }, []);

  const handleInputChange = (field: string, value: string | number | null) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }))
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
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
      const cleanData = { ...formData };
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
                <Label htmlFor="sales_diary_company_code">영업일지 회사코드</Label>
                <Input
                  id="sales_diary_company_code"
                  value={formData.sales_diary_company_code}
                  onChange={(e) => handleInputChange("sales_diary_company_code", e.target.value)}
                  placeholder="영업일지 회사코드를 입력하세요"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="company_code_sm">SM 회사코드</Label>
                <Input
                  id="company_code_sm"
                  value={formData.company_code_sm}
                  onChange={(e) => handleInputChange("company_code_sm", e.target.value)}
                  placeholder="SM 회사코드를 입력하세요"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="company_code_sap">SAP 회사코드</Label>
                <Input
                  id="company_code_sap"
                  value={formData.company_code_sap}
                  onChange={(e) => handleInputChange("company_code_sap", e.target.value)}
                  placeholder="SAP 회사코드를 입력하세요"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="company_type">기업형태</Label>
                <Select value={formData.company_type} onValueChange={(value) => handleInputChange("company_type", value)}>
                  <SelectTrigger>
                    <SelectValue placeholder="기업형태를 선택하세요" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="법인 또는 기타사업자">법인 또는 기타사업자</SelectItem>
                    <SelectItem value="개인사업자">개인사업자</SelectItem>
                  </SelectContent>
                </Select>
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

          {/* 연락처 정보 */}
          <Card>
            <CardHeader>
              <CardTitle>연락처 정보</CardTitle>
              <CardDescription>회사의 연락처 정보를 입력해주세요.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
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
                <Label htmlFor="address">주소</Label>
                <Input
                  id="address"
                  value={formData.address}
                  onChange={(e) => handleInputChange("address", e.target.value)}
                  placeholder="회사 주소를 입력하세요"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="contact_person">담당자</Label>
                <Input
                  id="contact_person"
                  value={formData.contact_person}
                  onChange={(e) => handleInputChange("contact_person", e.target.value)}
                  placeholder="담당자명을 입력하세요"
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
                <Label htmlFor="main_phone">대표전화</Label>
                <Input
                  id="main_phone"
                  value={formData.main_phone}
                  onChange={(e) => handleInputChange("main_phone", e.target.value)}
                  placeholder="대표전화번호를 입력하세요"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="website">웹사이트</Label>
                <Input
                  id="website"
                  value={formData.website}
                  onChange={(e) => handleInputChange("website", e.target.value)}
                  placeholder="웹사이트 주소를 입력하세요"
                />
              </div>
            </CardContent>
          </Card>

          {/* 비즈니스 정보 */}
          <Card>
            <CardHeader>
              <CardTitle>비즈니스 정보</CardTitle>
              <CardDescription>회사의 비즈니스 관련 정보를 입력해주세요.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="distribution_type_sap">SAP 유통유형</Label>
                <Input
                  id="distribution_type_sap"
                  value={formData.distribution_type_sap}
                  onChange={(e) => handleInputChange("distribution_type_sap", e.target.value)}
                  placeholder="SAP 유통유형을 입력하세요"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="industry_name">업종</Label>
                <Input
                  id="industry_name"
                  value={formData.industry_name}
                  onChange={(e) => handleInputChange("industry_name", e.target.value)}
                  placeholder="업종을 입력하세요"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="main_product">주요 제품</Label>
                <Input
                  id="main_product"
                  value={formData.main_product}
                  onChange={(e) => handleInputChange("main_product", e.target.value)}
                  placeholder="주요 제품을 입력하세요"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="transaction_start_date">거래개시일</Label>
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

              <div className="space-y-2">
                <Label htmlFor="customer_classification">고객구분</Label>
                <Select value={formData.customer_classification} onValueChange={(value) => handleInputChange("customer_classification", value)}>
                  <SelectTrigger>
                    <SelectValue placeholder="고객구분을 선택하세요" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="신규">신규</SelectItem>
                    <SelectItem value="기존">기존</SelectItem>
                    <SelectItem value="잠재">잠재</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label>소재지</Label>
                <Select value={formData.location} onValueChange={(value) => handleInputChange("location", value)}>
                  <SelectTrigger>
                    <SelectValue placeholder="소재지를 선택하세요" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="">(선택 안함)</SelectItem>
                    <SelectItem value="수도권">수도권</SelectItem>
                    <SelectItem value="충청권">충청권</SelectItem>
                    <SelectItem value="강원권">강원권</SelectItem>
                    <SelectItem value="영남권">영남권</SelectItem>
                    <SelectItem value="호남권">호남권</SelectItem>
                    <SelectItem value="기타">기타</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label htmlFor="products">사용품목</Label>
                <Input
                  id="products"
                  value={formData.products}
                  onChange={(e) => handleInputChange("products", e.target.value)}
                  placeholder="예: 국내산 닭, 수입산 돼지고기"
                />
              </div>
            </CardContent>
          </Card>

          {/* 기타 정보 */}
          <Card>
            <CardHeader>
              <CardTitle>기타 정보</CardTitle>
              <CardDescription>추가적인 정보나 메모를 입력해주세요.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="remarks">비고</Label>
                <Textarea
                  id="remarks"
                  value={formData.remarks}
                  onChange={(e) => handleInputChange("remarks", e.target.value)}
                  placeholder="추가적인 정보나 메모를 입력하세요"
                  rows={8}
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