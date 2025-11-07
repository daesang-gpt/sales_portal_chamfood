"use client"

import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { SapCodeOption } from "@/lib/constants/sapCodes"

interface SapCodeSelectProps {
  options: SapCodeOption[]
  codeValue: string
  nameValue: string
  onCodeChange: (code: string) => void
  onNameChange: (name: string) => void
  codeLabel: string
  nameLabel: string
  codePlaceholder?: string
  namePlaceholder?: string
  showCodeField?: boolean
  disabled?: boolean
}

export function SapCodeSelect({
  options,
  codeValue,
  nameValue,
  onCodeChange,
  onNameChange,
  codeLabel,
  nameLabel,
  codePlaceholder = "코드가 자동으로 입력됩니다",
  namePlaceholder = "명칭을 선택하세요",
  showCodeField = false,
  disabled = false,
}: SapCodeSelectProps) {
  const handleNameChange = (selectedName: string) => {
    const selectedOption = options.find(opt => opt.name === selectedName)
    if (selectedOption) {
      onNameChange(selectedOption.name)
      onCodeChange(selectedOption.code)
    }
  }

  // 현재 선택된 값에 맞는 코드 찾기
  const currentValue = nameValue || (codeValue ? options.find(opt => opt.code === codeValue)?.name : undefined)

  return (
    <div className="space-y-2">
      {showCodeField && (
        <div>
          <Label className="text-sm font-semibold text-foreground">{codeLabel}</Label>
          <Input
            value={codeValue || ""}
            placeholder={codePlaceholder}
            readOnly
            className="bg-muted cursor-not-allowed"
          />
        </div>
      )}
      <div>
        <Label className="text-sm font-semibold text-foreground">{nameLabel}</Label>
        <Select
          value={currentValue || undefined}
          onValueChange={handleNameChange}
          disabled={disabled}
        >
          <SelectTrigger>
            <SelectValue placeholder={namePlaceholder} />
          </SelectTrigger>
          <SelectContent>
            {options.map((option) => (
              <SelectItem key={option.code} value={option.name}>
                {option.name}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>
    </div>
  )
}

