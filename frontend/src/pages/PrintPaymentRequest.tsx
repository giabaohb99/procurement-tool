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

  const cell = { border: '1px solid #888', padding: '3px 6px', fontSize: 11 } as const
  const SH = { background: '#dbe5f1', fontWeight: 700, padding: '3px 8px', fontSize: 11.5, margin: '9px 0 3px', border: '1px solid #c6d4e6' } as const
  const lbl = { fontSize: 11, padding: '1px 4px' } as const
  // Ô cho bảng Mẫu/Phiên bản/Ngày update ở góc phải header — giữ font, chỉ thu HẸP width table
  const hcell = { border: '1px solid #888', padding: '2px 5px', fontSize: 10, lineHeight: 1.4 } as const
  const dots = '............................'
  const dot = (v: any) => (v ? String(v) : dots)   // có data thì hiện, không thì để chấm điền tay

  return (
    <div style={{ background: '#eee', minHeight: '100vh', padding: 16 }}>
      <style>{`@media print { .no-print { display:none } body { background:#fff } } @page { size: A4 portrait; margin: 12mm }`}</style>
      <div className="no-print" style={{ maxWidth: 800, margin: '0 auto 12px', display: 'flex', gap: 8 }}>
        <button className="btn" onClick={() => window.print()}>In / Lưu PDF</button>
        <button className="btn ghost" onClick={() => window.close()}>Đóng</button>
      </div>

      <div className="print-doc" style={{ maxWidth: 800, margin: '0 auto', background: '#fff', padding: '24px 30px', fontFamily: 'Arial, sans-serif', color: '#000' }}>
        {/* Header */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
          <div style={{ fontWeight: 700, fontSize: 13 }}>{co.name || ''}</div>
          <table style={{ borderCollapse: 'collapse', width: 150, tableLayout: 'fixed' }}>
            <tbody>
              <tr><td style={{ ...hcell, fontWeight: 600, whiteSpace: 'nowrap' }}>Mẫu</td><td style={hcell}>002/BM/PKT</td></tr>
              <tr><td style={{ ...hcell, fontWeight: 600, whiteSpace: 'nowrap' }}>Phiên bản</td><td style={hcell}>062026</td></tr>
              <tr><td style={{ ...hcell, fontWeight: 600, whiteSpace: 'nowrap' }}>Ngày update</td><td style={hcell}>17/6/2025</td></tr>
            </tbody>
          </table>
        </div>

        <h2 style={{ textAlign: 'center', fontSize: 17, margin: '10px 0 2px' }}>ĐỀ NGHỊ THANH TOÁN</h2>
        <div style={{ textAlign: 'center', fontSize: 12 }}>Số: {req.code}</div>
        <div style={{ textAlign: 'center', fontSize: 12, marginBottom: 4 }}>{viDate(req.request_date)}</div>

        {/* Thông tin chung */}
        <div style={SH}>THÔNG TIN CHUNG</div>
        <div style={{ lineHeight: 1.55 }}>
          <div style={lbl}><b>Người đề nghị thanh toán:</b> {req.created_by_name || ''}</div>
          <div style={lbl}><b>Chức vụ:</b> {dot(req.created_by_position)}</div>
          <div style={lbl}><b>Hiện công tác tại bộ phận:</b> {dot(req.created_by_dept)}</div>
          <div style={lbl}><b>Trưởng phòng ban/bộ phận:</b> {dot(req.dept_manager)}</div>
        </div>

        {/* Nội dung thanh toán */}
        <div style={SH}>NỘI DUNG THANH TOÁN</div>
        <div style={{ lineHeight: 1.55, marginBottom: 4 }}>
          <div style={lbl}><b>Đối tượng:</b> {sup}</div>
          <div style={lbl}><b>Mã khoản mục CP:</b> ............................</div>
          <div style={lbl}><b>Nội dung:</b> {noiDung}</div>
        </div>

        <div style={{ ...lbl, fontWeight: 700 }}>Đề nghị thanh toán:</div>
        <table style={{ width: '100%', borderCollapse: 'collapse', tableLayout: 'fixed' }}>
          <colgroup>
            <col style={{ width: '6%' }} /><col style={{ width: '11%' }} />
            <col style={{ width: '47%' }} /><col style={{ width: '15%' }} />
            <col style={{ width: '13%' }} /><col style={{ width: '8%' }} />
          </colgroup>
          <thead>
            <tr style={{ background: '#eef2f6' }}>
              <td style={{ ...cell, fontWeight: 700, textAlign: 'center' }} colSpan={2}>Chứng từ</td>
              <td style={{ ...cell, fontWeight: 700, textAlign: 'center', verticalAlign: 'middle' }} rowSpan={2}>Diễn giải</td>
              <td style={{ ...cell, fontWeight: 700, textAlign: 'center', verticalAlign: 'middle' }} rowSpan={2}>Số tiền đề nghị thanh toán</td>
              <td style={{ ...cell, fontWeight: 700, textAlign: 'center', verticalAlign: 'middle' }} rowSpan={2}>Số tiền được duyệt</td>
              <td style={{ ...cell, fontWeight: 700, textAlign: 'center', verticalAlign: 'middle' }} rowSpan={2}>Ghi chú</td>
            </tr>
            <tr style={{ background: '#eef2f6' }}>
              <td style={{ ...cell, fontWeight: 700, textAlign: 'center' }}>Số</td>
              <td style={{ ...cell, fontWeight: 700, textAlign: 'center' }}>Ngày</td>
            </tr>
          </thead>
          <tbody>
            {req.lines.map((l: any, i: number) => (
              <tr key={i}>
                <td style={{ ...cell, textAlign: 'center' }}>{l.invoice_no}</td>
                <td style={{ ...cell, textAlign: 'center' }}>{dmy(l.invoice_date || l.incur_date)}</td>
                {/* Diễn giải GỘP cho mọi dòng (rowSpan) — chỉ render ở dòng đầu */}
                {i === 0 && (
                  <td style={{ ...cell, verticalAlign: 'middle' }} rowSpan={req.lines.length || 1}>{noiDung}</td>
                )}
                <td style={{ ...cell, textAlign: 'right' }}>{fmt(l.amount)}</td>
                <td style={cell} />
                <td style={cell} />
              </tr>
            ))}
            {req.lines.length === 0 && (
              <tr><td style={cell} /><td style={cell} /><td style={cell}>{noiDung}</td><td style={cell} /><td style={cell} /><td style={cell} /></tr>
            )}
            <tr>
              <td style={{ ...cell, fontWeight: 700, textAlign: 'center' }} colSpan={3}>Cộng</td>
              <td style={{ ...cell, fontWeight: 700, textAlign: 'right' }}>{fmt(req.total)}</td>
              <td style={cell} colSpan={2} />
            </tr>
          </tbody>
        </table>

        {/* Đã tạm ứng/thanh toán — để trống điền tay (theo mẫu 002/BM/PKT) */}
        <div style={{ ...lbl, fontWeight: 700, marginTop: 10 }}>Đã tạm ứng/thanh toán:</div>
        <table style={{ width: '100%', borderCollapse: 'collapse', tableLayout: 'fixed' }}>
          <colgroup>
            <col style={{ width: '6%' }} /><col style={{ width: '11%' }} />
            <col style={{ width: '33%' }} /><col style={{ width: '20%' }} />
            <col style={{ width: '18%' }} /><col style={{ width: '12%' }} />
          </colgroup>
          <thead>
            <tr style={{ background: '#eef2f6' }}>
              <td style={{ ...cell, fontWeight: 700, textAlign: 'center' }} colSpan={2}>Chứng từ</td>
              <td style={{ ...cell, fontWeight: 700, textAlign: 'center', verticalAlign: 'middle' }} rowSpan={2}>Diễn giải</td>
              <td style={{ ...cell, fontWeight: 700, textAlign: 'center', verticalAlign: 'middle' }} rowSpan={2}>Số tiền đề nghị tạm ứng</td>
              <td style={{ ...cell, fontWeight: 700, textAlign: 'center', verticalAlign: 'middle' }} rowSpan={2}>Số tiền đã tạm ứng</td>
              <td style={{ ...cell, fontWeight: 700, textAlign: 'center', verticalAlign: 'middle' }} rowSpan={2}>Ghi chú</td>
            </tr>
            <tr style={{ background: '#eef2f6' }}>
              <td style={{ ...cell, fontWeight: 700, textAlign: 'center' }}>Số</td>
              <td style={{ ...cell, fontWeight: 700, textAlign: 'center' }}>Ngày</td>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td style={{ ...cell, height: 24 }} /><td style={cell} /><td style={cell} /><td style={cell} /><td style={cell} /><td style={cell} />
            </tr>
            <tr>
              <td style={{ ...cell, fontWeight: 700, textAlign: 'center' }}>Cộng</td>
              <td style={cell} />
              <td style={{ ...cell, fontWeight: 700 }}>Số lượng: ....mục</td>
              <td style={cell} /><td style={cell} /><td style={cell} />
            </tr>
          </tbody>
        </table>

        <div style={{ marginTop: 8, border: '1px solid #888', fontSize: 11 }}>
          <div style={{ display: 'flex', borderBottom: '1px solid #888' }}>
            <div style={{ padding: '4px 8px', borderRight: '1px solid #888', width: 230, fontWeight: 600 }}>☑&nbsp; Còn lại phải thanh toán</div>
            <div style={{ padding: '4px 8px', flex: 1, textAlign: 'right', fontWeight: 700 }}>{fmt(req.total)}</div>
          </div>
          <div style={{ display: 'flex' }}>
            <div style={{ padding: '4px 8px', borderRight: '1px solid #888', width: 230, fontWeight: 600 }}>☐&nbsp; Phải hoàn lại cho Công ty</div>
            <div style={{ padding: '4px 8px', flex: 1 }} />
          </div>
        </div>
        <div style={{ ...lbl, marginTop: 4 }}><b>Bằng chữ:</b> <i>{docTien(req.total)}</i></div>

        {/* Hình thức thanh toán — 2 cột: trái (đơn vị + hình thức) / phải (thông tin chuyển khoản) */}
        <div style={SH}>HÌNH THỨC THANH TOÁN</div>
        <div style={{ display: 'flex', fontSize: 11, lineHeight: 1.55 }}>
          <div style={{ width: '48%', paddingRight: 8 }}>
            <div style={lbl}><b>Mã đơn vị:</b> {co.name || ''}</div>
            <div style={lbl}>☐ &nbsp;Tiền mặt</div>
            <div style={lbl}>☐ &nbsp;Chuyển khoản</div>
          </div>
          <div style={{ width: '52%', fontWeight: 700 }}>
            <div style={lbl}>Thông tin chuyển khoản:</div>
            <div style={lbl}>Tên TK thụ hưởng: {sup}</div>
            <div style={lbl}>Số TK thụ hưởng: {dot(req.bank_account)}</div>
            <div style={lbl}>Ngân hàng: {dot(req.bank_name)}</div>
            <div style={lbl}>Nội dung chuyển khoản: {noiDung}</div>
          </div>
        </div>

        {/* Xét duyệt */}
        <div style={SH}>XÉT DUYỆT</div>
        <div style={{ display: 'flex', justifyContent: 'space-around', textAlign: 'center', fontSize: 11, marginTop: 6 }}>
          {['Giám đốc', 'KT trưởng/TP.Kế toán', 'TP/Trưởng BP duyệt', 'Người lập phiếu'].map((r) => (
            <div key={r} style={{ flex: 1 }}><b>{r}</b><div style={{ fontStyle: 'italic', fontSize: 10 }}>(Ký, ghi rõ họ tên)</div><div style={{ height: 44 }} /></div>
          ))}
        </div>

        <div style={SH}>HỒ SƠ ĐÍNH KÈM</div>
        <div style={{ fontSize: 11, padding: '2px 8px', lineHeight: 1.5 }}>
          {[1, 2, 3].map((i) => <div key={i}>{i}. ............................................</div>)}
        </div>

        {/* Cụm ký nhận Kế toán — Thanh toán / Công nợ (điền tay) */}
        <table style={{ width: '100%', borderCollapse: 'collapse', marginTop: 6, fontSize: 11 }}>
          <tbody>
            <tr>
              <td style={{ width: '22%' }} />
              {['KT Thanh toán', 'KT Công nợ'].map((r) => (
                <td key={r} style={{ width: '39%', textAlign: 'center', padding: '2px 8px' }}>
                  <b>{r}</b>
                  <div style={{ fontStyle: 'italic', fontSize: 10 }}>(Thời gian, ký tên)</div>
                </td>
              ))}
            </tr>
            {['Nhận hồ sơ:', 'Chứng từ hạch toán:', 'Hồ sơ trả về:'].map((r) => (
              <tr key={r}>
                <td style={{ fontWeight: 700, padding: '2px 4px', whiteSpace: 'nowrap' }}>{r}</td>
                <td style={{ padding: '2px 8px' }}><div style={{ borderBottom: '1px solid #000', height: 11 }} /></td>
                <td style={{ padding: '2px 8px' }}><div style={{ borderBottom: '1px solid #000', height: 11 }} /></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
