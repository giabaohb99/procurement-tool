/**
 * Phân quyền hai trục của backend:
 *  1. HÀNH ĐỘNG thuộc VAI TRÒ — ma trận (entity × action), chính là map dưới đây.
 *  2. PHẠM VI DỮ LIỆU thuộc NGƯỜI DÙNG — lọc ở tầng query của backend, frontend
 *     không nhìn thấy và cũng không cần biết.
 *
 * ⚠️ Map này CHỈ để ẩn/hiện menu và nút bấm cho đỡ vướng mắt. Chốt chặn thật nằm ở
 * backend (`require()` + `apply_scope()`) — tuyệt đối không coi `can()` là bảo mật.
 */

export const ACTIONS = [
  'read',
  'create',
  'write',
  'delete',
  'approve',
  'cancel',
  'print',
  'export',
  /** Cờ tổng hợp do backend thêm cho nhân sự thu mua, không phải ô trong ma trận vai trò. */
  'process',
] as const

export type PermissionAction = (typeof ACTIONS)[number]

/** Danh sách entity chuẩn — phải khớp `ENTITIES` trong backend `core/permissions.py`. */
export const ENTITIES = [
  'company',
  'department',
  'employee',
  'user',
  'role',
  'warehouse',
  'unit',
  'item_group',
  'brand',
  'supplier',
  'product',
  'contract',
  'purchase_request',
  'survey',
  'purchase_order',
  'goods_receipt',
  'inventory',
  'payable',
  'payment',
  'payment_request',
  'report',
  'setting',
  'category_assignee',
  'survey_request',
  'import',
  'backup',
  'help_article',
  'ticket',
  // Phân hệ Văn thư — phải khớp `ENTITIES` trong backend `core/permissions.py`.
  //  MỘT KHÓA = MỘT MÀN HÌNH (CR-157). Trước đó bốn màn danh mục dùng chung
  //  `doc_type` nên không tách được ba nhóm việc khai báo khác nhau.
  'doc_type',
  'doc_template',
  'doc_numbering_rule',
  'doc_link_rule',
  'external_party',
  'document_book',
  'document',
  'security_level',
  //  Phân hệ Duyệt dấu. Chưa có màn nào ở v2 gọi `can('seal_request', …)`, nhưng
  //  danh sách này là BẢN SAO của `ENTITIES` backend chứ không phải "những khóa
  //  v2 đang dùng" — thiếu một khóa thì `can()` không gõ nổi tên nó (union type),
  //  và người viết màn mới sẽ ép kiểu hoặc bỏ luôn cổng quyền.
  //  Bài kiểm canh: `test/backend/test_dong_bo_giao_dien_v2.py`.
  'seal_request',
  'seal_type',
  // Bộ máy phê duyệt dùng chung — không thuộc phân hệ nào.
  'approval_flow',
  // Trợ lý AI — cổng quyền thuần (chỉ ban lãnh đạo), khai PUBLIC ở scoping backend.
  'assistant',
  //  Ai được KHAI hộp thư gửi và cấp cho người khác dùng (26/08/2026). Khác hẳn
  //  quyền *dùng* một hộp thư — cái đó khai đích danh ở `tab_mailbox_member`.
  'mailbox',
  //  Phân hệ Công việc (CR-216). MỘT khóa cho cả phân hệ — quyền thật nằm ở
  //  tầng thành viên của từng list, xem `doc/erp/cong-viec/04-phan-quyen.md`.
  'work_task',
  //  Diễn đàn (CR-263): hai khóa CHỈ của vai trò `forum_admin` — kiểm duyệt bài
  //  và dựng chuyên mục. Người thường không có grant nào: đọc/đăng đi theo luật
  //  audience riêng trong API diễn đàn. FE chỉ dùng để hiện tab «Quản trị».
  'forum_post',
  'forum_board',
  //  Phân hệ Đặt xe nội bộ (DEGO Booking Auto). Ba khóa khớp backend
  //  `core/permissions.py`: phiếu đặt xe + hai danh mục Xe/Tài xế.
  'vehicle_booking',
  'vehicle',
  'driver',
  //  (seal_request / seal_type đã khai ở trên — không lặp lại.)
  //  Phân hệ Nghỉ phép (CR-259). Bốn khóa vì bốn màn của ba nhóm người khác
  //  nhau — gộp lại thì cho ai xem đơn của mình là cho họ tự tặng thêm ngày
  //  phép (`leave_balance.write` mở cột điều chỉnh tay).
  'leave_request',
  'leave_balance',
  'leave_type',
  'holiday',
  //  Đặt phòng họp (duoc-CR-279). Hai khóa: đặt phòng là việc của mọi người,
  //  khai danh mục phòng là việc quản trị.
  'room_booking',
  'meeting_room',
  //  Hồ sơ nhân sự mở rộng (HRM Đợt 1, 08/09/2026) — nhóm trường CCCD / ngân
  //  hàng / địa chỉ nhà / số BHXH và hai bảng người thân.
  //
  //  ⚠️ Khóa RIÊNG chứ không phải một action của `employee`: `employee.read` là
  //  quyền gần như mọi vai trò đều có (cần để đổ ô chọn người trong form), nhét
  //  nhóm nhạy cảm vào đó là cả công ty đọc được số tài khoản ngân hàng của nhau.
  //
  //  ⚠️ `can('employee_sensitive', 'read')` ở đây CHỈ để ẩn tab/ô cho đỡ vướng
  //  mắt. Backend đã che thẳng ở tầng serializer (`modules/employee/sensitive.py`)
  //  nên thiếu quyền thì các ô đó về rỗng dù giao diện có vẽ ra hay không.
  'employee_sensitive',
  //  Danh mục Chức vụ (duoc-CR-320) — nguồn của ô chọn «Vị trí / Chức vụ».
  //  MỌI vai trò được `read` (seed), quyền sửa dành cho `hr_profile`.
  'job_position',
  //  Điểm cà phê × POS365 (doc/erp/diem-ca-phe/04). Bốn khóa để ba quyền của
  //  PS12 tách được: xem sổ người khác · điều chỉnh tay · chạy đồng bộ.
  //  Ví của tôi KHÔNG cần khóa nào — endpoint riêng chỉ đòi đăng nhập.
  'coffee_policy',
  'coffee_member',
  'coffee_ledger',
  'pos_order',
] as const

export type PermissionEntity = (typeof ENTITIES)[number]

/**
 * `{ entity: { action: true } }`. Backend đôi khi trả chuỗi thay vì boolean ở một số ô
 * nên nới kiểu ra `boolean | string` và luôn ép về boolean khi đọc.
 */
export type PermissionMap = Record<string, Record<string, boolean | string>>
