import type { ErpModule } from '@/app/router/module-definition'
import type { PermissionAction, PermissionEntity } from '@/core/authorization/permission-types'

/** Đúng chữ ký của `can` từ `usePermission()`. */
type CanFn = (entity: PermissionEntity, action: PermissionAction) => boolean

/**
 * Người dùng có mở được phân hệ này không.
 *
 * ⚠️ **Không hỏi mỗi `module.entity`.** Một phân hệ mở được khi người dùng thấy
 * được **ít nhất một mục** trong thanh bên của nó — kể cả khi họ không có quyền
 * nào trên `module.entity`.
 *
 * Vì sao phải vậy: có những mục cố ý KHÔNG gác quyền, dành cho người ngoài phân
 * hệ. Rõ nhất là *«Chờ tôi duyệt»* của phân hệ Văn bản — người duyệt trong luồng
 * thường **không có vai trò nào** ở Văn bản, và backend đã mở đúng khe đó
 * (`doc_reader` trong `document/controller.py`).
 *
 * Trước 22/08/2026 màn chọn phân hệ chỉ xét `module.entity`, nên `DEMO_MANAGER`
 * — người ký ở ba trong bốn chặng của luồng ban hành — thấy ô **Văn bản** đeo ổ
 * khóa. Chuông báo 6 việc chờ mà bấm vào phân hệ không được: khe mở cho họ nằm
 * ngay bên trong, nhưng cửa ngoài đã đóng. Ngoại lệ viết cho đúng nhóm người đó
 * thành mã chết.
 *
 * Dùng CHUNG một luật với `ModuleSidebar` — hai nơi tự tính riêng là sớm muộn
 * lại lệch nhau đúng kiểu trên.
 */
export function visibleNavItems(module: ErpModule, can: CanFn) {
  return module.nav.filter((item) => !item.entity || can(item.entity, 'read'))
}

export function canOpenModule(module: ErpModule, can: CanFn) {
  return visibleNavItems(module, can).length > 0
}
