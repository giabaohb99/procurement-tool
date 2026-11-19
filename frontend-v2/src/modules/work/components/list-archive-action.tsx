import { Archive, ArchiveRestore } from 'lucide-react'
import { useState } from 'react'

import { Button } from '@/shared/ui/button'

import { useArchiveWorkList, useUpdateWorkList } from '../hooks/use-work-lists'
import type { WorkList } from '../types/work'

interface ListArchiveActionProps {
  list: WorkList
  /** Lưu trữ xong — hộp Quản lý đóng lại và đưa người dùng về danh sách dự án (dự án vừa lưu trữ biến khỏi cây). */
  onArchived: () => void
}

/**
 * Nút "Lưu trữ dự án" / "Khôi phục dự án" ở chân hộp Quản lý dự án — chỉ chủ dự án thấy (duoc-CR-783).
 *
 * Anh Được báo 19/11/2026: tạo dự án con xong không thấy chỗ xóa. Đường API lưu trữ (`DELETE /api/work/lists/{id}`) và
 * hook `useArchiveWorkList` có sẵn từ lâu nhưng chưa màn nào gắn nút. "Xóa" dự án là LƯU TRỮ (A-01): việc bên trong còn
 * nguyên, bật nút "Lưu trữ" ở màn Dự án là thấy lại và khôi phục được. Hỏi lại một lần ngay tại chỗ, cùng khuôn hộp nhóm.
 */
export function ListArchiveAction({ list, onArchived }: ListArchiveActionProps) {
  const archive = useArchiveWorkList()
  const restore = useUpdateWorkList()
  const [confirming, setConfirming] = useState(false)

  if (list.is_archived === 1) {
    return (
      <Button
        variant="ghost"
        size="sm"
        disabled={restore.isPending}
        onClick={() => restore.mutate({ id: list.id, values: { is_archived: 0 } })}
      >
        <ArchiveRestore className="size-4" />
        Khôi phục dự án
      </Button>
    )
  }

  if (confirming) {
    return (
      <span className="flex flex-wrap items-center gap-2 text-sm">
        <span className="text-muted-foreground">Đưa dự án này vào lưu trữ? Việc bên trong vẫn giữ nguyên.</span>
        <Button
          variant="destructive"
          size="sm"
          disabled={archive.isPending}
          onClick={() => archive.mutate(list.id, { onSuccess: onArchived })}
        >
          Đưa vào lưu trữ
        </Button>
        <Button variant="ghost" size="sm" onClick={() => setConfirming(false)}>
          Thôi
        </Button>
      </span>
    )
  }

  return (
    <Button variant="ghost" size="sm" onClick={() => setConfirming(true)}>
      <Archive className="size-4" />
      Đưa vào lưu trữ
    </Button>
  )
}
