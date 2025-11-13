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
import { dashboardApi } from "@/lib/api"

// 더미 데이터를 제거하고 실제 API 데이터를 사용하도록 변경

export default function Dashboard() {
  const [user, setUser] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [dashboardStats, setDashboardStats] = useState<any>(null);
  const [chartData, setChartData] = useState<any>(null);
  const [dataLoading, setDataLoading] = useState(true);
  const router = useRouter();
  const isViewer = user?.role === 'viewer';

  useEffect(() => {
    // 인증 확인
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
      // 병렬로 통계와 차트 데이터 가져오기
      const [statsResponse, chartsResponse] = await Promise.all([
        dashboardApi.getDashboardStats(),
        dashboardApi.getDashboardCharts()
      ]);
      
      setDashboardStats(statsResponse);
      setChartData(chartsResponse);
    } catch (error) {
      console.error('대시보드 데이터 로드 실패:', error);
    } finally {
      setDataLoading(false);
      setIsLoading(false);
    }
  };

  // 월별 매출 툴팁 (매출액, 매출이익, GP%) 표시
  const SalesTooltip = ({ active, payload, label }: any) => {
    if (!active || !payload || payload.length === 0) return null;
    const findVal = (key: string) => {
      const item = payload.find((p: any) => p.name === key || p.dataKey === key);
      return Number(item?.value || 0);
    };
    const toTenMillion = (v: number) => `${(v / 10000000).toFixed(1)}천만원`;
    const revenue = findVal('매출액');
    const profit = findVal('매출이익');
    const gp = revenue ? ((profit / revenue) * 100).toFixed(1) : '0.0';
    return (
      <div className="bg-white/95 border rounded-md p-3 shadow">
        <div className="text-sm font-medium mb-1">{label}</div>
        <div className="text-xs text-gray-700">매출액: {toTenMillion(revenue)}</div>
        <div className="text-xs text-gray-700">매출이익: {toTenMillion(profit)}</div>
        <div className="text-xs text-gray-700">GP%: {gp}%</div>
      </div>
    );
  };

  // 채널별 툴팁 (매출, 매출이익, GP%) 표시
  const ChannelTooltip = ({ active, payload }: any) => {
    if (!active || !payload || payload.length === 0) return null;
    const p = payload[0]?.payload || {};
    const revenue = Number(p.revenue || 0);
    const profit = Number(p.profit || 0);
    const gp = revenue ? ((profit / revenue) * 100).toFixed(1) : '0.0';
    const toTenMillion = (v: number) => `${(v / 10000000).toFixed(1)}천만원`;
    return (
      <div className="bg-white/95 border rounded-md p-3 shadow">
        <div className="text-sm font-medium mb-1">{p.name}</div>
        <div className="text-xs text-gray-700">매출: {toTenMillion(revenue)}</div>
        <div className="text-xs text-gray-700">매출이익: {toTenMillion(profit)}</div>
        <div className="text-xs text-gray-700">GP%: {gp}%</div>
      </div>
    );
  };

  const handleLogout = () => {
    logout();
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
        <Card>
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

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">신규 고객사</CardTitle>
            <Building2 className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{dashboardStats?.thisMonthNewCompanies || 0}개사</div>
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
                `${(dashboardStats.thisMonthRevenue / 100000000).toFixed(1)}억원` : 
                '0억원'
              }
            </div>
            <p className="text-xs text-muted-foreground">
              전월 대비 +{dashboardStats?.revenueGrowthRate || 0}%</p>
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
              <LineChart data={chartData?.salesData || []}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis tickFormatter={(value) => `${(value / 10000000).toFixed(0)}천만`} />
                <Tooltip content={<SalesTooltip />} />
                <Line type="monotone" dataKey="매출액" stroke="#8884d8" strokeWidth={2} />
                <Line type="monotone" dataKey="매출이익" stroke="#82ca9d" strokeWidth={2} />
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
                  data={chartData?.channelData || []}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, percent }) => `${name} ${((percent || 0) * 100).toFixed(0)}%`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {(chartData?.channelData || []).map((entry: any, index: number) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip content={<ChannelTooltip />} />
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
