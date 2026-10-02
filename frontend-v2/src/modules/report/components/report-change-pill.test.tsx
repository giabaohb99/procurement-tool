import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { describeMetricChange } from '../utils/report-period-comparison'
import { ReportChangePill } from './report-change-pill'

describe('ReportChangePill — good/bad/neutral tones follow metric.good, not the raw sign', () => {
  it('tones success (text-success) when the direction matches metric.good', () => {
    render(<ReportChangePill description={describeMetricChange(80, 100, 'money', 'down')} />)
    const pill = screen.getByText('−20%')
    expect(pill.closest('span')).toHaveClass('text-success')
  })

  it('tones destructive when the direction is the OPPOSITE of metric.good', () => {
    render(<ReportChangePill description={describeMetricChange(120, 100, 'money', 'down')} />)
    const pill = screen.getByText('+20%')
    expect(pill.closest('span')).toHaveClass('text-destructive')
  })

  it('tones muted (neutral) when metric.good is null — the number has no good/bad meaning', () => {
    render(<ReportChangePill description={describeMetricChange(120, 100, 'money', null)} />)
    const pill = screen.getByText('+20%')
    expect(pill.closest('span')).toHaveClass('text-muted-foreground')
  })
})

describe('ReportChangePill — special states have no misleading trend icon/color', () => {
  it('renders muted "Không đổi" for a zero change, not a green/red "+0%"', () => {
    render(<ReportChangePill description={describeMetricChange(100, 100, 'money', 'up')} />)
    const pill = screen.getByText('Không đổi')
    expect(pill.closest('span')).toHaveClass('text-muted-foreground')
  })

  it('renders muted "Mới" (no "+∞%", no up/down icon) when the previous period was 0', () => {
    render(<ReportChangePill description={describeMetricChange(50, 0, 'money', 'up')} />)
    const pill = screen.getByText('Mới')
    expect(pill.closest('span')).toHaveClass('text-muted-foreground')
    expect(pill.querySelector('svg')).not.toBeInTheDocument()
  })

  it('renders nothing for "unavailable" (missing data) instead of an empty pill', () => {
    const { container } = render(
      <ReportChangePill description={describeMetricChange(null, 100, 'money', 'up')} />,
    )
    expect(container).toBeEmptyDOMElement()
  })
})

describe('ReportChangePill — percent metrics use "điểm" (point delta), not "%"', () => {
  it('shows "−4,6 điểm" for a percent-kind metric, not a relative percentage', () => {
    render(<ReportChangePill description={describeMetricChange(74.5, 79.1, 'percent', 'up')} />)
    expect(screen.getByText('−4,6 điểm')).toBeInTheDocument()
  })
})
