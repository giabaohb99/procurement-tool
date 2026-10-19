import type { PermissionAction, PermissionEntity } from '@/core/authorization/permission-types'

/** Giá trị `?kind=` chọn mục «Mẫu hợp đồng lao động» trong tab Thư viện văn bản mẫu (duoc-CR-629b). */
export const LABOR_CONTRACT_KIND = 'labor-contract'
/** Tab chứa thư viện mẫu — nơi mẫu HĐLĐ đặt. */
export const TEMPLATES_TAB = 'templates'

type CanFn = (entity: PermissionEntity, action: PermissionAction) => boolean

/** Bốn khóa danh mục Văn bản; có quyền QUẢN LÝ bất kỳ khóa nào là «người quản lý danh mục Văn bản». */
const DOCUMENT_CATALOG_ENTITIES: PermissionEntity[] = [
  'doc_type',
  'doc_template',
  'security_level',
  'external_party',
]

export interface SettingsTabInput {
  value: string
  entity: PermissionEntity
}

export interface SettingsView {
  /** Các tab hiện, theo thứ tự khai. */
  visible: string[]
  /** Tab đang mở (undefined = không có tab nào xem được). */
  current: string | undefined
  /** Tab thư viện mẫu đang hiện mục HĐLĐ (thay vì mẫu văn bản thường). */
  laborContract: boolean
  /** Hiện công tắc «Văn bản mẫu | Mẫu hợp đồng lao động» (người có cả hai quyền). */
  showKindSwitch: boolean
}

/**
 * Luật chọn tab của trang Thiết lập văn bản — hàm thuần để test.
 *
 * - Người KHÔNG quản lý danh mục Văn bản nhưng đọc được `labor_contract_template` (Nhân sự):
 *   chỉ một tab «Thư viện văn bản mẫu» và chỉ mục HĐLĐ, bất kể `?tab=`/`?kind=`.
 * - Thiếu `labor_contract_template.read`: `?kind=labor-contract` bị bỏ qua (về thư viện thường).
 * - Có cả hai: đủ tab + công tắc, `?kind=` được giữ.
 */
export function resolveSettingsView(
  tabs: SettingsTabInput[],
  can: CanFn,
  canManage: (entity: PermissionEntity) => boolean,
  tab: string,
  kind: string,
): SettingsView {
  const canLct = can('labor_contract_template', 'read')
  const docManager = DOCUMENT_CATALOG_ENTITIES.some(canManage)

  if (!docManager && canLct) {
    return { visible: [TEMPLATES_TAB], current: TEMPLATES_TAB, laborContract: true, showKindSwitch: false }
  }

  const visible = tabs.filter((t) => can(t.entity, 'read')).map((t) => t.value)
  const current = visible.find((v) => v === tab) ?? visible[0]
  const onTemplates = current === TEMPLATES_TAB
  return {
    visible,
    current,
    laborContract: onTemplates && canLct && kind === LABOR_CONTRACT_KIND,
    showKindSwitch: onTemplates && canLct,
  }
}
