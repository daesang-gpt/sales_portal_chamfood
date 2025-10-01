"use client"

import React, { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Download, Upload, AlertCircle, CheckCircle, Loader2 } from "lucide-react"
import { companyApi } from "@/lib/api"
import { useToast } from "@/hooks/use-toast"
import { getUserFromToken, isAdmin } from "@/lib/auth"

export default function CsvManagementPage() {
  const [loading, setLoading] = useState<'reports-download' | 'companies-download' | 'reports-upload' | 'companies-upload' | null>(null)
  const [errors, setErrors] = useState<string[]>([])
  const [successMessage, setSuccessMessage] = useState('')
  const { toast } = useToast()
  
  const currentUser = getUserFromToken()
  const isAdminUser = isAdmin()

  const handleDownload = async (type: 'reports' | 'companies') => {
    try {
      setLoading(type === 'reports' ? 'reports-download' : 'companies-download')
      setErrors([])
      setSuccessMessage('')

      const blob = type === 'reports' 
        ? await companyApi.downloadReportsCsv() 
        : await companyApi.downloadCompaniesCsv()

      // 파일 다운로드
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = type === 'reports' ? '영업일지_백업.csv' : '회사_백업.csv'
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      window.URL.revokeObjectURL(url)

      toast({
        title: "다운로드 완료",
        description: type === 'reports' ? "영업일지 데이터를 다운로드했습니다." : "회사 데이터를 다운로드했습니다.",
        variant: "default",
      })

    } catch (error) {
      setErrors([error instanceof Error ? error.message : '다운로드 중 오류가 발생했습니다.'])
      toast({
        title: "다운로드 실패",
        description: error instanceof Error ? error.message : '다운로드 중 오류가 발생했습니다.',
        variant: "destructive",
      })
    } finally {
      setLoading(null)
    }
  }

  const handleUpload = async (type: 'reports' | 'companies', file: File) => {
    try {
      setLoading(type === 'reports' ? 'reports-upload' : 'companies-upload')
      setErrors([])
      setSuccessMessage('')

      const result = type === 'reports' 
        ? await companyApi.uploadReportsCsv(file) 
        : await companyApi.uploadCompaniesCsv(file)

      setSuccessMessage(result.message)
      setErrors(result.errors || [])

      toast({
        title: "업로드 완료",
        description: result.message,
        variant: "default",
      })

    } catch (error) {
      setErrors([error instanceof Error ? error.message : '업로드 중 오류가 발생했습니다.'])
      toast({
        title: "업로드 실패",
        description: error instanceof Error ? error.message : '업로드 중 오류가 발생했습니다.',
        variant: "destructive",
      })
    } finally {
      setLoading(null)
    }
  }

  if (!isAdminUser) {
    return (
      <div className="space-y-6">
        <div className="text-center py-8">
          <AlertCircle className="mx-auto h-16 w-16 text-red-500 mb-4" />
          <h1 className="text-2xl font-bold text-red-600 mb-2">권한 없음</h1>
          <p className="text-gray-600">관리자만 접근할 수 있는 페이지입니다.</p>
          <p className="text-sm text-gray-500 mt-2">
            현재 사용자: {currentUser?.name} ({currentUser?.role})
          </p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">CSV 데이터 관리</h1>
        <p className="text-muted-foreground mt-2">
          영업일지와 회사 데이터를 CSV/XLSX 파일로 일괄 다운로드하고 업로드할 수 있습니다.
        </p>
        <p className="text-sm text-gray-500 mt-1">
          관리자: {currentUser?.name} ({currentUser?.department})
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* 영업일지 다운로드/업로드 */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Download className="h-5 w-5" />
              영업일지 데이터
            </CardTitle>
            <CardDescription>
              영업일지 데이터를 CSV/XLSX 파일로 다운로드하거나 수정 후 업로드할 수 있습니다.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Button 
                onClick={() => handleDownload('reports')}
                disabled={loading === 'reports-download'}
                className="w-full"
                variant="outline"
              >
                {loading === 'reports-download' ? (
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                ) : (
                  <Download className="mr-2 h-4 w-4" />
                )}
                영업일지 다운로드
              </Button>
            </div>

            <div className="space-y-2">
              <Label htmlFor="reports-upload">영업일지 업로드</Label>
              <Input
                id="reports-upload"
                type="file"
                accept=".csv,.xlsx"
                disabled={loading === 'reports-upload'}
                onChange={(e) => {
                  const file = e.target.files?.[0]
                  if (file) {
                    handleUpload('reports', file)
                  }
                }}
              />
              <Button
                disabled={loading === 'reports-upload'}
                className="w-full"
              >
                {loading === 'reports-upload' && (
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                )}
                영업일지 업로드
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* 회사 데이터 다운로드/업로드 */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Upload className="h-5 w-5" />
              회사 데이터
            </CardTitle>
            <CardDescription>
              회사 데이터를 CSV/XLSX 파일로 다운로드하거나 수정 후 업로드할 수 있습니다.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Button 
                onClick={() => handleDownload('companies')}
                disabled={loading === 'companies-download'}
                className="w-full"
                variant="outline"
              >
                {loading === 'companies-download' ? (
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                ) : (
                  <Download className="mr-2 h-4 w-4" />
                )}
                회사 데이터 다운로드
              </Button>
            </div>

            <div className="space-y-2">
              <Label htmlFor="companies-upload">회사 데이터 업로드</Label>
              <Input
                id="companies-upload"
                type="file"
                accept=".csv,.xlsx"
                disabled={loading === 'companies-upload'}
                onChange={(e) => {
                  const file = e.target.files?.[0]
                  if (file) {
                    handleUpload('companies', file)
                  }
                }}
              />
              <Button
                disabled={loading === 'companies-upload'}
                className="w-full"
              >
                {loading === 'companies-upload' && (
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                )}
                회사 데이터 업로드
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* 결과 메시지 */}
      {successMessage && (
        <Card className="border-green-200 bg-green-50">
          <CardContent className="pt-6">
            <div className="flex items-start gap-3">
              <CheckCircle className="h-5 w-5 text-green-600 mt-0.5" />
              <div>
                <h3 className="font-medium text-green-800">업로드 완료</h3>
                <p className="text-green-700 text-sm mt-1">{successMessage}</p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* 오류 메시지 */}
      {errors.length > 0 && (
        <Card className="border-red-200 bg-red-50">
          <CardContent className="pt-6">
            <div className="flex items-start gap-3">
              <AlertCircle className="h-5 w-5 text-red-600 mt-0.5" />
              <div>
                <h3 className="font-medium text-red-800">오류 발생</h3>
                <div className="mt-2 space-y-1">
                  {errors.map((error, index) => (
                    <p key={index} className="text-red-700 text-sm">{error}</p>
                  ))}
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* 가이드 */}
      <Card>
        <CardHeader>
          <CardTitle>사용 가이드</CardTitle>
          <CardDescription>
            CSV/XLSX 파일 형식과 주의사항에 대한 안내입니다.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <h4 className="font-medium mb-2">영업일지 파일 형식 (CSV/XLSX)</h4>
            <p className="text-sm text-muted-foreground mb-2">
              필수 컬럼: ID, 작성자ID, 작성자명, 팀명, 방문일자, 회사명, 회사ID, 영업형태, 미팅내용, 태그, 작성일
            </p>
            <p className="text-sm text-muted-foreground">
              • ID가 있으면 업데이트, 없으면 새로 생성됩니다<br/>
              • 작성자ID와 회사ID는 실제 존재하는 ID여야 합니다<br/>
              • 방문일자는 YYYY-MM-DD 형식이어야 합니다
            </p>
          </div>

          <div>
            <h4 className="font-medium mb-2">회사 파일 형식 (CSV/XLSX)</h4>
            <p className="text-sm text-muted-foreground mb-2">
              필수 컬럼: ID, 회사명, 영업일지회사코드, 영업사원ID, 소재지, 사용품목
            </p>
            <p className="text-sm text-muted-foreground">
              • ID가 있으면 업데이트, 없으면 새로 생성됩니다<br/>
              • 영업사원ID는 실제 존재하는 사용자 ID여야 합니다<br/>
              • 소재지와 사용품목은 선택사항입니다
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
