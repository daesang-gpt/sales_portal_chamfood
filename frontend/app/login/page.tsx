'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { getApiBaseUrl } from '@/lib/api';

interface LoginResponse {
  success: boolean;
  message: string;
  access_token?: string;
  refresh_token?: string;
  requires_password_change?: boolean;
  user?: {
    id: number;
    name: string;
    department: string;
    employee_number: string;
    role: string;
    is_password_changed?: boolean;
  };
}

interface TokenResponse {
  access: string;
  refresh: string;
}

interface TokenPayload {
  user_id: number;
  role: string;
  exp: number;
  iat: number;
  // 필요시 name, department 등 추가
}

export default function LoginPage() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const router = useRouter();

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError('');

    try {
      const apiUrl = `${getApiBaseUrl()}/login/`;
      if (process.env.NODE_ENV === 'development') {
        console.log('Login API URL:', apiUrl);
      }
      
      const response = await fetch(apiUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          id: username,
          password: password,
        }),
      });

      if (!response.ok) {
        setError('아이디 또는 비밀번호가 올바르지 않습니다.');
        setIsLoading(false);
        return;
      }

      const data: LoginResponse = await response.json();
      
      if (data.success && data.access_token && data.user) {
        localStorage.setItem('access_token', data.access_token);
        localStorage.setItem('refresh_token', data.refresh_token || '');
        localStorage.setItem('user', JSON.stringify(data.user));
        
        // 로그인 성공 이벤트 발생 (Sidebar에서 감지)
        if (typeof window !== 'undefined') {
          window.dispatchEvent(new Event('auth-change'));
        }
        
        // 최초 로그인인 경우 비밀번호 변경 페이지로 이동
        if (data.requires_password_change) {
          router.push('/change-password');
          return;
        }
      } else {
        setError(data.message || '로그인에 실패했습니다.');
        setIsLoading(false);
        return;
      }
      router.push('/');
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
          <CardTitle className="text-2xl text-center">로그인</CardTitle>
          <CardDescription className="text-center">
            아이디와 비밀번호를 입력해주세요
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleLogin} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="username">아이디</Label>
              <Input
                id="username"
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="아이디를 입력하세요"
                required
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="password">비밀번호</Label>
              <Input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="비밀번호를 입력하세요"
                required
              />
            </div>
            
            {error && (
              <Alert variant="destructive">
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            )}

            <Button type="submit" className="w-full" disabled={isLoading}>
              {isLoading ? '로그인 중...' : '로그인'}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
} 