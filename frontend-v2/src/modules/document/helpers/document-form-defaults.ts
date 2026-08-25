import type { DocumentRecord } from '../types/document-record'
import type { DocumentRecordFormValues } from '../schemas/document-record-schema'

/** `2026-08-14` — đúng định dạng của `<input type="date">`. */
export function today(): string {
  return new Date().toISOString().slice(0, 10)
}

/**
 * Giá trị khởi tạo của form văn bản.
 *
 * Là HÀM chứ không phải hằng: `today()` phải tính lúc mở form, để sẵn một hằng
 * thì tab mở từ hôm qua chưa tải lại sẽ điền ngày hôm qua.
 *
 * `effective_date` để TRỐNG chứ không mặc định hôm nay: ngày hiệu lực là quyết
 * định nghiệp vụ (thường là đầu tháng sau), điền sẵn hôm nay thì người soạn dễ
 * bấm lưu luôn mà không để ý.
 */
/**
 * Vài ô suy được thẳng từ HỒ SƠ NGƯỜI ĐANG ĐĂNG NHẬP — xem `emptyDocumentForm`.
 *
 * Khai riêng một kiểu thay vì nhận cả `AuthUser`: helper này thuần, không cần
 * biết tới tầng xác thực, và chỗ gọi phải nói rõ nó đang mượn những ô nào.
 */
export interface DocumentFormSeed {
  company_id?: number
  department_id?: number
  employee_id?: number
}

export function emptyDocumentForm(seed: DocumentFormSeed = {}): DocumentRecordFormValues {
  return {
    doc_type_id: 0,
    //  TỰ ĐIỀN theo tài khoản đang đăng nhập (24/08/2026). Chín trên mười lần
    //  người soạn lập văn bản cho chính pháp nhân và phòng của mình, và chính
    //  họ là người chịu trách nhiệm nội dung — bắt chọn lại bốn ô đó mỗi lần là
    //  bắt gõ lại thứ hệ đã biết. Sửa được như thường, đây chỉ là giá trị mở sẵn.
    //
    //  ⚠️ Vẫn để 0 khi tài khoản chưa gắn hồ sơ nhân sự (tài khoản hệ thống):
    //  điền bừa một số 0 vào ô bắt buộc thì form báo lỗi ở một ô người dùng chưa
    //  hề đụng tới.
    company_id: seed.company_id || 0,
    //  0 = chưa chọn. Phòng chủ trì BẮT BUỘC (bước đầu luồng duyệt hỏi trưởng
    //  bộ phận của phòng này) nên nó đi cùng kiểu với các ô bắt buộc khác, chứ
    //  không còn `null` như ô tùy chọn.
    department_id: seed.department_id || 0,
    book_id: null,
    owner_employee_id: seed.employee_id || 0,
    //  Người SOẠN mặc định là người đang gõ — khác «người chịu trách nhiệm nội
    //  dung» ở chỗ ai hỏi thì trả lời, nhưng lúc lập mới thì thường là một người.
    drafter_employee_id: seed.employee_id || null,
    signer_employee_id: null,
    title: '',
    summary: '',
    keywords: '',
    //  2 Nội bộ — mức mặc định của mọi người khi chưa cấp mức nào khác. Chọn
    //  loại văn bản xong thì form kéo theo `default_secrecy` của loại đó.
    secrecy_level: 2,
    urgency: 1,
    effective_date: '',
    expire_date: '',
    attachment_view_until: '',
    legacy_code: '',
    storage_location: '',
    //  Khối nghỉ phép mở sẵn ở giá trị trung tính. Nó chỉ HIỆN khi loại văn bản
    //  là Giấy nghỉ phép; loại khác thì `formToPayload` không gửi nó lên.
    leave: {
      employee_id: 0,
      leave_type: 'annual',
      from_date: '',
      from_session: 'full',
      to_date: '',
      to_session: 'full',
      total_days: '',
      reason: '',
      handover_employee_id: 0,
      contact_phone: '',
    },
  }
}

/** Bản ghi từ API → giá trị form. Ngày `null` về chuỗi rỗng cho ô nhập ngày. */
export function documentToForm(record: DocumentRecord): DocumentRecordFormValues {
  return {
    doc_type_id: record.doc_type_id,
    company_id: record.company_id,
    //  Văn bản cũ lập trước ngày phòng chủ trì thành bắt buộc có thể còn rỗng —
    //  đưa về 0 để ô select hiện "chưa chọn" và bắt người sửa chọn một phòng.
    department_id: record.department_id ?? 0,
    book_id: record.book_id,
    owner_employee_id: record.owner_employee_id,
    drafter_employee_id: record.drafter_employee_id,
    signer_employee_id: record.signer_employee_id,
    title: record.title,
    summary: record.summary ?? '',
    keywords: record.keywords ?? '',
    secrecy_level: record.secrecy_level,
    urgency: record.urgency,
    effective_date: record.effective_date ?? '',
    expire_date: record.expire_date ?? '',
    attachment_view_until: record.attachment_view_until ?? '',
    legacy_code: record.legacy_code ?? '',
    storage_location: record.storage_location ?? '',
    //  Đọc ngược từ `metadata` để mở lại đơn nghỉ phép là thấy nguyên số liệu cũ.
    leave: {
      employee_id: Number(record.metadata?.employee_id ?? 0),
      leave_type: String(record.metadata?.leave_type ?? 'annual'),
      from_date: String(record.metadata?.from_date ?? ''),
      from_session: String(record.metadata?.from_session ?? 'full'),
      to_date: String(record.metadata?.to_date ?? ''),
      to_session: String(record.metadata?.to_session ?? 'full'),
      total_days: record.metadata?.total_days === undefined
        ? ''
        : Number(record.metadata.total_days),
      reason: String(record.metadata?.reason ?? ''),
      handover_employee_id: Number(record.metadata?.handover_employee_id ?? 0),
      contact_phone: String(record.metadata?.contact_phone ?? ''),
    },
  }
}

/** Giá trị form → payload API. Ngày rỗng phải gửi `null`, không phải `""`.
 *
 * `laNghiPhep` quyết định có gửi khối nghỉ phép hay không. Gửi kèm cho loại khác
 * cũng vô hại (backend loại bỏ metadata của loại chưa khai hình dạng), nhưng gửi
 * một cục dữ liệu rỗng lên mỗi lần lưu công văn thì đọc log ra không hiểu gì.
 */
export function formToPayload(values: DocumentRecordFormValues, laNghiPhep = false) {
  const { leave, ...chung } = values
  return {
    ...chung,
    effective_date: values.effective_date || null,
    expire_date: values.expire_date || null,
    attachment_view_until: values.attachment_view_until || null,
    metadata: laNghiPhep && leave
      ? { ...leave, total_days: leave.total_days === '' ? undefined : leave.total_days }
      : undefined,
  }
}
