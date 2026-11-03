import { TriangleAlert } from 'lucide-react'

import type { PermissionMeta, Role, RolePermissionRow } from '@/modules/hr/types/role'
import { permissionField } from '@/modules/hr/types/role'

interface SensitivePermissionWarningProps {
  meta: PermissionMeta
  role: Role | null
  rows: Record<string, RolePermissionRow>
}

/**
 * bao-CR-720 — dòng vàng dưới ma trận: vai trò NGƯỜI YÊU CẦU (mọi tài khoản mới tự
 * nhận, hàng trăm người giữ) đang được tick Xem / Xuất ở entity nhạy cảm của thu mua.
 *
 * Danh sách entity, hành động và mã vai trò đều do backend trả trong `meta`
 * (`core/permissions.py`), ở đây chỉ đọc — backend cũ chưa trả thì không hiện gì.
 * Chỉ nhắc, KHÔNG chặn lưu: có lúc cố ý cho mọi người xem (vd danh mục NCC công khai
 * nội bộ), quyết định là của người quản trị.
 */
export function SensitivePermissionWarning({ meta, role, rows }: SensitivePermissionWarningProps) {
  if (!role || !meta.requester_role_codes?.includes(role.code)) return null
  const actions = meta.sensitive_actions ?? []
  const actionLabel = new Map(meta.actions.map((a) => [a.key, a.label]))
  const entityLabel = new Map(meta.entities.map((e) => [e.key, e.label]))

  const hits = (meta.sensitive_entities ?? [])
    .map((entity) => {
      const row = rows[entity]
      const granted = row ? actions.filter((a) => !!row[permissionField(a)]) : []
      return granted.length > 0
        ? `${entityLabel.get(entity) ?? entity} (${granted.map((a) => actionLabel.get(a) ?? a).join(', ')})`
        : null
    })
    .filter((x): x is string => x !== null)
  if (hits.length === 0) return null

  const holders = role.user_count ?? 0
  return (
    <div
      role="status"
      className="flex items-start gap-2 rounded-md border border-amber-300 bg-amber-50 px-3 py-2 text-sm text-amber-900 dark:border-amber-700 dark:bg-amber-950/40 dark:text-amber-100"
    >
      <TriangleAlert className="mt-0.5 size-4 shrink-0" />
      <p>
        <strong>{role.name}</strong> là vai trò người yêu cầu, mọi tài khoản mới tự nhận.{' '}
        <strong>{holders} người đang giữ</strong> sẽ thấy toàn bộ dữ liệu này: {hits.join('; ')}. Muốn chỉ
        một nhóm thấy thì bỏ tick ở đây và tick cho vai trò riêng của nhóm đó.
      </p>
    </div>
  )
}
