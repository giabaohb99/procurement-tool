import type { Payable } from '@/modules/finance/types/payable'
import type { PurchaseOrderDetail } from '../types/purchase-order-detail'

/**
 * Dựng MỘT dòng công nợ ẢO cho luồng «thanh toán TRƯỚC» (CR-067).
 *
 * Đơn chưa nhận hàng thì `tab_payable` chưa có dòng nào — công nợ do backend sinh
 * ngầm lúc nhận hàng, không ai nhập tay được. Nhưng nghiệp vụ có thật: nhiều NCC
 * đòi đặt cọc / trả trước mới sản xuất. Bản v1 xử bằng cách nhảy thẳng sang màn
 * tạo YCTT với số tiền bằng TỔNG TIỀN ĐƠN; hàm này dựng đúng dòng đó cho v2.
 *
 * `id = 0` là điểm mấu chốt: màn tạo YCTT hiểu `payable_id = 0` là dòng gõ tay,
 * không gắn khoản nợ nào, nên phiếu tạo ra KHÔNG trừ vào công nợ chưa tồn tại.
 * Sau này nhận hàng xong, công nợ thật sinh ra và kế toán tự đối trừ.
 */
export function buildPrepayPayable(order: PurchaseOrderDetail): Payable {
  // Lấy tiền theo SL ĐẶT: chưa nhận hàng nên `total` (theo SL THỰC NHẬN) đang là 0.
  const amount = Number(order.order_total) || Number(order.total) || 0

  return {
    id: 0,
    company_id: order.company_id,
    supplier_code: order.supplier_code,
    supplier_name: order.supplier_name,
    source_type: 'goods',
    po_id: order.id,
    po_code: order.code,
    // Chưa có hóa đơn đỏ; mã MISA là thứ duy nhất kế toán bám được lúc này.
    invoice_no: order.misa_code || '',
    incur_date: '',
    due_date: '',
    created_at: '',
    // Chưa tách được phần trước thuế, để người lập tự sửa nếu cần.
    amount: 0,
    vat: 0,
    total: amount,
    paid_amount: 0,
    remaining: amount,
    status: 'unpaid',
    status_label: '',
    aging: '',
  }
}
