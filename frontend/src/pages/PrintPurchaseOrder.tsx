import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { api } from '../api/client'
import NotFound from '../components/NotFound'
import { tenFileIn, usePrintTitle } from '../hooks/usePrintTitle'
import { resolveTotalsCurrency } from '../utils/money'

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
  // bao-CR-321 — điều khoản mục 2 + mục 5 do backend gộp sẵn (đơn -> NCC -> mặc định).
  // Vẫn để mặc định ở đây phòng gọi nhầm bản API cũ chưa trả `print_terms`.
  const terms = po.print_terms || {}
  const inspectionDays = terms.inspection_days_label || '15'
  const returnDays = terms.return_days_label || '07'
  const invoiceDeadline = terms.invoice_deadline || 'Chậm nhất 24h kể từ khi nhận hàng'
  // bao-CR-364: từ bao-CR-319 mỗi dòng hàng mang tiền tệ riêng, còn tờ này in số nguyên tệ mà
  // không nói nó là tiền gì — đơn USD đọc ra y hệt đơn VND. Chú thêm tên tiền tệ khi khác VND.
  const items: any[] = po.items || []
  const poCurrency = (po.currency || 'VND').trim() || 'VND'
  const lineCurrency = (it: any) => (it?.currency || '').trim() || poCurrency
  const lineRate = (it: any) => Number(it?.exchange_rate) || Number(po.exchange_rate) || 1
  const { currency, mixed: mixedCurrency } =
    resolveTotalsCurrency(items.map((it) => lineCurrency(it)), poCurrency)
  const foreign = mixedCurrency || currency !== 'VND'
  const curSuffix = foreign ? ` (${mixedCurrency ? 'nguyên tệ' : currency})` : ''
  // Tổng QUY ĐỔI: nhân tỷ giá của TỪNG dòng rồi mới cộng.
  const totalBase = items.reduce(
    (s: number, it: any) => s + (Number(it.order_total) || 0) * lineRate(it), 0)

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
              {/* bao-CR-364: trộn nhiều loại tiền thì mọc thêm cột Tiền tệ */}
              {mixedCurrency && <td style={head}>Tiền tệ</td>}
              <td style={head}>Đơn giá (Chưa VAT){curSuffix}</td><td style={head}>VAT</td><td style={head}>Đơn giá (Đã VAT){curSuffix}</td>
              <td style={head}>Thành tiền{curSuffix}</td><td style={head}>Kho nhận</td><td style={head}>Tên trên HĐ</td><td style={head}>Ghi chú</td>
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
                  {mixedCurrency && (
                    <td style={{ ...cell, textAlign: 'center' }}>
                      {lineCurrency(it)}
                      <div style={{ fontSize: 9.5 }}>{fmtPrice(lineRate(it))}</div>
                    </td>
                  )}
                  <td style={{ ...cell, textAlign: 'right' }}>{fmtPrice(it.price)}</td>
                  <td style={{ ...cell, textAlign: 'center' }}>{it.vat ? it.vat + '%' : ''}</td>
                  <td style={{ ...cell, textAlign: 'right' }}>{fmtPrice(priceVat)}</td>
                  {/* Tiền ngoại tệ KHÔNG làm tròn về đơn vị — cắt phần lẻ là lệch tiền sau quy đổi */}
                  <td style={{ ...cell, textAlign: 'right' }}>
                    {foreign ? fmtPrice(it.qty_order * priceVat) : fmtVND(it.qty_order * priceVat)}
                  </td>
                  <td style={cell}>{it.warehouse_code}</td>
                  <td style={cell}>{it.invoice_name}</td>
                  <td style={cell}>
                    {(it.required_date || it.expected_date) ? (
                      <div style={{ fontWeight: 600 }}>Ngày cần hàng: {dmy(it.required_date || it.expected_date)}</div>
                    ) : null}
                    {it.note ? <div>{it.note}</div> : null}
                  </td>
                </tr>
              )
            })}
            <tr>
              <td style={{ ...cell, fontWeight: 700, textAlign: 'center' }} colSpan={mixedCurrency ? 10 : 9}>TỔNG CỘNG{curSuffix}</td>
              {/* bao-CR-364: trộn nhiều loại tiền thì cộng ngang là cộng USD với VND — để gạch
                  ngang, tổng thật nằm ở dòng quy đổi bên dưới. */}
              <td style={{ ...cell, textAlign: 'right', fontWeight: 700 }}>
                {mixedCurrency ? '—' : foreign ? fmtPrice(po.order_total) : fmtVND(po.order_total)}
              </td>
              <td style={cell} colSpan={3} />
            </tr>
            {foreign && (
              <tr>
                <td style={{ ...cell, fontWeight: 700, textAlign: 'center' }} colSpan={mixedCurrency ? 10 : 9}>TỔNG CỘNG (quy đổi VNĐ)</td>
                <td style={{ ...cell, textAlign: 'right', fontWeight: 700 }}>{fmtVND(totalBase)}</td>
                <td style={cell} colSpan={3} />
              </tr>
            )}
          </tbody>
        </table>

        {/* Thỏa thuận khác */}
        <div style={{ fontSize: 11.5, marginTop: 12, lineHeight: 1.7 }}>
          <div style={{ fontStyle: 'italic', fontWeight: 700 }}>* Thoả thuận khác:</div>
          <div><b>1. Thời gian thanh toán/ Số ngày công nợ:</b> {po.payment_terms || sup.payment_terms || '............'}</div>
          <div><b>2. Thời gian nhận hóa đơn:</b> {invoiceDeadline}</div>
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
          <div style={{ paddingLeft: 16 }}>- Bên mua kiểm tra hàng trong vòng {inspectionDays} ngày kể từ ngày nhận hàng.</div>
          <div style={{ paddingLeft: 16 }}>- Nếu hàng lỗi/sai mẫu, Bên mua thông báo kèm bằng chứng cho Bên bán.</div>
          <div style={{ paddingLeft: 16 }}>- Bên bán phải thu hồi, đổi trả trong vòng {returnDays} ngày; mọi chi phí phát sinh do Bên bán chịu.</div>
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
