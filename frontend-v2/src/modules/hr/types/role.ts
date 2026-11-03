/** Vai trò — khớp `RoleOut` của backend (`modules/role/schema.py`). */
export interface Role {
  id: number
  code: string
  name: string
  description: string
  /** Thứ tự hiện do người quản trị kéo thả. Vai trò chưa xếp thì là 0. */
  sort_order: number
  /**
   * Số tài khoản đang giữ vai trò — chỉ có ở `GET /api/roles` (bao-CR-428),
   * các đường trả một vai trò (tạo, sửa) không kèm.
   */
  user_count?: number
  /**
   * Ô đã tick của vai trò, khóa theo entity, giá trị là danh sách hành động
   * (`{ purchase_order: ['read', 'create'] }`). Cùng nguồn với `user_count`.
   * Chỉ dùng để in chip phân hệ ở cột trái; ma trận thật vẫn đọc từ
   * `/api/roles/{id}/permissions`.
   */
  granted?: Record<string, string[]>
}

/** Một cặp key/label do backend trả ở `/api/roles/meta`. */
export interface PermissionOption {
  key: string
  label: string
}

/**
 * Danh sách entity × action × scope dựng ma trận phân quyền. Lấy từ backend
 * thay vì hằng số ở frontend để thêm entity mới không phải sửa hai nơi.
 */
export interface PermissionMeta {
  entities: PermissionOption[]
  actions: PermissionOption[]
  scopes: PermissionOption[]
  /**
   * bao-CR-716: entity là danh mục dùng chung mọi pháp nhân (khai `PUBLIC` ở
   * `SCOPE_FIELDS` backend) — ô Phạm vi không có tác dụng, ai được tick quyền là
   * thấy toàn bộ. Màn Phân quyền khóa ô Phạm vi của những dòng này. Tùy chọn để
   * backend cũ chưa trả vẫn chạy.
   */
  public_entities?: string[]
  /**
   * bao-CR-720: entity nhạy cảm của thu mua + hành động cần nhắc (Xem / Xuất) + mã
   * vai trò người yêu cầu (mọi tài khoản mới tự nhận). Vai trò đó được tick ở đây
   * thì màn hiện dòng vàng, không chặn lưu. Khai ở backend, giao diện chỉ đọc.
   */
  sensitive_entities?: string[]
  sensitive_actions?: string[]
  requester_role_codes?: string[]
}

/**
 * Một dòng quyền của vai trò. Backend đặt tên cột theo dạng `can_<action>` nên
 * ở đây để index signature — action nào có trong meta thì đọc bằng `can_${key}`.
 */
export interface RolePermissionRow {
  entity: string
  scope: string
  [action: `can_${string}`]: boolean | string
}

/** Khóa cột quyền trong payload, vd `read` -> `can_read`. */
export function permissionField(action: string): `can_${string}` {
  return `can_${action}`
}
