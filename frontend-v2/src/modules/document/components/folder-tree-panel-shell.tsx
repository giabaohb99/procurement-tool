import { PanelLeftOpen } from 'lucide-react'

import { usePersistedToggle } from '@/shared/hooks/use-persisted-toggle'
import { useResizablePanel } from '@/shared/hooks/use-resizable-panel'
import { IconTooltip } from '@/shared/ui/icon-tooltip'
import { ResizeHandle } from '@/shared/ui/resize-handle'
import { FolderTreePanel, type FolderTreePanelProps } from './folder-tree-panel'

/**
 * Bề rộng cho phép của khung cây (spec §A: "200–480px, nhớ `localStorage`").
 * Sàn 200px: hẹp hơn thì tên thư mục cụt gần hết. Trần 480px: rộng hơn nữa ăn
 * hết chỗ khung nội dung bên phải, vốn mới là chỗ người dùng nhìn lâu nhất.
 */
const MIN_WIDTH = 200
const MAX_WIDTH = 480
const DEFAULT_WIDTH = 288

/**
 * Vỏ KÉO GIÃN + GẬP HẲN của `FolderTreePanel`, chỉ dùng ở khung desktop
 * (`document-folder-page.tsx`) — bản trong `Sheet` màn hẹp dùng thẳng
 * `FolderTreePanel`, không qua vỏ này (Sheet đã tự có bề rộng + nút đóng
 * riêng, kéo giãn/gập thêm một lớp nữa là thừa). Cùng khuôn với
 * `modules/assistant/components/conversation-sidebar.tsx` — nơi ĐẦU TIÊN
 * dùng `useResizablePanel`/`usePersistedToggle`/`ResizeHandle`.
 */
export function FolderTreePanelShell(props: FolderTreePanelProps) {
  const { width, startDrag, resizeByKey } = useResizablePanel({
    storageKey: 'erp.document.folders.tree-width',
    min: MIN_WIDTH,
    max: MAX_WIDTH,
    defaultValue: DEFAULT_WIDTH,
  })
  const [collapsed, toggleCollapsed] = usePersistedToggle('erp.document.folders.tree-collapsed')

  if (collapsed) {
    return (
      <aside className="hidden w-10 shrink-0 flex-col items-center border-r bg-card py-2 md:flex">
        <IconTooltip label="Mở lại khung thư mục" side="right">
          <button
            type="button"
            aria-label="Mở lại khung thư mục"
            onClick={toggleCollapsed}
            className="flex size-7 shrink-0 items-center justify-center rounded hover:bg-muted"
          >
            <PanelLeftOpen className="size-4" />
          </button>
        </IconTooltip>
      </aside>
    )
  }

  return (
    <aside
      className="relative hidden min-h-0 shrink-0 flex-col overflow-hidden border-r bg-card md:flex"
      style={{ width }}
    >
      <FolderTreePanel {...props} onCollapsePanel={toggleCollapsed} />
      <ResizeHandle
        label="Kéo để đổi bề ngang khung thư mục"
        width={width}
        min={MIN_WIDTH}
        max={MAX_WIDTH}
        onPointerDown={startDrag}
        onKeyResize={resizeByKey}
      />
    </aside>
  )
}
