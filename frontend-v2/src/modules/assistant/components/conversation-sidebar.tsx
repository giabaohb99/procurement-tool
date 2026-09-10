import { PanelLeftClose, PanelLeftOpen, SquarePen } from 'lucide-react'

import { usePersistedToggle } from '@/shared/hooks/use-persisted-toggle'
import { useResizablePanel } from '@/shared/hooks/use-resizable-panel'
import { ResizeHandle } from '@/shared/ui/resize-handle'
import { ConversationList, type ConversationListProps } from './conversation-list'

/**
 * Khoảng bề rộng cho phép của cột hội thoại.
 *
 * Sàn 200px: hẹp hơn thì tiêu đề nào cũng cụt thành "Hợp đồng nhà cung…", cột
 * hết tác dụng. Trần 420px: rộng hơn nữa là ăn vào cột đọc bên phải, mà cột đọc
 * mới là chỗ người ta nhìn lâu nhất.
 */
const MIN_WIDTH = 200
const MAX_WIDTH = 420
const DEFAULT_VALUE = 256

type ConversationSidebarProps = Omit<ConversationListProps, 'trailing'>

/**
 * Cột hội thoại bên trái — **chỉ dựng từ `md`**.
 *
 * ⚠️ **Ở khổ điện thoại cột này KHÔNG được đứng cạnh khung chat.** Nó rộng cố
 * định 256px (`shrink-0`), nên trên máy 390px phần chat chỉ còn ~130px: câu trả
 * lời rớt xuống **mỗi dòng một từ**, ô nhập co thành một ô vuông, và dòng hướng
 * dẫn dưới ô nhập vỡ thành một cột chữ dọc (khách báo 10/09/2026). Danh sách
 * hội thoại ở khổ đó đi bằng tờ trượt — xem `ConversationSheet`.
 *
 * **Kéo giãn** ở mép phải và **thu gọn** bằng nút ở đầu cột. Tiêu đề hội thoại
 * do model tự đặt nên dài ngắn thất thường: cột cố định thì quá nửa số dòng bị
 * cắt cụt, mà để rộng sẵn cho mọi trường hợp thì ngày thường phí một mảng màn
 * hình. Cả bề rộng lẫn trạng thái thu gọn đều nhớ vào `localStorage`.
 */
export function ConversationSidebar(props: ConversationSidebarProps) {
  const { width, startDrag, resizeByKey } = useResizablePanel({
    storageKey: 'erp.assistant-sidebar-width',
    min: MIN_WIDTH,
    max: MAX_WIDTH,
    defaultValue: DEFAULT_VALUE,
  })
  const [collapsed, toggleCollapsed] = usePersistedToggle('erp.assistant-sidebar-collapsed')

  /**
   * Thu gọn thì còn một THANH HẸP, không biến mất hẳn.
   *
   * Ẩn sạch thì nút mở lại phải đi nhờ chỗ khác trên trang — người dùng thu gọn
   * xong không biết bấm đâu để lấy lại. Thanh hẹp giữ đúng hai việc hay dùng
   * nhất: mở lại cột, và mở hội thoại mới.
   */
  if (collapsed) {
    return (
      <aside className="hidden w-12 shrink-0 flex-col items-center gap-1 border-r bg-card py-2 md:flex">
        <IconButton
          icon={PanelLeftOpen}
          label="Mở lại cột hội thoại"
          onClick={toggleCollapsed}
        />
        <IconButton icon={SquarePen} label="Hội thoại mới" onClick={props.onNew} />
      </aside>
    )
  }

  return (
    <aside
      className="relative hidden shrink-0 flex-col border-r bg-card md:flex"
      style={{ width }}
    >
      <ConversationList
        {...props}
        trailing={
          <IconButton
            icon={PanelLeftClose}
            label="Thu gọn cột hội thoại"
            onClick={toggleCollapsed}
          />
        }
      />

      <ResizeHandle
        label="Kéo để đổi bề ngang cột hội thoại"
        width={width}
        min={MIN_WIDTH}
        max={MAX_WIDTH}
        onPointerDown={startDrag}
        onKeyResize={resizeByKey}
      />
    </aside>
  )
}

/** Nút chỉ có biểu tượng — nhãn nằm ở `aria-label` và `title`. */
function IconButton({
  icon: Icon,
  label,
  onClick,
}: {
  icon: typeof SquarePen
  label: string
  onClick: () => void
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      title={label}
      aria-label={label}
      className="flex size-8 shrink-0 items-center justify-center rounded-lg text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
    >
      <Icon className="size-4" />
    </button>
  )
}
