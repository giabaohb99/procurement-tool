import { MessageSquarePlus, Trash2 } from 'lucide-react'

import { Button } from '@/shared/ui/button'
import { ConfirmIconButton } from '@/shared/ui/confirm-icon-button'
import { Skeleton } from '@/shared/ui/skeleton'
import { cn } from '@/shared/utils/cn'
import { formatDateTime } from '@/shared/utils/format-date'
import type { ConversationSummary } from '../types/assistant'

interface ConversationSidebarProps {
  items: ConversationSummary[]
  activeId: number
  loading: boolean
  onNew: () => void
  onSelect: (id: number) => void
  onDelete: (id: number) => void
}

/** Cột trái: nút mở hội thoại mới + danh sách hội thoại đã lưu. */
export function ConversationSidebar({
  items,
  activeId,
  loading,
  onNew,
  onSelect,
  onDelete,
}: ConversationSidebarProps) {
  return (
    <div className="flex w-64 shrink-0 flex-col border-r">
      <div className="p-3">
        <Button className="w-full" onClick={onNew}>
          <MessageSquarePlus className="size-4" />
          Hội thoại mới
        </Button>
      </div>

      <div className="min-h-0 flex-1 overflow-y-auto px-2 pb-3">
        {loading ? (
          <div className="space-y-2 px-1">
            <Skeleton className="h-12 w-full" />
            <Skeleton className="h-12 w-full" />
            <Skeleton className="h-12 w-full" />
          </div>
        ) : items.length === 0 ? (
          <p className="px-2 py-6 text-center text-sm text-muted-foreground">
            Chưa có hội thoại nào. Đặt câu hỏi đầu tiên ở khung bên phải.
          </p>
        ) : (
          <ul className="space-y-1">
            {items.map((conv) => {
              const active = conv.id === activeId
              return (
                <li key={conv.id}>
                  <div
                    className={cn(
                      'group flex items-center gap-1 rounded-md pr-1 transition-colors',
                      active ? 'bg-accent' : 'hover:bg-accent/50',
                    )}
                  >
                    <button
                      type="button"
                      onClick={() => onSelect(conv.id)}
                      className="min-w-0 flex-1 rounded-md px-2 py-2 text-left"
                    >
                      <p className="truncate text-sm font-medium text-navy">{conv.title}</p>
                      <p className="truncate text-xs text-muted-foreground">
                        {formatDateTime(conv.last_message_at)}
                      </p>
                    </button>
                    <div className="opacity-0 transition-opacity group-hover:opacity-100">
                      <ConfirmIconButton
                        icon={Trash2}
                        title="Xóa hội thoại"
                        confirmTitle="Xóa hội thoại này?"
                        confirmDescription="Toàn bộ câu hỏi và trả lời trong hội thoại sẽ bị xóa vĩnh viễn."
                        confirmLabel="Xóa"
                        destructive
                        onConfirm={() => onDelete(conv.id)}
                      />
                    </div>
                  </div>
                </li>
              )
            })}
          </ul>
        )}
      </div>
    </div>
  )
}
