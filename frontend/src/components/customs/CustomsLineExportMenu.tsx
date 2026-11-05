// bao-CR-728 (bê bao-CR-718 của bản v2) — nút "Xuất dữ liệu" của thẻ Danh sách thành menu ba mục:
//   (a) Xuất ngay — hành vi cũ, tải thẳng tối đa 50.000 dòng (`GET /api/customs/lines/export`);
//   (b) Xuất toàn bộ theo bộ lọc (chạy nền) — hỏi xác nhận (bộ lọc, số dòng, số tệp dự kiến) rồi tạo LÔ
//       (`POST /api/customs/export-batches`), sang màn chi tiết lô; 409 = đang có lô chưa xong, sang Lô xuất của tôi;
//   (c) Lô xuất của tôi.
// Quyền `customs_price.export` do trang gác (chỉ vẽ nút khi có quyền). Khuôn menu bám nút bê từ
// `CustomsPesticideExportMenu` (portal + `.col-menu`, tự đóng khi bấm ra ngoài / Esc / cuộn trang).
import { useLayoutEffect, useRef, useState } from 'react'
import { createPortal } from 'react-dom'
import { useNavigate } from 'react-router-dom'
import { api } from '../../api/client'
import { askConfirm } from '../confirm'
import { toast } from '../toast'
import {
  buildFullExportConfirmMessage, CUSTOMS_EXPORT_ROWS_PER_FILE, CUSTOMS_EXPORTS_PATH, customsExportPath,
  estimateExportFileCount,
} from '../../utils/customs-export'
import { blobErrorMessage, downloadBlob } from './customs-shared'

type Props = {
  /** Bộ lọc ĐÃ ÁP dựng bằng `toParams` — không kèm `page` / `page_size`. */
  params: Record<string, string>
  /** Câu mô tả bộ lọc cho hộp xác nhận (`describeCustomsFilters`). */
  filterSummary: string
  /** Tổng dòng khớp bộ lọc của bảng đang xem. */
  totalRows: number
}

const ITEM_STYLE: React.CSSProperties = {
  display: 'block', width: '100%', textAlign: 'left', background: 'none', border: 'none',
  font: 'inherit', color: 'inherit', cursor: 'pointer',
}
const DISABLED_STYLE: React.CSSProperties = { ...ITEM_STYLE, opacity: 0.5, cursor: 'not-allowed' }
const DESC_STYLE: React.CSSProperties = {
  fontSize: 11, fontWeight: 400, color: 'var(--muted)', marginTop: 2, whiteSpace: 'normal', lineHeight: 1.35,
}

export default function CustomsLineExportMenu({ params, filterSummary, totalRows }: Props) {
  const navigate = useNavigate()
  const [open, setOpen] = useState(false)
  const [working, setWorking] = useState(false)
  const [pos, setPos] = useState<{ top: number; right: number }>({ top: 0, right: 0 })
  const btnRef = useRef<HTMLButtonElement>(null)
  const menuRef = useRef<HTMLDivElement>(null)
  // Chặn bấm đúp ngay trong lượt bấm — bấm đúp "xuất toàn bộ" là hai lô, backend chặn lô sau bằng 409.
  const busy = useRef(false)
  const hasRows = totalRows > 0
  const overCap = totalRows > CUSTOMS_EXPORT_ROWS_PER_FILE
  const capLabel = CUSTOMS_EXPORT_ROWS_PER_FILE.toLocaleString('vi-VN')

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

  async function guarded(run: () => Promise<void>) {
    if (busy.current) return
    busy.current = true
    setOpen(false)
    setWorking(true)
    try { await run() } finally {
      busy.current = false
      setWorking(false)
    }
  }

  function exportNow() {
    if (!hasRows || overCap) return
    void guarded(async () => {
      try {
        await downloadBlob(api, '/api/customs/lines/export', 'tra-cuu-gia-hai-quan.xlsx', params)
      } catch (e: any) {
        toast.error(await blobErrorMessage(e, 'Không xuất được tệp Excel'))
      }
    })
  }

  function exportAll() {
    if (!hasRows) return
    void guarded(async () => {
      const ok = await askConfirm({
        title: 'Xuất toàn bộ theo bộ lọc',
        message: buildFullExportConfirmMessage(totalRows, filterSummary),
        confirmText: 'Đồng ý',
        danger: false,
      })
      if (!ok) return
      try {
        const r = await api.post('/api/customs/export-batches', null, { params, _silent: true } as any)
        const batch = r.data.data
        toast.success(r.data.message || `Đã tạo lô xuất #${batch.id}`)
        navigate(customsExportPath(batch.id))
      } catch (e: any) {
        const msg = e?.response?.data?.error?.message || 'Không tạo được lô xuất'
        toast.error(msg)
        //  409 = đang có một lô chờ / chạy của chính người này — chỉ đường sang danh sách lô.
        if (e?.response?.status === 409) navigate(CUSTOMS_EXPORTS_PATH)
      }
    })
  }

  return (
    <>
      <button ref={btnRef} type="button" className="btn ghost" disabled={working}
        onClick={() => setOpen((v) => !v)} title="Xuất các dòng đang lọc ra Excel">
        <i className={working ? 'ti ti-loader spin' : 'ti ti-file-spreadsheet'} />
        {working ? 'Đang xuất…' : 'Xuất dữ liệu'}
        <i className="ti ti-chevron-down" style={{ marginLeft: 2 }} />
      </button>

      {open && createPortal(
        <div className="col-menu" ref={menuRef} style={{ top: pos.top, right: pos.right, width: 320 }}>
          <button type="button" className="col-menu-item" style={!hasRows || overCap ? DISABLED_STYLE : ITEM_STYLE}
            disabled={!hasRows || overCap} onClick={exportNow}>
            <div><i className="ti ti-download" /> Xuất ngay (tối đa {capLabel} dòng)</div>
            <div style={DESC_STYLE}>
              {overCap
                ? `Bộ lọc đang có ${totalRows.toLocaleString('vi-VN')} dòng, quá trần. Dùng mục xuất toàn bộ bên dưới.`
                : 'Tải về ngay một tệp Excel đúng các dòng đang lọc.'}
            </div>
          </button>
          <button type="button" className="col-menu-item" style={hasRows ? ITEM_STYLE : DISABLED_STYLE}
            disabled={!hasRows} onClick={exportAll}>
            <div><i className="ti ti-files" /> Xuất toàn bộ theo bộ lọc (chạy nền)</div>
            <div style={DESC_STYLE}>
              {hasRows
                ? `${totalRows.toLocaleString('vi-VN')} dòng, dự kiến ${estimateExportFileCount(totalRows)} tệp. `
                  + 'Báo chuông khi xong; sửa tệp rồi nạp lại được (cột ID / Thao tác).'
                : 'Bộ lọc chưa có dòng nào để xuất.'}
            </div>
          </button>
          <div style={{ borderTop: '1px solid #f1f5f9', margin: '4px 0' }} />
          <button type="button" className="col-menu-item" style={ITEM_STYLE}
            onClick={() => { setOpen(false); navigate(CUSTOMS_EXPORTS_PATH) }}>
            <div><i className="ti ti-list-check" /> Lô xuất của tôi</div>
          </button>
        </div>,
        document.body,
      )}
    </>
  )
}
