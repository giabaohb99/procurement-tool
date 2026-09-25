import type { PurchaseRequestOption } from './purchase-request-options'

/**
 * bao-CR-422 — một YCBG đã sinh ra phiếu YCMH này, đủ để bày một dòng bấm được mà
 * không phải gọi thêm API: mã để bấm, trạng thái / ngày / người yêu cầu để người
 * đọc biết nguồn đang tới đâu.
 */
export interface LinkedSurveyRequest {
  id: number
  code: string
  /** Mã trạng thái YCBG — tra nhãn ở `SR_STATUS_LABELS`. */
  status: string
  request_date: string
  requester: string
}

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
  /**
   * bao-CR-310 — số PHƯƠNG ÁN đã gắn + phương án ĐÃ CHỐT của dòng. TÙY CHỌN vì
   * dòng nháp dựng ở màn sửa (spread EMPTY_PURCHASE_REQUEST_ITEM) không có chúng.
   */
  option_count?: number
  chosen_option?: PurchaseRequestOption | null
  /**
   * bao-CR-310 đợt 3b — NSTM đã "chốt hoàn thành xử lý" dòng chưa (khuôn YCBG):
   * chốt rồi NSTM hết sửa phương án, người yêu cầu mới bắt đầu chọn ở màn chi tiết.
   * `no_option` = chốt rỗng: xử lý rồi nhưng không có NCC phù hợp.
   */
  options_done?: boolean
  no_option?: boolean
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
  /**
   * CR-071: id NHÂN SỰ của người đứng tên Trưởng bộ phận trên phiếu.
   * `0` = lấy mặc định theo phòng ban. Ô này CHỈ để lưu + in, KHÔNG khóa quyền duyệt.
   * `head_of_dept` ở trên chỉ là bản chụp TÊN để in, backend đồng bộ theo id này.
   */
  head_of_dept_id: number
  /**
   * bao-CR-414: id PHÒNG BAN được NHỜ xử lý phiếu. `0` = không nhờ (thu mua chung xử lý,
   * hoặc phòng tự mua nếu phòng lập phiếu có bộ máy thu mua riêng). Chọn phòng thì quản lý
   * thu mua của phòng đó thấy + điều phối được phiếu; backend chép xuống ĐMH/YCBG con.
   */
  handler_dept_id: number
  /**
   * bao-CR-480: TÊN phòng xử lý do backend trả kèm (rỗng = thu mua chung) — màn hình
   * không cần quyền đọc danh mục phòng ban mới hiện được tên.
   */
  handler_dept_name?: string
  purpose: string
  /** bao-CR-316: ngày LẬP phiếu — không ai ghi đè nữa, xem `received_date` ngay dưới. */
  request_date: string
  /** Ngày thu mua TIẾP NHẬN phiếu; rỗng = chưa tiếp nhận. Chỉ backend điền lúc điều phối. */
  received_date: string
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
   * bao-CR-317 — backend tính: có báo giá đính kèm hay không, gộp cả tệp cũ
   * (`quote_file_url`) lẫn tệp đính kèm mới qua `tab_file`. Bản in đọc cờ này.
   */
  has_quote_file?: boolean
  /**
   * bao-CR-318 — YCBG sinh ra phiếu này (0 / rỗng = lập tay).
   *
   * Đây là phiếu nguồn ĐẦU TIÊN thôi. Một YCMH gom được nhiều dòng đã chốt phương
   * án nằm ở những YCBG khác nhau, nên danh sách đủ ở `survey_requests` (bao-CR-422).
   * Hai khóa này giữ nguyên tên vì giao diện cũ và bản in đang đọc thẳng chúng.
   */
  survey_request_id?: number
  survey_request_code?: string
  /** bao-CR-422 — MỌI YCBG đã sinh ra phiếu này, theo thứ tự liên kết. */
  survey_requests?: LinkedSurveyRequest[]

  /**
   * Công tắc "duyệt điều phối" của hệ thống. TẮT thì phiếu "Đã duyệt" đã làm
   * việc được luôn, không phải chờ bước điều phối.
   */
  dispatch_enabled: boolean
  /**
   * bao-CR-468 — công tắc cụm PHƯƠNG ÁN (màn Xử lý phương án + thẻ Chọn phương án).
   * Bật/tắt ở màn Cấu hình hệ thống; backend gửi kèm phiếu vì người dùng thường không có
   * quyền đọc cấu hình. TẮT thì hai chỗ đó biến mất và mọi thao tác phương án bị từ chối.
   * Bản backend cũ không gửi khóa này — thiếu thì coi như TẮT, đừng đọc trần.
   */
  options_enabled?: boolean
  /** Backend đã tính sẵn quyền của NGƯỜI ĐANG ĐĂNG NHẬP trên phiếu này. */
  can_dispatch: boolean
  can_approve: boolean
  /** bao-CR-414 GĐ5: được đẩy cả phiếu sang phòng khác / trả về phòng lập tự xử lý. */
  can_transfer_dept?: boolean
  can_return_dept?: boolean
  /** bao-CR-414 GĐ5: id phòng LẬP phiếu — backend luôn trả, chỉ hộp chuyển phòng cần tới. */
  department_id?: number

  created_at: string
  created_by_name: string
  requester_signature: string
  approver_name: string
  approver_signature: string
  dispatcher_name: string
  dispatcher_signature: string
  /**
   * bao-CR-397: TRƯỞNG PHÒNG của người bấm Điều phối (Department.manager_id) — người ký
   * ô "TP/BP mua hàng" trên bản in. Phòng chưa gán trưởng thì backend trả đúng
   * `dispatcher_*`. Rỗng khi phiếu chưa tới bước điều phối.
   */
  purchasing_head_name: string
  purchasing_head_signature: string
  /**
   * bao-CR-419 — MỐC "người yêu cầu đã chốt xong lựa chọn phương án" cho cả phiếu.
   * Rỗng nghĩa là chưa bấm chốt (kể cả khi mọi dòng đã có phương án được tick, vì
   * phương án 0 luôn được tick sẵn). Mở lại một dòng cho NSTM là mốc này bị xóa.
   */
  options_chosen_at: string | null
  options_chosen_by_name: string

  items: PurchaseRequestItem[]
  /** Tiền hàng chưa VAT / tiền VAT / tổng cộng — backend cộng từ các dòng. */
  subtotal: number
  vat: number
  total: number
}

/**
 * Phiếu YCMH mở TỪ MỘT ĐƠN MUA HÀNG — `GET /api/purchase-orders/{id}/purchase-request`
 * (bao-CR-314). Backend đã cắt `items` còn đúng các dòng có trên đơn đó và tính lại
 * `subtotal` / `vat` / `total` theo phần cắt, nên đây vẫn là một phiếu hợp lệ để in.
 */
export interface PurchaseRequestFromPo extends PurchaseRequestDetail {
  /** Mã đơn mua hàng đã mở bản in này. */
  po_code: string
  /**
   * Số dòng trên ĐƠN không đối chiếu được sang phiếu (bỏ trống mã hàng, hoặc mã không
   * có trên phiếu) nên KHÔNG in ra. Chỉ báo ở thanh công cụ, không in vào tờ giấy.
   */
  po_lines_unmatched: number
}

/**
 * Một người ĐƯỢC PHÉP duyệt bước 1 của phiếu — nguồn của ô "Trưởng bộ phận"
 * (`GET /api/purchase-requests/{id}/dept-head-candidates`, CR-071).
 * Danh sách rỗng = chưa ai đủ điều kiện, ô để dạng chữ như cũ.
 */
export interface DeptHeadCandidate {
  employee_id: number
  name: string
  code: string
  position: string
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

/**
 * Phiếu đã qua bước ĐIỀU PHỐI chưa — tức thu mua đã thật sự nhận việc chưa.
 *
 * Công tắc điều phối TẮT không phải ngoại lệ: lúc đó bước duyệt gọi thẳng `dispatch_pr`
 * nên phiếu vẫn sang `dispatched` — vì vậy luật này soi TRẠNG THÁI phiếu chứ không soi
 * công tắc.
 *
 * bao-CR-316: muốn HIỂN THỊ Ngày tiếp nhận thì đọc thẳng `received_date` (rỗng = chưa tiếp
 * nhận), đừng suy từ trạng thái. Luật này chỉ còn để bật/tắt thao tác theo bước làm việc.
 */
export function isDispatched(status: string): boolean {
  return ['dispatched', 'processing', 'purchasing', 'purchased', 'completed', 'done'].includes(
    status,
  )
}
