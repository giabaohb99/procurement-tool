import { useEffect, useState } from 'react'
import { api } from '../api/client'
import { fmtPrice, fmtVND } from '../utils/money'
import { useAuth } from '../auth/AuthContext'

/**
 * bao-CR-347 — Báo cáo giá vốn lô hàng nhập khẩu, HAI CÁCH ĐỌC trên cùng một lần lọc:
 *
 * - **Theo lô** (`LandedCostTable`) XOAY DỌC so với mọi báo cáo khác: mỗi ĐƠN là một CỘT,
 *   mỗi chỉ tiêu là một DÒNG, đúng mẫu kế toán khách đang dùng.
 * - **Theo dòng hàng** (`LandedCostItemTable`) là bảng ngang bình thường: mỗi mã hàng một
 *   dòng, chi phí của lô đã chia về tới dòng đó, ra giá vốn mỗi đơn vị.
 *
 * Hai bảng tách riêng để tab báo cáo và bản in ký tay dùng CHUNG một cách bày số — sửa một
 * chỗ là hai nơi cùng đổi. Tên loại chi phí lấy từ `data.cost_types` (danh mục của hệ thống,
 * chỉ loại có phát sinh), nên bố cục đổi theo lần lọc.
 *
 * Tên chỉ tiêu gọi theo TRƯỜNG của đơn mua hàng, không chép mẫu giấy của khách: đơn khai
 * đồng tiền riêng nên là "Tiền hàng (nguyên tệ)" chứ không phải "Giá đô", và có hẳn một
 * dòng "Đồng tiền" để đọc con số đó. Lọc trúng nhiều đồng tiền thì cột TỔNG bỏ trống ô
 * nguyên tệ — chỉ cộng được cột đã quy đổi VNĐ.
 */
export type LandedCostView = 'orders' | 'items'

export const VIEW_OPTS: { value: LandedCostView; label: string }[] = [
  { value: 'orders', label: 'Theo lô hàng' },
  { value: 'items', label: 'Chi tiết theo dòng hàng' },
]

const fmtQty = (n: any) => Number(n || 0).toLocaleString('vi-VN', { maximumFractionDigits: 3 })
const dmy = (d: string) => { if (!d) return ''; const [y, m, dd] = String(d).split('-'); return `${dd}/${m}/${y}` }
const empty = (msg: string) => <div style={{ padding: 18, textAlign: 'center', color: '#999' }}>{msg}</div>

type Col = { title: string; row: any; isTotal?: boolean }

export function LandedCostTable({ data, compact }: { data: any; compact?: boolean }) {
  const costTypes: any[] = data?.cost_types || []
  const orders: any[] = data?.orders || []
  const cols: Col[] = orders.map((o) => ({ title: o.code || `#${o.po_id}`, row: o }))
  if (orders.length) cols.push({ title: 'TỔNG', row: data.totals || {}, isTotal: true })
  const fs = compact ? 10.5 : 12.5

  const row = (label: string, get: (c: Col) => any,
               opts?: { bold?: boolean; no?: string; blankTotal?: boolean; text?: boolean }) => (
    <tr>
      <td style={{ textAlign: 'center', color: 'var(--muted)' }}>{opts?.no || ''}</td>
      <td style={{
        fontWeight: opts?.bold ? 700 : 500,
        paddingLeft: opts?.no && opts.no.includes('.') ? 22 : undefined,
      }}>{label}</td>
      {cols.map((c, i) => (
        <td key={i} style={{
          textAlign: opts?.text ? 'left' : 'right', fontWeight: opts?.bold || c.isTotal ? 700 : 400,
          background: c.isTotal ? '#f4f7fa' : undefined,
        }}>{c.isTotal && opts?.blankTotal ? '' : get(c)}</td>
      ))}
    </tr>
  )

  if (!orders.length) return empty('Chưa chọn được đơn nhập khẩu nào.')

  return (
    <div className="items-scroll">
      <table className="items-table" style={{ minWidth: 520 + cols.length * 130, fontSize: fs }}>
        <thead>
          <tr>
            <th style={{ width: 44 }}>STT</th>
            <th style={{ minWidth: 220, textAlign: 'left' }}>CHỈ TIÊU</th>
            {cols.map((c, i) => (
              <th key={i} style={{ textAlign: 'right', background: c.isTotal ? '#eef3f7' : undefined }}>{c.title}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {row('Ngày đặt hàng', (c) => dmy(c.row.order_date || ''), { text: true, blankTotal: true })}
          {row('Nhà cung cấp', (c) => c.row.supplier_name || '', { text: true, blankTotal: true })}
          {row('Trạng thái', (c) => c.row.status_label || '', { text: true, blankTotal: true })}
          {row('Ngày hàng rời cảng (ETD)', (c) => dmy(c.row.etd_date || ''), { text: true, blankTotal: true })}
          {row('Số tờ khai hải quan', (c) => c.row.customs_decl_no || '', { text: true, blankTotal: true })}
          {row('Ngày tờ khai', (c) => dmy(c.row.customs_decl_date || ''), { text: true, blankTotal: true })}
          {row('Ghi chú', (c) => c.row.note || '', { text: true, blankTotal: true })}
          {row('Số lượng', (c) => fmtQty(c.row.qty_total))}
          {row('Khối lượng (kg)', (c) => fmtQty(c.row.weight_total))}
          {row('Đồng tiền', (c) => c.row.currency_mixed ? 'Nhiều loại' : (c.row.currency || ''), { text: true })}
          {/* Nhiều đồng tiền thì cột TỔNG bỏ trống: cộng yên với đô ra một số vô nghĩa. */}
          {row('Tiền hàng (nguyên tệ)', (c) => c.row.currency_mixed ? '' : fmtPrice(c.row.goods_amount))}
          {row('Tỷ giá', (c) => fmtPrice(c.row.exchange_rate), { blankTotal: true })}
          {row('Tiền hàng (vnd)', (c) => fmtVND(c.row.goods_base), { bold: true, no: '1' })}
          {row('Chi phí nhập khẩu (vnd)', (c) => fmtVND(c.row.cost_total), { bold: true, no: '2' })}
          {costTypes.map((g) => (
            <LandedCostTypeRow key={g.code} label={g.label} no={g.no} cols={cols} code={String(g.code)} />
          ))}
          {row('Tổng giá vốn (vnd)', (c) => fmtVND(c.row.landed_total), { bold: true })}
          {row('Giá vốn/Kg (vnd)', (c) => fmtPrice(c.row.price_per_kg), { bold: true })}
        </tbody>
      </table>
    </div>
  )
}

/** Một dòng loại chi phí của bảng theo lô — tách hàm để `cols.map` khỏi lồng ba tầng. */
function LandedCostTypeRow({ label, no, cols, code }: { label: string; no: string; cols: Col[]; code: string }) {
  return (
    <tr>
      <td style={{ textAlign: 'center', color: 'var(--muted)' }}>{no}</td>
      <td style={{ paddingLeft: 22 }}>{label}</td>
      {cols.map((c, i) => (
        <td key={i} style={{
          textAlign: 'right', fontWeight: c.isTotal ? 700 : 400,
          background: c.isTotal ? '#f4f7fa' : undefined,
        }}>{fmtVND(c.row.by_type?.[code] || 0)}</td>
      ))}
    </tr>
  )
}

export function LandedCostItemTable({ data, compact }: { data: any; compact?: boolean }) {
  const costTypes: any[] = data?.cost_types || []
  const rows: any[] = data?.items || []
  const totals: any = data?.item_totals || {}
  const fs = compact ? 10.5 : 12.5
  const money = { textAlign: 'right' as const }

  if (!rows.length) return empty('Chưa có dòng hàng nào trong các đơn đã chọn.')

  return (
    <div className="items-scroll">
      <table className="items-table" style={{ minWidth: 1280 + costTypes.length * 130, fontSize: fs }}>
        <thead>
          <tr>
            <th style={{ width: 44 }}>STT</th>
            <th style={{ minWidth: 110 }}>Mã đơn</th>
            <th style={{ minWidth: 92 }}>Ngày ETD</th>
            <th style={{ minWidth: 110 }}>Mã hàng</th>
            <th style={{ minWidth: 240, textAlign: 'left' }}>Tên hàng</th>
            <th style={{ minWidth: 60 }}>ĐVT</th>
            <th style={money}>Số lượng</th>
            <th style={money}>Khối lượng (kg)</th>
            <th style={money}>Tiền hàng (vnd)</th>
            {costTypes.map((g) => <th key={g.code} style={money}>{g.label}</th>)}
            <th style={money}>Tổng chi phí (vnd)</th>
            <th style={{ ...money, background: '#eef3f7' }}>Tổng giá vốn (vnd)</th>
            <th style={{ ...money, background: '#fff3cd' }}>Giá vốn/ĐVT (vnd)</th>
            <th style={money}>Giá vốn/Kg (vnd)</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((r, i) => (
            <tr key={i}>
              <td style={{ textAlign: 'center', color: 'var(--muted)' }}>{i + 1}</td>
              <td>{r.code}</td>
              <td>{dmy(r.etd_date || '')}</td>
              <td>{r.product_code}</td>
              <td>{r.product_name}</td>
              <td>{r.unit}</td>
              <td style={money}>{fmtQty(r.qty_order)}</td>
              <td style={money}>{fmtQty(r.weight_kg)}</td>
              <td style={money}>{fmtVND(r.goods_base)}</td>
              {costTypes.map((g) => <td key={g.code} style={money}>{fmtVND(r.by_type?.[String(g.code)] || 0)}</td>)}
              <td style={money}>{fmtVND(r.cost_base)}</td>
              <td style={{ ...money, fontWeight: 600, background: '#f4f7fa' }}>{fmtVND(r.landed_base)}</td>
              <td style={{ ...money, fontWeight: 700, background: '#fff8e6' }}>{fmtPrice(r.price_per_unit)}</td>
              <td style={money}>{fmtPrice(r.price_per_kg)}</td>
            </tr>
          ))}
          <tr style={{ fontWeight: 700, background: '#f4f7fa' }}>
            <td colSpan={6} style={{ textAlign: 'right' }}>TỔNG</td>
            <td style={money}>{fmtQty(totals.qty_order)}</td>
            <td style={money}>{fmtQty(totals.weight_kg)}</td>
            <td style={money}>{fmtVND(totals.goods_base)}</td>
            {costTypes.map((g) => <td key={g.code} style={money}>{fmtVND(totals.by_type?.[String(g.code)] || 0)}</td>)}
            <td style={money}>{fmtVND(totals.cost_base)}</td>
            <td style={money}>{fmtVND(totals.landed_base)}</td>
            {/* Không cộng giá vốn/ĐVT: mỗi dòng một đơn vị tính, cộng lại là số không đọc được */}
            <td />
            <td style={money}>{fmtPrice(totals.price_per_kg)}</td>
          </tr>
        </tbody>
      </table>
    </div>
  )
}

/** Cảnh báo lúc chia chi phí (thiếu khối lượng, gõ tay lệch tổng…) — không chặn, chỉ nói rõ. */
export function LandedCostWarnings({ data }: { data: any }) {
  const warnings: string[] = data?.warnings || []
  if (!warnings.length) return null
  return (
    <div style={{ fontSize: 12, background: '#fff8e6', border: '1px solid #f0d68a', borderRadius: 8, padding: '8px 12px', marginBottom: 10, lineHeight: 1.55 }}>
      <b style={{ color: '#b45309' }}>Lưu ý khi chia chi phí về dòng hàng:</b>
      <ul style={{ margin: '4px 0 0', paddingLeft: 20 }}>
        {warnings.map((w, i) => <li key={i}>{w}</li>)}
      </ul>
    </div>
  )
}

/** Ba ô ký tay của bản in — quản lý duyệt bằng chữ ký, không có luồng duyệt trong phần mềm. */
export function LandedCostSignatures() {
  const boxes = ['Người lập biểu', 'Kế toán', 'Quản lý duyệt']
  return (
    <div style={{ display: 'flex', justifyContent: 'space-around', marginTop: 28, textAlign: 'center' }}>
      {boxes.map((b) => (
        <div key={b} style={{ minWidth: 180 }}>
          <div style={{ fontWeight: 700, fontSize: 11.5 }}>{b}</div>
          <div style={{ fontStyle: 'italic', fontSize: 10.5, color: '#555' }}>(Ký, ghi rõ họ tên)</div>
          <div style={{ height: 62 }} />
        </div>
      ))}
    </div>
  )
}

/** Tham số lọc dùng chung cho gọi API, xuất Excel và mở bản in. */
export function landedCostParams(f: { codes: string; date_from: string; date_to: string }, companyId?: string) {
  const params: any = {}
  const codes = f.codes.split(',').map((c) => c.trim()).filter(Boolean).join(',')
  if (codes) params.codes = codes
  else { if (f.date_from) params.date_from = f.date_from; if (f.date_to) params.date_to = f.date_to }
  if (companyId) params.company_id = companyId
  return params
}

export default function ImportLandedCostReport({ year, companyId }: { year: string; companyId?: string }) {
  const { can } = useAuth()
  const y = year && year !== 'all' ? year : String(new Date().getFullYear())
  const [f, setF] = useState({ codes: '', date_from: `${y}-01-01`, date_to: `${y}-12-31` })
  // Một lần gọi API trả cả hai cách đọc, nên đổi tab KHÔNG tải lại số liệu.
  const [view, setView] = useState<LandedCostView>('orders')
  const [data, setData] = useState<any>(null)
  const [busy, setBusy] = useState(false)

  async function load() {
    setBusy(true)
    try {
      const r = await api.get('/api/reports/import-landed-cost', { params: landedCostParams(f, companyId) })
      setData(r.data.data)
    } finally { setBusy(false) }
  }
  useEffect(() => { load() }, [companyId])

  async function exportExcel() {
    try {
      const r = await api.get('/api/reports/import-landed-cost/export',
                              { params: landedCostParams(f, companyId), responseType: 'blob' })
      const url = window.URL.createObjectURL(new Blob([r.data]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', 'bao-cao-gia-von-nhap-khau.xlsx')
      document.body.appendChild(link); link.click(); link.remove()
      window.URL.revokeObjectURL(url)
    } catch { /* interceptor tự toast lỗi */ }
  }

  function openPrint() {
    const qs = new URLSearchParams({ ...landedCostParams(f, companyId), view }).toString()
    window.open(`/print/import-landed-cost?${qs}`, '_blank')
  }

  return (
    <div className="card" style={{ padding: 16 }}>
      <div className="no-print" style={{ display: 'flex', alignItems: 'flex-end', gap: 10, flexWrap: 'wrap', marginBottom: 12 }}>
        <div className="filter-item" style={{ flex: '1 1 240px', minWidth: 200 }}><label>Mã đơn (nhiều mã cách nhau dấu phẩy)</label>
          <input value={f.codes} placeholder="Để trống = lấy theo khoảng ngày đặt"
                 onChange={(e) => setF((s) => ({ ...s, codes: e.target.value }))} /></div>
        <div className="filter-item" style={{ flex: '0 0 150px' }}><label>Từ ngày đặt</label>
          <input type="date" value={f.date_from} disabled={!!f.codes.trim()}
                 onChange={(e) => setF((s) => ({ ...s, date_from: e.target.value }))} /></div>
        <div className="filter-item" style={{ flex: '0 0 150px' }}><label>Đến ngày đặt</label>
          <input type="date" value={f.date_to} disabled={!!f.codes.trim()}
                 onChange={(e) => setF((s) => ({ ...s, date_to: e.target.value }))} /></div>
        <button className="btn" disabled={busy} onClick={() => load()}>Xem</button>
        <button className="btn ghost" disabled={!data?.orders?.length} onClick={openPrint}><i className="ti ti-printer" />In</button>
        {can('report', 'export') && (
          <button className="btn ghost" disabled={!data?.orders?.length} onClick={exportExcel}>
            <i className="ti ti-file-spreadsheet" />Xuất Excel</button>
        )}
      </div>

      <div className="no-print" style={{ display: 'flex', gap: 6, borderBottom: '1px solid var(--border)', marginBottom: 12 }}>
        {VIEW_OPTS.map((o) => (
          <button key={o.value} className="btn ghost" onClick={() => setView(o.value)}
            style={{
              border: 'none', borderRadius: 0, borderBottom: `2px solid ${view === o.value ? 'var(--teal)' : 'transparent'}`,
              color: view === o.value ? 'var(--navy)' : 'var(--muted)', fontWeight: view === o.value ? 700 : 500,
            }}>{o.label}</button>
        ))}
      </div>

      <div style={{ fontSize: 12, color: 'var(--muted)', marginBottom: 10, background: '#f6f8fa', border: '1px solid var(--border)', borderRadius: 8, padding: '8px 12px', lineHeight: 1.55 }}>
        <i className="ti ti-info-circle" style={{ marginRight: 5, color: 'var(--teal)' }} />
        Chỉ tính <b>đơn nhập khẩu</b>. Bảng chỉ bày những <b>loại chi phí có phát sinh</b> trong lần lọc này.
        Tab <b>Chi tiết theo dòng hàng</b> chia chi phí của lô về từng mã hàng theo đúng cách phân bổ khai
        trên từng khoản chi. Số liệu tính tại thời điểm xem, không lưu lại.
      </div>
      <LandedCostWarnings data={data} />
      {busy && !data ? <div style={{ padding: 18, color: '#999' }}>Đang tải…</div>
        : view === 'items' ? <LandedCostItemTable data={data} /> : <LandedCostTable data={data} />}
    </div>
  )
}
