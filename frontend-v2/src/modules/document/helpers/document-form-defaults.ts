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
export function emptyDocumentForm(): DocumentRecordFormValues {
  return {
    doc_type_id: 0,
    company_id: 0,
    department_id: null,
    book_id: null,
    owner_employee_id: 0,
    drafter_employee_id: null,
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
    legacy_code: '',
  }
}

/** Bản ghi từ API → giá trị form. Ngày `null` về chuỗi rỗng cho ô nhập ngày. */
export function documentToForm(record: DocumentRecord): DocumentRecordFormValues {
  return {
    doc_type_id: record.doc_type_id,
    company_id: record.company_id,
    department_id: record.department_id,
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
    legacy_code: record.legacy_code ?? '',
  }
}

/** Giá trị form → payload API. Ngày rỗng phải gửi `null`, không phải `""`. */
export function formToPayload(values: DocumentRecordFormValues) {
  return {
    ...values,
    effective_date: values.effective_date || null,
    expire_date: values.expire_date || null,
  }
}
