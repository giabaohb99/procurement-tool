import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it } from 'vitest'

import { resolveFormFields } from '@/shared/crud/resolve-form-fields'
import { LEAVE_TYPE_CRUD_CONFIG } from '../config/leave-type-crud'
import { accrualFixture } from './leave-accrual-fixture'
import { AccrualStartTooltip, LeaveAccrualStatusBadge } from './leave-accrual-status-badge'
import { LeaveAccrualStatusNote } from './leave-accrual-status-note'

describe('LeaveAccrualStatusBadge (text = API accrual_status_label)', () => {
  it('muted statuses 2, 5, 6 render the API label as is', () => {
    for (const status of [2, 5, 6]) {
      const info = accrualFixture(status)
      const { unmount } = render(<LeaveAccrualStatusBadge info={info} />)
      expect(screen.getByText(info.accrual_status_label ?? '')).toBeInTheDocument()
      unmount()
    }
  })

  it('renders whatever label the API sends — no hand-typed text in the UI', () => {
    render(<LeaveAccrualStatusBadge info={{ accrual_status: 2, accrual_status_label: 'Nhãn mới từ máy chủ' }} />)
    expect(screen.getByText('Nhãn mới từ máy chủ')).toBeInTheDocument()
  })

  it('status 3 shows the API label and the agreed action sentence on hover', async () => {
    render(<LeaveAccrualStatusBadge info={accrualFixture(3, '2026-03-01')} />)
    const badge = screen.getByText('Chưa có HĐLĐ trên hệ thống')
    await userEvent.hover(badge)
    expect(
      (
        await screen.findAllByText(
          'Chưa có HĐLĐ trên hệ thống. Đang tính từ ngày vào làm — nhập hợp đồng lao động để tính đúng',
        )
      ).length,
    ).toBeGreaterThan(0)
  })

  it('status 4 is amber too, with its own action hint in the accessible name', () => {
    render(<LeaveAccrualStatusBadge info={accrualFixture(4)} />)
    expect(screen.getByLabelText(/^Lịch sử HĐLĐ chưa đủ .*Nhập đủ hợp đồng lao động để tính đúng$/)).toBeInTheDocument()
  })

  it('status 1, null / absent fields, unknown codes and a missing label render nothing', () => {
    for (const info of [
      accrualFixture(1, '2026-02-01'),
      { accrual_status: null, accrual_start_date: null, accrual_status_label: null },
      {},
      null,
      undefined,
      { accrual_status: 99, accrual_status_label: 'Lạ' },
      { accrual_status: 3, accrual_status_label: null },
      { accrual_status: 2, accrual_status_label: '   ' },
    ]) {
      const { container, unmount } = render(<LeaveAccrualStatusBadge info={info} />)
      expect(container).toBeEmptyDOMElement()
      unmount()
    }
  })
})

describe('LeaveAccrualStatusBadge compact (narrow matrix name column)', () => {
  it('draws only an icon; the label lives in the accessible name and the hover hint', async () => {
    const { container } = render(<LeaveAccrualStatusBadge compact info={accrualFixture(2)} />)
    expect(container.textContent).toBe('')
    const badge = screen.getByLabelText('Đang thử việc — chưa tích')
    await userEvent.hover(badge)
    expect((await screen.findAllByText('Đang thử việc — chưa tích')).length).toBeGreaterThan(0)
  })

  it('still renders nothing for accruing / null info', () => {
    for (const info of [accrualFixture(1, '2026-02-01'), null]) {
      const { container, unmount } = render(<LeaveAccrualStatusBadge compact info={info} />)
      expect(container).toBeEmptyDOMElement()
      unmount()
    }
  })
})

describe('LeaveAccrualStatusBadge hideContractWarning (more than half missing, option B)', () => {
  it('hides amber statuses 3 and 4 but always keeps the muted ones', () => {
    for (const status of [3, 4]) {
      const { container, unmount } = render(<LeaveAccrualStatusBadge hideContractWarning info={accrualFixture(status)} />)
      expect(container).toBeEmptyDOMElement()
      unmount()
    }
    for (const status of [2, 5, 6]) {
      const info = accrualFixture(status)
      const { unmount } = render(<LeaveAccrualStatusBadge hideContractWarning info={info} />)
      expect(screen.getByText(info.accrual_status_label ?? '')).toBeInTheDocument()
      unmount()
    }
  })
})

describe('AccrualStartTooltip', () => {
  it('adds no visible text for an accruing employee, only a hover hint with the start date', async () => {
    render(
      <AccrualStartTooltip info={accrualFixture(1, '2026-02-01')}>
        <span>Phép năm</span>
      </AccrualStartTooltip>,
    )
    expect(screen.queryByText(/Tích từ/)).not.toBeInTheDocument()
    await userEvent.hover(screen.getByText('Phép năm'))
    expect((await screen.findAllByText('Tích từ 01/02/2026')).length).toBeGreaterThan(0)
  })

  it('returns the child untouched for other statuses and null info', () => {
    for (const info of [accrualFixture(2), accrualFixture(3, '2026-01-01'), accrualFixture(6, '2027-01-01'), null]) {
      const { container, unmount } = render(
        <AccrualStartTooltip info={info}>
          <span>12</span>
        </AccrualStartTooltip>,
      )
      expect(container.innerHTML).toBe('<span>12</span>')
      unmount()
    }
  })
})

describe('LeaveAccrualStatusNote (balance detail page)', () => {
  it('spells out each tone in a full sentence, since touch screens cannot hover', () => {
    const { rerender, container } = render(<LeaveAccrualStatusNote info={accrualFixture(3, '2026-03-01')} />)
    expect(container.textContent).toBe(
      'Chưa có HĐLĐ trên hệ thống — phép đang tính từ ngày vào làm 01/03/2026. Nhập hợp đồng lao động để tính đúng.',
    )

    rerender(<LeaveAccrualStatusNote info={accrualFixture(4, '2026-03-01')} />)
    expect(container.textContent).toBe(
      'Lịch sử HĐLĐ chưa đủ — đang tính từ ngày vào làm (01/03/2026). Nhập đủ hợp đồng lao động để tính đúng.',
    )

    rerender(<LeaveAccrualStatusNote info={accrualFixture(5)} />)
    expect(container.textContent).toBe('Hợp đồng dịch vụ / cộng tác viên — không tích phép năm.')

    rerender(<LeaveAccrualStatusNote info={accrualFixture(1, '2026-02-01')} />)
    expect(container.textContent).toMatch(/^Tích từ 01\/02\/2026/)
  })

  it('missing contract without any date still reads as a sentence', () => {
    const { container } = render(<LeaveAccrualStatusNote info={accrualFixture(3)} />)
    expect(container.textContent).toMatch(/từ ngày vào làm\. Nhập hợp đồng/)
  })

  it('renders nothing for other accrual modes (all null), accruing without a date, or a missing label', () => {
    for (const info of [
      { accrual_status: null },
      {},
      accrualFixture(1),
      { accrual_status: 3, accrual_status_label: null },
    ]) {
      const { container, unmount } = render(<LeaveAccrualStatusNote info={info} />)
      expect(container).toBeEmptyDOMElement()
      unmount()
    }
  })
})

describe('leave type form: accrual mode field', () => {
  it('offers mode 4 and explains it, including the recalculation on switch', () => {
    const field = resolveFormFields(LEAVE_TYPE_CRUD_CONFIG.formFields, { counts_balance: true }).find(
      (f) => f.name === 'accrual_mode',
    )
    expect(field?.options?.map((o) => o.value)).toEqual([1, 2, 3, 4])
    expect(field?.options?.find((o) => o.value === 4)?.label).toBe('Cộng dần sau mỗi tháng làm đủ')
    expect(field?.hint).toContain('hết tháng 1 → từ 01/02 có 1 ngày')
    expect(field?.hint).toContain('Thời gian thử việc không tích.')
    expect(field?.hint).toContain('Đổi sang chế độ này sẽ tính lại quỹ năm nay theo ngày làm chính thức')
  })
})
