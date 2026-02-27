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
  ComposedChart,
  Bar,
} from "recharts"
import { FileText, Building2, Phone, DollarSign, User, LogOut } from "lucide-react"
import Link from "next/link"
import { isAuthenticated, logout, getUserFromToken } from "@/lib/auth"
import { dashboardApi } from "@/lib/api"

export default function Dashboard() {
  const [user, setUser] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [dashboardStats, setDashboardStats] = useState<any>(null);
  const [chartData, setChartData] = useState<any>(null);
  const [dataLoading, setDataLoading] = useState(true);
  const router = useRouter();
  const isViewer = user?.role === 'viewer';

  useEffect(() => {
    if (!isAuthenticated()) {
      router.push('/login');
      return;
    }
    const currentUser = getUserFromToken();
    setUser(currentUser);
    loadDashboardData();
  }, [router]);

  const loadDashboardData = async () => {
    try {
      setDataLoading(true);
      const [statsResult, chartsResult] = await Promise.allSettled([
        dashboardApi.getDashboardStats(),
        dashboardApi.getDashboardCharts()
      ]);
      if (statsResult.status === 'fulfilled') {
        setDashboardStats(statsResult.value);
      } else {
        console.error('대시보드 통계 로드 실패:', statsResult.reason);
      }
      if (chartsResult.status === 'fulfilled') {
        setChartData(chartsResult.value);
      } else {
        console.error('대시보드 차트 로드 실패:', chartsResult.reason);
      }
    } catch (error) {
      console.error('대시보드 데이터 로드 실패:', error);
    } finally {
      setDataLoading(false);
      setIsLoading(false);
    }
  };

  // 월별 매출 툴팁
  const SalesTooltip = ({ active, payload, label }: any) => {
    if (!active || !payload || payload.length === 0) return null;
    const findVal = (key: string) => {
      const item = payload.find((p: any) => p.name === key || p.dataKey === key);
      return Number(item?.value || 0);
    };
    const toUnit = (v: number) => {
      if (v >= 100000000) return `${(v / 100000000).toFixed(1)}억원`;
      if (v >= 10000000) return `${(v / 10000000).toFixed(1)}천만원`;
      if (v >= 10000) return `${(v / 10000).toFixed(0)}만원`;
      return `${v.toLocaleString()}원`;
    };
    const revenue = findVal('매출액');
    const count = findVal('매출건수');
    return (
      <div className="bg-white/95 border rounded-md p-3 shadow z-[100]" style={{ zIndex: 100 }}>
        <div className="text-sm font-medium mb-2">{label}</div>
        <div className="grid grid-cols-2 gap-2">
          <div className="text-xs text-gray-700">매출액:</div>
          <div className="text-xs font-semibold text-gray-900">{toUnit(revenue)}</div>
          <div className="text-xs text-gray-700">건수:</div>
          <div className="text-xs font-semibold text-gray-900">{count}건</div>
        </div>
      </div>
    );
  };

  const handleLogout = async () => {
    await logout();
    router.push('/login');
  };

  if (isLoading || dataLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-lg">대시보드 로딩 중...</div>
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
            {!isViewer && (
              <>
                <Button asChild>
                  <Link href="/sales-reports/new">영업일지 작성</Link>
                </Button>
                <Button variant="outline" asChild>
                  <Link href="/companies/new">회사 등록</Link>
                </Button>
              </>
            )}
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
        <Card
          className="cursor-pointer hover:bg-muted/50 transition-colors"
          onClick={() => router.push('/sales-reports?period=1m')}
        >
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">이번 달 영업일지</CardTitle>
            <FileText className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{dashboardStats?.thisMonthReports || 0}건</div>
            <p className="text-xs text-muted-foreground">
              {dashboardStats?.reportsGrowthRate ?
                `전월 대비 ${dashboardStats.reportsGrowthRate > 0 ? '+' : ''}${dashboardStats.reportsGrowthRate}%` :
                '전월 대비 데이터 없음'
              }
            </p>
          </CardContent>
        </Card>

        <Card
          className="cursor-pointer hover:bg-muted/50 transition-colors"
          onClick={() => router.push('/companies?customer_classification=신규')}
        >
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">신규 거래처</CardTitle>
            <Building2 className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{dashboardStats?.thisMonthNewCompanies || 0}개</div>
            <p className="text-xs text-muted-foreground">이번 달 신규 등록</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">총 연락 횟수</CardTitle>
            <Phone className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{dashboardStats?.totalContacts || 0}회</div>
            <p className="text-xs text-muted-foreground">
              대면 {dashboardStats?.faceToFaceContacts || 0}회, 전화 {dashboardStats?.phoneContacts || 0}회
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">이번 달 매출</CardTitle>
            <DollarSign className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {dashboardStats?.thisMonthRevenue ?
                dashboardStats.thisMonthRevenue >= 100000000
                  ? `${(dashboardStats.thisMonthRevenue / 100000000).toFixed(1)}억원`
                  : `${(dashboardStats.thisMonthRevenue / 10000000).toFixed(1)}천만원`
                : '0원'
              }
            </div>
            <p className="text-xs text-muted-foreground">
              전월 대비 +{dashboardStats?.revenueGrowthRate || 0}%
            </p>
          </CardContent>
        </Card>
      </div>

      {/* 월별 매출 추이 */}
      <Card>
        <CardHeader>
          <CardTitle>월별 매출 추이</CardTitle>
          <CardDescription>최근 6개월 전체 매출 현황</CardDescription>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={320}>
            <ComposedChart data={chartData?.salesData || []}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis
                tickFormatter={(value) => {
                  if (value >= 100000000) return `${(value / 100000000).toFixed(0)}억`;
                  if (value >= 10000000) return `${(value / 10000000).toFixed(0)}천만`;
                  return `${(value / 10000).toFixed(0)}만`;
                }}
              />
              <Tooltip content={<SalesTooltip />} />
              <Bar dataKey="매출액" fill="#4F9DDE" name="매출액" radius={[4, 4, 0, 0]} />
            </ComposedChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      {/* 최근 영업 활동 */}
      <Card>
        <CardHeader>
          <CardTitle>최근 영업 활동</CardTitle>
          <CardDescription>최근 영업일지 작성 현황</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {(chartData?.recentActivities || []).length > 0 ? (
              chartData.recentActivities.map((activity: any, index: number) => (
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
              ))
            ) : (
              <div className="text-center text-gray-500 py-8">
                최근 영업 활동이 없습니다.
              </div>
            )}
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
