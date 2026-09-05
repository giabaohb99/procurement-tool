/**
 * DANH SÁCH TÀI KHOẢN DEMO — chỉ dùng cho bản chạy DEV.
 *
 * ⚠️ Tệp này chứa mật khẩu. Nó **không được lọt vào bản build thật**, và chỗ chặn
 * duy nhất là: mọi nơi đọc `DEMO_ACCOUNTS` đều phải nằm sau `HIEN_MENU_DEV` của
 * `demo-account-switcher.tsx`. Hai hằng trong đó (`import.meta.env.DEV` và
 * `VITE_DEVELOPER_MODE`) đều được Vite thay bằng giá trị thật lúc build, nên khi
 * build KHÔNG khai `VITE_DEVELOPER_MODE` thì cả biểu thức gập thành `false` và
 * Rollup cắt sạch nhánh chết lẫn mô-đun này. Đã kiểm bằng cách `grep` mật khẩu
 * trong `dist/` sau khi build — thêm nơi dùng mới thì kiểm lại, đừng tin suông.
 *
 * Ngược lại: bản chạy trên máy chủ DEV CÓ khai biến đó, tức mật khẩu ở đây nằm
 * trong gói JS mà deverp phục vụ công khai. Chấp nhận được vì đúng bằng những gì
 * bản v1 (devthumua) đang làm và đây là tài khoản của CSDL dev; đừng đặt tài
 * khoản của hệ thật vào danh sách này.
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
  /** Mã nhân viên (hiện thay `username` ở dòng phụ khi có). */
  code?: string
}

export const DEMO_ACCOUNTS: DemoAccount[] = [
  { username: 'DEGO0001', password: 'admin', label: 'Dego Admin', group: 'Quản trị', hint: 'toàn quyền' },
  { username: 'admin', password: 'admin', label: 'Quản trị viên (admin)', group: 'Quản trị', hint: 'toàn quyền' },

  // TK Đặt xe — 7 tài khoản test phân quyền phân hệ Đặt xe (mật khẩu seed: dego123).
  { username: 'duonghaiyen.idagroup@dego.com', password: 'dego123', code: 'NSU203', label: 'Dương Hải Yến (NS1)', group: 'TK Đặt xe', hint: 'Nhân sự — chỉ xem của mình' },
  { username: 'ndquyen.idagroup@dego.com', password: 'dego123', code: 'NSU202', label: 'Nguyễn Đỗ Quyên (TP1)', group: 'TK Đặt xe', hint: 'Trưởng bộ phận — duyệt, xem phòng ban' },
  { username: 'hnqanh.idagroup@dego.com', password: 'dego123', code: 'NSU171', label: 'Hồ Ngọc Quế Anh (NS2)', group: 'TK Đặt xe', hint: 'Nhân sự — chỉ xem của mình' },
  { username: 'nmtoan.idagroup@dego.com', password: 'dego123', code: 'NSU170', label: 'Nguyễn Minh Toàn (TP2)', group: 'TK Đặt xe', hint: 'Trưởng bộ phận — duyệt, xem phòng ban' },
  { username: 'bhtthanh.idaglobal@dego.com', password: 'dego123', code: 'NSU055', label: 'Bùi Huỳnh Trường Thành (ĐPV)', group: 'TK Đặt xe', hint: 'Điều phối viên — xem tất cả' },
  { username: 'ltnhut.idagroup@dego.com', password: 'dego123', code: 'NSU060', label: 'Lê Tấn Nhựt (TX1)', group: 'TK Đặt xe', hint: 'Tài xế — chỉ xem chuyến được giao' },
  { username: 'tqthai.idagroup@dego.com', password: 'dego123', code: 'NSU058', label: 'Trần Quốc Thái (TX2)', group: 'TK Đặt xe', hint: 'Tài xế — chỉ xem chuyến được giao' },

  // Các tài khoản test chính có dữ liệu mẫu DB
  { username: 'TESTREQ', password: 'TESTREQ', label: 'TESTREQ', group: 'Tài khoản Test (Data)', hint: 'người tạo phiếu test' },
  { username: 'DEMONV', password: 'DEMONV', label: 'DEMONV', group: 'Tài khoản Test (Data)', hint: 'nhân viên' },
  { username: 'DEMOTP', password: 'DEMOTP', label: 'DEMOTP', group: 'Tài khoản Test (Data)', hint: 'trưởng phòng' },
  { username: 'DEMOQL', password: 'DEMOQL', label: 'DEMOQL', group: 'Tài khoản Test (Data)', hint: 'quản lý' },
  { username: 'DEMOAD', password: 'DEMOAD', label: 'DEMOAD', group: 'Tài khoản Test (Data)', hint: 'admin demo' },
  { username: 'DEMOTP2', password: 'DEMOTP2', label: 'DEMOTP2', group: 'Tài khoản Test (Data)', hint: 'trưởng phòng 2' },
  { username: 'DEMOTP3', password: 'DEMOTP3', label: 'DEMOTP3', group: 'Tài khoản Test (Data)', hint: 'trưởng phòng 3' },

  { username: 'DEMO_MANAGER', password: 'demo123', label: 'Trưởng bộ phận (DEMO_MANAGER)', group: 'Duyệt · Văn thư', hint: 'người duyệt bước 1' },
  { username: 'DEMO_STAFF', password: 'demo123', label: 'Nhân viên (DEMO_STAFF)', group: 'Duyệt · Văn thư', hint: 'người trình' },
  { username: 'TESTMEDEGO', password: 'TESTMEDEGO', label: 'Văn thư DEGO HOLDING', group: 'Duyệt · Văn thư', hint: 'pháp nhân mẹ' },
  { username: 'TESTCONAGRI', password: 'TESTCONAGRI', label: 'Văn thư AGRIPLANT', group: 'Duyệt · Văn thư', hint: 'pháp nhân con' },

  { username: 'DEMO_MANAGER_PURCHASE', password: 'demo123', label: 'Trưởng phòng Thu mua', group: 'Thu mua' },
  { username: 'DEMO_PURCHASER', password: 'demo123', label: 'Nhân viên Thu mua', group: 'Thu mua' },

  // Văn thư ở TỪNG pháp nhân con — do `seed_van_thu_phap_nhan_con.py` tạo
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
