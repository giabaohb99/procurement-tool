/**
 * duoc-CR-784 — ô chọn NHIỀU mã bao bì của màn Tác động giá (bám `renderPicker` của bản mẫu).
 *
 * Không dùng thẳng `shared/ui/multi-picker.tsx` vì luật tìm khác hẳn: gõ TÊN NHÓM là lọc cả nhóm để
 * "Chọn tất cả" chọn đúng nhóm đó (`buildPackagingCodeMatcher`), còn ô chung chỉ tìm chuỗi con có dấu.
 * Trần `maxCodes` mã — vượt thì chặn cả lượt và báo, không cắt bớt ngầm.
 */
import { Check, Search, X } from 'lucide-react'
import { useMemo, useState } from 'react'
import { toast } from 'sonner'

import { Button } from '@/shared/ui/button'
import { Input } from '@/shared/ui/input'
import { Popover, PopoverAnchor, PopoverContent, PopoverTrigger } from '@/shared/ui/popover'
import { cn } from '@/shared/utils/cn'

import type { PackagingCodeOption } from '../types/packaging-cost-types'
import {
  buildPackagingCodeMatcher,
  collectSearchGroups,
  PACKAGING_MAX_CODES,
} from '../utils/packaging-code-match'
import { formatPackagingPrice } from '../utils/packaging-price-format'

/** Số chip mã hiện trong ô trước khi gộp thành "+n mã" — chọn cả nhóm hàng trăm mã thì ô không phình. */
const CHIP_MAX = 12
/** Số dòng vẽ trong danh sách; "Chọn tất cả" vẫn áp cho MỌI mã khớp, kể cả phần chưa vẽ. */
const LIST_MAX = 200

interface PackagingCodePickerProps {
  /** Danh sách đã xếp sẵn (`sortPackagingCodeOptions`). */
  options: PackagingCodeOption[]
  value: string[]
  onChange: (codes: string[]) => void
  loading?: boolean
  maxCodes?: number
}

export function PackagingCodePicker({
  options,
  value,
  onChange,
  loading = false,
  maxCodes = PACKAGING_MAX_CODES,
}: PackagingCodePickerProps) {
  const [open, setOpen] = useState(false)
  const [keyword, setKeyword] = useState('')

  const groups = useMemo(() => collectSearchGroups(options), [options])
  const filtered = useMemo(
    () => options.filter(buildPackagingCodeMatcher(keyword, groups)),
    [options, keyword, groups],
  )
  const selectedSet = useMemo(() => new Set(value), [value])
  const pickedInView = filtered.filter((option) => selectedSet.has(option.code)).length

  function commit(next: string[]) {
    if (next.length > maxCodes) {
      toast.error(
        `Chọn tối đa ${maxCodes} mã một lần — đang chọn ${next.length} mã. Thu hẹp bộ lọc rồi chọn lại.`,
      )
      return
    }
    onChange(next)
  }

  function toggle(code: string) {
    commit(selectedSet.has(code) ? value.filter((item) => item !== code) : [...value, code])
  }

  /** Chọn đúng các mã ĐANG LỌC, giữ nguyên mã đã chọn ngoài phần đó. */
  function selectAllFiltered() {
    commit([...value, ...filtered.map((o) => o.code).filter((code) => !selectedSet.has(code))])
  }

  function clearFiltered() {
    const dropped = new Set(filtered.map((option) => option.code))
    onChange(value.filter((code) => !dropped.has(code)))
  }

  return (
    <div className="space-y-2">
      <Popover open={open} onOpenChange={setOpen}>
        {/*
          Mã đã chọn hiện NGAY TRONG ô (chip có nút x để bỏ nhanh) + nút x cuối ô bỏ hết — người chủ chốt 20/11/2026.
          Khung là `div` (không phải `button`) vì chip chứa nút bỏ: nút lồng trong nút là HTML sai, bấm x lại mở danh sách.
          Phần chữ còn lại mới là nút mở danh sách; `PopoverAnchor` giữ danh sách bám theo cả khung.
        */}
        <PopoverAnchor asChild>
          <div
            className={cn(
              'flex min-h-10 w-full flex-wrap items-center gap-1.5 rounded-md border border-input bg-background px-2 py-1.5 shadow-xs',
              open && 'border-ring ring-[3px] ring-ring/50',
            )}
          >
            <Search className="mx-1 size-4 shrink-0 text-muted-foreground" />
            {value.slice(0, CHIP_MAX).map((code) => (
              <span
                key={code}
                //  Chip nổi hẳn trên nền ô (người chủ chốt 20/11/2026): nền + viền màu chính, chữ đậm.
                className="inline-flex items-center gap-1 rounded-md border border-primary/30 bg-primary/10 py-1 pr-1 pl-2.5 text-[13px] font-semibold text-primary tabular-nums"
              >
                {code}
                <button
                  type="button"
                  aria-label={`Bỏ ${code}`}
                  onClick={() => onChange(value.filter((item) => item !== code))}
                  className="rounded-sm p-0.5 text-primary/70 hover:bg-primary/15 hover:text-destructive"
                >
                  <X className="size-3.5" />
                </button>
              </span>
            ))}
            {value.length > CHIP_MAX && (
              <span className="rounded-md border border-primary/30 px-2.5 py-1 text-[13px] font-semibold text-primary">
                +{value.length - CHIP_MAX} mã
              </span>
            )}
            <PopoverTrigger asChild>
              <button
                type="button"
                aria-label="Chọn mã chai / nắp / nhãn / nhãn thùng / thùng"
                disabled={loading}
                className="min-w-[12rem] flex-1 truncate py-1 text-left text-sm text-muted-foreground outline-none disabled:cursor-not-allowed"
              >
                {loading
                  ? 'Đang nạp danh sách mã…'
                  : value.length
                    ? 'Thêm mã…'
                    : 'Chọn mã chai / nắp / nhãn / nhãn thùng / thùng — gõ mã, tên hoặc tên nhóm'}
              </button>
            </PopoverTrigger>
            {value.length > 0 && (
              <button
                type="button"
                aria-label="Bỏ hết mã đã chọn"
                title="Bỏ hết mã đã chọn"
                onClick={() => onChange([])}
                className="ml-auto rounded-sm p-1 text-muted-foreground hover:text-destructive"
              >
                <X className="size-4" />
              </button>
            )}
          </div>
        </PopoverAnchor>
        <PopoverContent align="start" className="w-[min(44rem,calc(100vw-2rem))] p-0">
          <div className="border-b p-2">
            <Input
              autoFocus
              aria-label="Tìm mã bao bì"
              placeholder="Vd: chai · nắp · nhãn, thùng · NAP0085"
              value={keyword}
              onChange={(event) => setKeyword(event.target.value)}
            />
          </div>
          <div className="flex flex-wrap items-center gap-2 border-b px-3 py-1.5 text-sm">
            <span className="text-muted-foreground">
              {filtered.length} mã bao bì đang dùng cho sản phẩm
            </span>
            <div className="ml-auto flex gap-1">
              <Button
                type="button"
                size="sm"
                variant="ghost"
                disabled={!filtered.length}
                onClick={selectAllFiltered}
              >
                Chọn tất cả ({filtered.length})
              </Button>
              <Button
                type="button"
                size="sm"
                variant="ghost"
                disabled={!pickedInView}
                onClick={clearFiltered}
              >
                Bỏ chọn{pickedInView ? ` (${pickedInView})` : ''}
              </Button>
            </div>
          </div>
          <div className="max-h-80 overflow-y-auto p-1" role="listbox" aria-multiselectable="true">
            {filtered.length === 0 && (
              <p className="px-2 py-4 text-center text-sm text-muted-foreground">
                Không có mã phù hợp.
              </p>
            )}
            {filtered.slice(0, LIST_MAX).map((option) => {
              const checked = selectedSet.has(option.code)
              return (
                <button
                  key={option.code}
                  type="button"
                  role="option"
                  aria-selected={checked}
                  onClick={() => toggle(option.code)}
                  className={cn(
                    'flex w-full items-center gap-2 rounded-sm px-2 py-1.5 text-left text-sm hover:bg-accent',
                    checked && 'bg-accent',
                  )}
                >
                  <Check className={cn('size-4 shrink-0', !checked && 'invisible')} />
                  <span className="w-28 shrink-0 font-medium tabular-nums">{option.code}</span>
                  <span className="w-24 shrink-0 truncate text-xs text-muted-foreground">
                    {option.group}
                  </span>
                  <span className="min-w-0 flex-1 truncate">{option.name}</span>
                  <span className="shrink-0 text-xs text-muted-foreground tabular-nums">
                    {option.usage} SP
                    {option.new != null && ` · ${formatPackagingPrice(option.new)}`}
                  </span>
                </button>
              )
            })}
            {filtered.length > LIST_MAX && (
              <p className="px-2 py-2 text-center text-xs text-muted-foreground">
                Còn {filtered.length - LIST_MAX} mã nữa — gõ để thu hẹp, hoặc bấm Chọn tất cả.
              </p>
            )}
          </div>
        </PopoverContent>
      </Popover>
    </div>
  )
}
