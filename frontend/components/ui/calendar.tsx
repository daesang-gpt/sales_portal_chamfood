"use client"

import * as React from "react"
import { useDatePicker } from "@rehookify/datepicker"
import { ChevronLeft, ChevronRight } from "lucide-react"
import { cn } from "@/lib/utils"
import { buttonVariants } from "@/components/ui/button"

export type CalendarProps = {
  value?: Date
  onChange?: (date: Date | null) => void
  className?: string
}

export function Calendar({ value, onChange, className }: CalendarProps) {
  const [selected, setSelected] = React.useState<Date | null>(value ?? null)

  const datePicker = useDatePicker({
    selectedDates: selected ? [selected] : [],
    onDatesChange: (dates: Date[]) => {
      const date = dates[0] ?? null
      setSelected(date)
      if (onChange) onChange(date)
    },
    calendar: {
      mode: "single",
      weekStart: 0,
    },
  })

  const calendar = datePicker.data.calendars[0]

  return (
    <div {...datePicker.propGetters.getContainerProps()} className={cn("p-3", className)}>
      <div className="flex justify-between items-center mb-2">
        <button
          type="button"
          {...datePicker.propGetters.getPrevMonthButtonProps()}
          className={buttonVariants({ variant: "outline" }) + " h-7 w-7 bg-transparent p-0 opacity-50 hover:opacity-100"}
        >
          <ChevronLeft className="h-4 w-4" />
        </button>
        <span className="text-sm font-medium">
          {calendar.month} {calendar.year}
        </span>
        <button
          type="button"
          {...datePicker.propGetters.getNextMonthButtonProps()}
          className={buttonVariants({ variant: "outline" }) + " h-7 w-7 bg-transparent p-0 opacity-50 hover:opacity-100"}
        >
          <ChevronRight className="h-4 w-4" />
        </button>
      </div>
      <div className="grid grid-cols-7 gap-1 mb-1">
        {calendar.daysOfWeek.map((day: any) => (
          <div key={day.full} className="text-muted-foreground rounded-md w-9 font-normal text-[0.8rem] text-center">
            {day.narrow}
          </div>
        ))}
      </div>
      <div className="flex flex-col space-y-1">
        {calendar.weeks.map((week: any[], i: number) => (
          <div key={i} className="flex w-full mt-2">
            {week.map((day: any) => (
              <button
                key={day.date}
                type="button"
                {...datePicker.propGetters.getDayProps(day)}
                className={cn(
                  buttonVariants({ variant: day.selected ? "default" : "ghost" }),
                  "h-9 w-9 p-0 font-normal text-sm text-center",
                  day.today && "bg-accent text-accent-foreground",
                  day.selected && "bg-primary text-primary-foreground hover:bg-primary hover:text-primary-foreground focus:bg-primary focus:text-primary-foreground",
                  day.disabled && "text-muted-foreground opacity-50",
                  day.blocked && "text-muted-foreground opacity-50",
                  !day.inMonth && "text-muted-foreground bg-accent/50"
                )}
                disabled={day.disabled || day.blocked}
              >
                {day.display}
              </button>
            ))}
          </div>
        ))}
      </div>
    </div>
  )
}
