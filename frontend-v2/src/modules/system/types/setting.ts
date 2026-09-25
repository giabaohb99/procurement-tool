/** Nhóm cấu hình do backend gán cho từng trường (`service.py` phía backend). */
export type SettingGroup =
  | 'workflow'
  | 'document'
  | 'email'
  | 'storage'
  | 'ai'
  | 'sync'
  | 'pos365'
  | 'system'

/** Kiểu ô nhập — quyết định trang vẽ công tắc, ô số, ô chọn hay ô chữ. */
export type SettingType = 'bool' | 'int' | 'str' | 'select'

/** Một lựa chọn của ô `select`. Backend khai kèm trường, frontend không tự đoán. */
export interface SettingOption {
  value: string
  label: string
}

/**
 * Một trường cấu hình THƯỜNG: đọc được, sửa được, hiển thị lại được.
 *
 * `value` để `unknown` vì backend trả về theo `type`: chuỗi cho `str`, số cho
 * `int`, luận lý cho `bool`. Trang đọc qua `SettingField` chứ không ép kiểu bừa.
 */
export interface SettingField {
  key: string
  group: SettingGroup
  label: string
  type: SettingType
  value: unknown
  /** Diễn giải dài cho công tắc đổi quy trình — hiện ngay dưới ô. */
  hint?: string
  /** Chỉ có ở `type: 'select'`. */
  options?: SettingOption[]
  /**
   * Đường dẫn TỚI CHỖ LẤY giá trị này (trang cấp khóa API, trang danh sách
   * model). Mở tab mới, không phải trang trong hệ thống.
   */
  doc_url?: string
}

/**
 * Một khóa BÍ MẬT (mật khẩu SMTP, khóa R2).
 *
 * Cố ý KHÔNG có trường `value`: backend chỉ trả `configured` để nói "đã đặt hay
 * chưa". Giá trị thật được mã hóa trong DB và không bao giờ đi ngược ra ngoài —
 * đừng thêm `value` vào đây.
 */
export interface SettingSecret {
  key: string
  group: SettingGroup
  label: string
  configured: boolean
  hint?: string
  /** Trang đăng ký lấy khóa — thứ người dùng cần nhất khi lần đầu vào ô này. */
  doc_url?: string
}

export interface SettingPayload {
  fields: SettingField[]
  secrets: SettingSecret[]
}

/** Kết quả của hai nút thử kết nối (email / lưu trữ). */
export interface SettingTestResult {
  ok: boolean
  message: string
}

/** Hai đường nạp chỉ mục tài liệu: bù phần thiếu, hoặc dựng lại toàn bộ. */
export type RagReindexMode = 'missing' | 'all'

/**
 * Số liệu đối chiếu DB với kho vector của Trợ lý AI.
 *
 * `enabled: false` nghĩa là `AI_RAG_ENABLED` đang tắt — lúc đó backend KHÔNG gửi các
 * con số, nên mọi trường đếm đều là tùy chọn, đừng đọc thẳng mà không hỏi `enabled`.
 * `orphans` = đoạn còn trong kho mà bản ghi dưới DB đã bị xóa.
 */
export interface RagIndexStatus {
  enabled: boolean
  help_total?: number
  faq_total?: number
  help_indexed?: number
  faq_indexed?: number
  missing?: number
  missing_help?: number
  missing_faq?: number
  orphans?: number
}
