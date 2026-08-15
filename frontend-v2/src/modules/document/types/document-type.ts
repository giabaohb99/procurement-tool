/**
 * LOẠI VĂN BẢN — danh mục gốc của phân hệ Văn thư (`tab_doc_type`).
 *
 * Mỗi văn bản khi tạo chọn một loại ở đây. Loại quyết định: kiểu định danh, mức
 * mật mặc định, cấp số lúc nào, có phải duyệt / ký / kèm Quyết định ban hành
 * không, chu kỳ rà soát và thời hạn lưu trữ.
 *
 * ⚠️ **Không có trường `prefix`.** Tiền tố số hiệu chính là `code` — hai trường
 * luôn phải bằng nhau thì sớm muộn cũng lệch. Muốn hiện mẫu số hiệu thì gọi
 * `documentCodeSample()` bên dưới.
 */

/** 1 = mã tài liệu bất biến · 2 = số hiệu theo sổ. Khai theo từng loại. */
export type IdScheme = 1 | 2

export const ID_SCHEME_LABELS: Record<IdScheme, string> = {
  1: 'Mã tài liệu bất biến',
  2: 'Số hiệu theo sổ',
}

export const ID_SCHEME_HINTS: Record<IdScheme, string> = {
  1: 'Mã không đổi kể cả khi lên phiên bản 5. Dùng cho quy chế, quy trình, biểu mẫu — thứ sống lâu.',
  2: 'Đếm lại từ 1 mỗi năm, mỗi pháp nhân một sổ. Dùng cho công văn, thông báo, quyết định — việc sự vụ.',
}

/** Lúc nào thì chiếm số: 1 = ngay khi tạo nháp · 2 = khi được duyệt. */
export type NumberWhen = 1 | 2

export const NUMBER_WHEN_LABELS: Record<NumberWhen, string> = {
  1: 'Khi tạo bản nháp',
  2: 'Khi được duyệt',
}

/** Mức mật — thang cố định, khai trong mã chứ không phải danh mục sửa được. */
export type SecrecyLevel = 1 | 2 | 3 | 4

/** Nhóm A–F của danh mục 32 loại. Rỗng = chưa xếp nhóm. */
export const DOC_GROUP_LABELS: Record<string, string> = {
  A: 'A · Tài liệu hệ thống',
  B: 'B · Văn bản quản lý',
  C: 'C · Hợp đồng, cam kết',
  D: 'D · Văn bản sự vụ',
  E: 'E · Hồ sơ, biên bản',
  F: 'F · Khác',
}

export interface DocumentType {
  id: number
  /** Mã loại, chữ HOA không dấu — **đi thẳng vào số hiệu văn bản**. */
  code: string
  name: string
  group_code: string
  description: string

  id_scheme: IdScheme
  number_when: NumberWhen
  default_secrecy: SecrecyLevel
  is_confidential_type: boolean

  needs_approval: boolean
  needs_signature: boolean
  needs_decision: boolean
  /**
   * Phải có yêu cầu được duyệt mới soạn được.
   *
   * Bản 1 **luôn `false`** và không hiện trên form: đã bỏ bước xin phép, ai có
   * quyền tạo thì soạn thẳng. Giữ trường để bật lại sau không phải sửa bảng.
   */
  needs_request: boolean

  /** 0 = không rà định kỳ. */
  review_cycle_months: number
  retention_months: number
  /** Luồng duyệt mặc định — bộ máy duyệt chưa làm, luôn là 0. */
  default_flow_id: number

  sort_order: number
  is_active: boolean
}

/**
 * Các cờ bật/tắt hiện thành hàng chip trên bảng và trên form.
 *
 * Khai MỘT CHỖ cho cả bảng, form và bộ lọc — thêm cờ mới chỉ cần nối một dòng
 * vào đây và một trường vào `DocumentType`.
 */
export type DocumentTypeFlagKey =
  | 'needs_approval'
  | 'needs_signature'
  | 'needs_decision'
  | 'is_confidential_type'

export const DOCUMENT_TYPE_FLAGS: {
  key: DocumentTypeFlagKey
  label: string
  hint: string
}[] = [
  {
    key: 'needs_approval',
    label: 'Cần duyệt',
    hint: 'Phải qua duyệt trước khi có hiệu lực.',
  },
  {
    key: 'needs_signature',
    label: 'Cần ký số',
    hint: 'Phải ký trước khi phát hành.',
  },
  {
    key: 'needs_decision',
    label: 'Cần QĐ ban hành',
    hint: 'Ban hành phải kèm một Quyết định. Mỗi lần sửa lớn cần một Quyết định mới.',
  },
  {
    key: 'is_confidential_type',
    label: 'Bảo mật',
    hint: 'Cả loại là loại bảo mật — chỉ người đủ mức mật mới xem được.',
  },
]

/** Mọi cờ đều TẮT — dùng cho form thêm mới. */
export const EMPTY_DOCUMENT_TYPE_FLAGS = {
  needs_approval: false,
  needs_signature: false,
  needs_decision: false,
  is_confidential_type: false,
}

/**
 * Mẫu số hiệu để người khai hình dung, KHÔNG phải số thật.
 *
 * Số thật do backend cấp trong cùng giao dịch với việc ghi bản ghi (khóa dòng bộ
 * đếm) — xem `van-thu/04` mục 4.4. Ở đây chỉ dựng chuỗi minh họa.
 */
export function documentCodeSample(
  code: string,
  idScheme: IdScheme,
  year = new Date().getFullYear(),
): string {
  const safe = code || 'XX'
  return idScheme === 1 ? `DEGO-${safe}-012` : `08/${year}/${safe}-NS-DEGO`
}
