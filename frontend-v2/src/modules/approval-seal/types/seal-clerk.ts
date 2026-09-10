/** Trạng thái phân công văn thư (khớp `ClerkStatus` backend). */
export const CLERK_STATUS = { active: 1, onLeave: 2, inactive: 3 } as const

export const CLERK_STATUS_LABELS: Record<number, string> = {
  [CLERK_STATUS.active]: 'Đang hoạt động',
  [CLERK_STATUS.onLeave]: 'Nghỉ phép',
  [CLERK_STATUS.inactive]: 'Ngưng sử dụng',
}

/** Một dòng phân công VĂN THƯ (Duyệt dấu) theo công ty — khớp `SealClerkOut` backend. */
export interface SealClerk {
  id: number
  employee_id: number
  company_id: number
  /** Văn thư tổng — phụ trách phiếu ĐA công ty. */
  is_head: boolean
  /** 1 = Đang hoạt động, 2 = Tạm dừng (giữ phân công nhưng ngừng nhận phiếu). */
  status: number
  employee_name: string | null
  employee_code: string | null
  company_name: string | null
  status_label: string | null
}

export interface SealClerkBulkPayload {
  employee_id: number
  company_ids: number[]
  is_head: boolean
}

/** Công ty phụ trách (kèm logo) để hiển thị chuỗi ảnh đại diện trên danh sách. */
export interface SealClerkCompany {
  id: number
  name: string
  logo: string
}

/** Một dòng danh sách GỘP THEO VĂN THƯ (mỗi người một dòng). */
export interface SealClerkGroup {
  employee_id: number
  /** Một dòng đại diện để mở trang chi tiết. */
  anchor_id: number
  employee_name: string | null
  employee_code: string | null
  company_count: number
  /** Đã sắp: DEGO HOLDING đứng đầu. */
  companies: SealClerkCompany[]
  is_head: boolean
  /** 1 = Đang hoạt động, 2 = Tạm dừng. */
  status: number
  status_label: string | null
}
