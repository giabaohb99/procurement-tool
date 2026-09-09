import { Fragment, useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { api } from '../api/client'
import NotFound from '../components/NotFound'
import { tenFileIn, usePrintTitle } from '../hooks/usePrintTitle'

/**
 * bao-CR-319 P4 — Bản in ĐƠN MUA HÀNG NHẬP KHẨU, 4 khối:
 *   A. Hàng hóa (VAT dòng hàng luôn 0, có cột kg)
 *   B. Chi phí lô hàng, lồng 2 tầng theo LOẠI chi phí, kèm NCC của từng khoản
 *   C. Phải trả theo từng NHÀ CUNG CẤP (NCC bán hàng + từng NCC dịch vụ / thuế)
 *   D. Chi phí chia về từng dòng hàng (chỉ để xem — backend chia, không lưu, không vào kho)
 * Hai bản in thường (Đơn đặt hàng / Đơn mua hàng) giữ nguyên, không đụng.
 * Mọi con số ở B/C/D đều ĐÃ QUY ĐỔI về VNĐ; khối A in cả nguyên tệ lẫn quy đổi.
 */
const fmtQty = (n: any) => Number(n || 0).toLocaleString('vi-VN', { maximumFractionDigits: 4 })
const fmtPrice = (n: any) => Number(n || 0).toLocaleString('vi-VN', { maximumFractionDigits: 4 })
const fmtVND = (n: any) => Math.round(Number(n) || 0).toLocaleString('vi-VN')
const fmtPct = (r: any) => `${(Number(r || 0) * 100).toFixed(2)}%`
function dmy(d: string) { if (!d) return ''; const [y, m, dd] = d.split('-'); return `${dd}/${m}/${y}` }

export default function PrintPurchaseOrderImport() {
  const { id } = useParams()
  const [po, setPo] = useState<any>(null)
  const [notFound, setNotFound] = useState(false)
  useEffect(() => {
    setNotFound(false)
    api.get(`/api/purchase-orders/${id}/print`, { _silent: true } as any)
      .then((r) => setPo(r.data.data))
      .catch(() => setNotFound(true))
  }, [id])
  usePrintTitle(po ? tenFileIn(`${po.code}-NK`, po.order_date) : '')
  if (notFound) return (
    <NotFound backTo="/purchase-orders"
              message="Đơn mua hàng này không tồn tại, đã bị xóa hoặc bạn không có quyền in." />
  )
  if (!po) return <div style={{ padding: 40 }}>Đang tải...</div>

  const co = po.company || {}
  const sup = po.supplier || {}
  const items: any[] = po.items || []
  const costs: any[] = po.import_costs || []
  const summary = po.import_cost_summary || { by_type: [], by_supplier: [], goods_base_total: 0, cost_total: 0, landed_total: 0 }
  const alloc = po.import_cost_allocation || { lines: [], warnings: [], goods_base_total: 0, cost_total: 0, landed_total: 0 }
  const currency = (po.currency || 'VND').trim()
  const rate = Number(po.exchange_rate) || 1
  // bao-CR-319 P5: tiền hàng đã trả = tổng "Đã trả theo dòng" (B.28), chi phí đã chi lấy từ summary
  const goodsPaid = items.reduce((s, it) => s + (Number(it.paid_total) || 0), 0)
  const goodsForeign = items.reduce((s, it) => s + (Number(it.order_total) || 0), 0)

  // Khối B: lồng theo loại — mỗi loại một dòng tổng, bên dưới là từng khoản
  const byType: { label: string, rows: any[], total: number }[] = []
  for (const c of costs) {
    let g = byType.find((x) => x.label === c.cost_type_label)
    if (!g) { g = { label: c.cost_type_label || 'Khác', rows: [], total: 0 }; byType.push(g) }
    g.rows.push(c); g.total += Number(c.base_amount) || 0
  }
  byType.sort((a, b) => b.total - a.total)

  const cell = { border: '1px solid #555', padding: '3px 5px', fontSize: 10.5, verticalAlign: 'top' } as const
  const head = { ...cell, background: '#eef2f6', fontWeight: 700, textAlign: 'center' as const }
  const right = { ...cell, textAlign: 'right' as const }
  const bold = { fontWeight: 700 } as const
  const blockTitle = { fontSize: 12.5, fontWeight: 700, margin: '14px 0 4px', color: '#1a4d6b' } as const

  return (
    <div className="print-wrap" style={{ background: '#eee', minHeight: '100vh', padding: 16 }}>
      <style>{`@media print {
        @page { size: A4 portrait; margin: 0; }
        html, body { margin: 0 !important; background: #fff !important; }
        .no-print { display: none !important; }
        .print-wrap { padding: 0 !important; background: #fff !important; min-height: 0 !important; }
        .print-doc {
          padding: 10mm 12mm !important;
          -webkit-box-decoration-break: clone; box-decoration-break: clone;
        }
        .print-block { break-inside: avoid; }
      }`}</style>
      <div className="no-print" style={{ maxWidth: 800, margin: '0 auto 12px', display: 'flex', gap: 8 }}>
        <button className="btn" onClick={() => window.print()}>In / Lưu PDF</button>
        <button className="btn ghost" onClick={() => window.close()}>Đóng</button>
      </div>

      <div className="print-doc" style={{ maxWidth: 800, margin: '0 auto', background: '#fff', padding: '24px 30px', fontFamily: 'Arial, sans-serif', color: '#000' }}>
        <div style={{ borderBottom: '2px solid #1a4d6b', paddingBottom: 6 }}>
          <div style={{ fontWeight: 700, fontSize: 13 }}>{co.name || ''}</div>
          <div style={{ fontSize: 10.5, fontStyle: 'italic' }}>Địa chỉ: {co.address || ''}</div>
        </div>

        <h2 style={{ textAlign: 'center', fontSize: 17, margin: '12px 0 2px' }}>ĐƠN MUA HÀNG NHẬP KHẨU</h2>
        <div style={{ textAlign: 'center', fontSize: 10.5, fontStyle: 'italic', marginBottom: 8 }}>Kèm bảng chi phí lô hàng và chi phí phân bổ theo dòng hàng (chỉ để tham khảo, không phải giá vốn)</div>

        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 11.5, lineHeight: 1.8 }}>
          <div style={{ flex: 1 }}>
            <div><b>Nhà cung cấp:</b> {sup.name || po.supplier_name || ''}</div>
            <div><b>Địa chỉ:</b> {sup.address || ''}</div>
            <div><b>Mã số thuế:</b> {sup.tax_code || ''}</div>
            <div><b>Nhân viên mua hàng:</b> {po.nspt || ''}</div>
            <div><b>Diễn giải:</b> {po.note || ''}</div>
          </div>
          <div style={{ width: 250, paddingLeft: 12 }}>
            <div><b>Ngày:</b> {dmy(po.order_date)}</div>
            <div><b>Số:</b> {po.misa_code || po.code}</div>
            <div><b>Loại tiền:</b> {currency}{currency !== 'VND' ? ` — tỷ giá ${fmtPrice(rate)}` : ''}</div>
            <div><b>Tờ khai hải quan:</b> {po.customs_decl_no || '..........'}{po.customs_decl_date ? ` ngày ${dmy(po.customs_decl_date)}` : ''}</div>
          </div>
        </div>

        {/* ── A. Hàng hóa ── */}
        <div className="print-block">
          <div style={blockTitle}>A. HÀNG HÓA</div>
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr>
                <td style={head}>STT</td><td style={head}>Mã hàng</td><td style={head}>Tên hàng</td>
                <td style={head}>ĐVT</td><td style={head}>SL đặt</td><td style={head}>KL (kg)</td>
                <td style={head}>Đơn giá ({currency})</td><td style={head}>Thành tiền ({currency})</td>
                <td style={head}>Quy đổi (VNĐ)</td>
              </tr>
            </thead>
            <tbody>
              {items.map((it, i) => (
                <tr key={i}>
                  <td style={{ ...cell, textAlign: 'center' }}>{i + 1}</td>
                  <td style={cell}>{it.product_code}</td>
                  <td style={cell}>{it.product_name}{it.spec ? <div style={{ fontSize: 9.5, fontStyle: 'italic' }}>{it.spec}</div> : null}</td>
                  <td style={{ ...cell, textAlign: 'center' }}>{it.unit}</td>
                  <td style={right}>{fmtQty(it.qty_order)}</td>
                  <td style={right}>{it.weight_kg ? fmtQty(it.weight_kg) : '-'}</td>
                  <td style={right}>{fmtPrice(it.price)}</td>
                  <td style={right}>{fmtPrice(it.order_total)}</td>
                  <td style={right}>{fmtVND((Number(it.order_total) || 0) * (Number(it.exchange_rate) || rate))}</td>
                </tr>
              ))}
              <tr>
                <td style={{ ...cell, ...bold }} colSpan={7}>Tổng tiền hàng (VAT dòng hàng = 0, thuế nhập khẩu / GTGT hàng nhập khai ở khối B):</td>
                <td style={{ ...right, ...bold }}>{fmtPrice(goodsForeign)}</td>
                <td style={{ ...right, ...bold }}>{fmtVND(summary.goods_base_total)}</td>
              </tr>
            </tbody>
          </table>
        </div>

        {/* ── B. Chi phí lô hàng, lồng theo loại ── */}
        <div className="print-block">
          <div style={blockTitle}>B. CHI PHÍ LÔ HÀNG</div>
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr>
                <td style={head}>Loại / Diễn giải</td><td style={head}>Nhà cung cấp</td><td style={head}>Số HĐ</td>
                <td style={head}>Số tiền (nguyên tệ)</td><td style={head}>VAT</td><td style={head}>Cách chia</td>
                <td style={head}>Quy đổi gồm VAT (VNĐ)</td>
              </tr>
            </thead>
            <tbody>
              {byType.map((g) => (
                <Fragment key={g.label}>
                  <tr style={{ background: '#f6f8fa' }}>
                    <td style={{ ...cell, ...bold }} colSpan={6}>{g.label} ({g.rows.length} khoản)</td>
                    <td style={{ ...right, ...bold }}>{fmtVND(g.total)}</td>
                  </tr>
                  {g.rows.map((c, j) => (
                    <tr key={j}>
                      <td style={{ ...cell, paddingLeft: 18 }}>{c.description || '-'}</td>
                      <td style={cell}>{c.supplier_name || c.supplier_code}</td>
                      <td style={cell}>{c.invoice_no}{c.invoice_date ? ` (${dmy(c.invoice_date)})` : ''}</td>
                      <td style={right}>{fmtPrice(c.amount)} {c.currency}</td>
                      <td style={{ ...cell, textAlign: 'center' }}>{Number(c.vat) ? `${fmtQty(c.vat)}%` : '-'}</td>
                      <td style={cell}>{c.allocation_method_label}{c.allocation_target ? ` (${c.allocation_target})` : ''}</td>
                      <td style={right}>{fmtVND(c.base_amount)}</td>
                    </tr>
                  ))}
                </Fragment>
              ))}
              {costs.length === 0 && <tr><td style={{ ...cell, textAlign: 'center', fontStyle: 'italic' }} colSpan={7}>Chưa khai chi phí nào cho lô hàng này</td></tr>}
              <tr>
                <td style={{ ...cell, ...bold }} colSpan={6}>Tổng chi phí lô hàng:</td>
                <td style={{ ...right, ...bold }}>{fmtVND(summary.cost_total)}</td>
              </tr>
              <tr>
                <td style={{ ...cell, ...bold }} colSpan={6}>TỔNG GIÁ TRỊ LÔ HÀNG (tiền hàng + chi phí):</td>
                <td style={{ ...right, ...bold }}>{fmtVND(summary.landed_total)}</td>
              </tr>
            </tbody>
          </table>
        </div>

        {/* ── C. Phải trả theo từng NCC ── */}
        <div className="print-block">
          <div style={blockTitle}>C. PHẢI TRẢ THEO TỪNG NHÀ CUNG CẤP</div>
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr>
                <td style={head}>STT</td><td style={head}>Nhà cung cấp</td><td style={head}>Nội dung</td>
                <td style={head}>Số khoản</td><td style={head}>Phải trả (VNĐ)</td>
                <td style={head}>Đã chi (VNĐ)</td><td style={head}>Còn lại (VNĐ)</td>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td style={{ ...cell, textAlign: 'center' }}>1</td>
                <td style={cell}>{sup.name || po.supplier_name || ''}</td>
                <td style={cell}>Tiền hàng ({currency})</td>
                <td style={{ ...cell, textAlign: 'center' }}>{items.length} dòng</td>
                <td style={right}>{fmtVND(summary.goods_base_total)}</td>
                <td style={right}>{fmtVND(goodsPaid)}</td>
                <td style={right}>{fmtVND(Math.max((summary.goods_base_total || 0) - goodsPaid, 0))}</td>
              </tr>
              {(summary.by_supplier || []).map((s: any, i: number) => (
                <tr key={i}>
                  <td style={{ ...cell, textAlign: 'center' }}>{i + 2}</td>
                  <td style={cell}>{s.supplier_name || s.supplier_code || '(chưa chọn NCC)'}</td>
                  <td style={cell}>Chi phí lô hàng</td>
                  <td style={{ ...cell, textAlign: 'center' }}>{s.count} khoản</td>
                  <td style={right}>{fmtVND(s.base_amount)}</td>
                  <td style={right}>{fmtVND(s.paid_amount)}</td>
                  <td style={right}>{fmtVND(s.remaining)}</td>
                </tr>
              ))}
              <tr>
                <td style={{ ...cell, ...bold }} colSpan={4}>Tổng phải trả:</td>
                <td style={{ ...right, ...bold }}>{fmtVND(summary.landed_total)}</td>
                <td style={{ ...right, ...bold }}>{fmtVND(goodsPaid + (summary.paid_total || 0))}</td>
                <td style={{ ...right, ...bold }}>
                  {fmtVND(Math.max((summary.landed_total || 0) - goodsPaid - (summary.paid_total || 0), 0))}
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        {/* ── D. Chi phí phân bổ theo dòng hàng ── */}
        <div className="print-block">
          <div style={blockTitle}>D. CHI PHÍ PHÂN BỔ THEO DÒNG HÀNG</div>
          <div style={{ fontSize: 10, fontStyle: 'italic', marginBottom: 4 }}>
            Chia theo cách ghi ở từng khoản chi phí (khối B); phần lệch làm tròn dồn vào dòng cuối để tổng luôn khớp.
            Số này chỉ để tham khảo, không ghi nhận vào giá nhập kho.
          </div>
          {alloc.warnings?.length > 0 && (
            <div style={{ fontSize: 10, color: '#9a3412', marginBottom: 4 }}>
              {alloc.warnings.map((w: string, i: number) => <div key={i}>Lưu ý: {w}</div>)}
            </div>
          )}
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr>
                <td style={head}>STT</td><td style={head}>Mã hàng / Khoản chi phí</td><td style={head}>Cách chia</td>
                <td style={head}>Tỷ lệ</td><td style={head}>Tiền hàng (VNĐ)</td><td style={head}>Chi phí phân bổ (VNĐ)</td>
                <td style={head}>Tổng giá trị (VNĐ)</td>
              </tr>
            </thead>
            <tbody>
              {alloc.lines.map((ln: any, i: number) => (
                <Fragment key={i}>
                  <tr style={{ background: '#f6f8fa' }}>
                    <td style={{ ...cell, textAlign: 'center', ...bold }}>{i + 1}</td>
                    <td style={{ ...cell, ...bold }}>{ln.product_code} — {ln.product_name} <span style={{ fontWeight: 400 }}>({fmtQty(ln.qty_order)} {ln.unit}{ln.weight_kg ? `, ${fmtQty(ln.weight_kg)} kg` : ''})</span></td>
                    <td style={cell} />
                    <td style={right}>{ln.goods_base > 0 ? `${(ln.cost_base / ln.goods_base * 100).toFixed(1)}%` : '-'}</td>
                    <td style={{ ...right, ...bold }}>{fmtVND(ln.goods_base)}</td>
                    <td style={{ ...right, ...bold }}>{fmtVND(ln.cost_base)}</td>
                    <td style={{ ...right, ...bold }}>{fmtVND(ln.landed_base)}</td>
                  </tr>
                  {ln.costs.map((c: any, j: number) => (
                    <tr key={j}>
                      <td style={cell} />
                      <td style={{ ...cell, paddingLeft: 18 }}>{c.cost_type_label}{c.description ? ` — ${c.description}` : ''} <span style={{ fontStyle: 'italic' }}>({c.supplier_name || c.supplier_code})</span></td>
                      <td style={cell}>{c.effective_method === c.allocation_method ? c.allocation_method_label : `${c.effective_method_label} (*)`}</td>
                      <td style={right}>{fmtPct(c.ratio)}</td>
                      <td style={cell} />
                      <td style={right}>{fmtVND(c.base_amount)}</td>
                      <td style={cell} />
                    </tr>
                  ))}
                </Fragment>
              ))}
              {alloc.lines.length === 0 && <tr><td style={{ ...cell, textAlign: 'center', fontStyle: 'italic' }} colSpan={7}>Đơn chưa có dòng hàng</td></tr>}
              <tr>
                <td style={{ ...cell, ...bold }} colSpan={3}>Tổng toàn đơn:</td>
                <td style={right}>{alloc.goods_base_total > 0 ? `${(alloc.cost_total / alloc.goods_base_total * 100).toFixed(1)}%` : '-'}</td>
                <td style={{ ...right, ...bold }}>{fmtVND(alloc.goods_base_total)}</td>
                <td style={{ ...right, ...bold }}>{fmtVND(alloc.cost_total)}</td>
                <td style={{ ...right, ...bold }}>{fmtVND(alloc.landed_total)}</td>
              </tr>
            </tbody>
          </table>
          {alloc.lines.some((ln: any) => ln.costs.some((c: any) => c.effective_method !== c.allocation_method)) && (
            <div style={{ fontSize: 10, fontStyle: 'italic', marginTop: 3 }}>(*) Cách chia đã chọn thiếu cơ sở (chưa có kg / SL / mã hàng) nên hệ thống lùi về cách ghi ở cột.</div>
          )}
        </div>

        <div style={{ display: 'flex', justifyContent: 'space-around', textAlign: 'center', fontSize: 11.5, marginTop: 18 }}>
          {['Người lập', 'Kế toán', 'Trưởng phòng/Trưởng BP'].map((r) => (
            <div key={r} style={{ flex: 1 }}><b>{r}</b><div style={{ fontStyle: 'italic', fontSize: 10.5 }}>(Ký, họ tên)</div><div style={{ height: 60 }} /></div>
          ))}
        </div>
      </div>
    </div>
  )
}
