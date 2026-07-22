import { useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../api/client'
import SearchSelect from '../components/SearchSelect'
import Pagination from '../components/Pagination'
import { fmtDate } from '../utils/datetime'

const fmt = (n: any) => Number(n || 0).toLocaleString('vi-VN')
const NOWRAP = { whiteSpace: 'nowrap' as const, overflow: 'hidden', textOverflow: 'ellipsis' }

// Trạng thái tiến độ dòng (đồng bộ ĐMH) — dùng cho filter + badge màu
const PG_COLOR: Record<string, string> = {
  'Chưa đặt hàng': '#94a3b8', 'Đã đặt hàng': '#2563eb', 'Đã nhận hàng': '#0891b2',
  'Chưa gửi ĐMH cho KT': '#db2777', 'Đã gửi ĐMH cho KT': '#7c3aed',
  'Hoàn thành': '#16a34a', 'Tạm ngưng': '#d97706', 'Hủy đơn': '#dc2626',
}
const PG_OPTS = Object.keys(PG_COLOR)
const pgBadge = (s: string) =>
  <span className="badge" style={{ background: (PG_COLOR[s] || '#94a3b8') + '22', color: PG_COLOR[s] || '#64748b' }}>{s || '—'}</span>

// CL quy định − nhận: <0 = trễ (đỏ), >=0 = đúng/sớm (xanh)
const diffCell = (n: number) =>
  <span style={{ color: n < 0 ? 'var(--red)' : n > 0 ? 'var(--green)' : 'var(--muted)' }}>{n || 0}</span>

export default function PurchaseProgress() {
  const navigate = useNavigate()
  const [rows, setRows] = useState<any[]>([])
  const [total, setTotal] = useState(0)
  const [showSupplier, setShowSupplier] = useState(true)
  const [companies, setCompanies] = useState<any[]>([])
  const [departments, setDepartments] = useState<any[]>([])
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(20)
  const [f, setF] = useState<any>({
    company_id: '', department: '', month: '', status: '', q: '',
    order_date_from: '', order_date_to: '', received_date_from: '', received_date_to: '',
  })
  const setFilter = (k: string, v: any) => { setF((s: any) => ({ ...s, [k]: v })); setPage(1) }
  const lbl = { fontSize: 12, color: 'var(--muted)' } as const

  async function load() {
    const p: any = { page, page_size: pageSize }
    Object.entries(f).forEach(([k, v]) => { const val = typeof v === 'string' ? v.trim() : v; if (val) p[k] = val })
    const r = await api.get('/api/purchase-progress', { params: p })
    const d = r.data.data
    setRows(d.items); setTotal(d.total); setShowSupplier(d.show_supplier)
  }
  useEffect(() => {
    api.get('/api/companies', { params: { page_size: 200 } }).then((r) => setCompanies(r.data.data.items))
    api.get('/api/departments', { params: { page_size: 500 } }).then((r) => setDepartments(r.data.data.items)).catch(() => {})
  }, [])

  // Tự tìm khi đổi filter (debounce) hoặc đổi trang
  const timer = useRef<any>(null)
  useEffect(() => {
    clearTimeout(timer.current)
    timer.current = setTimeout(load, 300)
    return () => clearTimeout(timer.current)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [f, page, pageSize])

  const companyName = (cid: number) => companies.find((c) => c.id === cid)?.name || '—'

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12, flexWrap: 'wrap', gap: 10 }}>
        <h2 className="page-title" style={{ margin: 0 }}>Tiến độ mua hàng</h2>
        <div style={{ fontSize: 12.5, color: 'var(--muted)' }}>Theo từng lần giao hàng · {fmt(total)} dòng</div>
      </div>

      <div className="card filters" style={{ padding: 14, marginBottom: 12, display: 'flex', gap: 10, flexWrap: 'wrap', alignItems: 'flex-end' }}>
        <div style={{ minWidth: 180 }}><label style={lbl}>Công ty</label>
          <SearchSelect value={f.company_id} placeholder="Tất cả"
            options={companies.map((c) => ({ value: String(c.id), label: c.name }))}
            onChange={(v) => setFilter('company_id', v)} />
        </div>
        <div style={{ minWidth: 180 }}><label style={lbl}>Bộ phận</label>
          <SearchSelect value={f.department} placeholder="Tất cả"
            options={departments.map((d) => ({ value: d.name, label: d.name }))}
            onChange={(v) => setFilter('department', v)} />
        </div>
        <div style={{ minWidth: 140 }}><label style={lbl}>Tháng (đặt hàng)</label>
          <input type="month" value={f.month} onChange={(e) => setFilter('month', e.target.value)} /></div>
        <div style={{ minWidth: 180 }}><label style={lbl}>Trạng thái tiến độ</label>
          <SearchSelect value={f.status} placeholder="Tất cả"
            options={PG_OPTS.map((s) => ({ value: s, label: s }))}
            onChange={(v) => setFilter('status', v)} />
        </div>
        <div><label style={lbl}>Ngày ĐH từ</label>
          <input type="date" value={f.order_date_from} onChange={(e) => setFilter('order_date_from', e.target.value)} /></div>
        <div><label style={lbl}>đến</label>
          <input type="date" value={f.order_date_to} onChange={(e) => setFilter('order_date_to', e.target.value)} /></div>
        <div><label style={lbl}>Ngày nhận từ</label>
          <input type="date" value={f.received_date_from} onChange={(e) => setFilter('received_date_from', e.target.value)} /></div>
        <div><label style={lbl}>đến</label>
          <input type="date" value={f.received_date_to} onChange={(e) => setFilter('received_date_to', e.target.value)} /></div>
        <div style={{ minWidth: 200, flex: 1 }}><label style={lbl}>Tìm kiếm</label>
          <input value={f.q} placeholder="Mã ĐMH / PYC / mã, tên SP…" onChange={(e) => setFilter('q', e.target.value)} /></div>
        <button className="btn ghost" onClick={() => setF({
          company_id: '', department: '', month: '', status: '', q: '',
          order_date_from: '', order_date_to: '', received_date_from: '', received_date_to: '',
        })}>Xóa lọc</button>
      </div>

      <div className="card">
        <div className="items-scroll">
          <table className="items-table wide-table" style={{ minWidth: showSupplier ? 5138 : 4258, tableLayout: 'fixed' }}>
            <colgroup>
              <col style={{ width: 44 }} />{/* STT */}
              <col style={{ width: 150 }} />{/* Mã ĐMH */}
              <col style={{ width: 92 }} />{/* Mã MISA */}
              <col style={{ width: 104 }} />{/* Mã PYC */}
              <col style={{ width: 180 }} />{/* Công ty */}
              <col style={{ width: 124 }} />{/* Bộ phận */}
              {showSupplier && <><col style={{ width: 130 }} />{/* Mã NCC */}<col style={{ width: 230 }} />{/* Nhà cung cấp */}</>}
              <col style={{ width: 150 }} />{/* NSPT */}
              <col style={{ width: 88 }} />{/* Ngày ĐH */}
              <col style={{ width: 140 }} />{/* Mã SP */}
              <col style={{ width: 220 }} />{/* Tên SP */}
              <col style={{ width: 150 }} />{/* Tên hóa đơn */}
              <col style={{ width: 120 }} />{/* Nhóm hàng */}
              <col style={{ width: 190 }} />{/* Quy cách */}
              <col style={{ width: 84 }} />{/* Mã HH */}
              <col style={{ width: 92 }} />{/* Số HĐ */}
              <col style={{ width: 88 }} />{/* Ngày cần */}
              <col style={{ width: 56 }} />{/* ĐVT */}
              <col style={{ width: 76 }} />{/* SL YC */}
              <col style={{ width: 76 }} />{/* SL đặt */}
              <col style={{ width: 96 }} />{/* Đơn giá */}
              <col style={{ width: 60 }} />{/* VAT% */}
              <col style={{ width: 128 }} />{/* Thành tiền ĐH */}
              <col style={{ width: 140 }} />{/* Tiến độ */}
              <col style={{ width: 72 }} />{/* Lần giao */}
              <col style={{ width: 96 }} />{/* Kho */}
              {showSupplier && <><col style={{ width: 160 }} />{/* Mã ĐVVC */}<col style={{ width: 160 }} />{/* Đơn vị VC */}</>}
              <col style={{ width: 84 }} />{/* SL giao */}
              <col style={{ width: 84 }} />{/* SL nhận */}
              <col style={{ width: 100 }} />{/* Cam kết giao */}
              <col style={{ width: 100 }} />{/* Dự kiến nhận */}
              <col style={{ width: 100 }} />{/* Ngày nhận */}
              <col style={{ width: 76 }} />{/* Ngày QĐ */}
              <col style={{ width: 108 }} />{/* Ngày quy định */}
              <col style={{ width: 84 }} />{/* CL cam kết */}
              <col style={{ width: 84 }} />{/* CL quy định */}
              <col style={{ width: 76 }} />{/* CL vs YC */}
              <col style={{ width: 108 }} />{/* Số HĐ (giao) */}
              {showSupplier && <><col style={{ width: 96 }} /><col style={{ width: 108 }} /></>}
              <col style={{ width: 64 }} />{/* QC */}
              <col style={{ width: 108 }} />{/* TT giao */}
              <col style={{ width: 128 }} />{/* Thành tiền nhận */}
              <col style={{ width: 150 }} />{/* Hồ sơ CT */}
            </colgroup>
            <thead>
              <tr>
                <th style={{ textAlign: 'right' }}>STT</th>
                <th>Mã ĐMH</th><th>Mã MISA</th><th>Mã PYC</th><th>Công ty</th><th>Bộ phận</th>
                {showSupplier && <><th>Mã NCC</th><th>Nhà cung cấp</th></>}
                <th>NSPT</th><th>Ngày ĐH</th>
                <th>Mã SP</th><th>Tên SP</th><th>Tên hóa đơn</th><th>Nhóm hàng</th><th>Quy cách</th>
                <th>Mã HH</th><th>Số HĐ</th><th>Ngày cần</th><th>ĐVT</th>
                <th style={{ textAlign: 'right' }}>SL YC</th><th style={{ textAlign: 'right' }}>SL đặt</th>
                <th style={{ textAlign: 'right' }}>Đơn giá</th><th style={{ textAlign: 'right' }}>VAT%</th>
                <th style={{ textAlign: 'right' }}>Thành tiền ĐH</th>
                <th>Tiến độ</th>
                <th style={{ textAlign: 'right' }}>Lần giao</th><th>Kho</th>
                {showSupplier && <><th>Mã ĐVVC</th><th>Đơn vị VC</th></>}
                <th style={{ textAlign: 'right' }}>SL giao</th><th style={{ textAlign: 'right' }}>SL nhận</th>
                <th>Cam kết giao</th><th>Dự kiến nhận</th><th>Ngày nhận</th>
                <th style={{ textAlign: 'right' }}>Ngày QĐ</th><th>Ngày quy định</th>
                <th style={{ textAlign: 'right' }}>CL cam kết</th><th style={{ textAlign: 'right' }}>CL quy định</th>
                <th style={{ textAlign: 'right' }}>CL vs YC</th>
                <th>Số HĐ (giao)</th>
                {showSupplier && <><th style={{ textAlign: 'right' }}>Đơn giá VC</th><th style={{ textAlign: 'right' }}>Tiền VC</th></>}
                <th>QC</th><th>TT giao</th>
                <th style={{ textAlign: 'right' }}>Thành tiền nhận</th>
                <th>Hồ sơ CT</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((r, i) => (
                <tr key={`${r.item_id}-${r.delivery_id ?? 'x'}-${i}`}>
                  <td style={{ textAlign: 'right', color: 'var(--muted)' }}>{r.stt ?? (page - 1) * pageSize + i + 1}</td>
                  <td style={NOWRAP}><a href={`/purchase-orders/${r.po_id}`}
                    onClick={(e) => { e.preventDefault(); navigate(`/purchase-orders/${r.po_id}`) }}
                    style={{ cursor: 'pointer', color: 'var(--navy)', fontWeight: 600, textDecoration: 'underline' }}
                    title="Mở đơn mua hàng">{r.po_code}</a></td>
                  <td style={{ ...NOWRAP, color: 'var(--muted)' }}>{r.misa_code}</td>
                  <td style={{ ...NOWRAP, color: 'var(--muted)' }}>{r.pr_code}</td>
                  <td>{companyName(r.company_id)}</td><td>{r.department}</td>
                  {showSupplier && <><td style={{ ...NOWRAP, color: 'var(--muted)' }}>{r.supplier_code}</td><td>{r.supplier_name}</td></>}
                  <td>{r.nspt}</td><td style={NOWRAP}>{fmtDate(r.order_date)}</td>
                  <td style={{ ...NOWRAP, color: 'var(--muted)' }}>{r.product_code}</td>
                  <td style={{ fontWeight: 500 }}>{r.product_name}</td>
                  <td>{r.invoice_name}</td><td>{r.item_group}</td><td>{r.spec}</td>
                  <td style={{ ...NOWRAP, color: 'var(--muted)' }}>{r.fg_code}</td><td style={NOWRAP}>{r.invoice_no}</td>
                  <td style={NOWRAP}>{fmtDate(r.required_date)}</td><td>{r.unit}</td>
                  <td style={{ textAlign: 'right' }}>{fmt(r.qty_request)}</td>
                  <td style={{ textAlign: 'right' }}>{fmt(r.qty_order)}</td>
                  <td style={{ textAlign: 'right' }}>{fmt(r.price)}</td>
                  <td style={{ textAlign: 'right' }}>{r.vat || 0}</td>
                  <td style={{ textAlign: 'right', fontWeight: 600 }}>{fmt(r.order_amount)}</td>
                  <td>{pgBadge(r.progress_status)}</td>
                  <td style={{ textAlign: 'right' }}>{r.delivery_no ?? '—'}</td><td style={NOWRAP}>{r.warehouse_code}</td>
                  {showSupplier && <><td style={{ ...NOWRAP, color: 'var(--muted)' }}>{r.carrier_code}</td><td>{r.carrier_name}</td></>}
                  <td style={{ textAlign: 'right' }}>{fmt(r.ship_qty)}</td>
                  <td style={{ textAlign: 'right' }}>{fmt(r.received_qty)}</td>
                  <td style={NOWRAP}>{fmtDate(r.promised_date)}</td><td style={NOWRAP}>{fmtDate(r.expected_date)}</td><td style={NOWRAP}>{fmtDate(r.received_date)}</td>
                  <td style={{ textAlign: 'right' }}>{r.std_days || 0}</td><td style={NOWRAP}>{fmtDate(r.regulated_date)}</td>
                  <td style={{ textAlign: 'right' }}>{diffCell(r.diff_promise)}</td>
                  <td style={{ textAlign: 'right' }}>{diffCell(r.diff_regulated)}</td>
                  <td style={{ textAlign: 'right' }}>{diffCell(r.diff_required)}</td>
                  <td style={NOWRAP}>{r.delivery_invoice_no}</td>
                  {showSupplier && <><td style={{ textAlign: 'right' }}>{fmt(r.shipping_unit_price)}</td><td style={{ textAlign: 'right' }}>{fmt(r.shipping_amount)}</td></>}
                  <td>{r.qc_result}</td><td>{r.delivery_status}</td>
                  <td style={{ textAlign: 'right', fontWeight: 600 }}>{fmt(r.amount)}</td>
                  <td>{r.document_status}</td>
                </tr>
              ))}
              {rows.length === 0 && <tr><td colSpan={showSupplier ? 46 : 40} style={{ textAlign: 'center', color: '#999', padding: 20 }}>Chưa có dữ liệu tiến độ</td></tr>}
            </tbody>
          </table>
        </div>
        <Pagination page={page} pageSize={pageSize} total={total}
          onChange={(p, s) => { setPage(p); setPageSize(s) }} />
      </div>
      <div style={{ marginTop: 8, fontSize: 12.5, color: 'var(--muted)' }}>
        * Mỗi dòng = 1 lần giao của 1 sản phẩm trên đơn mua hàng.
        {!showSupplier && ' Cột nhà cung cấp & chi phí vận chuyển được ẩn theo quyền của bạn.'}
      </div>
    </div>
  )
}
