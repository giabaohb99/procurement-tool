import { Search } from 'lucide-react'

import { Input } from '@/shared/ui/input'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/shared/ui/select'
import type { LookupOption } from '@/shared/types/api'

/** `0` = «mọi …» — cùng quy ước với tham số backend. */
export const ALL_OPTION = '0'

interface WorkRosterFilterBarProps {
  /** `null` = người xem không đọc được danh mục này → ẩn ô lọc (không gọi API, không 403). */
  companies: LookupOption[] | null
  departments: LookupOption[] | null
  companyId: number
  departmentId: number
  onCompanyChange: (id: number) => void
  onDepartmentChange: (id: number) => void
  search: string
  onSearchChange: (value: string) => void
}

/** Backend chặn `q` quá 100 ký tự → chặn ngay ở ô nhập thay vì để người dùng ăn 422. */
export const ROSTER_SEARCH_MAX_LENGTH = 100

function IdSelect({
  label,
  allLabel,
  options,
  value,
  onChange,
}: {
  label: string
  allLabel: string
  options: LookupOption[]
  value: number
  onChange: (id: number) => void
}) {
  return (
    <Select value={String(value)} onValueChange={(v) => onChange(Number(v))}>
      <SelectTrigger size="sm" className="w-full sm:w-52" aria-label={label}>
        <SelectValue />
      </SelectTrigger>
      <SelectContent>
        <SelectItem value={ALL_OPTION}>{allLabel}</SelectItem>
        {options.map((o) => (
          <SelectItem key={o.id} value={String(o.id)}>
            {o.name}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  )
}

export function WorkRosterFilterBar({
  companies,
  departments,
  companyId,
  departmentId,
  onCompanyChange,
  onDepartmentChange,
  search,
  onSearchChange,
}: WorkRosterFilterBarProps) {
  return (
    <div className="flex flex-col gap-2 sm:flex-row sm:flex-wrap sm:items-center">
      {companies && (
        <IdSelect
          label="Lọc theo pháp nhân"
          allLabel="Tất cả pháp nhân"
          options={companies}
          value={companyId}
          onChange={onCompanyChange}
        />
      )}
      {departments && (
        <IdSelect
          label="Lọc theo phòng ban"
          allLabel="Tất cả phòng ban"
          options={departments}
          value={departmentId}
          onChange={onDepartmentChange}
        />
      )}
      <div className="relative sm:w-64">
        <Search aria-hidden className="pointer-events-none absolute top-1/2 left-2.5 size-4 -translate-y-1/2 text-muted-foreground" />
        <Input
          type="search"
          value={search}
          maxLength={ROSTER_SEARCH_MAX_LENGTH}
          onChange={(e) => onSearchChange(e.target.value)}
          placeholder="Tìm theo mã hoặc tên"
          aria-label="Tìm nhân sự theo mã hoặc tên"
          className="h-8 pl-8"
        />
      </div>
    </div>
  )
}
