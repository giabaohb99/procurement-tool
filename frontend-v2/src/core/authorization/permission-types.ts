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
] as const

export type PermissionEntity = (typeof ENTITIES)[number]

/**
 * `{ entity: { action: true } }`. Backend đôi khi trả chuỗi thay vì boolean ở một số ô
 * nên nới kiểu ra `boolean | string` và luôn ép về boolean khi đọc.
 */
export type PermissionMap = Record<string, Record<string, boolean | string>>
