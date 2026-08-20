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

  //  Văn thư ở TỪNG pháp nhân con — do `seed_van_thu_phap_nhan_con.py` tạo, mật
  //  khẩu = mã nhân viên. Đây là nửa sau của luồng clone: ban hành ở Tập đoàn
  //  xong, đổi sang một trong những tài khoản này để xem bản nháp đã nằm sẵn ở
  //  công ty đó, sửa lại rồi tự ban hành với số hiệu riêng.
  //
  //  Mỗi tài khoản chỉ thấy văn bản của CHÍNH pháp nhân mình (phạm vi dữ liệu
  //  `company`) — đó mới là thứ đáng cho người xem demo thấy.
  //
  //  ⚠️ Viết TAY từng dòng, đừng rút gọn bằng `.map()` cho ngắn. Đã thử và
  //  `npm run kiem:bundle` bắt được: Rollup không chứng minh được lời gọi `.map()`
  //  là vô hại nên giữ nguyên cả mô-đun, và **12 mật khẩu lọt thẳng vào bản build
  //  thật**. Mảng literal thuần thì nó cắt sạch.
  { username: 'VTAGRIPLANT', password: 'VTAGRIPLANT', label: 'Văn thư AGRIPLANT', group: 'Pháp nhân con' },
  { username: 'VTSAM', password: 'VTSAM', label: 'Văn thư SAM', group: 'Pháp nhân con' },
  { username: 'VTICARE', password: 'VTICARE', label: 'Văn thư Dược phẩm ICARE', group: 'Pháp nhân con' },
  { username: 'VTIDA', password: 'VTIDA', label: 'Văn thư XNK IDA Global', group: 'Pháp nhân con' },
  { username: 'VTABA', password: 'VTABA', label: 'Văn thư SX Hóa chất ABA', group: 'Pháp nhân con' },
  { username: 'VTNNABA', password: 'VTNNABA', label: 'Văn thư Hóa chất NN ABA', group: 'Pháp nhân con' },
  { username: 'VTNNDEGO', password: 'VTNNDEGO', label: 'Văn thư Hóa chất NN DEGO', group: 'Pháp nhân con' },
  { username: 'VTN2SBIO', password: 'VTN2SBIO', label: 'Văn thư N2SBIO Việt Nam', group: 'Pháp nhân con' },
  { username: 'VTBAMBOO', password: 'VTBAMBOO', label: 'Văn thư XNK SX TM Bamboo', group: 'Pháp nhân con' },
  { username: 'VTDRXANH', password: 'VTDRXANH', label: 'Văn thư NPP Dr Xanh', group: 'Pháp nhân con' },
  { username: 'VTHKDDRXANH', password: 'VTHKDDRXANH', label: 'Văn thư Hộ KD Dr Xanh', group: 'Pháp nhân con' },
  { username: 'VTDEGOHOLDING', password: 'VTDEGOHOLDING', label: 'Văn thư Dego Holding', group: 'Pháp nhân con' },

  { username: 'HDSD0001', password: 'helpadmin', label: 'Quản trị Hướng dẫn sử dụng', group: 'Khác' },
]
