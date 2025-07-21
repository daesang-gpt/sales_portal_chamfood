"use client"

import { useEffect, useState } from "react"
import { useRouter } from "next/navigation"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import {
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  LineChart,
  Line,
  PieChart,
  Pie,
  Cell,
} from "recharts"
import { FileText, Building2, Phone, DollarSign, User, LogOut } from "lucide-react"
import Link from "next/link"
import { isAuthenticated, logout, getUserFromToken } from "@/lib/auth"

const salesData = [
  { name: "1월", 매출액: 45000000, 매출수량: 12500, 매출건수: 85 },
  { name: "2월", 매출액: 52000000, 매출수량: 14200, 매출건수: 92 },
  { name: "3월", 매출액: 48000000, 매출수량: 13100, 매출건수: 88 },
  { name: "4월", 매출액: 61000000, 매출수량: 16800, 매출건수: 105 },
  { name: "5월", 매출액: 58000000, 매출수량: 15900, 매출건수: 98 },
  { name: "6월", 매출액: 67000000, 매출수량: 18200, 매출건수: 112 },
]

const channelData = [
  { name: "가공장", value: 45, color: "#0088FE" },
  { name: "프랜차이즈", value: 30, color: "#00C49F" },
  { name: "도소매", value: 25, color: "#FFBB28" },
]

const recentActivities = [
  { company: "아이더스에프앤비", type: "대면", date: "2025-05-12", author: "엄재후" },
  { company: "(주)사세", type: "전화", date: "2025-05-11", author: "김영희" },
  { company: "푸라닭 본사", type: "대면", date: "2025-05-10", author: "엄재후" },
  { company: "움버거", type: "전화", date: "2025-05-09", author: "박민수" },
]

export default function Dashboard() {
  const [user, setUser] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(true);
  const router = useRouter();

  useEffect(() => {
    // 인증 확인
    if (!isAuthenticated()) {
      router.push('/login');
      return;
    }

    const currentUser = getUserFromToken();
    setUser(currentUser);
    setIsLoading(false);
  }, [router]);

  const handleLogout = () => {
    logout();
    router.push('/login');
  };

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-lg">로딩 중...</div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold">영업 대시보드</h1>
        <div className="flex items-center gap-4">
          {user && (
            <div className="flex items-center gap-2 text-sm text-gray-600">
              <User className="h-4 w-4" />
              <span>{user.name} ({user.department})</span>
              {user.role === 'admin' && (
                <Button variant="outline" size="sm" asChild>
                  <Link href="/admin">관리자</Link>
                </Button>
              )}
            </div>
          )}
          <div className="flex gap-2">
            <Button asChild>
              <Link href="/sales-reports/new">영업일지 작성</Link>
            </Button>
            <Button variant="outline" asChild>
              <Link href="/companies/new">회사 등록</Link>
            </Button>
            <Button variant="outline" asChild>
              <Link href="/mypage">마이페이지</Link>
            </Button>
            <Button variant="outline" onClick={handleLogout}>
              <LogOut className="h-4 w-4 mr-2" />
              로그아웃
            </Button>
          </div>
        </div>
      </div>

      {/* 주요 지표 카드 */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">이번 달 영업일지</CardTitle>
            <FileText className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">24건</div>
            <p className="text-xs text-muted-foreground">전월 대비 +12%</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">신규 고객사</CardTitle>
            <Building2 className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">8개사</div>
            <p className="text-xs text-muted-foreground">이번 달 신규 등록</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">총 연락 횟수</CardTitle>
            <Phone className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">156회</div>
            <p className="text-xs text-muted-foreground">대면 89회, 전화 67회</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">이번 달 매출</CardTitle>
            <DollarSign className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">6.7억원</div>
            <p className="text-xs text-muted-foreground">전월 대비 +15.5%</p>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        {/* 월별 매출 추이 */}
        <Card>
          <CardHeader>
            <CardTitle>월별 매출 추이</CardTitle>
            <CardDescription>최근 6개월 매출 현황</CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={salesData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis tickFormatter={(value) => `${(value / 10000000).toFixed(0)}천만`} />
                <Tooltip formatter={(value: number) => [`${(value / 10000000).toFixed(1)}천만원`, "매출액"]} />
                <Line type="monotone" dataKey="매출액" stroke="#8884d8" strokeWidth={2} />
              </LineChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* 채널별 매출 비율 */}
        <Card>
          <CardHeader>
            <CardTitle>채널별 매출 비율</CardTitle>
            <CardDescription>유통형태별 매출 구성</CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={channelData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, percent }) => `${name} ${((percent || 0) * 100).toFixed(0)}%`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {channelData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      {/* 최근 영업 활동 */}
      <Card>
        <CardHeader>
          <CardTitle>최근 영업 활동</CardTitle>
          <CardDescription>최근 영업일지 작성 현황</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {recentActivities.map((activity, index) => (
              <div key={index} className="flex items-center justify-between p-4 border rounded-lg">
                <div className="flex items-center space-x-4">
                  <div
                    className={`w-3 h-3 rounded-full ${activity.type === "대면" ? "bg-green-500" : "bg-blue-500"}`}
                  />
                  <div>
                    <p className="font-medium">{activity.company}</p>
                    <p className="text-sm text-muted-foreground">
                      {activity.type} 영업 - {activity.author}
                    </p>
                  </div>
                </div>
                <div className="text-sm text-muted-foreground">{activity.date}</div>
              </div>
            ))}
          </div>
          <div className="mt-4">
            <Button variant="outline" asChild className="w-full bg-transparent">
              <Link href="/sales-reports">전체 영업일지 보기</Link>
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
