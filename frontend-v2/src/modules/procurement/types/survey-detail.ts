/**
 * Phiếu KHẢO SÁT — bản chi tiết.
 *
 * Một phiếu gộp HAI bảng dòng độc lập nhau, backend lưu hai bảng khác nhau và
 * `GET /api/surveys/{id}` trả cả hai trong cùng một khung:
 * - `supplier_lines` — khảo sát NHÀ CUNG CẤP (27 cột: pháp lý, chính sách, đánh giá).
 * - `product_lines`  — khảo sát SẢN PHẨM (31 cột: báo giá, quy đổi, mẫu, LAB).
 *
 * Vì mỗi bảng vài chục cột và cùng một ô phải hiện được ở CẢ bảng lẫn popup chi
 * tiết dòng, cấu trúc cột được khai báo thành dữ liệu (`*_COLS` cho bảng,
 * `*_SECTIONS` cho popup) rồi render bằng một bộ renderer chung. Thêm cột mới =
 * thêm một dòng vào hai mảng, không phải sửa JSX.
 *
 * HAI CHỖ LỆCH GIỮA UI VÀ DB — đọc trước khi sửa (xem CR-091 trong change-log):
 * 1. `supplier_available` KHÔNG có cột DB và không có trong schema Pydantic. Nó
 *    chỉ là công tắc đổi kiểu ô NCC (chọn từ danh mục ↔ gõ tay). Bản v1 để mặc
 *    định bật nên tải lại phiếu là dòng NCC gõ tay nhảy về ô chọn; bản này suy
 *    lại từ dữ liệu (mã không khớp danh mục = NCC chưa có, tự tắt).
 * 2. Bảng SẢN PHẨM không có cột `supplier_name` (cả model lẫn `ProductLineIn`
 *    đều không có) — bản v1 vẫn cho gõ, và mọi thứ gõ vào đó bị vứt lúc lưu.
 *    Bản này để ô "Tên pháp lý" ở bảng SP thành CHỈ ĐỌC, suy từ danh mục NCC
 *    theo `supplier_code`. Muốn cho sửa thật thì phải thêm cột DB + migration.
 */

/** Hai bảng dòng của một phiếu. Dùng làm khóa cho mọi hàm nhận "bảng nào". */
export type SurveyTable = 'supplier' | 'product'

/** Giá trị một ô dòng khảo sát — không có kiểu nào khác ba kiểu này. */
export type SurveyLineValue = string | number | boolean

/**
 * Một dòng khảo sát. Cố tình để chỉ mục mở: hai bảng ~30 cột, khai báo cột là
 * dữ liệu nên renderer đọc theo `col.key` chứ không theo tên trường cố định.
 * Danh sách khóa hợp lệ nằm ở `SUPPLIER_SECTIONS` / `PRODUCT_SECTIONS`.
 */
export interface SurveyLine {
  /** Không có / 0 = dòng mới chưa lưu. */
  id?: number
  [key: string]: SurveyLineValue | undefined
}

/** Đầu phiếu + hai bảng dòng — `GET /api/surveys/{id}`. */
export interface SurveyDetail {
  id: number
  code: string
  /** `supplier` | `product` — loại phiếu suy từ bảng nào có dòng, backend tự đặt. */
  survey_type: string
  pr_code: string
  survey_request_id: number
  sr_code: string
  received_date: string
  result_due_date: string
  item_group: string
  main_content: string
  requirement_detail: string
  request_qty: number
  /** NSPT phụ trách — backend gán theo người tạo, form không cho sửa. */
  nspt: string
  /** Có mã hàng trong danh mục hay không. Bật thì mở khối mã hàng ở đầu phiếu. */
  has_product_code: boolean
  item_code: string
  item_name: string
  uom: string
  proposed_rate: number

  approve_status: string
  /** Lý do trả lại / từ chối cũng nằm ở đây — bảng `tab_survey` không có cột riêng. */
  approve_note: string
  status: string

  created_at: string
  created_by: number

  supplier_lines: SurveyLine[]
  product_lines: SurveyLine[]
  supplier_count: number
  product_count: number
  /** Tổng thành tiền các dòng SP, backend cộng sẵn. */
  subtotal: number
  main: string
}

/**
 * Kiểu ô. Quyết định renderer ở CẢ bảng lẫn popup:
 * - `text` / `textarea` — ô chữ tự giãn (mọi ô chữ đều phải xuống dòng, CR-090).
 * - `date` — `DatePicker`, giá trị `yyyy-mm-dd`.
 * - `num` — số; `vat` — số 0..99; `computed` — số backend/FE tự tính, chỉ đọc.
 * - `check` — ô tick; `select` — chọn từ `options`.
 * - `supplier` — ô chọn NCC từ danh mục (hoặc gõ tay khi NCC chưa có).
 * - `legal` — tên pháp lý NCC, CHỈ ĐỌC, suy từ danh mục (xem ghi chú đầu tệp).
 * - `unit` — chọn đơn vị tính từ danh mục.
 * - `approve` — ô duyệt của TP/QL, chỉ người có quyền `approve` mới sửa được.
 */
export type SurveyFieldType =
  | 'text'
  | 'textarea'
  | 'date'
  | 'num'
  | 'vat'
  | 'computed'
  | 'check'
  | 'select'
  | 'supplier'
  | 'legal'
  | 'unit'
  | 'approve'
  | 'lab'

/** Một cột của bảng dòng. `width` tính bằng px, bảng chạy `table-fixed`. */
export interface SurveyColumn {
  key: string
  label: string
  width: number
  type?: SurveyFieldType
  options?: readonly string[]
}

/** Một ô trong popup chi tiết dòng. `full` = chiếm trọn chiều ngang của nhóm. */
export interface SurveyField {
  key: string
  label: string
  type?: SurveyFieldType
  full?: boolean
  options?: readonly string[]
}

/** Một nhóm ô trong popup chi tiết dòng. */
export interface SurveySection {
  title: string
  fields: SurveyField[]
}

/** Bốn trạng thái duyệt DÒNG. Nhãn hiển thị chính là giá trị lưu xuống DB. */
export const SURVEY_APPROVE_OPTIONS = [
  'Chờ duyệt',
  'Đã duyệt',
  'Không duyệt',
  'Thiếu thông tin',
] as const

/**
 * Kết luận của LAB về mẫu hàng (CR-109, phiếu hỗ trợ TK20082601).
 *
 * Trước đây `lab_result` là ô chữ tự do nên mỗi người gõ một kiểu, không lọc và
 * không tô màu được. Nay nó là hai lựa chọn, phần nhận xét dài chuyển sang
 * `lab_note` ("Chi tiết đánh giá từ LAB"). Để trống = chưa có kết quả.
 */
export const SURVEY_LAB_OPTIONS = ['Mẫu đạt', 'Mẫu không đạt'] as const

/** Dòng mới luôn bắt đầu ở "Chờ duyệt" — để trống thì bảng duyệt lọc không thấy. */
export const LINE_APPROVE_DEFAULT = 'Chờ duyệt'

/** TP/QL yêu cầu bổ sung — chỉ dòng ở trạng thái này mới mở lại được để điền thêm. */
export const LINE_APPROVE_NEED_MORE = 'Thiếu thông tin'

/** Hai ô chỉ TP/QL đụng tới — kiểm tra "thiếu thông tin bắt buộc" phải bỏ qua. */
export const MANAGER_KEYS = ['line_approve', 'line_approve_note'] as const

/**
 * Những ô KHÔNG bắt buộc lúc gửi duyệt. Đa số là link/ghi chú phụ hoặc mốc thời
 * gian còn phụ thuộc phía NCC — bắt buộc thì phiếu không bao giờ gửi được.
 */
export const OPTIONAL_KEYS = [
  'supplier_code',
  'google_maps',
  'quote_folder',
  'quote_file',
  'source_of_information',
  'nspt_reason',
  'lab_note',
  'defect_return',
  'reply_date',
  'result_date',
  'result_due_date',
] as const

const RELIABILITY_OPTIONS = ['Cao', 'Trung bình', 'Thấp'] as const

const DEBT_POLICY_OPTIONS = [
  'Tiền mặt',
  'Công nợ 30 ngày',
  'Công nợ 60 ngày',
  'Công nợ 90 ngày',
  'Trả trước',
] as const

/* ========================= Bảng KHẢO SÁT NHÀ CUNG CẤP ========================= */

export const SUPPLIER_SECTIONS: SurveySection[] = [
  {
    title: 'Lịch làm việc với NCC',
    fields: [
      { key: 'contact_date', label: 'Ngày liên hệ NCC', type: 'date' },
      { key: 'reply_date', label: 'Ngày dự kiến NCC phản hồi', type: 'date' },
      { key: 'result_date', label: 'Ngày dự kiến trả KQ', type: 'date' },
    ],
  },
  {
    title: 'Thông tin nhà cung cấp',
    fields: [
      { key: 'supplier_code', label: 'Tên viết tắt NCC', type: 'supplier' },
      { key: 'supplier_name', label: 'Tên nhà cung cấp' },
      { key: 'tax_code', label: 'Mã số thuế' },
      { key: 'reg_address', label: 'Địa chỉ theo giấy đăng kí', type: 'textarea', full: true },
      { key: 'warehouse_address', label: 'Địa chỉ kho của NCC', type: 'textarea', full: true },
      { key: 'google_maps', label: 'Link định vị kho', full: true },
    ],
  },
  {
    title: 'Kinh doanh & Báo giá',
    fields: [
      { key: 'contact_person', label: 'NVKD của NCC' },
      { key: 'contact_phone', label: 'SĐT NCC đang làm việc' },
      { key: 'supply_group', label: 'Nhóm SP/dịch vụ cung ứng', type: 'textarea', full: true },
      { key: 'quote_folder', label: 'Link báo giá' },
      { key: 'source_of_information', label: 'Nguồn thông tin đầu vào' },
    ],
  },
  {
    title: 'Đánh giá mặt hàng khảo sát',
    fields: [
      {
        key: 'production_tech',
        label: 'Công nghệ SX, đa dạng chủng loại',
        type: 'textarea',
        full: true,
      },
      { key: 'production_time', label: 'Thời gian SX' },
      { key: 'nvkd_eval', label: 'Đánh giá tư vấn NVKD' },
      { key: 'invoice_policy', label: 'Hóa đơn' },
      { key: 'reliability', label: 'Mức độ tin cậy', type: 'select', options: RELIABILITY_OPTIONS },
      { key: 'delivery_policy', label: 'Chính sách nhận hàng', type: 'textarea', full: true },
      {
        key: 'debt_policy',
        label: 'Chính sách công nợ',
        type: 'select',
        options: DEBT_POLICY_OPTIONS,
      },
      { key: 'defect_return', label: 'Hàng lỗi, hàng trả', type: 'textarea', full: true },
      { key: 'nspt_note', label: 'Nhận xét (NSPT)', type: 'textarea', full: true },
      // Bản v1 quên ô này ở popup trong khi bảng vẫn có cột -> sửa được ở bảng mà
      // mở popup lại không thấy. Đưa vào đây cho hai chỗ khớp nhau.
      { key: 'nspt_reason', label: 'Lý do (NSPT)', type: 'textarea', full: true },
    ],
  },
  {
    title: 'Ghi chú',
    fields: [{ key: 'note', label: 'Ghi chú', type: 'textarea', full: true }],
  },
  {
    title: 'Phê duyệt Trưởng phòng / Quản lý',
    fields: [
      { key: 'line_approve', label: 'Duyệt (TP/QL)', type: 'approve' },
      { key: 'line_approve_note', label: 'Yêu cầu (TP/QL)', type: 'textarea', full: true },
    ],
  },
]

export const SUPPLIER_COLUMNS: SurveyColumn[] = [
  { key: 'contact_date', label: 'Ngày LH', width: 110, type: 'date' },
  { key: 'reply_date', label: 'NCC phản hồi', width: 120, type: 'date' },
  { key: 'result_date', label: 'Ngày trả KQ', width: 120, type: 'date' },
  { key: 'supplier_available', label: 'NCC sẵn có', width: 90, type: 'check' },
  { key: 'supplier_code', label: 'NCC (viết tắt) *', width: 140, type: 'supplier' },
  { key: 'supplier_name', label: 'Tên pháp lý', width: 220 },
  { key: 'tax_code', label: 'MST', width: 110 },
  { key: 'reg_address', label: 'Địa chỉ ĐKKD', width: 200 },
  { key: 'warehouse_address', label: 'Địa chỉ kho', width: 200 },
  { key: 'google_maps', label: 'Google Maps', width: 160 },
  { key: 'contact_person', label: 'Người LH (NVKD)', width: 140 },
  { key: 'contact_phone', label: 'SĐT', width: 110 },
  { key: 'supply_group', label: 'Nhóm SP cung ứng', width: 160 },
  { key: 'quote_folder', label: 'Folder báo giá', width: 160 },
  { key: 'production_tech', label: 'Công nghệ SX', width: 150 },
  { key: 'production_time', label: 'Thời gian SX', width: 120 },
  { key: 'nvkd_eval', label: 'Đánh giá NVKD', width: 130 },
  { key: 'invoice_policy', label: 'Chính sách hóa đơn', width: 170 },
  {
    key: 'reliability',
    label: 'Mức tin cậy',
    width: 130,
    type: 'select',
    options: RELIABILITY_OPTIONS,
  },
  { key: 'delivery_policy', label: 'Chính sách giao nhận', width: 170 },
  {
    key: 'debt_policy',
    label: 'Chính sách công nợ',
    width: 160,
    type: 'select',
    options: DEBT_POLICY_OPTIONS,
  },
  { key: 'defect_return', label: 'Hàng lỗi/trả', width: 150 },
  { key: 'nspt_note', label: 'Nhận xét NSPT', width: 160 },
  { key: 'nspt_reason', label: 'Lý do', width: 160 },
  { key: 'note', label: 'Ghi chú', width: 160 },
  {
    key: 'line_approve',
    label: 'Duyệt (TP/QL)',
    width: 140,
    type: 'approve',
    options: SURVEY_APPROVE_OPTIONS,
  },
  { key: 'line_approve_note', label: 'Ghi chú duyệt', width: 180 },
]

/** Cột hiện ở chế độ RÚT GỌN — 9 trong 27 cột. Phần còn lại xem ở popup. */
export const SUPPLIER_CORE_KEYS = [
  'contact_date',
  'supplier_available',
  'supplier_code',
  'supplier_name',
  'contact_person',
  'contact_phone',
  'nspt_note',
  'note',
  'line_approve',
] as const

/* ============================ Bảng KHẢO SÁT SẢN PHẨM ========================== */

export const PRODUCT_SECTIONS: SurveySection[] = [
  {
    title: 'Lịch làm việc',
    fields: [
      { key: 'contact_date', label: 'Ngày liên hệ', type: 'date' },
      { key: 'reply_date', label: 'Ngày dự kiến phản hồi', type: 'date' },
      { key: 'result_date', label: 'Ngày dự kiến trả KQ', type: 'date' },
    ],
  },
  {
    title: 'Nhà cung cấp & Sản phẩm',
    fields: [
      { key: 'supplier_code', label: 'Tên viết tắt NCC', type: 'supplier' },
      { key: 'supplier_name', label: 'Tên pháp lý NCC', type: 'legal' },
      { key: 'internal_code', label: 'Mã SP (theo NCC)' },
      { key: 'product_name', label: 'Tên SP (tên NCC đặt)', full: true },
      { key: 'spec', label: 'Thông số kỹ thuật', type: 'textarea', full: true },
      { key: 'origin', label: 'Xuất xứ sản phẩm' },
    ],
  },
  {
    title: 'Báo giá & Quy đổi',
    fields: [
      { key: 'quote_unit', label: 'ĐVT', type: 'unit' },
      { key: 'moq', label: 'MOQ tối thiểu', type: 'num' },
      { key: 'price_by_volume', label: 'Giá theo sản lượng (VNĐ)', type: 'num' },
      { key: 'volume_range', label: 'Khung sản lượng (theo ĐVT)' },
      { key: 'vat', label: 'VAT (%)', type: 'vat' },
      // v1 chỉ có cột này ở bảng, popup không có -> mở popup ra là không thấy SL yêu cầu.
      { key: 'request_qty', label: 'SL yêu cầu', type: 'num' },
      { key: 'amount', label: 'Thành tiền (VNĐ)', type: 'computed' },
      { key: 'internal_unit', label: 'ĐVT (quy đổi về ĐVT Cty)', type: 'unit' },
      { key: 'amount_converted', label: 'Thành tiền (đã quy đổi)', type: 'num' },
      { key: 'shipping_cost', label: 'Chi phí vận chuyển (VNĐ)', type: 'num' },
      { key: 'delivery_time', label: 'Thời gian giao hàng' },
      { key: 'delivery_place', label: 'Địa điểm giao/nhận hàng' },
      { key: 'quote_file', label: 'Link báo giá' },
    ],
  },
  {
    title: 'Lấy mẫu & LAB',
    fields: [
      { key: 'sample_ready', label: 'Mẫu sẵn', type: 'check' },
      { key: 'sample_date', label: 'Ngày lấy mẫu', type: 'date' },
      { key: 'sample_qty', label: 'Số lượng mẫu nhận', type: 'num' },
      { key: 'lab_result', label: 'Đánh giá của LAB', type: 'lab' },
      { key: 'lab_note', label: 'Chi tiết đánh giá từ LAB', type: 'textarea', full: true },
    ],
  },
  {
    title: 'Ghi chú',
    fields: [{ key: 'note', label: 'Ghi chú', type: 'textarea', full: true }],
  },
  {
    title: 'Đánh giá & Phê duyệt',
    fields: [
      { key: 'nspt_note', label: 'NSPT Đánh giá', type: 'textarea', full: true },
      { key: 'nspt_reason', label: 'Lý do NSPT', type: 'textarea', full: true },
      { key: 'line_approve', label: 'Duyệt', type: 'approve' },
      { key: 'line_approve_note', label: 'Ý kiến TP/QL', type: 'textarea', full: true },
    ],
  },
]

export const PRODUCT_COLUMNS: SurveyColumn[] = [
  { key: 'supplier_available', label: 'NCC sẵn có', width: 90, type: 'check' },
  { key: 'supplier_code', label: 'NCC *', width: 140, type: 'supplier' },
  { key: 'supplier_name', label: 'Tên pháp lý', width: 220, type: 'legal' },
  { key: 'internal_code', label: 'Mã SP (NCC)', width: 120 },
  { key: 'product_name', label: 'Tên SP theo NCC *', width: 220 },
  { key: 'spec', label: 'Thông số KT', width: 180 },
  { key: 'origin', label: 'Xuất xứ', width: 100 },
  { key: 'quote_unit', label: 'ĐVT báo giá', width: 120, type: 'unit' },
  { key: 'moq', label: 'MOQ', width: 90, type: 'num' },
  { key: 'price_by_volume', label: 'Giá theo khung', width: 120, type: 'num' },
  { key: 'volume_range', label: 'Khung SL', width: 110 },
  { key: 'vat', label: 'VAT(%)', width: 90, type: 'vat' },
  { key: 'request_qty', label: 'SL YC', width: 90, type: 'num' },
  { key: 'amount', label: 'Thành tiền', width: 120, type: 'computed' },
  { key: 'internal_unit', label: 'ĐVT quy đổi', width: 120, type: 'unit' },
  { key: 'amount_converted', label: 'TT quy đổi', width: 120, type: 'num' },
  { key: 'shipping_cost', label: 'Phí VC', width: 100, type: 'num' },
  { key: 'delivery_time', label: 'TG giao', width: 110 },
  { key: 'delivery_place', label: 'Nơi giao nhận', width: 150 },
  { key: 'quote_file', label: 'File báo giá', width: 150 },
  { key: 'sample_ready', label: 'Mẫu sẵn', width: 80, type: 'check' },
  { key: 'sample_date', label: 'Ngày mẫu', width: 120, type: 'date' },
  { key: 'sample_qty', label: 'SL mẫu', width: 90, type: 'num' },
  { key: 'lab_note', label: 'Chi tiết ĐG LAB', width: 180 },
  { key: 'nspt_note', label: 'Nhận xét NSPT', width: 160 },
  { key: 'nspt_reason', label: 'Lý do NSPT', width: 160 },
  { key: 'note', label: 'Ghi chú', width: 160 },
  // CR-109: kết luận LAB đứng ngay TRƯỚC cột Duyệt — người duyệt quét bảng là
  // thấy mẫu đạt hay không, khỏi mở từng dòng ra xem (đúng chỗ khách khoanh trong
  // phiếu hỗ trợ TK20082601).
  {
    key: 'lab_result',
    label: 'Mẫu đạt/không đạt',
    width: 150,
    type: 'lab',
    options: SURVEY_LAB_OPTIONS,
  },
  {
    key: 'line_approve',
    label: 'Duyệt (TP/QL)',
    width: 140,
    type: 'approve',
    options: SURVEY_APPROVE_OPTIONS,
  },
  { key: 'line_approve_note', label: 'Ghi chú duyệt', width: 180 },
]

/** Cột hiện ở chế độ RÚT GỌN — 11 trong 30 cột. */
export const PRODUCT_CORE_KEYS = [
  'supplier_available',
  'supplier_code',
  'supplier_name',
  'internal_code',
  'product_name',
  'quote_unit',
  'moq',
  'price_by_volume',
  'note',
  // CR-109: kết luận LAB phải thấy được cả ở bảng rút gọn — đây là căn cứ duyệt.
  'lab_result',
  'line_approve',
] as const

export const SURVEY_TABLE_LABELS: Record<SurveyTable, string> = {
  supplier: 'Khảo sát nhà cung cấp',
  product: 'Khảo sát sản phẩm',
}

export function columnsOf(table: SurveyTable): SurveyColumn[] {
  return table === 'supplier' ? SUPPLIER_COLUMNS : PRODUCT_COLUMNS
}

export function sectionsOf(table: SurveyTable): SurveySection[] {
  return table === 'supplier' ? SUPPLIER_SECTIONS : PRODUCT_SECTIONS
}

export function coreKeysOf(table: SurveyTable): readonly string[] {
  return table === 'supplier' ? SUPPLIER_CORE_KEYS : PRODUCT_CORE_KEYS
}

/** Chỉ nháp và bị trả lại mới sửa được nội dung phiếu. */
export function isSurveyEditable(status: string): boolean {
  return status === 'draft' || status === 'rejected'
}

/** Xóa được: chưa gửi, đã bị trả lại, hoặc đã từ chối. */
export function isSurveyDeletable(status: string): boolean {
  return ['draft', 'rejected', 'cancelled'].includes(status)
}
