// bao-CR-470 — lịch sử các lần nạp dữ liệu hải quan (lô chạy thử + lô ghi thật) và nút hoàn tác.
// Lô đã THAY dòng cũ (deleted_count > 0) không hoàn tác được: dòng cũ đã xóa lúc ghi, hoàn tác
// chỉ xóa được dòng mới và để lại một khoảng ngày trống — nút bị khóa kèm lời giải thích.
import { useCallback, useEffect, useState } from 'react'
import { api } from '../../api/client'
import { useAuth } from '../../auth/AuthContext'
import { askConfirm } from '../confirm'
import Pagination from '../Pagination'
import { toast } from '../toast'
import CustomsModal from './CustomsModal'
import { StatusBadge } from './CustomsImportDialog'
import { fmtDate } from './customs-shared'

const fmtDateTime = (iso?: string) => (iso ? `${fmtDate(iso)} ${iso.slice(11, 16)}` : '—')

export default function CustomsHistoryDialog({ onClose, onChanged }: { onClose: () => void; onChanged: () => void }) {
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
    const ok = await askConfirm({
      title: 'Hoàn tác lô nạp',
      message: `Xóa ${b.created_count} dòng hàng của tệp «${b.filename}»? Dữ liệu khoảng ${fmtDate(b.date_from)} → ${fmtDate(b.date_to)} sẽ trống.`,
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

  return (
    <CustomsModal title="Lịch sử nạp dữ liệu hải quan" width={1000} onClose={onClose}>
      <div className="table-scroll"><table>
        <thead><tr>
          <th>#</th><th>Tệp</th><th>Loại</th><th>Trạng thái</th><th style={{ textAlign: 'right' }}>Dòng hàng</th>
          <th>Khoảng ngày</th><th style={{ textAlign: 'right' }}>Vá ngày</th><th style={{ textAlign: 'right' }}>Thay dòng cũ</th>
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
              <td>{b.date_from ? `${fmtDate(b.date_from)} → ${fmtDate(b.date_to)}` : '—'}</td>
              <td style={{ textAlign: 'right' }}>{b.date_fixed || 0}</td>
              <td style={{ textAlign: 'right' }}>{b.deleted_count || 0}</td>
              <td>{b.created_by_name || '—'}</td>
              <td>{fmtDateTime(b.finished_at || b.created_at)}</td>
              <td style={{ whiteSpace: 'nowrap' }}>
                <button className="btn ghost" title="Nhật ký dòng lỗi / cảnh báo" onClick={() => setLogsOf(b)}>
                  <i className="ti ti-list-details" />
                </button>
                {b.mode === 1 && b.status === 2 && can('customs_price', 'delete') && (
                  <button className="btn ghost" disabled={b.deleted_count > 0} onClick={() => revert(b)}
                    title={b.deleted_count > 0
                      ? `Lô này đã thay ${b.deleted_count} dòng cũ nên không hoàn tác được — nạp lại tệp đúng để sửa.`
                      : 'Hoàn tác: xóa các dòng lô này đã ghi'}>
                    <i className="ti ti-arrow-back-up" />
                  </button>
                )}
              </td>
            </tr>
          ))}
          {!rows.length && <tr><td colSpan={11} className="table-empty">Chưa nạp lần nào</td></tr>}
        </tbody>
      </table></div>
      <div className="table-foot">
        <Pagination page={page} pageSize={20} total={total} hideSize onChange={(p) => setPage(p)} />
      </div>
      {logsOf && <BatchLogs batch={logsOf} onClose={() => setLogsOf(null)} />}
    </CustomsModal>
  )
}

const LEVELS: Record<number, [string, string]> = { 0: ['Thông tin', 'gray'], 1: ['Cảnh báo', 'warn'], 2: ['Cần rà', 'info'], 3: ['Lỗi', 'err'] }

function BatchLogs({ batch, onClose }: { batch: any; onClose: () => void }) {
  const [rows, setRows] = useState<any[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  useEffect(() => {
    api.get(`/api/customs/imports/${batch.id}/logs`, { params: { page, page_size: 50 } })
      .then((r) => { setRows(r.data.data.items); setTotal(r.data.data.total) })
  }, [batch.id, page])
  return (
    <CustomsModal title={`Nhật ký lô #${batch.id} — ${batch.filename}`} width={820} onClose={onClose}>
      {batch.error_summary && <div style={{ color: '#b91c1c', fontSize: 13, whiteSpace: 'pre-wrap', marginBottom: 10 }}>{batch.error_summary.split('\n')[0]}</div>}
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
