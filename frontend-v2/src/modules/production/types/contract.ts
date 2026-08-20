/**
 * Hợp đồng — khớp `_out()` của `backend/app/modules/contract/controller.py`.
 *
 * Đặt ở phân hệ Sản xuất vì hợp đồng gắn với danh mục ĐỐI TÁC (nhà cung cấp,
 * khách hàng) chứ không thuộc một chứng từ mua hàng nào.
 */
export interface Contract {
  id: number
  code: string
  /** `Nhà cung cấp` | `Khách hàng` — DB lưu thẳng chuỗi tiếng Việt, không phải mã enum. */
  party_type: string
  /** Mã đối tác. Với NCC đây chính là `Supplier.code`. */
  party_code: string
  party_name: string
  company_id: number
  title: string
  contract_type: string
  start_date: string
  end_date: string
  signed: boolean
  status: string
  note: string
  /**
   * Tình trạng hiệu lực do BACKEND tính theo `end_date` so với hôm nay —
   * `Hết hạn` | `Sắp hết hạn` (còn ≤ 30 ngày) | `Còn hạn` | rỗng (không có hạn).
   * Không tính lại ở frontend: máy người dùng lệch giờ là ra kết quả khác.
   */
  expiry: string
}

/** Tình trạng hiệu lực, theo đúng thứ tự "cần xử lý trước" của người dùng. */
export const CONTRACT_EXPIRY_STATES = ['Hết hạn', 'Sắp hết hạn', 'Còn hạn'] as const
