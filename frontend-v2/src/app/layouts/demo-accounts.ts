/**
 * DANH SÁCH TÀI KHOẢN DEMO — chỉ dùng cho bản chạy DEV.
 *
 * ⚠️ Tệp này chứa mật khẩu. Nó **không được lọt vào bản build thật**, và chỗ chặn
 * duy nhất là: mọi nơi đọc `DEMO_ACCOUNTS` đều phải nằm sau `import.meta.env.DEV`.
 * Vite thay hằng đó bằng `false` khi build, nên Rollup cắt sạch nhánh chết và cả
 * mô-đun này. Đã kiểm bằng cách `grep` mật khẩu trong `dist/` sau khi build —
 * thêm nơi dùng mới thì kiểm lại, đừng tin suông.
 *
 * Đây là mật khẩu của CSDL seed dùng cho máy lập trình, không phải của hệ thật.
 */
export interface DemoAccount {
  username: string
  password: string
  /** Tên hiện trên menu — nói rõ VAI TRÒ vì đó là thứ người xem demo quan tâm. */
  label: string
  /** Xếp nhóm trong menu. */
  group: string
  /** Chú thích ngắn bên phải: pháp nhân hoặc phạm vi dữ liệu. */
  hint?: string
}

export const DEMO_ACCOUNTS: DemoAccount[] = [
  { username: 'DEGO0001', password: 'admin', label: 'Dego Admin', group: 'Quản trị', hint: 'toàn quyền' },
  { username: 'admin', password: 'admin', label: 'Quản trị viên', group: 'Quản trị', hint: 'toàn quyền' },

  { username: 'DEMO_MANAGER', password: 'demo123', label: 'Trưởng bộ phận', group: 'Duyệt · Văn thư', hint: 'người duyệt bước 1' },
  { username: 'DEMO_STAFF', password: 'demo123', label: 'Nhân viên', group: 'Duyệt · Văn thư', hint: 'người trình' },
  { username: 'TESTMEDEGO', password: 'TESTMEDEGO', label: 'Văn thư DEGO HOLDING', group: 'Duyệt · Văn thư', hint: 'pháp nhân mẹ' },
  { username: 'TESTCONAGRI', password: 'TESTCONAGRI', label: 'Văn thư AGRIPLANT', group: 'Duyệt · Văn thư', hint: 'pháp nhân con' },

  { username: 'DEMO_MANAGER_PURCHASE', password: 'demo123', label: 'Trưởng phòng Thu mua', group: 'Thu mua' },
  { username: 'DEMO_PURCHASER', password: 'demo123', label: 'Nhân viên Thu mua', group: 'Thu mua' },

  { username: 'HDSD0001', password: 'helpadmin', label: 'Quản trị Hướng dẫn sử dụng', group: 'Khác' },
]
