import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import type { LeaveGlance } from '../hooks/use-hr-leave-glance'
import type { HrOverview } from '../hooks/use-hr-overview'
import { HrOverviewStats } from './hr-overview-stats'

function makeOverview(overrides: Partial<HrOverview> = {}): HrOverview {
  return {
    stats: { active: 0, inactive: 0, departments: 0, companies: 0, newHires: 0 },
    orgHint: undefined,
    byDepartment: [],
    byCompany: [],
    byStatus: [],
    gaps: { total: 0, noDepartment: 0, noManager: 0, noHireDate: 0, noPosition: 0 },
    accounts: {
      withAccount: 0,
      withoutAccount: 0,
      totalActive: 0,
      noRole: 0,
      orphan: 0,
      totalAccounts: 0,
    },
    isLoading: false,
    isLoadingAccounts: false,
    canReadEmployees: true,
    canReadAccounts: true,
    ...overrides,
  }
}

function makeLeave(overrides: Partial<LeaveGlance> = {}): LeaveGlance {
  return {
    pending: 0,
    upcoming: [],
    offToday: 0,
    today: '2026-09-19',
    canRead: true,
    isLoading: false,
    isLoadingPending: false,
    ...overrides,
  }
}

describe('HrOverviewStats', () => {
  it('nói rõ "không có quyền xem" thay vì khẳng định hồ sơ đã khai đủ', () => {
    //  Thiếu `employee.read` thì `useHrOverview` tắt truy vấn, mọi con số về 0.
    //  0 ở đây KHÔNG phải "không có ai" — thẻ phải nói ra, nếu không người dùng
    //  đọc «Hồ sơ cần bổ sung 0 — Đã khai đủ» và tin là thật (bắt được khi bấm
    //  tay trên trình duyệt, 19/09/2026).
    render(
      <HrOverviewStats
        overview={makeOverview({ canReadEmployees: false })}
        leave={makeLeave()}
      />,
    )

    expect(screen.queryByText('Đã khai đủ')).toBeNull()
    expect(screen.queryByText('Tính theo ngày vào làm')).toBeNull()
    //  Ba ô hồ sơ nhân sự (đang làm việc · mới vào · cần bổ sung).
    expect(screen.getAllByText('Không có quyền xem')).toHaveLength(3)
  })

  it('giữ nguyên câu chú thích thật khi có quyền đọc hồ sơ', () => {
    render(
      <HrOverviewStats
        overview={makeOverview({ stats: { active: 12, inactive: 1, departments: 3, companies: 2, newHires: 4 }, orgHint: '3 phòng ban · 2 pháp nhân' })}
        leave={makeLeave()}
      />,
    )

    expect(screen.getByText('3 phòng ban · 2 pháp nhân')).toBeTruthy()
    expect(screen.getByText('Tính theo ngày vào làm')).toBeTruthy()
    expect(screen.getByText('Đã khai đủ')).toBeTruthy()
    expect(screen.queryByText('Không có quyền xem')).toBeNull()
  })
})
