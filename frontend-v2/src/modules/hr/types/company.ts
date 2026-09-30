/** Công ty (pháp nhân) — khớp `CompanyOut` của backend. */
export interface Company {
  id: number
  code: string
  /** Tên pháp nhân đầy đủ. */
  name: string
  /** Mã chữ HOA/số đi vào số hiệu văn bản, khác mã hiển thị `code`. */
  issue_code: string
  short_name: string
  /** 1 Tập đoàn · 2 công ty thành viên · 3 đơn vị trực thuộc. */
  level: 1 | 2 | 3
  /** bao-CR-531 — loại hình: xem `COMPANY_TYPE`. Backend cũ chưa gửi thì coi là Công ty. */
  company_type?: CompanyTypeCode
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
  /** Lần sửa gần nhất — cột "Ngày cập nhật" (bao-CR-300, ticket 21). */
  updated_at?: string
}

export const COMPANY_LEVEL_LABELS: Record<Company['level'], string> = {
  1: 'Tập đoàn',
  2: 'Công ty thành viên',
  3: 'Đơn vị trực thuộc',
}

const COMPANY_LEVELS = [1, 2, 3] as const

/** Đổ vào ô chọn "Cấp pháp nhân"; dựng TỪ bảng nhãn để hai chỗ không trôi khỏi nhau. */
export const COMPANY_LEVEL_OPTIONS = COMPANY_LEVELS.map((value) => ({
  value,
  label: COMPANY_LEVEL_LABELS[value],
}))

/**
 * Loại hình pháp nhân — bao-CR-531. Mã SỐ, gõ tay theo `backend/app/modules/company/constants.py`
 * (`CompanyType`); `gen_status_ts.py` chỉ sinh bộ mã CHUỖI. Đổi ở backend thì sửa tay ở đây.
 * «Hộ kinh doanh» làm bản in Phiếu đề xuất mua hàng chỉ còn hai ô ký «Chủ hộ» + «Người lập».
 */
export const COMPANY_TYPE = {
  COMPANY: 1,
  HOUSEHOLD: 2,
} as const

export type CompanyTypeCode = (typeof COMPANY_TYPE)[keyof typeof COMPANY_TYPE]

export const COMPANY_TYPE_LABELS: Record<CompanyTypeCode, string> = {
  [COMPANY_TYPE.COMPANY]: 'Công ty',
  [COMPANY_TYPE.HOUSEHOLD]: 'Hộ kinh doanh',
}

/** Đổ vào ô chọn «Loại hình»; dựng TỪ bảng nhãn để hai chỗ không trôi khỏi nhau. */
export const COMPANY_TYPE_OPTIONS = Object.values(COMPANY_TYPE).map((value) => ({
  id: value as number,
  label: COMPANY_TYPE_LABELS[value],
}))

/**
 * Chữ viết tắt cho logo: lấy chữ đầu của MÃ công ty. Tên pháp nhân hay bắt đầu
 * bằng "CÔNG TY CỔ PHẦN…" nên lấy theo tên thì công ty nào cũng ra "C".
 */
export function companyInitial(company: Pick<Company, 'code' | 'name'>): string {
  return ((company.code || company.name || '?').trim()[0] || '?').toUpperCase()
}
