import { SquarePen, Trash2 } from 'lucide-react'

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
 * Dựng theo mẫu khách đưa (26/08/2026). Ba điều đổi so với bản trước và đều là
 * để **nhìn được nhiều hội thoại hơn trong một tầm mắt**:
 *
 *  - **Mỗi hội thoại một DÒNG**, chỉ có tiêu đề. Bản trước in thêm mốc thời gian
 *    xuống dòng dưới, tức là mỗi mục chiếm gấp đôi chỗ để nói một thứ người dùng
 *    hiếm khi cần — họ tìm theo NỘI DUNG đã hỏi, không tìm theo giờ. Mốc thời
 *    gian không mất hẳn: nó nằm ở `title` (rê chuột vào là thấy).
 *  - **«Hội thoại mới» là một hàng có biểu tượng**, không phải nút viền. Trong
 *    màn này thứ đáng nổi bật nhất là ô nhập câu hỏi bên phải.
 *  - **Nền trắng như phần đọc**, chỉ hàng đang chọn / rê chuột mới có nền chìm.
 *    Cả cột nền xám thì hàng đang chọn phải tô đậm hơn nữa mới nổi lên được.
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
    <aside className="flex w-64 shrink-0 flex-col border-r bg-card">
      <div className="p-2">
        <button
          type="button"
          onClick={onNew}
          className="flex w-full items-center gap-2.5 rounded-lg px-3 py-2 text-sm font-medium text-foreground transition-colors hover:bg-muted"
        >
          <SquarePen className="size-4 shrink-0 text-muted-foreground" />
          Hội thoại mới
        </button>
      </div>

      <div className="min-h-0 flex-1 overflow-y-auto px-2 pb-3">
        <p className="px-3 pt-2 pb-1 text-xs font-medium text-muted-foreground">Gần đây</p>

        {loading ? (
          <div className="space-y-1 px-1">
            <Skeleton className="h-8 w-full" />
            <Skeleton className="h-8 w-full" />
            <Skeleton className="h-8 w-full" />
          </div>
        ) : items.length === 0 ? (
          <p className="px-3 py-4 text-xs text-muted-foreground">Chưa có hội thoại nào.</p>
        ) : (
          <ul>
            {items.map((conv) => {
              const active = conv.id === activeId
              return (
                <li key={conv.id}>
                  <div
                    className={cn(
                      'group flex items-center rounded-lg pr-1 transition-colors',
                      active ? 'bg-muted' : 'hover:bg-muted/70',
                    )}
                  >
                    <button
                      type="button"
                      onClick={() => onSelect(conv.id)}
                      //  Mốc thời gian dồn vào đây thay vì chiếm một dòng riêng.
                      title={`${conv.title}\n${formatDateTime(conv.last_message_at)}`}
                      aria-current={active}
                      className={cn(
                        'min-w-0 flex-1 truncate rounded-lg px-3 py-2 text-left text-sm',
                        active ? 'font-medium text-navy' : 'text-foreground',
                      )}
                    >
                      {conv.title}
                    </button>

                    {/*  Nút xóa chỉ hiện khi rê chuột — bày sẵn vài chục cái
                         thùng rác trong một cột hẹp thì rối, mà đây lại là thao
                         tác không hoàn tác được. */}
                    <div className="shrink-0 opacity-0 transition-opacity group-hover:opacity-100 focus-within:opacity-100">
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
