export type ExclusionScope = 'employee' | 'department' | 'company'

/** Một luật loại trừ email — theo cá nhân / phòng ban / công ty. */
export interface EmailExclusion {
  id: number
  scope: ExclusionScope
  scope_label: string
  ref_id: number
  label: string
  /** Mã mẫu email áp dụng; "" = mọi mẫu. */
  event: string
  /** Nhãn mẫu email, vd "Duyệt → Điều phối viên" hoặc "Tất cả mẫu". */
  event_label: string
}
