/**
 * Dòng hoạt động cấp dự án (D-09, §8 của `05-giao-dien.md`).
 *
 * Khác khối «Lịch sử thao tác» trong panel một việc (E-04, `@/shared/audit`):
 * đây gộp nhật ký của CẢ dự án — việc + thành viên vào ra + sửa dự án và cột.
 */

/** Một dòng — khớp `_activity_out` của `work/activity_service.py`. */
export interface WorkActivity {
  id: number
  /** Loại sự kiện, xem {@link WORK_ACTIVITY_KIND}. */
  kind: number
  action: string
  /** Nhãn tiếng Việt của hành động ("Tạo mới", "Cập nhật", "Xóa"). */
  action_label: string
  /** Câu ghi log, ví dụ `Tạo công việc: Dựng khung`. */
  message: string
  /** Tên người thao tác, backend đã tra sẵn. */
  by: string
  by_id: number
  /** Mốc thời gian ISO, giờ UTC không hậu tố — `format-date` tự bù múi giờ. */
  at: string
  /** Có id thì dòng bấm sang được panel chi tiết việc. */
  task_id: number | null
  task_title: string
}

export interface WorkActivityPage {
  items: WorkActivity[]
  total: number
  has_more: boolean
}

/** Người từng thao tác trên dự án — nguồn cho ô lọc «theo người». */
export interface WorkActivityActor {
  /** `user_id` (trục của `tab_audit_log`), KHÔNG phải id nhân sự. */
  id: number
  name: string
}

/**
 * Loại sự kiện — khớp `WorkActivityKind` ở `work/audit_entity.py`.
 *
 * Khai tay ở đây chứ không sinh từ `gen_status_ts.py`: khung sinh mã đó phục vụ
 * bộ mã CHUỖI của `status_catalog.py` (QĐ-9), còn phân hệ này đi lối `IntEnum`
 * như `forum` — cùng khuôn với `WORK_TASK_STATUS` ở `types/work.ts`.
 */
export const WORK_ACTIVITY_KIND = {
  TASK: 1,
  MEMBER: 2,
  LIST: 3,
} as const

export type WorkActivityKind =
  (typeof WORK_ACTIVITY_KIND)[keyof typeof WORK_ACTIVITY_KIND]

/** Mục của ô lọc «loại sự kiện»; `null` = không lọc. */
export const WORK_ACTIVITY_KIND_OPTIONS: { value: WorkActivityKind | null; label: string }[] = [
  { value: null, label: 'Tất cả hoạt động' },
  { value: WORK_ACTIVITY_KIND.TASK, label: 'Công việc' },
  { value: WORK_ACTIVITY_KIND.MEMBER, label: 'Thành viên' },
  { value: WORK_ACTIVITY_KIND.LIST, label: 'Dự án & cột' },
]
