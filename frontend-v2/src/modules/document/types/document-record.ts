/**
 * VĂN BẢN — bản ghi chính của phân hệ.
 *
 * Ba luồng dùng chung một bảng, phân biệt bằng `direction`:
 *  - `incoming` (đến): nơi gửi = đối tác, có ngày đến và số đến.
 *  - `outgoing` (đi): nơi nhận = đối tác, có số đi.
 *  - `internal` (nội bộ): không có đối tác ngoài.
 *
 * Số hiệu (`code`) và số vào sổ (`book_no`) do hệ TỰ SINH lúc tạo — xem
 * `helpers/document-number.ts`.
 */
export type DocumentDirection = 'incoming' | 'outgoing' | 'internal'

export const DIRECTION_LABELS: Record<DocumentDirection, string> = {
  incoming: 'Văn bản đến',
  outgoing: 'Văn bản đi',
  internal: 'Văn bản nội bộ',
}

/** Sổ tương ứng với từng luồng — hiện trên màn "Sổ văn bản". */
export const BOOK_LABELS: Record<DocumentDirection, string> = {
  incoming: 'Sổ văn bản đến',
  outgoing: 'Sổ văn bản đi',
  internal: 'Sổ văn bản nội bộ',
}

/**
 * Hiệu lực do người dùng đặt. Riêng "hết hiệu lực theo ngày" thì KHÔNG lưu
 * thành trạng thái mà tính lúc hiển thị (xem `helpers/document-status.ts`) — để
 * lưu thì mỗi sáng phải có ai đó chạy tay cập nhật cả bảng.
 */
export type DocumentStatus = 'draft' | 'effective' | 'replaced' | 'revoked'

export const STATUS_LABELS: Record<DocumentStatus, string> = {
  draft: 'Dự thảo',
  effective: 'Còn hiệu lực',
  replaced: 'Đã thay thế',
  revoked: 'Thu hồi',
}

/**
 * TÌNH TRẠNG XỬ LÝ — văn bản này đang nằm ở đâu trong quy trình.
 *
 * Khác hẳn `DocumentStatus` (hiệu lực pháp lý của nội dung): một quyết định có
 * thể "Còn hiệu lực" mà vẫn "Đang xử lý" ở khâu phát hành, và ngược lại.
 */
export type ProcessingStatus = 'pending' | 'processing' | 'done' | 'on_hold'

export const PROCESSING_STATUS_LABELS: Record<ProcessingStatus, string> = {
  pending: 'Chưa xử lý',
  processing: 'Đang xử lý',
  done: 'Đã xử lý',
  on_hold: 'Tạm dừng',
}

/**
 * Ba mức bày ra lúc TẠO MỚI. "Tạm dừng" không có ở đây: văn bản vừa lập không
 * thể đang tạm dừng, mức đó chỉ đặt về sau ở trang chi tiết.
 */
export const NEW_DOCUMENT_PROCESSING_STATUSES = [
  'pending',
  'processing',
  'done',
] as const satisfies readonly ProcessingStatus[]

/** Biến thể `<Badge>` cho từng tình trạng — xanh khi xong, xám khi còn treo. */
export const PROCESSING_STATUS_VARIANTS: Record<
  ProcessingStatus,
  'default' | 'secondary' | 'outline' | 'destructive'
> = {
  pending: 'outline',
  processing: 'default',
  done: 'secondary',
  on_hold: 'destructive',
}

/**
 * HÌNH THỨC văn bản — bản đang cầm trên tay là bản gì.
 *
 * Khác hẳn "Loại văn bản" (công văn, quyết định, tờ trình…): một quyết định có
 * thể lưu bằng bản chính, bản sao y hay bản điện tử, hỏi chung một ô thì mất
 * một trong hai thông tin.
 */
export type DocumentFormat = 'original' | 'certified_copy' | 'electronic' | 'fax'

export const DOCUMENT_FORMAT_LABELS: Record<DocumentFormat, string> = {
  original: 'Bản chính',
  certified_copy: 'Bản sao y',
  electronic: 'Bản điện tử',
  fax: 'Bản fax',
}

export interface DocumentAttachment {
  /** Sinh lúc đính kèm, không trùng giữa các file. */
  id: string
  name: string
  /** Byte — chỉ để hiện "1,2 MB". */
  size: number
  at: string
}

export interface DocumentRecord {
  id: number
  /**
   * Số hiệu văn bản, vd `CV-2026-001`.
   *
   * Người vào sổ được gõ số riêng (nhiều đơn vị đã có cách đánh số của họ); bỏ
   * trống thì hệ ghép từ tiền tố loại văn bản + số vào sổ.
   */
  code: string
  /** Số thứ tự trong sổ đi/đến của năm. */
  book_no: number
  book_year: number
  direction: DocumentDirection

  document_type_id: number
  /** Mức mật + mức khẩn (mỗi thang một mức) — xem `types/security-level.ts`. */
  confidential_level_id: number | null
  urgent_level_id: number | null
  /** Nơi gửi (đến) / nơi nhận (đi); văn bản nội bộ để trống. */
  partner_id: number | null
  /**
   * NƠI NHẬN — lưu thẳng TÊN chứ không phải id đối tác.
   *
   * Một văn bản đi thường gửi nhiều nơi, trong đó có những nơi chỉ nhận đúng
   * một lần (một cá nhân, một đoàn công tác) — bắt khai vào danh bạ trước mới
   * chọn được thì danh bạ ngập rác. Nơi nào có sẵn trong danh bạ thì bấm
   * "Nhập từ danh bạ" để lấy đúng tên, khỏi gõ sai.
   */
  recipients: string[]
  /** Hình thức tồn tại của bản đang lưu — xem `DocumentFormat`. */
  doc_format: DocumentFormat
  /** Cần theo dõi gấp — hai cờ ĐỘC LẬP, một văn bản có thể vừa quan trọng vừa khẩn. */
  is_important: boolean
  is_urgent: boolean

  title: string
  summary: string
  signer: string
  /** Trưởng phòng duyệt trước khi phát hành; trống = theo mặc định của đơn vị. */
  approver: string
  /** Phòng ban soạn ra văn bản này. */
  drafting_department: string
  /** Ngày ký / ban hành. */
  issued_date: string
  /** Ngày phát hành đi. */
  sent_date: string
  /** Hạn mà NỘI DUNG văn bản yêu cầu nơi nhận phải hoàn thành. */
  required_due_date: string
  /** Ngày nhận — chỉ văn bản đến. */
  received_date: string
  effective_from: string
  /** Trống = không đặt hạn. */
  effective_to: string
  status: DocumentStatus

  /** Khâu xử lý hiện tại — xem `ProcessingStatus`. */
  processing_status: ProcessingStatus
  /** Người đang cầm việc; để trống nghĩa là chưa giao cho ai. */
  handler: string
  /** Người cần biết / phối hợp, không phải người cầm việc. */
  related_person: string
  /** Người nhận báo cáo kết quả sau khi xử lý xong. */
  report_receiver: string
  /** Hạn phải xử lý xong; trống = không đặt hạn. */
  due_date: string
  /** Kết quả sau khi xử lý xong: đã trả lời bằng công văn nào, chốt ra sao. */
  result: string
  /** Ghi chú của khâu xử lý: đã chuyển ai, vướng ở đâu. */
  processing_note: string
  /** Chỗ cất bản giấy, vd "Tủ A2 — kệ 3". */
  storage_location: string

  /**
   * Nội dung soạn thảo, lưu dạng HTML do trình soạn thảo sinh ra.
   *
   * Tách hẳn khỏi `summary` (trích yếu dài / ghi chú, chỉ là chữ trơn): đây là
   * THÂN văn bản, có tiêu đề, bảng biểu, canh lề — thứ trước kia phải soạn ở
   * Word rồi tải tệp lên.
   */
  content: string

  attachments: DocumentAttachment[]
  /** Giá trị của trường thông tin động, tra theo `DynamicField.code`. */
  field_values: Record<string, string>
}

export type DocumentRecordInput = Omit<DocumentRecord, 'id'>
