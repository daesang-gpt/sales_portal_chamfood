'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';

// 환경에 따른 API URL 설정
const getApiBaseUrl = () => {
  if (typeof window !== 'undefined') {
    const hostname = window.location.hostname;
    const port = window.location.port;
    
    if (hostname === 'localhost' || 
        hostname === '127.0.0.1' || 
        hostname.startsWith('172.28.') || 
        port === '3000') {
      return 'http://127.0.0.1:8000';
    }
    
    return 'http://192.168.99.37:8000';
  }
  
  return 'http://127.0.0.1:8000';
};

interface ChangePasswordResponse {
  success: boolean;
  message: string;
  errors?: {
    current_password?: string[];
    new_password?: string[];
    confirm_password?: string[];
  };
}

export default function ChangePasswordPage() {
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [fieldErrors, setFieldErrors] = useState<{ [key: string]: string }>({});
  const router = useRouter();

  useEffect(() => {
    // 로그인 확인
    const accessToken = localStorage.getItem('access_token');
    if (!accessToken) {
      router.push('/login');
    }
  }, [router]);

  const handleChangePassword = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError('');
    setFieldErrors({});

    // 클라이언트 측 유효성 검사
    if (newPassword !== confirmPassword) {
      setFieldErrors({ confirm_password: '새 비밀번호가 일치하지 않습니다.' });
      setIsLoading(false);
      return;
    }

    if (newPassword.length < 8) {
      setFieldErrors({ new_password: '비밀번호는 최소 8자 이상이어야 합니다.' });
      setIsLoading(false);
      return;
    }

    try {
      const apiUrl = `${getApiBaseUrl()}/api/change-password/`;
      const accessToken = localStorage.getItem('access_token');
      
      const response = await fetch(apiUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${accessToken}`,
        },
        body: JSON.stringify({
          current_password: currentPassword,
          new_password: newPassword,
          confirm_password: confirmPassword,
        }),
      });
      
      // JWT 토큰 만료 처리
      if (response.status === 401) {
        try {
          const errorData = await response.json();
          const errorDetail = errorData.detail || errorData.error || '';
          if (errorDetail.includes('Given token not valid for any token type') || 
              errorDetail.includes('token_not_valid') ||
              errorDetail.includes('Token is invalid or expired')) {
            localStorage.removeItem('access_token');
            localStorage.removeItem('refresh_token');
            localStorage.removeItem('user');
            alert('로그인 세션이 만료되었습니다. 다시 로그인해주세요.');
            router.push('/login');
            return;
          }
        } catch {
          // JSON 파싱 실패 시에도 401이면 토큰 만료로 간주
          localStorage.removeItem('access_token');
          localStorage.removeItem('refresh_token');
          localStorage.removeItem('user');
          alert('로그인 세션이 만료되었습니다. 다시 로그인해주세요.');
          router.push('/login');
          return;
        }
      }
      
      const data: ChangePasswordResponse = await response.json();
      
      if (data.success) {
        alert('비밀번호가 성공적으로 변경되었습니다. 다시 로그인해주세요.');
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        localStorage.removeItem('user');
        router.push('/login');
      } else {
        if (data.errors) {
          const errors: { [key: string]: string } = {};
          Object.keys(data.errors).forEach(key => {
            if (data.errors![key as keyof typeof data.errors] && data.errors![key as keyof typeof data.errors]!.length > 0) {
              errors[key] = data.errors![key as keyof typeof data.errors]![0];
            }
          });
          setFieldErrors(errors);
        }
        setError(data.message || '비밀번호 변경에 실패했습니다.');
      }
    } catch (err) {
      setError('서버 연결에 실패했습니다.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <Card className="w-full max-w-md">
        <CardHeader className="space-y-1">
          <CardTitle className="text-2xl text-center">비밀번호 변경</CardTitle>
          <CardDescription className="text-center">
            최초 로그인 시 비밀번호를 변경해주세요
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleChangePassword} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="current-password">현재 비밀번호</Label>
              <Input
                id="current-password"
                type="password"
                value={currentPassword}
                onChange={(e) => setCurrentPassword(e.target.value)}
                placeholder="현재 비밀번호를 입력하세요"
                required
                disabled={isLoading}
              />
              {fieldErrors.current_password && (
                <p className="text-sm text-red-500">{fieldErrors.current_password}</p>
              )}
            </div>
            <div className="space-y-2">
              <Label htmlFor="new-password">새 비밀번호</Label>
              <Input
                id="new-password"
                type="password"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                placeholder="새 비밀번호를 입력하세요 (최소 8자)"
                required
                disabled={isLoading}
                minLength={8}
              />
              {fieldErrors.new_password && (
                <p className="text-sm text-red-500">{fieldErrors.new_password}</p>
              )}
            </div>
            <div className="space-y-2">
              <Label htmlFor="confirm-password">새 비밀번호 확인</Label>
              <Input
                id="confirm-password"
                type="password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                placeholder="새 비밀번호를 다시 입력하세요"
                required
                disabled={isLoading}
                minLength={8}
              />
              {fieldErrors.confirm_password && (
                <p className="text-sm text-red-500">{fieldErrors.confirm_password}</p>
              )}
            </div>
            
            {error && (
              <Alert variant="destructive">
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            )}

            <Button type="submit" className="w-full" disabled={isLoading}>
              {isLoading ? '변경 중...' : '비밀번호 변경'}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}

