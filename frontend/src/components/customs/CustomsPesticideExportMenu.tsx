// Nút «Xuất Excel» của mục «Thuốc BVTV», hai lựa chọn: trang đang xem / cả danh mục. Khuôn
// dropdown bám nút bê từ `TableToolbar` (portal + `.col-menu`, tự đóng khi click ra ngoài / Esc /
// cuộn trang). Backend: `GET /api/customs/pesticides/export?scope=page|all`, quyền
// `customs_price.export` (giống nút Xuất Excel của thẻ Danh sách, KHÁC quyền sửa danh mục
// `customs_pesticide` của nút Nạp danh mục cạnh nó).
import { useLayoutEffect, useRef, useState } from 'react'
import { createPortal } from 'react-dom'
import { api } from '../../api/client'
import { toast } from '../toast'
import { buildPesticideParams, PesticideFilters } from '../../utils/customs-pesticide'
import { blobErrorMessage, downloadBlob } from './customs-shared'

type ExportScope = 'page' | 'all'

type Props = {
  /** Bộ lọc ĐÃ ÁP (không phải ô đang gõ) — đúng những gì `GET /pesticides` đang dùng. */
  filters: PesticideFilters
  page: number
  pageSize: number
  /** Số dòng của trang đang xem — hiện trong nhãn mục menu. */
  pageRowCount: number
  /** Chưa có thuốc nào trong danh mục (lọc hay không) → khóa cả nút, xuất ra tệp trống vô nghĩa. */
  disabled?: boolean
}

const ITEM_STYLE: React.CSSProperties = {
  display: 'block', width: '100%', textAlign: 'left', background: 'none', border: 'none',
  font: 'inherit', color: 'inherit', cursor: 'pointer',
}
const DESC_STYLE: React.CSSProperties = {
  fontSize: 11, fontWeight: 400, color: 'var(--muted)', marginTop: 2, whiteSpace: 'normal', lineHeight: 1.35,
}

export default function CustomsPesticideExportMenu({ filters, page, pageSize, pageRowCount, disabled }: Props) {
  const [open, setOpen] = useState(false)
  const [exporting, setExporting] = useState(false)
  const [pos, setPos] = useState<{ top: number; right: number }>({ top: 0, right: 0 })
  const btnRef = useRef<HTMLButtonElement>(null)
  const menuRef = useRef<HTMLDivElement>(null)
  // Chặn bấm đúp ngay trong lượt bấm — `disabled`/`exporting` (state) chỉ đúng ở lượt vẽ SAU.
  const busy = useRef(false)

  useLayoutEffect(() => {
    if (!open) return
    function place() {
      const r = btnRef.current?.getBoundingClientRect()
      if (r) setPos({ top: r.bottom + 6, right: window.innerWidth - r.right })
    }
    place()
    function onDown(e: MouseEvent) {
      const t = e.target as Node
      if (!menuRef.current?.contains(t) && !btnRef.current?.contains(t)) setOpen(false)
    }
    function onKey(e: KeyboardEvent) { if (e.key === 'Escape') setOpen(false) }
    document.addEventListener('mousedown', onDown)
    document.addEventListener('keydown', onKey)
    window.addEventListener('resize', place)
    window.addEventListener('scroll', place, true)
    return () => {
      document.removeEventListener('mousedown', onDown)
      document.removeEventListener('keydown', onKey)
      window.removeEventListener('resize', place)
      window.removeEventListener('scroll', place, true)
    }
  }, [open])

  async function runExport(scope: ExportScope) {
    if (busy.current) return
    busy.current = true
    setOpen(false)
    setExporting(true)
    try {
      const params: Record<string, string> = scope === 'all'
        ? { scope }
        : { scope, ...buildPesticideParams(filters), page: String(page), page_size: String(pageSize) }
      await downloadBlob(api, '/api/customs/pesticides/export', 'danh-muc-thuoc-bvtv.xlsx', params)
    } catch (e: any) {
      toast.error(await blobErrorMessage(e, 'Không xuất được tệp Excel'))
    } finally {
      busy.current = false
      setExporting(false)
    }
  }

  return (
    <>
      <button ref={btnRef} type="button" className="btn ghost" disabled={disabled || exporting}
        onClick={() => setOpen((v) => !v)} title="Xuất danh mục thuốc BVTV ra Excel">
        <i className={exporting ? 'ti ti-loader spin' : 'ti ti-file-spreadsheet'} />
        {exporting ? 'Đang xuất…' : 'Xuất Excel'}
      </button>

      {open && createPortal(
        <div className="col-menu" ref={menuRef} style={{ top: pos.top, right: pos.right }}>
          <button type="button" className="col-menu-item" style={ITEM_STYLE} onClick={() => runExport('page')}>
            <div>Trang hiện tại ({pageRowCount} dòng)</div>
            <div style={DESC_STYLE}>
              Chỉ các dòng đang xem theo bộ lọc hiện tại. Nạp lại tệp này qua «Nạp danh mục»
              <b> chỉ cập nhật</b> đúng các thuốc có trong tệp, phần còn lại giữ nguyên.
            </div>
          </button>
          <button type="button" className="col-menu-item" style={ITEM_STYLE} onClick={() => runExport('all')}>
            <div>Toàn bộ danh mục</div>
            <div style={DESC_STYLE}>
              Xuất hết, không theo bộ lọc. Nạp lại tệp này qua «Nạp danh mục» sẽ
              <b> thay toàn bộ danh mục</b>; thuốc thêm tay không có trong lần nạp (vẫn giữ trên hệ thống).
            </div>
          </button>
        </div>,
        document.body,
      )}
    </>
  )
}
