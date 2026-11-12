import { cleanup, render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import type { PermissionAction, PermissionEntity } from '@/core/authorization/permission-types'
import { HrSetupTabs } from './hr-setup-tabs'

//  Cặp "khóa.hành động" tài khoản đang thử được phép làm.
let grants: string[] = []

vi.mock('@/core/authorization/use-permission', () => ({
  usePermission: () => ({
    can: (entity: PermissionEntity, action: PermissionAction) => grants.includes(`${entity}.${action}`),
    canAny: () => true,
  }),
  useNavContext: () => ({}),
}))

function build(pathname: string) {
  render(
    <MemoryRouter initialEntries={[pathname]}>
      <HrSetupTabs />
    </MemoryRouter>,
  )
}

function tabLabels() {
  return screen.queryAllByRole('link').map((a) => a.textContent)
}

function activeLabels() {
  return screen
    .queryAllByRole('link')
    .filter((a) => a.getAttribute('aria-current') === 'page')
    .map((a) => a.textContent)
}

beforeEach(() => {
  grants = []
})

const ADMIN = [
  'setting.read',
  'leave_balance.write',
  'leave_type.write',
  'holiday.write',
  'work_schedule.write',
  'meeting_room.write',
]

describe('HrSetupTabs (duoc-CR-754)', () => {
  it('shows ONE flat row of nine screens for an HR admin — no tab inside a tab', () => {
    grants = ADMIN
    build('/hr/settings')
    expect(tabLabels()).toEqual([
      'Cài đặt nhân sự',
      'Phân bổ chính sách',
      'Gói chính sách',
      'Loại nghỉ',
      'Lịch ngày lễ',
      'Ngày cấm nghỉ',
      'Mẫu lịch tuần',
      'Gán lịch',
      'Danh mục phòng họp',
    ])
    expect(activeLabels()).toEqual(['Cài đặt nhân sự'])
  })

  it('hides tabs the user cannot open: read-only rights from the seed never count as setup rights', () => {
    //  Seed cấp đọc quỹ phép / danh mục phòng / lịch cho MỌI nhân viên — không được lộ ra tab nào.
    grants = ['leave_balance.read', 'meeting_room.read', 'work_schedule.read', 'work_schedule.write', 'setting.read']
    build('/hr/work-schedules')
    expect(tabLabels()).toEqual(['Cài đặt nhân sự', 'Mẫu lịch tuần', 'Gán lịch'])
  })

  it('splits the old leave-type strip by right: holiday.write alone opens only Lịch ngày lễ, leave_type.write opens Loại nghỉ + Ngày cấm nghỉ + Gói chính sách', () => {
    grants = ['setting.read', 'holiday.write']
    build('/hr/holidays')
    expect(tabLabels()).toEqual(['Cài đặt nhân sự', 'Lịch ngày lễ'])

    cleanup()
    grants = ['setting.read', 'leave_type.write']
    build('/hr/leave-types')
    expect(tabLabels()).toEqual(['Cài đặt nhân sự', 'Gói chính sách', 'Loại nghỉ', 'Ngày cấm nghỉ'])
  })

  it.each([
    ['/hr/holidays/3', 'Lịch ngày lễ'],
    ['/hr/leave-blocks/new', 'Ngày cấm nghỉ'],
    ['/hr/leave-types', 'Loại nghỉ'],
    ['/hr/leave-policy-assignments', 'Phân bổ chính sách'],
    ['/hr/leave-policy-assignments?tab=policies', 'Gói chính sách'],
    ['/hr/leave-policy-assignments?tab=%3Cx%3E', 'Phân bổ chính sách'],
    ['/hr/leave-policy-assignments/bulk', 'Phân bổ chính sách'],
    ['/hr/leave-policies/7', 'Gói chính sách'],
    ['/hr/meeting-rooms/2', 'Danh mục phòng họp'],
  ])('lights exactly one tab on %s', (path, label) => {
    grants = ADMIN
    build(path)
    expect(activeLabels()).toEqual([label])
  })

  it('a policy-only writer on the merged screen sees Gói chính sách lit, never Phân bổ', () => {
    grants = ['setting.read', 'leave_type.write']
    build('/hr/leave-policy-assignments?tab=assignments')
    expect(activeLabels()).toEqual(['Gói chính sách'])
  })

  it('renders nothing when only one setup screen is open to the user', () => {
    grants = ['meeting_room.write']
    build('/hr/meeting-rooms')
    expect(tabLabels()).toEqual([])
  })

  it('renders nothing for an ordinary employee', () => {
    grants = ['employee.read', 'leave_request.read', 'leave_balance.read', 'meeting_room.read']
    build('/hr/settings')
    expect(tabLabels()).toEqual([])
  })
})
