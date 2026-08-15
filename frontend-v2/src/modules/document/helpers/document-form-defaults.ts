import type { DocumentRecordFormValues } from '../schemas/document-record-schema'

/** `2026-08-13` — đúng định dạng của `<input type="date">`. */
export function today(): string {
  return new Date().toISOString().slice(0, 10)
}

/**
 * Giá trị khởi tạo của form văn bản.
 *
 * Là HÀM chứ không phải hằng: `today()` phải tính lúc mở form, để sẵn một hằng
 * thì tab mở từ hôm qua chưa tải lại sẽ điền ngày hôm qua.
 */
export function emptyDocumentForm(): DocumentRecordFormValues {
  return {
    code: '',
    direction: 'incoming',
    document_type_id: 0,
    doc_format: 'original',
    confidential_level_id: null,
    urgent_level_id: null,
    partner_id: null,
    recipients: [],
    is_important: false,
    is_urgent: false,
    title: '',
    summary: '',
    signer: '',
    approver: '',
    drafting_department: '',
    issued_date: today(),
    sent_date: today(),
    received_date: today(),
    required_due_date: '',
    effective_from: '',
    effective_to: '',
    status: 'draft',
    processing_status: 'pending',
    handler: '',
    related_person: '',
    report_receiver: '',
    due_date: '',
    result: '',
    processing_note: '',
    storage_location: '',
    field_values: {},
  }
}
