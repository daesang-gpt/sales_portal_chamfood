"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import { useEffect, useState } from "react"
import { cn } from "@/lib/utils"
import { Home, FileText, Building2, BarChart3, Users, Settings, Package, LogIn, LogOut, Database, FileSearch } from "lucide-react"
import { getUserFromToken, isAdmin, isAuthenticated, logout } from "@/lib/auth"

interface NavigationItem {
  name: string
  href: string
  icon: any
  adminOnly?: boolean
}

const navigation: NavigationItem[] = [
  { name: "대시보드", href: "/", icon: Home },
  { name: "영업일지", href: "/sales-reports", icon: FileText },
  { name: "회사 관리", href: "/companies", icon: Building2 },
  { name: "업체 리스트", href: "/prospects", icon: Users },
  { name: "분석", href: "/analytics", icon: BarChart3, adminOnly: true },
  { name: "설정", href: "/settings", icon: Settings, adminOnly: true },
]

export function Sidebar() {
  const pathname = usePathname()
  const [user, setUser] = useState<any>(null)
  const [isClient, setIsClient] = useState(false)
  const [isLoggedIn, setIsLoggedIn] = useState(false)
  const [isAdminUser, setIsAdminUser] = useState(false)

  // 사용자 정보 업데이트 함수
  const updateUserInfo = () => {
    const currentUser = getUserFromToken()
    const loggedIn = isAuthenticated()
    const adminUser = isAdmin()
    setUser(currentUser)
    setIsLoggedIn(loggedIn)
    setIsAdminUser(adminUser)
  }

  useEffect(() => {
    setIsClient(true)
    updateUserInfo()
  }, [])

  // pathname 변경 시 사용자 정보 업데이트
  useEffect(() => {
    if (isClient) {
      updateUserInfo()
    }
  }, [pathname, isClient])

  // localStorage 변경 감지 (다른 탭에서 로그인/로그아웃 시)
  useEffect(() => {
    if (!isClient) return

    const handleStorageChange = (e: StorageEvent) => {
      if (e.key === 'access_token' || e.key === 'user' || e.key === 'refresh_token') {
        updateUserInfo()
      }
    }

    // 커스텀 이벤트 리스너 (같은 탭에서 로그인 시)
    const handleAuthChange = () => {
      updateUserInfo()
    }

    window.addEventListener('storage', handleStorageChange)
    window.addEventListener('auth-change', handleAuthChange)

    return () => {
      window.removeEventListener('storage', handleStorageChange)
      window.removeEventListener('auth-change', handleAuthChange)
    }
  }, [isClient])

  const handleLogout = async () => {
    await logout()
    setUser(null)
    setIsLoggedIn(false)
    if (typeof window !== 'undefined') {
      window.location.href = '/login'
    }
  }

  return (
    <div className="flex flex-col w-64 bg-white shadow-lg">
      <div className="flex items-center justify-center h-16 bg-blue-600">
        <div className="flex items-center space-x-2">
          <Package className="h-8 w-8 text-white" />
          <span className="text-xl font-bold text-white">참푸드 영업포털</span>
        </div>
      </div>

      <nav className="flex-1 px-4 py-6 space-y-2">
        {navigation.map((item) => {
          // 관리자 전용 메뉴인 경우 관리자 권한 확인
          if (item.adminOnly && !isAdminUser) {
            return null
          }
          
          const isActive = pathname === item.href || (item.href !== "/" && pathname.startsWith(item.href))
          return (
            <Link
              key={item.name}
              href={item.href}
              className={cn(
                "flex items-center px-4 py-3 text-sm font-medium rounded-lg transition-colors",
                isActive ? "bg-blue-100 text-blue-700" : "text-gray-600 hover:bg-gray-100 hover:text-gray-900",
              )}
            >
              <item.icon className="mr-3 h-5 w-5" />
              {item.name}
            </Link>
          )
        })}
      </nav>

       <div className="p-4 border-t">
         {isClient && isLoggedIn && user ? (
           <div className="space-y-3">
             <div className="flex items-center justify-between">
               <div className="flex items-center space-x-3">
                 <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
                   <span className="text-sm font-medium text-blue-600">
                     {user.name.charAt(0)}
                   </span>
                 </div>
                 <div>
                   <p className="text-sm font-medium text-gray-900">
                     {user.name}
                   </p>
                   <p className="text-xs text-gray-500">
                     {user.department}
                   </p>
                 </div>
               </div>
               <button
                 onClick={handleLogout}
                 className="p-2 text-gray-400 hover:text-gray-600 transition-colors"
                 title="로그아웃"
               >
                 <LogOut className="h-4 w-4" />
               </button>
             </div>
             
             {/* 관리자 전용 데이터베이스 아이콘 */}
             {isAdminUser && (
               <div className="flex items-center justify-center">
                 <button
                  onClick={() => {
                    if (typeof window !== 'undefined') {
                      window.open('/manage', '_blank')
                    }
                  }}
                   className="flex items-center space-x-2 px-3 py-2 text-xs text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors"
                   title="데이터베이스 관리"
                 >
                   <Database className="h-4 w-4" />
                   <span>데이터 관리</span>
                 </button>
               </div>
             )}
           </div>
         ) : (
           <div className="flex items-center space-x-3">
             <div className="w-8 h-8 bg-gray-200 rounded-full flex items-center justify-center">
               <LogIn className="h-4 w-4 text-gray-400" />
             </div>
             <div className="flex-1">
               <p className="text-sm font-medium text-gray-500">
                 로그인이 필요합니다
               </p>
               <Link 
                 href="/login" 
                 className="text-xs text-blue-600 hover:text-blue-800 transition-colors"
               >
                 로그인하기
               </Link>
             </div>
           </div>
         )}
       </div>
    </div>
  )
}
