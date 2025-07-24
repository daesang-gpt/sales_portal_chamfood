"use client"

import * as React from "react"
import { ChevronLeft, ChevronRight } from "lucide-react"
import { cn } from "@/lib/utils"
import { buttonVariants } from "@/components/ui/button"

export type CalendarProps = {
  value?: Date
  onChange?: (date: Date | null) => void
  className?: string
}

export function Calendar({ value, onChange, className }: CalendarProps) {
  const [currentDate, setCurrentDate] = React.useState(() => {
    if (value) {
      return new Date(value.getFullYear(), value.getMonth(), 1)
    }
    return new Date(new Date().getFullYear(), new Date().getMonth(), 1)
  })

  const [selectedDate, setSelectedDate] = React.useState<Date | null>(value ?? null)

  // 현재 월의 첫 번째 날과 마지막 날 계산
  const firstDayOfMonth = new Date(currentDate.getFullYear(), currentDate.getMonth(), 1)
  const lastDayOfMonth = new Date(currentDate.getFullYear(), currentDate.getMonth() + 1, 0)
  const startDate = new Date(firstDayOfMonth)
  startDate.setDate(startDate.getDate() - firstDayOfMonth.getDay())

  // 달력에 표시할 날짜들 생성
  const days: Date[] = []
  const current = new Date(startDate)
  for (let i = 0; i < 42; i++) {
    days.push(new Date(current))
    current.setDate(current.getDate() + 1)
  }

  // 이전 달로 이동
  const goToPreviousMonth = () => {
    setCurrentDate(new Date(currentDate.getFullYear(), currentDate.getMonth() - 1, 1))
  }

  // 다음 달로 이동
  const goToNextMonth = () => {
    setCurrentDate(new Date(currentDate.getFullYear(), currentDate.getMonth() + 1, 1))
  }

  // 날짜 선택
  const selectDate = (date: Date) => {
    setSelectedDate(date)
    if (onChange) onChange(date)
  }

  // 오늘 날짜 확인
  const isToday = (date: Date) => {
    const today = new Date()
    return date.getDate() === today.getDate() &&
           date.getMonth() === today.getMonth() &&
           date.getFullYear() === today.getFullYear()
  }

  // 선택된 날짜 확인
  const isSelected = (date: Date) => {
    if (!selectedDate) return false
    return date.getDate() === selectedDate.getDate() &&
           date.getMonth() === selectedDate.getMonth() &&
           date.getFullYear() === selectedDate.getFullYear()
  }

  // 현재 월의 날짜인지 확인
  const isCurrentMonth = (date: Date) => {
    return date.getMonth() === currentDate.getMonth()
  }

  // 요일 이름
  const dayNames = ['일', '월', '화', '수', '목', '금', '토']

  return (
    <div className={cn("p-3", className)}>
      <div className="flex justify-between items-center mb-2">
        <button
          type="button"
          onClick={goToPreviousMonth}
          className={buttonVariants({ variant: "outline" }) + " h-7 w-7 bg-transparent p-0 opacity-50 hover:opacity-100"}
        >
          <ChevronLeft className="h-4 w-4" />
        </button>
        <span className="text-sm font-medium">
          {currentDate.getFullYear()}년 {currentDate.getMonth() + 1}월
        </span>
        <button
          type="button"
          onClick={goToNextMonth}
          className={buttonVariants({ variant: "outline" }) + " h-7 w-7 bg-transparent p-0 opacity-50 hover:opacity-100"}
        >
          <ChevronRight className="h-4 w-4" />
        </button>
      </div>
      
      <div className="grid grid-cols-7 gap-1 mb-1">
        {dayNames.map((day) => (
          <div key={day} className="text-muted-foreground rounded-md w-9 font-normal text-[0.8rem] text-center">
            {day}
          </div>
        ))}
      </div>
      
      <div className="grid grid-cols-7 gap-1">
        {days.map((day, index) => (
          <button
            key={index}
            type="button"
            onClick={() => selectDate(day)}
            className={cn(
              buttonVariants({ variant: isSelected(day) ? "default" : "ghost" }),
              "h-9 w-9 p-0 font-normal text-sm text-center",
              isToday(day) && "bg-accent text-accent-foreground",
              isSelected(day) && "bg-primary text-primary-foreground hover:bg-primary hover:text-primary-foreground focus:bg-primary focus:text-primary-foreground",
              !isCurrentMonth(day) && "text-muted-foreground opacity-50"
            )}
          >
            {day.getDate()}
          </button>
        ))}
      </div>
    </div>
  )
}
