import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { api } from '../api/client'

const fmt = (n: any) => Number(n || 0).toLocaleString('vi-VN')
function dmy(d: string) { if (!d) return ''; const [y, m, dd] = d.split('-'); return `${dd}/${m}/${y}` }
function viDate(d: string) { if (!d) return ''; const [y, m, dd] = d.split('-'); return `Ngày ${dd} tháng ${m} năm ${y}` }

// Đọc số tiền thành chữ (tiếng Việt)
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

export default function PrintPaymentRequest() {
  const { id } = useParams()
  const [req, setReq] = useState<any>(null)
  useEffect(() => { api.get(`/api/payment-requests/${id}/print`).then((r) => setReq(r.data.data)) }, [id])
  if (!req) return <div style={{ padding: 40 }}>Đang tải...</div>
  const co = req.company || {}
  const sup = req.supplier_name || req.supplier_code
  const period = (req.period || '').split('-').reverse().join('/')  // YYYY-MM -> MM/YYYY
  const noiDung = `Thanh toán công nợ ${sup}${period ? ' ' + period : ''}`

  const cell = { border: '1px solid #888', padding: '4px 8px', fontSize: 11.5 } as const
  const SH = { background: '#dbe5f1', fontWeight: 700, padding: '4px 8px', fontSize: 12, margin: '12px 0 0', border: '1px solid #c6d4e6' } as const
  const lbl = { fontSize: 11.5, padding: '2px 4px' } as const

  return (
    <div style={{ background: '#eee', minHeight: '100vh', padding: 16 }}>
      <style>{`@media print { .no-print { display:none } body { background:#fff } } @page { size: A4 portrait; margin: 12mm }`}</style>
      <div className="no-print" style={{ maxWidth: 800, margin: '0 auto 12px', display: 'flex', gap: 8 }}>
        <button className="btn" onClick={() => window.print()}>In / Lưu PDF</button>
        <button className="btn ghost" onClick={() => window.close()}>Đóng</button>
      </div>

      <div style={{ maxWidth: 800, margin: '0 auto', background: '#fff', padding: '24px 30px', fontFamily: 'Arial, sans-serif', color: '#000' }}>
        {/* Header */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
          <div style={{ fontWeight: 700, fontSize: 13 }}>{co.name || ''}</div>
          <table style={{ borderCollapse: 'collapse', fontSize: 10 }}>
            <tbody>
              <tr><td style={{ ...cell, fontWeight: 600 }}>Mẫu</td><td style={cell}>002/BM/PKT</td></tr>
              <tr><td style={{ ...cell, fontWeight: 600 }}>Phiên bản</td><td style={cell}>062026</td></tr>
              <tr><td style={{ ...cell, fontWeight: 600 }}>Ngày update</td><td style={cell}>17/6/2025</td></tr>
            </tbody>
          </table>
        </div>

        <h2 style={{ textAlign: 'center', fontSize: 17, margin: '10px 0 2px' }}>ĐỀ NGHỊ THANH TOÁN</h2>
        <div style={{ textAlign: 'center', fontSize: 12 }}>Số: {req.code}</div>
        <div style={{ textAlign: 'center', fontSize: 12, marginBottom: 4 }}>{viDate(req.request_date)}</div>

        {/* Thông tin chung */}
        <div style={SH}>THÔNG TIN CHUNG</div>
        <div style={{ lineHeight: 1.9 }}>
          <div style={lbl}><b>Người đề nghị thanh toán:</b> {req.created_by_name || ''}</div>
          <div style={lbl}><b>Chức vụ:</b> ............................</div>
          <div style={lbl}><b>Hiện công tác tại bộ phận:</b> ............................</div>
          <div style={lbl}><b>Trưởng phòng ban/bộ phận:</b> ............................</div>
        </div>

        {/* Nội dung thanh toán */}
        <div style={SH}>NỘI DUNG THANH TOÁN</div>
        <div style={{ lineHeight: 1.9, marginBottom: 4 }}>
          <div style={lbl}><b>Đối tượng:</b> {sup}</div>
          <div style={lbl}><b>Mã khoản mục CP:</b> ............................</div>
          <div style={lbl}><b>Nội dung:</b> {noiDung}</div>
        </div>

        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead>
            <tr style={{ background: '#eef2f6' }}>
              <td style={{ ...cell, fontWeight: 700, textAlign: 'center' }}>Số hóa đơn</td>
              <td style={{ ...cell, fontWeight: 700, textAlign: 'center' }}>Ngày</td>
              <td style={{ ...cell, fontWeight: 700 }}>Diễn giải</td>
              <td style={{ ...cell, fontWeight: 700, textAlign: 'center' }}>Số tiền đề nghị thanh toán</td>
              <td style={{ ...cell, fontWeight: 700, textAlign: 'center' }}>Số tiền được duyệt</td>
              <td style={{ ...cell, fontWeight: 700, textAlign: 'center' }}>Ghi chú</td>
            </tr>
          </thead>
          <tbody>
            {req.lines.map((l: any, i: number) => (
              <tr key={i}>
                <td style={{ ...cell, textAlign: 'center' }}>{l.invoice_no}</td>
                <td style={{ ...cell, textAlign: 'center' }}>{dmy(l.incur_date)}</td>
                <td style={cell}>{i === 0 ? noiDung : ''}</td>
                <td style={{ ...cell, textAlign: 'right' }}>{fmt(l.amount)}</td>
                <td style={cell} />
                <td style={cell} />
              </tr>
            ))}
            <tr>
              <td style={{ ...cell, fontWeight: 700, textAlign: 'center' }} colSpan={3}>Cộng</td>
              <td style={{ ...cell, fontWeight: 700, textAlign: 'right' }}>{fmt(req.total)}</td>
              <td style={cell} colSpan={2} />
            </tr>
          </tbody>
        </table>

        <div style={{ marginTop: 8, display: 'flex', border: '1px solid #888' }}>
          <div style={{ ...cell, border: 'none', borderRight: '1px solid #888', fontWeight: 600, width: 200 }}>Còn lại phải thanh toán</div>
          <div style={{ ...cell, border: 'none', textAlign: 'right', flex: 1, fontWeight: 700 }}>{fmt(req.total)}</div>
        </div>
        <div style={{ ...lbl, marginTop: 4 }}><b>Bằng chữ:</b> <i>{docTien(req.total)}</i></div>

        {/* Hình thức thanh toán */}
        <div style={SH}>HÌNH THỨC THANH TOÁN</div>
        <div style={{ fontSize: 11.5, lineHeight: 1.9 }}>
          <div style={lbl}>☐ Tiền mặt &nbsp;&nbsp;&nbsp; ☐ Chuyển khoản</div>
          <div style={lbl}><b>Tên TK thụ hưởng:</b> {sup}</div>
          <div style={lbl}><b>Số TK thụ hưởng:</b> ............................</div>
          <div style={lbl}><b>Ngân hàng/CN:</b> ............................</div>
          <div style={lbl}><b>Nội dung chuyển khoản:</b> {noiDung}</div>
        </div>

        {/* Xét duyệt */}
        <div style={SH}>XÉT DUYỆT</div>
        <div style={{ display: 'flex', justifyContent: 'space-around', textAlign: 'center', fontSize: 11.5, marginTop: 10 }}>
          {['Giám đốc', 'KT trưởng/TP.Kế toán', 'TP/Trưởng BP duyệt', 'Người lập phiếu'].map((r) => (
            <div key={r} style={{ flex: 1 }}><b>{r}</b><div style={{ fontStyle: 'italic', fontSize: 10.5 }}>(Ký, ghi rõ họ tên)</div><div style={{ height: 54 }} /></div>
          ))}
        </div>

        <div style={SH}>HỒ SƠ ĐÍNH KÈM</div>
        <div style={{ fontSize: 11.5, padding: '4px 8px', lineHeight: 1.8 }}>
          {[1, 2, 3, 4, 5].map((i) => <div key={i}>{i}. ............................................</div>)}
        </div>
      </div>
    </div>
  )
}
