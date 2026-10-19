import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import type { UsageProfileDetail, UsageSnapshot } from '../../types/usage-profile'
import { UsageMetricWithCohort } from './usage-metric-with-cohort'
import { UsageProfileHeaderCard } from './usage-profile-header-card'
import { UsageSecuritySection } from './usage-security-section'
import { UsageStyleLabelsSection } from './usage-style-labels-section'
import { MemoryRouter } from 'react-router-dom'

const baseProfile = (latest: UsageSnapshot | null): UsageProfileDetail => ({
  subject: { user_id: 5, full_name: 'Nguyễn Văn A', emp_code: 'NV005', department_name: 'Kế toán', role_names: ['Kế toán viên'], tenure_days: 120 },
  latest,
  weekly: [],
  daily: [],
  heatmap: [],
  screens: [],
  screens_source: 1,
  metric_meta: {},
  deferred_metrics: [],
  data_since: null,
  tracking_since: null,
})

describe('UsageMetricWithCohort', () => {
  it('shows value, cohort median and trend for a measured metric', () => {
    const snapshot: UsageSnapshot = { metrics: { active_ratio: { v: 0.95, med: 0.9, trend: [0.9, 1, 0.92, 0.95] } } }
    render(<UsageMetricWithCohort snapshot={snapshot} metricKey="active_ratio" />)
    expect(screen.getByText('95%')).toBeInTheDocument()
    expect(screen.getByText(/nhóm: 90%/)).toBeInTheDocument()
    expect(screen.getByLabelText(/Xu hướng tăng/)).toBeInTheDocument()
  })

  it('shows "Chưa đo được" with the reason, never 0, for an unmeasured metric', () => {
    const snapshot: UsageSnapshot = {
      metrics: { notif_read_p50_min: { v: 0 } }, // giá trị rác 0 đi kèm cờ unmeasured: vẫn không được hiện 0
      unmeasured: { notif_read_p50_min: 1 },
    }
    render(<UsageMetricWithCohort snapshot={snapshot} metricKey="notif_read_p50_min" />)
    expect(screen.getByText(/Chưa đo được — chưa thu thập/)).toBeInTheDocument()
    expect(screen.queryByText(/^0/)).not.toBeInTheDocument()
  })

  it('shows "Chưa đo được" when the key is absent or null', () => {
    const snapshot: UsageSnapshot = { metrics: { logins: { v: null } } }
    const { rerender } = render(<UsageMetricWithCohort snapshot={snapshot} metricKey="logins" />)
    expect(screen.getByText(/Chưa đo được/)).toBeInTheDocument()
    rerender(<UsageMetricWithCohort snapshot={snapshot} metricKey="no_such_metric" />)
    expect(screen.getByText(/Chưa đo được/)).toBeInTheDocument()
  })

  it('keeps a real zero as 0', () => {
    render(<UsageMetricWithCohort snapshot={{ metrics: { logins: { v: 0 } } }} metricKey="logins" />)
    expect(screen.getByText('0')).toBeInTheDocument()
  })

  it('shows no trend arrow with fewer than 2 numeric points', () => {
    render(<UsageMetricWithCohort snapshot={{ metrics: { logins: { v: 3, trend: [null, 3, null] } } }} metricKey="logins" />)
    expect(screen.queryByLabelText(/Xu hướng/)).not.toBeInTheDocument()
  })
})

describe('UsageSecuritySection', () => {
  it('says nothing unusual when there are no flags', () => {
    render(<UsageSecuritySection snapshot={{ metrics: { new_ip_logins: { v: 0 } } }} />)
    expect(screen.getByText('Không có gì bất thường')).toBeInTheDocument()
  })

  it('lists a flagged metric instead', () => {
    const snapshot: UsageSnapshot = { metrics: { new_ip_logins: { v: 2 } } }
    render(<UsageSecuritySection snapshot={snapshot} />)
    expect(screen.queryByText('Không có gì bất thường')).not.toBeInTheDocument()
    expect(screen.getByText('Đăng nhập từ IP lạ')).toBeInTheDocument()
  })
})

describe('UsageProfileHeaderCard', () => {
  it('explains why the comparison group is the company when the role group is too small', () => {
    const latest: UsageSnapshot = { metrics: {}, cohort: { kind: 3, key: 0, size: 40, name: '' } }
    render(
      <MemoryRouter>
        <UsageProfileHeaderCard profile={baseProfile(latest)} weeks={8} onWeeksChange={() => {}} />
      </MemoryRouter>,
    )
    expect(screen.getByText(/toàn công ty \(40 người\) vì chưa có vai trò nào đủ 5 người/)).toBeInTheDocument()
    expect(screen.getByText('Nguyễn Văn A')).toBeInTheDocument()
  })
})

describe('UsageStyleLabelsSection', () => {
  it('shows the style, a hint and evidence labels', () => {
    const snapshot: UsageSnapshot = { metrics: {}, labels: [{ code: 2, score: 0.8, evidence: ['approval_wait_p50_h', 'pending_now'] }] }
    render(<UsageStyleLabelsSection snapshot={snapshot} />)
    expect(screen.getByText('Nút thắt duyệt')).toBeInTheDocument()
    expect(screen.getByText(/Tới lượt → xử lý \(giữa\), Đang chờ duyệt/)).toBeInTheDocument()
  })

  it('says so when no style stands out', () => {
    render(<UsageStyleLabelsSection snapshot={{ metrics: {} }} />)
    expect(screen.getByText(/Chưa nhận ra kiểu làm việc nào/)).toBeInTheDocument()
  })

  it('does not crash on an unknown style code', () => {
    const snapshot: UsageSnapshot = { metrics: {}, labels: [{ code: 99, score: 1, evidence: [] }] }
    render(<UsageStyleLabelsSection snapshot={snapshot} />)
    expect(screen.getByText('Kiểu 99')).toBeInTheDocument()
  })
})
