/** Một dòng hàng của phiếu YCMH — khớp `items[]` của `GET /api/purchase-requests/{id}`. */
export interface PurchaseRequestItem {
  /** 0 / thiếu = dòng mới chưa lưu. GIỮ id khi sửa, nếu không ảnh đối chiếu sẽ mồ côi. */
  id?: number
  product_code: string
  product_name: string
  item_group: string
  group_desc: string
  qty: number
  unit: string
  /** Đơn giá giữ tới 4 số lẻ. */
  price: number
  /** % VAT theo TỪNG DÒNG (phiếu cũ dùng `vat_rate` chung ở header). */
  vat_pct: number
  /** Backend tự tính = qty × price × (1 + vat_pct). */
  amount: number
  warehouse: string
  required_date: string
  /** Mã nhân sự thu mua phụ trách dòng. */
  assignee: string
  expected_date: string
  /** Trạng thái dòng — chuỗi tiếng Việt, xem `LINE_STATUSES`. */
  line_status: string
  progress_note: string
  note: string
  /** Số đã đặt / đã nhận, backend cộng từ đơn mua hàng. Chỉ đọc. */
  qty_ordered: number
  qty_received: number
  product_id: number
  product_thumbnail_url: string
}

/** Nhà cung cấp đề xuất — phiếu có HAI cụm: bộ phận yêu cầu và thu mua. */
export interface SupplierCluster {
  name: string
  tax_code: string
  contact: string
}

/** Phiếu YCMH bản chi tiết — `GET /api/purchase-requests/{id}`. */
export interface PurchaseRequestDetail {
  id: number
  code: string
  company_id: number
  company_name: string
  requester: string
  requester_id: number
  requester_position: string
  department: string
  head_of_dept: string
  purpose: string
  request_date: string
  need_date: string
  status: string
  is_urgent: boolean
  /** VAT mặc định của phiếu; từng dòng vẫn có `vat_pct` riêng. */
  vat_rate: number
  assignee_id: number
  note: string
  show_code_on_print: boolean

  /** NCC do BỘ PHẬN YÊU CẦU đề xuất — ai cũng sửa được. */
  supplier_req: SupplierCluster
  /** NCC do THU MUA / khảo sát điền — cần quyền, xem `can_edit_supplier_pur`. */
  supplier_pur: SupplierCluster
  /** Cụm `pur` lấy từ phiếu khảo sát -> không cho sửa tay. */
  supplier_from_survey: boolean
  can_edit_supplier_pur: boolean

  /** Cột cũ (một cụm) — giữ để đọc dữ liệu phiếu lập trước khi tách hai cụm. */
  suggested_supplier: string
  suggested_supplier_tax_code: string
  suggested_supplier_contact: string
  quote_filename: string
  quote_file_url: string

  /**
   * Công tắc "duyệt điều phối" của hệ thống. TẮT thì phiếu "Đã duyệt" đã làm
   * việc được luôn, không phải chờ bước điều phối.
   */
  dispatch_enabled: boolean
  /** Backend đã tính sẵn quyền của NGƯỜI ĐANG ĐĂNG NHẬP trên phiếu này. */
  can_dispatch: boolean
  can_approve: boolean

  created_at: string
  created_by_name: string
  requester_signature: string
  approver_name: string
  approver_signature: string
  dispatcher_name: string
  dispatcher_signature: string

  items: PurchaseRequestItem[]
  /** Tiền hàng chưa VAT / tiền VAT / tổng cộng — backend cộng từ các dòng. */
  subtotal: number
  vat: number
  total: number
}

/** Trạng thái của một DÒNG hàng (khác trạng thái phiếu). */
export const LINE_STATUSES = [
  'Chưa đặt hàng',
  'Đã đặt hàng',
  'Đã nhận hàng',
  'Hoàn thành',
  'Hủy đơn',
] as const

/** Mức VAT hay dùng, đặt sẵn cho ô chọn ở dòng hàng. */
export const VAT_OPTIONS = [0, 5, 8, 10] as const

/** Phiếu đã chốt -> khóa mọi thao tác ghi. */
export function isClosed(status: string): boolean {
  return ['cancelled', 'completed', 'done'].includes(status)
}

/** Chỉ nháp và bị trả lại mới sửa được nội dung phiếu. */
export function isEditable(status: string): boolean {
  return ['draft', 'rejected'].includes(status)
}
