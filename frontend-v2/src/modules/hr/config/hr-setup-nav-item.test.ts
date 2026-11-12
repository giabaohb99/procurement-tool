import { describe, expect, it } from 'vitest'

import type { PermissionAction, PermissionEntity } from '@/core/authorization/permission-types'
import { canAccessRoute, visibleNavItems } from '@/app/router/module-visibility'
import { hrModule } from '../routes'

/** duoc-CR-753: menu Nhân sự là một danh sách xếp từ trên xuống (không tiêu đề nhóm), mọi màn cấu hình gom vào MỘT cụm Thiết lập. */

function makeCan(perms: Partial<Record<PermissionEntity, readonly PermissionAction[]>>) {
  return (entity: PermissionEntity, action: PermissionAction = 'read') => perms[entity]?.includes(action) ?? false
}

const allowEverything = () => true

describe('bố cục menu Nhân sự (duoc-CR-753)', () => {
  it('is one flat top-to-bottom list without group headings, setup items last', () => {
    //  Anh Được chốt 12/11/2026: không chia tiêu đề nhóm, chỉ xếp từ trên xuống.
    const items = visibleNavItems(hrModule, allowEverything).filter((i) => !i.hidden)
    expect(items.some((i) => i.group)).toBe(false)
    expect(items.map((i) => i.label)).toEqual([
      'Tổng quan',
      'Nhân sự',
      'Duyệt sửa hồ sơ',
      'Sơ đồ tổ chức',
      'Nghỉ phép',
      'Lịch làm việc',
      'Đặt phòng họp',
      'Danh mục',
      'Thiết lập',
    ])
  })

  it('no longer shows the English word Master anywhere in the menu', () => {
    const labels = hrModule.nav.flatMap((i) => [i.label, ...(i.children ?? []).map((c) => c.label)])
    expect(labels.some((l) => /master/i.test(l))).toBe(false)
    expect(labels).toContain('Danh mục')
  })

  it('collects all six setup screens under one Thiết lập item shown as tabs, Cài đặt nhân sự first', () => {
    const setup = visibleNavItems(hrModule, allowEverything).find((i) => i.label === 'Thiết lập')
    //  Anh Được chốt 12/11/2026: một mục menu, vào trong chia tab — không sổ xuống.
    expect(setup?.childrenAsTabs).toBe(true)
    expect(setup?.children?.map((c) => c.label)).toEqual([
      'Cài đặt nhân sự',
      'Chính sách nghỉ phép',
      'Loại nghỉ và ngày lễ',
      'Mẫu lịch tuần',
      'Gán lịch',
      'Danh mục phòng họp',
    ])
  })

  it('keeps setup screens out of the operational items so they do not show twice', () => {
    const items = visibleNavItems(hrModule, allowEverything)
    const childrenOf = (label: string) => items.find((i) => i.label === label)?.children?.map((c) => c.label) ?? []
    expect(childrenOf('Danh mục')).toEqual(['Phòng ban', 'Công ty', 'Chức vụ', 'Mẫu hợp đồng'])
    expect(childrenOf('Đặt phòng họp')).toEqual(['Lịch phòng họp', 'Phiếu đặt phòng'])
    expect(childrenOf('Nghỉ phép')).not.toContain('Chính sách nghỉ phép')
    expect(items.find((i) => i.label === 'Lịch làm việc')?.children).toBeUndefined()
  })

  it('an ordinary employee sees no Thiết lập item at all', () => {
    //  Seed cấp cho MỌI nhân viên: đọc hồ sơ, đọc quỹ phép "của tôi", đọc danh mục phòng họp / chức vụ / lịch.
    const can = makeCan({
      employee: ['read'],
      leave_request: ['read', 'create'],
      leave_balance: ['read'],
      leave_type: ['read'],
      holiday: ['read'],
      work_schedule: ['read'],
      meeting_room: ['read'],
      room_booking: ['read', 'create'],
      job_position: ['read'],
    })
    const items = visibleNavItems(hrModule, can)
    expect(items.some((i) => i.label === 'Thiết lập')).toBe(false)
    expect(items.find((i) => i.label === 'Danh mục')).toBeUndefined()
  })

  it('a meeting-room admin with no other setup right lands on Danh mục phòng họp when clicking Thiết lập', () => {
    //  Bấm mục cha mở mục con ĐẦU TIÊN còn lại sau khi lọc quyền — không được đẩy người dùng vào Cài đặt nhân sự.
    const setup = visibleNavItems(hrModule, makeCan({ meeting_room: ['read', 'write'] })).find(
      (i) => i.label === 'Thiết lập',
    )
    expect(setup?.children?.map((c) => c.path)).toEqual(['/hr/meeting-rooms'])
  })

  it.each([
    ['/hr/settings', { setting: ['read'] }, { employee: ['read', 'write'] }],
    ['/hr/meeting-rooms', { meeting_room: ['write'] }, { meeting_room: ['read'], room_booking: ['read', 'create'] }],
    ['/hr/work-schedules', { work_schedule: ['write'] }, { work_schedule: ['read'], employee: ['read'] }],
    ['/hr/work-schedule-assignments', { work_schedule: ['create'] }, { work_schedule: ['read'] }],
    ['/hr/leave-types', { leave_type: ['write'] }, { leave_type: ['read'], leave_request: ['read'] }],
    ['/hr/holidays', { holiday: ['write'] }, { holiday: ['read'] }],
    ['/hr/leave-policy-assignments', { leave_balance: ['write'] }, { leave_balance: ['read'] }],
  ] as const)('route guard of %s is unchanged after the move', (path, granted, denied) => {
    expect(canAccessRoute(hrModule, path, makeCan(granted))).toBe(true)
    expect(canAccessRoute(hrModule, path, makeCan(denied))).toBe(false)
    expect(canAccessRoute(hrModule, path, makeCan({}))).toBe(false)
  })
})
