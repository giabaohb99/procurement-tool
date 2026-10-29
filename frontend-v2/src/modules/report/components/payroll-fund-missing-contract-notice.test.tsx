import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import type { ReportMeta } from '../types/report-analytics'
import { PayrollFundMissingContractNotice } from './payroll-fund-missing-contract-notice'

const BASE: ReportMeta = { metrics: [], dimensions: [], group_by: 'company' }

describe('PayrollFundMissingContractNotice', () => {
  it('says how many working people are left out of the payroll fund', () => {
    render(<PayrollFundMissingContractNotice meta={{ ...BASE, people_without_contract: 1264 } as ReportMeta} />)
    expect(
      screen.getByText('1.264 người đang làm chưa có hợp đồng lao động hiệu lực — quỹ lương chưa gồm họ.'),
    ).toBeInTheDocument()
  })

  it('renders nothing when the count is zero or the server left it out (no employee read)', () => {
    const { container, rerender } = render(
      <PayrollFundMissingContractNotice meta={{ ...BASE, people_without_contract: 0 } as ReportMeta} />,
    )
    expect(container).toBeEmptyDOMElement()
    rerender(<PayrollFundMissingContractNotice meta={BASE} />)
    expect(container).toBeEmptyDOMElement()
  })
})
