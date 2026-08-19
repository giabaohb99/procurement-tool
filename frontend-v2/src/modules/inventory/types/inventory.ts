/**
 * Kiểu dữ liệu của phân hệ Kho — khớp `_out()` trong
 * `backend/app/modules/inventory/controller.py`.
 */

/**
 * Một dòng TỒN HIỆN TẠI. Khóa nghiệp vụ là bộ ba (công ty · kho · mã SP);
 * `id` chỉ là khóa kỹ thuật, đừng dùng để nối với bảng khác.
 *
 * Bảng này KHÔNG ai nhập tay trực tiếp: backend tính lại từ sổ phát sinh
 * (`tab_inventory_move`) mỗi lần nhận hàng hoặc điều chỉnh, nên `qty` /
 * `avg_cost` / `value` luôn là số dẫn xuất.
 */
export interface InventoryItem {
  id: number
  company_id: number
  /** Mã kho — `tab_inventory` neo bằng MÃ, không có cột id kho. */
  warehouse_code: string
  /** Mã sản phẩm — hạt dữ liệu chung của cả hệ (xem D-025). */
  product_code: string
  /** Bản sao TÊN sản phẩm lúc ghi sổ, không phải khóa. */
  product_name: string
  unit: string
  qty: number
  /** Đơn giá bình quân gia quyền, 4 số lẻ. */
  avg_cost: number
  /** Giá trị tồn = Σ(qty × đơn giá nhập), backend tính sẵn. */
  value: number
}

/** Một dòng sổ phát sinh nhập/xuất. `qty > 0` = nhập, `< 0` = xuất / điều chỉnh giảm. */
export interface InventoryMove {
  id: number
  company_id: number
  warehouse_code: string
  product_code: string
  qty: number
  unit_price: number
  /** `gr` = sinh từ phiếu nhận hàng · `adjust` = điều chỉnh tay. */
  ref_type: string
  /** Id lần giao hàng khi `ref_type = 'gr'`; 0 với điều chỉnh tay. */
  ref_id: number
  note: string
  /** Thời điểm ghi sổ (backend đổi tên `created_at` thành `at`). */
  at: string
  /** Họ tên người thao tác, backend join sẵn; rỗng thì trả "Hệ thống". */
  operator_name: string
}

/**
 * Lọc theo tình trạng tồn. Ba giá trị này backend đọc TAY từ query param
 * (`qty_status`), không qua `apply_filters` — nên không khai được ở bộ lọc nâng cao.
 */
export const QTY_STATUS_OPTIONS = [
  { value: 'in_stock', label: 'Có tồn (> 0)' },
  { value: 'out_of_stock', label: 'Hết hàng (= 0)' },
  { value: 'negative_stock', label: 'Âm kho (< 0)' },
] as const

const MOVE_KIND_LABELS: Record<string, string> = {
  gr: 'Nhập kho (nhận hàng)',
  adjust: 'Điều chỉnh tay',
}

export function moveKindLabel(refType: string): string {
  return MOVE_KIND_LABELS[refType] ?? 'Khác'
}

/**
 * Thành tiền của một phát sinh — GIỮ NGUYÊN DẤU.
 *
 * Bản v1 hiện `Math.abs(qty × unit_price)`: dòng điều chỉnh giảm 5 cái vẫn hiện
 * số dương, nhìn sổ tưởng kho vừa được cộng thêm tiền. Cột "Thay đổi" có dấu mà
 * cột "Thành tiền" thì không, hai cột cùng một dòng nói ngược nhau.
 */
export function moveAmount(move: Pick<InventoryMove, 'qty' | 'unit_price'>): number {
  return move.qty * move.unit_price
}
