import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api/client'
import { useAuth } from '../auth/AuthContext'
import { toast } from './toast'
import { fmtPrice, fmtVND } from '../utils/money'
import Pagination from './Pagination'
import SearchSelect from './SearchSelect'
import MultiCheckSelect from './MultiCheckSelect'
import { prBadge, PR_STATUS } from '../config/cruds'
import { fmt } from './report-table'
import { PR_LINE_STATUSES, PR_LINE_STATUS_COLOR, prLineStatusLabel } from '../utils/statusLabels'

// bao-CR-295/296 — báo cáo "Chi tiết Yêu cầu mua hàng" theo DÒNG hàng, dùng chung cho
// tab trong Báo cáo mua hàng và trang riêng /pr-lines-report (soi mã hàng chưa được đặt).
// Bộ lọc TIẾN ĐỘ dòng hàng: 'chua_dat' là giá trị GỘP (backend hiểu = no_po + not_ordered)
// — đúng mục tiêu báo cáo: soi mã chưa được đặt để khỏi đặt sót đơn.
// B-06 (erp-v2): `line_status` lưu MÃ nên option lấy từ PR_LINE_STATUSES, khác bản main.
const PRL_LINE_STATUS = [
  { value: 'chua_dat', label: 'Chưa được đặt hàng (gộp)' },
  ...PR_LINE_STATUSES,
]

/** Mã các ĐMH của dòng — máy chủ trả chuỗi nối dấu phẩy, không trả id (bao-CR-691, khớp v2). */
function splitPoCodes(raw: string | null | undefined): string[] {
  return Array.from(new Set((raw || '').split(',').map((c) => c.trim()).filter(Boolean)))
}

/** Số lượng đã đặt / đã nhận: máy chủ cũ chưa trả thì để trống thay vì in 0 sai. */
function qtyOrDash(v: number | null | undefined) {
  return v == null ? '—' : fmt(v)
}

export default function PrLinesReport({ year, companyId }: { year: string; companyId: string }) {
  //  bao-CR-691: tiến độ dòng chọn NHIỀU — mảng rỗng là Tất cả (không tự gán), gửi `line_status=a,b`.
  const [prlF, setPrlF] = useState<{ status: string; line_status: string[]; assignee: string; search: string }>(
    { status: '', line_status: [], assignee: '', search: '' })
  const [prlPage, setPrlPage] = useState(1)
  const [prlData, setPrlData] = useState<any>({ items: [], total: 0, assignees: [], page: 1, page_size: 50 })

  // Đổi Năm/Công ty ở ngoài -> quay về trang 1 (khỏi đứng ở trang không tồn tại của kỳ mới)
  useEffect(() => { setPrlPage((p) => (p === 1 ? p : 1)) }, [year, companyId])

  const { can } = useAuth()
  const canExport = can('report', 'export')
  const canReadPO = can('purchase_order', 'read')

  /** Bộ lọc đang chọn — DÙNG CHUNG cho bảng và nút Xuất Excel (bao-CR-691), để tệp xuất luôn khớp đúng bảng đang xem. */
  function filterParams(): Record<string, string> {
    const params: Record<string, string> = {}
    if (year) params.year = year
    if (companyId) params.company_id = companyId
    if (prlF.status) params.status = prlF.status
    if (prlF.line_status.length) params.line_status = prlF.line_status.join(',')
    if (prlF.assignee) params.assignee = prlF.assignee
    if (prlF.search) params.search = prlF.search
    return params
  }

  // Phân trang phía server (50/trang) như chi tiết chi phí vận chuyển
  useEffect(() => {
    const params = { ...filterParams(), page: prlPage, page_size: 50 }
    api.get('/api/reports/pr-lines', { params }).then((r) => setPrlData(r.data.data)).catch(() => {})
    // eslint-disable-next-line react-hooks/exhaustive-deps -- filterParams chỉ đọc đúng bốn giá trị dưới
  }, [year, companyId, prlF, prlPage])

  /** bao-CR-691 (khớp v2): xuất Excel ĐÚNG bộ lọc đang chọn, không phân trang — máy chủ chặn ở 5.000 dòng (400 có câu
   *  báo). Chép mẫu exportXlsx của Tiến độ đơn mua hàng: tên tệp theo máy chủ, lỗi là blob nên đọc text lấy message. */
  async function exportXlsx() {
    try {
      const r = await api.get('/api/reports/pr-lines/export', { params: filterParams(), responseType: 'blob' })
      const cd = String(r.headers['content-disposition'] || '')
      const name = /filename="?([^"]+)"?/.exec(cd)?.[1] || 'chi-tiet-yc-mua-hang-theo-dong.xlsx'
      const url = window.URL.createObjectURL(new Blob([r.data]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', name)
      document.body.appendChild(link)
      link.click()
      link.parentNode?.removeChild(link)
      window.URL.revokeObjectURL(url)
    } catch (e: any) {
      let msg = 'Lỗi khi xuất file Excel'
      try {
        const body = e?.response?.data
        const text = body instanceof Blob ? await body.text() : ''
        msg = JSON.parse(text)?.error?.message || msg
      } catch { /* giữ thông báo mặc định */ }
      toast.error(msg)
    }
  }

  return (
    <div className="card" style={{ padding: 16 }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 8, marginBottom: 10 }}>
        <h3 className="sec-title" style={{ margin: 0 }}>Chi tiết Yêu cầu mua hàng theo dòng hàng <span style={{ fontSize: 12, fontWeight: 400, color: 'var(--muted)' }}>(soi mã hàng chưa được đặt để không đặt sót đơn)</span></h3>
        <div className="no-print" style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 12.5, color: 'var(--muted)', flexWrap: 'wrap' }}>Lọc:
          <input className="input" style={{ width: 190 }} placeholder="Mã hàng / tên SP / mã PYC" defaultValue={prlF.search}
            onKeyDown={(e) => { if (e.key === 'Enter') { setPrlPage(1); setPrlF((s) => ({ ...s, search: (e.target as HTMLInputElement).value.trim() })) } }}
            onBlur={(e) => { const v = e.target.value.trim(); if (v !== prlF.search) { setPrlPage(1); setPrlF((s) => ({ ...s, search: v })) } }} />
          <div style={{ minWidth: 200 }}>
            <MultiCheckSelect value={prlF.line_status} placeholder="Tất cả tiến độ dòng" options={PRL_LINE_STATUS}
              onChange={(v) => { setPrlPage(1); setPrlF((s) => ({ ...s, line_status: v })) }} />
          </div>
          <div style={{ minWidth: 150 }}>
            <SearchSelect value={prlF.status} placeholder="Tất cả trạng thái phiếu"
              options={[{ value: '', label: 'Tất cả trạng thái phiếu' }, ...Object.entries(PR_STATUS).map(([k, v]) => ({ value: k, label: v.label }))]}
              onChange={(v) => { setPrlPage(1); setPrlF((s) => ({ ...s, status: v })) }} />
          </div>
          <div style={{ minWidth: 160 }}>
            <SearchSelect value={prlF.assignee} placeholder="Tất cả NSTM"
              options={[{ value: '', label: 'Tất cả NSTM' }, ...(prlData.assignees || []).map((a: any) => ({ value: a.code, label: a.name ? `${a.name} (${a.code})` : a.code }))]}
              onChange={(v) => { setPrlPage(1); setPrlF((s) => ({ ...s, assignee: v })) }} />
          </div>
          {canExport && (
            <button className="btn outline" onClick={exportXlsx} title="Xuất toàn bộ kết quả đang lọc ra Excel">
              <i className="ti ti-file-spreadsheet" />Xuất Excel
            </button>
          )}
        </div>
      </div>
      <div className="items-scroll">
        <table className="items-table" style={{ minWidth: 2000 }}>
          <thead><tr>
            <th>ID</th><th>Mã PYC</th><th style={{ minWidth: 96 }}>Ngày tạo</th><th>Người yêu cầu</th><th>Bộ phận</th>
            <th>Mã hàng</th><th>Tên sản phẩm</th><th>Kho nhận</th><th>Phân loại</th><th>Gram</th>
            <th style={{ textAlign: 'right' }}>SL</th><th style={{ textAlign: 'right' }}>Đơn giá</th>
            <th style={{ textAlign: 'right' }}>VAT</th><th style={{ textAlign: 'right' }}>Thành tiền</th>
            {/* 28/10/2026 bao-CR-691: Tiến độ của DÒNG đứng trước Trạng thái của PHIẾU — trước đây cột phiếu (Nháp) đứng trước dễ tưởng là của dòng */}
            <th>Tiến độ dòng</th><th>Trạng thái phiếu</th><th>Ngày dự kiến có hàng</th><th>NSTM phụ trách</th>
            {/* bao-CR-691 (khớp v2): ba cột theo dõi đặt / nhận — câu hỏi chính của báo cáo. Cột phụ khác: dùng Xuất Excel. */}
            <th style={{ textAlign: 'right' }}>SL đã đặt</th><th style={{ textAlign: 'right' }}>SL đã nhận</th><th style={{ minWidth: 140 }}>Mã ĐMH</th>
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
                <td><span className="badge wrap" style={{ background: (PR_LINE_STATUS_COLOR[r.line_status] || '#94a3b8') + '22', color: PR_LINE_STATUS_COLOR[r.line_status] || '#64748b' }}>{prLineStatusLabel(r.line_status)}</span></td><td>{prBadge(r.status)}</td>
                <td>{r.expected_date}</td><td>{r.assignee_name || r.assignee}</td>
                <td style={{ textAlign: 'right' }}>{qtyOrDash(r.qty_ordered)}</td>
                <td style={{ textAlign: 'right' }}>{qtyOrDash(r.qty_received)}</td>
                <td>{splitPoCodes(r.po_codes).length === 0 ? '—' : splitPoCodes(r.po_codes).map((code, i) => (
                  <span key={code}>{i > 0 && ', '}
                    {/* Máy chủ chỉ trả MÃ: dẫn sang danh sách ĐMH lọc sẵn theo mã. Thiếu quyền đọc ĐMH thì in chữ thường. */}
                    {canReadPO ? <Link to={`/purchase-orders?code=${encodeURIComponent(code)}`}>{code}</Link> : code}
                  </span>))}</td>
              </tr>))}
            {(prlData.total || 0) === 0 && <tr><td colSpan={21} style={{ textAlign: 'center', color: '#999', padding: 14 }}>{(prlF.status || prlF.line_status.length || prlF.assignee || prlF.search) ? 'Không có dòng khớp bộ lọc' : 'Chưa có dữ liệu'}</td></tr>}
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
