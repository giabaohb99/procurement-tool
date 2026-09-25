import { Ban, MoreHorizontal, Pencil, Users } from 'lucide-react'

import { Badge } from '@/shared/ui/badge'
import { Button } from '@/shared/ui/button'
import { confirm } from '@/shared/ui/confirm-dialog'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/shared/ui/dropdown-menu'
import { formatDate } from '@/shared/utils/format-date'
import { EFFECT, type DocumentAccess } from '../types/document-access'
import { AccessSubjectAvatar } from './access-subject-avatar'

interface DocumentShareAccessListProps {
  rows: DocumentAccess[]
  canWrite: boolean
  onEdit: (row: DocumentAccess) => void
  onRevoke: (row: DocumentAccess) => void
}

/** «xem · sửa · xóa» của một dòng cho phép. */
function describeRights(row: DocumentAccess): string {
  const rights = [row.can_read && 'Xem', row.can_write && 'Sửa', row.can_delete && 'Xóa'].filter(
    Boolean,
  )
  return rights.join(', ')
}

/**
 * Danh sách «Người có quyền riêng» trong hộp Chia sẻ văn bản — cùng khuôn
 * `folder-share-people-list.tsx` (khung viền, avatar, tên + dòng phụ, nhãn bên
 * phải) để hai hộp Chia sẻ nhìn như một.
 *
 * Chỉ dòng CÒN HIỆU LỰC — dòng đã thu hồi (kèm mốc + lý do) vẫn xem được ở
 * khối «Quyền truy cập» của trang chi tiết; nhét vào đây thì hộp chia sẻ thành
 * sổ lịch sử. Dòng CHẶN lên đầu: nó thắng mọi dòng cho phép.
 */
export function DocumentShareAccessList({
  rows,
  canWrite,
  onEdit,
  onRevoke,
}: DocumentShareAccessListProps) {
  const active = rows
    .filter((row) => row.is_active)
    .sort((a, b) => Number(b.effect === EFFECT.deny) - Number(a.effect === EFFECT.deny))

  if (active.length === 0) {
    return (
      <div className="flex flex-col items-center gap-1 rounded-md border border-dashed px-4 py-6 text-center">
        <Users className="mb-1 size-6 text-muted-foreground" />
        <p className="text-sm font-medium">Chưa chia riêng cho ai</p>
        <p className="text-xs text-muted-foreground">
          Hiện chỉ những người trong phạm vi vai trò mới xem được văn bản này.
        </p>
      </div>
    )
  }

  async function confirmRevoke(row: DocumentAccess) {
    const ok = await confirm({
      title: `Hủy quyền của ${row.subject_name}?`,
      message: 'Dòng này vẫn lưu trong lịch sử chia quyền ở trang văn bản.',
      confirmLabel: 'Hủy quyền',
    })
    if (ok) onRevoke(row)
  }

  return (
    <ul className="divide-y rounded-md border">
      {active.map((row) => {
        const name = row.subject_name || '(đã xóa)'
        const denied = row.effect === EFFECT.deny
        return (
          <li key={row.id} className="flex items-center gap-3 px-3 py-2">
            <AccessSubjectAvatar subjectKind={row.subject_kind} subjectName={name} />

            <div className="min-w-0 flex-1">
              <p className="truncate text-sm font-medium" title={name}>
                {name}
              </p>
              <p className="truncate text-xs text-muted-foreground">
                {row.subject_kind_label} ·{' '}
                {row.valid_to ? `Hết hạn ${formatDate(row.valid_to)}` : 'Không đặt hạn'}
                {row.reason && ` · ${row.reason}`}
              </p>
            </div>

            {denied ? (
              <Badge variant="destructive" className="shrink-0">
                <Ban className="size-3" />
                Chặn
              </Badge>
            ) : (
              <Badge variant="outline" className="shrink-0">
                {describeRights(row)}
              </Badge>
            )}

            {canWrite && (
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button
                    type="button"
                    variant="ghost"
                    size="icon-sm"
                    className="shrink-0"
                    aria-label={`Thao tác với quyền của ${name}`}
                  >
                    <MoreHorizontal />
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end">
                  <DropdownMenuItem onSelect={() => onEdit(row)}>
                    <Pencil className="size-4" />
                    Sửa quyền
                  </DropdownMenuItem>
                  <DropdownMenuItem variant="destructive" onSelect={() => void confirmRevoke(row)}>
                    <Ban className="size-4" />
                    Hủy quyền
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            )}
          </li>
        )
      })}
    </ul>
  )
}
