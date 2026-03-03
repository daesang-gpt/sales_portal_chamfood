"use client"

import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { ArrowLeft, Loader2, Filter } from "lucide-react"
import { useRouter } from "next/navigation"
import { getUserFromToken, isAdmin } from "@/lib/auth"
import { getApiBaseUrl } from "@/lib/api"

type AuditLogType = {
  id: number
  user: number | null
  username: string | null
  action_type: string
  action_type_display: string
  description: string | null
  ip_address: string | null
  user_agent: string | null
  target_user: number | null
  target_username: string | null
  old_value: string | null
  new_value: string | null
  resource_type: string | null
  resource_id: string | null
  created_at: string
}

type AuditLogsResponse = {
  results: AuditLogType[]
  count: number
  page: number
  page_size: number
  total_pages: number
}

const ACTION_TYPE_LABELS: Record<string, string> = {
  'login': '로그인',
  'logout': '로그아웃',
  'permission_change': '권한 변경',
  'personal_info_access': '개인정보 접근',
  'download': '다운로드',
}

const ACTION_TYPE_COLORS: Record<string, string> = {
  'login': 'bg-green-100 text-green-800',
  'logout': 'bg-gray-100 text-gray-800',
  'permission_change': 'bg-yellow-100 text-yellow-800',
  'personal_info_access': 'bg-blue-100 text-blue-800',
  'download': 'bg-purple-100 text-purple-800',
}

export default function AuditLogsPage() {
  const router = useRouter()
  const [logs, setLogs] = useState<AuditLogType[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [page, setPage] = useState(1)
  const [totalPages, setTotalPages] = useState(1)
  const [totalCount, setTotalCount] = useState(0)
  const [pageSize] = useState(50)
  
  const [actionTypeFilter, setActionTypeFilter] = useState<string>('')
  const [startDate, setStartDate] = useState<string>('')
  const [endDate, setEndDate] = useState<string>('')
  
  const isAdminUser = isAdmin()

  useEffect(() => {
    if (!isAdminUser) {
      router.push('/manage')
      return
    }

    fetchLogs()
  }, [page, actionTypeFilter, startDate, endDate])

  const fetchLogs = async () => {
    try {
      setLoading(true)
      setError(null)
      
      const apiBaseUrl = getApiBaseUrl()
      const token = typeof window !== 'undefined' ? localStorage.getItem('access_token') : null

      const params = new URLSearchParams()
      params.append('page', page.toString())
      params.append('page_size', pageSize.toString())
      if (actionTypeFilter) {
        params.append('action_type', actionTypeFilter)
      }
      if (startDate) {
        params.append('start_date', startDate)
      }
      if (endDate) {
        params.append('end_date', endDate)
      }

      const res = await fetch(`${apiBaseUrl}/audit-logs/?${params.toString()}`, {
        headers: {
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
      })

      if (!res.ok) {
        const errorData = await res.json().catch(() => ({}))
        throw new Error(errorData.error || '로그 조회에 실패했습니다.')
      }

      const data: AuditLogsResponse = await res.json()
      setLogs(data.results)
      setTotalPages(data.total_pages)
      setTotalCount(data.count)
    } catch (err: any) {
      setError(err.message || '로그를 불러오는 중 오류가 발생했습니다.')
      console.error('로그 조회 오류:', err)
    } finally {
      setLoading(false)
    }
  }

  const formatDateTime = (dateString: string) => {
    try {
      const date = new Date(dateString)
      return date.toLocaleString('ko-KR', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
      })
    } catch {
      return dateString
    }
  }

  const handleResetFilters = () => {
    setActionTypeFilter('')
    setStartDate('')
    setEndDate('')
    setPage(1)
  }

  if (!isAdminUser) {
    return null
  }

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-7xl mx-auto space-y-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Button
              variant="ghost"
              size="icon"
              onClick={() => router.push('/manage')}
            >
              <ArrowLeft className="h-4 w-4" />
            </Button>
            <div>
              <h1 className="text-3xl font-bold">접속 기록 및 권한 변경 로그</h1>
              <p className="text-gray-600 mt-1">시스템 접속 및 권한 변경 이력을 조회합니다.</p>
            </div>
          </div>
        </div>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Filter className="h-5 w-5" />
              필터
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div>
                <label className="text-sm font-medium mb-2 block">액션 타입</label>
                <Select value={actionTypeFilter || undefined} onValueChange={(value) => setActionTypeFilter(value || '')}>
                  <SelectTrigger>
                    <SelectValue placeholder="전체" />
                  </SelectTrigger>
                  <SelectContent>
                    {Object.entries(ACTION_TYPE_LABELS).map(([value, label]) => (
                      <SelectItem key={value} value={value}>
                        {label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div>
                <label className="text-sm font-medium mb-2 block">시작일</label>
                <Input
                  type="date"
                  value={startDate}
                  onChange={(e) => setStartDate(e.target.value)}
                />
              </div>
              <div>
                <label className="text-sm font-medium mb-2 block">종료일</label>
                <Input
                  type="date"
                  value={endDate}
                  onChange={(e) => setEndDate(e.target.value)}
                />
              </div>
              <div className="flex items-end">
                <Button
                  variant="outline"
                  onClick={handleResetFilters}
                  className="w-full"
                >
                  필터 초기화
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>로그 목록</CardTitle>
            <CardDescription>
              총 {totalCount.toLocaleString()}건의 로그가 있습니다.
            </CardDescription>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="flex items-center justify-center py-12">
                <Loader2 className="h-8 w-8 animate-spin text-gray-400" />
              </div>
            ) : error ? (
              <div className="text-center py-12 text-red-600">{error}</div>
            ) : logs.length === 0 ? (
              <div className="text-center py-12 text-gray-500">로그가 없습니다.</div>
            ) : (
              <>
                <div className="overflow-x-auto">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>일시</TableHead>
                        <TableHead>사용자</TableHead>
                        <TableHead>액션 타입</TableHead>
                        <TableHead>설명</TableHead>
                        <TableHead>IP 주소</TableHead>
                        <TableHead>대상 사용자</TableHead>
                        <TableHead>변경 내용</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {logs.map((log) => (
                        <TableRow key={log.id}>
                          <TableCell className="font-mono text-sm">
                            {formatDateTime(log.created_at)}
                          </TableCell>
                          <TableCell>{log.username || '-'}</TableCell>
                          <TableCell>
                            <Badge className={ACTION_TYPE_COLORS[log.action_type] || 'bg-gray-100 text-gray-800'}>
                              {log.action_type_display}
                            </Badge>
                          </TableCell>
                          <TableCell className="max-w-md truncate" title={log.description || ''}>
                            {log.description || '-'}
                          </TableCell>
                          <TableCell className="font-mono text-sm">
                            {log.ip_address || '-'}
                          </TableCell>
                          <TableCell>{log.target_username || '-'}</TableCell>
                          <TableCell>
                            {log.old_value && log.new_value ? (
                              <span className="text-sm">
                                <span className="text-red-600">{log.old_value}</span>
                                {' → '}
                                <span className="text-green-600">{log.new_value}</span>
                              </span>
                            ) : (
                              '-'
                            )}
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>

                {totalPages > 1 && (
                  <div className="flex items-center justify-between mt-4">
                    <div className="text-sm text-gray-600">
                      {((page - 1) * pageSize + 1).toLocaleString()} - {Math.min(page * pageSize, totalCount).toLocaleString()} / {totalCount.toLocaleString()}건
                    </div>
                    <div className="flex gap-2">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => setPage(p => Math.max(1, p - 1))}
                        disabled={page === 1}
                      >
                        이전
                      </Button>
                      <div className="flex items-center px-4 text-sm">
                        {page} / {totalPages}
                      </div>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                        disabled={page === totalPages}
                      >
                        다음
                      </Button>
                    </div>
                  </div>
                )}
              </>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
