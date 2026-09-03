import { Loader2 } from 'lucide-react'
import { useState } from 'react'
import { toast } from 'sonner'

import { extractErrorMessage } from '@/core/api/response-envelope'
import { Button } from '@/shared/ui/button'
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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/shared/ui/select'
import { Textarea } from '@/shared/ui/textarea'

import { useSaveForumBoard } from '../hooks/use-save-forum-board'
import { FORUM_BOARD_STATUS } from '../types/forum-board'
import type { ForumBoardNode } from '../types/forum-board'
import { BoardIcon } from './board-icon'

interface BoardFormDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  /** null = tạo mới; có giá trị = sửa nhóm/box đó. */
  board: ForumBoardNode | null
  /** Các nhóm cấp 1 để chọn làm cha — box phải nằm trong một nhóm. */
  groups: { id: number; name: string }[]
  /** Gợi ý cha khi TẠO MỚI (bấm «Thêm box» ngay trên một nhóm); 0 = tạo nhóm. */
  defaultParentId?: number
}

/**
 * Hộp tạo/sửa nhóm-box (CR-263). Nhóm (`parent_id = 0`) chỉ làm tiêu đề, box
 * mới là nơi đăng thread — backend chặn hạ nhóm đang chứa box xuống làm box,
 * lỗi đó trả qua toast chứ FE không đoán trước.
 */
export function BoardFormDialog({
  open,
  onOpenChange,
  board,
  groups,
  defaultParentId = 0,
}: BoardFormDialogProps) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      {/* Radix unmount content khi đóng — form nằm ở component con nên mỗi lần
          MỞ là state khởi tạo lại từ props, không cần useEffect reset tay. */}
      <BoardFormBody
        key={board?.id ?? 0}
        onOpenChange={onOpenChange}
        board={board}
        groups={groups}
        defaultParentId={defaultParentId}
      />
    </Dialog>
  )
}

function BoardFormBody({
  onOpenChange,
  board,
  groups,
  defaultParentId = 0,
}: Omit<BoardFormDialogProps, 'open'>) {
  const save = useSaveForumBoard()
  const [form, setForm] = useState({
    name: board?.name ?? '',
    description: board?.description ?? '',
    icon: board?.icon ?? '',
    parentId: board?.parent_id ?? defaultParentId,
    sortOrder: board?.sort_order ?? 0,
    status: (board?.status ?? FORUM_BOARD_STATUS.active) as number,
  })

  const isGroup = form.parentId === 0

  async function submit() {
    try {
      await save.mutateAsync({
        boardId: board?.id ?? 0,
        input: {
          name: form.name.trim(),
          description: form.description.trim(),
          icon: form.icon.trim(),
          parent_id: form.parentId,
          sort_order: form.sortOrder,
          status: form.status,
        },
      })
      toast.success(board ? 'Đã cập nhật nhóm/box' : 'Đã tạo nhóm/box')
      onOpenChange(false)
    } catch (error) {
      toast.error(extractErrorMessage(error))
    }
  }

  return (
    <DialogContent className="sm:max-w-lg">
      <DialogHeader>
          <DialogTitle>
            {board ? 'Sửa nhóm/box' : isGroup ? 'Thêm nhóm' : 'Thêm box'}
          </DialogTitle>
          <DialogDescription>
            Nhóm là tiêu đề cấp 1; box nằm trong nhóm và là nơi đăng thread.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-3">
          <div className="space-y-1.5">
            <Label htmlFor="board-name">Tên</Label>
            <Input
              id="board-name"
              value={form.name}
              onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))}
              maxLength={120}
              autoFocus
            />
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="board-parent">Thuộc nhóm</Label>
            <Select
              value={String(form.parentId)}
              onValueChange={(v) => setForm((f) => ({ ...f, parentId: Number(v) }))}
            >
              <SelectTrigger id="board-parent" className="w-full">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="0">Không — đây là NHÓM tiêu đề</SelectItem>
                {groups
                  .filter((g) => g.id !== board?.id)
                  .map((g) => (
                    <SelectItem key={g.id} value={String(g.id)}>
                      {g.name}
                    </SelectItem>
                  ))}
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="board-desc">Mô tả</Label>
            <Textarea
              id="board-desc"
              value={form.description}
              onChange={(e) => setForm((f) => ({ ...f, description: e.target.value }))}
              rows={2}
              placeholder="Một dòng nói box này bàn chuyện gì"
            />
          </div>

          <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
            <div className="space-y-1.5 sm:col-span-1">
              <Label htmlFor="board-icon">Icon</Label>
              <div className="flex items-center gap-2">
                <Input
                  id="board-icon"
                  value={form.icon}
                  onChange={(e) => setForm((f) => ({ ...f, icon: e.target.value }))}
                  placeholder="vd: megaphone"
                  maxLength={30}
                />
                <BoardIcon icon={form.icon} />
              </div>
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="board-sort">Thứ tự</Label>
              <Input
                id="board-sort"
                type="number"
                value={form.sortOrder}
                onChange={(e) =>
                  setForm((f) => ({ ...f, sortOrder: Number(e.target.value) || 0 }))
                }
              />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="board-status">Trạng thái</Label>
              <Select
                value={String(form.status)}
                onValueChange={(v) => setForm((f) => ({ ...f, status: Number(v) }))}
              >
                <SelectTrigger id="board-status" className="w-full">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value={String(FORUM_BOARD_STATUS.active)}>Đang mở</SelectItem>
                  <SelectItem value={String(FORUM_BOARD_STATUS.hidden)}>Đang ẩn</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </div>

        <DialogFooter>
          <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
            Hủy
          </Button>
          <Button
            type="button"
            disabled={!form.name.trim() || save.isPending}
            onClick={() => void submit()}
          >
            {save.isPending && <Loader2 className="size-4 animate-spin" />}
            {board ? 'Lưu' : 'Tạo'}
          </Button>
      </DialogFooter>
    </DialogContent>
  )
}
