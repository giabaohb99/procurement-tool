/**
 * Một dòng KẾ HOẠCH NHÂN SỰ (duoc-CR-689) — khớp `serialize_plans` ở
 * `backend/app/modules/headcount_plan/serializer.py`.
 *
 * Khai `type` (không `interface`) để thỏa ràng buộc `CrudRecord` của khung CRUD chung.
 */
export type HeadcountPlan = {
  id: number
  year: number
  company_id: number
  company_name: string
  /** `0` = dòng của CẢ pháp nhân (so với tổng pháp nhân ở báo cáo, không cộng dồn với các dòng phòng). */
  department_id: number
  /** Backend tự ghi «Toàn pháp nhân» cho dòng `department_id = 0`. */
  department_name: string
  planned_headcount: number
  /**
   * Quỹ lương kế hoạch / tháng (lương + phụ cấp, VND). `null` khi người xem KHÔNG có
   * `labor_contract.read` — backend che ở serializer, giao diện chỉ việc ẩn cột.
   */
  planned_payroll_monthly: number | null
  note: string
  updated_at?: string | null
}

/** Kết quả nhập CSV — `csv_service.import_rows`. */
export interface HeadcountPlanImportResult {
  created: number
  updated: number
}

/** Giá trị «Toàn pháp nhân» của ô phòng ban — `0` là giá trị THẬT, không phải «chưa chọn». */
export const WHOLE_COMPANY_DEPARTMENT_ID = 0
export const WHOLE_COMPANY_LABEL = 'Toàn pháp nhân'
