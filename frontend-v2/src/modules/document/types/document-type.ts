/**
 * Loại văn bản — danh mục nền của phân hệ Văn bản: mỗi văn bản khi tạo sẽ chọn
 * một loại, và số hiệu văn bản sinh theo `prefix` của loại đó.
 *
 * ⚠️ TẠM THỜI CHƯA CÓ BACKEND. Dữ liệu sống trong kho tạm phía trình duyệt (xem
 * `store/document-type-store.ts`). Kiểu dữ liệu dưới đây giữ tên trường theo lối
 * đặt của backend (`snake_case`, `is_*`, `has_*`) để lúc nối API không phải sửa
 * bảng và form.
 */
export interface DocumentType {
  id: number
  /** Mã loại, viết HOA không dấu — vd `CV`, `QD`. */
  code: string
  name: string
  /** Tiền tố số hiệu văn bản — vd `CV` → `CV-2026-001`. */
  prefix: string
  description: string
  is_active: boolean

  // ===== Tùy chọn khác — quyết định luồng làm việc của văn bản thuộc loại này =====
  /** Loại này soạn theo BIỂU MẪU dựng sẵn, không gõ tự do. */
  has_template: boolean
  /** Quản lý phiên bản: sửa nội dung thì ra bản mới, bản cũ vẫn tra lại được. */
  has_version: boolean
  /** Phải qua duyệt trước khi có hiệu lực. */
  needs_approval: boolean
  /** Phải kèm quyết định ban hành (thường đi với quy trình / quy chế). */
  needs_issue_decision: boolean
  /** Phải ký số trước khi phát hành. */
  needs_signature: boolean
  /** Chỉ người được cấp quyền mới xem được nội dung. */
  is_confidential: boolean
}

/** Các trường bật/tắt gom vào khối "Tùy chọn khác" của form. */
export type DocumentTypeOptionKey =
  | 'has_template'
  | 'has_version'
  | 'needs_approval'
  | 'needs_issue_decision'
  | 'needs_signature'
  | 'is_confidential'

/**
 * Khai báo MỘT CHỖ cho cả form, bảng và bộ lọc — thêm tùy chọn mới chỉ cần nối
 * một dòng vào đây (và một trường vào `DocumentType`).
 */
export const DOCUMENT_TYPE_OPTIONS: {
  key: DocumentTypeOptionKey
  label: string
  hint: string
}[] = [
  { key: 'has_template', label: 'Có mẫu', hint: 'Soạn theo biểu mẫu dựng sẵn.' },
  {
    key: 'has_version',
    label: 'Có phiên bản',
    hint: 'Sửa nội dung sẽ tạo bản mới, bản cũ vẫn tra lại được.',
  },
  { key: 'needs_approval', label: 'Cần duyệt', hint: 'Phải duyệt trước khi có hiệu lực.' },
  {
    key: 'needs_issue_decision',
    label: 'Cần QĐ ban hành',
    hint: 'Phải kèm quyết định ban hành.',
  },
  { key: 'needs_signature', label: 'Cần ký số', hint: 'Phải ký số trước khi phát hành.' },
  {
    key: 'is_confidential',
    label: 'Bảo mật',
    hint: 'Chỉ người được cấp quyền mới xem được nội dung.',
  },
]

/** Mọi tùy chọn đều TẮT — dùng cho form thêm mới. */
export const EMPTY_DOCUMENT_TYPE_OPTIONS = {
  has_template: false,
  has_version: false,
  needs_approval: false,
  needs_issue_decision: false,
  needs_signature: false,
  is_confidential: false,
}

/** Vài loại văn bản hành chính phổ biến, dùng làm dữ liệu khởi tạo của trang. */
export const DEFAULT_DOCUMENT_TYPES: DocumentType[] = [
  {
    id: 1,
    code: 'CV',
    name: 'Công văn',
    prefix: 'CV',
    description: 'Công văn trao đổi, đề nghị giữa các đơn vị.',
    is_active: true,
    ...EMPTY_DOCUMENT_TYPE_OPTIONS,
    has_template: true,
    needs_approval: true,
  },
  {
    id: 2,
    code: 'QD',
    name: 'Quyết định',
    prefix: 'QD',
    description: 'Quyết định bổ nhiệm, điều động, khen thưởng, kỷ luật.',
    is_active: true,
    ...EMPTY_DOCUMENT_TYPE_OPTIONS,
    has_template: true,
    needs_approval: true,
    needs_signature: true,
  },
  {
    id: 3,
    code: 'TB',
    name: 'Thông báo',
    prefix: 'TB',
    description: 'Thông báo nội bộ gửi toàn công ty hoặc từng bộ phận.',
    is_active: true,
    ...EMPTY_DOCUMENT_TYPE_OPTIONS,
    has_template: true,
  },
  {
    id: 4,
    code: 'QC',
    name: 'Quy chế / Quy trình',
    prefix: 'QC',
    description: 'Quy chế, quy trình nội bộ ban hành kèm quyết định.',
    is_active: true,
    ...EMPTY_DOCUMENT_TYPE_OPTIONS,
    has_template: true,
    has_version: true,
    needs_approval: true,
    needs_issue_decision: true,
  },
  {
    id: 5,
    code: 'HD',
    name: 'Hợp đồng',
    prefix: 'HD',
    description: 'Hợp đồng kinh tế, hợp đồng nguyên tắc với đối tác.',
    is_active: true,
    ...EMPTY_DOCUMENT_TYPE_OPTIONS,
    has_template: true,
    has_version: true,
    needs_approval: true,
    needs_signature: true,
    is_confidential: true,
  },
  {
    id: 6,
    code: 'BM',
    name: 'Biểu mẫu',
    prefix: 'BM',
    description: 'Biểu mẫu, phiếu in dùng chung trong nội bộ.',
    is_active: false,
    ...EMPTY_DOCUMENT_TYPE_OPTIONS,
    has_template: true,
    has_version: true,
  },
]
