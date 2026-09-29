// duoc-CR-490 — thẻ «Pháp lý», bấm số ở cột «Thuốc BVTV chứa» của một hoạt chất CẤM (TT 75/2025):
// danh sách thuốc trong danh mục BVTV đang chứa hoạt chất đó — MỌI tình trạng (số ở cột đếm đủ
// mọi tình trạng, lọc riêng ở đây thì số và danh sách sẽ lệch nhau). Bấm một thuốc mở TRANG chi
// tiết thuốc (duoc-CR-493); nút lùi của trang đưa về lại mục Pháp lý.
import { useCallback, useEffect, useState } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import { api } from '../../api/client'
import Pagination from '../Pagination'
import TableScroll from '../TableScroll'
import CustomsModal from './CustomsModal'
import { pesticideStatusBadgeClass } from '../../utils/customs-pesticide'
import { formatBannedLabel } from '../../utils/customs-regulation'

const PAGE_SIZE = 50

export default function CustomsBannedPesticideModal({ regulation, onClose }: {
  regulation: any | null
  onClose: () => void
}) {
  const navigate = useNavigate()
  const location = useLocation()
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(PAGE_SIZE)
  const [rows, setRows] = useState<any[]>([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(false)
  // Giữ dòng vừa mở để tiêu đề không nhảy về "hoạt chất cấm" lúc hộp đang đóng dần (cha đặt
  // `regulation = null` ngay khi bấm đóng, trước khi hộp kịp biến mất).
  const [shown, setShown] = useState(regulation)
  if (regulation && regulation !== shown) setShown(regulation)

  const load = useCallback(() => {
    if (regulation == null) return
    setLoading(true)
    api.get('/api/customs/pesticides', { params: { banned_regulation_id: regulation.id, page, page_size: pageSize } })
      .then((r) => { setRows(r.data.data.items); setTotal(r.data.data.total) })
      .finally(() => setLoading(false))
  }, [regulation, page, pageSize])
  useEffect(() => { load() }, [load])

  function close() {
    setPage(1)
    onClose()
  }

  return (
    <CustomsModal title={`Thuốc BVTV chứa ${shown?.name ?? 'hoạt chất cấm'}`} width={860} onClose={close}
      footer={<button className="btn ghost" onClick={close}>Đóng</button>}>
      {shown && (
        <div style={{ fontSize: 12, color: 'var(--muted)', marginBottom: 10 }}>
          {formatBannedLabel(shown.banned_year)} · {shown.legal_basis || 'TT 75/2025/TT-BNNMT'}. Khớp theo tên hoạt
          chất (danh mục thuốc không có số CAS) — chỉ để tham khảo, gồm cả thuốc đã hết hiệu lực.
        </div>
      )}
      <TableScroll>
        <table>
          <thead><tr><th>Tên thuốc</th><th>Hoạt chất</th><th>Công ty đăng ký</th><th>Số đăng ký</th><th>Tình trạng</th></tr></thead>
          <tbody>
            {rows.map((r) => (
              <tr key={r.id} className="clickable"
                onClick={() => navigate(`/customs-prices/pesticides/${r.id}`, { state: { from: `${location.pathname}${location.search}` } })}>
                <td><b>{r.trade_name}</b></td>
                <td>{r.active_ingredient}</td>
                <td>{r.registrant}</td>
                <td>{r.registration_no}</td>
                <td><span className={`badge ${pesticideStatusBadgeClass(r.status)}`}>{r.status_label || 'Chưa rõ'}</span></td>
              </tr>
            ))}
            {!loading && rows.length === 0 && (
              <tr><td colSpan={5} className="table-empty">Không còn thuốc nào trong danh mục chứa hoạt chất này.</td></tr>
            )}
          </tbody>
        </table>
      </TableScroll>
      <div className="table-foot">
        <Pagination page={page} pageSize={pageSize} total={total} onChange={(p, s) => { setPage(p); setPageSize(s) }} />
      </div>
    </CustomsModal>
  )
}
