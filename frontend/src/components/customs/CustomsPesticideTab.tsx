// duoc-CR-490 — thẻ "Thuốc BVTV" của Tra cứu thị trường (bản cũ, bê từ bản v2 + thêm form
// thêm/sửa/xóa — v2 chưa có form này). Nguồn: bản cào danhmuc.thuocbvtv.com, nạp lại bằng nút
// "Nạp danh mục".
//
// duoc-CR-493: bộ lọc nằm trên URL với tên RIÊNG (`pq`, `pstatus`, `pgroup`, `pbanned`) — bấm một
// dòng là sang TRANG chi tiết, bấm lùi phải về đúng bộ lọc đang xem. Không dùng bộ lọc dòng hàng
// của trang (nó là state khác, cho các mục khác). Mặc định lọc "Còn hiệu lực" — thuốc hết hiệu lực
// vẫn có, bỏ lọc là thấy. Số trang không lên URL: quay lại thì về trang 1.
//
// bao-CR-734 — đồng bộ bảng với v2 (`customs-pesticide-columns.tsx`): menu "Cột" ẩn/hiện cột (nhớ
// theo trình duyệt), thêm cột "Lĩnh vực" (mặc định ẩn, như v2), cột "Tên thuốc" GHIM bên trái khi
// cuộn ngang.
import { useCallback, useEffect, useState } from 'react'
import { useLocation, useNavigate, useSearchParams } from 'react-router-dom'
import { api } from '../../api/client'
import { useAuth } from '../../auth/AuthContext'
import Pagination from '../Pagination'
import TableHead, { TableCells } from '../TableHead'
import TableScroll from '../TableScroll'
import TableToolbar from '../TableToolbar'
import { TableColumn, useTableColumns } from '../../hooks/useTableColumns'
import { fmtDate } from './customs-shared'
import CustomsPesticideExportMenu from './CustomsPesticideExportMenu'
import CustomsPesticideFilterBar from './CustomsPesticideFilterBar'
import CustomsPesticideForm from './CustomsPesticideForm'
import CustomsPesticideImportDialog from './CustomsPesticideImportDialog'
import {
  BANNED_ONLY, DEFAULT_PESTICIDE_FILTERS, PesticideFilters, buildPesticideParams,
  pesticideStatusBadgeClass, resolvePesticideEmptyMessage,
} from '../../utils/customs-pesticide'
import { toSentenceCaseIfShouting } from '../../utils/customs-pesticide-display'

const PAGE_SIZE = 50

//  bao-CR-734 — cột "Tên thuốc" ghim trái: nền đặc để chữ các cột cuộn qua bên dưới không lộ ra.
//  Ô dữ liệu lấy nền của HÀNG (`inherit`) để vẫn đổi màu theo dòng chẵn lẻ và khi rê chuột — vì thế
//  dòng lẻ phải tự đặt nền trắng (CSS chung để trong suốt), xem `<tr style>` bên dưới.
const PINNED_EDGE = 'inset -1px 0 0 #e9edf7'
const PINNED_TH: React.CSSProperties = { position: 'sticky', left: 0, zIndex: 2, boxShadow: PINNED_EDGE }
const PINNED_TD: React.CSSProperties = { position: 'sticky', left: 0, zIndex: 1, background: 'inherit', boxShadow: PINNED_EDGE }

//  Thứ tự + tiêu đề theo v2. Đổi thứ tự / thêm bớt cột thì đổi luôn `PESTICIDE_TABLE_KEY` cho bản lưu
//  ẩn/hiện cũ khỏi lệch (cột mới khai `defaultHidden` thì `useTableColumns` tự ẩn, không cần đổi khóa).
const PESTICIDE_TABLE_KEY = 'customs-pesticides'
const COLS: TableColumn[] = [
  { key: 'trade_name', label: 'Tên thuốc', fixed: true, th: PINNED_TH, td: PINNED_TD, cell: (r) => (
    <>
      <b>{r.trade_name}</b>
      {r.is_manual && <span className="badge gray" style={{ marginLeft: 6 }}>Tự thêm</span>}
    </>
  ) },
  { key: 'active_ingredient', label: 'Hoạt chất' },
  { key: 'banned', label: 'Hoạt chất cấm', cell: (r) => r.banned?.length > 0 && (
    <span style={{ display: 'flex', flexWrap: 'wrap', gap: 4 }}>
      {r.banned.map((b: any) => <span key={b.id} className="badge err">{b.name}</span>)}
    </span>
  ) },
  { key: 'concentration', label: 'Hàm lượng' },
  { key: 'pest_group', label: 'Phân nhóm' },
  { key: 'registrant', label: 'Công ty đăng ký' },
  { key: 'registration_no', label: 'Số đăng ký' },
  { key: 'expires_on', label: 'Hết hạn đăng ký', cell: (r) => fmtDate(r.expires_on) },
  { key: 'status', label: 'Tình trạng', cell: (r) => (
    <span className={`badge ${pesticideStatusBadgeClass(r.status)}`}>{r.status_label || 'Chưa rõ'}</span>
  ) },
  { key: 'use_count', label: 'Phạm vi sử dụng', align: 'right', cell: (r) => r.use_count || '' },
  { key: 'sector', label: 'Lĩnh vực', defaultHidden: true, cell: (r) => toSentenceCaseIfShouting(r.sector || '') },
]

export default function CustomsPesticideTab() {
  const { can } = useAuth()
  const canCreate = can('customs_pesticide', 'create')
  const canWrite = can('customs_pesticide', 'write')
  const canExport = can('customs_price', 'export')

  const navigate = useNavigate()
  const location = useLocation()
  const [searchParams, setSearchParams] = useSearchParams()
  //  `pstatus=all` = mọi tình trạng; KHÔNG có param = mặc định "Còn hiệu lực".
  const applied: PesticideFilters = {
    q: searchParams.get('pq') ?? '',
    status: searchParams.get('pstatus') === 'all' ? '' : searchParams.get('pstatus') ?? DEFAULT_PESTICIDE_FILTERS.status,
    pestGroup: searchParams.get('pgroup') ?? '',
    sector: searchParams.get('psector') ?? '',
    banned: searchParams.get('pbanned') ?? '',
  }
  //  Ô tìm gõ vào state cục bộ cho khỏi giật; ngưng gõ 350ms mới ghi lên URL.
  const [draftQ, setDraftQ] = useState(applied.q)
  const draft = { ...applied, q: draftQ }
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(PAGE_SIZE)
  const [rows, setRows] = useState<any[]>([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(false)
  const [options, setOptions] = useState<any>(null)
  const [formOpen, setFormOpen] = useState(false)
  const [importOpen, setImportOpen] = useState(false)
  const table = useTableColumns(PESTICIDE_TABLE_KEY, COLS)

  const loadOptions = useCallback(() => {
    api.get('/api/customs/pesticides/options').then((r) => setOptions(r.data.data))
  }, [])
  useEffect(() => { loadOptions() }, [loadOptions])

  const load = useCallback(() => {
    setLoading(true)
    api.get('/api/customs/pesticides', { params: { ...buildPesticideParams(applied), page, page_size: pageSize } })
      .then((r) => { setRows(r.data.data.items); setTotal(r.data.data.total) })
      .finally(() => setLoading(false))
  }, [applied.q, applied.status, applied.pestGroup, applied.sector, applied.banned, page, pageSize])
  useEffect(() => { load() }, [load])

  /** Ghi NHIỀU param trong một lượt (`replace`: đổi lọc không đẻ mục lịch sử cho nút Back). */
  function writeParams(next: Record<string, string | null>) {
    setSearchParams((cur) => {
      const p = new URLSearchParams(cur)
      for (const [k, v] of Object.entries(next)) (v ? p.set(k, v) : p.delete(k))
      return p
    }, { replace: true })
    setPage(1)
  }

  // Gõ ô tìm xong ngưng 350ms mới áp — cùng nhịp mọi ô tìm khác trên màn; đổi ô CHỌN thì áp ngay.
  useEffect(() => {
    if (draftQ === applied.q) return
    const t = setTimeout(() => writeParams({ pq: draftQ.trim() ? draftQ : null }), 350)
    return () => clearTimeout(t)
  }, [draftQ])
  //  URL đổi từ ngoài (Xóa lọc, nút Back) thì ô tìm theo.
  useEffect(() => { setDraftQ(applied.q) }, [applied.q])

  function setSelect(k: 'status' | 'pestGroup' | 'sector' | 'banned', v: string) {
    if (k === 'status') writeParams({ pstatus: v === DEFAULT_PESTICIDE_FILTERS.status ? null : (v || 'all') })
    else writeParams({ [{ pestGroup: 'pgroup', sector: 'psector', banned: 'pbanned' }[k]]: v || null })
  }
  function resetFilters() {
    setDraftQ('')
    writeParams({ pq: null, pstatus: null, pgroup: null, psector: null, pbanned: null })
  }
  //  Mang theo chỗ đang đứng (bộ lọc trên URL) để nút lùi của trang chi tiết quay về đúng đây.
  function openDetail(pesticideId: number) {
    navigate(`/customs-prices/pesticides/${pesticideId}`, { state: { from: `${location.pathname}${location.search}` } })
  }
  function refresh() { loadOptions(); load() }

  const catalogTotal = options?.total ?? 0
  const filtersActive = draft.q !== '' || draft.status !== DEFAULT_PESTICIDE_FILTERS.status
    || draft.pestGroup !== '' || !!draft.sector || draft.banned !== ''
  const emptyMessage = resolvePesticideEmptyMessage(catalogTotal, canWrite,
    applied.banned === BANNED_ONLY ? options?.banned_rules : undefined)

  return (
    <div>
      <div className="card" style={{ padding: 12, marginBottom: 10 }}>
        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', alignItems: 'center' }}>
          <CustomsPesticideFilterBar draftQ={draftQ} onDraftQChange={setDraftQ} draft={draft} options={options}
            filtersActive={filtersActive} onSelect={setSelect} onReset={resetFilters} />
          <span style={{ flex: 1 }} />
          {canExport && (
            <CustomsPesticideExportMenu filters={applied} page={page} pageSize={pageSize}
              pageRowCount={rows.length} disabled={catalogTotal === 0} />
          )}
          {canWrite && (
            <button className="btn ghost" onClick={() => setImportOpen(true)}><i className="ti ti-upload" />Nạp danh mục</button>
          )}
          {canCreate && (
            <button className="btn" onClick={() => setFormOpen(true)}><i className="ti ti-plus" />Thêm thuốc</button>
          )}
        </div>
      </div>

      <div className="card table-card">
        <TableToolbar {...table} onRefresh={refresh} />
        <TableScroll>
          <table>
            <TableHead {...table} />
            <tbody>
              {rows.map((r, i) => (
                <tr key={r.id} className="clickable" onClick={() => openDetail(r.id)}
                  style={i % 2 === 0 ? { background: '#fff' } : undefined}>
                  <TableCells columns={table.columns} row={r} index={i} />
                </tr>
              ))}
              {!loading && rows.length === 0 && (
                <tr><td colSpan={table.columns.length} className="table-empty">{emptyMessage}</td></tr>
              )}
            </tbody>
          </table>
        </TableScroll>
        <div className="table-foot">
          <Pagination page={page} pageSize={pageSize} total={total} onChange={(p, s) => { setPage(p); setPageSize(s) }} />
        </div>
      </div>

      {formOpen && (
        <CustomsPesticideForm onClose={() => setFormOpen(false)} onSaved={(saved) => { setFormOpen(false); if (saved?.id) openDetail(saved.id); else refresh() }} />
      )}
      {importOpen && (
        <CustomsPesticideImportDialog options={options} onClose={() => setImportOpen(false)}
          onApplied={() => { setImportOpen(false); refresh() }} />
      )}
    </div>
  )
}
