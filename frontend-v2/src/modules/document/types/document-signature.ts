/**
 * CHỮ KÝ trên văn bản (J02, J03).
 *
 * Ba loại có **giá trị pháp lý khác hẳn nhau**. Câu mô tả giá trị (`legal_note`)
 * do backend cấp — giao diện KHÔNG tự viết lại: đây đúng là chỗ mà một câu chữ
 * nhẹ tay hơn sẽ dẫn tới việc gửi ra ngoài một văn bản tưởng có giá trị pháp lý
 * mà thật ra không.
 */

export const SIGN_KIND = {
  /** Hệ thống này tự làm. Đủ giá trị nội bộ tập đoàn. */
  internal: 1,
  /** Qua nhà cung cấp chứng thư số — J08, chưa làm; đây chỉ là bản ghi nhận. */
  certified: 2,
  /** Ký giấy đã quét lên. */
  scanned: 3,
} as const

export interface DocumentSignature {
  id: number
  document_id: number
  version_id: number
  version_no: string
  signer_employee_id: number
  signer_name: string
  sign_kind: number
  sign_kind_label: string
  /** Câu giá trị pháp lý, hiện NGAY CẠNH chữ ký (J03). */
  legal_note: string
  signed_at: string
  content_sha256: string
  cert_serial: string
  cert_issuer: string
  ip: string
  /**
   * Chữ ký còn khớp nội dung hiện tại của phiên bản không.
   * Lệch nghĩa là nội dung đã bị đổi SAU khi ký — đáng báo động.
   */
  content_matches: boolean
}

export interface SignKindOption {
  value: number
  label: string
  legal_note: string
}

export interface DocumentSignatureInput {
  version_id: number
  signer_employee_id: number
  sign_kind: number
  cert_serial?: string
  cert_issuer?: string
}
