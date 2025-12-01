'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { isAuthenticated, logout, getUserFromToken } from '@/lib/auth';

export default function MyPage() {
  const [user, setUser] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isEditing, setIsEditing] = useState(false);
  const [editData, setEditData] = useState({
    name: '',
    department: '',
    employee_number: ''
  });
  const [message, setMessage] = useState('');
  const router = useRouter();

  useEffect(() => {
    // 인증 확인
    if (!isAuthenticated()) {
      router.push('/login');
      return;
    }

    const currentUser = getUserFromToken();
    setUser(currentUser);
    setEditData({
      name: currentUser?.name || '',
      department: currentUser?.department || '',
      employee_number: currentUser?.employee_number || ''
    });
    setIsLoading(false);
  }, [router]);

  const handleLogout = async () => {
    await logout();
    router.push('/login');
  };

  const handleEdit = () => {
    setIsEditing(true);
  };

  const handleSave = async () => {
    try {
      // 여기서 실제로는 API 호출을 통해 사용자 정보를 업데이트합니다
      // 현재는 localStorage만 업데이트
      const updatedUser = { ...user, ...editData };
      localStorage.setItem('user', JSON.stringify(updatedUser));
      setUser(updatedUser);
      setIsEditing(false);
      setMessage('정보가 성공적으로 업데이트되었습니다.');
      
      // 사용자 정보 업데이트 이벤트 발생 (Sidebar에서 감지)
      if (typeof window !== 'undefined') {
        window.dispatchEvent(new Event('auth-change'));
      }
      
      setTimeout(() => setMessage(''), 3000);
    } catch (error) {
      setMessage('정보 업데이트에 실패했습니다.');
    }
  };

  const handleCancel = () => {
    setEditData({
      name: user?.name || '',
      department: user?.department || '',
      employee_number: user?.employee_number || ''
    });
    setIsEditing(false);
  };

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-lg">로딩 중...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-2xl mx-auto">
        <div className="flex justify-between items-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900">마이페이지</h1>
          <Button onClick={handleLogout} variant="outline">
            로그아웃
          </Button>
        </div>

        {message && (
          <Alert className="mb-6">
            <AlertDescription>{message}</AlertDescription>
          </Alert>
        )}

        {user && (
          <Card>
            <CardHeader>
              <div className="flex justify-between items-center">
                <div>
                  <CardTitle>내 정보</CardTitle>
                  <CardDescription>개인 정보를 확인하고 수정할 수 있습니다.</CardDescription>
                </div>
                {!isEditing && (
                  <Button onClick={handleEdit} variant="outline">
                    수정
                  </Button>
                )}
              </div>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="username">아이디</Label>
                  <Input
                    id="username"
                    value={user.username}
                    disabled
                    className="bg-gray-100"
                  />
                </div>
                
                <div className="space-y-2">
                  <Label htmlFor="role">권한</Label>
                  <Input
                    id="role"
                    value={user.role === 'admin' ? '관리자' : user.role === 'viewer' ? '뷰어' : '일반 사용자'}
                    disabled
                    className="bg-gray-100"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="name">이름</Label>
                  {isEditing ? (
                    <Input
                      id="name"
                      value={editData.name}
                      onChange={(e) => setEditData(prev => ({ ...prev, name: e.target.value }))}
                    />
                  ) : (
                    <Input
                      id="name"
                      value={user.name}
                      disabled
                      className="bg-gray-100"
                    />
                  )}
                </div>

                <div className="space-y-2">
                  <Label htmlFor="department">부서</Label>
                  {isEditing ? (
                    <Input
                      id="department"
                      value={editData.department}
                      onChange={(e) => setEditData(prev => ({ ...prev, department: e.target.value }))}
                    />
                  ) : (
                    <Input
                      id="department"
                      value={user.department}
                      disabled
                      className="bg-gray-100"
                    />
                  )}
                </div>

                <div className="space-y-2">
                  <Label htmlFor="employee_number">사번</Label>
                  {isEditing ? (
                    <Input
                      id="employee_number"
                      value={editData.employee_number}
                      onChange={(e) => setEditData(prev => ({ ...prev, employee_number: e.target.value }))}
                    />
                  ) : (
                    <Input
                      id="employee_number"
                      value={user.employee_number}
                      disabled
                      className="bg-gray-100"
                    />
                  )}
                </div>
              </div>

              {isEditing && (
                <div className="flex gap-2 pt-4">
                  <Button onClick={handleSave}>
                    저장
                  </Button>
                  <Button onClick={handleCancel} variant="outline">
                    취소
                  </Button>
                </div>
              )}
            </CardContent>
          </Card>
        )}

        <div className="mt-8 grid grid-cols-1 md:grid-cols-2 gap-6">
          <Card>
            <CardHeader>
              <CardTitle>내 활동</CardTitle>
              <CardDescription>최근 활동 내역을 확인합니다.</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                <p className="text-sm text-gray-600">최근 로그인: {new Date().toLocaleDateString()}</p>
                <p className="text-sm text-gray-600">작성한 보고서: 0개</p>
                <p className="text-sm text-gray-600">담당 고객사: 0개</p>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>빠른 메뉴</CardTitle>
              <CardDescription>자주 사용하는 메뉴로 이동합니다.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-2">
              {user?.role !== 'viewer' ? (
                <>
                  <Button variant="outline" className="w-full justify-start">
                    내 보고서 작성
                  </Button>
                  <Button variant="outline" className="w-full justify-start">
                    담당 고객사 관리
                  </Button>
                </>
              ) : (
                <p className="text-sm text-muted-foreground">뷰어 권한은 작성 메뉴를 사용할 수 없습니다.</p>
              )}
              {user?.role === 'admin' && (
                <Button variant="outline" className="w-full justify-start" onClick={() => router.push('/admin')}>
                  관리자 페이지
                </Button>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
} 