import { jwtDecode } from 'jwt-decode';

interface User {
  id: number;
  name: string;
  department: string;
  employee_number: string;
  role: string;
}

interface JWTPayload {
  user_id: number;
  exp: number;
  iat: number;
}

// JWT 토큰에서 사용자 정보 추출
export const getUserFromToken = (): User | null => {
  if (typeof window === 'undefined') return null;
  
  const userStr = localStorage.getItem('user');
  if (!userStr) return null;
  
  try {
    return JSON.parse(userStr);
  } catch {
    return null;
  }
};

// JWT 토큰 유효성 검사
export const isTokenValid = (): boolean => {
  if (typeof window === 'undefined') return false;
  
  const token = localStorage.getItem('access_token');
  if (!token) return false;
  
  try {
    const decoded = jwtDecode<JWTPayload>(token);
    const currentTime = Date.now() / 1000;
    
    return decoded.exp > currentTime;
  } catch {
    return false;
  }
};

// 사용자가 로그인되어 있는지 확인
export const isAuthenticated = (): boolean => {
  return isTokenValid() && getUserFromToken() !== null;
};

// 사용자 권한 확인
export const hasRole = (requiredRole: 'admin' | 'user'): boolean => {
  const user = getUserFromToken();
  if (!user) return false;
  
  if (requiredRole === 'admin') {
    return user.role === 'admin';
  }
  
  return true; // user 권한은 모든 사용자가 접근 가능
};

// 관리자 권한 확인
export const isAdmin = (): boolean => {
  return hasRole('admin');
};

// 로그아웃
export const logout = (): void => {
  if (typeof window === 'undefined') return;
  
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
  localStorage.removeItem('user');
  
  // 로그아웃 이벤트 발생 (Sidebar에서 감지)
  window.dispatchEvent(new Event('auth-change'));
};

// API 요청을 위한 인증 헤더 생성
export const getAuthHeaders = (): HeadersInit => {
  const token = localStorage.getItem('access_token');
  return {
    'Content-Type': 'application/json',
    ...(token && { Authorization: `Bearer ${token}` }),
  };
}; 