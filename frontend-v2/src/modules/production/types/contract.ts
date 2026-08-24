/**
 * Hợp đồng — khớp `_out()` của `backend/app/modules/contract/controller.py`.
 *
 * Đặt ở phân hệ Sản xuất vì hợp đồng gắn với danh mục ĐỐI TÁC (nhà cung cấp,
 * khách hàng) chứ không thuộc một chứng từ mua hàng nào.
 */
export type Contract = {
  id: number
  code: string
  /** MÃ `supplier` | `customer` | `other` (B-02). Hiển thị thì dùng `party_type_label`. */
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
  /** MÃ `active` | `expired` | `liquidated` | `cancelled` (B-02). */
  status: string
  note: string
  /**
   * Tình trạng hiệu lực do BACKEND tính theo `end_date` so với hôm nay —
   * MÃ `expired` | `expiring_soon` (còn ≤ 30 ngày) | `valid` | rỗng (không có hạn).
   * Không tính lại ở frontend: máy người dùng lệch giờ là ra kết quả khác.
   *
   * ⚠️ `expired` của bộ này KHÁC `expired` của `status`: cái này TÍNH từ ngày hết hạn,
   * cái kia do người dùng đặt tay. Một hợp đồng quá hạn mà chưa ai đụng vào thì
   * `expiry = "expired"` nhưng `status` vẫn là `active`.
   */
  expiry: string
  /**
   * Nhãn tiếng Việt backend gửi kèm cho bốn cột mã ở trên (B-02).
   *
   * Có sẵn nhãn nhưng chỗ nào vẽ ĐỒNG BỘ (chip, ô chọn, bộ lọc) vẫn tra từ
   * `@/shared/constants/statuses` — nhãn chỉ đi cùng bản ghi, không đi cùng ô chọn rỗng.
   */
  party_type_label: string
  status_label: string
  expiry_label: string
  contract_type_label: string
}
