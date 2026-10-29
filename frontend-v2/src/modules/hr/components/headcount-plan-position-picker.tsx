import { Plus } from 'lucide-react'
import { useMemo, useState } from 'react'

import { Button } from '@/shared/ui/button'
import { Input } from '@/shared/ui/input'
import { Popover, PopoverContent, PopoverTrigger } from '@/shared/ui/popover'
import { matchesVietnamese } from '@/shared/utils/vn-text'

/** Số dòng tối đa trong danh sách — dài hơn thì bắt gõ tìm (cùng trần với `SearchSelect`). */
const MAX_VISIBLE = 60

interface HeadcountPlanPositionPickerProps {
  /** Chức vụ CHƯA có dòng. */
  options: readonly { id: number; name: string }[]
  onPick: (id: number, name: string) => void
}

/**
 * Nút «+ Thêm vị trí» — bấm là mở ô tìm chức vụ, chọn là thêm dòng ngay (không có ô chọn đứng riêng rồi
 * mới bấm Thêm). Gõ không dấu vẫn khớp; Enter chọn kết quả đầu tiên.
 */
export function HeadcountPlanPositionPicker({ options, onPick }: HeadcountPlanPositionPickerProps) {
  const [open, setOpen] = useState(false)
  const [keyword, setKeyword] = useState('')
  const matches = useMemo(
    () => options.filter((p) => matchesVietnamese(p.name, keyword)).slice(0, MAX_VISIBLE),
    [options, keyword],
  )

  const toggle = (next: boolean) => {
    setOpen(next)
    if (!next) setKeyword('')
  }
  const pick = (p: { id: number; name: string }) => {
    onPick(p.id, p.name)
    toggle(false)
  }

  return (
    <Popover open={open} onOpenChange={toggle}>
      <PopoverTrigger asChild>
        <Button type="button" size="sm">
          <Plus className="size-4" />
          Thêm vị trí
        </Button>
      </PopoverTrigger>
      <PopoverContent align="start" className="w-72 p-0">
        <div className="border-b p-2">
          <Input
            autoFocus
            value={keyword}
            placeholder="Tìm chức vụ…"
            aria-label="Tìm chức vụ"
            onChange={(e) => setKeyword(e.target.value)}
            onKeyDown={(e) => {
              if (e.key !== 'Enter') return
              e.preventDefault()
              if (matches[0]) pick(matches[0])
            }}
          />
        </div>
        <div className="max-h-72 overflow-y-auto p-1">
          {matches.length === 0 && (
            <p className="px-2 py-4 text-center text-sm text-muted-foreground">
              {options.length ? 'Không thấy chức vụ nào khớp.' : 'Mọi chức vụ đã có dòng.'}
            </p>
          )}
          {matches.map((p) => (
            <button
              key={p.id}
              type="button"
              className="w-full rounded-sm px-2 py-1.5 text-left text-sm hover:bg-accent focus-visible:bg-accent focus-visible:outline-none"
              onClick={() => pick(p)}
            >
              {p.name}
            </button>
          ))}
        </div>
      </PopoverContent>
    </Popover>
  )
}
