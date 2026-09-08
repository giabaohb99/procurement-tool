import { formatMoney, formatQuantity, formatUnitPrice } from '@/shared/utils/format-money'
import { formatDate } from '@/shared/utils/format-date'
import { numberToVietnameseWords } from '@/shared/utils/number-to-vietnamese-words'
import type { PurchaseOrderPrintData } from '../api/purchase-order-api'
import { PurchaseOrderPrintSignatureBox } from './purchase-order-print-signature-box'

interface PurchaseOrderPrintGoodsFormProps {
  data: PurchaseOrderPrintData
  /** Tắt thì chỉ bỏ ẢNH chữ ký, họ tên vẫn in để người ký tay biết ký vào ô nào. */
  showSignature?: boolean
}

/**
 * Mẫu **ĐƠN MUA HÀNG** lưu nội bộ / gửi kế toán (khổ dọc).
 *
 * Khác mẫu Đơn đặt hàng ở chỗ có cột SL THỰC NHẬP, tiền thuế tách riêng và số
 * tiền viết bằng chữ — đây là bản đối chiếu khi nhận hàng, không phải bản chào.
 */
export function PurchaseOrderPrintGoodsForm({
  data,
  showSignature = true,
}: PurchaseOrderPrintGoodsFormProps) {
  const company = data.company ?? {}
  const supplier = data.supplier ?? {}
  const warehouseNames = data.wh_names ?? {}
  const signers = data.signers
  const total = data.order_total || 0
  const tax = Math.round((total - (data.order_subtotal || 0)) * 100) / 100
  /** "Công nợ 30 ngày" -> 30. Chỉ để điền ô "Số ngày được nợ". */
  const debtDays = /(\d+)\s*ng[aà]y/i.exec(data.payment_terms || '')?.[1] ?? ''

  return (
    <article className="po-print-doc po-print-doc--portrait">
      <div className="border-b-2 border-[#1a4d6b] pb-1.5">
        <p className="text-[13px] font-bold">{company.name}</p>
        <p className="text-[10.5px] italic">Địa chỉ: {company.address}</p>
      </div>

      <h1 className="my-3 text-center text-[17px] font-bold">ĐƠN MUA HÀNG</h1>

      <div className="flex justify-between text-[11.5px] leading-7">
        <div className="flex-1">
          <p>
            <b>Tên nhà cung cấp:</b> {supplier.name || data.supplier_name}
          </p>
          <p>
            <b>Địa chỉ:</b> {supplier.address}
          </p>
          <p>
            <b>Mã số thuế:</b> {supplier.tax_code}
          </p>
          <p>
            <b>Nhân viên mua hàng:</b> {data.nspt}
          </p>
          <p>
            <b>Diễn giải:</b> {data.note}
          </p>
        </div>
        <div className="w-56 pl-3">
          <p>
            <b>Ngày:</b> {formatDate(data.order_date)}
          </p>
          <p>
            <b>Số:</b> {data.misa_code || data.code}
          </p>
          <p>
            <b>Loại tiền:</b> VND
          </p>
        </div>
      </div>

      <table className="po-print-table mt-2">
        <thead>
          <tr>
            <th>STT</th>
            <th>Tên kho nhập</th>
            <th>Mã hàng</th>
            <th>Tên hàng</th>
            <th>Tên hàng xuất hóa đơn</th>
            <th>ĐVT</th>
            <th>SL yêu cầu</th>
            <th>SL thực nhập</th>
            <th>Đơn giá</th>
            <th>Thành tiền</th>
            <th>Ghi chú</th>
          </tr>
        </thead>
        <tbody>
          {data.items.map((item, index) => (
            <tr key={item.id ?? index}>
              <td className="text-center">{index + 1}</td>
              <td>{warehouseNames[item.warehouse_code] || item.warehouse_code}</td>
              <td>{item.product_code}</td>
              <td>{item.product_name}</td>
              <td>{item.invoice_name}</td>
              <td className="text-center">{item.unit}</td>
              <td className="text-right">{formatQuantity(item.qty_order)}</td>
              <td className="text-right">
                {item.qty_received ? formatQuantity(item.qty_received) : '-'}
              </td>
              <td className="text-right">{formatUnitPrice(item.price)}</td>
              <td className="text-right">{formatMoney(item.qty_order * item.price)}</td>
              <td>{item.note}</td>
            </tr>
          ))}
          <tr>
            <td className="font-bold" colSpan={9}>
              Tiền thuế GTGT:
            </td>
            <td className="text-right font-bold">{formatMoney(tax)}</td>
            <td />
          </tr>
          <tr>
            <td className="font-bold" colSpan={9}>
              Tổng tiền thanh toán:
            </td>
            <td className="text-right font-bold">{formatMoney(total)}</td>
            <td />
          </tr>
        </tbody>
      </table>

      <p className="mt-1 text-[11.5px] italic">
        <b>Số tiền viết bằng chữ:</b> {numberToVietnameseWords(total)}.
      </p>

      <div className="mt-3 flex justify-between text-[11.5px]">
        <span>
          <b>Ngày giao hàng:</b> ....................
        </span>
        <span>
          <b>Số ngày được nợ:</b> {debtDays || '..........'} {debtDays ? 'ngày' : ''}
        </span>
      </div>
      <p className="mt-1.5 text-[11.5px]">
        <b>Điều khoản thanh toán:</b> {data.payment_terms}
      </p>

      <div className="mt-2 flex gap-5 text-[11px]">
        <div className="flex-1 border border-[#888] px-2 py-1.5">
          <p className="mb-1 font-semibold">Hồ sơ NCC gửi kèm:</p>
          {[1, 2, 3, 4].map((line) => (
            <p key={line}>{line}. ..................................</p>
          ))}
        </div>
        <div className="flex-1 border border-[#888] px-2 py-1.5">
          <p className="mb-1 font-semibold">Các tiêu chí cần nhà máy đánh giá trước khi nhận:</p>
          <p className="mb-0.5 text-[10px] italic">
            (VD: màu sắc, ngoại dạng, trọng lượng, bao bì…)
          </p>
          {[1, 2, 3, 4].map((line) => (
            <p key={line}>{line}. ..................................</p>
          ))}
        </div>
      </div>

      {/* Ô "Người nhận" luôn để trống: hệ thống không có thao tác nào ứng với việc
          nhận hàng tận tay, ô đó ký tươi lúc giao nhận. */}
      <div className="mt-5 flex justify-around text-[11.5px]">
        <PurchaseOrderPrintSignatureBox
          className="flex-1"
          title="Người lập"
          hint="(Ký, họ tên)"
          name={signers?.creator_name}
          signature={showSignature ? signers?.creator_signature : ''}
        />
        <PurchaseOrderPrintSignatureBox className="flex-1" title="Người nhận" hint="(Ký, họ tên)" />
        <PurchaseOrderPrintSignatureBox
          className="flex-1"
          title="Trưởng phòng / Trưởng BP"
          hint="(Ký, họ tên)"
          name={signers?.approver_name}
          signature={showSignature ? signers?.approver_signature : ''}
        />
      </div>
    </article>
  )
}
