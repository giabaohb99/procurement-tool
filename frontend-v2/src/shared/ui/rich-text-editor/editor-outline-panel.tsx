import type { Editor } from '@tiptap/react'
import { useRef } from 'react'

import { EditorOutline } from './editor-outline'

/** Khoảng bề ngang cho phép của cột mục lục (px). */
const MIN_WIDTH = 160
const MAX_WIDTH = 420

interface EditorOutlinePanelProps {
  editor: Editor
  width: number
  onWidthChange: (width: number) => void
}

/**
 * Cột MỤC LỤC kèm thanh kéo giãn ở viền phải.
 *
 * Kéo được vì tiêu đề công văn dài ngắn thất thường: cột hẹp thì tiêu đề nào
 * cũng bị cắt cụt thành "Về việc tạm ứng chi phí…", mà để rộng sẵn thì tờ giấy
 * bị đẩy lệch khỏi giữa màn hình.
 *
 * Chỉ hiện từ màn `lg` trở lên — màn hẹp mà cắt thêm một cột nữa thì trang giấy
 * không còn chỗ.
 */
export function EditorOutlinePanel({ editor, width, onWidthChange }: EditorOutlinePanelProps) {
  const startRef = useRef<{ x: number; width: number } | null>(null)

  function startDrag(event: React.PointerEvent) {
    event.preventDefault()
    startRef.current = { x: event.clientX, width }

    const move = (moveEvent: PointerEvent) => {
      const start = startRef.current
      if (!start) return
      const next = start.width + (moveEvent.clientX - start.x)
      onWidthChange(Math.min(Math.max(next, MIN_WIDTH), MAX_WIDTH))
    }

    const stop = () => {
      startRef.current = null
      window.removeEventListener('pointermove', move)
      window.removeEventListener('pointerup', stop)
    }

    window.addEventListener('pointermove', move)
    window.addEventListener('pointerup', stop)
  }

  return (
    <div className="relative hidden shrink-0 lg:block" style={{ width }}>
      <EditorOutline
        editor={editor}
        className="max-h-[calc(100vh-16rem)] w-full overflow-y-auto border-r"
      />

      {/* Thanh kéo nằm ĐÈ lên viền phải, rộng hơn viền vài px cho dễ bắt chuột —
          viền 1px thì phải căn tay mới trúng. */}
      <div
        role="separator"
        aria-orientation="vertical"
        aria-label="Kéo để đổi bề ngang mục lục"
        onPointerDown={startDrag}
        className="absolute inset-y-0 -right-1 w-2 cursor-col-resize hover:bg-primary/20"
      />
    </div>
  )
}
