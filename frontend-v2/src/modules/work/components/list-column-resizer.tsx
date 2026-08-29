import { useRef, type PointerEvent as ReactPointerEvent, type RefObject } from 'react'

import { columnWidthVar, MIN_COLUMN_WIDTH } from '../hooks/use-list-column-widths'

interface ListColumnResizerProps {
  columnKey: string
  /** Khung bao mang các biến CSS `--wcol-*` — sửa thẳng lên đây lúc kéo. */
  gridRef: RefObject<HTMLDivElement | null>
  onResize: (width: number) => void
}

/**
 * Vạch kéo giãn cột cho khung nhìn Danh sách.
 *
 * Không dùng lại `ColumnResizeHandle` của `shared/data-table` được: bản đó đi
 * tìm `closest('th')` và `closest('table')` để đo và để tự vừa nội dung, mà
 * bảng này dựng bằng div + flex nên không có thẻ nào như thế.
 *
 * Lúc kéo, bề rộng ghi thẳng vào **biến CSS** trên khung bao chứ không vào React
 * state: mọi ô của mọi dòng đọc chung biến ấy nên trình duyệt tự dàn lại, còn
 * `setState` mỗi nhịp chuột thì vẽ lại cả trăm dòng cho một cú kéo. State chỉ
 * được đụng tới lúc THẢ, cũng là lúc duy nhất ghi `localStorage`.
 */
export function ListColumnResizer({ columnKey, gridRef, onResize }: ListColumnResizerProps) {
  const dragRef = useRef<{ startX: number; startWidth: number; width: number } | null>(null)

  function currentWidth(): number {
    const grid = gridRef.current
    if (!grid) return MIN_COLUMN_WIDTH
    const raw = getComputedStyle(grid).getPropertyValue(columnWidthVar(columnKey))
    const value = Number.parseFloat(raw)
    return Number.isFinite(value) ? value : MIN_COLUMN_WIDTH
  }

  function handlePointerDown(event: ReactPointerEvent<HTMLDivElement>) {
    //  Chặn nổi bọt: vạch nằm trong hàng tiêu đề, để lọt lên thì cú kéo bị hiểu
    //  thành cú bấm vào tiêu đề.
    event.preventDefault()
    event.stopPropagation()

    event.currentTarget.setPointerCapture(event.pointerId)
    const startWidth = currentWidth()
    dragRef.current = { startX: event.clientX, startWidth, width: startWidth }
  }

  function handlePointerMove(event: ReactPointerEvent<HTMLDivElement>) {
    const drag = dragRef.current
    if (!drag) return

    const width = Math.max(MIN_COLUMN_WIDTH, drag.startWidth + event.clientX - drag.startX)
    drag.width = width
    gridRef.current?.style.setProperty(columnWidthVar(columnKey), `${width}px`)
  }

  function handlePointerUp(event: ReactPointerEvent<HTMLDivElement>) {
    const drag = dragRef.current
    dragRef.current = null
    if (!drag) return

    event.currentTarget.releasePointerCapture(event.pointerId)
    if (drag.width !== drag.startWidth) onResize(drag.width)
  }

  return (
    <div
      role="separator"
      aria-orientation="vertical"
      aria-label="Kéo để đổi độ rộng cột"
      title="Kéo để đổi độ rộng cột"
      onClick={(e) => e.stopPropagation()}
      onPointerDown={handlePointerDown}
      onPointerMove={handlePointerMove}
      onPointerUp={handlePointerUp}
      onPointerCancel={handlePointerUp}
      className="absolute inset-y-0 -right-1 z-10 w-2 cursor-col-resize touch-none select-none before:absolute before:inset-y-1 before:left-1/2 before:w-px before:-translate-x-1/2 before:bg-transparent group-hover/head:before:bg-border hover:before:bg-primary"
    />
  )
}
