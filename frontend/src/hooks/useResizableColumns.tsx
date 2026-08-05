import { useCallback, useRef, useState } from 'react'

/**
 * Hook kéo giãn độ rộng cột cho bảng HTML thuần.
 * - Lưu độ rộng vào localStorage theo `key` (nhớ cho lần sau).
 * - `id` của cột: nên dùng KEY của cột (bền khi ẩn/hiện cột); bảng cũ có thể dùng index.
 *
 * Dùng:
 *   const { startResize, thStyle, colW } = useResizableColumns('colw:xxx')
 *   // Bảng table-layout auto: gắn thStyle(id) vào <th>, đặt <ResizeHandle> bên trong <th>
 *   // Bảng table-layout fixed: dùng colW(id, mặc_định) cho width của <col>
 */
export type ColumnWidths = Record<string, number>

const MIN_WIDTH = 48

function loadWidths(key: string): ColumnWidths {
  try {
    const raw = localStorage.getItem(key)
    return raw ? JSON.parse(raw) : {}
  } catch {
    return {}
  }
}

export function useResizableColumns(key: string) {
  const [widths, setWidths] = useState<ColumnWidths>(() => loadWidths(key))
  const ref = useRef<ColumnWidths>(widths)
  ref.current = widths

  const startResize = useCallback((id: string | number, e: React.MouseEvent) => {
    e.preventDefault()
    e.stopPropagation()   // tránh kích hoạt sort khi kéo giãn cột
    const col = String(id)
    const handle = e.currentTarget as HTMLElement
    const th = handle.closest('th') as HTMLElement | null
    const startX = e.clientX
    const startW = th ? th.offsetWidth : (ref.current[col] || 120)

    function onMove(ev: MouseEvent) {
      const w = Math.max(MIN_WIDTH, startW + (ev.clientX - startX))
      const next = { ...ref.current, [col]: w }
      ref.current = next
      setWidths(next)
    }
    function onUp() {
      document.removeEventListener('mousemove', onMove)
      document.removeEventListener('mouseup', onUp)
      document.body.style.cursor = ''
      document.body.style.userSelect = ''
      try { localStorage.setItem(key, JSON.stringify(ref.current)) } catch { /* bỏ qua */ }
    }
    document.addEventListener('mousemove', onMove)
    document.addEventListener('mouseup', onUp)
    document.body.style.cursor = 'col-resize'
    document.body.style.userSelect = 'none'
  }, [key])

  // Cho bảng table-layout auto: width gợi ý trên <th>
  const thStyle = useCallback((id: string | number): React.CSSProperties | undefined => {
    const w = widths[String(id)]
    return w ? { width: w, minWidth: w } : undefined
  }, [widths])

  // Cho bảng table-layout fixed: width cho <col> (fallback về mặc định nếu chưa kéo).
  // def có thể là số px hoặc chuỗi (vd '32%') để giữ layout co giãn khi chưa kéo.
  const colW = useCallback((id: string | number, def: number | string): number | string => {
    return widths[String(id)] || def
  }, [widths])

  // Trả mọi cột về bề rộng mặc định
  const resetWidths = useCallback(() => {
    ref.current = {}
    setWidths({})
    try { localStorage.removeItem(key) } catch { /* bỏ qua */ }
  }, [key])

  return { widths, startResize, thStyle, colW, resetWidths }
}

/** Tay nắm kéo giãn — đặt bên trong <th> (th đã có position:relative từ CSS chung).
 * Style nằm ở `.col-resizer` trong index.css để mọi bảng dùng chung một kiểu. */
export function ResizeHandle({ onMouseDown }: { onMouseDown: (e: React.MouseEvent) => void }) {
  return (
    <span
      className="col-resizer"
      onMouseDown={onMouseDown}
      onClick={(e) => e.stopPropagation()}
      title="Kéo để giãn cột"
    />
  )
}
