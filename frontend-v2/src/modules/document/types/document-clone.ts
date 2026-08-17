/**
 * CLONE XUỐNG PHÁP NHÂN CON (F06–F10).
 *
 * Quyết định cũ từng cấm hẳn việc nhân bản — *"sau 6 tháng sẽ có 12 bản khác
 * nhau và không ai biết bản nào đúng"*. Mở lại kèm bốn điều kiện bắt buộc, và
 * bảng theo dõi này chính là điều kiện thứ tư.
 */

export const CLONE_STATUS = {
  sent: 1,
  drafting: 2,
  submitted: 3,
  issued: 4,
  rejected: 5,
  /** Cần rà lại vì bản gốc đã lên phiên bản mới. */
  stale: 6,
} as const

export interface DocumentCloneRow {
  document_id: number
  company_id: number
  company_name: string
  title: string
  display_code: string
  status: number
  status_label: string
  clone_status: number
  clone_status_label: string
  version_no: string
  /** Bản clone đang bám phiên bản CŨ của gốc — câu khó nhất trong bốn câu. */
  is_outdated: boolean
  assignee_name: string
  due_date: string | null
  handled_at: string
}

export interface PendingCompany {
  company_id: number
  company_name: string
  /** Đã khai trong kế hoạch từ lúc tạo văn bản — hộp thoại tick sẵn. */
  planned: boolean
}

/** Một dòng KẾ HOẠCH clone: đã khai, chưa sinh bản nháp. */
export interface DocumentClonePlanRow {
  company_id: number
  company_name: string
  due_date: string | null
  note: string
}

export interface DocumentCloneList {
  items: DocumentCloneRow[]
  /** Pháp nhân chưa nhận bản clone nào — phần "ai chưa đụng tới". */
  pending_companies: PendingCompany[]
  /** Dự định khai từ lúc tạo, chạy được sau khi ban hành. */
  plan: DocumentClonePlanRow[]
}

export interface DocumentCloneInput {
  company_ids: number[]
  due_date?: string | null
  note?: string
}

/**
 * Kế hoạch clone gửi lên: danh sách pháp nhân **cuối cùng** đang tick.
 *
 * Ghi đè chứ không cộng dồn — bỏ tick một nơi phải là gỡ nơi đó khỏi kế hoạch.
 */
export interface DocumentClonePlanInput {
  company_ids: number[]
  due_date: string
  note: string
}
