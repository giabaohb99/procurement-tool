/**
 * HỘP THƯ GỬI THÔNG BÁO BAN HÀNH (26/08/2026).
 *
 * Ca nghiệp vụ: nhân sự hành chính đăng nhập bằng tài khoản của chính mình
 * (`nhanvien@gmail.com`) nhưng ban hành *Thông báo nghỉ lễ* cho toàn công ty
 * **danh nghĩa `hr@gmail.com`** — người nhận phải thấy thư đến từ phòng Hành
 * chính, không phải từ một cá nhân.
 *
 * Danh sách này backend đã lọc sẵn theo hai điều kiện, client KHÔNG tự lọc lại:
 * chỉ hộp thư người đang đăng nhập được cấp, và chỉ hộp thư dùng được ở pháp
 * nhân ban hành văn bản đó.
 */
export interface IssueMailbox {
  id: number
  /** Địa chỉ sẽ hiện ở dòng «Từ» trên thư người nhận mở ra. */
  email: string
  name: string
  display_name: string
  /**
   * Đã khai đủ đường SMTP để gửi được chưa.
   *
   * Hộp thư thiếu máy chủ hay mật khẩu ứng dụng vẫn bày ra — nhưng phải nói rõ
   * và không cho chọn. Giấu đi thì người dùng không hiểu vì sao hộp thư mình
   * được cấp lại không có trong danh sách.
   */
  ready: boolean
}
