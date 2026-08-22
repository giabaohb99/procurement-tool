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
  'doc_type',
  'external_party',
  'document_book',
  'document',
  'security_level',
  // Bộ máy phê duyệt dùng chung — không thuộc phân hệ nào.
  'approval_flow',
] as const

export type PermissionEntity = (typeof ENTITIES)[number]

/**
 * `{ entity: { action: true } }`. Backend đôi khi trả chuỗi thay vì boolean ở một số ô
 * nên nới kiểu ra `boolean | string` và luôn ép về boolean khi đọc.
 */
export type PermissionMap = Record<string, Record<string, boolean | string>>
