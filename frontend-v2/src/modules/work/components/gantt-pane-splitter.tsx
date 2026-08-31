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
      className="w-1.5 shrink-0 cursor-col-resize touch-none bg-border/60 transition-colors hover:bg-primary"
    />
  )
}
