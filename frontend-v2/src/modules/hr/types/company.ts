/** Công ty (pháp nhân) — khớp `CompanyOut` của backend. */
export interface Company {
  id: number
  code: string
  /** Tên pháp nhân đầy đủ. */
  name: string
  tax_code: string
  address: string
  /** Nơi nhận hóa đơn điện tử của pháp nhân này. */
  invoice_email: string
  /** ID pháp nhân cấp trên; 0 = công ty gốc. */
  parent: number
  legal_representative_id: number | null
  /** Chức danh in trên hợp đồng / chứng từ, vd "Giám đốc". */
  legal_rep_title: string
  is_active: boolean
  legal_rep_name?: string | null
  /** Đặt qua endpoint upload riêng, KHÔNG nhập trong form. */
  logo: string
}

/**
 * Chữ viết tắt cho logo: lấy chữ đầu của MÃ công ty. Tên pháp nhân hay bắt đầu
 * bằng "CÔNG TY CỔ PHẦN…" nên lấy theo tên thì công ty nào cũng ra "C".
 */
export function companyInitial(company: Pick<Company, 'code' | 'name'>): string {
  return ((company.code || company.name || '?').trim()[0] || '?').toUpperCase()
}
