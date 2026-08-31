import { useRef, type PointerEvent as ReactPointerEvent, type RefObject } from 'react'

import { columnWidthVar, MIN_COLUMN_WIDTH } from '../hooks/use-list-column-widths'

interface ListColumnResizerProps {
  columnKey: string
  /** Khung bao mang các biến CSS `--wcol-*` — sửa thẳng lên đây lúc kéo. */
  gridRef: RefObject<HTMLDivElement | null>
  /** Chặn dưới của CHÍNH cột này — cột tên rộng hơn hẳn các cột chip. */
  minWidth?: number
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
export function ListColumnResizer({
  columnKey,
  gridRef,
  minWidth = MIN_COLUMN_WIDTH,
  onResize,
}: ListColumnResizerProps) {
  const dragRef = useRef<{ startX: number; startWidth: number; width: number } | null>(null)

  function currentWidth(): number {
    const grid = gridRef.current
    if (!grid) return minWidth
    const raw = getComputedStyle(grid).getPropertyValue(columnWidthVar(columnKey))
    const value = Number.parseFloat(raw)
    return Number.isFinite(value) ? value : minWidth
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

    const width = Math.max(minWidth, drag.startWidth + event.clientX - drag.startX)
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
      /*  Vùng bắt CAO HƠN ô tiêu đề (`-inset-y-2.5` ăn ra đúng `py-2.5` của
          hàng) và RỘNG 12px thay vì 8px.

          Bản đầu bám `inset-y-0` nên chỉ cao bằng dòng chữ — 16px trong một hàng
          28px — nghĩa là muốn kéo giãn cột thì phải đoán trúng một dải 8×16px:
          chức năng có mà người dùng báo "không có". Vùng bắt nay cao hết hàng.

          Còn NÉT KẺ thì ẩn cho tới khi rê chuột vào hàng tiêu đề: kẻ sẵn đủ 6-7
          vạch dọc là hàng tiêu đề nhìn như một cái bảng lưới, ồn hơn hẳn phần
          thân vốn chỉ có vạch ngang mảnh. Rê vào hàng mới hiện vạch mờ (chỉ ra
          rằng có chỗ để kéo), rê trúng vạch thì nó dày lên và đổi màu nhấn.  */
      className="absolute -inset-y-2.5 -right-1.5 z-10 w-3 cursor-col-resize touch-none select-none before:absolute before:inset-y-1 before:left-1/2 before:w-px before:-translate-x-1/2 before:rounded-full before:bg-transparent before:transition-all group-hover/head:before:bg-border hover:before:w-0.5 hover:before:bg-primary"
    />
  )
}
