// bao-CR-470 — lịch sử các lần nạp dữ liệu hải quan (lô chạy thử + lô ghi thật) và nút hoàn tác.
// bao-CR-541: lô chỉ THÊM dòng chưa có (trùng thì bỏ qua) nên luôn hoàn tác được. Riêng lô CŨ nạp
// trước CR đã THAY dòng cũ (deleted_count > 0) thì không: dòng cũ đã xóa lúc ghi, hoàn tác chỉ để
// lại một khoảng ngày trống — nút bị khóa kèm lời giải thích.
// bao-CR-493: từ hộp thoại thành MỘT THẺ trên trang (thẻ «Lịch sử nạp», yêu cầu F11 phòng Thu mua)
// và thêm nút tải lại tệp GTT02 gốc — chỉ lô nạp qua màn hình có tệp (`has_file`).
// bao-CR-608: thêm cột Ghi đè / Xóa (tệp có cột «ID» + «Thao tác»). Lô ghi đè / xóa có bản chụp
// nên VẪN hoàn tác được — backend báo lô cũ không hoàn tác được bằng `legacy_replace`.
import { useCallback, useEffect, useState } from 'react'
import { api } from '../../api/client'
import { useAuth } from '../../auth/AuthContext'
import { askConfirm } from '../confirm'
import Pagination from '../Pagination'
import { toast } from '../toast'
import CustomsModal from './CustomsModal'
import { StatusBadge } from './CustomsImportDialog'
import { blobErrorMessage, downloadBlob, fmtDate } from './customs-shared'

const fmtDateTime = (iso?: string) => (iso ? `${fmtDate(iso)} ${iso.slice(11, 16)}` : '—')
// bao-CR-608 — lô CŨ đã thay dòng mà không có bản chụp; backend chưa có khóa thì lùi về luật cũ.
const legacy = (b: any): boolean => (b.legacy_replace ?? b.deleted_count > 0)

export default function CustomsHistoryPanel({ onChanged }: { onChanged: () => void }) {
  const { can } = useAuth()
  const [rows, setRows] = useState<any[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [logsOf, setLogsOf] = useState<any>(null)

  const load = useCallback(() => {
    api.get('/api/customs/imports', { params: { page, page_size: 20 } })
      .then((r) => { setRows(r.data.data.items); setTotal(r.data.data.total) })
  }, [page])
  useEffect(() => { load() }, [load])

  async function revert(b: any) {
    // bao-CR-608 — nói đủ ba việc hoàn tác sẽ làm (như `formatRevertConfirm` bản v2).
    const parts = [`xóa ${b.created_count} dòng lô này đã thêm`]
    if (b.updated_count) parts.push(`trả ${b.updated_count} dòng lô đã ghi đè về bản trước lô`)
    if (b.deleted_count) parts.push(`dựng lại ${b.deleted_count} dòng lô đã xóa`)
    const ok = await askConfirm({
      title: 'Hoàn tác lô nạp',
      message: `Hoàn tác tệp «${b.filename}»: ${parts.join(', ')}?`
        + (b.updated_count ? ' Dòng bị sửa tiếp sau lô này cũng trả về bản trước lô — phần sửa sau sẽ mất.' : ''),
      confirmText: 'Hoàn tác',
    })
    if (!ok) return
    try {
      const r = await api.post(`/api/customs/imports/${b.id}/revert`)
      toast.success(r.data.message || 'Đã hoàn tác')
      load()
      onChanged()
    } catch { /* interceptor đã báo lỗi */ }
  }

  async function downloadSource(b: any) {
    try {
      await downloadBlob(api, `/api/customs/imports/${b.id}/file`, b.filename || `gtt02-${b.id}.xls`)
    } catch (e: any) {
      toast.error(await blobErrorMessage(e, 'Không tải được tệp gốc'))
    }
  }

  return (
    <div className="card table-card">
      <div style={{ padding: '10px 14px 0', fontSize: 13, color: 'var(--muted)' }}>
        Mọi lô chạy thử và ghi thật, mới nhất lên đầu. Dòng trùng được bỏ qua khi nạp; hoàn tác một lô xóa dòng lô đó đã thêm và trả lại
        dòng lô đó đã ghi đè / xóa (theo cột ID / Thao tác); lô nạp qua màn hình tải lại được tệp gốc.
      </div>
      <div className="table-scroll"><table>
        <thead><tr>
          <th>#</th><th>Tệp</th><th>Loại</th><th>Trạng thái</th><th style={{ textAlign: 'right' }}>Thêm mới</th>
          <th style={{ textAlign: 'right' }}>Ghi đè</th><th style={{ textAlign: 'right' }}>Xóa</th>
          <th>Khoảng ngày</th><th style={{ textAlign: 'right' }}>Vá ngày</th><th style={{ textAlign: 'right' }}>Bỏ qua (trùng)</th>
          <th>Người nạp</th><th>Lúc</th><th />
        </tr></thead>
        <tbody>
          {rows.map((b) => (
            <tr key={b.id}>
              <td>{b.id}</td>
              <td style={{ wordBreak: 'break-all' }}>{b.filename}</td>
              <td>{b.mode === 0 ? 'Chạy thử' : 'Ghi thật'}</td>
              <td><StatusBadge b={b} /></td>
              <td style={{ textAlign: 'right' }}>{b.created_count}</td>
              <td style={{ textAlign: 'right' }}>{b.updated_count || 0}</td>
              <td style={{ textAlign: 'right' }}>{b.deleted_count || 0}</td>
              <td>{b.date_from ? `${fmtDate(b.date_from)} → ${fmtDate(b.date_to)}` : '—'}</td>
              <td style={{ textAlign: 'right' }}>{b.date_fixed || 0}</td>
              <td style={{ textAlign: 'right' }}>{(b.existing_rows || 0) + (b.duplicate_rows || 0)}</td>
              <td>{b.created_by_name || '—'}</td>
              <td>{fmtDateTime(b.finished_at || b.created_at)}</td>
              <td style={{ whiteSpace: 'nowrap' }}>
                {b.has_file && (
                  <button className="btn ghost" title="Tải lại tệp gốc đã nạp" onClick={() => downloadSource(b)}>
                    <i className="ti ti-download" />
                  </button>
                )}
                <button className="btn ghost" title="Nhật ký dòng lỗi / cảnh báo" onClick={() => setLogsOf(b)}>
                  <i className="ti ti-list-details" />
                </button>
                {b.mode === 1 && b.status === 2 && can('customs_price', 'delete') && (
                  <button className="btn ghost" disabled={legacy(b)} onClick={() => revert(b)}
                    title={legacy(b)
                      ? `Lô này nạp theo cách cũ, đã thay ${b.deleted_count} dòng cũ nên không hoàn tác được.`
                      : 'Hoàn tác: xóa dòng lô này đã thêm, trả lại dòng lô đã ghi đè / xóa'}>
                    <i className="ti ti-arrow-back-up" />
                  </button>
                )}
              </td>
            </tr>
          ))}
          {!rows.length && <tr><td colSpan={13} className="table-empty">Chưa nạp lần nào</td></tr>}
        </tbody>
      </table></div>
      <div className="table-foot">
        <Pagination page={page} pageSize={20} total={total} hideSize onChange={(p) => setPage(p)} />
      </div>
      {logsOf && <BatchLogs batch={logsOf} onClose={() => setLogsOf(null)} />}
    </div>
  )
}

const LEVELS: Record<number, [string, string]> = { 0: ['Thông tin', 'gray'], 1: ['Cảnh báo', 'warn'], 2: ['Cần rà', 'info'], 3: ['Lỗi', 'err'] }

// bao-CR-496 — kết cục từng dòng của tệp, khớp `ImportRowStatus` backend
// (1 Thêm mới · 2 Lỗi · 3 Trùng trong tệp · 4 Đã có). bao-CR-541: 3 và 4 là dòng BỎ QUA.
// bao-CR-608: 5 Ghi đè · 6 Xóa (theo cột «ID» / «Thao tác») · 7 Bỏ qua (xóa hỏng / ID lặp).
const ROW_STATUS: Record<number, [string, string]> = {
  1: ['Thêm mới', 'ok'], 2: ['Lỗi', 'err'], 3: ['Trùng trong tệp', 'warn'], 4: ['Đã có', 'gray'],
  5: ['Ghi đè', 'info'], 6: ['Xóa', 'err'], 7: ['Bỏ qua', 'warn'],
}

/** Kết cục TỪNG DÒNG của tệp (bê từ `customs-batch-rows-panel.tsx` bản v2): tổng theo kết cục, bấm để lọc. */
function BatchRows({ batchId }: { batchId: number }) {
  const [summary, setSummary] = useState<any>(null)
  const [status, setStatus] = useState<number | undefined>(undefined)
  const [rows, setRows] = useState<any[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  useEffect(() => {
    api.get(`/api/customs/imports/${batchId}/rows/summary`).then((r) => setSummary(r.data.data)).catch(() => setSummary(null))
  }, [batchId])
  useEffect(() => {
    api.get(`/api/customs/imports/${batchId}/rows`, { params: { page, page_size: 50, row_status: status } })
      .then((r) => { setRows(r.data.data.items); setTotal(r.data.data.total) })
      .catch(() => { setRows([]); setTotal(0) })
  }, [batchId, page, status])
  const chips: [number | undefined, string, number][] = summary ? [
    [undefined, 'Tất cả', summary.total], [1, 'Thêm mới', summary.new], [2, 'Lỗi', summary.error], [3, 'Trùng trong tệp', summary.duplicate], [4, 'Đã có', summary.existing || 0],
    // bao-CR-608 — chỉ hiện khi lô có dòng mang kết cục đó.
    ...([[5, 'Ghi đè', summary.updated || 0], [6, 'Xóa', summary.deleted || 0], [7, 'Bỏ qua', summary.ignored || 0]] as [number, string, number][])
      .filter(([, , n]) => n > 0),
  ] : []
  return (
    <div style={{ marginBottom: 14 }}>
      <div style={{ fontWeight: 600, fontSize: 13, marginBottom: 6 }}>Từng dòng của tệp</div>
      <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', marginBottom: 8, fontSize: 12 }}>
        {chips.map(([v, label, n]) => (
          <button key={label} type="button" className={status === v ? 'btn' : 'btn ghost'} style={{ padding: '2px 10px' }}
            onClick={() => { setStatus(v); setPage(1) }}>{label}: {Number(n || 0).toLocaleString('vi-VN')}</button>
        ))}
        {summary && summary.total === 0 && (
          <span style={{ color: 'var(--muted)' }}>Lô này nạp trước khi có nhật ký từng dòng — chỉ có ghi chú ở bảng dưới.</span>
        )}
      </div>
      <div className="table-scroll" style={{ maxHeight: 320 }}><table>
        <thead><tr><th style={{ width: 70 }}>Dòng</th><th style={{ width: 120 }}>Kết cục</th><th>Tên hàng</th><th>Ghi chú</th></tr></thead>
        <tbody>
          {rows.map((x) => (
            <tr key={x.id}>
              <td>{x.row_no || '—'}</td>
              <td><span className={`badge ${ROW_STATUS[x.row_status]?.[1] || 'gray'}`}>{ROW_STATUS[x.row_status]?.[0] || x.row_status_label}</span></td>
              <td style={{ whiteSpace: 'normal' }}>{x.product_name || '—'}</td>
              <td style={{ whiteSpace: 'normal' }}>{x.message}</td>
            </tr>
          ))}
          {!rows.length && <tr><td colSpan={4} className="table-empty">{status ? 'Không có dòng nào mang kết cục này.' : 'Lô này chưa có nhật ký từng dòng.'}</td></tr>}
        </tbody>
      </table></div>
      <div className="table-foot">
        <Pagination page={page} pageSize={50} total={total} hideSize onChange={(p) => setPage(p)} />
      </div>
    </div>
  )
}

function BatchLogs({ batch, onClose }: { batch: any; onClose: () => void }) {
  const [rows, setRows] = useState<any[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  useEffect(() => {
    api.get(`/api/customs/imports/${batch.id}/logs`, { params: { page, page_size: 50 } })
      .then((r) => { setRows(r.data.data.items); setTotal(r.data.data.total) })
  }, [batch.id, page])
  return (
    <CustomsModal title={`Nhật ký lô #${batch.id} — ${batch.filename}`} width={1000} onClose={onClose}>
      {batch.error_summary && <div style={{ color: '#b91c1c', fontSize: 13, whiteSpace: 'pre-wrap', marginBottom: 10 }}>{batch.error_summary.split('\n')[0]}</div>}
      <BatchRows batchId={batch.id} />
      <div style={{ fontWeight: 600, fontSize: 13, marginBottom: 6 }}>Ghi chú khi đọc tệp</div>
      <div className="table-scroll"><table>
        <thead><tr><th style={{ width: 80 }}>Dòng</th><th style={{ width: 110 }}>Mức</th><th>Nội dung</th></tr></thead>
        <tbody>
          {rows.map((x) => (
            <tr key={x.id}>
              <td>{x.row_no || '—'}</td>
              <td><span className={`badge ${LEVELS[x.level]?.[1] || 'gray'}`}>{LEVELS[x.level]?.[0] || x.level}</span></td>
              <td>{x.message}</td>
            </tr>
          ))}
          {!rows.length && <tr><td colSpan={3} className="table-empty">Không có ghi chú nào — mọi dòng đọc được bình thường</td></tr>}
        </tbody>
      </table></div>
      <div className="table-foot">
        <Pagination page={page} pageSize={50} total={total} hideSize onChange={(p) => setPage(p)} />
      </div>
    </CustomsModal>
  )
}
