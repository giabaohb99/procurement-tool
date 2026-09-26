import { Bookmark, BookmarkPlus, Loader2, Save, Trash2 } from 'lucide-react'
import { useRef, useState } from 'react'

import { Button } from '@/shared/ui/button'
import { confirm } from '@/shared/ui/confirm-dialog'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/shared/ui/dialog'
import { Input } from '@/shared/ui/input'
import { Label } from '@/shared/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/shared/ui/select'

import { useCustomsSavedFilterMutations, useCustomsSavedFilters } from '../../hooks/use-customs-saved-filters'
import { parseFilterParams, sameFilterParams } from '../../utils/customs-saved-filter'

/**
 * «Bộ lọc đã lưu» + «Lưu bộ lọc này» trên thanh lọc của màn Tra cứu giá hải quan — bao-CR-496 (F07).
 *
 * Bộ lọc là của RIÊNG tài khoản, lưu ở backend (đổi máy không mất — đại ca chốt, không dùng
 * localStorage). Chọn một bộ → trang về ĐÚNG trạng thái đó (ô không có trong bộ bị xóa khỏi
 * URL). Đang đứng trên một bộ mà điều kiện đã đổi thì có «Cập nhật» để ghi đè; «Xóa» hỏi lại.
 */
interface CustomsSavedFilterBarProps {
  /** Chuỗi ô lọc đang áp (từ `collectFilterParams`). */
  currentParams: string
  /** Danh sách tên ô lọc của trang — chỉ những khóa này được ghi / đọc. */
  filterNames: readonly string[]
  /** Nạp bộ lọc lên URL (thường là `setUrlParams`). */
  onApply: (next: Record<string, string | null>) => void
  className?: string
}

const NONE = '__none__'

export function CustomsSavedFilterBar({
  currentParams,
  filterNames,
  onApply,
  className,
}: CustomsSavedFilterBarProps) {
  const { data } = useCustomsSavedFilters()
  const { create, update, remove } = useCustomsSavedFilterMutations()
  const [selectedId, setSelectedId] = useState<number | null>(null)
  const [saveOpen, setSaveOpen] = useState(false)
  const [name, setName] = useState('')
  //  Chặn bấm đúp bằng ref đổi ngay trong tick — `disabled={isPending}` chỉ đúng ở lượt render sau.
  const busy = useRef(false)

  const items = data?.items ?? []
  const selected = items.find((f) => f.id === selectedId) ?? null
  const dirty = selected !== null && !sameFilterParams(selected.params, currentParams, filterNames)
  const atCap = data !== undefined && items.length >= data.max_per_user

  function pick(value: string) {
    if (value === NONE) {
      setSelectedId(null)
      return
    }
    const f = items.find((x) => String(x.id) === value)
    if (!f) return
    setSelectedId(f.id)
    onApply(parseFilterParams(f.params, filterNames))
  }

  async function submitSave() {
    const trimmed = name.trim()
    if (!trimmed || busy.current) return
    busy.current = true
    try {
      const f = await create.mutateAsync({ name: trimmed, params: currentParams })
      setSelectedId(f.id)
      setSaveOpen(false)
      setName('')
    } catch {
      // http-client đã hiện toast lỗi (trùng tên, quá 50 bộ…)
    } finally {
      busy.current = false
    }
  }

  async function overwrite() {
    if (!selected || busy.current) return
    busy.current = true
    try {
      await update.mutateAsync({ id: selected.id, params: currentParams })
    } catch {
      // toast lỗi đã hiện
    } finally {
      busy.current = false
    }
  }

  async function removeSelected() {
    if (!selected) return
    const ok = await confirm({
      title: 'Xóa bộ lọc đã lưu',
      message: `Xóa bộ lọc «${selected.name}»? Điều kiện đang áp trên màn hình không đổi.`,
      confirmLabel: 'Xóa',
    })
    if (!ok) return
    await remove.mutateAsync(selected.id)
    setSelectedId(null)
  }

  return (
    <div className={className}>
      <div className="flex flex-wrap items-center gap-2">
        <Select value={selected ? String(selected.id) : NONE} onValueChange={pick}>
          <SelectTrigger className="h-9 w-56" aria-label="Bộ lọc đã lưu">
            <Bookmark className="size-4 text-muted-foreground" />
            <SelectValue placeholder="Bộ lọc đã lưu" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value={NONE}>Bộ lọc đã lưu — không chọn</SelectItem>
            {items.map((f) => (
              <SelectItem key={f.id} value={String(f.id)}>
                {f.name}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>

        {dirty && (
          <Button
            type="button"
            variant="outline"
            size="sm"
            disabled={update.isPending}
            onClick={() => void overwrite()}
            title="Ghi điều kiện đang áp vào bộ lọc đang chọn"
          >
            {update.isPending ? <Loader2 className="size-4 animate-spin" /> : <Save className="size-4" />}
            Cập nhật
          </Button>
        )}

        <Button
          type="button"
          variant="outline"
          size="sm"
          disabled={!currentParams || atCap}
          onClick={() => setSaveOpen(true)}
          title={
            atCap
              ? `Mỗi người lưu tối đa ${data?.max_per_user ?? 50} bộ lọc — xóa bớt rồi lưu lại`
              : !currentParams
                ? 'Chưa áp điều kiện nào để lưu'
                : 'Đặt tên cho tổ hợp điều kiện đang áp'
          }
        >
          <BookmarkPlus className="size-4" />
          Lưu bộ lọc này
        </Button>

        {selected && (
          <Button
            type="button"
            variant="ghost"
            size="sm"
            disabled={remove.isPending}
            onClick={() => void removeSelected()}
            aria-label={`Xóa bộ lọc ${selected.name}`}
            title="Xóa bộ lọc đang chọn"
          >
            <Trash2 className="size-4" />
            Xóa
          </Button>
        )}
      </div>

      <Dialog open={saveOpen} onOpenChange={(open) => !open && setSaveOpen(false)}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>Lưu bộ lọc này</DialogTitle>
            <DialogDescription>
              Đặt tên cho tổ hợp điều kiện đang áp (ví dụ «Abamectin 3.6 EC»). Lần sau chọn tên
              này là màn hình về đúng trạng thái đó. Bộ lọc là của riêng bạn.
            </DialogDescription>
          </DialogHeader>
          <form
            onSubmit={(e) => {
              e.preventDefault()
              void submitSave()
            }}
            className="space-y-2"
          >
            <Label htmlFor="customs-saved-filter-name">Tên bộ lọc</Label>
            <Input
              id="customs-saved-filter-name"
              value={name}
              maxLength={120}
              autoFocus
              onChange={(e) => setName(e.target.value)}
              placeholder="Tối đa 120 ký tự"
            />
            <DialogFooter className="pt-2">
              <Button type="button" variant="outline" onClick={() => setSaveOpen(false)}>
                Hủy
              </Button>
              <Button type="submit" disabled={!name.trim() || create.isPending}>
                {create.isPending ? <Loader2 className="size-4 animate-spin" /> : <Save className="size-4" />}
                Lưu
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  )
}
