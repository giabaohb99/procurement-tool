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
  /**
   * Chiều cao ĐO THẬT của khung soạn thảo, để cột mục lục cao đúng bằng tờ giấy.
   *
   * ⚠️ Trước đây cột này khai `max-h-[calc(100vh-16rem)]` — đúng cái hằng số mà
   * `use-fill-viewport-height.ts` sinh ra để thay thế, nhưng hồi đó chỉ đổi cho
   * khung giấy và **bỏ quên cột mục lục**. Hậu quả đo được trên văn bản 800
   * chương: cột bắt đầu ở 354px, `16rem` = 256px nên nó tự cho mình 525px trong
   * khi chỗ trống chỉ có 415px — đáy cột nằm ở 879px, **thò xuống dưới đáy cửa
   * sổ 98px**, mục cuối bị cắt và không cuộn tới được.
   */
  maxHeight?: number
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
export function EditorOutlinePanel({
  editor,
  width,
  onWidthChange,
  maxHeight,
}: EditorOutlinePanelProps) {
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
      {/*  Cao ĐÚNG BẰNG khung giấy bên cạnh — xem `maxHeight`. Giữ lại
           `calc(100vh-16rem)` làm nhánh lùi cho nơi chưa truyền số đo (ô rich
           text trong hộp thoại), nhưng trang soạn thảo luôn truyền. */}
      <EditorOutline
        editor={editor}
        style={maxHeight ? { height: maxHeight } : undefined}
        className={
          maxHeight
            ? 'w-full overflow-y-auto border-r'
            : 'max-h-[calc(100vh-16rem)] w-full overflow-y-auto border-r'
        }
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
