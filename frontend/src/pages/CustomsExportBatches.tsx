// bao-CR-728 (bê bao-CR-718 của bản v2) — "Lô xuất của tôi" (`/customs-prices/exports`): các lô XUẤT TOÀN BỘ chạy
// nền của chính người đang đăng nhập (Tra cứu thị trường → Danh sách → Xuất dữ liệu → Xuất toàn bộ theo bộ lọc). Mới
// nhất lên đầu; bấm dòng mở chi tiết lô để tải từng tệp. Còn lô chờ / đang xuất thì bảng tự hỏi lại mỗi 3 giây.
// Quyền: `customs_price.export` (backend `GET /api/customs/export-batches` gác cùng khóa).
import { useCallback, useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../api/client'
import { useAuth } from '../auth/AuthContext'
import Pagination from '../components/Pagination'
import { customsSectionPath } from '../config/customs-sections'
import {
  CustomsExportBatch, customsExportPath, exportStatusBadgeClass,
} from '../utils/customs-export'
import { fmtDateTime } from '../utils/datetime'

const PAGE_SIZE = 20
const POLL_MS = 3000

export default function CustomsExportBatches() {
  const { can } = useAuth()
  const navigate = useNavigate()
  const [rows, setRows] = useState<CustomsExportBatch[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [loading, setLoading] = useState(true)
  const allowed = can('customs_price', 'export')

  const load = useCallback(() => {
    if (!allowed) return
    api.get('/api/customs/export-batches', { params: { page, page_size: PAGE_SIZE } })
      .then((r) => { setRows(r.data.data.items); setTotal(r.data.data.total) })
      .finally(() => setLoading(false))
  }, [page, allowed])
  useEffect(() => { load() }, [load])

  //  Còn lô chưa xong thì hỏi lại tiến độ; xong hết thì thôi.
  const anyActive = rows.some((b) => b.active)
  useEffect(() => {
    if (!anyActive) return
    const t = setInterval(load, POLL_MS)
    return () => clearInterval(t)
  }, [anyActive, load])

  if (!allowed) return (
    <div className="card" style={{ padding: 24, color: 'var(--muted)' }}>
      Tài khoản chưa được cấp quyền <b>Xuất</b> của Tra cứu thị trường. Nhờ quản trị tick quyền này trên vai trò của bạn.
    </div>
  )

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
        <button className="btn ghost" title="Quay lại Tra cứu thị trường" aria-label="Quay lại Tra cứu thị trường"
          onClick={() => navigate(customsSectionPath('list'))}><i className="ti ti-arrow-left" /></button>
        <h2 className="page-title" style={{ margin: 0, flex: 1 }}>Lô xuất của tôi</h2>
      </div>
      <div style={{ fontSize: 13, color: 'var(--muted)', marginBottom: 10 }}>
        Các lần xuất toàn bộ dữ liệu theo bộ lọc, chạy nền và chia mỗi tệp tối đa 50.000 dòng. Bấm một lô để tải tệp.
      </div>
      <div className="card table-card">
        <div className="table-scroll"><table>
          <thead><tr>
            <th>Mã lô</th><th>Lúc tạo</th><th>Bộ lọc</th><th>Trạng thái</th>
            <th style={{ textAlign: 'right' }}>Tệp xong</th><th style={{ textAlign: 'right' }}>Số dòng</th><th>Hạn giữ</th>
          </tr></thead>
          <tbody>
            {rows.map((b) => (
              <tr key={b.id} className="clickable" onClick={() => navigate(customsExportPath(b.id))}>
                <td>#{b.id}</td>
                <td style={{ whiteSpace: 'nowrap' }}>{fmtDateTime(b.created_at)}</td>
                <td style={{ whiteSpace: 'normal', minWidth: 260 }}>{b.filter_summary || 'Toàn bộ dữ liệu'}</td>
                <td><span className={exportStatusBadgeClass(b.status)}>{b.status_label || `Trạng thái ${b.status}`}</span></td>
                <td style={{ textAlign: 'right' }}>{b.files_done}/{b.file_count}</td>
                <td style={{ textAlign: 'right' }}>{b.total_rows.toLocaleString('vi-VN')}</td>
                <td style={{ whiteSpace: 'nowrap' }}>{b.expires_at ? fmtDateTime(b.expires_at) : (b.active ? '—' : 'Giữ mãi')}</td>
              </tr>
            ))}
            {!loading && !rows.length && (
              <tr><td colSpan={7} className="table-empty">
                Chưa có lô xuất nào. Ở Tra cứu thị trường, bấm "Xuất dữ liệu" rồi chọn xuất toàn bộ theo bộ lọc.
              </td></tr>
            )}
          </tbody>
        </table></div>
        <div className="table-foot">
          <Pagination page={page} pageSize={PAGE_SIZE} total={total} hideSize onChange={(p) => setPage(p)} />
        </div>
      </div>
    </div>
  )
}
