import { useRef, type PointerEvent as ReactPointerEvent } from 'react'

interface ColumnResizeHandleProps {
  minWidth: number
  onResize: (width: number) => void
  /**
   * Báo cho ô tiêu đề biết đang kéo giãn để nó TẮT `draggable` — ô tiêu đề vừa
   * kéo thả đổi vị trí vừa kéo giãn, không tắt thì trình duyệt nuốt mất chuỗi
   * pointer event và biến cú kéo giãn thành cú kéo cả cột đi chỗ khác.
   */
  onResizingChange?: (resizing: boolean) => void
}

/**
 * Vạch kéo ở mép phải ô tiêu đề để chỉnh độ rộng cột.
 *
 * Dùng Pointer Events + `setPointerCapture`: chuột đi ra ngoài vạch, ra ngoài
 * cả cửa sổ vẫn nhận được sự kiện, nên không có cảnh "kéo hụt rồi cột kẹt".
 * Chỉ báo độ rộng mới ra ngoài khi THẢ chuột — cập nhật theo từng pixel sẽ ghi
 * localStorage hàng trăm lần cho một cú kéo.
 */
export function ColumnResizeHandle({
  minWidth,
  onResize,
  onResizingChange,
}: ColumnResizeHandleProps) {
  const dragRef = useRef<{ startX: number; startWidth: number; width: number } | null>(null)

  function handlePointerDown(event: ReactPointerEvent<HTMLDivElement>) {
    // Ngăn click lan lên <th> (kẻo trang lại hiểu là bấm vào tiêu đề để sắp xếp).
    event.preventDefault()
    event.stopPropagation()

    const handle = event.currentTarget
    // Đo độ rộng THẬT của ô lúc này thay vì tin vào prop: cột chưa khai `width`
    // hoặc đang bị bảng co giãn thì con số trong state không khớp thực tế.
    const startWidth = handle.closest('th')?.getBoundingClientRect().width ?? minWidth

    handle.setPointerCapture(event.pointerId)
    dragRef.current = { startX: event.clientX, startWidth, width: startWidth }
    onResizingChange?.(true)
  }

  function handlePointerMove(event: ReactPointerEvent<HTMLDivElement>) {
    const drag = dragRef.current
    if (!drag) return

    const width = Math.max(minWidth, drag.startWidth + event.clientX - drag.startX)
    drag.width = width

    // Sửa thẳng DOM trong lúc kéo để mượt, không đụng tới React state.
    const cell = event.currentTarget.closest('th')
    if (cell) cell.style.width = `${width}px`
  }

  function handlePointerUp(event: ReactPointerEvent<HTMLDivElement>) {
    const drag = dragRef.current
    dragRef.current = null
    onResizingChange?.(false)
    if (!drag) return

    event.currentTarget.releasePointerCapture(event.pointerId)
    if (drag.width !== drag.startWidth) onResize(drag.width)
  }

  return (
    <div
      role="separator"
      aria-orientation="vertical"
      aria-label="Kéo để đổi độ rộng cột"
      onPointerDown={handlePointerDown}
      onPointerMove={handlePointerMove}
      onPointerUp={handlePointerUp}
      onPointerCancel={handlePointerUp}
      className="absolute inset-y-0 -right-1 z-10 w-2 cursor-col-resize touch-none select-none before:absolute before:inset-y-1 before:left-1/2 before:w-px before:-translate-x-1/2 before:bg-transparent hover:before:bg-primary"
    />
  )
}
