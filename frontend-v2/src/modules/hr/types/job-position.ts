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

/**
 * Đếm ngược từ hồ sơ: chức vụ này có bao nhiêu người giữ, ở những phòng nào
 * (duoc-CR-322, `GET /api/job-positions/stats`).
 *
 * ⚠️ `total` **lọc theo phạm vi dữ liệu** của người đang xem, nên nó có thể NHỎ
 * HƠN con số mà backend nêu khi từ chối xóa (chốt đó đếm toàn công ty). Câu
 * chặn xóa tự nói rõ «trên toàn công ty» vì lý do đó.
 */
/**
 * Một gương mặt trong cụm xếp chồng ảnh. `avatar` rỗng khi hồ sơ chưa được cấp
 * tài khoản hoặc chưa đặt ảnh — giao diện rơi về chữ viết tắt, không phải lỗi.
 */
export type JobPositionHolderFace = { id: number; full_name: string; avatar: string }

export type JobPositionStat = {
  position_id: number
  total: number
  /**
   * Phòng ban đang có người giữ chức vụ này, đông người nhất trước.
   *
   * ⚠️ CỐ Ý không kèm gương mặt: cột «Phòng ban đang giữ» xếp chồng ảnh của
   * **phòng ban** (chữ viết tắt tên phòng), không phải ảnh người trong phòng —
   * thứ đó đã có ở cột «Đang giữ» ngay bên cạnh.
   */
  departments: { id: number; name: string; count: number }[]
  /**
   * Gương mặt ở mức chức vụ, tối đa 6 (`HOLDER_FACES_PER_POSITION` ở backend).
   * ⚠️ **Không phải danh sách đầy đủ** — số thật là `total`, nên «+N» phải tính
   * từ `total` chứ đừng lấy `holders.length`. Xem đủ thì mở tab «Người đang giữ».
   */
  holders: JobPositionHolderFace[]
}
