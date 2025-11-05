"use client"

import React, { useState, useEffect, useRef, useCallback } from "react"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { X, ChevronDown } from "lucide-react"
import { cn } from "@/lib/utils"

interface LocationSelectProps {
  value: string
  onChange: (value: string) => void
  placeholder?: string
  className?: string
  required?: boolean
  disabled?: boolean
}

const LOCATION_DATA: Record<string, string[]> = {
  "서울특별시": [
    "강남구", "강동구", "강북구", "강서구", "관악구", "광진구", "구로구", "금천구",
    "노원구", "도봉구", "동대문구", "동작구", "마포구", "서대문구", "서초구", "성동구",
    "성북구", "송파구", "양천구", "영등포구", "용산구", "은평구", "종로구", "중구", "중랑구"
  ],
  "부산광역시": [
    "강서구", "금정구", "남구", "동구", "동래구", "부산진구", "북구", "사상구", "사하구",
    "서구", "수영구", "연제구", "영도구", "중구", "해운대구", "기장군"
  ],
  "대구광역시": [
    "남구", "달서구", "동구", "북구", "서구", "수성구", "중구", "달성군", "군위군"
  ],
  "인천광역시": [
    "강화군", "계양구", "미추홀구", "남동구", "동구", "부평구", "서구", "연수구", "중구", "옹진군"
  ],
  "광주광역시": ["광산구", "남구", "동구", "북구", "서구"],
  "대전광역시": ["대덕구", "동구", "서구", "유성구", "중구"],
  "울산광역시": ["남구", "동구", "북구", "중구", "울주군"],
  "세종특별자치시": [],
  "경기도": [
    "수원시 장안구", "수원시 권선구", "수원시 팔달구", "수원시 영통구",
    "고양특례시 덕양구", "고양특례시 일산동구", "고양특례시 일산서구",
    "용인특례시 처인구", "용인특례시 기흥구", "용인특례시 수지구",
    "성남시 수정구", "성남시 중원구", "성남시 분당구",
    "안산시 상록구", "안산시 단원구", "안양시 만안구", "안양시 동안구",
    "부천시", "광명시", "평택시", "의정부시", "동두천시", "구리시", "남양주시",
    "오산시", "시흥시", "군포시", "의왕시", "하남시", "이천시", "안성시", "김포시",
    "화성시", "광주시", "양주시", "포천시", "여주시", "연천군", "가평군", "양평군"
  ],
  "강원특별자치도": [
    "춘천시", "원주시", "강릉시", "동해시", "태백시", "속초시", "삼척시",
    "홍천군", "횡성군", "영월군", "평창군", "정선군", "철원군", "화천군",
    "양구군", "인제군", "고성군", "양양군"
  ],
  "충청북도": [
    "청주시 상당구", "청주시 서원구", "청주시 흥덕구", "청주시 청원구",
    "충주시", "제천시", "보은군", "옥천군", "영동군", "진천군", "괴산군", "음성군", "단양군"
  ],
  "충청남도": [
    "천안시 동남구", "천안시 서북구", "공주시", "보령시", "아산시", "서산시", "논산시", "계룡시", "당진시",
    "금산군", "부여군", "서천군", "청양군", "홍성군", "예산군", "태안군"
  ],
  "전북특별자치도": [
    "전주시 완산구", "전주시 덕진구", "익산시", "군산시", "정읍시", "남원시", "김제시",
    "완주군", "진안군", "무주군", "장수군", "임실군", "순창군", "고창군", "부안군"
  ],
  "전라남도": [
    "목포시", "여수시", "순천시", "나주시", "광양시",
    "담양군", "곡성군", "구례군", "고흥군", "보성군", "화순군", "장흥군", "강진군", "해남군",
    "영암군", "무안군", "함평군", "영광군", "장성군", "완도군", "진도군", "신안군"
  ],
  "경상북도": [
    "포항시 남구", "포항시 북구", "경주시", "김천시", "안동시", "구미시", "영주시", "영천시", "상주시", "문경시",
    "예천군", "경산시", "의성군", "청송군", "영양군", "영덕군", "청도군", "고령군", "성주군", "칠곡군", "울진군", "울릉군"
  ],
  "경상남도": [
    "창원특례시 의창구", "창원특례시 성산구", "창원특례시 마산합포구", "창원특례시 마산회원구", "창원특례시 진해구",
    "진주시", "통영시", "사천시", "김해시", "밀양시", "거제시", "양산시",
    "의령군", "함안군", "창녕군", "고성군", "남해군", "하동군", "산청군", "함양군", "거창군", "합천군"
  ],
  "제주특별자치도": ["제주시", "서귀포시"]
}

// 모든 지역 옵션 생성 (시/도 + 구/군 조합)
const generateLocationOptions = (): string[] => {
  const options: string[] = []
  
  Object.keys(LOCATION_DATA).forEach(city => {
    const districts = LOCATION_DATA[city]
    if (districts.length === 0) {
      // 세종특별자치시처럼 구/군이 없는 경우
      options.push(city)
    } else {
      districts.forEach(district => {
        options.push(`${city} ${district}`)
      })
    }
  })
  
  return options.sort((a, b) => a.localeCompare(b, 'ko'))
}

const LOCATION_OPTIONS = generateLocationOptions()

export function LocationSelect({
  value,
  onChange,
  placeholder = "지역을 선택하세요",
  className,
  required = false,
  disabled = false
}: LocationSelectProps) {
  const [filteredOptions, setFilteredOptions] = useState<string[]>(LOCATION_OPTIONS)
  const [isOpen, setIsOpen] = useState(false)
  const [inputValue, setInputValue] = useState(value)
  const [selectedIndex, setSelectedIndex] = useState(-1)
  const inputRef = useRef<HTMLInputElement>(null)
  const suggestionsRef = useRef<HTMLDivElement>(null)

  // value prop 변경 시 inputValue 동기화
  useEffect(() => {
    setInputValue(value)
  }, [value])

  // 검색 필터링 함수
  const filterOptions = useCallback((query: string) => {
    if (!query.trim()) {
      setFilteredOptions(LOCATION_OPTIONS)
      return
    }

    const queryLower = query.toLowerCase().trim()
    const filtered = LOCATION_OPTIONS.filter(location => 
      location.toLowerCase().includes(queryLower)
    )
    setFilteredOptions(filtered)
    setSelectedIndex(-1)
  }, [])

  // 입력값 변경 처리
  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newValue = e.target.value
    setInputValue(newValue)
    filterOptions(newValue)
    setIsOpen(true)
    
    // 값이 변경되면 onChange 호출 (부분 입력도 허용)
    onChange(newValue)
  }

  // 지역 선택 처리
  const handleSelectLocation = (location: string) => {
    setInputValue(location)
    setFilteredOptions(LOCATION_OPTIONS)
    setIsOpen(false)
    setSelectedIndex(-1)
    onChange(location)
    inputRef.current?.blur()
  }

  // 선택 해제 처리
  const handleClearSelection = () => {
    setInputValue("")
    setFilteredOptions(LOCATION_OPTIONS)
    setIsOpen(false)
    setSelectedIndex(-1)
    onChange("")
    inputRef.current?.focus()
  }

  // 키보드 네비게이션
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (!isOpen && e.key !== 'Enter' && e.key !== 'Escape') {
      setIsOpen(true)
      return
    }

    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault()
        setSelectedIndex(prev => 
          prev < filteredOptions.length - 1 ? prev + 1 : prev
        )
        break
      case 'ArrowUp':
        e.preventDefault()
        setSelectedIndex(prev => prev > 0 ? prev - 1 : -1)
        break
      case 'Enter':
        e.preventDefault()
        if (selectedIndex >= 0 && filteredOptions[selectedIndex]) {
          handleSelectLocation(filteredOptions[selectedIndex])
        } else if (filteredOptions.length === 1) {
          // 정확히 하나만 매칭되면 자동 선택
          handleSelectLocation(filteredOptions[0])
        }
        break
      case 'Escape':
        setIsOpen(false)
        setSelectedIndex(-1)
        inputRef.current?.blur()
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
        // 선택된 값이 있으면 그대로 유지, 없으면 빈 문자열로
        if (!value || !LOCATION_OPTIONS.includes(value)) {
          setInputValue(value || "")
        }
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [value])

  return (
    <div className="relative">
      <div className="relative">
        <Input
          ref={inputRef}
          value={inputValue}
          onChange={handleInputChange}
          onKeyDown={handleKeyDown}
          onFocus={() => {
            setIsOpen(true)
            filterOptions(inputValue)
          }}
          placeholder={placeholder}
          className={cn("pr-10", className)}
          disabled={disabled}
          required={required}
        />
        
        {/* 우측 아이콘들 */}
        <div className="absolute right-2 top-1/2 transform -translate-y-1/2 flex items-center space-x-1">
          {value && !disabled && (
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
          
          {!value && !disabled && (
            <ChevronDown className="h-4 w-4 text-muted-foreground" />
          )}
        </div>
      </div>

      {/* 자동완성 드롭다운 */}
      {isOpen && !disabled && (
        <div
          ref={suggestionsRef}
          className="absolute z-50 w-full mt-1 bg-white border border-gray-200 rounded-md shadow-lg max-h-[300px] overflow-y-auto"
        >
          {filteredOptions.length === 0 ? (
            <div className="px-3 py-2 text-sm text-gray-500">
              검색 결과가 없습니다.
            </div>
          ) : (
            filteredOptions.map((location, index) => (
              <button
                key={location}
                type="button"
                className={cn(
                  "w-full px-3 py-2 text-left hover:bg-gray-100 focus:bg-gray-100 focus:outline-none",
                  index === selectedIndex && "bg-gray-100",
                  value === location && "bg-blue-50 font-medium"
                )}
                onClick={() => handleSelectLocation(location)}
              >
                <div>{location}</div>
              </button>
            ))
          )}
        </div>
      )}
    </div>
  )
}

