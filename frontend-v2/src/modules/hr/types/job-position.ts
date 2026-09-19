/**
 * DANH MỤC CHỨC VỤ — `tab_job_position` (duoc-CR-320).
 *
 * Nguồn của ô chọn «Vị trí / Chức vụ» trên hồ sơ nhân sự. Trước đợt này ô đó là
 * chữ gõ tay, nên cùng một chức vụ hiện ra bốn cách viết trên bản in, tệp Excel
 * và hồ sơ mà trợ lý AI đọc.
 *
 * ⚠️ Đừng nhầm với `JOB_LEVEL_OPTIONS` (Cấp bậc) ở `employee-codes.ts`: cấp bậc
 * là thang bậc CỐ ĐỊNH bảy mức khai trong mã nguồn, còn chức vụ là danh sách
 * người dùng tự thêm bớt trên màn hình.
 */
//  ⚠️ `type` chứ KHÔNG `interface`: khung CRUD khai báo ràng `T extends
//  CrudRecord` (`Record<string, unknown>`), mà TypeScript chỉ cấp "chỉ mục
//  ngầm" cho type alias — một `interface` y hệt sẽ báo không gán được, đúng lỗi
//  vừa gặp lúc dựng màn này. Cùng lý do `MeetingRoom` cũng là `type`.
export type JobPosition = {
  id: number
  /** Mã ổn định, KHÔNG sửa được sau khi tạo (backend bỏ `code` khỏi schema sửa). */
  code: string
  name: string
  is_active: boolean
  sort_order: number
  note: string
  /** `0` = chức vụ dùng chung mọi phòng ban, không phải «chưa chọn». */
  department_id: number
  updated_at?: string | null
}
