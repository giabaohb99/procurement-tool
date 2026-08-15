import { useCallback, useRef, useState, type PointerEvent as ReactPointerEvent } from 'react'

import type { ColumnDropSide } from './types'

/** Đi quá ngần này pixel mới tính là kéo — dưới đó vẫn là một cú bấm. */
const DRAG_THRESHOLD = 4

export interface ColumnDragState {
  fromKey: string
  /** Nhãn hiện trên "viên" bám theo con trỏ. */
  label: string
  /** Cột đang trỏ tới và sẽ chèn vào trước/sau nó. */
  overKey: string | null
  side: ColumnDropSide | null
  x: number
  y: number
}

/**
 * Kéo thả đổi thứ tự cột bằng POINTER EVENT, không dùng HTML5 drag-and-drop.
 *
 * HTML5 DnD để trình duyệt tự chụp ảnh ô tiêu đề làm ảnh kéo, ảnh đó nhòe và trễ
 * một nhịp so với con trỏ; lại còn xung khắc với vạch kéo giãn nằm cùng ô. Pointer
 * event cho phép tự vẽ chỉ báo, chạy mượt theo từng khung hình và dùng được trên
 * cảm ứng — cùng cơ chế với `column-resize-handle.tsx`.
 */
export function useColumnDrag(
  onReorder: (fromKey: string, toKey: string, side: ColumnDropSide) => void,
) {
  const [drag, setDrag] = useState<ColumnDragState | null>(null)
  const dragRef = useRef<ColumnDragState | null>(null)

  const startDrag = useCallback(
    (event: ReactPointerEvent<HTMLTableCellElement>, key: string, label: string) => {
      // Chỉ chuột trái; bấm trúng vạch kéo giãn thì đó là đổi ĐỘ RỘNG.
      if (event.button !== 0) return
      if ((event.target as HTMLElement).closest('[role="separator"]')) return

      const row = event.currentTarget.closest('tr')
      if (!row) return

      const startX = event.clientX
      let moved = false

      const handleMove = (moveEvent: PointerEvent) => {
        if (!moved && Math.abs(moveEvent.clientX - startX) < DRAG_THRESHOLD) return
        if (!moved) {
          moved = true
          // Kéo ngang qua cả bảng mà không bôi đen chữ trong ô tiêu đề.
          document.body.classList.add('select-none', 'cursor-grabbing')
        }

        const target = columnUnder(row, moveEvent.clientX)
        const next: ColumnDragState = {
          fromKey: key,
          label,
          overKey: target?.key ?? null,
          side: target?.side ?? null,
          x: moveEvent.clientX,
          y: moveEvent.clientY,
        }
        dragRef.current = next
        setDrag(next)
      }

      const handleUp = () => {
        window.removeEventListener('pointermove', handleMove)
        window.removeEventListener('pointerup', handleUp)
        window.removeEventListener('pointercancel', handleUp)
        document.body.classList.remove('select-none', 'cursor-grabbing')

        const finished = dragRef.current
        dragRef.current = null
        setDrag(null)

        if (finished?.overKey && finished.side && finished.overKey !== finished.fromKey) {
          onReorder(finished.fromKey, finished.overKey, finished.side)
        }
      }

      window.addEventListener('pointermove', handleMove)
      window.addEventListener('pointerup', handleUp)
      window.addEventListener('pointercancel', handleUp)
    },
    [onReorder],
  )

  return { drag, startDrag }
}

/**
 * Cột nằm dưới hoành độ `x`, kèm việc sẽ chèn vào nửa trái (before) hay nửa phải
 * (after). Ra ngoài hai mép bảng thì bám vào cột đầu / cột cuối để thả ở rìa vẫn ăn.
 */
function columnUnder(
  row: Element,
  x: number,
): { key: string; side: ColumnDropSide } | null {
  const cells = [...row.querySelectorAll<HTMLElement>('th[data-column-key]')]
  if (cells.length === 0) return null

  for (const cell of cells) {
    const box = cell.getBoundingClientRect()
    if (x < box.left || x > box.right) continue
    return {
      key: cell.dataset.columnKey as string,
      side: x < box.left + box.width / 2 ? 'before' : 'after',
    }
  }

  const first = cells[0].getBoundingClientRect()
  if (x < first.left) return { key: cells[0].dataset.columnKey as string, side: 'before' }

  const last = cells[cells.length - 1]
  return { key: last.dataset.columnKey as string, side: 'after' }
}
