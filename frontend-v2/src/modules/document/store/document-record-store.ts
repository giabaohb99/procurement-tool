import type { DocumentRecord } from '../types/document-record'
import { createLocalCollection } from './local-collection'

/**
 * Một văn bản MẪU để mở màn hình lên là thấy ngay sổ, bảng danh sách và trang
 * chi tiết trông ra sao — chứ không phải bảng trắng.
 *
 * Chọn công văn đi vì đó là luồng khai đủ nhất: có nơi nhận, có người duyệt,
 * có hạn xử lý. Các id danh mục (loại, mức mật/khẩn, đối tác) trỏ đúng dữ liệu
 * khởi tạo trong `types/document-type.ts`, `types/security-level.ts`,
 * `types/document-partner.ts` — đổi mấy chỗ đó thì sửa cả ở đây.
 */
const SAMPLE_DOCUMENTS: DocumentRecord[] = [
  {
    id: 1,
    code: 'CV-2026-001',
    book_no: 1,
    book_year: 2026,
    direction: 'outgoing',

    document_type_id: 1, // Công văn
    doc_format: 'original',
    confidential_level_id: 1, // Thường
    urgent_level_id: 6, // Khẩn
    partner_id: 1, // Sở Kế hoạch và Đầu tư
    recipients: ['Sở Kế hoạch và Đầu tư', 'Cục Thuế TP.HCM'],
    is_important: true,
    is_urgent: false,

    title: 'Công văn giải trình số liệu quyết toán thuế năm 2025',
    summary:
      'Giải trình chênh lệch giữa số liệu quyết toán thuế năm 2025 của công ty và số liệu cơ quan thuế đang ghi nhận, kèm bảng đối chiếu chi tiết theo từng quý.',
    signer: 'Nguyễn Văn An',
    approver: 'Trần Thị Bình',
    drafting_department: 'Phòng Kế toán',

    issued_date: '2026-08-10',
    sent_date: '2026-08-11',
    received_date: '',
    required_due_date: '2026-08-25',
    effective_from: '2026-08-10',
    effective_to: '',
    status: 'effective',

    processing_status: 'processing',
    handler: 'Lê Văn Cường',
    related_person: 'Phạm Thị Dung',
    report_receiver: 'Nguyễn Văn An',
    due_date: '2026-08-20',
    result: '',
    processing_note: 'Đã gửi bản giấy qua bưu điện ngày 11/8, đang chờ phản hồi.',
    storage_location: 'Tủ A2 — kệ 3',

    content: [
      '<p><strong>CÔNG TY CP DEGO HOLDING</strong></p>',
      '<p>Kính gửi: Cục Thuế TP.HCM</p>',
      '<p>Căn cứ Biên bản làm việc ngày 05/8/2026, Công ty xin giải trình chênh lệch số liệu quyết toán thuế năm 2025 như sau:</p>',
      '<p>1. Chênh lệch doanh thu quý III phát sinh do hóa đơn điều chỉnh giảm số 0001234 lập ngày 12/10/2025.</p>',
      '<p>2. Chi phí lãi vay đã loại trừ phần vượt mức khống chế theo quy định.</p>',
      '<p>Trân trọng./.</p>',
    ].join(''),

    attachments: [],
  },
]

/**
 * Kho tạm của VĂN BẢN (đến / đi / nội bộ).
 *
 * ⚠️ Khóa lưu có đuôi `.v2`: bản ghi lưu trước đợt dựng lại form theo mẫu mới
 * còn thiếu hẳn các trường `recipients`, `doc_format`, `is_important`… — đọc
 * lên là form vỡ. Đổi khóa để máy nào đã có dữ liệu cũ cũng bắt đầu lại sạch
 * (dữ liệu cũ vẫn nằm ở khóa `erp.document-records`, chỉ là không dùng nữa).
 */
export const documentRecordCollection = createLocalCollection<DocumentRecord>({
  storageKey: 'erp.document-records.v2',
  seed: SAMPLE_DOCUMENTS,
  labels: {
    code: 'số văn bản',
    direction: 'sổ',
    document_type_id: 'loại văn bản',
    doc_format: 'hình thức văn bản',
    confidential_level_id: 'độ mật',
    urgent_level_id: 'độ khẩn',
    partner_id: 'đối tác',
    recipients: 'nơi nhận',
    is_important: 'mức quan trọng',
    is_urgent: 'mức khẩn cấp',
    title: 'tên văn bản',
    summary: 'trích yếu nội dung',
    signer: 'người ký',
    approver: 'người phê duyệt',
    drafting_department: 'đơn vị soạn thảo',
    issued_date: 'ngày ban hành',
    sent_date: 'ngày đi',
    received_date: 'ngày đến',
    required_due_date: 'thời hạn văn bản yêu cầu',
    effective_from: 'hiệu lực từ',
    effective_to: 'hiệu lực đến',
    status: 'hiệu lực',
    processing_status: 'tình trạng xử lý',
    handler: 'người xử lý',
    related_person: 'người liên quan',
    report_receiver: 'người nhận báo cáo',
    due_date: 'hạn xử lý',
    result: 'kết quả xử lý',
    processing_note: 'ghi chú xử lý',
    storage_location: 'vị trí lưu trữ',
    content: 'nội dung soạn thảo',
    attachments: 'tệp đính kèm',
  },
})
