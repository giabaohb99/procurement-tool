import type { ErpModule } from '@/app/router/module-definition'
import type { PermissionAction, PermissionEntity } from '@/core/authorization/permission-types'

/** Đúng chữ ký của `can` từ `usePermission()`. */
type CanFn = (entity: PermissionEntity, action: PermissionAction) => boolean

/**
 * Kiểm tra quyền quản lý danh mục / hệ thống (yêu cầu ít nhất 1 trong 3 quyền: tạo, sửa, xóa).
 * Quyền `read` thuần túy chỉ dùng để đổ dropdown trên form, không cho hiện menu quản lý danh mục.
 */
export function canManageEntity(entity: PermissionEntity, can: CanFn): boolean {
  return can(entity, 'create') || can(entity, 'write') || can(entity, 'delete')
}

/**
 * Lọc mục thanh bên theo quyền:
 * - khai `action` -> hỏi đúng hành động đó;
 * - khai `manage: true` -> hỏi `canManageEntity`;
 * - còn lại -> hỏi `read`.
 *
 * ⚠️ **Mục KHÔNG khai `entity` thì luôn hiện** — đó là chủ ý, không phải sót.
 * Có những mục dành cho người NGOÀI phân hệ. Rõ nhất là *«Chờ tôi duyệt»* của
 * phân hệ Văn bản: người duyệt trong luồng thường **không có vai trò nào** ở Văn
 * bản, và backend đã mở đúng khe đó (`doc_reader` trong `document/controller.py`).
 *
 * Cũng vì vậy `canOpenModule` **không hỏi mỗi `module.entity`**. Trước 22/08/2026
 * màn chọn phân hệ chỉ xét `module.entity`, nên `DEMO_MANAGER` — người ký ở ba
 * trong bốn chặng của luồng ban hành — thấy ô **Văn bản** đeo ổ khóa. Chuông báo
 * 6 việc chờ mà bấm vào phân hệ không được: khe mở cho họ nằm ngay bên trong,
 * nhưng cửa ngoài đã đóng. Ngoại lệ viết cho đúng nhóm người đó thành mã chết.
 *
 * Dùng CHUNG một luật với `ModuleSidebar` — hai nơi tự tính riêng là sớm muộn
 * lại lệch nhau đúng kiểu trên.
 */
export function visibleNavItems(module: ErpModule, can: CanFn) {
  return module.nav.filter((item) => {
    if (!item.entity) return true
    if (item.action) return can(item.entity, item.action)
    if (item.manage) return canManageEntity(item.entity, can)
    return can(item.entity, 'read')
  })
}

export function canOpenModule(module: ErpModule, can: CanFn) {
  return visibleNavItems(module, can).length > 0
}
