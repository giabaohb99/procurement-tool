import { useLayoutEffect, useRef, useState, type ReactNode, type RefObject } from 'react'
import { createPortal } from 'react-dom'
import './packaging.css'

/**
 * duoc-CR-784 — hộp nổi nhỏ bám dưới một phần tử (nút "Thêm điều kiện", chip điều kiện) của thanh lọc chip. Vẽ qua portal
 * để không bị `overflow` của thẻ cắt (cùng nếp với menu chọn cột); tự dời lên khi sát đáy màn, kẹp trong màn khi sát mép phải.
 * Đóng khi bấm ra ngoài (bấm ngay phần tử neo thì do chính phần tử đó quyết — nó bật / tắt hộp), nhấn Esc, hoặc đổi cỡ màn.
 */
export default function PackagingAnchoredPanel({ anchorRef, onClose, width = 320, label, children }: {
  anchorRef: RefObject<HTMLElement | null>
  onClose: () => void
  width?: number
  label: string
  children: ReactNode
}) {
  const [pos, setPos] = useState({ top: 0, left: 0 })
  const panelRef = useRef<HTMLDivElement>(null)
  const closeRef = useRef(onClose)
  useLayoutEffect(() => { closeRef.current = onClose })

  useLayoutEffect(() => {
    function place() {
      const r = anchorRef.current?.getBoundingClientRect()
      if (!r) return
      const height = panelRef.current?.offsetHeight ?? 0
      const top = Math.max(8, Math.min(r.bottom + 6, window.innerHeight - height - 8))
      setPos({ top, left: Math.max(8, Math.min(r.left, window.innerWidth - width - 8)) })
    }
    place()
    function onDown(e: MouseEvent) {
      const t = e.target as Node
      if (!panelRef.current?.contains(t) && !anchorRef.current?.contains(t)) closeRef.current()
    }
    function onKey(e: KeyboardEvent) { if (e.key === 'Escape') closeRef.current() }
    function onScroll(e: Event) { if (!panelRef.current?.contains(e.target as Node)) place() }
    document.addEventListener('mousedown', onDown)
    document.addEventListener('keydown', onKey)
    window.addEventListener('resize', place)
    window.addEventListener('scroll', onScroll, true)
    return () => {
      document.removeEventListener('mousedown', onDown)
      document.removeEventListener('keydown', onKey)
      window.removeEventListener('resize', place)
      window.removeEventListener('scroll', onScroll, true)
    }
  }, [anchorRef, width])

  return createPortal(
    <div ref={panelRef} className="pkg-filter-panel" role="dialog" aria-label={label} style={{ top: pos.top, left: pos.left, width }}>
      {children}
    </div>,
    document.body,
  )
}
