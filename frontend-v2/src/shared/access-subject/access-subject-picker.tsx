import { Search } from 'lucide-react'
import { useMemo, useState } from 'react'

import { Badge } from '@/shared/ui/badge'
import { Checkbox } from '@/shared/ui/checkbox'
import { Input } from '@/shared/ui/input'
import { Popover, PopoverContent, PopoverTrigger } from '@/shared/ui/popover'
import { cn } from '@/shared/utils/cn'
import { SubjectChips } from './access-subject-chips'
import {
  KIND_FILTER_ORDER,
  filterOptionsByKeyword,
  keyOfSubject,
  toPickerOptions,
} from './access-subject-picker-options'
import { SUBJECT_KIND_LABELS } from './subject-kind'
import type { MixedSubject, SubjectOption } from './subject-kind'

interface AccessSubjectPickerProps {
  value: MixedSubject[]
  onChange: (value: MixedSubject[]) => void
  /** Danh mục đã trộn sẵn bốn loại — nơi sở hữu dữ liệu tự dựng rồi truyền vào. */
  options: SubjectOption[]
  /** Hiện "Đang tải…" khi danh mục chưa về, thay vì "Không có ai khớp." gây hiểu nhầm. */
  loading?: boolean
}

/**
 * Ô CHỌN NHIỀU trộn đủ BỐN loại đối tượng cùng một danh sách (đặc tả §C) —
 * khác `SubjectMultiSelect` của `document-access-dialog.tsx` (chọn LOẠI trước
 * rồi mới chọn trong loại đó): ở đây gõ một từ khóa là khớp CẢ BỐN danh mục
 * cùng lúc, đúng cảm giác hộp «Chia sẻ» của Drive — chọn quyền cho cả một nhóm
 * hỗn hợp người/phòng/pháp nhân/vai trò không cần đổi tab.
 *
 * Bản THUẦN UI — chuyển từ
 * `document/components/folder-share-subject-picker.tsx` lên đây
 * (phase 04, kế hoạch `plans/261002-0836-phan-quyen-tung-bao-cao`) để phân hệ
 * Báo cáo dùng lại được: nhận sẵn `options` qua prop, KHÔNG tự gọi hook của
 * `hr` — `shared/` cấm import các phân hệ. Nơi gọi tự lấy `options` từ
 * `useAccessSubjectOptions()` (hr sở hữu dữ liệu người/phòng/pháp nhân/vai trò).
 *
 * Không dùng `cmdk` (repo tránh thêm phụ thuộc chỉ để có ô tìm, xem
 * `shared/ui/search-select.tsx`) — dựng trên `Popover + Input`, lọc bằng
 * `stripDiacritics` để gõ không dấu vẫn khớp.
 */
export function AccessSubjectPicker({
  value,
  onChange,
  options,
  loading,
}: AccessSubjectPickerProps) {
  const [open, setOpen] = useState(false)
  const [keyword, setKeyword] = useState('')
  const [kindFilter, setKindFilter] = useState<number | null>(null)

  const allOptions = useMemo(() => toPickerOptions(options), [options])

  const selectedKeys = useMemo(() => new Set(value.map(keyOfSubject)), [value])
  const selectedOptions = allOptions.filter((option) => selectedKeys.has(option.key))

  const keywordMatches = useMemo(
    () => filterOptionsByKeyword(allOptions, keyword),
    [allOptions, keyword],
  )
  const matches =
    kindFilter == null
      ? keywordMatches
      : keywordMatches.filter((option) => option.subject_kind === kindFilter)
  const countByKind = (kind: number) =>
    keywordMatches.filter((option) => option.subject_kind === kind).length

  function toggle(option: SubjectOption) {
    const key = keyOfSubject(option)
    if (selectedKeys.has(key)) {
      onChange(value.filter((item) => keyOfSubject(item) !== key))
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
                {loading ? 'Đang tải…' : 'Không có ai khớp.'}
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
          onRemove={(key) => onChange(value.filter((item) => keyOfSubject(item) !== key))}
        />
      )}
    </div>
  )
}
