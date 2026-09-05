import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api/client'
import { fmtPrice, fmtVND } from '../utils/money'
import Pagination from './Pagination'
import SearchSelect from './SearchSelect'
import { prBadge, PR_STATUS } from '../config/cruds'
import { fmt } from './report-table'

// bao-CR-295/296 — báo cáo "Chi tiết Yêu cầu mua hàng" theo DÒNG hàng, dùng chung cho
// tab trong Báo cáo mua hàng và trang riêng /pr-lines-report (soi mã hàng chưa được đặt).
// Bộ lọc TIẾN ĐỘ dòng hàng: 'chua_dat' là giá trị GỘP (backend hiểu = Chưa tạo đơn mua hàng
// + Chưa đặt hàng) — đúng mục tiêu báo cáo: soi mã chưa được đặt để khỏi đặt sót đơn.
const PRL_LINE_STATUS = [
  { value: 'chua_dat', label: 'Chưa được đặt hàng (gộp)' },
  { value: 'Chưa tạo đơn mua hàng', label: 'Chưa tạo đơn mua hàng' },
  { value: 'Chưa đặt hàng', label: 'Chưa đặt hàng' },
  { value: 'Đã đặt hàng', label: 'Đã đặt hàng' },
  { value: 'Đã nhận hàng', label: 'Đã nhận hàng' },
  { value: 'Hoàn thành', label: 'Hoàn thành' },
  { value: 'Hủy đơn', label: 'Hủy đơn' },
]

export default function PrLinesReport({ year, companyId }: { year: string; companyId: string }) {
  const [prlF, setPrlF] = useState({ status: '', line_status: '', assignee: '', search: '' })
  const [prlPage, setPrlPage] = useState(1)
  const [prlData, setPrlData] = useState<any>({ items: [], total: 0, assignees: [], page: 1, page_size: 50 })

  // Đổi Năm/Công ty ở ngoài -> quay về trang 1 (khỏi đứng ở trang không tồn tại của kỳ mới)
  useEffect(() => { setPrlPage((p) => (p === 1 ? p : 1)) }, [year, companyId])

  // Phân trang phía server (50/trang) như chi tiết chi phí vận chuyển
  useEffect(() => {
    const params: any = { page: prlPage, page_size: 50 }
    if (year) params.year = year
    if (companyId) params.company_id = companyId
    if (prlF.status) params.status = prlF.status
    if (prlF.line_status) params.line_status = prlF.line_status
    if (prlF.assignee) params.assignee = prlF.assignee
    if (prlF.search) params.search = prlF.search
    api.get('/api/reports/pr-lines', { params }).then((r) => setPrlData(r.data.data)).catch(() => {})
  }, [year, companyId, prlF, prlPage])

  return (
    <div className="card" style={{ padding: 16 }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 8, marginBottom: 10 }}>
        <h3 className="sec-title" style={{ margin: 0 }}>Chi tiết Yêu cầu mua hàng theo dòng hàng <span style={{ fontSize: 12, fontWeight: 400, color: 'var(--muted)' }}>(soi mã hàng chưa được đặt để không đặt sót đơn)</span></h3>
        <div className="no-print" style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 12.5, color: 'var(--muted)', flexWrap: 'wrap' }}>Lọc:
          <input className="input" style={{ width: 190 }} placeholder="Mã hàng / tên SP / mã PYC" defaultValue={prlF.search}
            onKeyDown={(e) => { if (e.key === 'Enter') { setPrlPage(1); setPrlF((s) => ({ ...s, search: (e.target as HTMLInputElement).value.trim() })) } }}
            onBlur={(e) => { const v = e.target.value.trim(); if (v !== prlF.search) { setPrlPage(1); setPrlF((s) => ({ ...s, search: v })) } }} />
          <div style={{ minWidth: 160 }}>
            <SearchSelect value={prlF.line_status} placeholder="Tất cả tiến độ"
              options={[{ value: '', label: 'Tất cả tiến độ' }, ...PRL_LINE_STATUS]}
              onChange={(v) => { setPrlPage(1); setPrlF((s) => ({ ...s, line_status: v })) }} />
          </div>
          <div style={{ minWidth: 150 }}>
            <SearchSelect value={prlF.status} placeholder="Tất cả trạng thái"
              options={[{ value: '', label: 'Tất cả trạng thái' }, ...Object.entries(PR_STATUS).map(([k, v]) => ({ value: k, label: v.label }))]}
              onChange={(v) => { setPrlPage(1); setPrlF((s) => ({ ...s, status: v })) }} />
          </div>
          <div style={{ minWidth: 160 }}>
            <SearchSelect value={prlF.assignee} placeholder="Tất cả NSTM"
              options={[{ value: '', label: 'Tất cả NSTM' }, ...(prlData.assignees || []).map((a: any) => ({ value: a.code, label: a.name ? `${a.name} (${a.code})` : a.code }))]}
              onChange={(v) => { setPrlPage(1); setPrlF((s) => ({ ...s, assignee: v })) }} />
          </div>
        </div>
      </div>
      <div className="items-scroll">
        <table className="items-table" style={{ minWidth: 1650 }}>
          <thead><tr>
            <th>ID</th><th>Mã PYC</th><th style={{ minWidth: 96 }}>Ngày tạo</th><th>Người yêu cầu</th><th>Bộ phận</th>
            <th>Mã hàng</th><th>Tên sản phẩm</th><th>Kho nhận</th><th>Phân loại</th><th>Gram</th>
            <th style={{ textAlign: 'right' }}>SL</th><th style={{ textAlign: 'right' }}>Đơn giá</th>
            <th style={{ textAlign: 'right' }}>VAT</th><th style={{ textAlign: 'right' }}>Thành tiền</th>
            <th>Trạng thái</th><th>Tiến độ</th><th>Ngày dự kiến có hàng</th><th>NSTM phụ trách</th>
          </tr></thead>
          <tbody>
            {(prlData.items || []).map((r: any) => (
              <tr key={r.id}>
                <td>{r.id}</td>
                <td><Link to={`/purchase-requests/${r.pr_id}`}>{r.pr_code}</Link></td>
                <td style={{ whiteSpace: 'nowrap' }}>{r.created_date}</td><td>{r.requester}</td><td>{r.department}</td>
                <td>{r.product_code}</td><td>{r.product_name}</td><td>{r.warehouse}</td><td>{r.item_group}</td><td>{r.gram}</td>
                <td style={{ textAlign: 'right' }}>{fmt(r.qty)}</td>
                <td style={{ textAlign: 'right' }}>{fmtPrice(r.price)}</td>
                <td style={{ textAlign: 'right' }}>{r.vat_pct ? `${fmt(r.vat_pct)}%` : ''}</td>
                <td style={{ textAlign: 'right' }}>{fmtVND(r.amount)}</td>
                <td>{prBadge(r.status)}</td><td>{r.line_status}</td>
                <td>{r.expected_date}</td><td>{r.assignee_name || r.assignee}</td>
              </tr>))}
            {(prlData.total || 0) === 0 && <tr><td colSpan={18} style={{ textAlign: 'center', color: '#999', padding: 14 }}>{(prlF.status || prlF.line_status || prlF.assignee || prlF.search) ? 'Không có dòng khớp bộ lọc' : 'Chưa có dữ liệu'}</td></tr>}
          </tbody>
        </table>
      </div>
      {prlData.total > 0 && (
        <div className="no-print" style={{ marginTop: 10 }}>
          <Pagination page={prlData.page} pageSize={prlData.page_size} total={prlData.total}
            hideSize onChange={(p) => setPrlPage(p)} />
        </div>
      )}
    </div>
  )
}
