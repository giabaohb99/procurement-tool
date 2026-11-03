import { render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'

import { RolePermissionMatrix } from './role-permission-matrix'
import type { PermissionMeta, RolePermissionRow } from '@/modules/hr/types/role'
import { TooltipProvider } from '@/shared/ui/tooltip'

//  bao-CR-716: danh mục dùng chung (NCC, sản phẩm...) không lọc theo phạm vi — ô Phạm vi
//  của dòng đó phải KHÓA và nói rõ, còn dòng thường vẫn là ô chọn.
const META: PermissionMeta = {
  entities: [
    { key: 'purchase_request', label: 'Yêu cầu mua hàng' },
    { key: 'supplier', label: 'Nhà cung cấp' },
  ],
  actions: [{ key: 'read', label: 'Xem' }],
  scopes: [
    { key: 'own', label: 'Của mình' },
    { key: 'all', label: 'Tất cả' },
  ],
  public_entities: ['supplier'],
}

const ROWS: Record<string, RolePermissionRow> = {
  purchase_request: { entity: 'purchase_request', scope: 'own', can_read: true },
  supplier: { entity: 'supplier', scope: 'own', can_read: true },
}

function dung(meta: PermissionMeta = META) {
  const onChange = vi.fn()
  render(
    <TooltipProvider>
      <RolePermissionMatrix meta={meta} rows={ROWS} onChange={onChange} />
    </TooltipProvider>,
  )
  return onChange
}

describe('RolePermissionMatrix — ô Phạm vi của danh mục dùng chung', () => {
  it('dòng danh mục dùng chung khóa ô Phạm vi và ghi "Toàn bộ (danh mục dùng chung)"', () => {
    dung()
    expect(screen.getByText('Toàn bộ (danh mục dùng chung)')).toBeInTheDocument()
    expect(
      screen.getByLabelText('Nhà cung cấp — phạm vi khóa: danh mục dùng chung'),
    ).toBeInTheDocument()
    //  Dòng thường vẫn còn ô chọn phạm vi; dòng dùng chung thì không.
    expect(screen.getAllByRole('combobox')).toHaveLength(1)
  })

  it('backend cũ chưa trả public_entities thì mọi dòng vẫn là ô chọn như trước', () => {
    const { public_entities: _bo, ...metaCu } = META
    dung(metaCu)
    expect(screen.queryByText('Toàn bộ (danh mục dùng chung)')).not.toBeInTheDocument()
    expect(screen.getAllByRole('combobox')).toHaveLength(2)
  })
})
