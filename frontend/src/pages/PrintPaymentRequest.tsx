import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { api } from '../api/client'

const fmt = (n: any) => Number(n || 0).toLocaleString('vi-VN')
function viDate(d: string) {
  if (!d) return ''
  const [y, m, dd] = d.split('-')
  return `Ngày ${dd} tháng ${m} năm ${y}`
}

export default function PrintPaymentRequest() {
  const { id } = useParams()
  const [req, setReq] = useState<any>(null)
  useEffect(() => { api.get(`/api/payment-requests/${id}/print`).then((r) => setReq(r.data.data)) }, [id])
  if (!req) return <div style={{ padding: 40 }}>Đang tải...</div>
  const co = req.company || {}
  const cell = { border: '1px solid #555', padding: '5px 8px', fontSize: 12 } as const
  const head = { ...cell, background: '#e9edf1', fontWeight: 700, textAlign: 'center' as const }

  return (
    <div style={{ background: '#eee', minHeight: '100vh', padding: 16 }}>
      <style>{`@media print { .no-print { display:none } body { background:#fff } } @page { size: A4 portrait; margin: 14mm }`}</style>
      <div className="no-print" style={{ maxWidth: 760, margin: '0 auto 12px', display: 'flex', gap: 8 }}>
        <button className="btn" onClick={() => window.print()}>In / Lưu PDF</button>
        <button className="btn ghost" onClick={() => window.close()}>Đóng</button>
      </div>
      <div style={{ maxWidth: 760, margin: '0 auto', background: '#fff', padding: '28px 32px', fontFamily: 'Arial, sans-serif', color: '#000' }}>
        <div style={{ fontWeight: 700, fontSize: 14 }}>{co.name || ''}</div>
        <div style={{ fontSize: 11 }}>Địa chỉ: {co.address || ''}</div>
        <div style={{ fontSize: 11 }}>Mã số thuế: {co.tax_code || ''}</div>

        <h2 style={{ textAlign: 'center', fontSize: 18, margin: '14px 0 2px' }}>ĐỀ NGHỊ THANH TOÁN</h2>
        <div style={{ textAlign: 'center', fontSize: 12, marginBottom: 10 }}>Số: {req.code}</div>

        <div style={{ fontSize: 12.5, lineHeight: 1.9, marginBottom: 8 }}>
          <div><b>Nhà cung cấp:</b> {req.supplier_name || req.supplier_code}</div>
          <div><b>Loại công nợ:</b> {req.source_type === 'shipping' ? 'Vận chuyển' : 'Hàng hóa'}</div>
          <div><b>Đơn vị thanh toán:</b> {co.name || ''}</div>
        </div>

        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead><tr><td style={head}>STT</td><td style={head}>Đơn hàng (PO)</td><td style={head}>Số hóa đơn</td><td style={head}>Hạn trả</td><td style={head}>Số tiền đề nghị</td></tr></thead>
          <tbody>
            {req.lines.map((l: any, i: number) => (
              <tr key={i}>
                <td style={{ ...cell, textAlign: 'center' }}>{i + 1}</td>
                <td style={cell}>{l.po_code}</td><td style={cell}>{l.invoice_no}</td>
                <td style={{ ...cell, textAlign: 'center' }}>{l.due_date}</td>
                <td style={{ ...cell, textAlign: 'right' }}>{fmt(l.amount)}</td>
              </tr>
            ))}
            <tr><td style={{ ...cell, fontWeight: 700, textAlign: 'center' }} colSpan={4}>TỔNG CỘNG</td><td style={{ ...cell, textAlign: 'right', fontWeight: 700 }}>{fmt(req.total)}</td></tr>
          </tbody>
        </table>

        {req.note && <div style={{ fontSize: 12, marginTop: 10 }}><b>Ghi chú:</b> {req.note}</div>}

        <div style={{ textAlign: 'right', fontSize: 12, marginTop: 16, fontStyle: 'italic' }}>{viDate(req.request_date)}</div>
        <div style={{ display: 'flex', justifyContent: 'space-around', textAlign: 'center', fontSize: 12, marginTop: 8 }}>
          {['Người lập', 'Kế toán', 'Duyệt chi'].map((r) => (
            <div key={r}><b>{r}</b><div style={{ fontStyle: 'italic', fontSize: 11 }}>(Ký, ghi rõ họ tên)</div><div style={{ height: 56 }} /></div>
          ))}
        </div>
      </div>
    </div>
  )
}
