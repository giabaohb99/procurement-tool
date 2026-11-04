import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { describeBlockConflicts, formatBlockRange } from '../utils/leave-block-conflicts'
import { LeaveBlockWarningBanner } from './leave-block-warning-banner'

const ONE = { id: 1, from_date: '2026-12-20', to_date: '2026-12-31', reason: 'Chốt sổ cuối năm' }
const DAY = { id: 2, from_date: '2026-12-24', to_date: '2026-12-24', reason: '' }

describe('formatBlockRange / describeBlockConflicts', () => {
  it('khoảng nhiều ngày hiện hai đầu dd/mm/yyyy, một ngày hiện một ngày', () => {
    expect(formatBlockRange(ONE)).toBe('20/12/2026 – 31/12/2026')
    expect(formatBlockRange(DAY)).toBe('24/12/2026')
  })

  it('mỗi khoảng một dòng, có lý do thì nối sau dấu chấm giữa', () => {
    expect(describeBlockConflicts([ONE, DAY])).toEqual([
      '20/12/2026 – 31/12/2026 · Chốt sổ cuối năm',
      '24/12/2026',
    ])
    expect(describeBlockConflicts(undefined)).toEqual([])
  })
})

describe('LeaveBlockWarningBanner', () => {
  it('không có xung đột (rỗng / thiếu) thì không dựng gì', () => {
    const { container, rerender } = render(<LeaveBlockWarningBanner conflicts={[]} />)
    expect(container).toBeEmptyDOMElement()
    rerender(<LeaveBlockWarningBanner conflicts={undefined} />)
    expect(container).toBeEmptyDOMElement()
  })

  it('có xung đột thì hiện khung cảnh báo kèm ngày và lý do', () => {
    render(<LeaveBlockWarningBanner conflicts={[ONE]} />)
    expect(screen.getByRole('alert')).toHaveTextContent('ngày cấm nghỉ')
    expect(screen.getByText('20/12/2026 – 31/12/2026 · Chốt sổ cuối năm')).toBeInTheDocument()
  })
})
