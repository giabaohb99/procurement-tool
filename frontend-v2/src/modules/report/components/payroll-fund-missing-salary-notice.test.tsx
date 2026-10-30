import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import type { ReportMeta } from '../types/report-analytics'
import { PayrollFundMissingSalaryNotice } from './payroll-fund-missing-salary-notice'

const BASE: ReportMeta = { metrics: [], dimensions: [], group_by: 'company' }

describe('PayrollFundMissingSalaryNotice', () => {
  it('says how many working people are left out of the payroll fund', () => {
    render(<PayrollFundMissingSalaryNotice meta={{ ...BASE, people_without_salary: 1264 } as ReportMeta} />)
    expect(
      screen.getByText('1.264 người đang làm chưa nhập lương — quỹ lương chưa gồm họ.'),
    ).toBeInTheDocument()
  })

  it('renders nothing when the count is zero, negative, null or left out by the server', () => {
    const { container, rerender } = render(
      <PayrollFundMissingSalaryNotice meta={{ ...BASE, people_without_salary: 0 } as ReportMeta} />,
    )
    expect(container).toBeEmptyDOMElement()
    rerender(<PayrollFundMissingSalaryNotice meta={{ ...BASE, people_without_salary: -3 } as ReportMeta} />)
    expect(container).toBeEmptyDOMElement()
    rerender(<PayrollFundMissingSalaryNotice meta={{ ...BASE, people_without_salary: null } as ReportMeta} />)
    expect(container).toBeEmptyDOMElement()
    rerender(<PayrollFundMissingSalaryNotice meta={BASE} />)
    expect(container).toBeEmptyDOMElement()
  })

  it('ignores the old contract-based key — the fund no longer reads labor contracts', () => {
    // duoc-CR-692 đọc `people_without_contract`; từ CR-693 nguồn là ô lương hồ sơ, khóa cũ không còn nghĩa.
    const { container } = render(
      <PayrollFundMissingSalaryNotice meta={{ ...BASE, people_without_contract: 5 } as ReportMeta} />,
    )
    expect(container).toBeEmptyDOMElement()
  })
})
