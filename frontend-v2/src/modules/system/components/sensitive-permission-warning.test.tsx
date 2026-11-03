import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { SensitivePermissionWarning } from './sensitive-permission-warning'
import type { PermissionMeta, Role, RolePermissionRow } from '@/modules/hr/types/role'

const META: PermissionMeta = {
  entities: [
    { key: 'supplier', label: 'Nhà cung cấp' },
    { key: 'contract', label: 'Hợp đồng' },
    { key: 'vehicle', label: 'Xe cộ' },
  ],
  actions: [
    { key: 'read', label: 'Xem' },
    { key: 'write', label: 'Sửa' },
    { key: 'export', label: 'Xuất' },
  ],
  scopes: [{ key: 'own', label: 'Của mình' }],
  sensitive_entities: ['supplier', 'contract'],
  sensitive_actions: ['read', 'export'],
  requester_role_codes: ['employee'],
}
const EMPLOYEE: Role = { id: 2, code: 'employee', name: 'Nhân sự', description: '', sort_order: 2, user_count: 232 }
const BUYER: Role = { id: 7, code: 'pur_staff', name: 'Nhân viên thu mua', description: '', sort_order: 7, user_count: 5 }
const ROWS: Record<string, RolePermissionRow> = {
  supplier: { entity: 'supplier', scope: 'all', can_read: true, can_export: true },
  contract: { entity: 'contract', scope: 'all', can_write: true },
  vehicle: { entity: 'vehicle', scope: 'all', can_read: true },
}

describe('SensitivePermissionWarning (bao-CR-720)', () => {
  it('vai trò người yêu cầu có Xem/Xuất ở entity nhạy cảm → dòng vàng nêu quyền + số người giữ', () => {
    render(<SensitivePermissionWarning meta={META} role={EMPLOYEE} rows={ROWS} />)
    const box = screen.getByRole('status')
    expect(box).toHaveTextContent('232 người đang giữ')
    expect(box).toHaveTextContent('Nhà cung cấp (Xem, Xuất)')
    //  Hợp đồng chỉ có Sửa (không thuộc hành động cần nhắc) và Xe cộ không nhạy cảm: không nêu.
    expect(box).not.toHaveTextContent('Hợp đồng')
    expect(box).not.toHaveTextContent('Xe cộ')
  })

  it('vai trò khác (không phải người yêu cầu) thì không hiện dù tick y hệt', () => {
    render(<SensitivePermissionWarning meta={META} role={BUYER} rows={ROWS} />)
    expect(screen.queryByRole('status')).not.toBeInTheDocument()
  })

  it('người yêu cầu nhưng không tick gì nhạy cảm, hay backend cũ chưa trả danh sách → không hiện', () => {
    const { unmount } = render(
      <SensitivePermissionWarning meta={META} role={EMPLOYEE} rows={{ vehicle: ROWS.vehicle }} />,
    )
    expect(screen.queryByRole('status')).not.toBeInTheDocument()
    unmount()
    const { sensitive_entities: _a, sensitive_actions: _b, requester_role_codes: _c, ...metaCu } = META
    render(<SensitivePermissionWarning meta={metaCu} role={EMPLOYEE} rows={ROWS} />)
    expect(screen.queryByRole('status')).not.toBeInTheDocument()
  })
})
