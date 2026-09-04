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
  it('giữ NGUYÊN năm đường dẫn cũ — tab chỉ là thanh điều hướng', () => {
    //  Link trong thư báo việc duyệt trỏ thẳng `/hr/leave-requests/{id}`
    //  (`task_notification.ENTITY_LINKS`). Gộp về một đường `?tab=…` là gãy hết
    //  thư đã gửi lẫn link người dùng dán cho nhau.
    grants = NHAN_SU
    build(appRoutes.hr.leaveRequests)
    const hrefs = screen.getAllByRole('link').map((a) => a.getAttribute('href'))
    expect(hrefs).toContain(appRoutes.hr.leaveRequests)
    expect(hrefs).toContain(appRoutes.hr.leaveCalendar)
    expect(hrefs).toContain(appRoutes.hr.leaveBalances)
    expect(hrefs).toContain(appRoutes.hr.leaveTypes)
  })

  it('người thường KHÔNG thấy tab «Quỹ phép năm» và «Thiết lập»', () => {
    //  Quyền chuyển từ MENU xuống thanh tab này. Bê thiếu luật đó là nhân viên
    //  nhìn thấy cả tab khai danh mục rồi bấm vào ăn 403.
    grants = NHAN_VIEN
    build(appRoutes.hr.leaveRequests)
    expect(screen.queryByRole('link', { name: 'Quỹ phép năm' })).toBeNull()
    expect(screen.queryByRole('link', { name: 'Thiết lập' })).toBeNull()
    expect(screen.getByRole('link', { name: 'Lịch nghỉ' })).toBeInTheDocument()
  })

  it('chỉ có quyền một trong hai danh mục thì vẫn vào được «Thiết lập»', () => {
    grants = [...NHAN_VIEN, 'holiday.write']
    build(appRoutes.hr.leaveRequests)
    expect(screen.getByRole('link', { name: 'Thiết lập' })).toBeInTheDocument()
  })

  it('tab «Thiết lập» SÁNG cả khi đang ở màn Lịch ngày lễ', () => {
    //  Hai màn con một tab: `NavLink` một mình chỉ so đúng đường của chính nó,
    //  nên không có `alsoMatch` thì mở Lịch ngày lễ xong cả hàng tab tối om.
    grants = NHAN_SU
    build(appRoutes.hr.holidays)
    expect(activeLabels()).toContain('Thiết lập')
  })

  it('trong «Thiết lập» thì hiện hàng tab con, ngoài đó thì không', () => {
    grants = NHAN_SU
    build(appRoutes.hr.leaveTypes)
    expect(screen.getByRole('link', { name: 'Lịch ngày lễ' })).toBeInTheDocument()
  })

  it('không đứng trong «Thiết lập» thì không có hàng tab con', () => {
    grants = NHAN_SU
    build(appRoutes.hr.leaveCalendar)
    expect(screen.queryByRole('link', { name: 'Lịch ngày lễ' })).toBeNull()
  })

  it('chỉ sửa được MỘT danh mục thì không dựng hàng tab con một mục', () => {
    //  Một tab thì không phải là tab — người dùng không chuyển đi đâu được.
    grants = [...NHAN_VIEN, 'leave_type.write']
    build(appRoutes.hr.leaveTypes)
    expect(screen.queryByRole('link', { name: 'Loại nghỉ' })).toBeNull()
  })

  it('chỉ còn một tab và không ở Thiết lập thì ẩn hẳn thanh', () => {
    //  Người không có `leave_request.read` (vd chỉ giữ khóa quỹ) thì thanh còn
    //  đúng một mục — vẽ ra chỉ tốn một dòng mà không đi đâu được.
    grants = ['leave_balance.read']
    const { container } = render(
      <MemoryRouter initialEntries={[appRoutes.hr.leaveBalances]}>
        <LeaveSectionTabs />
      </MemoryRouter>,
    )
    expect(container).toBeEmptyDOMElement()
  })
})
