import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { api } from '../api/client'
import NotFound from '../components/NotFound'
import { tenFileIn, usePrintTitle } from '../hooks/usePrintTitle'

const fmt = (n: any) => (Number(n) ? Number(n).toLocaleString('vi-VN') : '')
// ĐƠN GIÁ in đủ 4 số lẻ; TIỀN in làm tròn về đồng (kế toán chỉ ghi nhận tới đồng)
const fmtPrice = (n: any) => (Number(n) ? Number(n).toLocaleString('vi-VN', { maximumFractionDigits: 4 }) : '')
const fmtVND = (n: any) => (Number(n) ? Math.round(Number(n)).toLocaleString('vi-VN') : '')
function viDate(d: string) {
  if (!d) return ''
  const [y, m, dd] = d.split('-')
  return `Cần Thơ, ngày ${dd} tháng ${m} năm ${y}`
}
function dmy(d: string) {
  if (!d) return ''
  const parts = d.split('-')
  return parts.length === 3 ? `${parts[2]}/${parts[1]}/${parts[0]}` : d
}

export default function PrintPurchaseOrder() {
  const { id } = useParams()
  const [po, setPo] = useState<any>(null)
  // Đơn đã bị xóa / không có quyền in -> API trả 404·403. Không bắt lỗi thì trang kẹt
  // "Đang tải..." vĩnh viễn, người dùng tưởng hệ thống treo.
  const [notFound, setNotFound] = useState(false)

  useEffect(() => {
    setNotFound(false)
    api.get(`/api/purchase-orders/${id}/print`, { _silent: true } as any)
      .then((r) => setPo(r.data.data))
      .catch(() => setNotFound(true))
  }, [id])
  // Tên file gợi ý khi lưu PDF = Mã PO + ngày đơn, thay cho "Thu Mua Tool" mặc định.
  // Lấy `code` chứ không lấy `misa_code`: mã MISA là mã của hệ thống cũ, chỉ một phần đơn
  // có, và trùng nhau giữa các đơn nhập lại — đặt tên file theo nó thì đè file của nhau.
  usePrintTitle(po ? tenFileIn(po.code, po.order_date) : '')

  if (notFound) return (
    <NotFound backTo="/purchase-orders"
              message="Đơn mua hàng này không tồn tại, đã bị xóa hoặc bạn không có quyền in." />
  )
  if (!po) return <div style={{ padding: 40 }}>Đang tải...</div>
  const co = po.company || {}
  const sup = po.supplier || {}
  const wh = po.warehouse || {}
  const cell = { border: '1px solid #555', padding: '4px 6px', fontSize: 11, verticalAlign: 'top' } as const
  const head = { ...cell, background: '#dfe7df', fontWeight: 700, textAlign: 'center' as const }

  return (
    <div className="print-wrap" style={{ background: '#eee', minHeight: '100vh', padding: 16 }}>
      {/* `@page { margin: 0 }`: trình duyệt vẽ ngày giờ / tên tab / đường dẫn / số trang vào đúng
          dải lề của khổ giấy — bỏ lề đi thì không còn chỗ cho mấy dòng đó. Lề thật của đơn
          chuyển xuống padding của .print-doc (!important vì padding đang đặt bằng style inline). */}
      <style>{`@media print {
        @page { size: A4 landscape; margin: 0; }
        html, body { margin: 0 !important; background: #fff !important; }
        .no-print { display: none !important; }
        .print-wrap { padding: 0 !important; background: #fff !important; min-height: 0 !important; }
        /* Lề trên/dưới 8mm: đơn ngang vốn cao sát mép khổ A4, để 10mm là tràn sang tờ thứ hai
           chỉ vì vài milimet. box-decoration-break: clone -> đơn nhiều dòng hàng phải sang
           trang 2 thì mỗi mảnh vẫn đủ lề, không chạy sát mép giấy. */
        .print-doc {
          padding: 8mm 12mm !important;
          -webkit-box-decoration-break: clone; box-decoration-break: clone;
        }
      }`}</style>
      <div className="no-print" style={{ maxWidth: 1100, margin: '0 auto 12px', display: 'flex', gap: 8 }}>
        <button className="btn" onClick={() => window.print()}>In / Lưu PDF</button>
        <button className="btn ghost" onClick={() => window.close()}>Đóng</button>
      </div>

      <div className="print-doc" style={{ maxWidth: 1100, margin: '0 auto', background: '#fff', padding: '24px 28px', fontFamily: 'Arial, sans-serif', color: '#000' }}>
        {/* Header công ty + kính gửi */}
        <div style={{ fontWeight: 700, fontSize: 14 }}>{co.name || ''}</div>
        <div style={{ fontSize: 11 }}>Địa chỉ: {co.address || ''}</div>
        <div style={{ fontSize: 11 }}>Mã số thuế: {co.tax_code || ''}</div>
        <div style={{ fontSize: 12, marginTop: 8 }}><b>Kính gửi:</b> {sup.name || po.supplier_name || ''}</div>
        <div style={{ fontSize: 12 }}><b>Địa chỉ:</b> {sup.address || ''}</div>

        <h2 style={{ textAlign: 'center', fontSize: 18, margin: '12px 0 2px' }}>ĐƠN ĐẶT HÀNG</h2>
        <div style={{ textAlign: 'center', fontSize: 12, color: '#c0392b', fontWeight: 700, marginBottom: 8 }}>Số: {po.misa_code || po.code}</div>

        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead>
            <tr>
              <td style={head}>STT</td><td style={head}>Mã</td><td style={head}>Tên hàng hóa</td>
              <td style={head}>Xuất xứ/ TSKT/<br />chất liệu</td><td style={head}>ĐVT</td><td style={head}>SL</td>
              <td style={head}>Đơn giá (Chưa VAT)</td><td style={head}>VAT</td><td style={head}>Đơn giá (Đã VAT)</td>
              <td style={head}>Thành tiền</td><td style={head}>Kho nhận</td><td style={head}>Tên trên HĐ</td><td style={head}>Ghi chú</td>
            </tr>
          </thead>
          <tbody>
            {po.items.map((it: any, i: number) => {
              const priceVat = it.price * (1 + (it.vat || 0) / 100)
              return (
                <tr key={i}>
                  <td style={{ ...cell, textAlign: 'center' }}>{i + 1}</td>
                  <td style={cell}>{it.product_code}</td>
                  <td style={cell}>{it.product_name}</td>
                  <td style={cell}>{it.spec}</td>
                  <td style={{ ...cell, textAlign: 'center' }}>{it.unit}</td>
                  <td style={{ ...cell, textAlign: 'right' }}>{fmt(it.qty_order)}</td>
                  <td style={{ ...cell, textAlign: 'right' }}>{fmtPrice(it.price)}</td>
                  <td style={{ ...cell, textAlign: 'center' }}>{it.vat ? it.vat + '%' : ''}</td>
                  <td style={{ ...cell, textAlign: 'right' }}>{fmtPrice(priceVat)}</td>
                  <td style={{ ...cell, textAlign: 'right' }}>{fmtVND(it.qty_order * priceVat)}</td>
                  <td style={cell}>{it.warehouse_code}</td>
                  <td style={cell}>{it.invoice_name}</td>
                  <td style={cell}>
                    {(it.required_date || it.expected_date) ? (
                      <div style={{ fontWeight: 600 }}>Ngày cần: {dmy(it.required_date || it.expected_date)}</div>
                    ) : null}
                    {it.note ? <div>{it.note}</div> : null}
                  </td>
                </tr>
              )
            })}
            <tr>
              <td style={{ ...cell, fontWeight: 700, textAlign: 'center' }} colSpan={9}>TỔNG CỘNG</td>
              <td style={{ ...cell, textAlign: 'right', fontWeight: 700 }}>{fmtVND(po.order_total)}</td>
              <td style={cell} colSpan={3} />
            </tr>
          </tbody>
        </table>

        {/* Thỏa thuận khác */}
        <div style={{ fontSize: 11.5, marginTop: 12, lineHeight: 1.7 }}>
          <div style={{ fontStyle: 'italic', fontWeight: 700 }}>* Thoả thuận khác:</div>
          <div><b>1. Thời gian thanh toán/ Số ngày công nợ:</b> {po.payment_terms || sup.payment_terms || '............'}</div>
          <div><b>2. Thời gian nhận hóa đơn:</b> Chậm nhất 24h kể từ khi nhận hàng</div>
          <div><b>3. Thông tin nhận hàng:</b></div>
          <div style={{ paddingLeft: 16 }}>- Phương thức giao nhận:</div>
          <div style={{ paddingLeft: 16 }}>- Nơi giao (kho nhận): {wh.name || co.name || ''}</div>
          <div style={{ paddingLeft: 16 }}>- Địa chỉ: {wh.address || co.address || ''}</div>
          <div style={{ paddingLeft: 16 }}>- Người liên hệ bên mua:</div>
          <div><b>4. Thông tin nhận hóa đơn:</b></div>
          <div style={{ paddingLeft: 16 }}>- Tên đơn vị: {co.name || ''}</div>
          <div style={{ paddingLeft: 16 }}>- Mã số thuế: {co.tax_code || ''}</div>
          <div style={{ paddingLeft: 16 }}>- Địa chỉ: {co.address || ''}</div>
          <div style={{ paddingLeft: 16 }}>- Mail nhận hóa đơn: {co.invoice_email || ''}</div>
          <div><b>5. Hàng lỗi, sai mẫu:</b></div>
          <div style={{ paddingLeft: 16 }}>- Bên mua kiểm tra hàng trong vòng 15 ngày kể từ ngày nhận hàng.</div>
          <div style={{ paddingLeft: 16 }}>- Nếu hàng lỗi/sai mẫu, Bên mua thông báo kèm bằng chứng cho Bên bán.</div>
          <div style={{ paddingLeft: 16 }}>- Bên bán phải thu hồi, đổi trả trong vòng 07 ngày; mọi chi phí phát sinh do Bên bán chịu.</div>
        </div>

        <div style={{ fontSize: 11.5, marginTop: 10 }}>Các thông tin, file, hình ảnh gửi kèm đơn hàng:</div>
        <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 18, fontSize: 12 }}>
          <div style={{ width: '48%', textAlign: 'center' }}>
            <b>Trưởng bộ phận</b>
            <div style={{ fontStyle: 'italic', fontSize: 11 }}>(Ký, ghi rõ họ tên)</div>
            <div style={{ height: 60 }} />
          </div>
          <div style={{ width: '48%', textAlign: 'center' }}>
            <div style={{ fontStyle: 'italic', fontSize: 11.5, marginBottom: 6 }}>{viDate(po.order_date)}</div>
            <b>Người lập</b>
            <div style={{ fontStyle: 'italic', fontSize: 11 }}>(Ký, ghi rõ họ tên)</div>
            <div style={{ height: 60 }} />
          </div>
        </div>
      </div>
    </div>
  )
}
