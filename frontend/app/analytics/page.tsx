"use client"

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import {
  BarChart,
  Bar,
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
import { TrendingUp, FileText, Building2, Phone } from "lucide-react"

// 영업사원별 일별 데이터
const salesPersonData = [
  { name: "엄재후", 매출액: 25000000, 매출수량: 6800, 매출건수: 45, 매출이익: 2500000 },
  { name: "김영희", 매출액: 18000000, 매출수량: 4900, 매출건수: 32, 매출이익: 1800000 },
  { name: "박민수", 매출액: 22000000, 매출수량: 6100, 매출건수: 38, 매출이익: 2200000 },
  { name: "이수진", 매출액: 15000000, 매출수량: 4200, 매출건수: 28, 매출이익: 1500000 },
]

// 채널별 매출 데이터
const channelSalesData = [
  { name: "가공장", 매출액: 35000000, 비율: 43.8 },
  { name: "프랜차이즈", 매출액: 28000000, 비율: 35.0 },
  { name: "도소매", 매출액: 17000000, 비율: 21.3 },
]

// 축종별 매출 데이터
const livestockData = [
  { name: "닭고기", value: 45, color: "#0088FE" },
  { name: "돼지고기", value: 30, color: "#00C49F" },
  { name: "소고기", value: 20, color: "#FFBB28" },
  { name: "기타", value: 5, color: "#FF8042" },
]

// 월별 신규 고객사 연락 현황
const newCustomerContactData = [
  { month: "1월", 연락횟수: 25, 매출발생: 8 },
  { month: "2월", 연락횟수: 32, 매출발생: 12 },
  { month: "3월", 연락횟수: 28, 매출발생: 9 },
  { month: "4월", 연락횟수: 35, 매출발생: 15 },
  { month: "5월", 연락횟수: 42, 매출발생: 18 },
  { month: "6월", 연락횟수: 38, 매출발생: 16 },
]

export default function AnalyticsPage() {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold">영업 분석</h1>
      </div>

      {/* 주요 지표 */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">총 영업일지 작성</CardTitle>
            <FileText className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">143건</div>
            <p className="text-xs text-muted-foreground">이번 달 24건</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">총 업체 연락</CardTitle>
            <Phone className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">238회</div>
            <p className="text-xs text-muted-foreground">대면 142회, 전화 96회</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">신규 고객사 연락</CardTitle>
            <Building2 className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">78회</div>
            <p className="text-xs text-muted-foreground">매출 발생 32건</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">전환율</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">41.0%</div>
            <p className="text-xs text-muted-foreground">신규→매출 전환율</p>
          </CardContent>
        </Card>
      </div>

      {/* 영업사원별 성과 */}
      <Card>
        <CardHeader>
          <CardTitle>영업사원별 일별 성과</CardTitle>
          <CardDescription>매출액, 매출수량, 매출건수, 매출이익 현황</CardDescription>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={400}>
            <BarChart data={salesPersonData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis tickFormatter={(value) => `${(value / 10000000).toFixed(0)}천만`} />
              <Tooltip
                formatter={(value: number, name: string) => {
                  if (name === "매출액" || name === "매출이익") {
                    return [`${(value / 10000000).toFixed(1)}천만원`, name]
                  } else if (name === "매출수량") {
                    return [`${(value / 1000).toFixed(1)}톤`, name]
                  } else {
                    return [`${value}건`, name]
                  }
                }}
              />
              <Bar dataKey="매출액" fill="#8884d8" />
              <Bar dataKey="매출이익" fill="#82ca9d" />
            </BarChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      <div className="grid gap-6 md:grid-cols-2">
        {/* 채널별 매출 현황 */}
        <Card>
          <CardHeader>
            <CardTitle>채널별 매출 현황</CardTitle>
            <CardDescription>유통형태별 매출 분석</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {channelSalesData.map((channel, index) => (
                <div key={index} className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <div className="w-3 h-3 rounded-full bg-blue-500" />
                    <span className="font-medium">{channel.name}</span>
                  </div>
                  <div className="text-right">
                    <div className="font-bold">{(channel.매출액 / 10000000).toFixed(1)}천만원</div>
                    <div className="text-sm text-muted-foreground">{channel.비율}%</div>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* 축종별 매출 비율 */}
        <Card>
          <CardHeader>
            <CardTitle>축종별 매출 비율</CardTitle>
            <CardDescription>품목별 매출 구성</CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={250}>
              <PieChart>
                <Pie
                  data={livestockData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={(props: any) => {
                    const { name, percent } = props;
                    return `${name} ${(percent * 100).toFixed(0)}%`;
                  }}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {livestockData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      {/* 신규 고객사 연락 및 매출 발생 현황 */}
      <Card>
        <CardHeader>
          <CardTitle>신규 고객사 연락 및 매출 발생 현황</CardTitle>
          <CardDescription>월별 신규 고객사 연락 횟수와 매출 발생 건수</CardDescription>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={newCustomerContactData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="month" />
              <YAxis />
              <Tooltip />
              <Line type="monotone" dataKey="연락횟수" stroke="#8884d8" strokeWidth={2} name="연락 횟수" />
              <Line type="monotone" dataKey="매출발생" stroke="#82ca9d" strokeWidth={2} name="매출 발생" />
            </LineChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>
    </div>
  )
}
