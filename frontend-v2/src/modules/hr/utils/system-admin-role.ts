/**
 * Vai trò Quản trị hệ thống (bao-CR-523, khách chốt 30/09/2026).
 *
 * - Người giữ vai trò này được TỰ sửa vai trò / phạm vi của mình và sửa ma trận
 *   của vai trò mình đang giữ — backend miễn L1 cho họ
 *   (`core/privilege_escalation.py`). Người khác vẫn bị khóa như cũ.
 * - Ma trận của CHÍNH vai trò này luôn đủ mọi quyền: giao diện chỉ cho xem,
 *   backend từ chối mọi bản làm hụt.
 * - Tự bỏ vai trò này của chính mình: backend trả 409 kèm câu hỏi, giao diện
 *   hiện hộp xác nhận rồi gửi lại kèm `confirm_self_admin_removal: true`.
 *
 * Nhận diện theo MÃ `admin` (chữ thường, khớp chính xác) — không theo tên hiển
 * thị, và vai trò đời cũ `ADMINISTRATOR` KHÔNG được tính.
 */
export const SYSTEM_ADMIN_ROLE_CODE = 'admin'

/** Câu ghi chú dưới tiêu đề ma trận khi đang xem vai trò Quản trị hệ thống. */
export const SYSTEM_ADMIN_FULL_NOTE = 'Vai trò Quản trị hệ thống luôn đủ mọi quyền'

interface RoleCodeLike {
  id: number
  code: string
}

/** Vai trò đang xem có phải vai trò Quản trị hệ thống không. */
export function isSystemAdminRole(role: Pick<RoleCodeLike, 'code'> | null | undefined): boolean {
  return role?.code === SYSTEM_ADMIN_ROLE_CODE
}

/**
 * Tập vai trò `roleIds` có chứa vai trò Quản trị hệ thống không.
 *
 * Danh sách vai trò chưa nạp (hoặc người xem không có `role.read`) thì trả
 * `false` — tức giữ khóa như người thường. Khóa THỪA thì người dùng chỉ phải nhờ
 * người khác; mở THỪA thì họ tick xong mới ăn 403.
 */
export function holdsSystemAdminRole(
  roles: readonly RoleCodeLike[] | null | undefined,
  roleIds: readonly number[] | null | undefined,
): boolean {
  if (!roles || !roleIds?.length) return false
  const adminIds = roles.filter(isSystemAdminRole).map((role) => role.id)
  return adminIds.some((id) => roleIds.includes(id))
}

/**
 * Lỗi này có phải câu hỏi «bạn đang tự bỏ vai trò Quản trị, tiếp tục?» của
 * backend không. Có thì trả NGUYÊN câu backend gửi (một nguồn chữ duy nhất),
 * không thì `null`.
 */
export function readSelfAdminRemovalQuestion(error: unknown): string | null {
  if (!error || typeof error !== 'object') return null
  const response = (error as {
    response?: { status?: number; data?: { error?: { message?: unknown } } }
  }).response
  if (response?.status !== 409) return null
  const message = response.data?.error?.message
  return typeof message === 'string' && message.trim() ? message : null
}
