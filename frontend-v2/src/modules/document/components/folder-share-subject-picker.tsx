import { Search } from 'lucide-react'
import { useMemo, useState } from 'react'

import { useCompanies } from '@/modules/hr/hooks/use-companies'
import { useDepartments } from '@/modules/hr/hooks/use-departments'
import { useEmployees } from '@/modules/hr/hooks/use-employees'
import { useRoles } from '@/modules/hr/hooks/use-roles'
import { Badge } from '@/shared/ui/badge'
import { Checkbox } from '@/shared/ui/checkbox'
import { Input } from '@/shared/ui/input'
import { Popover, PopoverContent, PopoverTrigger } from '@/shared/ui/popover'
import { cn } from '@/shared/utils/cn'
import { stripDiacritics } from '@/shared/utils/vn-text'
import { SubjectChips } from './access-subject-chips'
import { SUBJECT_KIND, SUBJECT_KIND_LABELS } from '../types/document-access'

export interface MixedSubject {
  subject_kind: number
  subject_id: number
}

interface MixedOption extends MixedSubject {
  key: string
  label: string
  kindLabel: string
}

interface FolderShareSubjectPickerProps {
  value: MixedSubject[]
  onChange: (value: MixedSubject[]) => void
}

/** Thứ tự nút lọc — cùng thứ tự xếp danh sách (pháp nhân/phòng ban trước, người sau). */
const KIND_FILTER_ORDER = [
  SUBJECT_KIND.company,
  SUBJECT_KIND.department,
  SUBJECT_KIND.role,
  SUBJECT_KIND.employee,
] as const

function keyOf(s: MixedSubject) {
  return `${s.subject_kind}-${s.subject_id}`
}

/**
 * Ô CHỌN NHIỀU trộn đủ BỐN loại đối tượng cùng một danh sách (đặc tả §C) —
 * khác `SubjectMultiSelect` của `document-access-dialog.tsx` (chọn LOẠI trước
 * rồi mới chọn trong loại đó): ở đây gõ một từ khóa là khớp CẢ BỐN danh mục
 * cùng lúc, đúng cảm giác hộp «Chia sẻ» của Drive — chọn quyền thư mục cho cả
 * một nhóm hỗn hợp người/phòng/pháp nhân/vai trò không cần đổi tab.
 *
 * Không dùng `cmdk` (repo tránh thêm phụ thuộc chỉ để có ô tìm, xem
 * `shared/ui/search-select.tsx`) — dựng trên `Popover + Input`, lọc bằng
 * `stripDiacritics` để gõ không dấu vẫn khớp.
 */
export function FolderShareSubjectPicker({ value, onChange }: FolderShareSubjectPickerProps) {
  const [open, setOpen] = useState(false)
  const [keyword, setKeyword] = useState('')
  const [kindFilter, setKindFilter] = useState<number | null>(null)

  const { data: employees } = useEmployees({ page_size: 1000, is_active: true })
  const { data: departments } = useDepartments({ page_size: 500 })
  const { data: companies } = useCompanies({ page_size: 200, is_active: true })
  const { data: roles } = useRoles()

  const allOptions = useMemo<MixedOption[]>(() => {
    const companyNames = new Map(
      (companies?.items ?? []).map((c) => [c.id, c.short_name || c.name] as const),
    )
    const fromEmployees = (employees?.items ?? []).map((e) => ({
      subject_kind: SUBJECT_KIND.employee,
      subject_id: e.id,
      label: e.full_name,
    }))
    const fromDepartments = (departments?.items ?? [])
      .filter((d) => d.is_active)
      //  Kèm tên pháp nhân: nhiều công ty có phòng TRÙNG TÊN («Kế toán»…),
      //  không kèm thì chọn nhầm phòng của công ty khác mà không biết.
      .map((d) => {
        const company = companyNames.get(d.company_id)
        return {
          subject_kind: SUBJECT_KIND.department,
          subject_id: d.id,
          label: company ? `${d.name} · ${company}` : d.name,
        }
      })
    const fromCompanies = (companies?.items ?? []).map((c) => ({
      subject_kind: SUBJECT_KIND.company,
      subject_id: c.id,
      label: c.short_name || c.name,
    }))
    const fromRoles = (roles ?? []).map((r) => ({
      subject_kind: SUBJECT_KIND.role,
      subject_id: r.id,
      label: r.name,
    }))
    //  Pháp nhân · phòng ban · vai trò LÊN TRƯỚC, người xuống cuối (phản hồi
    //  24/09/2026: 272 dòng người đứng đầu vùi mất 18 phòng ban + 14 pháp nhân,
    //  người dùng tưởng chỉ chia sẻ được cho từng người).
    return [...fromCompanies, ...fromDepartments, ...fromRoles, ...fromEmployees].map((option) => ({
      ...option,
      key: keyOf(option),
      kindLabel: SUBJECT_KIND_LABELS[option.subject_kind],
    }))
  }, [employees, departments, companies, roles])

  const selectedKeys = useMemo(() => new Set(value.map(keyOf)), [value])
  const selectedOptions = allOptions.filter((option) => selectedKeys.has(option.key))

  const keywordMatches = useMemo(() => {
    const needle = stripDiacritics(keyword.trim().toLowerCase())
    if (!needle) return allOptions
    return allOptions.filter((option) =>
      stripDiacritics(option.label.toLowerCase()).includes(needle),
    )
  }, [allOptions, keyword])
  const matches =
    kindFilter == null
      ? keywordMatches
      : keywordMatches.filter((option) => option.subject_kind === kindFilter)
  const countByKind = (kind: number) =>
    keywordMatches.filter((option) => option.subject_kind === kind).length

  function toggle(option: MixedOption) {
    if (selectedKeys.has(option.key)) {
      onChange(value.filter((item) => keyOf(item) !== option.key))
    } else {
      onChange([...value, { subject_kind: option.subject_kind, subject_id: option.subject_id }])
    }
  }

  return (
    <div className="space-y-2">
      <Popover open={open} onOpenChange={setOpen}>
        <PopoverTrigger asChild>
          <button
            type="button"
            className="flex h-9 w-full items-center gap-2 rounded-md border bg-transparent px-3 text-sm text-muted-foreground shadow-xs focus-visible:ring-[3px] focus-visible:ring-ring/50 focus-visible:outline-none"
          >
            <Search className="size-4 shrink-0" />
            Thêm người · phòng ban · pháp nhân · vai trò…
          </button>
        </PopoverTrigger>

        <PopoverContent align="start" className="w-(--radix-popover-trigger-width) min-w-80 p-0">
          <div className="relative border-b">
            <Search className="absolute top-1/2 left-2.5 size-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              autoFocus
              value={keyword}
              onChange={(event) => setKeyword(event.target.value)}
              placeholder="Gõ để tìm…"
              className="border-0 pl-8 shadow-none focus-visible:ring-0"
            />
          </div>

          {/*  Lọc theo LOẠI đối tượng — số đếm đi theo từ khóa đang gõ. */}
          <div
            role="group"
            aria-label="Lọc theo loại"
            className="flex flex-wrap gap-1 border-b p-1.5"
          >
            {[null, ...KIND_FILTER_ORDER].map((kind) => {
              const active = kindFilter === kind
              const count = kind == null ? keywordMatches.length : countByKind(kind)
              return (
                <button
                  key={kind ?? 'all'}
                  type="button"
                  aria-pressed={active}
                  onClick={() => setKindFilter(kind)}
                  className={cn(
                    'rounded-full border px-2 py-0.5 text-xs text-muted-foreground hover:bg-accent',
                    active && 'border-primary bg-accent font-medium text-foreground',
                  )}
                >
                  {kind == null ? 'Tất cả' : SUBJECT_KIND_LABELS[kind]} ({count})
                </button>
              )
            })}
          </div>

          <ul role="listbox" aria-multiselectable="true" className="max-h-64 overflow-y-auto p-1">
            {matches.length === 0 ? (
              <li className="px-2 py-6 text-center text-xs text-muted-foreground">
                Không có ai khớp.
              </li>
            ) : (
              matches.map((option) => {
                const checked = selectedKeys.has(option.key)
                return (
                  //  ⚠️ Dòng KHÔNG được là `<button>` bọc `Checkbox` — `Checkbox`
                  //  (Radix) tự render thành `<button role="checkbox">`, lồng
                  //  button-trong-button là HTML không hợp lệ (React cảnh báo
                  //  "cannot contain a nested <button>", lead bắt 23/09/2026).
                  //  Dùng `div role="option"` bấm được bằng chuột LẪN bàn phím
                  //  (Enter/Space), `Checkbox` chỉ còn là hình minh họa
                  //  (`tabIndex={-1}` + `pointer-events-none`, gỡ khỏi lượt Tab).
                  <li key={option.key} role="presentation">
                    <div
                      role="option"
                      aria-selected={checked}
                      tabIndex={0}
                      onClick={() => toggle(option)}
                      onKeyDown={(event) => {
                        if (event.key === 'Enter' || event.key === ' ') {
                          event.preventDefault()
                          toggle(option)
                        }
                      }}
                      className="flex w-full cursor-pointer items-center gap-2.5 rounded-sm px-2 py-1.5 text-sm hover:bg-accent focus-visible:bg-accent focus-visible:outline-none data-[checked=true]:bg-accent/60"
                      data-checked={checked}
                    >
                      <Checkbox checked={checked} tabIndex={-1} className="pointer-events-none" />
                      <span className="min-w-0 flex-1 truncate">{option.label}</span>
                      <Badge variant="outline" className="shrink-0 font-normal">
                        {option.kindLabel}
                      </Badge>
                    </div>
                  </li>
                )
              })
            )}
          </ul>
        </PopoverContent>
      </Popover>

      {selectedOptions.length > 0 && (
        <SubjectChips
          items={selectedOptions.map((option) => ({
            key: option.key,
            label: `${option.label} · ${option.kindLabel}`,
          }))}
          onRemove={(key) => onChange(value.filter((item) => keyOf(item) !== key))}
        />
      )}
    </div>
  )
}
