import { useLayoutEffect, useRef, useState } from 'react'
import { createPortal } from 'react-dom'
import { TableColumn } from '../hooks/useTableColumns'

type Props = {
  allColumns: TableColumn[]
  hidden: string[]
  toggleColumn: (key: string) => void
  showAllColumns: () => void
  resetTable: () => void
  /** Tải lại dữ liệu bảng. Bỏ trống = ẩn nút Tải lại. */
  onRefresh?: () => void | Promise<void>
  children?: React.ReactNode   // nút riêng của trang (nếu muốn gộp chung hàng)
}

/**
 * Thanh công cụ chung của bảng: chọn cột hiển thị + tải lại dữ liệu.
 * Đặt ngay trên bảng, bên trong thẻ card. Menu chọn cột render qua portal
 * để không bị `overflow` của card cắt mất.
 */
export default function TableToolbar({
  allColumns, hidden, toggleColumn, showAllColumns, resetTable, onRefresh, children,
}: Props) {
  const [open, setOpen] = useState(false)
  const [pos, setPos] = useState<{ top: number; right: number }>({ top: 0, right: 0 })
  const [busy, setBusy] = useState(false)
  const btnRef = useRef<HTMLButtonElement>(null)
  const menuRef = useRef<HTMLDivElement>(null)

  // Menu dùng position: fixed → phải bám lại theo nút mỗi khi trang cuộn / đổi kích thước
  useLayoutEffect(() => {
    if (!open) return
    function place() {
      const r = btnRef.current?.getBoundingClientRect()
      if (r) setPos({ top: r.bottom + 6, right: window.innerWidth - r.right })
    }
    place()
    function onScroll(e: Event) {
      // cuộn bên trong menu thì vị trí nút không đổi — bỏ qua cho nhẹ
      if (menuRef.current?.contains(e.target as Node)) return
      place()
    }
    function onDown(e: MouseEvent) {
      const t = e.target as Node
      if (!menuRef.current?.contains(t) && !btnRef.current?.contains(t)) setOpen(false)
    }
    function onKey(e: KeyboardEvent) { if (e.key === 'Escape') setOpen(false) }
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
  }, [open])

  async function refresh() {
    if (!onRefresh || busy) return
    setBusy(true)
    try { await onRefresh() } finally { setBusy(false) }
  }

  const hideable = allColumns.filter((c) => !c.fixed)
  const hiddenCount = hideable.filter((c) => hidden.includes(c.key)).length

  return (
    <div className="table-tools">
      {children}

      {hideable.length > 0 && (
        <button ref={btnRef} className={hiddenCount ? 'btn secondary' : 'btn ghost'}
          onClick={() => setOpen((v) => !v)} title="Chọn cột hiển thị">
          <i className="ti ti-columns-3" />Cột{hiddenCount ? ` (ẩn ${hiddenCount})` : ''}
        </button>
      )}

      {open && createPortal(
        <div className="col-menu" ref={menuRef} style={{ top: pos.top, right: pos.right }}>
          <div className="col-menu-head">
            <span>Hiển thị cột</span>
            <button className="col-menu-link" onClick={showAllColumns} disabled={!hiddenCount}>Chọn tất cả</button>
          </div>
          <div className="col-menu-list">
            {hideable.map((c) => (
              <label key={c.key} className="col-menu-item">
                <input type="checkbox" checked={!hidden.includes(c.key)} onChange={() => toggleColumn(c.key)} />
                <span>{c.label}</span>
              </label>
            ))}
          </div>
          <div className="col-menu-foot">
            <button className="col-menu-link" onClick={resetTable}>
              <i className="ti ti-arrow-back-up" />Mặc định (cột &amp; bề rộng)
            </button>
          </div>
        </div>,
        document.body,
      )}

      {onRefresh && (
        <button className="btn ghost" onClick={refresh} disabled={busy} title="Tải lại dữ liệu">
          <i className={'ti ti-refresh' + (busy ? ' spin' : '')} />Tải lại
        </button>
      )}
    </div>
  )
}
