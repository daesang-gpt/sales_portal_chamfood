'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import Link from 'next/link';
import { jwtDecode } from 'jwt-decode';

interface LoginResponse {
  success: boolean;
  message: string;
  access_token?: string;
  refresh_token?: string;
  user?: {
    id: number;
    name: string;
    department: string;
    employee_number: string;
    role: string;
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
      const response = await fetch('http://localhost:8000/api/token/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          username: username,
          password: password,
        }),
      });

      if (!response.ok) {
        setError('아이디 또는 비밀번호가 올바르지 않습니다.');
        setIsLoading(false);
        return;
      }

      const data: TokenResponse = await response.json();
      // access 토큰에서 사용자 정보 추출
      const payload: TokenPayload = jwtDecode(data.access);
      // user 정보 구성 (role, user_id만 기본, 필요시 추가)
      const user = {
        id: payload.user_id,
        name: '', // 필요시 별도 API로 조회
        department: '',
        employee_number: '',
        role: payload.role,
      };
      localStorage.setItem('access_token', data.access);
      localStorage.setItem('refresh_token', data.refresh);
      localStorage.setItem('user', JSON.stringify(user));
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

            <div className="text-center text-sm">
              계정이 없으신가요?{' '}
              <Link href="/register" className="text-blue-600 hover:underline">
                회원가입
              </Link>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  );
} 