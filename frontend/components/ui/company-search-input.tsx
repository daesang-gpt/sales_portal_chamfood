"use client"

import React, { useState, useEffect, useRef, useCallback } from "react"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { X, ChevronDown, Loader2 } from "lucide-react"
import { companyApi } from "@/lib/api"
import { cn } from "@/lib/utils"

interface CompanySuggestion {
  id: string  // company_code (문자열)
  name: string
}

interface CompanySearchInputProps {
  value: string
  selectedCompanyId?: string  // company_code (문자열)
  onChange: (value: string, companyId?: string) => void
  placeholder?: string
  className?: string
  disabled?: boolean
}

export function CompanySearchInput({
  value,
  selectedCompanyId,
  onChange,
  placeholder = "회사명을 입력하세요",
  className,
  disabled = false
}: CompanySearchInputProps) {
  const [suggestions, setSuggestions] = useState<CompanySuggestion[]>([])
  const [isOpen, setIsOpen] = useState(false)
  const [loading, setLoading] = useState(false)
  const [inputValue, setInputValue] = useState(value)
  const [selectedIndex, setSelectedIndex] = useState(-1)
  const inputRef = useRef<HTMLInputElement>(null)
  const suggestionsRef = useRef<HTMLDivElement>(null)
  const debounceTimeoutRef = useRef<NodeJS.Timeout | null>(null)

  // value prop 변경 시 inputValue 동기화
  useEffect(() => {
    setInputValue(value)
  }, [value])

  // 디바운스된 검색 함수
  const searchCompanies = useCallback(async (query: string) => {
    if (!query.trim() || query.length < 1) {
      setSuggestions([])
      setIsOpen(false)
      return
    }

    try {
      setLoading(true)
      const results = await companyApi.suggestCompanies(query)
      setSuggestions(results)
      setIsOpen(results.length > 0)
      setSelectedIndex(-1)
    } catch (error) {
      console.error('회사 검색 오류:', error)
      setSuggestions([])
      setIsOpen(false)
    } finally {
      setLoading(false)
    }
  }, [])

  // 입력값 변경 처리
  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newValue = e.target.value
    setInputValue(newValue)
    
    // 디바운스 처리 (300ms)
    if (debounceTimeoutRef.current) {
      clearTimeout(debounceTimeoutRef.current)
    }
    
    debounceTimeoutRef.current = setTimeout(() => {
      searchCompanies(newValue)
    }, 300)

    // 선택된 회사가 있으면 초기화
    if (selectedCompanyId) {
      onChange(newValue, undefined)
    } else {
      onChange(newValue)
    }
  }

  // 회사 선택 처리
  const handleSelectCompany = (company: CompanySuggestion) => {
    setInputValue(company.name)
    setSuggestions([])
    setIsOpen(false)
    setSelectedIndex(-1)
    onChange(company.name, company.id)
  }

  // 선택 해제 처리
  const handleClearSelection = () => {
    setInputValue("")
    setSuggestions([])
    setIsOpen(false)
    setSelectedIndex(-1)
    onChange("", undefined)
    inputRef.current?.focus()
  }

  // 키보드 네비게이션
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (!isOpen) return

    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault()
        setSelectedIndex(prev => 
          prev < suggestions.length - 1 ? prev + 1 : prev
        )
        break
      case 'ArrowUp':
        e.preventDefault()
        setSelectedIndex(prev => prev > 0 ? prev - 1 : -1)
        break
      case 'Enter':
        e.preventDefault()
        if (selectedIndex >= 0 && suggestions[selectedIndex]) {
          handleSelectCompany(suggestions[selectedIndex])
        }
        break
      case 'Escape':
        setIsOpen(false)
        setSelectedIndex(-1)
        break
    }
  }

  // 외부 클릭 시 드롭다운 닫기
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        suggestionsRef.current &&
        !suggestionsRef.current.contains(event.target as Node) &&
        inputRef.current &&
        !inputRef.current.contains(event.target as Node)
      ) {
        setIsOpen(false)
        setSelectedIndex(-1)
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [suggestionsRef, inputRef])

  // 컴포넌트 언마운트 시 타이머 정리
  useEffect(() => {
    return () => {
      if (debounceTimeoutRef.current) {
        clearTimeout(debounceTimeoutRef.current)
      }
    }
  }, [debounceTimeoutRef])

  return (
    <div className="relative">
      <div className="relative">
        <Input
          ref={inputRef}
          value={inputValue}
          onChange={handleInputChange}
          onKeyDown={handleKeyDown}
          onFocus={() => {
            if (suggestions.length > 0) {
              setIsOpen(true)
            }
          }}
          placeholder={placeholder}
          className={cn("pr-10", className)}
          disabled={disabled}
        />
        
        {/* 우측 아이콘들 */}
        <div className="absolute right-2 top-1/2 transform -translate-y-1/2 flex items-center space-x-1">
          {loading && (
            <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />
          )}
          
          {selectedCompanyId && (
            <Button
              type="button"
              variant="ghost"
              size="sm"
              className="h-6 w-6 p-0 hover:bg-muted"
              onClick={handleClearSelection}
              disabled={disabled}
            >
              <X className="h-3 w-3" />
            </Button>
          )}
          
          {!selectedCompanyId && !loading && (
            <ChevronDown className="h-4 w-4 text-muted-foreground" />
          )}
        </div>
      </div>

      {/* 자동완성 드롭다운 */}
      {isOpen && (
        <div
          ref={suggestionsRef}
          className="absolute z-50 w-full mt-1 bg-white border border-gray-200 rounded-md shadow-lg max-h-60 overflow-y-auto"
        >
          {suggestions.map((company, index) => (
            <button
              key={company.id}
              type="button"
              className={cn(
                "w-full px-3 py-2 text-left hover:bg-gray-100 focus:bg-gray-100 focus:outline-none",
                index === selectedIndex && "bg-gray-100"
              )}
              onClick={() => handleSelectCompany(company)}
            >
              <div className="font-medium">{company.name}</div>
            </button>
          ))}
          
          {suggestions.length === 0 && !loading && inputValue.trim() && (
            <div className="px-3 py-2 text-sm text-gray-500">
              검색 결과가 없습니다.
            </div>
          )}
        </div>
      )}
    </div>
  )
} 