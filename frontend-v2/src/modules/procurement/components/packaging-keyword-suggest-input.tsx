/**
 * duoc-CR-784 — ô tìm CÓ GỢI Ý của thanh lọc chip (Tổng hợp theo sản phẩm, bảng sản phẩm của Tác động giá; 27/11/2026):
 * gõ chữ thì vẫn lọc như cũ, đồng thời sổ ra tối đa vài dòng gợi ý — SẢN PHẨM (mã HH + tên, từ danh sách sản phẩm có định
 * mức) và MÃ THÀNH PHẦN (mã VTBB + tên, từ danh sách mã trong định mức). Bấm / Enter một dòng = điền đúng mã đó vào ô.
 *
 * Hai danh sách dùng lại cache của màn Lịch sử / Tác động (`usePackagingFgOptions`, `usePackagingCodeOptions`), nạp một lần
 * khi ô được bấm lần đầu. Lọc tại trình duyệt, không dấu, mọi từ phải có mặt trong mã hoặc tên.
 */
import { Search } from 'lucide-react'
import { useId, useMemo, useState, type KeyboardEvent } from 'react'

import { Input } from '@/shared/ui/input'
import { Popover, PopoverAnchor, PopoverContent } from '@/shared/ui/popover'
import { cn } from '@/shared/utils/cn'

import { usePackagingFgOptions } from '../hooks/use-packaging-history'
import { usePackagingCodeOptions } from '../hooks/use-packaging-impact'
import { pickKeywordSuggestions, type KeywordSuggestion } from '../utils/packaging-keyword-suggestions'

interface PackagingKeywordSuggestInputProps {
  value: string
  onChange: (value: string) => void
  className?: string
}

export function PackagingKeywordSuggestInput({ value, onChange, className }: PackagingKeywordSuggestInputProps) {
  const [open, setOpen] = useState(false)
  //  Chỉ nạp hai danh sách khi người dùng thật sự bấm vào ô (màn mở ra không tốn thêm hai lượt gọi).
  const [touched, setTouched] = useState(false)
  const [active, setActive] = useState(-1)
  const listId = useId()
  const fgQuery = usePackagingFgOptions(touched)
  const codeQuery = usePackagingCodeOptions(touched)
  const suggestions = useMemo(
    () => pickKeywordSuggestions(value, fgQuery.data ?? [], codeQuery.data ?? []),
    [value, fgQuery.data, codeQuery.data],
  )
  const showList = open && suggestions.length > 0

  const choose = (item: KeywordSuggestion) => {
    onChange(item.code)
    setOpen(false)
    setActive(-1)
  }

  const handleKeyDown = (event: KeyboardEvent<HTMLInputElement>) => {
    if (!showList) return
    if (event.key === 'ArrowDown') {
      event.preventDefault()
      setActive((index) => Math.min(index + 1, suggestions.length - 1))
    } else if (event.key === 'ArrowUp') {
      event.preventDefault()
      setActive((index) => Math.max(index - 1, -1))
    } else if (event.key === 'Enter' && active >= 0) {
      event.preventDefault()
      choose(suggestions[active])
    } else if (event.key === 'Escape') {
      setOpen(false)
    }
  }

  return (
    <Popover open={showList} onOpenChange={setOpen}>
      <PopoverAnchor asChild>
        <div className={cn('relative', className)}>
          <Search className="absolute top-1/2 left-3 size-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            className="pl-9"
            role="combobox"
            aria-label="Tìm sản phẩm"
            aria-expanded={showList}
            aria-controls={showList ? listId : undefined}
            aria-autocomplete="list"
            aria-activedescendant={showList && active >= 0 ? `${listId}-${active}` : undefined}
            autoComplete="off"
            placeholder="Tìm mã HH, tên, mã thành phần…"
            value={value}
            onFocus={() => {
              setTouched(true)
              setOpen(true)
            }}
            onChange={(event) => {
              onChange(event.target.value)
              setActive(-1)
              setOpen(true)
            }}
            onKeyDown={handleKeyDown}
          />
        </div>
      </PopoverAnchor>
      <PopoverContent
        align="start"
        className="w-[min(36rem,calc(100vw-2rem))] p-1"
        //  Tiêu điểm ở lại ô gõ: không cướp khi mở / đóng, bấm trong danh sách không làm ô mất tiêu điểm.
        onOpenAutoFocus={(event) => event.preventDefault()}
        onCloseAutoFocus={(event) => event.preventDefault()}
        onMouseDown={(event) => event.preventDefault()}
      >
        <ul id={listId} role="listbox" aria-label="Gợi ý" className="max-h-80 overflow-y-auto">
          {suggestions.map((item, index) => (
            <li
              key={`${item.kind}-${item.code}`}
              id={`${listId}-${index}`}
              role="option"
              aria-selected={index === active}
              onClick={() => choose(item)}
              onMouseEnter={() => setActive(index)}
              className={cn(
                'flex cursor-pointer items-baseline gap-3 rounded-sm px-2 py-1.5 text-sm',
                index === active && 'bg-accent',
              )}
            >
              <span className="w-24 shrink-0 font-semibold tabular-nums">{item.code}</span>
              <span className="min-w-0 flex-1 truncate" title={item.name}>
                {item.name}
              </span>
              <span className="shrink-0 text-xs text-muted-foreground">
                {item.kind === 'product' ? 'Sản phẩm' : 'Thành phần'}
              </span>
            </li>
          ))}
        </ul>
      </PopoverContent>
    </Popover>
  )
}
