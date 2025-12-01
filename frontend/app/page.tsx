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
  Legend,
  ComposedChart,
  Bar,
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

  // 월별 매출 툴팁 (매출액, 매출이익, GP%) 표시 - 2열 그리드
  const SalesTooltip = ({ active, payload, label }: any) => {
    if (!active || !payload || payload.length === 0) return null;
    const findVal = (key: string) => {
      const item = payload.find((p: any) => p.name === key || p.dataKey === key);
      return Number(item?.value || 0);
    };
    const toTenMillion = (v: number) => `${(v / 10000000).toFixed(1)}천만원`;
    const revenue = findVal('매출액');
    const profit = findVal('매출이익');
    const gp = findVal('GP') || (revenue ? ((profit / revenue) * 100).toFixed(1) : '0.0');
    return (
      <div className="bg-white/95 border rounded-md p-3 shadow z-[100]" style={{ zIndex: 100 }}>
        <div className="text-sm font-medium mb-2">{label}</div>
        <div className="grid grid-cols-2 gap-2">
          <div className="text-xs text-gray-700">매출액:</div>
          <div className="text-xs font-semibold text-gray-900">{toTenMillion(revenue)}</div>
          <div className="text-xs text-gray-700">매출이익:</div>
          <div className="text-xs font-semibold text-gray-900">{toTenMillion(profit)}</div>
          <div className="text-xs text-gray-700">GP%:</div>
          <div className="text-xs font-semibold text-gray-900">{gp}%</div>
        </div>
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

  // 축종별/팀별 그래프를 위한 헬퍼 함수
  const getUniqueKeys = (data: any[], suffix: string) => {
    const keys = new Set<string>();
    data.forEach((item) => {
      Object.keys(item).forEach((key) => {
        if (key.endsWith(suffix) && key !== 'name') {
          const baseKey = key.replace(suffix, '');
          keys.add(baseKey);
        }
      });
    });
    return Array.from(keys);
  };

  // 축종별/팀별 툴팁 (각 항목별 매출액, 매출이익 표시) - 축종들을 2x2 그리드로 배치
  const CategoryTooltip = ({ active, payload, label }: any) => {
    if (!active || !payload || payload.length === 0) return null;
    const toTenMillion = (v: number) => `${(v / 10000000).toFixed(1)}천만원`;
    
    // payload를 그룹화 (같은 항목의 매출액/매출이익/GP를 묶음)
    const grouped: { [key: string]: { revenue: number; profit: number; gp: number } } = {};
    
    payload.forEach((item: any) => {
      const dataKey = item.dataKey as string;
      if (dataKey.endsWith('_매출액')) {
        const baseKey = dataKey.replace('_매출액', '');
        if (!grouped[baseKey]) grouped[baseKey] = { revenue: 0, profit: 0, gp: 0 };
        grouped[baseKey].revenue = Number(item.value || 0);
      } else if (dataKey.endsWith('_매출이익')) {
        const baseKey = dataKey.replace('_매출이익', '');
        if (!grouped[baseKey]) grouped[baseKey] = { revenue: 0, profit: 0, gp: 0 };
        grouped[baseKey].profit = Number(item.value || 0);
      } else if (dataKey.endsWith('_GP')) {
        const baseKey = dataKey.replace('_GP', '');
        if (!grouped[baseKey]) grouped[baseKey] = { revenue: 0, profit: 0, gp: 0 };
        grouped[baseKey].gp = Number(item.value || 0);
      }
    });
    
    // 축종별 순서 정렬 (우육, 돈육, 계육, 양육)
    const sortedEntries = Object.entries(grouped).sort(([a], [b]) => {
      const order = ['우육', '돈육', '계육', '양육'];
      const indexA = order.indexOf(a);
      const indexB = order.indexOf(b);
      if (indexA === -1 && indexB === -1) return 0;
      if (indexA === -1) return 1;
      if (indexB === -1) return -1;
      return indexA - indexB;
    });
    
    return (
      <div className="bg-white/95 border rounded-md p-3 shadow z-[100]" style={{ zIndex: 100 }}>
        <div className="text-sm font-medium mb-3">{label}</div>
        <div className="grid grid-cols-2 gap-3">
          {sortedEntries.map(([key, values]) => {
            const gp = values.gp || (values.revenue ? ((values.profit / values.revenue) * 100).toFixed(1) : '0.0');
            return (
              <div key={key} className="border rounded p-2">
                <div className="text-xs font-semibold text-gray-800 mb-1">{key}</div>
                <div className="space-y-0.5">
                  <div className="text-xs text-gray-700">매출액: <span className="font-semibold text-gray-900">{toTenMillion(values.revenue)}</span></div>
                  <div className="text-xs text-gray-700">매출이익: <span className="font-semibold text-gray-900">{toTenMillion(values.profit)}</span></div>
                  <div className="text-xs text-gray-700">GP%: <span className="font-semibold text-gray-900">{gp}%</span></div>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    );
  };

  // 색상 팔레트
  const colors = [
    '#8884d8', '#82ca9d', '#ffc658', '#ff7300', '#00ff00', '#0088fe',
    '#00c49f', '#ffbb28', '#ff8042', '#af19ff', '#00b8d9', '#ff6b6b'
  ];

  // 축종별 고정 순서 및 색상 매핑 (가공품 제외)
  const livestockOrder = ['우육', '돈육', '계육', '양육'];
  const livestockColors: { [key: string]: string } = {
    '우육': '#8884d8',
    '돈육': '#82ca9d',
    '계육': '#ffc658',
    '양육': '#ff7300'
  };

  // 팀별 고정 순서 및 색상 매핑
  const teamOrder = ['가공장영업팀', '도매영업팀', '신경로사업팀', '중부지점'];
  const teamColors: { [key: string]: string } = {
    '가공장영업팀': '#8884d8',
    '도매영업팀': '#82ca9d',
    '신경로사업팀': '#ffc658',
    '중부지점': '#ff7300'
  };

  // 축종별 범례 컴포넌트
  const LivestockLegend = ({ data }: { data: any[] }) => {
    const availableTypes = new Set<string>();
    data.forEach((item) => {
      Object.keys(item).forEach((key) => {
        if (key.endsWith('_매출액') && key !== 'name') {
          const baseKey = key.replace('_매출액', '');
          if (livestockOrder.includes(baseKey)) {
            availableTypes.add(baseKey);
          }
        }
      });
    });
    
    const sortedTypes = livestockOrder.filter(type => availableTypes.has(type));
    
    return (
      <div className="mt-4 grid grid-cols-2 gap-2 text-xs">
        {sortedTypes.map((type) => (
          <div key={type} className="flex items-center gap-2">
            <div 
              className="w-3 h-3 rounded" 
              style={{ backgroundColor: livestockColors[type] }}
            />
            <span className="text-gray-700">{type}</span>
          </div>
        ))}
      </div>
    );
  };

  // 팀별 범례 컴포넌트
  const TeamLegend = ({ data }: { data: any[] }) => {
    const availableTeams = new Set<string>();
    data.forEach((item) => {
      Object.keys(item).forEach((key) => {
        if (key.endsWith('_매출액') && key !== 'name') {
          const baseKey = key.replace('_매출액', '');
          if (teamOrder.includes(baseKey)) {
            availableTeams.add(baseKey);
          }
        }
      });
    });
    
    const sortedTeams = teamOrder.filter(team => availableTeams.has(team));
    
    const getTeamDisplayName = (team: string) => {
      if (team === '가공장영업팀') return '가공장영업팀 (구. 수도권1팀)';
      if (team === '도매영업팀') return '도매영업팀 (구. 수도권2팀)';
      return team;
    };
    
    return (
      <div className="mt-4 grid grid-cols-2 gap-2 text-xs">
        {sortedTeams.map((team) => (
          <div key={team} className="flex items-center gap-2">
            <div 
              className="w-3 h-3 rounded" 
              style={{ backgroundColor: teamColors[team] }}
            />
            <span className="text-gray-700">{getTeamDisplayName(team)}</span>
          </div>
        ))}
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
              <ComposedChart data={chartData?.salesData || []}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis 
                  yAxisId="left"
                  tickFormatter={(value) => `${(value / 10000000).toFixed(0)}천만`} 
                />
                <YAxis 
                  yAxisId="right" 
                  orientation="right"
                  tickFormatter={(value) => `${value}%`}
                  domain={[0, 10]}
                />
                <Tooltip content={<SalesTooltip />} />
                <Bar dataKey="매출액" fill="#8884d8" yAxisId="left" opacity={0.8} name="매출액" />
                <Bar dataKey="매출이익" fill="#82ca9d" yAxisId="left" opacity={0.6} name="매출이익" />
                <Line 
                  type="monotone" 
                  dataKey="GP" 
                  stroke="#ff7300" 
                  strokeWidth={3}
                  yAxisId="right"
                  name="GP%"
                  dot={{ r: 4 }}
                />
              </ComposedChart>
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

      {/* 축종별 및 팀별 그래프 */}
      <div className="grid gap-6 md:grid-cols-2">
        {/* 축종별 매출 추이 */}
        <Card>
          <CardHeader>
            <CardTitle>축종별 매출 추이</CardTitle>
            <CardDescription>최근 6개월 축종별 매출 현황</CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <ComposedChart data={chartData?.livestockData || []}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis 
                  yAxisId="left"
                  tickFormatter={(value) => `${(value / 10000000).toFixed(0)}천만`} 
                />
                <YAxis 
                  yAxisId="right" 
                  orientation="right"
                  tickFormatter={(value) => `${value}%`}
                  domain={[0, 10]}
                />
                <Tooltip content={<CategoryTooltip />} />
                {(() => {
                  const livestockTypes = livestockOrder.filter(type => {
                    const data = chartData?.livestockData || [];
                    return data.some((item: any) => `${type}_매출액` in item);
                  });
                  return livestockTypes.flatMap((type) => [
                    <Bar 
                      key={`${type}_매출액`}
                      dataKey={`${type}_매출액`} 
                      fill={livestockColors[type]} 
                      yAxisId="left"
                      opacity={0.8}
                      name={`${type} 매출액`}
                    />,
                    <Bar 
                      key={`${type}_매출이익`}
                      dataKey={`${type}_매출이익`} 
                      fill={livestockColors[type]} 
                      yAxisId="left"
                      opacity={0.6}
                      name={`${type} 매출이익`}
                    />,
                    <Line 
                      key={`${type}_GP`}
                      type="monotone" 
                      dataKey={`${type}_GP`} 
                      stroke={livestockColors[type]} 
                      strokeWidth={3}
                      yAxisId="right"
                      name={`${type} GP%`}
                      dot={{ r: 4 }}
                    />
                  ]);
                })()}
              </ComposedChart>
            </ResponsiveContainer>
            <LivestockLegend data={chartData?.livestockData || []} />
          </CardContent>
        </Card>

        {/* 팀별 매출 추이 */}
        <Card>
          <CardHeader>
            <CardTitle>팀별 매출 추이</CardTitle>
            <CardDescription>최근 6개월 팀별 매출 현황</CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <ComposedChart data={chartData?.teamData || []}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis 
                  yAxisId="left"
                  tickFormatter={(value) => `${(value / 10000000).toFixed(0)}천만`} 
                />
                <YAxis 
                  yAxisId="right" 
                  orientation="right"
                  tickFormatter={(value) => `${value}%`}
                  domain={[0, 10]}
                />
                <Tooltip content={<CategoryTooltip />} />
                {(() => {
                  const teams = teamOrder.filter(team => {
                    const data = chartData?.teamData || [];
                    return data.some((item: any) => `${team}_매출액` in item);
                  });
                  return teams.flatMap((team) => [
                    <Bar 
                      key={`${team}_매출액`}
                      dataKey={`${team}_매출액`} 
                      fill={teamColors[team]} 
                      yAxisId="left"
                      opacity={0.8}
                      name={`${team} 매출액`}
                    />,
                    <Bar 
                      key={`${team}_매출이익`}
                      dataKey={`${team}_매출이익`} 
                      fill={teamColors[team]} 
                      yAxisId="left"
                      opacity={0.6}
                      name={`${team} 매출이익`}
                    />,
                    <Line 
                      key={`${team}_GP`}
                      type="monotone" 
                      dataKey={`${team}_GP`} 
                      stroke={teamColors[team]} 
                      strokeWidth={3}
                      yAxisId="right"
                      name={`${team} GP%`}
                      dot={{ r: 4 }}
                    />
                  ]);
                })()}
              </ComposedChart>
            </ResponsiveContainer>
            <TeamLegend data={chartData?.teamData || []} />
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
