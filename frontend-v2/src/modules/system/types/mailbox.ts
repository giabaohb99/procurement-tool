/**
 * HỘP THƯ GỬI — địa chỉ đứng tên gửi thư thay cho địa chỉ hệ thống (26/08/2026).
 *
 * Ca dựng nên nó: nhân sự hành chính đăng nhập bằng tài khoản của chính mình
 * nhưng ban hành *Thông báo nghỉ lễ* cho toàn công ty **danh nghĩa
 * `hr@gmail.com`** — người nhận phải thấy thư đến từ phòng Hành chính.
 *
 * Mỗi hộp thư giữ bộ SMTP RIÊNG chứ không chỉ đổi dòng «Từ»: Gmail ghi đè `From`
 * về đúng tài khoản đã đăng nhập trừ khi địa chỉ kia đã khai *Send mail as*, nên
 * chỉ đổi tiêu đề là người nhận vẫn thấy địa chỉ cũ — hỏng mà không báo.
 */
export interface Mailbox {
  id: number
  code: string
  name: string
  email: string
  /** Tên hiện trước địa chỉ: «Phòng Hành chính &lt;hr@gmail.com&gt;». */
  display_name: string

  smtp_host: string
  smtp_port: number
  smtp_user: string
  /**
   * Đã có mật khẩu ứng dụng chưa. **Giá trị thật không bao giờ trả về** — cùng
   * quy ước với `smtp_password` ở màn Cấu hình hệ thống.
   */
  has_password: boolean
  /** Đã khai đủ để gửi được chưa (máy chủ + mật khẩu). */
  ready: boolean
  use_tls: boolean

  /** Rỗng = hộp thư cấp Tập đoàn, pháp nhân nào cũng dùng được. */
  company_id: number | null
  note: string
  is_active: boolean

  /** Nhân sự được gửi danh nghĩa hộp thư này. */
  employee_ids: number[]
}

export interface MailboxInput {
  code: string
  name: string
  email: string
  display_name: string
  smtp_host: string
  smtp_port: number
  smtp_user: string
  /**
   * ⚠️ Chuỗi rỗng = **GIỮ NGUYÊN** mật khẩu đang có, KHÔNG phải xóa.
   *
   * Màn sửa không bao giờ nhận lại được giá trị cũ (API không trả), nên nó gửi
   * rỗng ở mọi lần sửa tên hay ghi chú. Coi rỗng là xóa thì sửa một cái nhãn
   * cũng đủ làm hộp thư ngừng gửi được mà không dòng nào báo. Muốn xóa thật thì
   * gọi `DELETE /api/mailboxes/{id}/password`.
   */
  smtp_password: string
  use_tls: boolean
  company_id: number | null
  note: string
  is_active: boolean
  employee_ids: number[]
}
