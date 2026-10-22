import { Loader2, RotateCcw, Trash2 } from 'lucide-react'

import { Button } from '@/shared/ui/button'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/shared/ui/dialog'
import { Skeleton } from '@/shared/ui/skeleton'
import { formatDateTime } from '@/shared/utils/format-date'
import { useRestoreTask, useWorkTrash } from '../hooks/use-work-trash'

interface WorkTrashDialogProps {
  open: boolean
  listId: number
  onClose: () => void
}

/**
 * Thùng rác của dự án (B-09): xem việc đã xóa và khôi phục.
 *
 * Quyền khôi phục do backend quyết (`can_restore` từng dòng) — quản trị khôi phục
 * mọi việc, thành viên chỉ việc mình tạo, dự án đã lưu trữ thì khóa. Giao diện chỉ
 * ẩn nút, không tự suy quyền.
 */
export function WorkTrashDialog({ open, listId, onClose }: WorkTrashDialogProps) {
  const { data, isLoading, isError } = useWorkTrash(listId, open)
  const restore = useRestoreTask(listId)
  const items = data ?? []

  return (
    <Dialog open={open} onOpenChange={(next) => !next && onClose()}>
      <DialogContent className="sm:max-w-xl">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Trash2 className="size-4" />
            Thùng rác
          </DialogTitle>
          <DialogDescription>
            Công việc đã xóa của dự án này. Khôi phục việc cha thì các việc con xóa cùng lúc cũng
            quay lại.
          </DialogDescription>
        </DialogHeader>

        {isLoading && <Skeleton className="h-24 w-full" />}
        {isError && (
          <p className="text-sm text-destructive">Không tải được thùng rác. Thử đóng rồi mở lại.</p>
        )}
        {!isLoading && !isError && items.length === 0 && (
          <p className="py-6 text-center text-sm text-muted-foreground">Thùng rác đang trống.</p>
        )}

        <ul className="max-h-96 divide-y overflow-y-auto">
          {items.map((item) => (
            <li key={item.id} className="flex items-center gap-3 py-2">
              <div className="min-w-0 flex-1">
                <p className="truncate text-sm font-medium" title={item.title}>
                  {item.title}
                </p>
                <p className="truncate text-xs text-muted-foreground">
                  {item.parent_id ? `Việc con của «${item.parent_title}» · ` : ''}
                  Xóa {formatDateTime(item.deleted_at)}
                  {item.deleted_by_name ? ` bởi ${item.deleted_by_name}` : ''}
                </p>
              </div>
              {item.can_restore && (
                <Button
                  variant="outline"
                  size="sm"
                  disabled={restore.isPending}
                  onClick={() => restore.mutate(item.id)}
                  aria-label={`Khôi phục ${item.title}`}
                >
                  {restore.isPending && restore.variables === item.id ? (
                    <Loader2 className="size-3.5 animate-spin" />
                  ) : (
                    <RotateCcw className="size-3.5" />
                  )}
                  Khôi phục
                </Button>
              )}
            </li>
          ))}
        </ul>
      </DialogContent>
    </Dialog>
  )
}
