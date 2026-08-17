/**
 * VĂN BẢN — bản ghi chính của phân hệ Văn thư.
 *
 * Trục của bản ghi là **loại văn bản × pháp nhân ban hành × phiên bản**. Nội
 * dung KHÔNG nằm ở đây mà ở phiên bản (`DocumentVersion`); `current_version_id`
 * trỏ tới bản đang có hiệu lực.
 *
 * ⚠️ Đừng nhầm `status` của văn bản với `status` của phiên bản. Quy chế lên bản
 * 2.0 thì văn bản VẪN "Có hiệu lực", chỉ dòng phiên bản 1.0 chuyển sang "Đã
 * thay thế". Nhầm chỗ này là cả công ty thấy quy chế biến mất.
 *
 * Số hiệu do BACKEND cấp trong cùng giao dịch ghi bản ghi. Client chỉ **xem
 * trước** qua `/api/documents/number-preview` và không có đường nào tự dựng số —
 * hai người bấm cùng lúc mà client tự đánh số là ra hai văn bản trùng số.
 */

/** Vòng đời văn bản (`van-thu` J01). Số, không phải chuỗi — khớp `tab_document.status`. */
export const DOCUMENT_STATUS = {
  draft: 1,
  submitted: 2,
  approved: 3,
  effective: 4,
  replaced: 5,
  expired: 6,
  revoked: 7,
  archived: 8,
} as const

export const STATUS_LABELS: Record<number, string> = {
  1: 'Nháp',
  2: 'Đang duyệt',
  3: 'Đã duyệt',
  4: 'Có hiệu lực',
  5: 'Đã thay thế',
  6: 'Hết hiệu lực',
  7: 'Bãi bỏ',
  8: 'Lưu trữ',
}

export const STATUS_VARIANTS: Record<number, 'default' | 'secondary' | 'outline' | 'destructive'> =
  {
    1: 'outline',
    2: 'secondary',
    3: 'secondary',
    4: 'default',
    5: 'secondary',
    6: 'secondary',
    7: 'destructive',
    8: 'outline',
  }

/** Trạng thái của PHIÊN BẢN — thang riêng, xem chú thích đầu tệp. */
export const VERSION_STATUS_LABELS: Record<number, string> = {
  1: 'Nháp',
  2: 'Đang duyệt',
  3: 'Đã duyệt',
  4: 'Đã thay thế',
}

export const CHANGE_KIND = { major: 1, minor: 2 } as const

export const CHANGE_KIND_LABELS: Record<number, string> = {
  1: 'Sửa lớn',
  2: 'Sửa nhỏ',
}

export interface DocumentRecord {
  id: number
  /** 1 nội bộ · 2 văn bản pháp luật ngoài · 3 văn bản đến. Màn hình chỉ thấy 1. */
  origin: number

  /** `DEGO-QC-012` — mã tài liệu bất biến (loại `id_scheme = 1`). */
  doc_code: string | null
  /** `08/2026/TB-NS-DEGO` — số hiệu theo sổ (loại `id_scheme = 2`). */
  issue_number: string
  /** Mã bất biến nếu có, không thì số theo sổ — dùng cho cột "Số hiệu". */
  display_code: string
  seq_no: number | null
  issue_year: number | null
  /** Quy tắc đã cấp số có cho phép văn thư chỉnh số và ghi lý do hay không. */
  allow_manual_number: boolean
  /** Số hiệu của bản GIẤY trước khi lên hệ thống; tìm kiếm chấp nhận số này. */
  legacy_code: string

  doc_type_id: number
  doc_type_name: string
  doc_type_code: string
  /** Pháp nhân BAN HÀNH — không phải pháp nhân của người ngồi nhập. */
  company_id: number
  company_name: string
  /** Phòng chủ trì. */
  department_id: number | null
  department_name: string

  /** Người chịu trách nhiệm NỘI DUNG — người trả lời khi có ai hỏi về văn bản này. */
  owner_employee_id: number
  owner_name: string
  /** Người ngồi gõ. */
  drafter_employee_id: number | null
  drafter_name: string
  signer_employee_id: number | null
  signer_name: string

  title: string
  summary: string
  /** Từ khóa tra cứu, ngăn bằng dấu phẩy. */
  keywords: string

  /** 1 Công khai · 2 Nội bộ · 3 Mật · 4 Tuyệt mật. */
  secrecy_level: number
  /** 1 thường · 2 khẩn · 3 hỏa tốc. Độc lập hoàn toàn với mức mật. */
  urgency: number

  status: number
  status_label: string
  effective_date: string | null
  expire_date: string | null

  /**
   * SỔ VĂN BẢN chứa văn bản này (có thể trống).
   *
   * Vào sổ mang lại hai thứ: một **số thứ tự trong sổ** (`book_seq_no`, khác số
   * hiệu đi ra ngoài) và **quyền theo sổ** — thành viên sổ đọc được, người quản
   * lý sổ sửa được, khỏi phải chia tay từng văn bản.
   */
  book_id: number | null
  book_name: string
  book_seq_no: number | null
  book_year: number | null
  /** `CVĐ 08/2026` — số vào sổ để hiển thị. */
  book_number_display: string

  current_version_id: number | null
  /** `2.0` — của bản đang dùng. */
  version_no: string
  version_count: number
  attachment_count: number
  /**
   * CẦN RÀ LẠI — bật khi văn bản CHA đổi: lên phiên bản mới hoặc bị bãi bỏ (E11).
   * Hệ thống chỉ đánh dấu, không tự sửa nội dung con.
   */
  needs_review: boolean
  needs_review_note: string
  created_at: string
}

export interface DocumentVersion {
  id: number
  document_id: number
  /** `2.0` — chuỗi để hiển thị; sắp xếp thì dùng `major`/`minor`. */
  version_no: string
  major: number
  minor: number
  status: number
  status_label: string
  /** Đã duyệt thì khóa, một chiều — sửa = mở phiên bản mới. */
  is_locked: boolean
  change_kind: number
  change_summary: string
  change_reason: string
  requires_reconfirm: boolean
  /** Ngày hiệu lực RIÊNG của phiên bản, khác ngày được duyệt. */
  effective_from: string | null
  content_sha256: string
  prev_version_id: number | null
  approved_at: string
  approved_by_name: string
  /** Ai đang giữ bản nháp — dùng cho câu báo khi người thứ hai bấm mở bản mới. */
  created_by_name: string
  created_at: string
  /** Bản văn bản đang dùng. Bản cũ hiện băng cảnh báo "đã bị thay thế". */
  is_current: boolean
  /** Chỉ có khi đọc MỘT phiên bản; danh sách không kèm nội dung. */
  content_html?: string
}

/** Một dòng gợi ý "đã có văn bản cùng loại cùng phòng" (B05). */
export interface DocumentSuggestion {
  id: number
  display_code: string
  title: string
  effective_date: string
}

export interface NumberPreview {
  preview: string
  /** 1 cấp lúc tạo nháp · 2 cấp lúc được duyệt. */
  number_when: number
  /** 1 mã tài liệu bất biến · 2 số hiệu theo sổ. */
  id_scheme: number
}

/** Tôi được làm gì trên ĐÚNG văn bản này — chỉ để ẩn nút, không phải bảo mật. */
export interface DocumentPermissions {
  read: boolean
  write: boolean
  delete: boolean
}
