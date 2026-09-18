import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import type { PermissionAction, PermissionEntity } from '@/core/authorization/permission-types'
import { appRoutes } from '@/shared/constants/app-routes'
import { LeaveSectionTabs } from './leave-section-tabs'

//  Cặp «khóa + hành động» mà tài khoản đang thử được phép làm.
let grants: string[] = []

vi.mock('@/core/authorization/use-permission', () => ({
  usePermission: () => ({
    can: (entity: PermissionEntity, action: PermissionAction) =>
      grants.includes(`${entity}.${action}`),
    canAny: () => true,
  }),
}))

/** Quyền của một người NỘP ĐƠN bình thường: xem đơn, không đụng danh mục. */
const NHAN_VIEN = ['leave_request.read']
/** Thêm quyền của Nhân sự: xem quỹ phép và sửa được hai danh mục. */
const NHAN_SU = [...NHAN_VIEN, 'leave_balance.read', 'leave_type.write', 'holiday.write']

function build(pathname: string) {
  render(
    <MemoryRouter initialEntries={[pathname]}>
      <LeaveSectionTabs />
    </MemoryRouter>,
  )
}

/** Tab đang mở = link mang `aria-current="page"` do `NavLink` gắn. */
function activeLabels() {
  return screen
    .getAllByRole('link')
    .filter((a) => a.getAttribute('aria-current') === 'page')
    .map((a) => a.textContent)
}

beforeEach(() => {
  grants = []
})

describe('LeaveSectionTabs', () => {
  it('trong «Thiết lập» thì hiện hai tab con Loại nghỉ và Lịch ngày lễ', () => {
    grants = NHAN_SU
    build(appRoutes.hr.leaveTypes)
    expect(screen.getByRole('link', { name: 'Loại nghỉ' })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Lịch ngày lễ' })).toBeInTheDocument()
  })

  it('tab «Lịch ngày lễ» SÁNG khi đang ở màn Lịch ngày lễ', () => {
    grants = NHAN_SU
    build(appRoutes.hr.holidays)
    expect(activeLabels()).toContain('Lịch ngày lễ')
  })

  it('không đứng trong «Thiết lập» thì ẩn hẳn thanh', () => {
    grants = NHAN_SU
    const { container } = render(
      <MemoryRouter initialEntries={[appRoutes.hr.leaveCalendar]}>
        <LeaveSectionTabs />
      </MemoryRouter>,
    )
    expect(container).toBeEmptyDOMElement()
  })

  it('người thường KHÔNG thấy tab con Thiết lập', () => {
    grants = NHAN_VIEN
    const { container } = render(
      <MemoryRouter initialEntries={[appRoutes.hr.leaveTypes]}>
        <LeaveSectionTabs />
      </MemoryRouter>,
    )
    expect(container).toBeEmptyDOMElement()
  })

  it('chỉ sửa được MỘT danh mục thì không dựng hàng tab một mục', () => {
    // Một tab thì không phải là tab — người dùng không chuyển đi đâu được.
    grants = [...NHAN_VIEN, 'leave_type.write']
    const { container } = render(
      <MemoryRouter initialEntries={[appRoutes.hr.leaveTypes]}>
        <LeaveSectionTabs />
      </MemoryRouter>,
    )
    expect(container).toBeEmptyDOMElement()
  })
})
