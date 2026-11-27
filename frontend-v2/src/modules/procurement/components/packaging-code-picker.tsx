/**
 * duoc-CR-784 — ô chọn NHIỀU mã bao bì của màn Tác động giá (bám `renderPicker` của bản mẫu).
 *
 * Cả khung là MỘT combobox: chip + ô gõ nằm chung một hàng, gõ ở đâu thì danh sách lọc ở đó (người chủ chốt 21/11/2026,
 * bỏ ô tìm thứ hai trong popup). Tiêu điểm LUÔN ở ô gõ khi danh sách mở; danh sách chỉ là listbox gắn bằng
 * `aria-activedescendant`, bấm chọn xong vẫn giữ chữ đang gõ để chọn tiếp nhiều mã khớp.
 *
 * Không dùng thẳng `shared/ui/multi-picker.tsx` vì luật tìm khác hẳn: gõ TÊN NHÓM là lọc cả nhóm để
 * "Chọn tất cả" chọn đúng nhóm đó (`buildPackagingCodeMatcher`), còn ô chung chỉ tìm chuỗi con có dấu.
 * Trần `maxCodes` mã — vượt thì chặn cả lượt và báo, không cắt bớt ngầm.
 */
import { Check, Search, X } from 'lucide-react'
import { useEffect, useId, useMemo, useRef, useState } from 'react'
import type { KeyboardEvent, MouseEvent } from 'react'
import { toast } from 'sonner'

import { Button } from '@/shared/ui/button'
import { Popover, PopoverAnchor, PopoverContent } from '@/shared/ui/popover'
import { cn } from '@/shared/utils/cn'

import type { PackagingCodeOption } from '../types/packaging-cost-types'
import {
  buildPackagingCodeMatcher,
  collectPackagingGroups,
  collectSearchGroups,
  PACKAGING_MAX_CODES,
} from '../utils/packaging-code-match'
import { formatPackagingPrice } from '../utils/packaging-price-format'

/** Số chip mã hiện trong ô trước khi gộp thành "+n mã" — chọn cả nhóm hàng trăm mã thì ô không phình. */
const CHIP_MAX = 12
/** Kiểu gọn (`compact`): chỉ chừng này chip, còn lại gộp "+n mã" để ô giữ đúng MỘT dòng. */
const COMPACT_CHIP_MAX = 2
/** Số dòng vẽ trong danh sách; "Chọn tất cả" vẫn áp cho MỌI mã khớp, kể cả phần chưa vẽ. */
const LIST_MAX = 200

/**
 * Ô chọn dùng cho ba loại mã: `material` (mã vật tư bao bì, mặc định — tìm theo tên nhóm, kèm số SP + giá mới), `product`
 * (mã sản phẩm có định mức, Lịch sử mua hàng — chỉ tìm chữ trong mã / tên, không có nhóm, không có số SP / giá) và
 * `rawMaterial` (mã nguyên liệu của Bảng giá nguyên liệu, bao-CR-800 — có nhóm + giá mới, KHÔNG có số SP vì nguyên liệu không
 * nằm trong định mức bao bì; tên nhóm để hiểu từ khóa chỉ lấy từ chính dữ liệu, không thêm năm vai trò chai / nắp / nhãn…).
 */
export type PackagingPickerKind = 'material' | 'product' | 'rawMaterial'

const PICKER_TEXT: Record<
  PackagingPickerKind,
  { aria: string; empty: string; more: string; summary: string }
> = {
  material: {
    aria: 'Chọn mã chai / nắp / nhãn / nhãn thùng / thùng',
    empty: 'Chọn mã chai / nắp / nhãn / nhãn thùng / thùng — gõ mã, tên hoặc tên nhóm',
    more: 'Thêm mã… (vd: chai · nắp · nhãn, thùng · NAP0085)',
    summary: 'mã vật tư bao bì khớp',
  },
  product: {
    aria: 'Chọn mã sản phẩm',
    empty: 'Chọn sản phẩm — gõ mã hoặc tên',
    more: 'Thêm sản phẩm… (vd: HH0713 · tên sản phẩm)',
    summary: 'sản phẩm có định mức bao bì',
  },
  rawMaterial: {
    aria: 'Chọn mã nguyên liệu',
    empty: 'Chọn mã nguyên liệu — gõ mã, tên, nhóm hoặc NCC',
    more: 'Thêm mã nguyên liệu…',
    summary: 'mã nguyên liệu khớp',
  },
}

interface PackagingCodePickerProps {
  /** Danh sách đã xếp sẵn (`sortPackagingCodeOptions`). */
  options: PackagingCodeOption[]
  kind?: PackagingPickerKind
  /** Chữ gợi ý khi CHƯA chọn mã nào (mặc định theo `kind`) — màn cho phép để trống = tất cả nói rõ ở đây. */
  emptyPlaceholder?: string
  value: string[]
  onChange: (codes: string[]) => void
  loading?: boolean
  maxCodes?: number
  /**
   * Kiểu gọn MỘT dòng, cao bằng các ô lọc bên cạnh (Giá mua gần nhất, 27/11/2026: kiểu thường hai dòng trông "mập"):
   * chip + chỗ gõ chung một hàng, tối đa `COMPACT_CHIP_MAX` chip rồi "+n mã". Màn Tác động / Lịch sử giữ kiểu thường.
   */
  compact?: boolean
}

export function PackagingCodePicker({
  options,
  value,
  onChange,
  loading = false,
  maxCodes = PACKAGING_MAX_CODES,
  kind = 'material',
  emptyPlaceholder,
  compact = false,
}: PackagingCodePickerProps) {
  const [open, setOpen] = useState(false)
  const [keyword, setKeyword] = useState('')
  //  -1 = chưa tô dòng nào: Enter khi chưa tô thì không chọn gì (tránh chọn nhầm dòng đầu).
  const [activeIndex, setActiveIndex] = useState(-1)
  const boxRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)
  const listboxId = useId()
  const text = PICKER_TEXT[kind]
  const showMaterialMeta = kind !== 'product'
  const chipMax = compact ? COMPACT_CHIP_MAX : CHIP_MAX

  //  Sản phẩm không có "nhóm": để rỗng thì từ khóa luôn rơi về tìm chữ (gõ "chai" ra sản phẩm tên có chữ chai).
  const groups = useMemo(
    () =>
      kind === 'material'
        ? collectSearchGroups(options)
        : kind === 'rawMaterial'
          ? collectPackagingGroups(options)
          : [],
    [options, kind],
  )
  const filtered = useMemo(
    () => options.filter(buildPackagingCodeMatcher(keyword, groups)),
    [options, keyword, groups],
  )
  const visible = useMemo(() => filtered.slice(0, LIST_MAX), [filtered])
  const selectedSet = useMemo(() => new Set(value), [value])
  const pickedInView = filtered.filter((option) => selectedSet.has(option.code)).length
  const activeOption = open && activeIndex >= 0 ? visible[activeIndex] : undefined
  const optionDomId = (code: string) => `${listboxId}-opt-${code}`

  //  Dòng đang tô luôn nằm trong khung nhìn khi bấm mũi tên (listbox cuộn riêng, tiêu điểm không rời ô gõ).
  useEffect(() => {
    if (activeOption) document.getElementById(optionDomId(activeOption.code))?.scrollIntoView?.({ block: 'nearest' })
    // eslint-disable-next-line react-hooks/exhaustive-deps -- optionDomId chỉ phụ thuộc listboxId (ổn định)
  }, [activeOption])

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

  /** Đóng danh sách và bỏ chữ đang gõ để ô trở về dạng "chip + gợi ý". */
  function closeList() {
    setOpen(false)
    setKeyword('')
    setActiveIndex(-1)
  }

  function handleKeyDown(event: KeyboardEvent<HTMLInputElement>) {
    //  Đang gõ dấu tiếng Việt (Telex / VNI): Enter / mũi tên thuộc về bộ gõ, không phải của ô chọn.
    if (event.nativeEvent.isComposing) return
    switch (event.key) {
      case 'ArrowDown':
      case 'ArrowUp': {
        event.preventDefault()
        if (!open) {
          setOpen(true)
          return
        }
        if (!visible.length) return
        const step = event.key === 'ArrowDown' ? 1 : -1
        setActiveIndex((current) => (current < 0 ? (step === 1 ? 0 : visible.length - 1) : (current + step + visible.length) % visible.length))
        return
      }
      case 'Enter': {
        //  Luôn chặn: ô nằm trong <form> thì Enter không được gửi form cha (bẫy biểu mẫu), kể cả khi không chọn được gì.
        event.preventDefault()
        if (!open) {
          setOpen(true)
          return
        }
        //  Có dòng đang tô (mũi tên) thì bật / tắt dòng đó; không thì theo bản mẫu: gõ ĐÚNG một mã trong danh sách,
        //  hoặc bộ lọc chỉ còn đúng một mã thì thêm mã đó. Xong xóa chữ để gõ mã kế tiếp.
        if (activeOption) {
          toggle(activeOption.code)
        } else {
          const typedCode = keyword.trim().split(/\s+/)[0]?.toUpperCase() ?? ''
          const hit =
            options.find((option) => option.code.toUpperCase() === typedCode) ??
            (filtered.length === 1 ? filtered[0] : undefined)
          if (!hit) return
          if (!selectedSet.has(hit.code)) commit([...value, hit.code])
        }
        setKeyword('')
        setActiveIndex(-1)
        return
      }
      case 'Escape':
        if (open) {
          event.preventDefault()
          event.stopPropagation()
          closeList()
          inputRef.current?.blur()
        }
        return
      case 'Tab':
        closeList()
        return
      case 'Backspace':
        //  Ô gõ trống thì Backspace bỏ chip cuối, như mọi ô chọn nhiều.
        if (!keyword && value.length > 0) onChange(value.slice(0, -1))
        return
      default:
    }
  }

  /** Bấm vào khoảng trống của khung (không phải chip / nút) thì đưa tiêu điểm về ô gõ. */
  function handleBoxMouseDown(event: MouseEvent<HTMLDivElement>) {
    const target = event.target as HTMLElement
    if (target === inputRef.current || target.closest('button')) return
    event.preventDefault()
    inputRef.current?.focus()
    if (!loading) setOpen(true)
  }

  return (
    <div className="space-y-2">
      <Popover open={open} onOpenChange={(next) => (next ? setOpen(true) : closeList())}>
        {/*
          Mã đã chọn hiện NGAY TRONG ô (chip có nút x để bỏ nhanh) + nút x cuối ô bỏ hết — người chủ chốt 20/11/2026.
          Khung là `div` vì chip chứa nút bỏ (nút lồng nút là HTML sai); `PopoverAnchor` giữ danh sách bám theo cả khung,
          không có `PopoverTrigger` — danh sách mở bằng tiêu điểm / bấm / gõ trong ô gõ.
        */}
        <PopoverAnchor asChild>
          <div
            ref={boxRef}
            onMouseDown={handleBoxMouseDown}
            className={cn(
              'flex w-full cursor-text items-center gap-1.5 rounded-md border border-input bg-background px-2 shadow-xs',
              compact ? 'h-9 flex-nowrap overflow-hidden py-1' : 'min-h-10 flex-wrap py-1.5',
              open && 'border-ring ring-[3px] ring-ring/50',
            )}
          >
            <Search className="mx-1 size-4 shrink-0 text-muted-foreground" />
            {value.slice(0, chipMax).map((code) => (
              <span
                key={code}
                //  Chip nổi hẳn trên nền ô (người chủ chốt 20/11/2026): nền + viền màu chính, chữ đậm.
                className={cn(
                  'inline-flex shrink-0 items-center gap-1 rounded-md border border-primary/30 bg-primary/10 pr-1 pl-2.5 text-[13px] font-semibold text-primary tabular-nums',
                  compact ? 'py-0.5' : 'py-1',
                )}
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
            {value.length > chipMax && (
              <span
                title={value.slice(chipMax).join(', ')}
                className={cn(
                  'shrink-0 rounded-md border border-primary/30 px-2.5 text-[13px] font-semibold text-primary',
                  compact ? 'py-0.5' : 'py-1',
                )}
              >
                +{value.length - chipMax} mã
              </span>
            )}
            <input
              ref={inputRef}
              type="text"
              role="combobox"
              aria-label={text.aria}
              aria-expanded={open}
              aria-controls={open ? listboxId : undefined}
              aria-autocomplete="list"
              aria-activedescendant={activeOption ? optionDomId(activeOption.code) : undefined}
              autoComplete="off"
              disabled={loading}
              value={keyword}
              placeholder={
                loading
                  ? 'Đang nạp danh sách mã…'
                  : value.length
                    ? compact
                      ? 'Thêm mã…'
                      : text.more
                    : (emptyPlaceholder ?? text.empty)
              }
              onChange={(event) => {
                setKeyword(event.target.value)
                setActiveIndex(-1)
                setOpen(true)
              }}
              onFocus={() => setOpen(true)}
              onClick={() => setOpen(true)}
              onKeyDown={handleKeyDown}
              className={cn(
                'flex-1 truncate bg-transparent py-1 text-sm outline-none placeholder:text-muted-foreground disabled:cursor-not-allowed',
                compact ? 'min-w-[5rem]' : 'min-w-[12rem]',
              )}
            />
            {value.length > 0 && (
              <button
                type="button"
                aria-label="Bỏ hết mã đã chọn"
                title="Bỏ hết mã đã chọn"
                onClick={() => onChange([])}
                className="ml-auto shrink-0 rounded-sm p-1 text-muted-foreground hover:text-destructive"
              >
                <X className="size-4" />
              </button>
            )}
          </div>
        </PopoverAnchor>
        <PopoverContent
          align="start"
          className="w-[min(44rem,calc(100vw-2rem))] p-0"
          //  Tiêu điểm ở lại ô gõ: không cướp khi mở, không trả về "nút kích hoạt" khi đóng, và bấm trong danh sách
          //  (kể cả nút Chọn tất cả) không làm ô gõ mất tiêu điểm.
          onOpenAutoFocus={(event) => event.preventDefault()}
          onCloseAutoFocus={(event) => event.preventDefault()}
          onMouseDown={(event) => event.preventDefault()}
          //  Bấm / chuyển tiêu điểm trong khung của chính ô này không tính là "ra ngoài".
          onInteractOutside={(event) => {
            if (boxRef.current?.contains(event.target as Node)) event.preventDefault()
          }}
        >
          <div className="flex flex-wrap items-center gap-2 border-b px-3 py-1.5 text-sm">
            <span className="text-muted-foreground">
              {filtered.length} {text.summary}
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
          <div
            id={listboxId}
            className="max-h-80 overflow-y-auto p-1"
            role="listbox"
            aria-label={text.aria}
            aria-multiselectable="true"
          >
            {filtered.length === 0 && (
              <p className="px-2 py-4 text-center text-sm text-muted-foreground">
                Không có mã phù hợp.
              </p>
            )}
            {visible.map((option, index) => {
              const checked = selectedSet.has(option.code)
              return (
                <div
                  key={option.code}
                  id={optionDomId(option.code)}
                  role="option"
                  aria-selected={checked}
                  onClick={() => toggle(option.code)}
                  onMouseMove={() => activeIndex !== index && setActiveIndex(index)}
                  className={cn(
                    'flex w-full cursor-pointer items-center gap-2 rounded-sm px-2 py-1.5 text-left text-sm hover:bg-accent',
                    checked && 'bg-accent',
                    index === activeIndex && 'bg-accent ring-1 ring-ring/60',
                  )}
                >
                  <Check className={cn('size-4 shrink-0', !checked && 'invisible')} />
                  <span className="w-28 shrink-0 font-medium tabular-nums">{option.code}</span>
                  {showMaterialMeta && (
                    <span className="w-24 shrink-0 truncate text-xs text-muted-foreground">
                      {option.group}
                    </span>
                  )}
                  <span className="min-w-0 flex-1 truncate">{option.name}</span>
                  {showMaterialMeta && (
                    <span className="shrink-0 text-xs text-muted-foreground tabular-nums">
                      {kind === 'material' && `${option.usage} SP`}
                      {option.new != null &&
                        `${kind === 'material' ? ' · ' : ''}${formatPackagingPrice(option.new)}`}
                    </span>
                  )}
                </div>
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
