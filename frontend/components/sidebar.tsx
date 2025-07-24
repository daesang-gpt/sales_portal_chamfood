"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import { useEffect, useState } from "react"
import { cn } from "@/lib/utils"
import { Home, FileText, Building2, BarChart3, Users, Settings, Package } from "lucide-react"
import { getUserFromToken } from "@/lib/auth"

const navigation = [
  { name: "대시보드", href: "/", icon: Home },
  { name: "영업일지", href: "/sales-reports", icon: FileText },
  { name: "회사 관리", href: "/companies", icon: Building2 },
  { name: "업체 리스트", href: "/prospects", icon: Users },
  { name: "분석", href: "/analytics", icon: BarChart3 },
  { name: "설정", href: "/settings", icon: Settings },
]

export function Sidebar() {
  const pathname = usePathname()
  const [user, setUser] = useState<any>(null)
  const [isClient, setIsClient] = useState(false)

  useEffect(() => {
    setIsClient(true)
    const currentUser = getUserFromToken()
    setUser(currentUser)
  }, [])

  return (
    <div className="flex flex-col w-64 bg-white shadow-lg">
      <div className="flex items-center justify-center h-16 bg-blue-600">
        <div className="flex items-center space-x-2">
          <Package className="h-8 w-8 text-white" />
          <span className="text-xl font-bold text-white">축산물 영업포털</span>
        </div>
      </div>

      <nav className="flex-1 px-4 py-6 space-y-2">
        {navigation.map((item) => {
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
        <div className="flex items-center space-x-3">
          <div className="w-8 h-8 bg-gray-300 rounded-full flex items-center justify-center">
            <span className="text-sm font-medium">
              {isClient && user ? user.name.charAt(0) : "사"}
            </span>
          </div>
          <div>
            <p className="text-sm font-medium">
              {isClient && user ? user.name : "사용자"}
            </p>
            <p className="text-xs text-gray-500">
              {isClient && user ? user.department : "로그인 필요"}
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
