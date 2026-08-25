import { Plus, Trash2 } from 'lucide-react'

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

/**
 * Cột trái: mở hội thoại mới + danh sách hội thoại đã lưu.
 *
 * Nền chìm (`bg-muted/40`) để tách khỏi cột đọc màu trắng bên phải — mắt nhận
 * ra ngay đâu là chỗ điều hướng, đâu là chỗ đọc. Nút «Hội thoại mới» để dạng
 * viền mảnh chứ không phải nút xanh đặc: trong màn này thứ đáng nổi bật nhất là
 * ô nhập câu hỏi, không phải nút mở hội thoại.
 */
export function ConversationSidebar({
  items,
  activeId,
  loading,
  onNew,
  onSelect,
  onDelete,
}: ConversationSidebarProps) {
  return (
    <aside className="flex w-64 shrink-0 flex-col border-r bg-muted/40">
      <div className="p-3">
        <button
          type="button"
          onClick={onNew}
          className="flex w-full items-center gap-2 rounded-lg border bg-card px-3 py-2 text-sm font-medium text-navy transition-colors hover:border-primary/40 hover:bg-accent"
        >
          <Plus className="size-4 text-primary" />
          Hội thoại mới
        </button>
      </div>

      <div className="min-h-0 flex-1 overflow-y-auto px-2 pb-3">
        {loading ? (
          <div className="space-y-1.5 px-1">
            <Skeleton className="h-11 w-full" />
            <Skeleton className="h-11 w-full" />
            <Skeleton className="h-11 w-full" />
          </div>
        ) : items.length === 0 ? (
          <p className="px-3 py-6 text-center text-xs text-muted-foreground">
            Chưa có hội thoại nào.
          </p>
        ) : (
          <ul className="space-y-0.5">
            {items.map((conv) => {
              const active = conv.id === activeId
              return (
                <li key={conv.id}>
                  <div
                    className={cn(
                      'group flex items-center gap-1 rounded-lg pr-1 transition-colors',
                      active ? 'bg-card shadow-sm' : 'hover:bg-card/70',
                    )}
                  >
                    <button
                      type="button"
                      onClick={() => onSelect(conv.id)}
                      className="min-w-0 flex-1 rounded-lg px-3 py-2 text-left"
                    >
                      <p
                        className={cn(
                          'truncate text-sm',
                          active ? 'font-medium text-navy' : 'text-foreground',
                        )}
                      >
                        {conv.title}
                      </p>
                      <p className="truncate text-xs text-muted-foreground">
                        {formatDateTime(conv.last_message_at)}
                      </p>
                    </button>

                    {/*  Nút xóa chỉ hiện khi rê chuột — bày sẵn 20 cái thùng rác
                         trong một cột hẹp thì rối, mà đây lại là thao tác không
                         hoàn tác được. */}
                    <div className="opacity-0 transition-opacity group-hover:opacity-100 focus-within:opacity-100">
                      <ConfirmIconButton
                        icon={Trash2}
                        title="Xóa hội thoại"
                        confirmTitle="Xóa hội thoại này?"
                        confirmDescription="Toàn bộ câu hỏi và trả lời trong hội thoại sẽ bị xóa vĩnh viễn."
                        confirmLabel="Xóa hội thoại"
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
    </aside>
  )
}
