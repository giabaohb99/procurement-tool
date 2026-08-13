/**
 * ĐỐI TÁC văn bản — nơi GỬI của văn bản đến và nơi NHẬN của văn bản đi.
 *
 * Cố ý tách khỏi danh mục Nhà cung cấp của phân hệ Thu mua: bên đó là pháp nhân
 * mua bán (có mã số thuế, VAT, hợp đồng), còn ở đây phần lớn là cơ quan nhà
 * nước, ngân hàng, đơn vị nội bộ — trùng nhau rất ít.
 */
export type PartnerKind = 'agency' | 'company' | 'individual' | 'internal'

export const PARTNER_KIND_LABELS: Record<PartnerKind, string> = {
  agency: 'Cơ quan nhà nước',
  company: 'Doanh nghiệp',
  individual: 'Cá nhân',
  internal: 'Đơn vị nội bộ',
}

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

export const DEFAULT_DOCUMENT_PARTNERS: DocumentPartner[] = [
  {
    id: 1,
    code: 'SKHDT',
    name: 'Sở Kế hoạch và Đầu tư',
    kind: 'agency',
    contact_person: '',
    phone: '',
    email: '',
    address: '',
    is_active: true,
  },
  {
    id: 2,
    code: 'CUCTHUE',
    name: 'Cục Thuế TP.HCM',
    kind: 'agency',
    contact_person: '',
    phone: '',
    email: '',
    address: '',
    is_active: true,
  },
  {
    id: 3,
    code: 'VCB',
    name: 'Ngân hàng Vietcombank — CN Tân Bình',
    kind: 'company',
    contact_person: 'Phòng KHDN',
    phone: '',
    email: '',
    address: '',
    is_active: true,
  },
  {
    id: 4,
    code: 'DEGO-HO',
    name: 'DEGO Holding — Văn phòng công ty',
    kind: 'internal',
    contact_person: '',
    phone: '',
    email: '',
    address: '',
    is_active: true,
  },
]
