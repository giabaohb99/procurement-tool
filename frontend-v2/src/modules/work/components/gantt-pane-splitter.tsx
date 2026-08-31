import { useRef, type PointerEvent as ReactPointerEvent } from 'react'

interface GanttPaneSplitterProps {
  width: number
  maxWidth: number
  onResize: (width: number) => void
}

/**
 * Thanh CHIA ĐÔI giữa lưới trái và trục thời gian — kéo để đổi phần chia màn
 * hình, đúng lối DHTMLX.
 *
 * Nằm trong CÙNG khối dính bên trái với lưới (xem `gantt-view.tsx`), nên cuộn
 * sang tháng sau nó vẫn ở đó — trôi mất thì không còn cách nào kéo lại.
 *
 * Kéo thì ghi thẳng vào biến CSS của chính ô chứa (`--gantt-pane`), state chỉ
 * đụng tới lúc THẢ — giống `ListColumnResizer`, và vì lý do y hệt: mỗi nhịp
 * chuột mà `setState` là cả biểu đồ vẽ lại, kéo thành giật.
 */
export function GanttPaneSplitter({ width, maxWidth, onResize }: GanttPaneSplitterProps) {
  const dragRef = useRef<{ startX: number; startWidth: number; width: number } | null>(null)

  function handlePointerDown(event: ReactPointerEvent<HTMLDivElement>) {
    event.preventDefault()
    event.stopPropagation()
    event.currentTarget.setPointerCapture(event.pointerId)
    dragRef.current = { startX: event.clientX, startWidth: width, width }
  }

  function handlePointerMove(event: ReactPointerEvent<HTMLDivElement>) {
    const drag = dragRef.current
    if (!drag) return
    const next = Math.min(maxWidth, Math.max(160, drag.startWidth + event.clientX - drag.startX))
    drag.width = next
    //  Ô chứa lưới là ANH TRƯỚC của thanh này; sửa thẳng biến trên nó để cả hai
    //  bên dàn lại ngay trong lúc kéo.
    const pane = event.currentTarget.previousElementSibling
    if (pane instanceof HTMLElement) pane.style.width = `${next}px`
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
      aria-label="Kéo để đổi bề rộng lưới công việc"
      title="Kéo để đổi bề rộng lưới công việc"
      onPointerDown={handlePointerDown}
      onPointerMove={handlePointerMove}
      onPointerUp={handlePointerUp}
      onPointerCancel={handlePointerUp}
      /*  ⚠️ `z-50` — phải CAO HƠN cả hai hàng tiêu đề (tiêu đề trục `z-40`, tiêu
           đề lưới trái `z-20`). Nét đậm khi rê chuột vẽ đè ra hai bên, mà hai
           hàng ấy đứng sau trong cây và có z-index nên chúng che mất hai pixel
           tràn: ở dải tiêu đề nét chỉ còn 1px trong khi phần thân dày 3px, nhìn
           như thanh chia bị hụt mất một khúc trên đầu.  */
      className="group/splitter relative z-50 w-px shrink-0 cursor-col-resize touch-none bg-border"
    >
      {/*  VÙNG BẮT CHUỘT rộng 9px, trong suốt và đè ra hai bên. Nét vẽ chỉ 1px
           thì gần như không rê trúng; mà nới nét cho dễ bắt thì nó thành một
           thanh xám 6px chạy dọc giữa màn hình — khách chê đúng chỗ này.
           Sự kiện nổi bọt lên thẻ cha nên bộ xử lý kéo vẫn nguyên. */}
      <span aria-hidden className="absolute inset-y-0 -right-1 -left-1" />

      {/*  Nét ĐẬM khi rê chuột — báo "kéo được". Vẽ ĐÈ ra hai bên
           (`-inset-x-px`) chứ không nới bề rộng thẻ: nới thì cả lưới trái lẫn
           trục dịch đi 2px mỗi lần con trỏ quét ngang qua. */}
      <span
        aria-hidden
        className="pointer-events-none absolute inset-y-0 -right-px -left-px bg-primary opacity-0 transition-opacity group-hover/splitter:opacity-100"
      />
    </div>
  )
}
