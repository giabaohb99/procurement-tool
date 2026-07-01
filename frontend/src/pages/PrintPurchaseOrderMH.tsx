import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { api } from '../api/client'

const fmt = (n: any) => Number(n || 0).toLocaleString('vi-VN')
function dmy(d: string) { if (!d) return ''; const [y, m, dd] = d.split('-'); return `${dd}/${m}/${y}` }

function docTien(amount: number): string {
  let n = Math.round(Number(amount) || 0)
  if (n <= 0) return 'Không đồng'
  const d = ['không', 'một', 'hai', 'ba', 'bốn', 'năm', 'sáu', 'bảy', 'tám', 'chín']
  const readTriple = (num: number, showH: boolean) => {
    const tram = Math.floor(num / 100), chuc = Math.floor((num % 100) / 10), dv = num % 10
    const p: string[] = []
    if (showH || tram > 0) p.push(d[tram] + ' trăm')
    if (chuc === 0) { if (dv > 0) p.push((showH || tram > 0 ? 'lẻ ' : '') + d[dv]) }
    else if (chuc === 1) { p.push('mười'); if (dv === 5) p.push('lăm'); else if (dv > 0) p.push(d[dv]) }
    else { p.push(d[chuc] + ' mươi'); if (dv === 1) p.push('mốt'); else if (dv === 5) p.push('lăm'); else if (dv > 0) p.push(d[dv]) }
    return p.join(' ')
  }
  const groups: number[] = []
  while (n > 0) { groups.push(n % 1000); n = Math.floor(n / 1000) }
  const scale = ['', ' nghìn', ' triệu', ' tỷ', ' nghìn tỷ']
  const out: string[] = []
  for (let i = groups.length - 1; i >= 0; i--) {
    if (groups[i] === 0) continue
    out.push(readTriple(groups[i], i < groups.length - 1) + scale[i])
  }
  let s = out.join(' ').replace(/\s+/g, ' ').trim()
  return s.charAt(0).toUpperCase() + s.slice(1) + ' đồng chẵn'
}

export default function PrintPurchaseOrderMH() {
  const { id } = useParams()
  const [po, setPo] = useState<any>(null)
  useEffect(() => { api.get(`/api/purchase-orders/${id}/print`).then((r) => setPo(r.data.data)) }, [id])
  if (!po) return <div style={{ padding: 40 }}>Đang tải...</div>
  const co = po.company || {}
  const sup = po.supplier || {}
  const whNames = po.wh_names || {}
  const docNo = po.misa_code || po.code
  const debtDays = (po.payment_terms || '').match(/(\d+)\s*ng[aà]y/i)?.[1] || ''
  const subtotal = po.order_subtotal || 0
  const total = po.order_total || 0
  const tax = Math.round((total - subtotal) * 100) / 100

  const cell = { border: '1px solid #555', padding: '4px 6px', fontSize: 11 } as const
  const head = { ...cell, background: '#eef2f6', fontWeight: 700, textAlign: 'center' as const }

  return (
    <div style={{ background: '#eee', minHeight: '100vh', padding: 16 }}>
      <style>{`@media print { .no-print { display:none } body { background:#fff } } @page { size: A4 portrait; margin: 12mm }`}</style>
      <div className="no-print" style={{ maxWidth: 800, margin: '0 auto 12px', display: 'flex', gap: 8 }}>
        <button className="btn" onClick={() => window.print()}>In / Lưu PDF</button>
        <button className="btn ghost" onClick={() => window.close()}>Đóng</button>
      </div>

      <div style={{ maxWidth: 800, margin: '0 auto', background: '#fff', padding: '24px 30px', fontFamily: 'Arial, sans-serif', color: '#000' }}>
        {/* Header công ty */}
        <div style={{ borderBottom: '2px solid #1a4d6b', paddingBottom: 6 }}>
          <div style={{ fontWeight: 700, fontSize: 13 }}>{co.name || ''}</div>
          <div style={{ fontSize: 10.5, fontStyle: 'italic' }}>Địa chỉ: {co.address || ''}</div>
        </div>

        <h2 style={{ textAlign: 'center', fontSize: 17, margin: '12px 0 10px' }}>ĐƠN MUA HÀNG</h2>

        {/* Thông tin NCC + đơn */}
        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 11.5, lineHeight: 1.9 }}>
          <div style={{ flex: 1 }}>
            <div><b>Tên nhà cung cấp:</b> {sup.name || po.supplier_name || ''}</div>
            <div><b>Địa chỉ:</b> {sup.address || ''}</div>
            <div><b>Mã số thuế:</b> {sup.tax_code || ''}</div>
            <div><b>Điện thoại:</b> </div>
            <div><b>Nhân viên mua hàng:</b> {po.nspt || ''}</div>
            <div><b>Diễn giải:</b> {po.note || ''}</div>
          </div>
          <div style={{ width: 220, paddingLeft: 12 }}>
            <div><b>Ngày:</b> {dmy(po.order_date)}</div>
            <div><b>Số:</b> {docNo}</div>
            <div><b>Loại tiền:</b> VND</div>
          </div>
        </div>

        {/* Bảng hàng */}
        <table style={{ width: '100%', borderCollapse: 'collapse', marginTop: 8 }}>
          <thead>
            <tr>
              <td style={head}>STT</td><td style={head}>Tên kho nhập</td><td style={head}>Mã hàng</td>
              <td style={head}>Tên hàng</td><td style={head}>Tên hàng xuất hóa đơn</td><td style={head}>ĐVT</td>
              <td style={head}>SL yêu cầu</td><td style={head}>SL thực nhập</td><td style={head}>Đơn giá</td>
              <td style={head}>Thành tiền</td><td style={head}>Ghi chú</td>
            </tr>
          </thead>
          <tbody>
            {po.items.map((it: any, i: number) => (
              <tr key={i}>
                <td style={{ ...cell, textAlign: 'center' }}>{i + 1}</td>
                <td style={cell}>{whNames[it.warehouse_code] || it.warehouse_code}</td>
                <td style={cell}>{it.product_code}</td>
                <td style={cell}>{it.product_name}</td>
                <td style={cell}>{it.invoice_name}</td>
                <td style={{ ...cell, textAlign: 'center' }}>{it.unit}</td>
                <td style={{ ...cell, textAlign: 'right' }}>{fmt(it.qty_order)}</td>
                <td style={{ ...cell, textAlign: 'right' }}>{it.qty_received ? fmt(it.qty_received) : '-'}</td>
                <td style={{ ...cell, textAlign: 'right' }}>{fmt(it.price)}</td>
                <td style={{ ...cell, textAlign: 'right' }}>{fmt(it.qty_order * it.price)}</td>
                <td style={cell}>{it.note}</td>
              </tr>
            ))}
            <tr>
              <td style={{ ...cell, fontWeight: 700 }} colSpan={9}>Tiền thuế GTGT:</td>
              <td style={{ ...cell, textAlign: 'right', fontWeight: 700 }}>{fmt(tax)}</td>
              <td style={cell} />
            </tr>
            <tr>
              <td style={{ ...cell, fontWeight: 700 }} colSpan={9}>Tổng tiền thanh toán:</td>
              <td style={{ ...cell, textAlign: 'right', fontWeight: 700 }}>{fmt(total)}</td>
              <td style={cell} />
            </tr>
          </tbody>
        </table>
        <div style={{ fontSize: 11.5, fontStyle: 'italic', marginTop: 4 }}><b>Số tiền viết bằng chữ:</b> {docTien(total)}.</div>

        {/* Điều khoản */}
        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 11.5, marginTop: 12 }}>
          <div><b>Ngày giao hàng:</b> ....................</div>
          <div><b>Số ngày được nợ:</b> {debtDays || '..........'} {debtDays ? 'ngày' : ''}</div>
        </div>
        <div style={{ fontSize: 11.5, marginTop: 6 }}><b>Điều khoản thanh toán:</b> {po.payment_terms || ''}</div>

        <div style={{ display: 'flex', gap: 20, marginTop: 8, fontSize: 11 }}>
          <div style={{ flex: 1, border: '1px solid #888', padding: '6px 8px' }}>
            <div style={{ fontWeight: 600, marginBottom: 4 }}>Hồ sơ NCC gửi kèm:</div>
            {[1, 2, 3, 4].map((i) => <div key={i}>{i}. ..................................</div>)}
          </div>
          <div style={{ flex: 1, border: '1px solid #888', padding: '6px 8px' }}>
            <div style={{ fontWeight: 600, marginBottom: 4 }}>Các tiêu chí cần nhà máy đánh giá trước khi nhận:</div>
            <div style={{ fontSize: 10, fontStyle: 'italic', marginBottom: 2 }}>(VD: màu sắc, ngoại dạng, trọng lượng, bao bì…)</div>
            {[1, 2, 3, 4].map((i) => <div key={i}>{i}. ..................................</div>)}
          </div>
        </div>

        {/* Chữ ký */}
        <div style={{ display: 'flex', justifyContent: 'space-around', textAlign: 'center', fontSize: 11.5, marginTop: 18 }}>
          {['Người lập', 'Người nhận', 'Trưởng phòng/Trưởng BP'].map((r) => (
            <div key={r} style={{ flex: 1 }}><b>{r}</b><div style={{ fontStyle: 'italic', fontSize: 10.5 }}>(Ký, họ tên)</div><div style={{ height: 60 }} /></div>
          ))}
        </div>
      </div>
    </div>
  )
}
