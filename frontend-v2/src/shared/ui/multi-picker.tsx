import { Check, ChevronDown, ChevronUp, Search, X } from 'lucide-react'
import { useMemo, useState } from 'react'

import { Badge } from '@/shared/ui/badge'
import { Button } from '@/shared/ui/button'
import { Input } from '@/shared/ui/input'
import { Popover, PopoverContent, PopoverTrigger } from '@/shared/ui/popover'
import { cn } from '@/shared/utils/cn'

/**
 * Định danh của một mục.
 *
 * Cho phép cả CHUỖI vì có chỗ mục không phải một bản ghi đơn mà là một CẶP —
 * ví dụ (phòng ban × pháp nhân) ở khối phạm vi áp dụng của văn bản, khóa dạng
 * `"4:1"`. Ép về số thì hai phòng cùng tên ở hai công ty dính làm một.
 */
export type MultiPickerId = number | string

export interface MultiPickerOption {
  id: MultiPickerId
  label: string
  /** Chữ mờ bên phải: mã, số hiệu, chức danh… — thứ để phân biệt hai dòng trùng tên. */
  hint?: string
}

/**
 * `Id` bám theo kiểu của `value`, nên nơi gọi truyền `number[]` vẫn nhận lại
 * `number[]` ở `onChange` — không phải ép kiểu ở mọi chỗ đang dùng.
 */
interface MultiPickerProps<Id extends MultiPickerId = MultiPickerId> {
  value: Id[]
  onChange: (ids: Id[]) => void
  options: (Omit<MultiPickerOption, 'id'> & { id: Id })[]
  placeholder: string
  searchPlaceholder?: string
  emptyMessage?: string
  disabled?: boolean
}

/** Số dòng tối đa trong danh sách thả xuống — dài hơn thì bắt gõ tìm. */
const MAX_VISIBLE = 50

/**
 * Số chip bày ra trước khi gộp lại; muốn xem hết thì bấm «Xem thêm».
 *
 * Khách báo 25/08/2026: sổ văn bản chọn ~200 người xem, mỗi người một chip nên
 * dải chip cao hơn cả màn hình — ô «Người quản lý» ngay dưới bị đẩy đi mất,
 * người dùng tưởng form hỏng. Mười chip là đủ nhận ra "đang chọn những ai" mà
 * vẫn gọn trong hai hàng (khách chốt con số này).
 */
const MAX_CHIPS = 10

/**
 * Chiều cao tối đa của dải chip khi ĐÃ bung.
 *
 * Bung ra mà thả trôi thì 200 chip lại dựng đúng bức tường vừa dỡ. Cho nó cuộn
 * trong khung riêng: xem được hết mà phần dưới của form không bị đẩy đi đâu cả.
 */
const CAO_TOI_DA_KHI_BUNG = 'max-h-44 overflow-y-auto'

/**
 * Chọn NHIỀU mục từ một danh sách có sẵn: nút mở, ô tìm, danh sách tick, và dải
 * chip của những mục đã chọn.
 *
 * Dùng cho nhân sự, loại văn bản, văn bản… — bất cứ thứ gì rút gọn được về
 * `{id, label, hint}`. Trước đây chỉ có bản riêng cho nhân sự, và mỗi lần cần
 * chọn nhiều thứ khác lại chép ra một bản gần giống.
 */
export function MultiPicker<Id extends MultiPickerId = MultiPickerId>({
  value,
  onChange,
  options,
  placeholder,
  searchPlaceholder = 'Tìm…',
  emptyMessage = 'Không tìm thấy mục nào.',
  disabled,
}: MultiPickerProps<Id>) {
  const [open, setOpen] = useState(false)
  const [keyword, setKeyword] = useState('')
  //  Bung hết dải chip. Mặc định gập lại — xem `MAX_CHIPS`.
  const [xemHetChip, setXemHetChip] = useState(false)

  const selected = useMemo(
    () => value.map((id) => options.find((item) => item.id === id)).filter(Boolean) as typeof options,
    [value, options],
  )

  // Giữ CẢ danh sách lọc được, không chỉ phần bày ra: nút "Chọn tất cả" phải áp
  // cho mọi mục khớp từ khóa, kể cả những mục bị `MAX_VISIBLE` cắt bớt — người
  // dùng gõ tìm rồi bấm chọn tất cả là muốn hết chỗ đó, không phải 50 dòng đầu.
  const filtered = useMemo(() => {
    const needle = keyword.trim().toLowerCase()
    if (!needle) return options
    return options.filter((item) =>
      [item.label, item.hint].some((field) => (field ?? '').toLowerCase().includes(needle)),
    )
  }, [options, keyword])

  const matches = useMemo(() => filtered.slice(0, MAX_VISIBLE), [filtered])

  const conNhieuHonMucGap = selected.length > MAX_CHIPS
  const chipHienRa = xemHetChip ? selected : selected.slice(0, MAX_CHIPS)

  /** Đã tick hết phần đang lọc chưa — quyết định nút là "Chọn" hay "Bỏ chọn". */
  const allPicked = filtered.length > 0 && filtered.every((item) => value.includes(item.id))

  function toggle(id: Id) {
    onChange(value.includes(id) ? value.filter((item) => item !== id) : [...value, id])
  }

  /** Tick / bỏ tick TOÀN BỘ phần đang lọc, giữ nguyên các mục đã chọn ngoài đó. */
  function toggleAll() {
    const ids = filtered.map((item) => item.id)
    if (allPicked) {
      const dropped = new Set(ids)
      onChange(value.filter((id) => !dropped.has(id)))
      return
    }
    onChange([...value, ...ids.filter((id) => !value.includes(id))])
  }

  return (
    <div className="space-y-2">
      <Popover open={open} onOpenChange={setOpen}>
        <PopoverTrigger asChild>
          <Button
            type="button"
            variant="outline"
            disabled={disabled}
            className={cn(
              'w-full justify-start font-normal',
              selected.length === 0 && 'text-muted-foreground',
            )}
          >
            <Search className="size-4" />
            {/*  Có chọn rồi thì nút nói SỐ LƯỢNG, không lặp lại câu mời chọn:
                 với dải chip đã gập, đây là chỗ duy nhất đọc ra "đang chọn bao
                 nhiêu" mà không phải đếm tay. */}
            {selected.length > 0 ? `Đã chọn ${selected.length}` : placeholder}
          </Button>
        </PopoverTrigger>
        <PopoverContent align="start" className="w-80 p-0">
          <div className="border-b p-2">
            <Input
              autoFocus
              placeholder={searchPlaceholder}
              value={keyword}
              onChange={(event) => setKeyword(event.target.value)}
            />
          </div>
          {filtered.length > 0 && (
            <div className="flex items-center justify-between gap-2 border-b px-2 py-1.5">
              <button
                type="button"
                onClick={toggleAll}
                className="rounded-sm px-1 py-0.5 text-sm font-medium text-primary hover:underline focus-visible:ring-2 focus-visible:ring-ring focus-visible:outline-none"
              >
                {allPicked ? 'Bỏ chọn tất cả' : 'Chọn tất cả'}
                <span className="ml-1 font-normal text-muted-foreground tabular-nums">
                  ({filtered.length})
                </span>
              </button>
              {/* Nhắc rõ nút đang áp cho phần lọc được, không phải cả danh sách. */}
              {keyword.trim() && (
                <span className="text-xs text-muted-foreground">theo từ khóa đang tìm</span>
              )}
            </div>
          )}

          <div className="max-h-72 overflow-y-auto p-1">
            {matches.length === 0 && (
              <p className="px-2 py-4 text-center text-sm text-muted-foreground">
                {emptyMessage}
              </p>
            )}
            {matches.map((item) => {
              const checked = value.includes(item.id)
              return (
                <button
                  key={item.id}
                  type="button"
                  onClick={() => toggle(item.id)}
                  className={cn(
                    'flex w-full items-center gap-2 rounded-sm px-2 py-1.5 text-left text-sm hover:bg-accent',
                    checked && 'bg-accent/50',
                  )}
                >
                  <Check className={cn('size-4 shrink-0', !checked && 'invisible')} />
                  <span className="flex-1 truncate">{item.label}</span>
                  {item.hint && (
                    <span className="shrink-0 text-xs text-muted-foreground">{item.hint}</span>
                  )}
                </button>
              )
            })}

            {/* Danh sách bị cắt bớt thì phải nói ra, không thì nhìn như đã hết
                mục — trong khi "Chọn tất cả" vẫn tính cả phần chưa bày. */}
            {filtered.length > matches.length && (
              <p className="px-2 py-2 text-center text-xs text-muted-foreground">
                Còn {filtered.length - matches.length} mục nữa — gõ để thu hẹp danh sách.
              </p>
            )}
          </div>
        </PopoverContent>
      </Popover>

      {selected.length > 0 && (
        <div className="space-y-1.5">
          {/*  Dải chip. Khi bung thì đóng khung + cho cuộn, không để nó đẩy phần
               dưới của form đi (xem `CAO_TOI_DA_KHI_BUNG`). */}
          <div
            className={cn(
              'flex flex-wrap gap-1',
              xemHetChip && conNhieuHonMucGap && `${CAO_TOI_DA_KHI_BUNG} rounded-md border p-2`,
            )}
          >
            {chipHienRa.map((item) => (
              <Badge key={item.id} variant="secondary" className="gap-1 font-normal">
                {item.label}
                <button
                  type="button"
                  aria-label={`Bỏ ${item.label}`}
                  onClick={() => toggle(item.id)}
                  className="text-muted-foreground hover:text-foreground"
                >
                  <X className="size-3" />
                </button>
              </Badge>
            ))}
          </div>

          {/*  HÀNG THAO TÁC riêng, không trộn vào dải chip: hai nút này không
               phải là "một người đã chọn" nên đứng lẫn giữa các chip là đọc
               nhầm. Trái = xem thêm / thu gọn, phải = bỏ hết. */}
          {(conNhieuHonMucGap || selected.length > 1) && (
            <div className="flex items-center justify-between gap-2">
              {conNhieuHonMucGap ? (
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  className="h-7 gap-1 px-2 text-xs text-muted-foreground"
                  onClick={() => setXemHetChip((truoc) => !truoc)}
                >
                  {xemHetChip ? (
                    <>
                      <ChevronUp className="size-3.5" />
                      Thu gọn
                    </>
                  ) : (
                    <>
                      <ChevronDown className="size-3.5" />
                      Xem thêm {selected.length - MAX_CHIPS}
                    </>
                  )}
                </Button>
              ) : (
                <span />
              )}

              {selected.length > 1 && (
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  className="h-7 px-2 text-xs text-muted-foreground hover:text-destructive"
                  onClick={() => onChange([])}
                  disabled={disabled}
                >
                  Bỏ hết
                </Button>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
