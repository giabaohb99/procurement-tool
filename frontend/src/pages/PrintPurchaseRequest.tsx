import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { api } from '../api/client'

const fmt = (n: any) => Number(n || 0).toLocaleString('vi-VN')
function viDate(d: string) {
  if (!d) return '............'
  const [y, m, dd] = d.split('-')
  return `Ngày ${dd} tháng ${m} năm ${y}`
}

export default function PrintPurchaseRequest() {
  const { id } = useParams()
  const [pr, setPr] = useState<any>(null)
  const [company, setCompany] = useState('')
  const [files, setFiles] = useState<any[]>([])

  useEffect(() => {
    api.get(`/api/purchase-requests/${id}`).then(async (r) => {
      const d = r.data.data; setPr(d)
      if (d.company_id) { try { const c = await api.get(`/api/companies/${d.company_id}`); setCompany(c.data.data.name) } catch { } }
    })
    api.get('/api/attachments', { params: { entity: 'purchase_request', entity_id: id } }).then((x) => setFiles(x.data.data || []))
  }, [id])

  if (!pr) return <div style={{ padding: 40 }}>Đang tải...</div>

  const SH = { background: '#e9edf1', fontWeight: 700, padding: '5px 8px', fontSize: 12, margin: '14px 0 0' } as const
  const cell = { border: '1px solid #999', padding: '6px 8px', fontSize: 12 } as const

  return (
    <div style={{ background: '#f0f0f0', minHeight: '100vh', padding: 20 }}>
      <div className="no-print" style={{ maxWidth: 820, margin: '0 auto 12px', display: 'flex', gap: 8 }}>
        <button className="btn" onClick={() => window.print()}>In / Lưu PDF</button>
        <button className="btn ghost" onClick={() => window.close()}>Đóng</button>
      </div>

      <div style={{ maxWidth: 820, margin: '0 auto', background: '#fff', padding: '28px 32px', fontFamily: 'Inter, Arial, sans-serif', color: '#000' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
          <div style={{ fontSize: 13 }}><b>Đơn vị:</b> {company || '...'}</div>
          <table style={{ borderCollapse: 'collapse', fontSize: 12, textAlign: 'left' }}>
            <tbody>
              {(() => {
                const c = { border: '1px solid #999', padding: '4px 8px', lineHeight: 1.4, whiteSpace: 'nowrap' } as const; return (
                  <>
                    <tr><td colSpan={2} style={{ ...c, fontWeight: 700, textAlign: 'center' }}>Mẫu 003/BM/PKT</td></tr>
                    <tr><td style={{ ...c, width: 80 }}>Phiên bản</td><td style={{ ...c, textAlign: 'center' }}>V1-062025</td></tr>
                    <tr><td style={{ ...c, width: 80 }}>Ngày update:</td><td style={{ ...c, textAlign: 'center' }}>17/7/2025</td></tr>
                  </>
                )
              })()}
            </tbody>
          </table>
        </div>

        <h2 style={{ textAlign: 'center', fontSize: 17, margin: '14px 0 2px' }}>PHIẾU ĐỀ XUẤT MUA HÀNG HÓA/DỊCH VỤ</h2>
        <div style={{ textAlign: 'center', fontSize: 12 }}>Số: {pr.show_code_on_print !== false ? pr.code : '....................'}</div>
        <div style={{ textAlign: 'center', fontSize: 12, marginBottom: 6 }}>{viDate(pr.request_date)}</div>

        <div style={SH}>THÔNG TIN CHUNG</div>
        <div style={{ fontSize: 12, padding: '6px 4px', lineHeight: 1.8 }}>
          <div><b>Người đề xuất:</b> {pr.requester}</div>
          <div><b>Chức vụ:</b> {pr.requester_position || '............'}</div>
          <div><b>Hiện công tác tại bộ phận:</b> {pr.department || '............'}</div>
          <div><b>Trưởng phòng ban/bộ phận:</b> {pr.head_of_dept || '............'}</div>
        </div>

        <div style={SH}>MỤC ĐÍCH &amp; NỘI DUNG ĐỀ XUẤT</div>
        <div style={{ fontSize: 12, padding: '6px 4px', lineHeight: 1.8 }}>
          <div><b>Mục đích mua hàng/dịch vụ:</b> {pr.is_urgent ? '[Gấp] ' : ''}{pr.purpose}</div>
          <div><b>Thời gian cần hàng/dịch vụ:</b> {pr.need_date || '...'}</div>
          <div><b>Nội dung:</b> {pr.note || ''}</div>
        </div>

        <table style={{ width: '100%', borderCollapse: 'collapse', marginTop: 6 }}>
          <thead>
            <tr style={{ background: '#e9edf1' }}>
              <td style={cell}>STT</td><td style={cell}>Tên hàng hóa/dịch vụ</td><td style={cell}>Mã hàng</td>
              <td style={cell}>ĐVT</td><td style={cell}>SL yêu cầu</td><td style={cell}>Đơn giá</td>
              <td style={cell}>Thành tiền</td><td style={cell}>Ghi chú</td>
            </tr>
          </thead>
          <tbody>
            {pr.items.map((it: any, i: number) => (
              <tr key={i}>
                <td style={cell}>{i + 1}</td><td style={cell}>{it.product_name}</td><td style={cell}>{it.product_code}</td>
                <td style={cell}>{it.unit}</td><td style={{ ...cell, textAlign: 'right' }}>{fmt(it.qty)}</td>
                <td style={{ ...cell, textAlign: 'right' }}>{fmt(it.price)}</td><td style={{ ...cell, textAlign: 'right' }}>{fmt(it.amount)}</td>
                <td style={cell}>{it.note}</td>
              </tr>
            ))}
            <tr><td style={{ ...cell, fontWeight: 700 }} colSpan={6}>Tổng cộng</td><td style={{ ...cell, textAlign: 'right', fontWeight: 700 }}>{fmt(pr.subtotal)}</td><td style={cell} /></tr>
          </tbody>
        </table>
        <div style={{ textAlign: 'right', fontSize: 12, marginTop: 6 }}>VAT: <b>{fmt(pr.vat)}</b></div>
        <div style={{ textAlign: 'right', fontSize: 13 }}>Tổng cộng thanh toán: <b>{fmt(pr.total)}</b></div>

        <div style={SH}>THÔNG TIN NHÀ CUNG CẤP</div>
        <div style={{ fontSize: 12, padding: '6px 4px', lineHeight: 1.8 }}>
          <div><b>Tên nhà cung cấp:</b> {pr.suggested_supplier || ''}</div>
          <div><b>Mã số thuế:</b> {pr.suggested_supplier_tax_code || ''}</div>
          <div><b>Liên hệ:</b> {pr.suggested_supplier_contact || ''}</div>
          <div><b>Báo giá đính kèm:</b> {pr.quote_file_url || files.length > 0 ? '☑ Có' : '☐ Có'} &nbsp;&nbsp; {pr.quote_file_url || files.length > 0 ? '☐ Không' : '☑ Không'} {pr.quote_filename ? `( ${pr.quote_filename} )` : ''}</div>
        </div>

        <div style={SH}>PHẦN DÀNH CHO BỘ PHẬN MUA HÀNG</div>
        <div style={{ fontSize: 12, padding: '6px 4px', lineHeight: 1.8 }}>
          <div><b>Thời gian cần hàng/dịch vụ:</b> .............................</div>
          <div><b>Yêu cầu khác (nếu có):</b> .............................</div>
        </div>

        <div style={SH}>XÉT DUYỆT</div>
        <div style={{ display: 'flex', justifyContent: 'space-around', textAlign: 'center', fontSize: 12, marginTop: 16 }}>
          {['Giám đốc', 'TP/BP mua hàng', 'TP/BP đề xuất', 'Người lập'].map((r) => (
            <div key={r}>
              <b>{r}</b>
              <div style={{ fontStyle: 'italic', fontSize: 11 }}>(Ký, ghi rõ họ tên)</div>
              <div style={{ height: 60, display: 'flex', alignItems: 'flex-end', justifyContent: 'center', fontWeight: 500 }}>
                {r === 'Người lập' ? pr.requester : ''}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
