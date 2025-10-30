"use client"

import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Badge } from "@/components/ui/badge"
import { ArrowLeft, Loader2, User } from "lucide-react"
import { useRouter } from "next/navigation"
import { getUserFromToken, isAdmin } from "@/lib/auth"

type UserType = {
  id: number
  name: string
  username: string
  department: string
  employee_number: string
  role: string
}

export default function UsersManagementPage() {
  const router = useRouter()
  const [users, setUsers] = useState<UserType[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const currentUser = getUserFromToken()
  const isAdminUser = isAdmin()

  useEffect(() => {
    if (!isAdminUser) {
      router.push('/admin')
      return
    }

    fetchUsers()
  }, [])

  const fetchUsers = async () => {
    try {
      setLoading(true)
      setError(null)
      
      // 환경에 따른 API URL 설정
      const apiBaseUrl = 'http://127.0.0.1:8000/api'
      
      const res = await fetch(`${apiBaseUrl}/users/`)
      if (res.ok) {
        const data = await res.json()
        setUsers(data)
      } else {
        setError('사용자 목록을 불러오는데 실패했습니다.')
      }
    } catch (err) {
      console.error('사용자 목록 불러오기 실패:', err)
      setError('사용자 목록을 불러오는데 실패했습니다.')
    } finally {
      setLoading(false)
    }
  }

  if (!isAdminUser) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-red-600 mb-2">권한 없음</h1>
          <p className="text-gray-600">관리자만 접근할 수 있는 페이지입니다.</p>
        </div>
      </div>
    )
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="flex flex-col items-center">
          <Loader2 className="h-8 w-8 animate-spin mb-4" />
          <p>사용자 목록을 불러오는 중...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6 p-8">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button
            variant="outline"
            size="sm"
            onClick={() => router.push('/admin')}
          >
            <ArrowLeft className="mr-2 h-4 w-4" />
            관리자 대시보드로
          </Button>
          <h1 className="text-3xl font-bold">사용자 관리</h1>
        </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <User className="h-5 w-5" />
            전체 사용자 목록
          </CardTitle>
          <CardDescription>
            등록된 모든 사용자의 정보를 확인하고 관리합니다.
          </CardDescription>
        </CardHeader>
        <CardContent>
          {error ? (
            <div className="text-center py-8">
              <p className="text-red-600">{error}</p>
              <Button 
                variant="outline" 
                onClick={fetchUsers}
                className="mt-4"
              >
                다시 시도
              </Button>
            </div>
          ) : (
            <div className="rounded-md border">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="w-[80px]">ID</TableHead>
                    <TableHead>이름</TableHead>
                    <TableHead>아이디</TableHead>
                    <TableHead>부서</TableHead>
                    <TableHead>사번</TableHead>
                    <TableHead>권한</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {users.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={6} className="text-center py-8">
                        등록된 사용자가 없습니다.
                      </TableCell>
                    </TableRow>
                  ) : (
                    users.map((user) => (
                      <TableRow key={user.id}>
                        <TableCell className="font-medium">{user.id}</TableCell>
                        <TableCell>{user.name}</TableCell>
                        <TableCell>{user.username}</TableCell>
                        <TableCell>{user.department}</TableCell>
                        <TableCell>{user.employee_number}</TableCell>
                        <TableCell>
                          <Badge variant={user.role === 'admin' ? 'default' : 'secondary'}>
                            {user.role === 'admin' ? '관리자' : '사용자'}
                          </Badge>
                        </TableCell>
                      </TableRow>
                    ))
                  )}
                </TableBody>
              </Table>
            </div>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardContent className="pt-6">
          <div className="flex justify-between items-center">
            <div>
              <p className="text-sm text-muted-foreground">총 사용자 수</p>
              <p className="text-2xl font-bold">{users.length}명</p>
            </div>
            <div className="text-right">
              <p className="text-sm text-muted-foreground">관리자 수</p>
              <p className="text-2xl font-bold">
                {users.filter(u => u.role === 'admin').length}명
              </p>
            </div>
            <div className="text-right">
              <p className="text-sm text-muted-foreground">일반 사용자 수</p>
              <p className="text-2xl font-bold">
                {users.filter(u => u.role === 'user').length}명
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

