import { useCallback, useRef, useState } from 'react'

/**
 * Hook kéo giãn độ rộng cột cho bảng HTML thuần.
 * - Lưu độ rộng theo `key` vào localStorage (nhớ cho lần sau).
 * - Cột được đánh số theo vị trí (index).
 *
 * Dùng:
 *   const { startResize, thStyle, colW } = useResizableColumns('colw:xxx')
 *   // Bảng table-layout auto: gắn thStyle(i) vào <th>, đặt <ResizeHandle> bên trong <th> (th cần position:relative)
 *   // Bảng table-layout fixed: dùng colW(i, mặc_định) cho width của <col>
 */
type Widths = Record<number, number>

function loadWidths(key: string): Widths {
  try {
    const raw = localStorage.getItem(key)
    return raw ? JSON.parse(raw) : {}
  } catch {
    return {}
  }
}

export function useResizableColumns(key: string) {
  const [widths, setWidths] = useState<Widths>(() => loadWidths(key))
  const ref = useRef<Widths>(widths)
  ref.current = widths

  const startResize = useCallback((index: number, e: React.MouseEvent) => {
    e.preventDefault()
    e.stopPropagation()   // tránh kích hoạt sort khi kéo giãn cột
    const handle = e.currentTarget as HTMLElement
    const th = handle.closest('th') as HTMLElement | null
    const startX = e.clientX
    const startW = th ? th.offsetWidth : (ref.current[index] || 120)

    function onMove(ev: MouseEvent) {
      const w = Math.max(48, startW + (ev.clientX - startX))
      const next = { ...ref.current, [index]: w }
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
  const thStyle = useCallback((index: number): React.CSSProperties | undefined => {
    const w = widths[index]
    return w ? { width: w, minWidth: w } : undefined
  }, [widths])

  // Cho bảng table-layout fixed: width cho <col> (fallback về mặc định nếu chưa kéo).
  // def có thể là số px hoặc chuỗi (vd '32%') để giữ layout co giãn khi chưa kéo.
  const colW = useCallback((index: number, def: number | string): number | string => {
    return widths[index] || def
  }, [widths])

  return { startResize, thStyle, colW }
}

/** Tay nắm kéo giãn — đặt bên trong <th> (th phải có position:relative).
 * Luôn hiển thị 1 vạch chia mờ ở mép phải cột; đậm lên khi rê chuột để thấy rõ chỗ kéo. */
export function ResizeHandle({ onMouseDown }: { onMouseDown: (e: React.MouseEvent) => void }) {
  const [hover, setHover] = useState(false)
  return (
    <span
      onMouseDown={onMouseDown}
      onClick={(e) => e.stopPropagation()}
      onMouseEnter={() => setHover(true)}
      onMouseLeave={() => setHover(false)}
      title="Kéo để giãn cột"
      style={{
        position: 'absolute',
        top: 0,
        right: 0,
        height: '100%',
        width: 9,
        cursor: 'col-resize',
        userSelect: 'none',
        touchAction: 'none',
        zIndex: 2,
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
      }}
    >
      {/* Vạch chia dọc: mờ khi bình thường, đậm (xanh) khi rê chuột */}
      <span
        style={{
          display: 'block',
          width: hover ? 3 : 2,
          height: '58%',
          borderRadius: 2,
          background: hover ? 'var(--teal, #0ea5a5)' : 'rgba(148,163,184,0.55)',
          transition: 'background 0.12s, width 0.12s',
        }}
      />
    </span>
  )
}
