/**
 * ĐƠN VỊ GỬI NHẬN BÊN NGOÀI (`tab_external_party`) — nơi GỬI của văn bản đến và
 * nơi NHẬN của văn bản đi.
 *
 * Cố ý tách khỏi danh mục Nhà cung cấp của phân hệ Thu mua: bên đó là pháp nhân
 * mua bán (mã số thuế, VAT, hợp đồng), còn ở đây phần lớn là cơ quan nhà nước,
 * ngân hàng, đơn vị nội bộ — trùng nhau rất ít.
 *
 * `kind` là **số** đúng như cột trong DB, không phải chuỗi: trạng thái và phân
 * loại lưu bằng số là quy ước chung của cả cơ sở dữ liệu này.
 */

export type PartnerKind = 1 | 2 | 3 | 4 | 5

export const PARTNER_KIND_LABELS: Record<PartnerKind, string> = {
  1: 'Cơ quan nhà nước',
  2: 'Đối tác',
  3: 'Khách hàng',
  4: 'Đơn vị nội bộ',
  5: 'Khác',
}

/** Dùng cho ô chọn trên form — thứ tự hiện đúng thứ tự khai ở trên. */
export const PARTNER_KIND_OPTIONS = (
  Object.entries(PARTNER_KIND_LABELS) as [string, string][]
).map(([value, label]) => ({ value: Number(value) as PartnerKind, label }))

export interface DocumentPartner {
  id: number
  code: string
  name: string
  kind: PartnerKind
  /** Người liên hệ / người ký thường gặp. */
  contact_person: string
  phone: string
  email: string
  address: string
  is_active: boolean
}
