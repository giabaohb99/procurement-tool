import type { PurchaseOrderPrintData } from '../api/purchase-order-api'
import { formatMoney, formatQuantity, formatUnitPrice } from '@/shared/utils/format-money'

/**
 * Mẫu **ĐƠN ĐẶT HÀNG** gửi nhà cung cấp (khổ ngang).
 *
 * Số liệu lấy theo SL ĐẶT — đây là cam kết mua, không phải biên bản nhận hàng.
 */
export function PurchaseOrderPrintOrderForm({ data }: { data: PurchaseOrderPrintData }) {
  const company = data.company ?? {}
  const supplier = data.supplier ?? {}
  const warehouse = data.warehouse ?? {}

  return (
    <article className="po-print-doc po-print-doc--landscape">
      <p className="text-[14px] font-bold">{company.name}</p>
      <p className="text-[11px]">Địa chỉ: {company.address}</p>
      <p className="text-[11px]">Mã số thuế: {company.tax_code}</p>
      <p className="mt-2 text-[12px]">
        <b>Kính gửi:</b> {supplier.name || data.supplier_name}
      </p>
      <p className="text-[12px]">
        <b>Địa chỉ:</b> {supplier.address}
      </p>

      <h1 className="mt-3 text-center text-[18px] font-bold">ĐƠN ĐẶT HÀNG</h1>
      <p className="mb-2 text-center text-[12px] font-bold text-red-700">
        Số: {data.misa_code || data.code}
      </p>

      <table className="po-print-table">
        <thead>
          <tr>
            <th>STT</th>
            <th>Mã</th>
            <th>Tên hàng hóa</th>
            <th>
              Xuất xứ / TSKT /<br />
              chất liệu
            </th>
            <th>ĐVT</th>
            <th>SL</th>
            <th>Đơn giá (chưa VAT)</th>
            <th>VAT</th>
            <th>Đơn giá (đã VAT)</th>
            <th>Thành tiền</th>
            <th>Kho nhận</th>
            <th>Tên trên HĐ</th>
            <th>Ghi chú</th>
          </tr>
        </thead>
        <tbody>
          {data.items.map((item, index) => {
            const priceWithVat = item.price * (1 + (item.vat || 0) / 100)
            return (
              <tr key={item.id ?? index}>
                <td className="text-center">{index + 1}</td>
                <td>{item.product_code}</td>
                <td>{item.product_name}</td>
                <td>{item.spec}</td>
                <td className="text-center">{item.unit}</td>
                <td className="text-right">{formatQuantity(item.qty_order)}</td>
                <td className="text-right">{formatUnitPrice(item.price)}</td>
                <td className="text-center">{item.vat ? `${item.vat}%` : ''}</td>
                <td className="text-right">{formatUnitPrice(priceWithVat)}</td>
                <td className="text-right">{formatMoney(item.qty_order * priceWithVat)}</td>
                <td>{item.warehouse_code}</td>
                <td>{item.invoice_name}</td>
                <td>{item.note}</td>
              </tr>
            )
          })}
          <tr>
            <td className="text-center font-bold" colSpan={9}>
              TỔNG CỘNG
            </td>
            <td className="text-right font-bold">{formatMoney(data.order_total)}</td>
            <td colSpan={3} />
          </tr>
        </tbody>
      </table>

      <div className="mt-3 text-[11.5px] leading-7">
        <p className="font-bold italic">* Thỏa thuận khác:</p>
        <p>
          <b>1. Thời gian thanh toán / Số ngày công nợ:</b>{' '}
          {data.payment_terms || supplier.payment_terms || '............'}
        </p>
        <p>
          <b>2. Thời gian nhận hóa đơn:</b> Chậm nhất 24h kể từ khi nhận hàng
        </p>
        <p>
          <b>3. Thông tin nhận hàng:</b>
        </p>
        <p className="pl-4">- Phương thức giao nhận:</p>
        <p className="pl-4">- Nơi giao (kho nhận): {warehouse.name || company.name}</p>
        <p className="pl-4">- Địa chỉ: {warehouse.address || company.address}</p>
        <p className="pl-4">- Người liên hệ bên mua:</p>
        <p>
          <b>4. Thông tin nhận hóa đơn:</b>
        </p>
        <p className="pl-4">- Tên đơn vị: {company.name}</p>
        <p className="pl-4">- Mã số thuế: {company.tax_code}</p>
        <p className="pl-4">- Địa chỉ: {company.address}</p>
        <p className="pl-4">- Mail nhận hóa đơn: {company.invoice_email}</p>
        <p>
          <b>5. Hàng lỗi, sai mẫu:</b>
        </p>
        <p className="pl-4">- Bên mua kiểm tra hàng trong vòng 15 ngày kể từ ngày nhận hàng.</p>
        <p className="pl-4">
          - Nếu hàng lỗi/sai mẫu, Bên mua thông báo kèm bằng chứng cho Bên bán.
        </p>
        <p className="pl-4">
          - Bên bán phải thu hồi, đổi trả trong vòng 07 ngày; mọi chi phí phát sinh do Bên bán
          chịu.
        </p>
      </div>

      <p className="mt-2 text-[11.5px]">Các thông tin, file, hình ảnh gửi kèm đơn hàng:</p>

      <div className="mt-4 flex justify-between text-[12px]">
        <div className="w-[48%] text-center">
          <b>Trưởng bộ phận</b>
          <p className="text-[11px] italic">(Ký, ghi rõ họ tên)</p>
          <div className="h-16" />
        </div>
        <div className="w-[48%] text-center">
          <p className="mb-1 text-[11.5px] italic">{signatureDate(data.order_date)}</p>
          <b>Người lập</b>
          <p className="text-[11px] italic">(Ký, ghi rõ họ tên)</p>
          <div className="h-16" />
        </div>
      </div>
    </article>
  )
}

/** "Cần Thơ, ngày dd tháng mm năm yyyy" — nơi lập giữ theo bản v1. */
function signatureDate(date: string): string {
  if (!date) return ''
  const [year, month, day] = date.split('-')
  return `Cần Thơ, ngày ${day} tháng ${month} năm ${year}`
}
